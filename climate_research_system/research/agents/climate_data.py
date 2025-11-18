"""
Climate Data Agent - Collects historical and projected climate data.
"""

from typing import Any, Dict, List
from datetime import datetime
import sys
from pathlib import Path

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent.parent))
from core.agent_base import Agent, AgentStatus


class ClimateDataAgent(Agent):
    """
    Agent responsible for collecting climate data.

    Collects:
    - Historical temperature data
    - Precipitation patterns
    - Extreme weather events
    - Climate projections

    Sources (to be implemented):
    - NOAA Climate Data Online
    - World Bank Climate Portal
    - Local meteorological services
    - OpenWeatherMap API
    """

    def __init__(self, agent_id: str = "climate_data_agent", config: Dict = None):
        """
        Initialize Climate Data Agent.

        Args:
            agent_id: Unique identifier
            config: Configuration with API keys, data sources, etc.
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

    def execute(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute climate data collection.

        Args:
            task: Dictionary with 'city', 'country', 'years' (optional)

        Returns:
            Climate data dictionary
        """
        city = task.get('city')
        country = task.get('country')
        years = task.get('years', 30)  # Default to 30-year climate normal

        if not city or not country:
            raise ValueError("Both 'city' and 'country' are required")

        self.logger.info(f"Collecting climate data for {city}, {country}")

        # TODO: Replace with real API calls
        # For now, return mock data structure
        results = {
            'city': city,
            'country': country,
            'data_period': f"{datetime.now().year - years}-{datetime.now().year}",
            'collected_at': datetime.now().isoformat(),
            'metrics': self._collect_climate_metrics(city, country, years),
            'sources': self._get_data_sources(),
            'confidence_score': 0.0,  # Will be calculated by validator
            'notes': []
        }

        # Validate collected data
        validation = self.validate(results['metrics'])
        if not validation['valid']:
            results['notes'].extend(validation['errors'])
            self.logger.warning(f"Data validation warnings: {validation['errors']}")

        return results

    def _collect_climate_metrics(self, city: str, country: str, years: int) -> Dict[str, Any]:
        """
        Collect actual climate metrics.

        TODO: Implement real data collection from:
        - NOAA API: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
        - World Bank API: https://datahelpdesk.worldbank.org/knowledgebase/articles/902061
        - OpenWeatherMap: https://openweathermap.org/api

        Args:
            city: City name
            country: Country name
            years: Number of years of historical data

        Returns:
            Climate metrics dictionary
        """
        # MOCK DATA - Replace with real API calls
        self.logger.info(f"[MOCK] Fetching climate data from APIs...")

        # Example structure for real implementation:
        # temperature_data = self._fetch_noaa_temperature(city, country, years)
        # precipitation_data = self._fetch_precipitation(city, country, years)
        # extreme_events = self._fetch_extreme_events(city, country, years)

        return {
            'temperature_avg': None,  # TODO: Fetch from API
            'temperature_min': None,  # TODO: Fetch from API
            'temperature_max': None,  # TODO: Fetch from API
            'precipitation_annual': None,  # TODO: Fetch from API
            'precipitation_seasonal': None,  # TODO: Fetch from API
            'extreme_events': {
                'heatwaves': None,  # TODO: Fetch from API
                'floods': None,
                'droughts': None,
                'storms': None
            },
            'climate_zone': None,  # TODO: Determine from data
            'trends': {
                'temperature_trend': None,  # TODO: Calculate trend
                'precipitation_trend': None
            }
        }

    def _get_data_sources(self) -> List[Dict[str, str]]:
        """
        Get list of data sources used.

        Returns:
            List of source dictionaries
        """
        return [
            {
                'name': 'NOAA Climate Data Online',
                'url': 'https://www.ncdc.noaa.gov/cdo-web/',
                'credibility': 'Tier 1',
                'accessed': datetime.now().isoformat()
            },
            {
                'name': 'World Bank Climate Portal',
                'url': 'https://climateknowledgeportal.worldbank.org/',
                'credibility': 'Tier 1',
                'accessed': datetime.now().isoformat()
            },
            {
                'name': 'OpenWeatherMap',
                'url': 'https://openweathermap.org/',
                'credibility': 'Tier 2',
                'accessed': datetime.now().isoformat()
            }
        ]

    def validate(self, data: Any) -> Dict[str, Any]:
        """
        Validate climate data.

        Checks:
        - Required metrics present
        - Data ranges reasonable
        - Consistency checks

        Args:
            data: Climate metrics dictionary

        Returns:
            Validation result
        """
        errors = []
        warnings = []

        # Check required metrics
        for metric in self.required_metrics:
            if metric not in data or data[metric] is None:
                errors.append(f"Missing required metric: {metric}")

        # Temperature range validation
        if data.get('temperature_avg') is not None:
            temp = data['temperature_avg']
            if temp < -50 or temp > 50:
                warnings.append(f"Temperature {temp}°C outside typical range")

        # Precipitation validation
        if data.get('precipitation_annual') is not None:
            precip = data['precipitation_annual']
            if precip < 0:
                errors.append("Precipitation cannot be negative")
            elif precip > 10000:  # mm per year
                warnings.append(f"Very high precipitation: {precip}mm/year")

        # Check data consistency
        if (data.get('temperature_min') is not None and
            data.get('temperature_max') is not None):
            if data['temperature_min'] > data['temperature_max']:
                errors.append("Min temperature exceeds max temperature")

        is_valid = len(errors) == 0

        return {
            'valid': is_valid,
            'errors': errors,
            'warnings': warnings,
            'completeness': self._calculate_completeness(data),
            'validated_at': datetime.now().isoformat()
        }

    def _calculate_completeness(self, data: Dict) -> float:
        """
        Calculate data completeness percentage.

        Args:
            data: Climate metrics dictionary

        Returns:
            Completeness percentage (0.0 to 1.0)
        """
        total_metrics = len(self.required_metrics)
        present_metrics = sum(
            1 for metric in self.required_metrics
            if data.get(metric) is not None
        )
        return present_metrics / total_metrics if total_metrics > 0 else 0.0

    # Placeholder methods for real API integration
    def _fetch_noaa_temperature(self, city: str, country: str, years: int) -> Dict:
        """TODO: Implement NOAA API call for temperature data."""
        pass

    def _fetch_precipitation(self, city: str, country: str, years: int) -> Dict:
        """TODO: Implement precipitation data fetch."""
        pass

    def _fetch_extreme_events(self, city: str, country: str, years: int) -> List:
        """TODO: Implement extreme events data fetch."""
        pass
