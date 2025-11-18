"""
Data Validation and Source Tracking Demo

Demonstrates the research integrity features:
- Source provenance tracking
- Multi-source verification
- Confidence scoring
- Data quality assessment
"""

import sys
from pathlib import Path

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


def print_sources(sources, limit=None):
    """Print source information."""
    for i, source in enumerate(sources[:limit] if limit else sources, 1):
        reliability_tier = source.get('reliability_tier', 'unknown')
        source_type = source.get('source_type', 'unknown')

        print(f"{i}. {source.get('title', 'Unknown Source')}")
        print(f"   Type: {source_type}")
        print(f"   Reliability: Tier {reliability_tier}")
        print(f"   URL: {source.get('url', 'N/A')}")
        print(f"   Method: {source.get('collection_method', 'unknown')}")
        if source.get('methodology'):
            print(f"   Methodology: {source.get('methodology')}")
        print()


def print_validation_results(validation_report):
    """Print validation results."""
    overall = validation_report.get('overall_assessment', {})

    print(f"Overall Quality: {overall.get('overall_quality', 'unknown').upper()}")
    print(f"Average Confidence: {overall.get('average_confidence', 0.0):.2f}")
    print(f"Total Sources: {validation_report.get('total_sources', 0)}")
    print(f"Cross-verified Facts: {overall.get('cross_verified_facts', 0)}")
    print(f"Ready for Publication: {'✓ Yes' if overall.get('ready_for_publication') else '✗ No'}")

    # Show issues if any
    issues = overall.get('issues', [])
    if issues:
        print(f"\nIssues Identified ({len(issues)}):")
        for issue in issues[:5]:
            print(f"  • {issue}")


def print_provenance_report(provenance):
    """Print data provenance report."""
    print(f"Total Sources: {provenance.get('total_sources', 0)}")
    print(f"Verified Facts: {provenance.get('verified_facts', 0)}")
    print(f"Average Confidence: {provenance.get('average_confidence', 0.0):.2f}")
    print(f"Tier 1 Sources: {provenance.get('tier_1_percentage', 0)}%")

    print("\nSources by Tier:")
    sources_by_tier = provenance.get('sources_by_tier', {})
    for tier, count in sorted(sources_by_tier.items()):
        print(f"  Tier {tier.replace('tier_', '')}: {count} sources")

    print("\nSources by Type:")
    sources_by_type = provenance.get('sources_by_type', {})
    for source_type, count in sorted(sources_by_type.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source_type}: {count}")


def main():
    """Run validation demonstration."""
    print_section("🔍 Climate Research Data Validation & Source Tracking Demo")

    print("This demo shows how the system ensures research integrity through:")
    print("  1. Comprehensive source tracking with provenance")
    print("  2. Multi-source verification and cross-checking")
    print("  3. Confidence scoring based on source reliability")
    print("  4. Data quality assessment and recommendations")
    print()

    # Initialize orchestrator
    orchestrator = ResearchOrchestrator()

    # Load model configuration
    print("Loading model configuration...")
    try:
        model_config = load_model_config()  # Uses default or mock
    except Exception as e:
        print(f"Warning: Could not load model config: {e}")
        print("Using mock configuration")
        model_config = {'llm': {'provider': 'mock', 'model': 'mock-model'}}

    # Register data collection agents
    print("Registering research agents...")
    agents = [
        ClimateDataAgent(agent_id="climate_001", config=model_config),
        EmissionsAgent(agent_id="emissions_001", config=model_config),
        VulnerabilityAgent(agent_id="vulnerability_001", config=model_config),
        AdaptationAgent(agent_id="adaptation_001", config=model_config),
    ]

    for agent in agents:
        orchestrator.register_agent(agent)

    # Register validation agent (runs AFTER data collection)
    validation_agent = ValidationAgent(agent_id="validation_001", config=model_config)
    orchestrator.register_agent(validation_agent)

    print(f"✓ Registered {len(orchestrator.agents)} agents")
    print()

    # Conduct research with validation
    city = "Copenhagen"
    country = "Denmark"

    print_section(f"📊 Researching: {city}, {country}")

    print("Executing research pipeline...")
    print("  → Step 1: Data collection agents gather information")
    print("  → Step 2: Validation agent verifies and assesses quality")
    print("  → Step 3: Sources tracked with full provenance")
    print()

    results = orchestrator.research_city(city, country)

    # Display Results
    print_section("✅ Research Complete")

    print(f"Research ID: {results.get('research_id')}")
    print(f"Completed: {results.get('completed_at')}")
    print(f"Agents Used: {results['metadata']['successful_agents']}/{results['metadata']['total_agents']}")
    print()

    # Show validation results
    validation_report = results.get('validation_report', {})

    if validation_report:
        print_section("🔬 Validation Results")
        print_validation_results(validation_report)
        print()

        # Show provenance report
        if 'provenance_report' in validation_report:
            print_section("📚 Data Provenance Report")
            print_provenance_report(validation_report['provenance_report'])
            print()

        # Show detailed sources
        sources = validation_report.get('sources', [])
        if sources:
            print_section(f"📖 Data Sources ({len(sources)} total)")
            print("Showing sources with full provenance tracking:\n")
            print_sources(sources, limit=10)

            if len(sources) > 10:
                print(f"... and {len(sources) - 10} more sources")
                print("(See full results in data/sources/ directory)")
            print()

    # Show agent-specific validation
    if 'validation_results' in validation_report:
        print_section("📋 Per-Agent Quality Assessment")

        for agent_id, validation in validation_report['validation_results'].items():
            print(f"{agent_id}:")
            print(f"  Confidence Score: {validation.get('confidence_score', 0.0):.2f}")
            print(f"  Number of Sources: {validation.get('num_sources', 0)}")

            issues = validation.get('issues', [])
            if issues:
                print(f"  Issues: {', '.join(issues)}")

            recommendations = validation.get('recommendations', [])
            if recommendations:
                print(f"  Recommendations:")
                for rec in recommendations[:2]:
                    print(f"    • {rec}")
            print()

    # Key findings
    print_section("💡 Key Findings")

    overall = validation_report.get('overall_assessment', {})
    quality = overall.get('overall_quality', 'unknown')

    if quality == 'excellent':
        print("✓ Excellent data quality - ready for publication")
        print("  - High confidence scores across all agents")
        print("  - Multiple authoritative sources verified")
        print("  - Cross-agent consistency confirmed")
    elif quality == 'good':
        print("✓ Good data quality - suitable for research use")
        print("  - Acceptable confidence scores")
        print("  - Reliable sources identified")
        print("  - Minor improvements suggested")
    elif quality == 'moderate':
        print("⚠ Moderate data quality - additional verification recommended")
        print("  - Some sources may need verification")
        print("  - Consider adding more authoritative sources")
    else:
        print("✗ Data quality needs improvement")
        print("  - Insufficient source verification")
        print("  - Add more reliable sources")
        print("  - Cross-check critical facts")

    print()

    # Final summary
    print_section("📁 Results Saved")

    print(f"Research results: climate_research_system/data/{results['research_id']}.json")
    print(f"Source database: climate_research_system/data/sources/sources.json")
    print(f"Source index: climate_research_system/data/sources/index.json")
    print()

    print("=" * 80)
    print("  ✨ Demo Complete")
    print("=" * 80)
    print()
    print("The system now tracks:")
    print("  ✓ Every data source with full metadata")
    print("  ✓ Source reliability tiers (1-5, lower is better)")
    print("  ✓ Collection methods and methodologies")
    print("  ✓ Cross-verification across multiple sources")
    print("  ✓ Confidence scores for each data point")
    print("  ✓ Complete audit trail for research integrity")
    print()


if __name__ == "__main__":
    main()
