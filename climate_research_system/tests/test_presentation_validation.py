#!/usr/bin/env python3
"""
Tests for Presentation and Validation Agents

Tests the PresentationAgent and ValidationAgent functionality.
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from presentation.presentation_agent import PresentationAgent
from research.agents.validation import ValidationAgent
from core.source_tracker import SourceType, ReliabilityTier


class TestPresentationAgent(unittest.TestCase):
    """Test PresentationAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'llm': {
                'provider': 'mock',
                'model': 'test-model'
            }
        }
        self.agent = PresentationAgent(
            agent_id="test_presentation",
            name="Test Presentation Agent",
            config=self.config
        )

        # Mock LLM responses
        self.agent.llm.generate = Mock(return_value={
            'content': 'Test LLM response',
            'model': 'test-model',
            'tokens_used': 100
        })

    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        self.assertEqual(self.agent.agent_id, "test_presentation")
        self.assertEqual(self.agent.name, "Test Presentation Agent")
        self.assertIsNotNone(self.agent.llm)

    def test_execute_basic(self):
        """Test basic presentation generation."""
        task = {
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': {
                'climate': {'data': 'climate data'},
                'emissions': {'data': 'emissions data'}
            },
            'validation_report': {
                'overall_confidence': 0.85,
                'total_sources': 10,
                'validation_status': 'passed'
            }
        }

        result = self.agent.execute(task)

        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertEqual(result['city'], 'Munich')
        self.assertEqual(result['country'], 'Germany')
        self.assertIn('executive_summary', result)
        self.assertIn('key_insights', result)
        self.assertIn('detailed_findings', result)
        self.assertIn('recommendations', result)

    def test_extract_findings(self):
        """Test findings extraction from agent results."""
        agent_results = {
            'climate': {'data': {'temp': 15}},
            'emissions': {'findings': ['High CO2']},
            'vulnerability': {'info': 'flood risk'}
        }

        findings = self.agent._extract_findings(agent_results)

        self.assertIsInstance(findings, dict)
        self.assertIn('climate', findings)
        self.assertEqual(findings['climate'], {'temp': 15})

    def test_generate_executive_summary(self):
        """Test executive summary generation."""
        findings = {'climate': {'temp': 15}}
        validation_report = {
            'overall_confidence': 0.9,
            'total_sources': 5,
            'validation_status': 'passed'
        }

        summary = self.agent._generate_executive_summary(
            'Munich', 'Germany', findings, validation_report
        )

        self.assertIsInstance(summary, str)
        self.assertGreater(len(summary), 0)

    def test_generate_recommendations(self):
        """Test recommendations generation."""
        findings = {'climate': {'temp': 15}}
        validation_report = {'overall_confidence': 0.8}

        # Mock LLM to return numbered list
        self.agent.llm.generate = Mock(return_value={
            'content': '1. Implement mitigation\n2. Monitor trends\n3. Engage stakeholders',
            'model': 'test'
        })

        recommendations = self.agent._generate_recommendations(
            'Munich', 'Germany', findings, validation_report
        )

        self.assertIsInstance(recommendations, list)
        self.assertGreater(len(recommendations), 0)

    def test_generate_key_insights(self):
        """Test key insights generation."""
        findings = {'climate': {'temp': 15}}

        # Mock LLM to return bullet list
        self.agent.llm.generate = Mock(return_value={
            'content': '- Rising temperatures\n- Increased precipitation\n- Flood risk',
            'model': 'test'
        })

        insights = self.agent._generate_key_insights(
            'Munich', 'Germany', findings
        )

        self.assertIsInstance(insights, list)
        self.assertGreater(len(insights), 0)

    def test_validate_presentation(self):
        """Test presentation validation."""
        # Valid presentation
        valid_data = {
            'city': 'Munich',
            'country': 'Germany',
            'executive_summary': 'Summary text',
            'recommendations': ['Rec 1', 'Rec 2']
        }
        self.assertTrue(self.agent.validate(valid_data))

        # Invalid presentation (missing fields)
        invalid_data = {
            'city': 'Munich'
        }
        self.assertFalse(self.agent.validate(invalid_data))

    def test_error_handling(self):
        """Test agent handles errors gracefully."""
        # Simulate LLM error
        self.agent.llm.generate = Mock(side_effect=Exception("LLM error"))

        task = {
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': {},
            'validation_report': {}
        }

        # Should not crash, should use fallback
        result = self.agent.execute(task)
        self.assertIsInstance(result, dict)
        self.assertIn('recommendations', result)

    def test_llm_response_handling(self):
        """Test correct handling of LLM dict responses."""
        # Test dict response
        self.agent.llm.generate = Mock(return_value={
            'content': 'Test response',
            'model': 'test',
            'tokens_used': 50
        })

        findings = {'test': 'data'}
        validation_report = {'overall_confidence': 0.8}

        summary = self.agent._generate_executive_summary(
            'Munich', 'Germany', findings, validation_report
        )

        # Should extract 'content' from dict
        self.assertEqual(summary, 'Test response')


class TestValidationAgent(unittest.TestCase):
    """Test ValidationAgent class."""

    def setUp(self):
        """Set up test fixtures."""
        self.config = {
            'llm': {
                'provider': 'mock',
                'model': 'test-model'
            }
        }
        self.agent = ValidationAgent(
            agent_id="test_validation",
            name="Test Validation Agent",
            config=self.config
        )

        # Mock LLM responses
        self.agent.llm.generate = Mock(return_value={
            'content': '{"confidence": 0.85, "issues": []}',
            'model': 'test-model'
        })

    def test_agent_initialization(self):
        """Test agent initializes correctly."""
        self.assertEqual(self.agent.agent_id, "test_validation")
        self.assertIsNotNone(self.agent.llm)

    def test_execute_basic(self):
        """Test basic validation."""
        task = {
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': {
                'climate': {
                    'data': 'climate data',
                    'sources': [
                        {
                            'type': SourceType.ACADEMIC,
                            'reliability': ReliabilityTier.HIGH,
                            'url': 'http://example.com'
                        }
                    ]
                }
            }
        }

        result = self.agent.execute(task)

        # Verify structure
        self.assertIsInstance(result, dict)
        self.assertIn('validation_status', result)
        self.assertIn('overall_confidence', result)
        self.assertIn('total_sources', result)
        self.assertIn('source_breakdown', result)

    def test_source_tracking(self):
        """Test source tracking and counting."""
        agent_results = {
            'climate': {
                'sources': [
                    {'type': SourceType.ACADEMIC, 'reliability': ReliabilityTier.HIGH},
                    {'type': SourceType.GOVERNMENT, 'reliability': ReliabilityTier.HIGH}
                ]
            },
            'emissions': {
                'sources': [
                    {'type': SourceType.ACADEMIC, 'reliability': ReliabilityTier.MEDIUM}
                ]
            }
        }

        stats = self.agent._count_sources(agent_results)

        self.assertEqual(stats['total_sources'], 3)
        self.assertIn(SourceType.ACADEMIC.value, stats['by_type'])
        self.assertIn(ReliabilityTier.HIGH.value, stats['by_reliability'])

    def test_confidence_calculation(self):
        """Test confidence score calculation."""
        agent_results = {
            'agent1': {
                'sources': [
                    {'type': SourceType.ACADEMIC, 'reliability': ReliabilityTier.HIGH}
                ] * 5
            }
        }

        confidence = self.agent._calculate_confidence(agent_results)

        self.assertIsInstance(confidence, float)
        self.assertGreaterEqual(confidence, 0.0)
        self.assertLessEqual(confidence, 1.0)

    def test_cross_validation(self):
        """Test cross-validation of data."""
        agent_results = {
            'agent1': {'data': {'temp': 15}},
            'agent2': {'data': {'temp': 15.5}}
        }

        if hasattr(self.agent, '_cross_validate'):
            issues = self.agent._cross_validate(agent_results)
            self.assertIsInstance(issues, list)

    def test_enum_json_serialization(self):
        """Test that SourceType enums serialize correctly to JSON."""
        import json
        from research.agents.validation import EnumJSONEncoder

        data = {
            'type': SourceType.ACADEMIC,
            'reliability': ReliabilityTier.HIGH
        }

        # Should not raise exception
        json_str = json.dumps(data, cls=EnumJSONEncoder)
        self.assertIsInstance(json_str, str)
        self.assertIn('academic', json_str)

    def test_validation_status_determination(self):
        """Test validation status is determined correctly."""
        task = {
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': {
                'climate': {
                    'sources': [
                        {'type': SourceType.ACADEMIC, 'reliability': ReliabilityTier.HIGH}
                    ] * 10  # Many high-quality sources
                }
            }
        }

        result = self.agent.execute(task)

        # Should have high confidence
        self.assertGreater(result['overall_confidence'], 0.5)
        self.assertIn(result['validation_status'], ['passed', 'warning', 'failed'])

    def test_error_handling(self):
        """Test agent handles errors gracefully."""
        # Simulate LLM error
        self.agent.llm.generate = Mock(side_effect=Exception("LLM error"))

        task = {
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': {}
        }

        # Should not crash
        result = self.agent.execute(task)
        self.assertIsInstance(result, dict)


class TestIntegration(unittest.TestCase):
    """Integration tests for validation → presentation flow."""

    def test_validation_to_presentation_flow(self):
        """Test that validation output works as presentation input."""
        # Create agents
        validation_agent = ValidationAgent(agent_id="val", config={'llm': {'provider': 'mock'}})
        presentation_agent = PresentationAgent(agent_id="pres", config={'llm': {'provider': 'mock'}})

        # Mock LLM
        validation_agent.llm.generate = Mock(return_value={'content': '{"confidence": 0.8}', 'model': 'test'})
        presentation_agent.llm.generate = Mock(return_value={'content': 'Test', 'model': 'test'})

        # Run validation
        agent_results = {
            'climate': {
                'data': 'climate data',
                'sources': [
                    {'type': SourceType.ACADEMIC, 'reliability': ReliabilityTier.HIGH}
                ]
            }
        }

        validation_result = validation_agent.execute({
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': agent_results
        })

        # Use validation result in presentation
        presentation_result = presentation_agent.execute({
            'city': 'Munich',
            'country': 'Germany',
            'agent_results': agent_results,
            'validation_report': validation_result
        })

        # Both should succeed
        self.assertIsInstance(validation_result, dict)
        self.assertIsInstance(presentation_result, dict)
        self.assertTrue(presentation_agent.validate(presentation_result))


def run_tests():
    """Run all presentation and validation tests."""
    print("=" * 80)
    print("PRESENTATION & VALIDATION AGENTS TEST SUITE")
    print("=" * 80)

    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # Add all test classes
    suite.addTests(loader.loadTestsFromTestCase(TestPresentationAgent))
    suite.addTests(loader.loadTestsFromTestCase(TestValidationAgent))
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
