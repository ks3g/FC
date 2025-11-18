"""
State management for agents and orchestrators.
"""

from typing import Any, Dict, Optional
from pathlib import Path
from datetime import datetime
import sys

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent.parent))
from utils import file_opener


class StateManager:
    """
    Manages persistent state for agents and orchestrators.

    Saves and loads state to/from JSON files.
    """

    def __init__(self, storage_dir: str = "data"):
        """
        Initialize state manager.

        Args:
            storage_dir: Directory to store state files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_agent_state(self, agent_id: str, state: Dict[str, Any]) -> bool:
        """
        Save agent state to file.

        Args:
            agent_id: Agent identifier
            state: State dictionary

        Returns:
            True if successful
        """
        file_path = self.storage_dir / f"agent_{agent_id}.json"
        state['saved_at'] = datetime.now().isoformat()
        return file_opener.write_json(file_path, state)

    def load_agent_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Load agent state from file.

        Args:
            agent_id: Agent identifier

        Returns:
            State dictionary or None if not found
        """
        file_path = self.storage_dir / f"agent_{agent_id}.json"
        return file_opener.read_json(file_path)

    def save_research_results(self, research_id: str, results: Dict[str, Any]) -> bool:
        """
        Save research results.

        Args:
            research_id: Research identifier (e.g., city name)
            results: Research results dictionary

        Returns:
            True if successful
        """
        file_path = self.storage_dir / f"research_{research_id}.json"
        results['saved_at'] = datetime.now().isoformat()
        return file_opener.write_json(file_path, results)

    def load_research_results(self, research_id: str) -> Optional[Dict[str, Any]]:
        """
        Load research results.

        Args:
            research_id: Research identifier

        Returns:
            Results dictionary or None if not found
        """
        file_path = self.storage_dir / f"research_{research_id}.json"
        return file_opener.read_json(file_path)

    def save_validation_report(self, research_id: str, report: Dict[str, Any]) -> bool:
        """
        Save validation report.

        Args:
            research_id: Research identifier
            report: Validation report

        Returns:
            True if successful
        """
        file_path = self.storage_dir / f"validation_{research_id}.json"
        report['saved_at'] = datetime.now().isoformat()
        return file_opener.write_json(file_path, report)

    def list_research_results(self) -> list:
        """
        List all available research results.

        Returns:
            List of research IDs
        """
        pattern = self.storage_dir / "research_*.json"
        files = list(self.storage_dir.glob("research_*.json"))
        return [f.stem.replace('research_', '') for f in files]

    def delete_research_results(self, research_id: str) -> bool:
        """
        Delete research results.

        Args:
            research_id: Research identifier

        Returns:
            True if successful
        """
        file_path = self.storage_dir / f"research_{research_id}.json"
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Error deleting results: {e}")
            return False

    def export_to_csv(self, research_id: str, output_path: str) -> bool:
        """
        Export research results to CSV.

        Args:
            research_id: Research identifier
            output_path: Path to output CSV file

        Returns:
            True if successful
        """
        results = self.load_research_results(research_id)
        if not results:
            return False

        # Flatten nested data for CSV export
        flat_data = []
        for key, value in results.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    flat_data.append({
                        'category': key,
                        'metric': sub_key,
                        'value': str(sub_value)
                    })
            else:
                flat_data.append({
                    'category': 'general',
                    'metric': key,
                    'value': str(value)
                })

        return file_opener.write_csv(output_path, flat_data)
