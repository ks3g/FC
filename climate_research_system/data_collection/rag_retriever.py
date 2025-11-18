"""
RAG Retriever

Retrieval-Augmented Generation system for querying PDF documents.
Combines semantic search with LLM-based extraction.
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import logging
from datetime import datetime

from .document_store import DocumentStore, get_document_store
from .pdf_processor import PDFProcessor, PDFChunk


class RetrievalResult:
    """Represents a retrieval result with source tracking."""

    def __init__(
        self,
        text: str,
        source: str,
        page_number: int,
        relevance_score: float,
        metadata: Dict[str, Any]
    ):
        self.text = text
        self.source = source
        self.page_number = page_number
        self.relevance_score = relevance_score
        self.metadata = metadata

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'text': self.text,
            'source': self.source,
            'page_number': self.page_number,
            'relevance_score': self.relevance_score,
            'metadata': self.metadata
        }

    def __repr__(self) -> str:
        return f"RetrievalResult(source={self.source}, page={self.page_number}, score={self.relevance_score:.3f})"


class RAGRetriever:
    """
    Retrieval-Augmented Generation system.

    Features:
    - Semantic search across PDF documents
    - City-specific filtering
    - Source tracking for provenance
    - Relevance scoring
    """

    def __init__(
        self,
        document_store: Optional[DocumentStore] = None,
        pdf_processor: Optional[PDFProcessor] = None
    ):
        """
        Initialize RAG retriever.

        Args:
            document_store: DocumentStore instance (creates default if None)
            pdf_processor: PDFProcessor instance (creates default if None)
        """
        self.document_store = document_store or get_document_store()
        self.pdf_processor = pdf_processor or PDFProcessor()

        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("RAGRetriever initialized")

    def ingest_pdfs(
        self,
        pdf_paths: List[Path],
        batch_size: int = 100
    ) -> Dict[str, Any]:
        """
        Ingest PDF files into the document store.

        Args:
            pdf_paths: List of PDF file paths
            batch_size: Batch size for adding to vector store

        Returns:
            Ingestion statistics
        """
        self.logger.info(f"Ingesting {len(pdf_paths)} PDF files")

        stats = {
            'total_pdfs': len(pdf_paths),
            'successful': 0,
            'failed': 0,
            'total_chunks': 0,
            'errors': []
        }

        all_chunks = []

        for pdf_path in pdf_paths:
            try:
                # Process PDF
                chunks = self.pdf_processor.process_pdf(pdf_path)

                if chunks:
                    all_chunks.extend(chunks)
                    stats['successful'] += 1
                    stats['total_chunks'] += len(chunks)
                else:
                    stats['failed'] += 1
                    stats['errors'].append(f"{pdf_path.name}: No chunks extracted")

            except Exception as e:
                stats['failed'] += 1
                stats['errors'].append(f"{pdf_path.name}: {str(e)}")
                self.logger.error(f"Failed to process {pdf_path}: {e}")

        # Add chunks to document store in batches
        if all_chunks:
            for i in range(0, len(all_chunks), batch_size):
                batch = all_chunks[i:i + batch_size]

                texts = [chunk.text for chunk in batch]
                metadatas = [chunk.to_dict() for chunk in batch]

                try:
                    self.document_store.add_documents(texts, metadatas)
                except Exception as e:
                    self.logger.error(f"Failed to add batch to store: {e}")

        self.logger.info(
            f"Ingestion complete: {stats['successful']}/{stats['total_pdfs']} PDFs, "
            f"{stats['total_chunks']} chunks"
        )

        return stats

    def ingest_directory(
        self,
        directory: Path,
        pattern: str = "*.pdf"
    ) -> Dict[str, Any]:
        """
        Ingest all PDFs from a directory.

        Args:
            directory: Directory containing PDFs
            pattern: File pattern (default: *.pdf)

        Returns:
            Ingestion statistics
        """
        pdf_files = list(Path(directory).glob(pattern))
        return self.ingest_pdfs(pdf_files)

    def retrieve(
        self,
        query: str,
        city: Optional[str] = None,
        n_results: int = 5,
        min_relevance: float = 0.0
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant document chunks.

        Args:
            query: Search query
            city: Optional city name for filtering
            n_results: Number of results to return
            min_relevance: Minimum relevance score (0.0-1.0)

        Returns:
            List of RetrievalResult objects
        """
        self.logger.info(f"Retrieving documents for query: {query[:100]}...")

        if city:
            # City-specific search
            results = self.document_store.search_by_city(
                city=city,
                query=query,
                n_results=n_results
            )
        else:
            # General search
            results = self.document_store.search(
                query=query,
                n_results=n_results
            )

        # Convert to RetrievalResult objects
        retrieval_results = []

        for i, (text, metadata, distance) in enumerate(zip(
            results['documents'],
            results['metadatas'],
            results['distances']
        )):
            # Convert distance to relevance score (0-1, higher is better)
            # ChromaDB uses L2 distance, so smaller is better
            relevance_score = max(0.0, 1.0 - distance)

            if relevance_score >= min_relevance:
                result = RetrievalResult(
                    text=text,
                    source=metadata.get('source', 'unknown'),
                    page_number=metadata.get('page_number', 0),
                    relevance_score=relevance_score,
                    metadata=metadata
                )
                retrieval_results.append(result)

        self.logger.info(f"Retrieved {len(retrieval_results)} results")

        return retrieval_results

    def retrieve_for_city(
        self,
        city: str,
        topics: Optional[List[str]] = None,
        n_results_per_topic: int = 3
    ) -> Dict[str, List[RetrievalResult]]:
        """
        Retrieve climate data for a specific city across multiple topics.

        Args:
            city: City name
            topics: List of topics (default: climate standard topics)
            n_results_per_topic: Results per topic

        Returns:
            Dict mapping topic to list of results
        """
        if topics is None:
            topics = [
                'temperature climate data',
                'precipitation rainfall',
                'emissions greenhouse gas',
                'climate risks vulnerability',
                'adaptation measures'
            ]

        results = {}

        for topic in topics:
            query = f"{city} {topic}"
            topic_results = self.retrieve(
                query=query,
                city=city,
                n_results=n_results_per_topic
            )
            results[topic] = topic_results

        return results

    def build_context(
        self,
        retrieval_results: List[RetrievalResult],
        max_length: int = 4000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Build context string from retrieval results for LLM.

        Args:
            retrieval_results: List of retrieval results
            max_length: Maximum context length in characters

        Returns:
            Tuple of (context_string, sources)
        """
        context_parts = []
        sources = []
        current_length = 0

        for i, result in enumerate(retrieval_results):
            # Format chunk with source info
            chunk_text = f"[Source: {result.source}, Page {result.page_number}]\n{result.text}\n"

            if current_length + len(chunk_text) > max_length:
                break

            context_parts.append(chunk_text)
            current_length += len(chunk_text)

            # Track source
            sources.append({
                'source': result.source,
                'page': result.page_number,
                'relevance': result.relevance_score,
                'excerpt': result.text[:200] + '...' if len(result.text) > 200 else result.text
            })

        context = "\n---\n".join(context_parts)

        return context, sources

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the RAG system."""
        doc_stats = self.document_store.get_statistics()

        return {
            'document_store': doc_stats,
            'retriever': {
                'chunk_size': self.pdf_processor.chunk_size,
                'chunk_overlap': self.pdf_processor.chunk_overlap
            }
        }

    def delete_pdf(self, pdf_filename: str) -> int:
        """
        Remove all chunks from a specific PDF.

        Args:
            pdf_filename: Name of PDF file

        Returns:
            Number of chunks deleted
        """
        return self.document_store.delete_by_source(pdf_filename)

    def reset(self):
        """Delete all documents (use with caution!)."""
        self.document_store.reset()


# Global RAG retriever instance
_rag_retriever = None


def get_rag_retriever() -> RAGRetriever:
    """
    Get global RAG retriever instance.

    Returns:
        RAGRetriever instance
    """
    global _rag_retriever

    if _rag_retriever is None:
        _rag_retriever = RAGRetriever()

    return _rag_retriever
