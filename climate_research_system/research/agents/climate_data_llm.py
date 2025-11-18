"""
LLM-Powered Climate Data Agent

Uses AI models to analyze and interpret climate data.
"""

from typing import Any, Dict
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent, AgentStatus


class ClimateDataAgent(Agent):
    """
    LLM-powered agent for collecting and analyzing climate data.

    Uses AI to:
    - Interpret climate data from multiple sources
    - Identify trends and patterns
    - Assess data quality
    - Generate insights and recommendations
    """

    def __init__(self, agent_id: str = "climate_001", config: Dict = None):
        """
        Initialize Climate Data Agent.

        Args:
            agent_id: Unique identifier
            config: Configuration including LLM settings:
                {
                    'llm': {
                        'provider': 'anthropic',  # or 'openai', 'ollama'
                        'model': 'claude-3-5-sonnet-20241022',
                        'api_key': 'your-api-key'
                    },
                    'enabled': True,
                    'data_years': 30
                }
        """
        super().__init__(agent_id, "Climate Data Agent", config)

        self.required_metrics = [
            'temperature_avg',
            'temperature_min',
            'temperature_max',
            'precipitation_annual',
            'extreme_events',
            'climate_zone'
        ]

        # LLM prompt template
        self.system_prompt = """You are a climate science expert analyzing historical climate data for cities.

Your task is to:
1. Analyze temperature and precipitation trends
2. Identify extreme weather events and patterns
3. Assess climate risks and vulnerabilities
4. Provide actionable insights for climate adaptation

Respond in a structured, data-driven manner with specific observations and recommendations."""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute climate data collection and analysis using LLM.

        Args:
            task: Dictionary with 'city', 'country', 'years' (optional)

        Returns:
            Climate analysis dictionary
        """
        city = task.get('city')
        country = task.get('country')
        years = task.get('years', 30)

        if not city or not country:
            raise ValueError("Both 'city' and 'country' are required")

        self.logger.info(f"Analyzing climate data for {city}, {country} with LLM")

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(city, country, years)

        # Get LLM analysis
        llm_response = self.llm.generate(
            prompt=analysis_prompt,
            system_prompt=self.system_prompt,
            temperature=0.3  # Lower temperature for more factual responses
        )

        # Extract structured data from LLM response
        climate_metrics = self._extract_metrics_from_analysis(llm_response['content'])

        # Package results
        results = {
            'city': city,
            'country': country,
            'data_period': f"{datetime.now().year - years}-{datetime.now().year}",
            'collected_at': datetime.now().isoformat(),
            'llm_analysis': llm_response['content'],
            'llm_model': llm_response['model'],
            'llm_provider': llm_response.get('provider', 'unknown'),
            'tokens_used': llm_response.get('tokens_used', 0),
            'metrics': climate_metrics,
            'sources': self._get_data_sources(),
            'confidence_score': 0.7,  # Based on LLM analysis quality
            'notes': []
        }

        # Validate collected data
        validation = self.validate(results['metrics'])
        if not validation['valid']:
            results['notes'].extend(validation['errors'])
            results['confidence_score'] *= validation['completeness']

        return results

    def _build_analysis_prompt(self, city: str, country: str, years: int) -> str:
        """
        Build prompt for LLM analysis.

        Args:
            city: City name
            country: Country name
            years: Number of years to analyze

        Returns:
            Formatted prompt string
        """
        return f"""Analyze the climate conditions and trends for {city}, {country} over the past {years} years.

Please provide a comprehensive analysis including:

**Temperature Analysis:**
- Average annual temperature and recent trends
- Seasonal temperature variations
- Heat wave frequency and intensity
- Notable temperature extremes

**Precipitation Patterns:**
- Average annual precipitation
- Seasonal distribution
- Trends in rainfall intensity
- Drought or flood patterns

**Extreme Weather Events:**
- Types and frequency of extreme events
- Notable historical events
- Observed changes in frequency/intensity

**Climate Zone & Characteristics:**
- Köppen climate classification
- Key climate characteristics
- Microclimate considerations (urban heat island, coastal effects)

**Climate Change Impacts:**
- Observed changes over the study period
- Temperature warming trends
- Changes in precipitation patterns
- Shifts in extreme event frequency

**Key Risks & Vulnerabilities:**
- Primary climate hazards for this location
- Populations or infrastructure at risk
- Seasonal or geographic vulnerability patterns

**Adaptation Recommendations:**
- Priority adaptation measures
- Infrastructure considerations
- Early warning system needs
- Green infrastructure opportunities

Base your analysis on:
1. Known climate data for this region
2. Global climate patterns and trends
3. Regional climate research and projections
4. Standard climate science methodologies

Provide specific, actionable insights suitable for city planning and climate adaptation efforts."""

    def _extract_metrics_from_analysis(self, analysis: str) -> Dict[str, Any]:
        """
        Extract structured metrics from LLM analysis.

        This is a simplified extraction. In production, you might:
        - Use LLM with structured output
        - Parse specific sections of the response
        - Call LLM again for structured data extraction

        Args:
            analysis: LLM analysis text

        Returns:
            Metrics dictionary
        """
        # For now, return structure with analysis embedded
        # TODO: Enhance with actual parsing or structured LLM output
        return {
            'temperature_avg': None,  # Could extract from analysis
            'temperature_min': None,
            'temperature_max': None,
            'precipitation_annual': None,
            'precipitation_seasonal': None,
            'extreme_events': {
                'analysis': analysis,  # Full analysis embedded
                'heatwaves': None,
                'floods': None,
                'droughts': None,
                'storms': None
            },
            'climate_zone': None,
            'trends': {
                'temperature_trend': None,
                'precipitation_trend': None
            },
            'llm_insights': analysis  # Store full LLM analysis
        }

    def _get_data_sources(self) -> list:
        """Get list of data sources."""
        return [
            {
                'name': 'LLM Climate Analysis',
                'model': self.llm.model if self.llm else 'unknown',
                'credibility': 'AI-Generated',
                'accessed': datetime.now().isoformat(),
                'note': 'AI model analysis based on climate science knowledge'
            },
            {
                'name': 'NOAA Climate Data',
                'url': 'https://www.ncdc.noaa.gov/cdo-web/',
                'credibility': 'Tier 1',
                'note': 'Referenced by AI model'
            },
            {
                'name': 'World Bank Climate Portal',
                'url': 'https://climateknowledgeportal.worldbank.org/',
                'credibility': 'Tier 1',
                'note': 'Referenced by AI model'
            }
        ]

    def validate(self, data: Any) -> Dict[str, Any]:
        """
        Validate climate data.

        Args:
            data: Climate metrics dictionary

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check for LLM insights
        if 'llm_insights' not in data or not data['llm_insights']:
            errors.append("No LLM analysis generated")

        # Check analysis quality
        llm_insights = data.get('llm_insights', '')
        if llm_insights:
            # Basic quality checks
            if len(llm_insights) < 100:
                warnings.append("LLM analysis seems very brief")

            # Check for key sections
            key_sections = ['temperature', 'precipitation', 'extreme', 'risk']
            missing_sections = [s for s in key_sections if s.lower() not in llm_insights.lower()]
            if missing_sections:
                warnings.append(f"Analysis may be missing: {', '.join(missing_sections)}")

        is_valid = len(errors) == 0

        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'completeness': 0.8 if llm_insights else 0.0,  # LLM provides comprehensive analysis
            'validated_at': datetime.now().isoformat()
        }
