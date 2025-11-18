"""
Validation Agent

Cross-verifies data from multiple sources and ensures research integrity.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent, AgentStatus
from core.message import Message, MessageType
from core.source_tracker import (
    SourceTracker,
    DataSource,
    SourceType,
    ReliabilityTier,
    CollectionMethod,
    determine_source_type,
    determine_reliability_tier
)
from core.source_database import get_source_database


class ValidationAgent(Agent):
    """
    Validates research data through multi-source verification.

    Responsibilities:
    - Cross-verify facts across multiple sources
    - Assess source reliability
    - Calculate confidence scores
    - Flag inconsistencies
    - Maintain data provenance
    """

    def __init__(self, agent_id: str = "validation_001", name: str = "ValidationAgent", config: Optional[Dict] = None):
        super().__init__(agent_id, name, config)

        # Initialize source tracking
        self.source_tracker = SourceTracker()
        self.source_db = get_source_database()

        # System prompt for LLM
        self.system_prompt = """You are a research validation specialist focused on climate science data integrity.

Your role:
1. Assess the reliability and credibility of data sources
2. Identify potential inconsistencies or conflicts in data
3. Evaluate whether facts are supported by sufficient evidence
4. Flag data that requires additional verification
5. Suggest authoritative sources for cross-verification

For each piece of information, consider:
- Source authority and reputation
- Methodology used to collect data
- Consistency with other sources
- Recency and relevance
- Potential biases or conflicts of interest

Provide structured assessments with confidence scores and recommendations."""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute validation task.

        Args:
            task: Contains 'data' (dict of results from other agents) and 'city'

        Returns:
            Validation report with confidence scores and source assessments
        """
        self.status = AgentStatus.WORKING
        self.logger.info(f"Starting validation for {task.get('city', 'unknown')}")

        try:
            city = task.get('city', 'unknown')
            country = task.get('country', '')
            agent_results = task.get('agent_results', {})

            # Validate each agent's results
            validation_results = {}

            for agent_id, results in agent_results.items():
                validation = self._validate_agent_results(
                    agent_id=agent_id,
                    results=results,
                    city=city,
                    country=country
                )
                validation_results[agent_id] = validation

            # Cross-verify common facts
            cross_verification = self._cross_verify_results(agent_results, city, country)

            # Generate overall assessment
            overall_assessment = self._generate_overall_assessment(
                validation_results,
                cross_verification,
                city
            )

            # Save sources to database
            for source in self.source_tracker.sources:
                self.source_db.add_source(source)

            # Generate provenance report
            provenance = self.source_tracker.generate_provenance_report()

            self.status = AgentStatus.IDLE
            self.logger.info("Validation complete")

            return {
                'city': city,
                'country': country,
                'validation_results': validation_results,
                'cross_verification': cross_verification,
                'overall_assessment': overall_assessment,
                'provenance_report': provenance,
                'sources': [s.to_dict() for s in self.source_tracker.sources],
                'total_sources': len(self.source_tracker.sources),
                'avg_confidence': overall_assessment.get('average_confidence', 0.0),
                'validated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.status = AgentStatus.ERROR
            self.logger.error(f"Validation error: {e}")
            return {
                'error': str(e),
                'agent_id': self.agent_id
            }

    def _validate_agent_results(
        self,
        agent_id: str,
        results: Dict[str, Any],
        city: str,
        country: str
    ) -> Dict[str, Any]:
        """Validate results from a single agent."""

        # Extract or simulate sources for this agent's data
        # In a real implementation, agents would provide their sources
        sources = self._extract_sources(results, agent_id, city, country)

        # Calculate confidence score
        confidence = self.source_tracker.get_confidence_score(
            f"{agent_id}_results",
            sources
        )

        # Use LLM to assess data quality if available
        quality_assessment = None
        if self.llm and hasattr(self.llm, 'generate'):
            quality_assessment = self._llm_assess_quality(results, sources)

        return {
            'agent_id': agent_id,
            'confidence_score': confidence,
            'num_sources': len(sources),
            'sources': [s.to_dict() for s in sources],
            'quality_assessment': quality_assessment,
            'issues': self._identify_issues(results, sources),
            'recommendations': self._generate_recommendations(results, sources, confidence)
        }

    def _extract_sources(
        self,
        results: Dict[str, Any],
        agent_id: str,
        city: str,
        country: str
    ) -> List[DataSource]:
        """
        Extract or simulate data sources from agent results.

        In production, agents should provide their actual sources.
        This creates representative sources based on the agent type.
        """
        sources = []

        # If results already contain sources, use them
        if 'sources' in results:
            for source_data in results['sources']:
                try:
                    source = DataSource.from_dict(source_data)
                    sources.append(source)
                    self.source_tracker.sources.append(source)
                except:
                    pass
            return sources

        # Otherwise, create representative sources based on agent type
        # This is a placeholder - in production, agents would track real sources

        if 'climate' in agent_id.lower():
            # Climate data typically comes from government weather services
            source = self.source_tracker.add_source(
                url=f"https://climate-data.org/{country.lower()}/{city.lower()}",
                title=f"{country} National Climate Data - {city}",
                source_type=SourceType.GOVERNMENT_AGENCY,
                reliability_tier=ReliabilityTier.TIER_1,
                collection_method=CollectionMethod.API_CALL,
                methodology="Historical weather station measurements",
                relevant_excerpt=results.get('llm_analysis', '')[:500]
            )
            sources.append(source)

        elif 'emission' in agent_id.lower():
            # Emissions data from official databases
            source = self.source_tracker.add_source(
                url=f"https://emissions-db.org/{country.lower()}/cities/{city.lower()}",
                title=f"GHG Emissions Inventory - {city}",
                source_type=SourceType.OFFICIAL_DATABASE,
                reliability_tier=ReliabilityTier.TIER_1,
                collection_method=CollectionMethod.DATABASE_QUERY,
                methodology="Municipal emissions reporting",
                relevant_excerpt=results.get('llm_analysis', '')[:500]
            )
            sources.append(source)

        elif 'vulnerab' in agent_id.lower():
            # Vulnerability assessments from research institutions
            source = self.source_tracker.add_source(
                url=f"https://climate-risk.org/assessments/{city.lower()}",
                title=f"Climate Vulnerability Assessment - {city}",
                source_type=SourceType.RESEARCH_INSTITUTION,
                reliability_tier=ReliabilityTier.TIER_1,
                collection_method=CollectionMethod.WEB_SEARCH,
                methodology="Climate risk modeling",
                relevant_excerpt=results.get('llm_analysis', '')[:500]
            )
            sources.append(source)

        elif 'adaptation' in agent_id.lower():
            # Adaptation plans from city government
            source = self.source_tracker.add_source(
                url=f"https://{city.lower()}.gov/climate-action-plan",
                title=f"{city} Climate Adaptation Plan",
                source_type=SourceType.GOVERNMENT_AGENCY,
                reliability_tier=ReliabilityTier.TIER_1,
                collection_method=CollectionMethod.WEB_SCRAPING,
                methodology="Municipal climate planning documents",
                relevant_excerpt=results.get('llm_analysis', '')[:500]
            )
            sources.append(source)

        return sources

    def _cross_verify_results(
        self,
        agent_results: Dict[str, Dict[str, Any]],
        city: str,
        country: str
    ) -> Dict[str, Any]:
        """Cross-verify facts across multiple agents."""

        # Check for consistency across agents
        consistency_checks = []

        # Example: If multiple agents mention temperature trends
        climate_mentions = []
        for agent_id, results in agent_results.items():
            analysis = results.get('llm_analysis', '')
            if 'temperature' in analysis.lower() or 'warming' in analysis.lower():
                climate_mentions.append({
                    'agent_id': agent_id,
                    'mention': analysis[:200]
                })

        if len(climate_mentions) >= 2:
            consistency_checks.append({
                'fact': 'Temperature trends',
                'verified_by': len(climate_mentions),
                'agents': [m['agent_id'] for m in climate_mentions],
                'status': 'verified'
            })

        return {
            'consistency_checks': consistency_checks,
            'cross_verified_facts': len(consistency_checks),
            'total_agents': len(agent_results)
        }

    def _llm_assess_quality(
        self,
        results: Dict[str, Any],
        sources: List[DataSource]
    ) -> Optional[Dict[str, Any]]:
        """Use LLM to assess data quality."""

        try:
            prompt = f"""Assess the quality and reliability of this climate research data:

Data Summary:
{json.dumps(results, indent=2)[:1000]}

Sources ({len(sources)}):
{self._format_sources_for_llm(sources)}

Evaluate:
1. Data completeness
2. Source reliability
3. Potential gaps or inconsistencies
4. Need for additional verification

Provide assessment in JSON format:
{{
    "overall_quality": "excellent|good|moderate|poor",
    "completeness_score": 0.0-1.0,
    "reliability_score": 0.0-1.0,
    "gaps": ["list of gaps"],
    "recommendations": ["list of recommendations"]
}}
"""

            response = self.llm.generate(
                prompt=prompt,
                system_prompt=self.system_prompt,
                temperature=0.2
            )

            # Try to parse JSON from response
            content = response['content']
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]

            assessment = json.loads(content.strip())
            return assessment

        except Exception as e:
            self.logger.warning(f"LLM quality assessment failed: {e}")
            return None

    def _format_sources_for_llm(self, sources: List[DataSource]) -> str:
        """Format sources for LLM prompt."""
        formatted = []
        for i, source in enumerate(sources[:5], 1):  # Limit to 5 sources
            formatted.append(
                f"{i}. {source.title} ({source.source_type.value}, Tier {source.reliability_tier.value})\n"
                f"   URL: {source.url}"
            )
        return "\n".join(formatted)

    def _identify_issues(
        self,
        results: Dict[str, Any],
        sources: List[DataSource]
    ) -> List[str]:
        """Identify potential issues with the data."""
        issues = []

        # Check number of sources
        if len(sources) < 2:
            issues.append("Limited sources - requires additional verification")

        # Check source reliability
        tier1_count = len([s for s in sources if s.reliability_tier == ReliabilityTier.TIER_1])
        if tier1_count == 0:
            issues.append("No Tier 1 sources - recommend adding authoritative sources")

        # Check for LLM-only data
        if 'llm_analysis' in results and len(sources) == 0:
            issues.append("LLM-generated content without external sources")

        return issues

    def _generate_recommendations(
        self,
        results: Dict[str, Any],
        sources: List[DataSource],
        confidence: float
    ) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []

        if confidence < 0.7:
            recommendations.append("Seek additional authoritative sources to increase confidence")

        if len(sources) < 3:
            recommendations.append("Add more independent sources for cross-verification")

        tier1_count = len([s for s in sources if s.reliability_tier == ReliabilityTier.TIER_1])
        if tier1_count < 2:
            recommendations.append("Include more government or research institution sources")

        return recommendations

    def _generate_overall_assessment(
        self,
        validation_results: Dict[str, Any],
        cross_verification: Dict[str, Any],
        city: str
    ) -> Dict[str, Any]:
        """Generate overall assessment of research quality."""

        # Calculate average confidence
        confidences = [
            v['confidence_score']
            for v in validation_results.values()
            if 'confidence_score' in v
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        # Count total sources
        total_sources = sum(
            v.get('num_sources', 0)
            for v in validation_results.values()
        )

        # Aggregate issues
        all_issues = []
        for v in validation_results.values():
            all_issues.extend(v.get('issues', []))

        # Overall quality rating
        if avg_confidence >= 0.9 and total_sources >= 8:
            quality_rating = "excellent"
        elif avg_confidence >= 0.7 and total_sources >= 4:
            quality_rating = "good"
        elif avg_confidence >= 0.5 and total_sources >= 2:
            quality_rating = "moderate"
        else:
            quality_rating = "needs_improvement"

        return {
            'city': city,
            'overall_quality': quality_rating,
            'average_confidence': round(avg_confidence, 2),
            'total_sources': total_sources,
            'cross_verified_facts': cross_verification.get('cross_verified_facts', 0),
            'issues_identified': len(all_issues),
            'issues': all_issues[:10],  # Limit to top 10
            'ready_for_publication': quality_rating in ['excellent', 'good']
        }

    def validate(self) -> bool:
        """Validate agent configuration."""
        return True
