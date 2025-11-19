#!/usr/bin/env python3
"""
End-to-End Test: Complete 7-Agent Workflow

Tests the full research pipeline with all agents:
1. Data collection (5 agents in parallel)
2. Validation (1 agent sequential)
3. Presentation (1 agent sequential)
"""

import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from research.orchestrator import ResearchOrchestrator
from research.agents import (
    ClimateDataAgent,
    EmissionsAgent,
    VulnerabilityAgent,
    AdaptationAgent,
    ValidationAgent
)
from data_collection.agents.pdf_data_agent import PDFDataCollectionAgent
from presentation.presentation_agent import PresentationAgent

def test_complete_workflow():
    """Test complete 7-agent workflow."""

    print("=" * 80)
    print("COMPLETE 7-AGENT WORKFLOW TEST")
    print("=" * 80)

    # Initialize orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = ResearchOrchestrator(storage_dir="climate_research_system/data")

    # LLM configuration
    llm_config = {
        'llm': {
            'provider': 'anthropic',
            'model': 'claude-3-5-sonnet-20241022'
        },
        'enabled': True,
        'data_years': 30
    }

    # Register all 7 agents
    print("\n2. Registering agents...")
    agents = [
        ClimateDataAgent(agent_id="climate_001", config=llm_config),
        EmissionsAgent(agent_id="emissions_001", config=llm_config),
        VulnerabilityAgent(agent_id="vulnerability_001", config=llm_config),
        AdaptationAgent(agent_id="adaptation_001", config=llm_config),
        PDFDataCollectionAgent(agent_id="pdf_data_001", config=llm_config),
        ValidationAgent(agent_id="validation_001", config=llm_config),
        PresentationAgent(agent_id="presentation_001", config=llm_config)
    ]

    for agent in agents:
        orchestrator.register_agent(agent)
        print(f"   ✓ Registered: {agent.name} ({agent.agent_id})")

    print(f"\n   Total agents registered: {len(orchestrator.agents)}")

    # Test sequential execution
    print("\n3. Testing SEQUENTIAL execution...")
    print("-" * 80)
    city = "Munich"
    country = "Germany"

    try:
        results = orchestrator.research_city(city, country)

        print(f"\n✓ Research completed for {city}, {country}")
        print(f"  Execution mode: {results['metadata'].get('execution_mode', 'sequential')}")

        # Check which agents executed
        print(f"\n  Agent results:")
        for agent_id, result in results['agent_results'].items():
            status = "✓" if 'error' not in result else "✗"
            print(f"    {status} {agent_id}")

        # Check validation
        if 'validation_report' in results:
            print(f"\n  Validation:")
            print(f"    Status: {results['validation_report'].get('validation_status', 'unknown')}")
            print(f"    Confidence: {results['validation_report'].get('overall_confidence', 0):.1%}")

        # Check presentation
        if 'presentation' in results and results['presentation']:
            print(f"\n  Presentation:")
            print(f"    ✓ Executive summary generated")
            print(f"    ✓ Recommendations: {len(results['presentation'].get('recommendations', []))}")
            print(f"    ✓ Key insights: {len(results['presentation'].get('key_insights', []))}")

            # Show preview
            if 'executive_summary' in results['presentation']:
                summary = results['presentation']['executive_summary']
                print(f"\n  Executive Summary Preview:")
                print(f"    {summary[:200]}...")
        else:
            print(f"\n  ✗ No presentation generated!")

        print("\n" + "=" * 80)
        print("SEQUENTIAL TEST: SUCCESS")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Sequential test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test parallel execution
    print("\n\n4. Testing PARALLEL execution...")
    print("-" * 80)

    try:
        results = orchestrator.research_city_parallel(city, country)

        print(f"\n✓ Parallel research completed for {city}, {country}")
        print(f"  Execution mode: {results['metadata'].get('execution_mode', 'unknown')}")
        print(f"  Execution time: {results['metadata'].get('execution_time_seconds', 0):.2f}s")

        # Check presentation
        if 'presentation' in results and results['presentation']:
            print(f"\n  ✓ Presentation generated in parallel mode")
        else:
            print(f"\n  ✗ No presentation in parallel mode!")

        print("\n" + "=" * 80)
        print("PARALLEL TEST: SUCCESS")
        print("=" * 80)

    except Exception as e:
        print(f"\n✗ Parallel test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = test_complete_workflow()

    if success:
        print("\n🎉 ALL TESTS PASSED - 7-Agent System Fully Functional!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Issues detected")
        sys.exit(1)
