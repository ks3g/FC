"""
Metrics Tracker

Comprehensive tracking system for monitoring research operations:
- Token usage and costs
- Performance metrics
- Data quality metrics
- Agent statistics
- System health
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import json
from collections import defaultdict
import logging


class ModelPricing:
    """Model pricing information for cost calculation."""

    # Pricing per 1M tokens (USD)
    PRICES = {
        # Anthropic Claude
        'claude-3-5-sonnet-20241022': {'input': 3.00, 'output': 15.00},
        'claude-3-5-haiku-20241022': {'input': 0.80, 'output': 4.00},

        # OpenAI
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'gpt-4': {'input': 30.00, 'output': 60.00},
        'gpt-3.5-turbo': {'input': 0.50, 'output': 1.50},

        # Azure OpenAI (same as OpenAI)
        'azure-gpt-4': {'input': 10.00, 'output': 30.00},
        'azure-gpt-35-turbo': {'input': 0.50, 'output': 1.50},

        # Local models (free)
        'llama3': {'input': 0.00, 'output': 0.00},
        'mixtral': {'input': 0.00, 'output': 0.00},
        'mock-model': {'input': 0.00, 'output': 0.00},
    }

    @classmethod
    def get_cost(cls, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate cost for token usage.

        Args:
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        # Find matching pricing (handle model variants)
        pricing = None
        for price_model, prices in cls.PRICES.items():
            if price_model in model.lower() or model.lower() in price_model:
                pricing = prices
                break

        if not pricing:
            # Unknown model, assume GPT-3.5 pricing
            pricing = cls.PRICES['gpt-3.5-turbo']

        input_cost = (input_tokens / 1_000_000) * pricing['input']
        output_cost = (output_tokens / 1_000_000) * pricing['output']

        return input_cost + output_cost


class MetricsTracker:
    """
    Tracks comprehensive metrics for research operations.

    Collects data on:
    - Token usage and costs
    - Performance (execution time, throughput)
    - Data quality (confidence, sources)
    - Agent statistics
    - System health
    """

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize metrics tracker.

        Args:
            storage_path: Path to store metrics data
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent / "data" / "metrics"

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.metrics_file = self.storage_path / "metrics.json"
        self.logger = logging.getLogger(__name__)

        # Load existing metrics
        self.metrics = self._load_metrics()

    def _load_metrics(self) -> Dict[str, Any]:
        """Load metrics from storage."""
        if self.metrics_file.exists():
            try:
                with open(self.metrics_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Failed to load metrics: {e}")

        return {
            'research_sessions': [],
            'token_usage': {
                'total_tokens': 0,
                'total_cost': 0.0,
                'by_model': {},
                'by_agent': {},
                'by_date': {}
            },
            'performance': {
                'total_research_count': 0,
                'avg_execution_time': 0.0,
                'parallel_count': 0,
                'sequential_count': 0
            },
            'data_quality': {
                'avg_confidence': 0.0,
                'total_sources': 0,
                'sources_by_tier': {}
            },
            'agents': {},
            'system': {
                'pdf_count': 0,
                'vector_store_size': 0,
                'last_updated': datetime.utcnow().isoformat()
            }
        }

    def _save_metrics(self):
        """Save metrics to storage."""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(self.metrics, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    def track_research(self, research_results: Dict[str, Any]):
        """
        Track a completed research session.

        Args:
            research_results: Complete research results
        """
        research_id = research_results.get('research_id', 'unknown')
        metadata = research_results.get('metadata', {})

        # Create session record
        session = {
            'research_id': research_id,
            'city': research_results.get('city'),
            'country': research_results.get('country'),
            'timestamp': research_results.get('completed_at', datetime.utcnow().isoformat()),
            'execution_time': metadata.get('execution_time_seconds', 0),
            'execution_mode': metadata.get('execution_mode', 'sequential'),
            'agents_used': metadata.get('agents_used', []),
            'successful_agents': metadata.get('successful_agents', 0),
            'total_tokens': 0,
            'cost': 0.0,
            'confidence': 0.0,
            'sources': 0
        }

        # Track tokens and costs
        agent_results = research_results.get('agent_results', {})
        total_tokens = 0
        total_cost = 0.0

        for agent_id, result in agent_results.items():
            if isinstance(result, dict) and 'error' not in result:
                tokens = result.get('tokens_used', 0)
                model = result.get('llm_model', 'unknown')

                # Estimate input/output split (60/40 ratio typical)
                input_tokens = int(tokens * 0.6)
                output_tokens = int(tokens * 0.4)

                cost = ModelPricing.get_cost(model, input_tokens, output_tokens)

                total_tokens += tokens
                total_cost += cost

                # Track by agent
                if agent_id not in self.metrics['token_usage']['by_agent']:
                    self.metrics['token_usage']['by_agent'][agent_id] = {
                        'total_tokens': 0,
                        'total_cost': 0.0,
                        'count': 0
                    }

                self.metrics['token_usage']['by_agent'][agent_id]['total_tokens'] += tokens
                self.metrics['token_usage']['by_agent'][agent_id]['total_cost'] += cost
                self.metrics['token_usage']['by_agent'][agent_id]['count'] += 1

                # Track by model
                if model not in self.metrics['token_usage']['by_model']:
                    self.metrics['token_usage']['by_model'][model] = {
                        'total_tokens': 0,
                        'total_cost': 0.0,
                        'count': 0
                    }

                self.metrics['token_usage']['by_model'][model]['total_tokens'] += tokens
                self.metrics['token_usage']['by_model'][model]['total_cost'] += cost
                self.metrics['token_usage']['by_model'][model]['count'] += 1

        session['total_tokens'] = total_tokens
        session['cost'] = round(total_cost, 4)

        # Track data quality
        validation = research_results.get('validation_report', {})
        overall = validation.get('overall_assessment', {})

        session['confidence'] = overall.get('average_confidence', 0.0)
        session['sources'] = validation.get('total_sources', 0)

        # Update global metrics
        self.metrics['token_usage']['total_tokens'] += total_tokens
        self.metrics['token_usage']['total_cost'] += total_cost

        # Track by date
        date = datetime.fromisoformat(session['timestamp']).date().isoformat()
        if date not in self.metrics['token_usage']['by_date']:
            self.metrics['token_usage']['by_date'][date] = {
                'tokens': 0,
                'cost': 0.0,
                'research_count': 0
            }

        self.metrics['token_usage']['by_date'][date]['tokens'] += total_tokens
        self.metrics['token_usage']['by_date'][date]['cost'] += total_cost
        self.metrics['token_usage']['by_date'][date]['research_count'] += 1

        # Update performance metrics
        self.metrics['performance']['total_research_count'] += 1

        if session['execution_mode'] == 'parallel':
            self.metrics['performance']['parallel_count'] += 1
        else:
            self.metrics['performance']['sequential_count'] += 1

        # Update average execution time
        current_avg = self.metrics['performance']['avg_execution_time']
        count = self.metrics['performance']['total_research_count']
        new_avg = ((current_avg * (count - 1)) + session['execution_time']) / count
        self.metrics['performance']['avg_execution_time'] = round(new_avg, 2)

        # Update data quality metrics
        if session['confidence'] > 0:
            current_conf = self.metrics['data_quality']['avg_confidence']
            new_conf = ((current_conf * (count - 1)) + session['confidence']) / count
            self.metrics['data_quality']['avg_confidence'] = round(new_conf, 2)

        self.metrics['data_quality']['total_sources'] += session['sources']

        # Track sources by tier
        sources = validation.get('sources', [])
        for source in sources:
            tier = source.get('reliability_tier', 'unknown')
            tier_key = f"tier_{tier}"
            self.metrics['data_quality']['sources_by_tier'][tier_key] = \
                self.metrics['data_quality']['sources_by_tier'].get(tier_key, 0) + 1

        # Add session to history
        self.metrics['research_sessions'].append(session)

        # Keep only last 1000 sessions
        if len(self.metrics['research_sessions']) > 1000:
            self.metrics['research_sessions'] = self.metrics['research_sessions'][-1000:]

        # Update system timestamp
        self.metrics['system']['last_updated'] = datetime.utcnow().isoformat()

        # Save
        self._save_metrics()

    def get_token_summary(self) -> Dict[str, Any]:
        """Get token usage summary."""
        return {
            'total_tokens': self.metrics['token_usage']['total_tokens'],
            'total_cost': round(self.metrics['token_usage']['total_cost'], 2),
            'by_model': self.metrics['token_usage']['by_model'],
            'by_agent': self.metrics['token_usage']['by_agent'],
            'recent_usage': self._get_recent_token_usage(days=7)
        }

    def _get_recent_token_usage(self, days: int = 7) -> List[Dict[str, Any]]:
        """Get token usage for recent days."""
        by_date = self.metrics['token_usage']['by_date']

        # Get last N days
        today = datetime.utcnow().date()
        recent = []

        for i in range(days):
            date = (today - timedelta(days=i)).isoformat()
            if date in by_date:
                recent.append({
                    'date': date,
                    **by_date[date]
                })
            else:
                recent.append({
                    'date': date,
                    'tokens': 0,
                    'cost': 0.0,
                    'research_count': 0
                })

        return list(reversed(recent))

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        perf = self.metrics['performance']

        return {
            'total_research': perf['total_research_count'],
            'avg_execution_time': perf['avg_execution_time'],
            'parallel_count': perf['parallel_count'],
            'sequential_count': perf['sequential_count'],
            'parallel_percentage': round(
                (perf['parallel_count'] / max(1, perf['total_research_count'])) * 100, 1
            ),
            'recent_research': self._get_recent_research(limit=10)
        }

    def _get_recent_research(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent research sessions."""
        sessions = self.metrics['research_sessions']
        return sessions[-limit:] if sessions else []

    def get_quality_summary(self) -> Dict[str, Any]:
        """Get data quality metrics summary."""
        quality = self.metrics['data_quality']

        return {
            'avg_confidence': quality['avg_confidence'],
            'total_sources': quality['total_sources'],
            'sources_by_tier': quality['sources_by_tier'],
            'tier_breakdown': self._calculate_tier_percentages()
        }

    def _calculate_tier_percentages(self) -> Dict[str, float]:
        """Calculate percentage breakdown of sources by tier."""
        sources_by_tier = self.metrics['data_quality']['sources_by_tier']
        total = sum(sources_by_tier.values())

        if total == 0:
            return {}

        return {
            tier: round((count / total) * 100, 1)
            for tier, count in sources_by_tier.items()
        }

    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get per-agent statistics."""
        stats = {}

        for agent_id, data in self.metrics['token_usage']['by_agent'].items():
            stats[agent_id] = {
                'executions': data['count'],
                'total_tokens': data['total_tokens'],
                'avg_tokens': round(data['total_tokens'] / max(1, data['count']), 0),
                'total_cost': round(data['total_cost'], 2),
                'avg_cost': round(data['total_cost'] / max(1, data['count']), 4)
            }

        return stats

    def get_system_health(self) -> Dict[str, Any]:
        """Get system health metrics."""
        # This could be enhanced with actual system checks
        return {
            'status': 'healthy',
            'last_updated': self.metrics['system']['last_updated'],
            'total_research': self.metrics['performance']['total_research_count'],
            'vector_store': {
                'pdf_count': self.metrics['system'].get('pdf_count', 0),
                'size_mb': self.metrics['system'].get('vector_store_size', 0)
            }
        }

    def update_system_metrics(self, pdf_count: int = 0, vector_size_mb: int = 0):
        """Update system metrics."""
        self.metrics['system']['pdf_count'] = pdf_count
        self.metrics['system']['vector_store_size'] = vector_size_mb
        self.metrics['system']['last_updated'] = datetime.utcnow().isoformat()
        self._save_metrics()


# Global metrics tracker instance
_metrics_tracker = None


def get_metrics_tracker() -> MetricsTracker:
    """Get global metrics tracker instance."""
    global _metrics_tracker

    if _metrics_tracker is None:
        _metrics_tracker = MetricsTracker()

    return _metrics_tracker
