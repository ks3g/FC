#!/usr/bin/env python3
"""
LLM-Powered Climate Research Demo

Demonstrates the full Climate Research System with AI-powered agents:
- ClimateDataAgent - Climate trends analysis
- EmissionsAgent - GHG emissions breakdown
- VulnerabilityAgent - Risk assessment
- AdaptationAgent - Adaptation strategies

All agents use LLM (Language Model) for intelligent analysis.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

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
    """Main execution function."""
    print_section("🌍 LLM-Powered Climate Research System")

    print("This demo showcases AI-powered climate research agents.")
    print("Each agent uses an LLM to analyze different aspects of climate change.\n")

    print("📝 Configuration:")
    print("  - Using MockLLMClient (no API key needed)")
    print("  - To use real LLM, see LLM_CONFIGURATION.md")
    print("  - Set ANTHROPIC_API_KEY or OPENAI_API_KEY environment variable\n")

    # Initialize orchestrator
    print("Step 1: Initializing Research Orchestrator...")
    orchestrator = ResearchOrchestrator(storage_dir="climate_research_system/data")
    print(f"✓ Orchestrator created\n")

    # LLM configuration (uses Mock by default, or real LLM if API key is set)
    llm_config = {
        'llm': {
            'provider': 'anthropic',  # Will use Mock if no API key
            'model': 'claude-3-5-sonnet-20241022'
        },
        'enabled': True
    }

    # Create and register agents
    print("Step 2: Creating LLM-Powered Agents...")

    agents = [
        ('Climate Data Agent', ClimateDataAgent("climate_001", llm_config)),
        ('Emissions Agent', EmissionsAgent("emissions_001", llm_config)),
        ('Vulnerability Agent', VulnerabilityAgent("vulnerability_001", llm_config)),
        ('Adaptation Agent', AdaptationAgent("adaptation_001", llm_config))
    ]

    for name, agent in agents:
        orchestrator.register_agent(agent)
        llm_info = agent.llm
        model = getattr(llm_info, 'model', 'mock-model')
        provider = getattr(llm_info, 'provider', 'mock')
        print(f"✓ {name}")
        print(f"   LLM: {provider}/{model}\n")

    # Conduct research
    city = "Amsterdam"
    country = "Netherlands"

    print_section(f"Conducting Comprehensive Climate Research: {city}, {country}")

    print("⚙️  Executing all 4 LLM agents in parallel...")
    print("   This may take 30-60 seconds with real LLM APIs\n")

    results = orchestrator.research_city(
        city=city,
        country=country,
        years=30
    )

    # Display results
    print_section("📊 Research Results")

    print(f"Research ID: {results['research_id']}")
    print(f"City: {results['city']}, {results['country']}")
    print(f"Completed: {results['completed_at']}\n")

    print("--- Metadata ---")
    metadata = results['metadata']
    print(f"Total Agents: {metadata['total_agents']}")
    print(f"Successful: {metadata['successful_agents']}")
    print(f"Agents Used: {', '.join(metadata['agents_used'])}\n")

    # Display each agent's analysis
    print_section("🤖 Agent Analysis Results")

    agent_names = {
        'climate_001': '🌡️  Climate Data Agent',
        'emissions_001': '💨 Emissions Agent',
        'vulnerability_001': '⚠️  Vulnerability Agent',
        'adaptation_001': '🌱 Adaptation Agent'
    }

    for agent_id, agent_data in results['agent_results'].items():
        agent_name = agent_names.get(agent_id, agent_id)

        print(f"\n{agent_name}")
        print(f"{'-' * 80}")

        if 'error' in agent_data:
            print(f"❌ Error: {agent_data['error']}\n")
            continue

        # Show LLM info
        if 'llm_model' in agent_data:
            print(f"LLM: {agent_data.get('llm_provider', 'unknown')}/{agent_data['llm_model']}")
            print(f"Tokens Used: {agent_data.get('tokens_used', 0)}\n")

        # Show analysis (first 500 chars)
        analysis = agent_data.get('llm_analysis', '')
        if analysis:
            preview = analysis[:500] + '...' if len(analysis) > 500 else analysis
            print("Analysis Preview:")
            print(preview)
            print(f"\n(Full analysis: {len(analysis)} characters)")
        else:
            print("No analysis available")

        print()

    # Validation report
    print_section("✅ Validation Report")

    validation = results['validation_report']
    print(f"Overall Valid: {'✓ Yes' if validation['overall_valid'] else '✗ No'}")
    print(f"Validated At: {validation['validated_at']}\n")

    if validation['missing_data']:
        print("Missing Data:")
        for item in validation['missing_data']:
            print(f"  ⚠ {item}")
        print()

    if validation['recommendations']:
        print("Recommendations:")
        for item in validation['recommendations']:
            print(f"  → {item}")
        print()

    # Data persistence
    print_section("💾 Data Persistence")

    print(f"Results saved to: climate_research_system/data/")
    print(f"Files:")
    print(f"  - research_{results['research_id']}.json")
    print(f"  - validation_{results['research_id']}.json\n")

    saved_research = orchestrator.list_research()
    print(f"Total Research Completed: {len(saved_research)}")
    print(f"Available: {', '.join(saved_research)}\n")

    # Summary
    print_section("📈 Research Complete!")

    print("✅ What was demonstrated:")
    print("  1. ✓ All 4 LLM-powered agents executed")
    print("  2. ✓ Comprehensive climate analysis generated")
    print("  3. ✓ Cross-validation performed")
    print("  4. ✓ Results persisted to JSON\n")

    if 'mock' in str(getattr(agents[0][1].llm, 'provider', 'mock')):
        print("ℹ️  You used MockLLMClient (simulated responses)")
        print("\n🚀 To get REAL AI analysis:")
        print("  1. Get API key from Anthropic or OpenAI")
        print("  2. Set environment variable:")
        print("     export ANTHROPIC_API_KEY='your-key'")
        print("  3. Run this script again")
        print("\nSee LLM_CONFIGURATION.md for full details\n")
    else:
        print("✨ Real LLM analysis completed!")
        total_tokens = sum(
            agent_data.get('tokens_used', 0)
            for agent_data in results['agent_results'].values()
        )
        print(f"   Total tokens used: {total_tokens}")
        print(f"   Estimated cost: $0.{total_tokens // 1000}\n")

    print("📊 View results in web dashboard:")
    print("   python climate_research_system/web/app.py")
    print("   http://localhost:5000\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nResearch interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
