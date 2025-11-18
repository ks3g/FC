"""
Document Store using ChromaDB

Vector database for storing and retrieving PDF chunks with semantic search.
Supports multilingual embeddings (German/English).
"""

from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime
import logging

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    chromadb = None
    Settings = None
    print("Warning: chromadb not installed. Run: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    SentenceTransformer = None
    print("Warning: sentence-transformers not installed. Run: pip install sentence-transformers")


class DocumentStore:
    """
    Vector database for document storage and retrieval.

    Uses ChromaDB for local, persistent vector storage.
    Supports semantic search with multilingual embeddings.
    """

    def __init__(
        self,
        persist_directory: Optional[Path] = None,
        collection_name: str = "climate_documents",
        embedding_model: str = "paraphrase-multilingual-MiniLM-L12-v2"
    ):
        """
        Initialize document store.

        Args:
            persist_directory: Directory for persistent storage
            collection_name: Name of the collection
            embedding_model: Sentence transformer model (multilingual by default)
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("chromadb is required. Install with: pip install chromadb")

        if persist_directory is None:
            persist_directory = Path(__file__).parent.parent / "data" / "vector_store"

        self.persist_directory = Path(persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        self.collection_name = collection_name
        self.embedding_model_name = embedding_model

        # Setup logging
        self.logger = logging.getLogger(__name__)

        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

        # Initialize or get collection
        self.collection = self._get_or_create_collection()

        # Initialize embedding model
        self.embedding_model = self._initialize_embeddings()

        self.logger.info(f"DocumentStore initialized at {self.persist_directory}")
        self.logger.info(f"Collection: {self.collection_name}")
        self.logger.info(f"Embedding model: {self.embedding_model_name}")

    def _get_or_create_collection(self):
        """Get or create ChromaDB collection."""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            self.logger.info(f"Loaded existing collection: {self.collection_name}")
        except:
            # Create new collection
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "Climate research documents"}
            )
            self.logger.info(f"Created new collection: {self.collection_name}")

        return collection

    def _initialize_embeddings(self):
        """Initialize embedding model."""
        if not EMBEDDINGS_AVAILABLE:
            self.logger.warning("sentence-transformers not available, using ChromaDB default embeddings")
            return None

        try:
            model = SentenceTransformer(self.embedding_model_name)
            self.logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            return model
        except Exception as e:
            self.logger.error(f"Failed to load embedding model: {e}")
            return None

    def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]],
        ids: Optional[List[str]] = None
    ) -> List[str]:
        """
        Add documents to the vector store.

        Args:
            texts: List of document texts/chunks
            metadatas: List of metadata dicts for each chunk
            ids: Optional list of IDs (auto-generated if not provided)

        Returns:
            List of document IDs
        """
        if not texts:
            return []

        # Generate IDs if not provided
        if ids is None:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            ids = [f"doc_{timestamp}_{i}" for i in range(len(texts))]

        # Generate embeddings if model available
        embeddings = None
        if self.embedding_model:
            try:
                embeddings = self.embedding_model.encode(texts).tolist()
            except Exception as e:
                self.logger.warning(f"Failed to generate embeddings: {e}")

        # Add to collection
        try:
            if embeddings:
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids,
                    embeddings=embeddings
                )
            else:
                # Let ChromaDB generate embeddings
                self.collection.add(
                    documents=texts,
                    metadatas=metadatas,
                    ids=ids
                )

            self.logger.info(f"Added {len(texts)} documents to store")
            return ids

        except Exception as e:
            self.logger.error(f"Failed to add documents: {e}")
            raise

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """
        Search for relevant documents.

        Args:
            query: Search query
            n_results: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            Dict with 'documents', 'metadatas', 'distances', 'ids'
        """
        # Generate query embedding if model available
        query_embedding = None
        if self.embedding_model:
            try:
                query_embedding = self.embedding_model.encode([query])[0].tolist()
            except Exception as e:
                self.logger.warning(f"Failed to generate query embedding: {e}")

        # Build query parameters
        query_params = {
            "n_results": n_results
        }

        if filter_metadata:
            query_params["where"] = filter_metadata

        # Execute search
        try:
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    **query_params
                )
            else:
                results = self.collection.query(
                    query_texts=[query],
                    **query_params
                )

            self.logger.info(f"Search returned {len(results['ids'][0])} results")

            # Flatten results (ChromaDB returns nested lists)
            return {
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else [],
                'ids': results['ids'][0] if results['ids'] else []
            }

        except Exception as e:
            self.logger.error(f"Search failed: {e}")
            return {
                'documents': [],
                'metadatas': [],
                'distances': [],
                'ids': []
            }

    def search_by_city(
        self,
        city: str,
        query: str,
        n_results: int = 5
    ) -> Dict[str, List]:
        """
        Search for documents related to a specific city.

        Args:
            city: City name
            query: Search query
            n_results: Number of results

        Returns:
            Search results
        """
        # Create city-specific query
        city_query = f"{city} {query}"

        # Search with city filter if available in metadata
        return self.search(
            query=city_query,
            n_results=n_results,
            filter_metadata={"city": city} if self.has_city_metadata() else None
        )

    def has_city_metadata(self) -> bool:
        """Check if any documents have city metadata."""
        try:
            results = self.collection.peek(limit=1)
            if results['metadatas']:
                return 'city' in results['metadatas'][0]
        except:
            pass
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the document store."""
        try:
            count = self.collection.count()

            # Get sample documents to analyze
            sample = self.collection.peek(limit=min(100, count))

            # Count by document source
            sources = {}
            cities = {}

            for metadata in sample['metadatas']:
                source = metadata.get('source', 'unknown')
                sources[source] = sources.get(source, 0) + 1

                city = metadata.get('city', 'unknown')
                cities[city] = cities.get(city, 0) + 1

            return {
                'total_documents': count,
                'sources': sources,
                'cities': cities,
                'embedding_model': self.embedding_model_name,
                'collection_name': self.collection_name
            }

        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {'error': str(e)}

    def delete_by_source(self, source: str) -> int:
        """
        Delete all documents from a specific source.

        Args:
            source: Source identifier (e.g., PDF filename)

        Returns:
            Number of documents deleted
        """
        try:
            # Get documents from this source
            results = self.collection.get(
                where={"source": source}
            )

            if results['ids']:
                self.collection.delete(ids=results['ids'])
                self.logger.info(f"Deleted {len(results['ids'])} documents from source: {source}")
                return len(results['ids'])

            return 0

        except Exception as e:
            self.logger.error(f"Failed to delete documents: {e}")
            return 0

    def reset(self):
        """Delete all documents (use with caution!)."""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self._get_or_create_collection()
            self.logger.warning("Document store has been reset")
        except Exception as e:
            self.logger.error(f"Failed to reset store: {e}")

    def export_metadata(self, output_path: Path):
        """Export all metadata to JSON file."""
        try:
            count = self.collection.count()
            all_data = self.collection.get(limit=count)

            export_data = {
                'exported_at': datetime.utcnow().isoformat(),
                'total_documents': count,
                'metadatas': all_data['metadatas'],
                'ids': all_data['ids']
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)

            self.logger.info(f"Exported metadata to {output_path}")

        except Exception as e:
            self.logger.error(f"Failed to export metadata: {e}")


# Global document store instance
_document_store = None


def get_document_store(
    persist_directory: Optional[Path] = None,
    collection_name: str = "climate_documents"
) -> DocumentStore:
    """
    Get global document store instance.

    Args:
        persist_directory: Optional custom directory
        collection_name: Optional custom collection name

    Returns:
        DocumentStore instance
    """
    global _document_store

    if _document_store is None:
        _document_store = DocumentStore(
            persist_directory=persist_directory,
            collection_name=collection_name
        )

    return _document_store
