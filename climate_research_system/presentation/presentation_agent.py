"""
Presentation Agent

LLM-powered agent that synthesizes all research data into a comprehensive
presentation/report. Runs after all data collection and validation is complete.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path
import json
from enum import Enum

sys.path.append(str(Path(__file__).parent.parent))
from core.agent_base import Agent, AgentStatus
from core.message import Message, MessageType


class EnumJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles Enum types."""
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        if hasattr(obj, '__dict__'):
            # Convert objects to dict, handling Enums
            return {k: v.value if isinstance(v, Enum) else v
                    for k, v in obj.__dict__.items()
                    if not k.startswith('_')}
        return super().default(obj)


class PresentationAgent(Agent):
    """
    LLM-powered agent for creating final presentations and reports.

    Responsibilities:
    - Synthesize data from all agents into cohesive report
    - Generate executive summary
    - Create actionable recommendations
    - Format findings professionally
    - Highlight key insights and trends
    - Create data visualizations (future)

    This agent runs AFTER all data collection and validation is complete.
    """

    def __init__(
        self,
        agent_id: str = "presentation_001",
        name: str = "Presentation Agent",
        config: Optional[Dict] = None
    ):
        super().__init__(agent_id, name, config)
        # LLM client is initialized by Agent base class as self.llm
        self.logger.info(f"Initialized Presentation Agent")

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create comprehensive presentation from all agent results.

        Args:
            task: Contains city, country, agent_results, validation_report

        Returns:
            Presentation with executive summary, findings, recommendations
        """
        city = task.get('city')
        country = task.get('country')
        agent_results = task.get('agent_results', {})
        validation_report = task.get('validation_report', {})

        self.logger.info(f"Creating presentation for {city}, {country}")

        # Extract all findings from agents
        all_findings = self._extract_findings(agent_results)

        # Generate executive summary
        exec_summary = self._generate_executive_summary(
            city, country, all_findings, validation_report
        )

        # Generate detailed findings section
        detailed_findings = self._generate_detailed_findings(
            city, country, all_findings
        )

        # Generate recommendations
        recommendations = self._generate_recommendations(
            city, country, all_findings, validation_report
        )

        # Generate key insights
        key_insights = self._generate_key_insights(
            city, country, all_findings
        )

        # Compile presentation
        presentation = {
            'city': city,
            'country': country,
            'generated_at': datetime.now().isoformat(),
            'executive_summary': exec_summary,
            'key_insights': key_insights,
            'detailed_findings': detailed_findings,
            'recommendations': recommendations,
            'data_quality': {
                'overall_confidence': validation_report.get('overall_confidence', 0),
                'total_sources': validation_report.get('total_sources', 0),
                'validation_status': validation_report.get('validation_status', 'unknown')
            },
            'metadata': {
                'agents_used': list(agent_results.keys()),
                'report_version': '1.0'
            }
        }

        self.logger.info("Presentation created successfully")
        return presentation

    def _extract_findings(self, agent_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and organize findings from all agents."""
        findings = {}

        for agent_id, result in agent_results.items():
            if isinstance(result, dict) and 'error' not in result:
                # Extract data from each agent
                if 'data' in result:
                    findings[agent_id] = result['data']
                elif 'findings' in result:
                    findings[agent_id] = result['findings']
                else:
                    findings[agent_id] = result

        return findings

    def _generate_executive_summary(
        self,
        city: str,
        country: str,
        findings: Dict[str, Any],
        validation_report: Dict[str, Any]
    ) -> str:
        """Generate executive summary using LLM."""

        # Build context from all findings
        context = self._build_context_summary(findings)

        prompt = f"""You are a climate research analyst preparing an executive summary.

City: {city}, {country}

Research Data Summary:
{context}

Data Quality:
- Overall Confidence: {validation_report.get('overall_confidence', 0):.1%}
- Total Sources: {validation_report.get('total_sources', 0)}
- Validation Status: {validation_report.get('validation_status', 'unknown')}

Task: Write a concise executive summary (3-4 paragraphs, ~300 words) that:
1. Provides overview of {city}'s climate situation
2. Highlights most critical findings
3. Summarizes key risks and vulnerabilities
4. Notes data quality and confidence level

Write in professional, accessible language suitable for decision-makers."""

        try:
            response = self.llm.generate(prompt, max_tokens=500)
            return response['content'].strip() if isinstance(response, dict) else response.strip()
        except Exception as e:
            self.logger.error(f"Error generating executive summary: {e}")
            return f"Executive Summary for {city}, {country}\n\nA comprehensive climate research analysis was conducted, examining multiple dimensions including climate data, emissions, vulnerabilities, and adaptation strategies. See detailed findings below."

    def _generate_detailed_findings(
        self,
        city: str,
        country: str,
        findings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate detailed findings section using LLM."""

        detailed = {}

        for agent_id, data in findings.items():
            agent_name = agent_id.replace('_', ' ').title()

            # Summarize this agent's findings
            data_str = json.dumps(data, indent=2, cls=EnumJSONEncoder) if isinstance(data, dict) else str(data)

            prompt = f"""You are a climate research analyst preparing a detailed findings section.

Agent: {agent_name}
City: {city}, {country}

Raw Data:
{data_str[:2000]}  # Limit context size

Task: Summarize the key findings from this research area in 2-3 paragraphs (~200 words):
1. What are the main findings?
2. What trends or patterns emerge?
3. What are the most significant data points?

Write in clear, professional language."""

            try:
                response = self.llm.generate(prompt, max_tokens=300)
                content = response['content'] if isinstance(response, dict) else response
                detailed[agent_name] = content.strip()
            except Exception as e:
                self.logger.error(f"Error generating findings for {agent_id}: {e}")
                detailed[agent_name] = f"Data collected from {agent_name}. See raw data for details."

        return detailed

    def _generate_recommendations(
        self,
        city: str,
        country: str,
        findings: Dict[str, Any],
        validation_report: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations using LLM."""

        context = self._build_context_summary(findings)

        prompt = f"""You are a climate adaptation strategist preparing recommendations.

City: {city}, {country}

Research Findings Summary:
{context}

Task: Generate 5-7 specific, actionable recommendations for {city}'s climate adaptation:
1. Each recommendation should be concrete and implementable
2. Prioritize based on urgency and impact
3. Consider data quality (overall confidence: {validation_report.get('overall_confidence', 0):.1%})
4. Address different time horizons (short-term, medium-term, long-term)

Format as a numbered list. Each recommendation should be 1-2 sentences."""

        try:
            response = self.llm.generate(prompt, max_tokens=500)
            content = response['content'] if isinstance(response, dict) else response
            # Parse recommendations into list
            recommendations = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and (line[0].isdigit() or line.startswith('-') or line.startswith('•')):
                    # Remove numbering/bullets
                    clean_line = line.lstrip('0123456789.-•) ').strip()
                    if clean_line:
                        recommendations.append(clean_line)
            return recommendations if recommendations else [content.strip()]
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return [
                f"Conduct comprehensive climate risk assessment for {city}",
                "Develop city-level climate adaptation strategy",
                "Strengthen climate monitoring and data collection infrastructure",
                "Engage stakeholders in climate resilience planning"
            ]

    def _generate_key_insights(
        self,
        city: str,
        country: str,
        findings: Dict[str, Any]
    ) -> List[str]:
        """Generate 3-5 key insights using LLM."""

        context = self._build_context_summary(findings)

        prompt = f"""You are a climate research analyst identifying key insights.

City: {city}, {country}

Research Findings:
{context}

Task: Identify 3-5 key insights that stand out from this research:
1. Each insight should be a significant finding or pattern
2. Focus on what's most important for decision-makers
3. Highlight unexpected findings or critical risks
4. Keep each insight to one clear sentence

Format as a bullet list."""

        try:
            response = self.llm.generate(prompt, max_tokens=300)
            content = response['content'] if isinstance(response, dict) else response
            # Parse insights into list
            insights = []
            for line in content.strip().split('\n'):
                line = line.strip()
                if line and (line.startswith('-') or line.startswith('•') or line.startswith('*')):
                    clean_line = line.lstrip('-•* ').strip()
                    if clean_line:
                        insights.append(clean_line)
            return insights if insights else [content.strip()]
        except Exception as e:
            self.logger.error(f"Error generating key insights: {e}")
            return [
                f"{city} faces multiple climate-related challenges requiring coordinated response",
                "Data quality varies across sources; additional monitoring recommended",
                "Near-term adaptation actions are urgently needed"
            ]

    def _build_context_summary(self, findings: Dict[str, Any]) -> str:
        """Build a concise context summary from all findings."""
        summary_parts = []

        for agent_id, data in findings.items():
            agent_name = agent_id.replace('_', ' ').title()

            # Extract key information
            if isinstance(data, dict):
                # Try to get summary-level info
                if 'summary' in data:
                    summary_parts.append(f"{agent_name}: {data['summary']}")
                elif 'findings' in data and isinstance(data['findings'], list):
                    summary_parts.append(f"{agent_name}: {len(data['findings'])} findings")
                else:
                    # Just note we have data
                    summary_parts.append(f"{agent_name}: Data collected")
            else:
                summary_parts.append(f"{agent_name}: {str(data)[:100]}")

        return '\n'.join(summary_parts)

    def validate(self, data: Dict[str, Any]) -> bool:
        """
        Validate presentation data.

        Args:
            data: Presentation data to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        required_fields = ['city', 'country', 'executive_summary', 'recommendations']

        for field in required_fields:
            if field not in data or not data[field]:
                self.logger.warning(f"Missing required field: {field}")
                return False

        return True
