"""
Source Database for Persistent Storage

Manages storage and retrieval of data sources with full provenance tracking.
"""

from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from datetime import datetime
from .source_tracker import DataSource, SourceType, ReliabilityTier, CollectionMethod


class SourceDatabase:
    """
    Persistent database for data sources.

    Stores all sources with full metadata for audit trails and reproducibility.
    """

    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize source database.

        Args:
            db_path: Path to database directory. If None, uses default.
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "data" / "sources"

        self.db_path = Path(db_path)
        self.db_path.mkdir(parents=True, exist_ok=True)

        # Database files
        self.sources_file = self.db_path / "sources.json"
        self.index_file = self.db_path / "index.json"

        # In-memory cache
        self.sources: Dict[str, DataSource] = {}
        self.index: Dict[str, Any] = {}

        # Load existing data
        self._load()

    def _load(self):
        """Load database from disk."""
        if self.sources_file.exists():
            try:
                with open(self.sources_file, 'r') as f:
                    data = json.load(f)
                    for source_id, source_data in data.items():
                        try:
                            self.sources[source_id] = DataSource.from_dict(source_data)
                        except Exception as e:
                            print(f"Warning: Failed to load source {source_id}: {e}")
            except Exception as e:
                print(f"Warning: Failed to load sources database: {e}")

        if self.index_file.exists():
            try:
                with open(self.index_file, 'r') as f:
                    self.index = json.load(f)
            except Exception as e:
                print(f"Warning: Failed to load index: {e}")
                self.index = self._build_index()
        else:
            self.index = self._build_index()

    def _save(self):
        """Save database to disk."""
        try:
            # Save sources
            sources_data = {
                source_id: source.to_dict()
                for source_id, source in self.sources.items()
            }

            with open(self.sources_file, 'w') as f:
                json.dump(sources_data, f, indent=2)

            # Save index
            with open(self.index_file, 'w') as f:
                json.dump(self.index, f, indent=2)

        except Exception as e:
            print(f"Error saving sources database: {e}")

    def _build_index(self) -> Dict[str, Any]:
        """Build index for fast lookups."""
        index = {
            'by_url': {},
            'by_type': {},
            'by_tier': {},
            'by_hash': {}
        }

        for source_id, source in self.sources.items():
            # Index by URL
            index['by_url'][source.url] = source_id

            # Index by type
            source_type = source.source_type.value
            if source_type not in index['by_type']:
                index['by_type'][source_type] = []
            index['by_type'][source_type].append(source_id)

            # Index by tier
            tier = str(source.reliability_tier.value)
            if tier not in index['by_tier']:
                index['by_tier'][tier] = []
            index['by_tier'][tier].append(source_id)

            # Index by content hash
            if source.content_hash:
                index['by_hash'][source.content_hash] = source_id

        return index

    def add_source(self, source: DataSource) -> str:
        """
        Add a source to the database.

        Args:
            source: DataSource object

        Returns:
            Source ID
        """
        # Generate unique ID
        source_id = f"src_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{len(self.sources)}"

        # Check for duplicates by URL
        existing_id = self.index.get('by_url', {}).get(source.url)
        if existing_id and existing_id in self.sources:
            # Update existing source
            source_id = existing_id

        self.sources[source_id] = source
        self.index = self._build_index()
        self._save()

        return source_id

    def get_source(self, source_id: str) -> Optional[DataSource]:
        """Get source by ID."""
        return self.sources.get(source_id)

    def get_source_by_url(self, url: str) -> Optional[DataSource]:
        """Get source by URL."""
        source_id = self.index.get('by_url', {}).get(url)
        if source_id:
            return self.sources.get(source_id)
        return None

    def get_sources_by_type(self, source_type: SourceType) -> List[DataSource]:
        """Get all sources of a specific type."""
        source_ids = self.index.get('by_type', {}).get(source_type.value, [])
        return [self.sources[sid] for sid in source_ids if sid in self.sources]

    def get_sources_by_tier(self, tier: ReliabilityTier) -> List[DataSource]:
        """Get all sources of a specific reliability tier."""
        source_ids = self.index.get('by_tier', {}).get(str(tier.value), [])
        return [self.sources[sid] for sid in source_ids if sid in self.sources]

    def get_tier1_sources(self) -> List[DataSource]:
        """Get all Tier 1 (most reliable) sources."""
        return self.get_sources_by_tier(ReliabilityTier.TIER_1)

    def search_sources(
        self,
        query: Optional[str] = None,
        source_type: Optional[SourceType] = None,
        reliability_tier: Optional[ReliabilityTier] = None,
        min_tier: Optional[int] = None
    ) -> List[DataSource]:
        """
        Search sources with filters.

        Args:
            query: Search in title and URL
            source_type: Filter by source type
            reliability_tier: Filter by exact tier
            min_tier: Minimum reliability tier (1 is best)

        Returns:
            List of matching sources
        """
        results = list(self.sources.values())

        # Filter by type
        if source_type:
            results = [s for s in results if s.source_type == source_type]

        # Filter by exact tier
        if reliability_tier:
            results = [s for s in results if s.reliability_tier == reliability_tier]

        # Filter by minimum tier (lower is better)
        if min_tier:
            results = [s for s in results if s.reliability_tier.value <= min_tier]

        # Search query
        if query:
            query_lower = query.lower()
            results = [
                s for s in results
                if query_lower in s.title.lower() or query_lower in s.url.lower()
            ]

        return results

    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        total = len(self.sources)

        by_type = {}
        by_tier = {}

        for source in self.sources.values():
            # Count by type
            stype = source.source_type.value
            by_type[stype] = by_type.get(stype, 0) + 1

            # Count by tier
            tier = source.reliability_tier.value
            by_tier[f"tier_{tier}"] = by_tier.get(f"tier_{tier}", 0) + 1

        verified_count = len([s for s in self.sources.values() if s.verified])

        return {
            'total_sources': total,
            'by_type': by_type,
            'by_tier': by_tier,
            'verified_sources': verified_count,
            'verification_rate': round(verified_count / max(1, total) * 100, 1)
        }

    def export_for_research(self, research_id: str) -> Dict[str, Any]:
        """
        Export sources for a specific research session.

        Args:
            research_id: Research session ID

        Returns:
            Dict with sources and metadata suitable for research documentation
        """
        stats = self.get_statistics()

        return {
            'research_id': research_id,
            'export_date': datetime.utcnow().isoformat(),
            'total_sources': len(self.sources),
            'statistics': stats,
            'sources': [s.to_dict() for s in self.sources.values()],
            'tier_1_sources': [s.to_dict() for s in self.get_tier1_sources()]
        }

    def clear(self):
        """Clear all sources from database."""
        self.sources = {}
        self.index = self._build_index()
        self._save()


# Global database instance
_source_db = None


def get_source_database(db_path: Optional[Path] = None) -> SourceDatabase:
    """
    Get global source database instance.

    Args:
        db_path: Optional path to database directory

    Returns:
        SourceDatabase instance
    """
    global _source_db

    if _source_db is None:
        _source_db = SourceDatabase(db_path)

    return _source_db
