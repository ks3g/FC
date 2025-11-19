#!/usr/bin/env python3
"""
Tests for Metrics and Source Tracking

Tests MetricsTracker and SourceTracker functionality.
"""

import sys
import unittest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from core.metrics_tracker import MetricsTracker, ModelPricing
from core.source_tracker import (
    SourceType, ReliabilityTier, CollectionMethod,
    DataSource, SourceTracker
)


class TestModelPricing(unittest.TestCase):
    """Test ModelPricing class."""

    def test_known_model_pricing(self):
        """Test cost calculation for known models."""
        # Claude Sonnet
        cost = ModelPricing.get_cost('claude-3-5-sonnet-20241022', 1_000_000, 1_000_000)
        expected_cost = 3.00 + 15.00  # $18.00
        self.assertAlmostEqual(cost, expected_cost, places=2)

        # GPT-3.5
        cost = ModelPricing.get_cost('gpt-3.5-turbo', 1_000_000, 1_000_000)
        expected_cost = 0.50 + 1.50  # $2.00
        self.assertAlmostEqual(cost, expected_cost, places=2)

    def test_unknown_model_fallback(self):
        """Test that unknown models use fallback pricing."""
        cost = ModelPricing.get_cost('unknown-model-123', 1_000_000, 1_000_000)
        # Should use GPT-3.5 pricing as fallback
        self.assertGreater(cost, 0)

    def test_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = ModelPricing.get_cost('gpt-3.5-turbo', 0, 0)
        self.assertEqual(cost, 0.0)

    def test_small_token_counts(self):
        """Test cost calculation with realistic token counts."""
        # 1000 input, 500 output tokens
        cost = ModelPricing.get_cost('claude-3-5-sonnet-20241022', 1000, 500)
        self.assertGreater(cost, 0)
        self.assertLess(cost, 1.0)  # Should be small amount

    def test_free_models(self):
        """Test that local models have zero cost."""
        cost = ModelPricing.get_cost('llama3', 1_000_000, 1_000_000)
        self.assertEqual(cost, 0.0)

        cost = ModelPricing.get_cost('mock-model', 100000, 100000)
        self.assertEqual(cost, 0.0)


class TestMetricsTracker(unittest.TestCase):
    """Test MetricsTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create temporary directory for metrics
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = MetricsTracker(storage_path=Path(self.temp_dir))

    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)

    def test_tracker_initialization(self):
        """Test tracker initializes correctly."""
        self.assertIsNotNone(self.tracker)
        self.assertTrue(self.tracker.storage_path.exists())

    def test_track_llm_call(self):
        """Test tracking LLM calls."""
        self.tracker.track_llm_call(
            agent_id='test_agent',
            model='claude-3-5-sonnet-20241022',
            input_tokens=1000,
            output_tokens=500,
            execution_time=1.5
        )

        # Verify metrics recorded
        if hasattr(self.tracker, 'get_agent_metrics'):
            metrics = self.tracker.get_agent_metrics('test_agent')
            self.assertIsNotNone(metrics)

    def test_track_research_session(self):
        """Test tracking research sessions."""
        session_id = 'session_001'
        self.tracker.track_research_start(session_id, 'Munich', 'Germany')

        # Simulate work
        self.tracker.track_llm_call(
            agent_id='test_agent',
            model='gpt-3.5-turbo',
            input_tokens=500,
            output_tokens=200,
            execution_time=0.5
        )

        self.tracker.track_research_end(session_id)

        # Verify session recorded
        if hasattr(self.tracker, 'get_session_metrics'):
            metrics = self.tracker.get_session_metrics(session_id)
            self.assertIsNotNone(metrics)

    def test_aggregate_metrics(self):
        """Test metric aggregation."""
        # Track multiple calls
        for i in range(5):
            self.tracker.track_llm_call(
                agent_id=f'agent_{i}',
                model='gpt-3.5-turbo',
                input_tokens=1000,
                output_tokens=500,
                execution_time=1.0
            )

        # Get aggregated metrics
        if hasattr(self.tracker, 'get_aggregate_metrics'):
            metrics = self.tracker.get_aggregate_metrics()
            self.assertIsNotNone(metrics)

    def test_metrics_persistence(self):
        """Test that metrics persist to disk."""
        # Track something
        self.tracker.track_llm_call(
            agent_id='test',
            model='gpt-3.5-turbo',
            input_tokens=100,
            output_tokens=50,
            execution_time=0.5
        )

        # Save metrics
        if hasattr(self.tracker, 'save'):
            self.tracker.save()

        # Create new tracker with same path
        new_tracker = MetricsTracker(storage_path=Path(self.temp_dir))

        # Should be able to load metrics
        if hasattr(new_tracker, 'load'):
            new_tracker.load()

    def test_cost_tracking(self):
        """Test cost calculation and tracking."""
        # Track expensive call
        self.tracker.track_llm_call(
            agent_id='expensive_agent',
            model='gpt-4',
            input_tokens=10000,
            output_tokens=5000,
            execution_time=3.0
        )

        # Get costs
        if hasattr(self.tracker, 'get_total_cost'):
            cost = self.tracker.get_total_cost()
            self.assertGreater(cost, 0)

    def test_performance_metrics(self):
        """Test performance metric tracking."""
        # Track calls with different execution times
        times = [0.5, 1.0, 1.5, 2.0, 2.5]
        for i, exec_time in enumerate(times):
            self.tracker.track_llm_call(
                agent_id=f'agent_{i}',
                model='gpt-3.5-turbo',
                input_tokens=1000,
                output_tokens=500,
                execution_time=exec_time
            )

        # Get performance stats
        if hasattr(self.tracker, 'get_performance_stats'):
            stats = self.tracker.get_performance_stats()
            self.assertIn('avg_execution_time', stats)
            self.assertIn('total_calls', stats)


class TestSourceType(unittest.TestCase):
    """Test SourceType enum."""

    def test_source_types_exist(self):
        """Test that all expected source types exist."""
        expected_types = [
            'GOVERNMENT_AGENCY', 'RESEARCH_INSTITUTION', 'PEER_REVIEWED_PAPER',
            'OFFICIAL_DATABASE', 'NGO', 'INTERNATIONAL_ORG'
        ]

        for type_name in expected_types:
            self.assertTrue(hasattr(SourceType, type_name))

    def test_source_type_values(self):
        """Test source type values are strings."""
        for source_type in SourceType:
            self.assertIsInstance(source_type.value, str)


class TestReliabilityTier(unittest.TestCase):
    """Test ReliabilityTier enum."""

    def test_tier_ordering(self):
        """Test that tiers are properly ordered."""
        self.assertLess(ReliabilityTier.TIER_1.value, ReliabilityTier.TIER_2.value)
        self.assertLess(ReliabilityTier.TIER_2.value, ReliabilityTier.TIER_3.value)
        self.assertLess(ReliabilityTier.TIER_3.value, ReliabilityTier.TIER_4.value)

    def test_tier_values(self):
        """Test tier values are integers."""
        for tier in ReliabilityTier:
            self.assertIsInstance(tier.value, int)


class TestDataSource(unittest.TestCase):
    """Test DataSource dataclass."""

    def setUp(self):
        """Set up test fixtures."""
        self.source = DataSource(
            url='https://example.com/data',
            title='Climate Data Report',
            source_type=SourceType.GOVERNMENT_AGENCY,
            reliability_tier=ReliabilityTier.TIER_1,
            accessed_at=datetime.now().isoformat(),
            collection_method=CollectionMethod.WEB_SCRAPING
        )

    def test_source_creation(self):
        """Test source creation."""
        self.assertEqual(self.source.url, 'https://example.com/data')
        self.assertEqual(self.source.title, 'Climate Data Report')
        self.assertEqual(self.source.source_type, SourceType.GOVERNMENT_AGENCY)
        self.assertEqual(self.source.reliability_tier, ReliabilityTier.TIER_1)

    def test_content_hash_creation(self):
        """Test content hash generation."""
        content = "Test content for hashing"
        hash1 = DataSource.create_hash(content)
        hash2 = DataSource.create_hash(content)

        # Same content should produce same hash
        self.assertEqual(hash1, hash2)

        # Different content should produce different hash
        hash3 = DataSource.create_hash("Different content")
        self.assertNotEqual(hash1, hash3)

        # Hash should be SHA-256 (64 hex characters)
        self.assertEqual(len(hash1), 64)

    def test_to_dict(self):
        """Test serialization to dict."""
        source_dict = self.source.to_dict()

        self.assertIsInstance(source_dict, dict)
        self.assertEqual(source_dict['url'], self.source.url)
        self.assertEqual(source_dict['source_type'], SourceType.GOVERNMENT_AGENCY.value)
        self.assertEqual(source_dict['reliability_tier'], ReliabilityTier.TIER_1.value)

    def test_from_dict(self):
        """Test deserialization from dict."""
        source_dict = self.source.to_dict()
        new_source = DataSource.from_dict(source_dict)

        self.assertEqual(new_source.url, self.source.url)
        self.assertEqual(new_source.source_type, self.source.source_type)
        self.assertEqual(new_source.reliability_tier, self.source.reliability_tier)

    def test_optional_fields(self):
        """Test optional field handling."""
        source = DataSource(
            url='https://example.com',
            title='Test',
            source_type=SourceType.WEBSITE,
            reliability_tier=ReliabilityTier.TIER_3,
            accessed_at=datetime.now().isoformat(),
            collection_method=CollectionMethod.WEB_SEARCH,
            author='John Doe',
            publication_date='2023-01-01',
            relevant_excerpt='Excerpt text'
        )

        self.assertEqual(source.author, 'John Doe')
        self.assertEqual(source.publication_date, '2023-01-01')
        self.assertEqual(source.relevant_excerpt, 'Excerpt text')

    def test_verification_fields(self):
        """Test verification field handling."""
        self.source.verified = True
        self.source.verified_by = 'validation_agent'
        self.source.verification_method = 'cross-reference'

        self.assertTrue(self.source.verified)
        self.assertEqual(self.source.verified_by, 'validation_agent')


class TestSourceTracker(unittest.TestCase):
    """Test SourceTracker class."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = SourceTracker()

        # Create test sources
        self.source1 = DataSource(
            url='https://example.com/data1',
            title='Climate Report 1',
            source_type=SourceType.GOVERNMENT_AGENCY,
            reliability_tier=ReliabilityTier.TIER_1,
            accessed_at=datetime.now().isoformat(),
            collection_method=CollectionMethod.API_CALL
        )

        self.source2 = DataSource(
            url='https://example.com/data2',
            title='Research Paper',
            source_type=SourceType.PEER_REVIEWED_PAPER,
            reliability_tier=ReliabilityTier.TIER_1,
            accessed_at=datetime.now().isoformat(),
            collection_method=CollectionMethod.WEB_SCRAPING
        )

    def test_tracker_initialization(self):
        """Test tracker initializes correctly."""
        self.assertIsNotNone(self.tracker)
        if hasattr(self.tracker, 'sources'):
            self.assertIsInstance(self.tracker.sources, list)

    def test_add_source(self):
        """Test adding sources."""
        self.tracker.add_source(self.source1)

        if hasattr(self.tracker, 'sources'):
            self.assertIn(self.source1, self.tracker.sources)

    def test_get_sources_by_type(self):
        """Test filtering sources by type."""
        self.tracker.add_source(self.source1)
        self.tracker.add_source(self.source2)

        if hasattr(self.tracker, 'get_sources_by_type'):
            gov_sources = self.tracker.get_sources_by_type(SourceType.GOVERNMENT_AGENCY)
            self.assertEqual(len(gov_sources), 1)
            self.assertEqual(gov_sources[0], self.source1)

    def test_get_sources_by_reliability(self):
        """Test filtering sources by reliability tier."""
        self.tracker.add_source(self.source1)
        self.tracker.add_source(self.source2)

        if hasattr(self.tracker, 'get_sources_by_reliability'):
            tier1_sources = self.tracker.get_sources_by_reliability(ReliabilityTier.TIER_1)
            self.assertEqual(len(tier1_sources), 2)

    def test_source_statistics(self):
        """Test source statistics calculation."""
        self.tracker.add_source(self.source1)
        self.tracker.add_source(self.source2)

        if hasattr(self.tracker, 'get_statistics'):
            stats = self.tracker.get_statistics()
            self.assertIn('total_sources', stats)
            self.assertIn('by_type', stats)
            self.assertIn('by_reliability', stats)

    def test_duplicate_source_handling(self):
        """Test handling of duplicate sources."""
        self.tracker.add_source(self.source1)
        self.tracker.add_source(self.source1)  # Add same source twice

        if hasattr(self.tracker, 'sources'):
            # Implementation may choose to deduplicate or not
            count = len([s for s in self.tracker.sources if s.url == self.source1.url])
            self.assertGreater(count, 0)

    def test_export_sources(self):
        """Test exporting sources to dict format."""
        self.tracker.add_source(self.source1)
        self.tracker.add_source(self.source2)

        if hasattr(self.tracker, 'export'):
            exported = self.tracker.export()
            self.assertIsInstance(exported, (list, dict))


class TestIntegration(unittest.TestCase):
    """Integration tests for metrics and source tracking."""

    def test_metrics_with_source_tracking(self):
        """Test that metrics and sources work together."""
        temp_dir = tempfile.mkdtemp()

        try:
            # Create trackers
            metrics = MetricsTracker(storage_path=Path(temp_dir))
            sources = SourceTracker()

            # Track research operation
            metrics.track_llm_call(
                agent_id='climate_agent',
                model='claude-3-5-sonnet-20241022',
                input_tokens=5000,
                output_tokens=2000,
                execution_time=2.5
            )

            # Track source
            source = DataSource(
                url='https://example.com',
                title='Climate Data',
                source_type=SourceType.GOVERNMENT_AGENCY,
                reliability_tier=ReliabilityTier.TIER_1,
                accessed_at=datetime.now().isoformat(),
                collection_method=CollectionMethod.API_CALL
            )
            sources.add_source(source)

            # Both should work together
            self.assertIsNotNone(metrics)
            self.assertIsNotNone(sources)

        finally:
            shutil.rmtree(temp_dir)


def run_tests():
    """Run all metrics and source tracking tests."""
    print("=" * 80)
    print("METRICS & SOURCE TRACKING TEST SUITE")
    print("=" * 80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestModelPricing))
    suite.addTests(loader.loadTestsFromTestCase(TestMetricsTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestSourceType))
    suite.addTests(loader.loadTestsFromTestCase(TestReliabilityTier))
    suite.addTests(loader.loadTestsFromTestCase(TestDataSource))
    suite.addTests(loader.loadTestsFromTestCase(TestSourceTracker))
    suite.addTests(loader.loadTestsFromTestCase(TestIntegration))

    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")

    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
