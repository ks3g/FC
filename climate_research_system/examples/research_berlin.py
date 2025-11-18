#!/usr/bin/env python3
"""
Example: Research Berlin for Climate Adaptation

Demonstrates the Climate Research Agent Orchestration System by:
1. Setting up the research orchestrator
2. Registering climate research agents
3. Conducting research on Berlin, Germany
4. Displaying results and validation reports
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from research.orchestrator import ResearchOrchestrator
from research.agents.climate_data import ClimateDataAgent


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}\n")


def print_results(results: dict, indent: int = 0):
    """Recursively print results dictionary."""
    prefix = "  " * indent
    for key, value in results.items():
        if isinstance(value, dict):
            print(f"{prefix}{key}:")
            print_results(value, indent + 1)
        elif isinstance(value, list):
            print(f"{prefix}{key}:")
            for item in value:
                if isinstance(item, dict):
                    print_results(item, indent + 1)
                    print()
                else:
                    print(f"{prefix}  - {item}")
        else:
            print(f"{prefix}{key}: {value}")


def main():
    """Main execution function."""
    print_section("Climate Research Agent Orchestration System")
    print("Demonstrating city climate research with Berlin, Germany\n")

    # 1. Initialize the orchestrator
    print("Step 1: Initializing Research Orchestrator...")
    orchestrator = ResearchOrchestrator(storage_dir="climate_research_system/data")
    print(f"✓ Orchestrator created: {orchestrator}")

    # 2. Create and register agents
    print("\nStep 2: Creating and registering research agents...")

    # Climate Data Agent
    climate_agent = ClimateDataAgent(
        agent_id="climate_001",
        config={
            'api_keys': {
                'noaa': 'YOUR_NOAA_API_KEY',  # TODO: Add real API key
                'worldbank': 'YOUR_WORLDBANK_KEY'
            },
            'data_years': 30,  # 30-year climate normal
            'include_projections': True
        }
    )
    orchestrator.register_agent(climate_agent)
    print(f"✓ Registered: {climate_agent.name}")

    # TODO: Add more agents as they are implemented
    # emissions_agent = EmissionsAgent(agent_id="emissions_001")
    # orchestrator.register_agent(emissions_agent)
    # vulnerability_agent = VulnerabilityAgent(agent_id="vulnerability_001")
    # orchestrator.register_agent(vulnerability_agent)

    # 3. Conduct research
    print_section("Conducting Climate Research on Berlin")

    results = orchestrator.research_city(
        city="Berlin",
        country="Germany",
        years=30,  # Climate data period
        focus="climate_adaptation"
    )

    # 4. Display results
    print_section("Research Results")
    print(f"Research ID: {results['research_id']}")
    print(f"City: {results['city']}, {results['country']}")
    print(f"Completed: {results['completed_at']}")

    print("\n--- Metadata ---")
    print_results(results['metadata'])

    print("\n--- Summary ---")
    print_results(results['summary'])

    print("\n--- Agent Results ---")
    for agent_id, agent_data in results['agent_results'].items():
        print(f"\n{agent_id}:")
        if 'error' in agent_data:
            print(f"  ERROR: {agent_data['error']}")
        else:
            print_results(agent_data, indent=1)

    # 5. Display validation report
    print_section("Validation Report")
    validation = results['validation_report']
    print(f"Overall Valid: {validation['overall_valid']}")
    print(f"Validated At: {validation['validated_at']}")

    if validation['inconsistencies']:
        print("\nInconsistencies:")
        for item in validation['inconsistencies']:
            print(f"  ⚠ {item}")

    if validation['missing_data']:
        print("\nMissing Data:")
        for item in validation['missing_data']:
            print(f"  ⚠ {item}")

    if validation['recommendations']:
        print("\nRecommendations:")
        for item in validation['recommendations']:
            print(f"  → {item}")

    # 6. Show saved files
    print_section("Data Persistence")
    print(f"Results saved to: climate_research_system/data/")

    saved_research = orchestrator.list_research()
    print(f"\nAvailable research:")
    for research_id in saved_research:
        print(f"  - {research_id}")

    # 7. Agent status
    print_section("Agent Status")
    for agent_id in orchestrator.agents:
        status = orchestrator.get_agent_status(agent_id)
        print(f"\n{status['name']}:")
        print(f"  Status: {status['status']}")
        print(f"  Messages Processed: {status['message_count']}")
        if status['errors']:
            print(f"  Errors: {len(status['errors'])}")

    print_section("Research Complete!")
    print("Next steps:")
    print("  1. Implement additional agents (Emissions, Vulnerability, etc.)")
    print("  2. Add real API integrations")
    print("  3. Implement Local Data Collection Module")
    print("  4. Implement Presentation Module")
    print("  5. Add more validation rules")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nResearch interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
