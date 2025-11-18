"""
Source Tracking and Data Provenance

Ensures research integrity by tracking all data sources and enabling verification.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import hashlib
import json


class SourceType(Enum):
    """Type of data source."""
    GOVERNMENT_AGENCY = "government_agency"
    RESEARCH_INSTITUTION = "research_institution"
    PEER_REVIEWED_PAPER = "peer_reviewed_paper"
    OFFICIAL_DATABASE = "official_database"
    NGO = "ngo"
    INTERNATIONAL_ORG = "international_org"
    NEWS_ARTICLE = "news_article"
    REPORT = "report"
    WEBSITE = "website"
    API = "api"
    MANUAL_ENTRY = "manual_entry"
    UNKNOWN = "unknown"


class ReliabilityTier(Enum):
    """Source reliability tier."""
    TIER_1 = 1  # Government agencies, research institutions, peer-reviewed
    TIER_2 = 2  # NGOs, established organizations, official reports
    TIER_3 = 3  # News articles, credible websites
    TIER_4 = 4  # Blogs, unverified sources
    UNVERIFIED = 5  # Not verified


class CollectionMethod(Enum):
    """Method used to collect data."""
    WEB_SCRAPING = "web_scraping"
    API_CALL = "api_call"
    WEB_SEARCH = "web_search"
    MANUAL_ENTRY = "manual_entry"
    DATABASE_QUERY = "database_query"
    FILE_UPLOAD = "file_upload"
    LLM_GENERATED = "llm_generated"


@dataclass
class DataSource:
    """
    Represents a single data source with full provenance tracking.
    """
    url: str
    title: str
    source_type: SourceType
    reliability_tier: ReliabilityTier
    accessed_at: str  # ISO format timestamp
    collection_method: CollectionMethod

    # Optional fields
    content_hash: Optional[str] = None
    relevant_excerpt: Optional[str] = None
    author: Optional[str] = None
    publication_date: Optional[str] = None
    methodology: Optional[str] = None
    data_format: Optional[str] = None  # e.g., "JSON", "HTML", "PDF"

    # Verification
    verified: bool = False
    verified_by: Optional[str] = None  # Agent ID that verified
    verification_method: Optional[str] = None

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def create_hash(cls, content: str) -> str:
        """Create SHA-256 hash of content."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['source_type'] = self.source_type.value
        data['reliability_tier'] = self.reliability_tier.value
        data['collection_method'] = self.collection_method.value
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DataSource':
        """Create from dictionary."""
        data['source_type'] = SourceType(data['source_type'])
        data['reliability_tier'] = ReliabilityTier(data['reliability_tier'])
        data['collection_method'] = CollectionMethod(data['collection_method'])
        return cls(**data)


@dataclass
class VerificationResult:
    """Result of multi-source verification."""
    fact: str
    verified: bool
    confidence_score: float  # 0.0 to 1.0
    num_sources: int
    agreeing_sources: int
    conflicting_sources: int
    sources: List[DataSource]
    verification_method: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'fact': self.fact,
            'verified': self.verified,
            'confidence_score': self.confidence_score,
            'num_sources': self.num_sources,
            'agreeing_sources': self.agreeing_sources,
            'conflicting_sources': self.conflicting_sources,
            'sources': [s.to_dict() for s in self.sources],
            'verification_method': self.verification_method,
            'notes': self.notes
        }


class SourceTracker:
    """
    Tracks data sources and manages provenance information.
    """

    def __init__(self):
        self.sources: List[DataSource] = []
        self.verification_results: List[VerificationResult] = []

    def add_source(
        self,
        url: str,
        title: str,
        source_type: SourceType,
        reliability_tier: ReliabilityTier,
        collection_method: CollectionMethod,
        content: Optional[str] = None,
        **kwargs
    ) -> DataSource:
        """
        Add a data source with full tracking.

        Args:
            url: Source URL or identifier
            title: Source title/name
            source_type: Type of source
            reliability_tier: Reliability tier (1-5)
            collection_method: How data was collected
            content: Optional content for hashing
            **kwargs: Additional metadata

        Returns:
            DataSource object
        """
        # Create content hash if content provided
        content_hash = None
        if content:
            content_hash = DataSource.create_hash(content)

        source = DataSource(
            url=url,
            title=title,
            source_type=source_type,
            reliability_tier=reliability_tier,
            accessed_at=datetime.utcnow().isoformat(),
            collection_method=collection_method,
            content_hash=content_hash,
            **kwargs
        )

        self.sources.append(source)
        return source

    def verify_fact(
        self,
        fact: str,
        sources: List[DataSource],
        verification_method: str = "multi_source"
    ) -> VerificationResult:
        """
        Verify a fact across multiple sources.

        Args:
            fact: The fact to verify
            sources: List of sources supporting this fact
            verification_method: Method used for verification

        Returns:
            VerificationResult object
        """
        num_sources = len(sources)

        # Calculate confidence based on:
        # 1. Number of sources (more is better)
        # 2. Reliability tier (lower tier number is better)
        # 3. Source diversity (different types is better)

        if num_sources == 0:
            confidence = 0.0
        elif num_sources == 1:
            # Single source confidence based on tier
            tier = sources[0].reliability_tier.value
            confidence = max(0.3, 1.0 - (tier - 1) * 0.15)
        else:
            # Multiple sources - higher confidence
            avg_tier = sum(s.reliability_tier.value for s in sources) / num_sources

            # Base confidence from tier quality
            tier_confidence = max(0.5, 1.0 - (avg_tier - 1) * 0.1)

            # Bonus for multiple sources
            source_bonus = min(0.3, (num_sources - 1) * 0.1)

            # Bonus for source diversity
            source_types = set(s.source_type for s in sources)
            diversity_bonus = min(0.1, (len(source_types) - 1) * 0.05)

            confidence = min(1.0, tier_confidence + source_bonus + diversity_bonus)

        verified = confidence >= 0.7 and num_sources >= 1

        result = VerificationResult(
            fact=fact,
            verified=verified,
            confidence_score=round(confidence, 2),
            num_sources=num_sources,
            agreeing_sources=num_sources,  # Assume agreement for now
            conflicting_sources=0,
            sources=sources,
            verification_method=verification_method
        )

        self.verification_results.append(result)
        return result

    def get_confidence_score(self, data_point: str, sources: List[DataSource]) -> float:
        """
        Calculate confidence score for a data point.

        Args:
            data_point: The data point to score
            sources: Sources supporting this data point

        Returns:
            Confidence score (0.0 to 1.0)
        """
        result = self.verify_fact(data_point, sources)
        return result.confidence_score

    def get_sources_by_tier(self, tier: ReliabilityTier) -> List[DataSource]:
        """Get all sources of a specific reliability tier."""
        return [s for s in self.sources if s.reliability_tier == tier]

    def get_sources_by_type(self, source_type: SourceType) -> List[DataSource]:
        """Get all sources of a specific type."""
        return [s for s in self.sources if s.source_type == source_type]

    def get_tier1_sources(self) -> List[DataSource]:
        """Get all Tier 1 (most reliable) sources."""
        return self.get_sources_by_tier(ReliabilityTier.TIER_1)

    def to_dict(self) -> Dict[str, Any]:
        """Export tracking data to dictionary."""
        return {
            'sources': [s.to_dict() for s in self.sources],
            'verification_results': [v.to_dict() for v in self.verification_results],
            'total_sources': len(self.sources),
            'verified_facts': len([v for v in self.verification_results if v.verified])
        }

    def generate_provenance_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive provenance report.

        Returns:
            Report with source statistics and quality metrics
        """
        tier_counts = {}
        for tier in ReliabilityTier:
            count = len(self.get_sources_by_tier(tier))
            if count > 0:
                tier_counts[f"tier_{tier.value}"] = count

        type_counts = {}
        for source_type in SourceType:
            count = len(self.get_sources_by_type(source_type))
            if count > 0:
                type_counts[source_type.value] = count

        avg_confidence = 0.0
        if self.verification_results:
            avg_confidence = sum(v.confidence_score for v in self.verification_results) / len(self.verification_results)

        return {
            'total_sources': len(self.sources),
            'sources_by_tier': tier_counts,
            'sources_by_type': type_counts,
            'total_verifications': len(self.verification_results),
            'verified_facts': len([v for v in self.verification_results if v.verified]),
            'average_confidence': round(avg_confidence, 2),
            'tier_1_percentage': round(len(self.get_tier1_sources()) / max(1, len(self.sources)) * 100, 1)
        }


def determine_source_type(url: str, title: str = "") -> SourceType:
    """
    Heuristically determine source type from URL and title.

    Args:
        url: Source URL
        title: Source title (optional)

    Returns:
        SourceType enum value
    """
    url_lower = url.lower()
    title_lower = title.lower()

    # Government agencies
    gov_domains = ['.gov', '.gov.', 'europa.eu', 'who.int', 'un.org', 'ipcc.ch']
    if any(domain in url_lower for domain in gov_domains):
        return SourceType.GOVERNMENT_AGENCY

    # Research institutions
    edu_domains = ['.edu', '.ac.', 'nature.com', 'sciencedirect.com', 'springer.com']
    if any(domain in url_lower for domain in edu_domains) or 'doi.org' in url_lower:
        return SourceType.RESEARCH_INSTITUTION

    # Official databases
    db_keywords = ['data.', 'opendata', 'database', 'climate-adapt']
    if any(kw in url_lower for kw in db_keywords):
        return SourceType.OFFICIAL_DATABASE

    # NGOs and International Organizations
    ngo_domains = ['greenpeace', 'wwf', 'oxfam', 'wri.org', 'c40.org']
    if any(domain in url_lower for domain in ngo_domains):
        return SourceType.NGO

    # News
    news_domains = ['bbc.', 'reuters', 'theguardian', 'nytimes', 'apnews']
    if any(domain in url_lower for domain in news_domains):
        return SourceType.NEWS_ARTICLE

    return SourceType.WEBSITE


def determine_reliability_tier(source_type: SourceType, url: str = "") -> ReliabilityTier:
    """
    Determine reliability tier based on source type and URL.

    Args:
        source_type: Type of source
        url: Source URL (optional, for additional context)

    Returns:
        ReliabilityTier enum value
    """
    tier_mapping = {
        SourceType.GOVERNMENT_AGENCY: ReliabilityTier.TIER_1,
        SourceType.RESEARCH_INSTITUTION: ReliabilityTier.TIER_1,
        SourceType.PEER_REVIEWED_PAPER: ReliabilityTier.TIER_1,
        SourceType.OFFICIAL_DATABASE: ReliabilityTier.TIER_1,
        SourceType.INTERNATIONAL_ORG: ReliabilityTier.TIER_1,
        SourceType.NGO: ReliabilityTier.TIER_2,
        SourceType.REPORT: ReliabilityTier.TIER_2,
        SourceType.NEWS_ARTICLE: ReliabilityTier.TIER_3,
        SourceType.WEBSITE: ReliabilityTier.TIER_3,
        SourceType.API: ReliabilityTier.TIER_2,
        SourceType.MANUAL_ENTRY: ReliabilityTier.UNVERIFIED,
        SourceType.UNKNOWN: ReliabilityTier.UNVERIFIED,
    }

    return tier_mapping.get(source_type, ReliabilityTier.UNVERIFIED)
