#!/usr/bin/env python3
"""
Local Model Configuration Demo

Shows how to configure and use local models or custom API endpoints
with the Climate Research System.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import load_model_config, load_agent_config, get_config_loader
from research.orchestrator import ResearchOrchestrator
from research.agents import (
    ClimateDataAgent,
    EmissionsAgent,
    VulnerabilityAgent,
    AdaptationAgent
)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def main():
    """Main demo function."""
    print_section("🏢 Local Model Configuration Demo")

    print("This demo shows how to use custom model configurations.")
    print("Edit config/models.yaml to configure your local models.\n")

    # Load configuration
    config_loader = get_config_loader()

    # Show available models
    print_section("📋 Available Models")

    all_models = config_loader.list_available_models()

    for model in all_models:
        status = "✓ ENABLED" if model['enabled'] else "○ disabled"
        print(f"{status} {model['name']}")
        print(f"   Title: {model['title']}")
        print(f"   Provider: {model['provider']}")
        print(f"   Model: {model['model']}")
        if model['description']:
            print(f"   Description: {model['description']}")
        print()

    # Show enabled models
    print_section("✓ Enabled Models")

    enabled = config_loader.get_enabled_models()
    if enabled:
        for model in enabled:
            print(f"• {model['title']} ({model['name']})")
        print()
    else:
        print("No models are enabled in config/models.yaml")
        print("Enable at least one model to run research.\n")
        return

    # Show agent-specific assignments
    print_section("🤖 Agent Model Assignments")

    agent_ids = ['climate_001', 'emissions_001', 'vulnerability_001', 'adaptation_001']
    agent_names = {
        'climate_001': 'Climate Data Agent',
        'emissions_001': 'Emissions Agent',
        'vulnerability_001': 'Vulnerability Agent',
        'adaptation_001': 'Adaptation Agent'
    }

    for agent_id in agent_ids:
        config = load_agent_config(agent_id)
        llm_config = config.get('llm', {})
        print(f"{agent_names[agent_id]} ({agent_id}):")
        print(f"   Provider: {llm_config.get('provider', 'default')}")
        print(f"   Model: {llm_config.get('model', 'default')}")
        if llm_config.get('api_base'):
            print(f"   API Base: {llm_config['api_base']}")
        print()

    # Initialize orchestrator with configured models
    print_section("🚀 Starting Research with Configured Models")

    print("Initializing orchestrator with models from config...")
    orchestrator = ResearchOrchestrator(storage_dir="climate_research_system/data")

    # Register agents using config
    agents = []
    for agent_id, agent_class in [
        ('climate_001', ClimateDataAgent),
        ('emissions_001', EmissionsAgent),
        ('vulnerability_001', VulnerabilityAgent),
        ('adaptation_001', AdaptationAgent)
    ]:
        config = load_agent_config(agent_id)
        agent = agent_class(agent_id=agent_id, config=config)
        orchestrator.register_agent(agent)
        agents.append(agent)

        llm_config = config.get('llm', {})
        print(f"✓ Registered: {agent.name}")
        print(f"   Using: {llm_config.get('provider')}/{llm_config.get('model')}")
        if llm_config.get('api_base'):
            print(f"   Endpoint: {llm_config['api_base']}")
        print()

    # Conduct research
    city = "Rotterdam"
    country = "Netherlands"

    print(f"\nConducting research on {city}, {country}...\n")

    results = orchestrator.research_city(city, country, years=30)

    # Display results
    print_section("📊 Research Results")

    print(f"Research ID: {results['research_id']}")
    print(f"City: {results['city']}, {results['country']}")
    print(f"Completed: {results['completed_at']}\n")

    print("Agent Results:")
    for agent_id, agent_data in results['agent_results'].items():
        if 'error' in agent_data:
            print(f"  ❌ {agent_id}: {agent_data['error']}")
        else:
            model_info = f"{agent_data.get('llm_provider', 'unknown')}/{agent_data.get('llm_model', 'unknown')}"
            tokens = agent_data.get('tokens_used', 0)
            print(f"  ✓ {agent_id}: {model_info} ({tokens} tokens)")

    print()

    # Show validation
    validation = results['validation_report']
    print(f"Validation: {'✓ Valid' if validation['overall_valid'] else '✗ Issues found'}")

    if validation['recommendations']:
        print("\nRecommendations:")
        for rec in validation['recommendations']:
            print(f"  → {rec}")

    print()

    print_section("💡 Configuration Tips")

    print("""
1. **Using Local Ollama Models:**
   - Install Ollama: https://ollama.ai
   - Pull a model: `ollama pull llama3`
   - In models.yaml, set provider='ollama', model='llama3'
   - apiBase: http://localhost:11434 (default)

2. **Using vLLM Server:**
   - Deploy vLLM with your model
   - In models.yaml, set provider='openai' (vLLM is OpenAI-compatible)
   - Set apiBase to your vLLM endpoint: http://your-server:8000/v1

3. **Using LM Studio:**
   - Start LM Studio server (port 1234)
   - Set provider='openai', apiBase='http://localhost:1234/v1'

4. **Using Text Generation WebUI:**
   - Enable API mode in WebUI
   - Set provider='openai', apiBase='http://localhost:5000/v1'

5. **Custom Research Center Infrastructure:**
   - Configure your internal model endpoint
   - Set provider='openai' for OpenAI-compatible APIs
   - Add apiKey if your endpoint requires authentication

6. **Environment Variables:**
   - Use ${VARIABLE_NAME} in models.yaml
   - System will read from environment
   - Useful for keeping keys out of config files

See config/models.yaml for full examples!
    """)

    print_section("✨ Research Complete")

    print(f"Results saved to: climate_research_system/data/{results['research_id']}.json")
    print("\nEdit config/models.yaml to change model assignments per agent!")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
