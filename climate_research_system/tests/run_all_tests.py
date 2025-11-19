#!/usr/bin/env python3
"""
Test Runner - Runs All Test Suites

Executes all test suites and provides comprehensive reporting.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tests import test_rag_components
from tests import test_presentation_validation
from tests import test_metrics_sources


def main():
    """Run all test suites."""
    print("\n" + "=" * 80)
    print("CLIMATE RESEARCH SYSTEM - COMPLETE TEST SUITE")
    print("=" * 80 + "\n")

    all_results = []
    test_modules = [
        ("RAG Components", test_rag_components),
        ("Presentation & Validation", test_presentation_validation),
        ("Metrics & Sources", test_metrics_sources)
    ]

    for name, module in test_modules:
        print(f"\n{'=' * 80}")
        print(f"Running: {name}")
        print('=' * 80)

        try:
            success = module.run_tests()
            all_results.append((name, success))
        except Exception as e:
            print(f"\n✗ Test suite {name} failed with error: {e}")
            import traceback
            traceback.print_exc()
            all_results.append((name, False))

    # Print overall summary
    print("\n\n" + "=" * 80)
    print("OVERALL TEST SUMMARY")
    print("=" * 80)

    total_suites = len(all_results)
    passed_suites = sum(1 for _, success in all_results if success)
    failed_suites = total_suites - passed_suites

    for name, success in all_results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}: {name}")

    print("\n" + "-" * 80)
    print(f"Total Test Suites: {total_suites}")
    print(f"Passed: {passed_suites}")
    print(f"Failed: {failed_suites}")

    if failed_suites == 0:
        print("\n🎉 ALL TEST SUITES PASSED!")
        print("=" * 80)
        return 0
    else:
        print(f"\n❌ {failed_suites} TEST SUITE(S) FAILED")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
