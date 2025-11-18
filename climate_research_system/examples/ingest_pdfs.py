#!/usr/bin/env python3
"""
PDF Ingestion Script

Processes all PDFs in the data/pdfs directory and stores them in ChromaDB
for semantic search by the PDF Data Collection Agent.

Usage:
    python climate_research_system/examples/ingest_pdfs.py

Requirements:
    pip install chromadb sentence-transformers docling
"""

import sys
from pathlib import Path
import logging

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.pdf_processor import PDFProcessor
from data_collection.document_store import DocumentStore

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def ingest_pdfs(pdf_directory: str = "climate_research_system/data/pdfs"):
    """
    Ingest all PDFs from the specified directory.

    Args:
        pdf_directory: Directory containing PDF files
    """
    pdf_dir = Path(pdf_directory)

    if not pdf_dir.exists():
        logger.error(f"PDF directory not found: {pdf_directory}")
        logger.info("Please create the directory and add PDF files:")
        logger.info(f"  mkdir -p {pdf_directory}")
        return

    # Find all PDF files
    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {pdf_directory}")
        logger.info("Please add PDF files to the directory:")
        logger.info(f"  cp /path/to/your/pdfs/*.pdf {pdf_directory}/")
        return

    logger.info(f"Found {len(pdf_files)} PDF files to process")
    logger.info("=" * 70)

    # Initialize components
    try:
        logger.info("Initializing PDF processor...")
        processor = PDFProcessor(
            chunk_size=1000,
            chunk_overlap=200,
            extract_tables=True
        )

        logger.info("Initializing document store (ChromaDB)...")
        store = DocumentStore(
            persist_directory=Path("climate_research_system/data/vector_store"),
            collection_name="climate_documents",
            embedding_model="paraphrase-multilingual-MiniLM-L12-v2"
        )

    except Exception as e:
        logger.error(f"Failed to initialize components: {e}")
        logger.error("\nPlease install required packages:")
        logger.error("  pip install chromadb sentence-transformers docling")
        return

    # Process each PDF
    total_chunks = 0
    successful_files = 0
    failed_files = []

    for pdf_file in pdf_files:
        logger.info(f"\nProcessing: {pdf_file.name}")
        logger.info("-" * 70)

        try:
            # Extract chunks from PDF
            chunks = processor.process_pdf(pdf_file)
            logger.info(f"  Extracted {len(chunks)} chunks")

            if chunks:
                # Add to document store
                store.add_documents(chunks)
                logger.info(f"  ✓ Stored in vector database")

                total_chunks += len(chunks)
                successful_files += 1
            else:
                logger.warning(f"  ⚠ No content extracted from {pdf_file.name}")

        except Exception as e:
            logger.error(f"  ✗ Error processing {pdf_file.name}: {e}")
            failed_files.append((pdf_file.name, str(e)))

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("INGESTION SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total PDFs processed:     {len(pdf_files)}")
    logger.info(f"Successfully ingested:    {successful_files}")
    logger.info(f"Failed:                   {len(failed_files)}")
    logger.info(f"Total chunks stored:      {total_chunks}")

    if failed_files:
        logger.info("\nFailed Files:")
        for filename, error in failed_files:
            logger.info(f"  - {filename}: {error}")

    # Get collection stats
    try:
        stats = store.get_collection_stats()
        logger.info("\nVector Store Statistics:")
        logger.info(f"  Total documents:  {stats['total_documents']}")
        logger.info(f"  Collection name:  {stats['collection_name']}")
        logger.info(f"  Embedding model:  {stats['embedding_model']}")
    except Exception as e:
        logger.warning(f"Could not retrieve collection stats: {e}")

    logger.info("\n" + "=" * 70)
    logger.info("Ingestion complete! PDFs are now ready for semantic search.")
    logger.info("=" * 70)


def test_search(query: str = "Berlin climate data"):
    """
    Test the document store with a sample search.

    Args:
        query: Search query to test
    """
    logger.info(f"\nTesting search with query: '{query}'")
    logger.info("-" * 70)

    try:
        store = DocumentStore(
            persist_directory=Path("climate_research_system/data/vector_store"),
            collection_name="climate_documents"
        )

        results = store.search(query, n_results=3)

        if results['documents']:
            logger.info(f"Found {len(results['documents'])} results:")
            for i, (doc, metadata, distance) in enumerate(
                zip(results['documents'], results['metadatas'], results['distances'])
            ):
                logger.info(f"\n  Result {i+1}:")
                logger.info(f"    Source: {metadata.get('source', 'unknown')}")
                logger.info(f"    Page: {metadata.get('page_number', '?')}")
                logger.info(f"    Relevance: {1 - distance:.2%}")
                logger.info(f"    Preview: {doc[:200]}...")
        else:
            logger.info("No results found")

    except Exception as e:
        logger.error(f"Search test failed: {e}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Ingest PDFs into vector database")
    parser.add_argument(
        "--pdf-dir",
        default="climate_research_system/data/pdfs",
        help="Directory containing PDF files"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Run a test search after ingestion"
    )
    parser.add_argument(
        "--test-query",
        default="Berlin climate data",
        help="Query to use for test search"
    )

    args = parser.parse_args()

    # Run ingestion
    ingest_pdfs(args.pdf_dir)

    # Run test search if requested
    if args.test:
        test_search(args.test_query)
