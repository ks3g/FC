"""
LLM-Powered Emissions Agent

Analyzes greenhouse gas emissions and carbon footprints for cities.
"""

from typing import Any, Dict
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent


class EmissionsAgent(Agent):
    """
    LLM-powered agent for analyzing city greenhouse gas emissions.

    Analyzes:
    - Total GHG emissions inventory
    - Emissions by sector (transport, buildings, industry, waste)
    - Per capita emissions
    - Trends and reduction targets
    - Mitigation strategies
    """

    def __init__(self, agent_id: str = "emissions_001", config: Dict = None):
        super().__init__(agent_id, "Emissions Agent", config)

        self.system_prompt = """You are a carbon emissions and climate mitigation expert.

Analyze city greenhouse gas emissions with focus on:
1. Total emissions inventory (CO2 equivalent)
2. Sector-by-sector breakdown
3. Per capita and per GDP emissions
4. Historical trends and projections
5. Reduction targets and progress
6. Mitigation strategies and their effectiveness

Provide quantitative estimates based on city size, economic profile, and typical emissions patterns."""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        city = task.get('city')
        country = task.get('country')

        self.logger.info(f"Analyzing emissions for {city}, {country} with LLM")

        prompt = f"""Analyze the greenhouse gas emissions profile for {city}, {country}.

**Required Analysis:**

**Emissions Inventory:**
- Estimated total annual GHG emissions (tons CO2e)
- Scope 1, 2, and 3 emissions categories
- Historical emission trends (last 10-20 years)

**Sector Breakdown:**
- Transportation (% of total, tons CO2e)
  - Road transport, public transit, aviation
- Buildings (% of total, tons CO2e)
  - Residential, commercial, heating/cooling
- Industry & Manufacturing (% of total, tons CO2e)
- Waste Management (% of total, tons CO2e)
- Agriculture (if applicable)
- Other sectors

**Per Capita Metrics:**
- Emissions per capita (tons CO2e/person/year)
- Comparison to national and global averages
- Trends over time

**Emissions Intensity:**
- Emissions per unit GDP
- Energy intensity trends

**Climate Commitments:**
- Emission reduction targets (e.g., 50% by 2030)
- Paris Agreement alignment
- Net-zero commitments and timeline
- Progress toward targets

**Mitigation Strategies:**
- Current decarbonization efforts
- Renewable energy adoption
- Transportation electrification
- Building efficiency programs
- Carbon pricing or emissions trading
- Nature-based solutions

**Key Challenges:**
- Main sources of emissions growth
- Hard-to-abate sectors
- Political and economic barriers

**Recommendations:**
- Priority mitigation actions
- Quick wins and long-term strategies
- Policy and investment needs

Base analysis on:
- City's population and economic profile
- Typical emissions patterns for similar cities
- Regional and national climate policies
- Published climate action plans if available"""

        llm_response = self.llm.generate(
            prompt=prompt,
            system_prompt=self.system_prompt,
            temperature=0.3
        )

        results = {
            'city': city,
            'country': country,
            'collected_at': datetime.now().isoformat(),
            'llm_analysis': llm_response['content'],
            'llm_model': llm_response['model'],
            'tokens_used': llm_response.get('tokens_used', 0),
            'emissions_data': {
                'analysis': llm_response['content']
            },
            'sources': [{
                'name': 'LLM Emissions Analysis',
                'model': llm_response['model'],
                'credibility': 'AI-Generated',
                'note': 'Based on climate science and emissions data patterns'
            }]
        }

        return results

    def validate(self, data: Any) -> Dict[str, Any]:
        errors = []
        analysis = data.get('llm_analysis', '')

        if not analysis:
            errors.append("No emissions analysis generated")

        key_terms = ['emissions', 'ghg', 'co2', 'carbon', 'sector']
        if not any(term in analysis.lower() for term in key_terms):
            errors.append("Analysis missing key emissions terminology")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'completeness': 0.75 if analysis else 0.0
        }
