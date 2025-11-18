#!/usr/bin/env python3
"""
Flask Web Dashboard for Climate Research Agent Orchestration System

Provides a web interface to:
- View and manage agents
- Start research tasks
- View results and validation reports
- Monitor agent status
"""

from flask import Flask, render_template, jsonify, request, send_file
from datetime import datetime
import sys
from pathlib import Path
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.orchestrator import ResearchOrchestrator
from research.agents import (
    ClimateDataAgent,
    EmissionsAgent,
    VulnerabilityAgent,
    AdaptationAgent
)
from core.agent_base import AgentStatus
from core.metrics_tracker import get_metrics_tracker

app = Flask(__name__)
app.config['SECRET_KEY'] = 'climate-research-secret-key'

# Global orchestrator instance
orchestrator = None

# Global metrics tracker
metrics_tracker = get_metrics_tracker()


def init_orchestrator():
    """Initialize the orchestrator with LLM-powered agents."""
    global orchestrator
    orchestrator = ResearchOrchestrator(storage_dir="climate_research_system/data")

    # LLM configuration - will use MockLLMClient if no API key set
    # Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable to use real LLM
    llm_config = {
        'llm': {
            'provider': 'anthropic',  # or 'openai', 'ollama'
            'model': 'claude-3-5-sonnet-20241022'
            # API key read from environment variable
        },
        'enabled': True,
        'data_years': 30
    }

    # Register all LLM-powered agents
    agents = [
        ClimateDataAgent(agent_id="climate_001", config=llm_config),
        EmissionsAgent(agent_id="emissions_001", config=llm_config),
        VulnerabilityAgent(agent_id="vulnerability_001", config=llm_config),
        AdaptationAgent(agent_id="adaptation_001", config=llm_config)
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    return orchestrator


# Initialize on startup
init_orchestrator()


# ============================================================================
# Web Pages
# ============================================================================

@app.route('/')
def index():
    """Dashboard home page."""
    return render_template('dashboard.html')


@app.route('/research')
def research_page():
    """Research page to start new research."""
    return render_template('research.html')


@app.route('/results')
def results_page():
    """Results viewer page."""
    return render_template('results.html')


# ============================================================================
# API Endpoints - Agent Management
# ============================================================================

@app.route('/api/agents', methods=['GET'])
def get_agents():
    """Get list of all agents with their status."""
    agents_data = []

    for agent_id, agent in orchestrator.agents.items():
        agent_state = agent.get_state()
        agents_data.append({
            'id': agent_id,
            'name': agent.name,
            'status': agent_state['status'],
            'enabled': agent.config.get('enabled', True),
            'message_count': agent_state['message_count'],
            'error_count': len(agent_state['errors']),
            'config': agent.config,
            'created_at': agent_state['created_at'],
            'updated_at': agent_state['updated_at']
        })

    return jsonify({
        'success': True,
        'agents': agents_data,
        'total': len(agents_data)
    })


@app.route('/api/agents/<agent_id>', methods=['GET'])
def get_agent(agent_id):
    """Get details of a specific agent."""
    if agent_id not in orchestrator.agents:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    agent = orchestrator.agents[agent_id]
    return jsonify({
        'success': True,
        'agent': agent.get_state()
    })


@app.route('/api/agents/<agent_id>/toggle', methods=['POST'])
def toggle_agent(agent_id):
    """Enable or disable an agent."""
    if agent_id not in orchestrator.agents:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    agent = orchestrator.agents[agent_id]
    current_status = agent.config.get('enabled', True)
    agent.config['enabled'] = not current_status

    # Update status
    if agent.config['enabled']:
        if agent.status == AgentStatus.DISABLED:
            agent.set_status(AgentStatus.IDLE)
    else:
        agent.set_status(AgentStatus.DISABLED)

    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'enabled': agent.config['enabled']
    })


@app.route('/api/agents/<agent_id>/reset', methods=['POST'])
def reset_agent(agent_id):
    """Reset an agent to initial state."""
    if agent_id not in orchestrator.agents:
        return jsonify({'success': False, 'error': 'Agent not found'}), 404

    orchestrator.agents[agent_id].reset()

    return jsonify({
        'success': True,
        'agent_id': agent_id,
        'message': 'Agent reset successfully'
    })


# ============================================================================
# API Endpoints - Research
# ============================================================================

@app.route('/api/research/start', methods=['POST'])
def start_research():
    """Start a new research task."""
    data = request.get_json()

    city = data.get('city')
    country = data.get('country')

    if not city or not country:
        return jsonify({
            'success': False,
            'error': 'Both city and country are required'
        }), 400

    # Get enabled agents only
    enabled_agents = {
        agent_id: agent for agent_id, agent in orchestrator.agents.items()
        if agent.config.get('enabled', True)
    }

    if not enabled_agents:
        return jsonify({
            'success': False,
            'error': 'No agents are enabled'
        }), 400

    # Start research
    try:
        # Check if parallel execution requested
        use_parallel = data.get('parallel', False)

        if use_parallel:
            results = orchestrator.research_city_parallel(
                city=city,
                country=country,
                **data.get('params', {})
            )
        else:
            results = orchestrator.research_city(
                city=city,
                country=country,
                **data.get('params', {})
            )

        # Track metrics
        try:
            metrics_tracker.track_research(results)
        except Exception as e:
            # Don't fail research if metrics tracking fails
            print(f"Warning: Metrics tracking failed: {e}")

        return jsonify({
            'success': True,
            'research_id': results['research_id'],
            'message': f'Research started for {city}, {country}',
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/research/list', methods=['GET'])
def list_research():
    """List all completed research."""
    research_ids = orchestrator.list_research()

    research_list = []
    for research_id in research_ids:
        results = orchestrator.get_research_status(research_id)
        if results:
            research_list.append({
                'id': research_id,
                'city': results.get('city'),
                'country': results.get('country'),
                'completed_at': results.get('completed_at'),
                'agents_used': len(results.get('metadata', {}).get('agents_used', [])),
                'data_completeness': results.get('summary', {}).get('data_completeness', 0)
            })

    return jsonify({
        'success': True,
        'research': research_list,
        'total': len(research_list)
    })


@app.route('/api/research/<research_id>', methods=['GET'])
def get_research(research_id):
    """Get detailed research results."""
    results = orchestrator.get_research_status(research_id)

    if not results:
        return jsonify({
            'success': False,
            'error': 'Research not found'
        }), 404

    return jsonify({
        'success': True,
        'results': results
    })


@app.route('/api/research/<research_id>/download', methods=['GET'])
def download_research(research_id):
    """Download research results as JSON."""
    results = orchestrator.get_research_status(research_id)

    if not results:
        return jsonify({
            'success': False,
            'error': 'Research not found'
        }), 404

    # Create temporary file
    file_path = f"climate_research_system/data/{research_id}_export.json"
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=2)

    return send_file(
        file_path,
        as_attachment=True,
        download_name=f"{research_id}.json"
    )


# ============================================================================
# API Endpoints - Statistics
# ============================================================================

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get system statistics."""
    research_list = orchestrator.list_research()

    total_agents = len(orchestrator.agents)
    enabled_agents = sum(
        1 for agent in orchestrator.agents.values()
        if agent.config.get('enabled', True)
    )

    return jsonify({
        'success': True,
        'stats': {
            'total_agents': total_agents,
            'enabled_agents': enabled_agents,
            'disabled_agents': total_agents - enabled_agents,
            'total_research': len(research_list),
            'system_uptime': str(datetime.now() - orchestrator.created_at)
        }
    })


# ============================================================================
# API Endpoints - Metrics & Analytics
# ============================================================================

@app.route('/api/metrics/dashboard', methods=['GET'])
def get_dashboard_metrics():
    """Get comprehensive dashboard metrics."""
    token_summary = metrics_tracker.get_token_summary()
    performance = metrics_tracker.get_performance_summary()
    quality = metrics_tracker.get_quality_summary()
    agent_stats = metrics_tracker.get_agent_statistics()
    system_health = metrics_tracker.get_system_health()

    # Get current model info
    model_info = {}
    for agent_id, agent in orchestrator.agents.items():
        llm_config = agent.config.get('llm', {})
        model_info[agent_id] = {
            'provider': llm_config.get('provider', 'unknown'),
            'model': llm_config.get('model', 'unknown'),
            'is_local': llm_config.get('provider') in ['ollama', 'mock']
        }

    return jsonify({
        'success': True,
        'metrics': {
            'tokens': token_summary,
            'performance': performance,
            'quality': quality,
            'agents': agent_stats,
            'system': system_health,
            'models': model_info
        }
    })


@app.route('/api/metrics/tokens', methods=['GET'])
def get_token_metrics():
    """Get detailed token usage metrics."""
    return jsonify({
        'success': True,
        'metrics': metrics_tracker.get_token_summary()
    })


@app.route('/api/metrics/performance', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics."""
    return jsonify({
        'success': True,
        'metrics': metrics_tracker.get_performance_summary()
    })


@app.route('/api/metrics/quality', methods=['GET'])
def get_quality_metrics():
    """Get data quality metrics."""
    return jsonify({
        'success': True,
        'metrics': metrics_tracker.get_quality_summary()
    })


@app.route('/api/metrics/agents', methods=['GET'])
def get_agent_metrics():
    """Get per-agent statistics."""
    agent_stats = metrics_tracker.get_agent_statistics()

    # Enhance with current agent info
    for agent_id, agent in orchestrator.agents.items():
        if agent_id in agent_stats:
            llm_config = agent.config.get('llm', {})
            agent_stats[agent_id]['model'] = llm_config.get('model', 'unknown')
            agent_stats[agent_id]['provider'] = llm_config.get('provider', 'unknown')
            agent_stats[agent_id]['name'] = agent.name
            agent_stats[agent_id]['enabled'] = agent.config.get('enabled', True)

    return jsonify({
        'success': True,
        'agents': agent_stats
    })


@app.route('/api/metrics/system', methods=['GET'])
def get_system_metrics():
    """Get system health metrics."""
    return jsonify({
        'success': True,
        'metrics': metrics_tracker.get_system_health()
    })


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Not found'}), 404
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500
    return render_template('500.html'), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 70)
    print("  Climate Research Agent Orchestration System - Web Dashboard")
    print("=" * 70)
    print()
    print(f"  Dashboard URL: http://localhost:5000")
    print(f"  Registered Agents: {len(orchestrator.agents)}")
    print()
    print("  Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    app.run(debug=True, host='0.0.0.0', port=5000)
