"""
Parallel Execution Demo

Compares sequential vs parallel execution performance.
Shows speed improvements when running multiple agents.
"""

import sys
from pathlib import Path
import time

sys.path.append(str(Path(__file__).parent.parent))

from research.orchestrator import ResearchOrchestrator
from research.agents.climate_data_llm import ClimateDataAgent
from research.agents.emissions import EmissionsAgent
from research.agents.vulnerability import VulnerabilityAgent
from research.agents.adaptation import AdaptationAgent
from research.agents.validation import ValidationAgent
from config.config_loader import load_model_config


def print_section(title):
    """Print formatted section header."""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print(f"{'=' * 80}\n")


def print_timing_comparison(sequential_time, parallel_time, num_agents):
    """Print performance comparison."""
    speedup = sequential_time / parallel_time if parallel_time > 0 else 0
    time_saved = sequential_time - parallel_time

    print(f"⏱  Performance Comparison:")
    print(f"   Sequential: {sequential_time:.2f} seconds")
    print(f"   Parallel:   {parallel_time:.2f} seconds")
    print(f"   ")
    print(f"   🚀 Speedup: {speedup:.2f}x faster")
    print(f"   ⏰ Time Saved: {time_saved:.2f} seconds")
    print(f"   📊 Agents: {num_agents}")
    print()


def main():
    """Run parallel execution demonstration."""
    print_section("⚡ Parallel Execution Demo")

    print("This demo shows the performance benefit of parallel agent execution.")
    print()
    print("How it works:")
    print("  • Sequential: Agents run one after another (agent1 → agent2 → agent3...)")
    print("  • Parallel: Agents run simultaneously (agent1 + agent2 + agent3...)")
    print("  • ValidationAgent always runs AFTER all data collection completes")
    print()

    # Initialize orchestrator
    orchestrator = ResearchOrchestrator()

    # Load model configuration
    print("Loading model configuration...")
    try:
        model_config = load_model_config()
    except Exception as e:
        print(f"Warning: Could not load model config: {e}")
        model_config = {'llm': {'provider': 'mock', 'model': 'mock-model'}}

    # Register agents
    print("Registering agents...")
    agents = [
        ClimateDataAgent(agent_id="climate_001", config=model_config),
        EmissionsAgent(agent_id="emissions_001", config=model_config),
        VulnerabilityAgent(agent_id="vulnerability_001", config=model_config),
        AdaptationAgent(agent_id="adaptation_001", config=model_config),
        ValidationAgent(agent_id="validation_001", config=model_config),
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    print(f"✓ Registered {len(orchestrator.agents)} agents")
    print()

    city = "Hamburg"
    country = "Germany"

    # Test 1: Sequential Execution
    print_section(f"🐌 Test 1: Sequential Execution")
    print(f"Researching {city}, {country} with sequential execution...")
    print("(Each agent waits for the previous to complete)\n")

    start_time = time.time()
    results_sequential = orchestrator.research_city(city, country)
    sequential_time = time.time() - start_time

    print(f"\n✓ Sequential execution completed in {sequential_time:.2f} seconds")
    print(f"  Agents: {results_sequential['metadata']['successful_agents']}/{results_sequential['metadata']['total_agents']}")
    print(f"  Sources: {results_sequential.get('total_sources', 0)}")

    # Test 2: Parallel Execution
    print_section(f"⚡ Test 2: Parallel Execution")
    print(f"Researching {city}, {country} with PARALLEL execution...")
    print("(All agents run simultaneously)\n")

    start_time = time.time()
    results_parallel = orchestrator.research_city_parallel(city, country)
    parallel_time = time.time() - start_time

    print(f"\n✓ Parallel execution completed in {parallel_time:.2f} seconds")
    print(f"  Agents: {results_parallel['metadata']['successful_agents']}/{results_parallel['metadata']['total_agents']}")
    print(f"  Sources: {results_parallel.get('total_sources', 0)}")
    print(f"  Execution mode: {results_parallel['metadata'].get('execution_mode', 'unknown')}")

    # Performance Comparison
    print_section("📊 Performance Results")

    num_agents = len([a for a in agents if 'validation' not in a.agent_id.lower()])

    print_timing_comparison(sequential_time, parallel_time, num_agents)

    # Show detailed timing breakdown
    print("Execution Breakdown:")
    print()
    print("Sequential Mode:")
    print("  agent1 ----→ (5s)")
    print("         agent2 ----→ (5s)")
    print("                agent3 ----→ (5s)")
    print("                       agent4 ----→ (5s)")
    print("                              validation ----→ (2s)")
    print(f"  Total: ~{sequential_time:.1f}s")
    print()
    print("Parallel Mode:")
    print("  agent1 ----→ (5s)")
    print("  agent2 ----→ (5s)  ← All run")
    print("  agent3 ----→ (5s)  ← at the")
    print("  agent4 ----→ (5s)  ← same time!")
    print("         validation ----→ (2s)")
    print(f"  Total: ~{parallel_time:.1f}s")
    print()

    # Benefits
    print_section("💡 When to Use Parallel Execution")

    print("✅ Use Parallel When:")
    print("  • You have multiple independent agents")
    print("  • Each agent takes significant time (>2 seconds)")
    print("  • You want faster research results")
    print("  • Agents don't depend on each other's data")
    print()
    print("⚠ Use Sequential When:")
    print("  • Agents depend on previous results")
    print("  • You're debugging agent behavior")
    print("  • Resource constrained (limited CPU/memory)")
    print("  • Agents share rate-limited APIs")
    print()

    # Advanced Usage
    print_section("🔧 Advanced Configuration")

    print("Control parallel workers:")
    print()
    print("  # Run with max 2 agents at a time")
    print("  results = orchestrator.research_city_parallel(")
    print("      city='Berlin',")
    print("      country='Germany',")
    print("      max_workers=2")
    print("  )")
    print()
    print("  # Let system decide (default: all agents at once)")
    print("  results = orchestrator.research_city_parallel(")
    print("      city='Berlin',")
    print("      country='Germany'")
    print("  )")
    print()

    # Summary
    print_section("✨ Summary")

    improvement_pct = ((sequential_time - parallel_time) / sequential_time * 100) if sequential_time > 0 else 0

    print(f"With {num_agents} data collection agents:")
    print(f"  • Parallel execution is {improvement_pct:.0f}% faster")
    print(f"  • Saved {sequential_time - parallel_time:.2f} seconds per research")
    print(f"  • Same results, same validation, faster delivery")
    print()
    print("For 100 cities:")
    print(f"  • Sequential: ~{sequential_time * 100 / 60:.1f} minutes")
    print(f"  • Parallel: ~{parallel_time * 100 / 60:.1f} minutes")
    print(f"  • Time saved: ~{(sequential_time - parallel_time) * 100 / 60:.1f} minutes")
    print()
    print("Both methods produce identical results - parallel just does it faster! 🚀")
    print()


if __name__ == "__main__":
    main()
