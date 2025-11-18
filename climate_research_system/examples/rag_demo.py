"""
RAG System Demo

Demonstrates PDF-based data collection with Retrieval-Augmented Generation.
Shows semantic search across German/English climate documents.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from data_collection.rag_retriever import get_rag_retriever
from data_collection.agents.pdf_data_agent import PDFDataCollectionAgent
from config.config_loader import load_model_config


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_retrieval_result(result, index):
    """Print a single retrieval result."""
    print(f"{index}. Source: {result.source} (Page {result.page_number})")
    print(f"   Relevance: {result.relevance_score:.3f}")
    print(f"   Excerpt: {result.text[:200]}...")
    print()


def main():
    """Run RAG demonstration."""
    print_section("🔍 RAG System Demo - PDF Data Collection")

    print("This demo shows how the system uses Retrieval-Augmented Generation (RAG)")
    print("to extract climate data from PDF documents.")
    print()
    print("Features:")
    print("  ✓ Semantic search across documents")
    print("  ✓ Multilingual support (German/English)")
    print("  ✓ Exact source tracking (PDF + page number)")
    print("  ✓ LLM-powered data extraction")
    print()

    # Check if document store has documents
    print_section("📊 System Status")

    try:
        rag_retriever = get_rag_retriever()
        stats = rag_retriever.get_statistics()
        doc_count = stats.get('document_store', {}).get('total_documents', 0)

        print(f"Document Store Status:")
        print(f"  Total Documents: {doc_count}")
        print(f"  Embedding Model: {stats.get('document_store', {}).get('embedding_model', 'unknown')}")

        if doc_count == 0:
            print()
            print("⚠ WARNING: Document store is empty!")
            print()
            print("To use this demo, you need to ingest PDF documents first:")
            print("  python scripts/ingest_pdfs.py /path/to/your/pdfs")
            print()
            print("For testing, you can create a sample PDF or use existing climate reports.")
            return

    except Exception as e:
        print(f"✗ Error initializing RAG system: {e}")
        print("\nMake sure required packages are installed:")
        print("  pip install chromadb sentence-transformers docling")
        return

    # Demo 1: Direct semantic search
    print_section("🔎 Demo 1: Semantic Search")

    print("Searching for: 'Berlin temperature trends climate change'\n")

    try:
        results = rag_retriever.retrieve(
            query="Berlin temperature trends climate change",
            n_results=3
        )

        if results:
            print(f"Found {len(results)} relevant documents:\n")
            for i, result in enumerate(results, 1):
                print_retrieval_result(result, i)
        else:
            print("No results found. Make sure PDFs contain relevant information.")

    except Exception as e:
        print(f"Search error: {e}")

    # Demo 2: City-specific search
    print_section("🏙 Demo 2: City-Specific Search")

    city = "Munich"
    print(f"Retrieving climate data for {city} across multiple topics...\n")

    try:
        city_results = rag_retriever.retrieve_for_city(
            city=city,
            topics=['temperature', 'precipitation', 'emissions'],
            n_results_per_topic=2
        )

        for topic, results in city_results.items():
            print(f"Topic: {topic}")
            print(f"Found {len(results)} results")
            if results:
                print(f"  Top result: {results[0].source}, Page {results[0].page_number}")
                print(f"  Relevance: {results[0].relevance_score:.3f}")
            print()

    except Exception as e:
        print(f"City search error: {e}")

    # Demo 3: Agent-based extraction
    print_section("🤖 Demo 3: Agent-Based Data Extraction")

    print("Using PDFDataCollectionAgent to extract structured data...\n")

    try:
        # Load model config
        model_config = load_model_config()

        # Create agent
        pdf_agent = PDFDataCollectionAgent(
            agent_id="pdf_demo_001",
            config=model_config
        )

        # Validate agent
        if not pdf_agent.validate():
            print("⚠ Agent validation failed")
            return

        # Execute extraction for a city
        test_city = "Berlin"
        print(f"Extracting climate data for {test_city}...\n")

        results = pdf_agent.execute({
            'city': test_city,
            'country': 'Germany'
        })

        if 'error' in results:
            print(f"✗ Error: {results['error']}")
        else:
            print(f"✓ Data extraction complete!")
            print()
            print(f"City: {results['city']}")
            print(f"Agent: {results['agent_id']}")
            print(f"LLM Model: {results['llm_model']}")
            print(f"Sources Used: {len(results.get('sources', []))}")
            print(f"Confidence Score: {results.get('confidence_score', 0.0)}")
            print()

            # Show sources
            sources = results.get('sources', [])
            if sources:
                print("Data Sources:")
                for i, source in enumerate(sources[:3], 1):
                    print(f"  {i}. {source.get('title', 'Unknown')}")
                    print(f"     Reliability: Tier {source.get('reliability_tier', 'unknown')}")
                    excerpt = source.get('relevant_excerpt', '')
                    if excerpt:
                        print(f"     Excerpt: {excerpt[:150]}...")
                    print()

            # Show extraction stats
            stats = results.get('retrieval_stats', {})
            if stats:
                print(f"Retrieval Statistics:")
                print(f"  Topics Searched: {stats.get('topics_searched', 0)}")
                print(f"  Chunks Retrieved: {stats.get('total_chunks_retrieved', 0)}")
                print()

            # Show extracted data (first 500 chars)
            extracted = results.get('extracted_data', {})
            if extracted:
                raw_analysis = extracted.get('raw_analysis', '')
                if raw_analysis:
                    print("Extracted Climate Data (excerpt):")
                    print("─" * 80)
                    print(raw_analysis[:500])
                    if len(raw_analysis) > 500:
                        print("...")
                        print(f"\n({len(raw_analysis)} total characters)")
                    print()

    except Exception as e:
        print(f"Agent error: {e}")
        import traceback
        traceback.print_exc()

    # Summary
    print_section("✨ Demo Complete")

    print("RAG System Capabilities Demonstrated:")
    print("  ✓ Semantic search across PDF documents")
    print("  ✓ City-specific information retrieval")
    print("  ✓ Multi-topic data extraction")
    print("  ✓ LLM-powered structured data extraction")
    print("  ✓ Full source provenance tracking")
    print()
    print("Benefits for Research:")
    print("  • Handles 40+ PDFs efficiently")
    print("  • Works with German and English documents")
    print("  • Finds relevant info even with different wording (semantic search)")
    print("  • Tracks exact PDF and page number for citations")
    print("  • Extracts structured data automatically")
    print()


if __name__ == "__main__":
    main()
