"""
PDF Data Collection Agent

LLM-powered agent that extracts climate data from PDF documents using RAG.
Supports multilingual documents (German/English).
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent, AgentStatus
from core.source_tracker import (
    SourceTracker,
    DataSource,
    SourceType,
    ReliabilityTier,
    CollectionMethod
)

# Import RAG components
sys.path.append(str(Path(__file__).parent.parent))
from rag_retriever import RAGRetriever, get_rag_retriever


class PDFDataCollectionAgent(Agent):
    """
    LLM-powered agent for extracting climate data from PDFs using RAG.

    Responsibilities:
    - Query PDF documents for city-specific climate data
    - Use semantic search to find relevant information
    - Extract structured data with LLM
    - Track sources with full provenance (PDF, page number, excerpt)
    """

    def __init__(
        self,
        agent_id: str = "pdf_data_001",
        name: str = "PDF Data Collection Agent",
        config: Optional[Dict] = None
    ):
        super().__init__(agent_id, name, config)

        # Initialize source tracking
        self.source_tracker = SourceTracker()

        # Initialize RAG retriever
        try:
            self.rag_retriever = get_rag_retriever()
            self.logger.info("RAG retriever initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize RAG retriever: {e}")
            self.rag_retriever = None

        # System prompt for LLM
        self.system_prompt = """You are a climate data extraction specialist analyzing German and English PDF documents.

Your task:
1. Extract factual climate data from provided document excerpts
2. Focus on quantitative data (temperatures, precipitation, emissions, etc.)
3. Preserve exact numbers and units
4. Note the source and page number for each data point
5. Handle both German and English text
6. Only extract information that is explicitly stated in the documents

Important:
- Be precise with numbers and units
- Do not make assumptions or extrapolations
- If data is unclear or missing, state that explicitly
- Preserve German city names and terminology
- Cite the specific document and page for each fact"""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute PDF data collection task.

        Args:
            task: Dictionary with 'city', 'country' (optional), 'topics' (optional)

        Returns:
            Extracted climate data with sources
        """
        self.status = AgentStatus.WORKING
        city = task.get('city')
        country = task.get('country', '')

        if not city:
            return {'error': 'City name is required'}

        self.logger.info(f"Collecting PDF data for {city}")

        if not self.rag_retriever:
            return {'error': 'RAG retriever not available'}

        try:
            # Define topics to search for
            topics = task.get('topics', [
                'Temperatur Klima temperature climate',
                'Niederschlag Regen precipitation rainfall',
                'Emissionen Treibhausgas emissions greenhouse',
                'Klimarisiko Vulnerabilität vulnerability risk',
                'Anpassung Maßnahmen adaptation measures'
            ])

            # Retrieve relevant documents for each topic
            all_results = {}
            retrieval_stats = {
                'topics_searched': len(topics),
                'total_chunks_retrieved': 0
            }

            for topic in topics:
                query = f"{city} {topic}"
                results = self.rag_retriever.retrieve(
                    query=query,
                    city=city,
                    n_results=3
                )

                if results:
                    all_results[topic] = results
                    retrieval_stats['total_chunks_retrieved'] += len(results)

            self.logger.info(f"Retrieved {retrieval_stats['total_chunks_retrieved']} relevant chunks")

            # Build context for LLM
            all_retrieval_results = []
            for topic_results in all_results.values():
                all_retrieval_results.extend(topic_results)

            context, sources = self.rag_retriever.build_context(
                all_retrieval_results,
                max_length=6000
            )

            # Extract data using LLM
            extracted_data = self._extract_data_with_llm(
                city=city,
                country=country,
                context=context
            )

            # Track sources
            pdf_sources = self._track_pdf_sources(sources)

            # Build results
            results = {
                'city': city,
                'country': country,
                'collected_at': datetime.utcnow().isoformat(),
                'agent_id': self.agent_id,
                'extracted_data': extracted_data,
                'sources': [s.to_dict() for s in pdf_sources],
                'retrieval_stats': retrieval_stats,
                'llm_model': self.llm.model if hasattr(self.llm, 'model') else 'unknown',
                'confidence_score': self._calculate_confidence(sources)
            }

            self.status = AgentStatus.IDLE
            self.logger.info(f"PDF data collection complete for {city}")

            return results

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"PDF data collection error: {e}")
            return {
                'error': str(e),
                'agent_id': self.agent_id,
                'city': city
            }

    def _extract_data_with_llm(
        self,
        city: str,
        country: str,
        context: str
    ) -> Dict[str, Any]:
        """Use LLM to extract structured data from context."""

        if not context or not context.strip():
            return {
                'note': 'No relevant data found in PDF documents',
                'raw_analysis': 'No documents contained information for this city.'
            }

        prompt = f"""Extract climate data for {city}, {country} from the following document excerpts.

The documents may be in German or English. Extract all relevant climate information.

Document Excerpts:
{context}

Please extract and structure the following information (if available):

**Temperature Data:**
- Average temperature
- Temperature trends
- Extreme temperature events

**Precipitation Data:**
- Average precipitation
- Seasonal patterns
- Extreme events (floods, droughts)

**Emissions Data:**
- GHG emissions
- Sector breakdown
- Trends

**Climate Risks:**
- Identified vulnerabilities
- At-risk populations or infrastructure
- Risk assessments

**Adaptation Measures:**
- Implemented measures
- Planned actions
- Policies

For each data point, note:
- The exact value with units
- The source document and page number
- The year or time period

Format as structured JSON where possible. Be precise and cite sources."""

        response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.2  # Low temperature for factual extraction
        )

        return {
            'raw_analysis': response['content'],
            'llm_model': response.get('model', 'unknown'),
            'tokens_used': response.get('tokens_used', 0)
        }

    def _track_pdf_sources(self, sources: List[Dict[str, Any]]) -> List[DataSource]:
        """Track PDF sources for provenance."""
        pdf_sources = []

        for source_info in sources:
            source = self.source_tracker.add_source(
                url=f"file://{source_info['source']}#page={source_info['page']}",
                title=f"{source_info['source']} (Page {source_info['page']})",
                source_type=SourceType.OFFICIAL_DATABASE,  # PDFs from research center
                reliability_tier=ReliabilityTier.TIER_1,  # Internal research documents
                collection_method=CollectionMethod.DATABASE_QUERY,
                relevant_excerpt=source_info.get('excerpt', ''),
                methodology="RAG-based semantic search and LLM extraction from PDF documents",
                data_format="PDF",
                metadata={
                    'page_number': source_info['page'],
                    'relevance_score': source_info.get('relevance', 0.0)
                }
            )
            pdf_sources.append(source)

        return pdf_sources

    def _calculate_confidence(self, sources: List[Dict[str, Any]]) -> float:
        """Calculate confidence score based on sources."""
        if not sources:
            return 0.0

        # Base confidence on number of sources and relevance scores
        num_sources = len(sources)
        avg_relevance = sum(s.get('relevance', 0.0) for s in sources) / num_sources

        # Higher confidence with more sources and higher relevance
        confidence = min(1.0, (num_sources / 5.0) * avg_relevance)

        return round(confidence, 2)

    def validate(self) -> bool:
        """Validate agent configuration."""
        if not self.rag_retriever:
            self.logger.error("RAG retriever not initialized")
            return False

        # Check if document store has documents
        try:
            stats = self.rag_retriever.get_statistics()
            doc_count = stats.get('document_store', {}).get('total_documents', 0)

            if doc_count == 0:
                self.logger.warning("Document store is empty - no PDFs have been ingested")
                self.logger.warning("Use ingest_pdfs.py to load PDF documents first")

            return True

        except Exception as e:
            self.logger.error(f"Validation error: {e}")
            return False
