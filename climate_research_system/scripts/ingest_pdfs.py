"""
PDF Ingestion Script

Loads PDF documents into the RAG system for semantic search.
Supports German and English climate documents.

Usage:
    python scripts/ingest_pdfs.py /path/to/pdfs
    python scripts/ingest_pdfs.py /path/to/pdfs --reset  # Clear existing data first
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from data_collection.rag_retriever import get_rag_retriever
from data_collection.document_store import get_document_store


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Ingest PDF documents into the climate research RAG system'
    )
    parser.add_argument(
        'pdf_path',
        type=str,
        help='Path to PDF file or directory containing PDFs'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Reset document store before ingesting (deletes existing data)'
    )
    parser.add_argument(
        '--pattern',
        type=str,
        default='*.pdf',
        help='File pattern for directory ingestion (default: *.pdf)'
    )

    args = parser.parse_args()

    print_section("🔄 PDF Ingestion - Climate Research System")

    print("This script loads PDF documents into the vector database for semantic search.")
    print("Supports multilingual documents (German/English).\n")

    # Initialize RAG retriever
    print("Initializing RAG system...")
    try:
        rag_retriever = get_rag_retriever()
        print("✓ RAG system initialized")
    except Exception as e:
        print(f"✗ Failed to initialize RAG system: {e}")
        print("\nMake sure required packages are installed:")
        print("  pip install chromadb sentence-transformers docling")
        return 1

    # Reset if requested
    if args.reset:
        print("\n⚠ Resetting document store...")
        response = input("This will delete all existing documents. Continue? (yes/no): ")
        if response.lower() == 'yes':
            rag_retriever.reset()
            print("✓ Document store reset complete")
        else:
            print("Reset cancelled")
            return 0

    # Get PDF path
    pdf_path = Path(args.pdf_path)

    if not pdf_path.exists():
        print(f"✗ Error: Path does not exist: {pdf_path}")
        return 1

    print_section("📄 Processing PDFs")

    # Process PDFs
    if pdf_path.is_file():
        # Single PDF file
        if pdf_path.suffix.lower() != '.pdf':
            print(f"✗ Error: {pdf_path.name} is not a PDF file")
            return 1

        print(f"Processing single PDF: {pdf_path.name}")
        stats = rag_retriever.ingest_pdfs([pdf_path])

    elif pdf_path.is_directory():
        # Directory of PDFs
        pdf_files = list(pdf_path.glob(args.pattern))

        if not pdf_files:
            print(f"✗ No PDF files found matching pattern: {args.pattern}")
            return 1

        print(f"Found {len(pdf_files)} PDF files in {pdf_path}")
        print(f"Pattern: {args.pattern}\n")

        for i, pdf_file in enumerate(pdf_files, 1):
            print(f"  {i}. {pdf_file.name}")

        print()
        stats = rag_retriever.ingest_directory(pdf_path, pattern=args.pattern)

    else:
        print(f"✗ Error: Invalid path type: {pdf_path}")
        return 1

    # Display results
    print_section("✅ Ingestion Complete")

    print(f"PDFs Processed: {stats['successful']}/{stats['total_pdfs']}")
    print(f"Total Chunks Created: {stats['total_chunks']}")
    print(f"Failed: {stats['failed']}")

    if stats['errors']:
        print(f"\n⚠ Errors ({len(stats['errors'])}):")
        for error in stats['errors'][:5]:
            print(f"  • {error}")
        if len(stats['errors']) > 5:
            print(f"  ... and {len(stats['errors']) - 5} more")

    # Show statistics
    print_section("📊 Document Store Statistics")

    try:
        store_stats = rag_retriever.get_statistics()
        doc_stats = store_stats.get('document_store', {})

        print(f"Total Documents in Store: {doc_stats.get('total_documents', 0)}")
        print(f"Embedding Model: {doc_stats.get('embedding_model', 'unknown')}")

        sources = doc_stats.get('sources', {})
        if sources:
            print(f"\nDocuments by Source ({len(sources)} unique sources):")
            for source, count in list(sources.items())[:10]:
                print(f"  • {source}: {count} chunks")

        cities = doc_stats.get('cities', {})
        if cities:
            print(f"\nDetected Cities ({len(cities)}):")
            for city, count in sorted(cities.items(), key=lambda x: x[1], reverse=True)[:15]:
                if city != 'unknown':
                    print(f"  • {city}: {count} mentions")

    except Exception as e:
        print(f"Could not retrieve statistics: {e}")

    print_section("💡 Next Steps")

    print("Your PDFs have been indexed and are ready for semantic search!")
    print()
    print("To query the data:")
    print("  1. Use the PDFDataCollectionAgent in your research pipeline")
    print("  2. Run: python examples/rag_demo.py")
    print("  3. Use the web dashboard with PDF data enabled")
    print()
    print("The system uses:")
    print("  ✓ Semantic search (finds relevant info even with different wording)")
    print("  ✓ Multilingual support (German/English)")
    print("  ✓ Source tracking (exact PDF and page number)")
    print("  ✓ LLM-powered extraction (structured data from text)")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
