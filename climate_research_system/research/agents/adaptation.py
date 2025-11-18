"""
LLM-Powered Adaptation Agent

Analyzes climate adaptation strategies and measures for cities.
"""

from typing import Any, Dict
from datetime import datetime
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent


class AdaptationAgent(Agent):
    """
    LLM-powered agent for climate adaptation analysis.

    Analyzes:
    - Climate action plans and strategies
    - Implemented adaptation measures
    - Green infrastructure
    - Policy and governance
    - Budget and financing
    """

    def __init__(self, agent_id: str = "adaptation_001", config: Dict = None):
        super().__init__(agent_id, "Adaptation Agent", config)

        self.system_prompt = """You are a climate adaptation and urban resilience expert.

Analyze cities' climate adaptation efforts including:
1. Strategic planning (climate action plans)
2. Nature-based solutions and green infrastructure
3. Gray infrastructure and engineering solutions
4. Social and community-based adaptation
5. Policy and governance frameworks
6. Finance and implementation

Provide practical, evidence-based recommendations for strengthening climate resilience."""

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        city = task.get('city')
        country = task.get('country')

        self.logger.info(f"Analyzing climate adaptation for {city}, {country} with LLM")

        prompt = f"""Analyze the climate adaptation strategies and measures for {city}, {country}.

**Strategic Planning:**

**Climate Action Plan:**
- Existence and scope of climate action/adaptation plan
- Vision and goals
- Timeline and milestones
- Integration with urban planning

**Risk Assessment:**
- Climate risk analysis completed
- Vulnerability mapping
- Priority hazards identified

**Targets and Metrics:**
- Adaptation goals and indicators
- Progress tracking mechanisms
- Reporting frameworks

**Nature-Based Solutions:**

**Green Infrastructure:**
- Urban forests and tree canopy coverage
- Parks and green spaces (acres, % of city area)
- Green roofs and walls
- Bioswales and rain gardens

**Blue Infrastructure:**
- Restored wetlands and waterways
- Permeable surfaces
- Urban water retention
- Coastal restoration (if applicable)

**Ecosystem Services:**
- Cooling effects quantified
- Stormwater management capacity
- Air quality improvements
- Biodiversity benefits

**Gray Infrastructure:**

**Flood Protection:**
- Levees, flood walls, dams
- Stormwater systems and drainage
- Pump stations
- Flood-proofing buildings

**Heat Management:**
- Cool roofs and pavements
- District cooling systems
- Building insulation standards

**Water Infrastructure:**
- Water storage capacity
- Desalination (if applicable)
- Water recycling and reuse

**Social Adaptation:**

**Community Programs:**
- Cooling centers locations and capacity
- Heat action plans
- Emergency preparedness training
- Vulnerable population support

**Health Systems:**
- Climate health early warning
- Vector-borne disease surveillance
- Mental health support

**Awareness and Education:**
- Public information campaigns
- Community engagement
- Climate literacy programs

**Policy and Governance:**

**Regulatory Framework:**
- Building codes for climate resilience
- Zoning for flood/heat risk
- Environmental regulations
- Land use policies

**Institutional Capacity:**
- Dedicated climate office/staff
- Inter-departmental coordination
- Stakeholder engagement
- Science-policy integration

**Finance and Implementation:**

**Budget Allocation:**
- Climate adaptation spending (annual)
- % of city budget
- Funding sources

**Financing Mechanisms:**
- Green bonds
- Climate funds
- International finance (GCF, etc.)
- Public-private partnerships

**Implementation Status:**
- Projects completed
- Projects in progress
- Pipeline and planned projects

**Barriers and Challenges:**
- Resource constraints
- Political will
- Technical capacity
- Data and information gaps
- Coordination challenges

**Best Practices and Innovations:**
- Unique or exemplary initiatives
- Scalable solutions
- Lessons learned

**Recommendations:**

**Priority Actions (1-3 years):**
- Quick wins
- Urgent vulnerabilities to address

**Medium-term (3-10 years):**
- Strategic investments
- Capacity building

**Long-term (10+ years):**
- Transformative changes
- System-wide resilience

**Key Enablers:**
- Policy reforms needed
- Finance mobilization
- Partnership opportunities
- Technology adoption

Provide comprehensive, actionable analysis based on best practices in climate adaptation and urban resilience."""

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
            'adaptation_assessment': {
                'analysis': llm_response['content']
            },
            'sources': [{
                'name': 'LLM Adaptation Analysis',
                'model': llm_response['model'],
                'credibility': 'AI-Generated',
                'note': 'Based on climate adaptation frameworks and urban resilience best practices'
            }]
        }

        return results

    def validate(self, data: Any) -> Dict[str, Any]:
        errors = []
        analysis = data.get('llm_analysis', '')

        if not analysis:
            errors.append("No adaptation analysis generated")

        key_terms = ['adaptation', 'resilience', 'infrastructure', 'plan', 'strategy']
        present_terms = [term for term in key_terms if term in analysis.lower()]

        if len(present_terms) < 3:
            errors.append("Analysis missing key adaptation concepts")

        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'completeness': 0.85 if analysis else 0.0
        }
