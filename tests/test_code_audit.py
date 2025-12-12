#!/usr/bin/env python3
"""
Test script for code audit functionality
"""

import asyncio
import os
import sys

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


async def test_code_auditor_directly():
    """Test CodeAuditor directly."""
    print("\n" + "=" * 60)
    print("Testing CodeAuditor directly")
    print("=" * 60)

    try:
        # Import CodeAuditor from auditor package
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from auditor.auditor import CodeAuditor

        auditor = CodeAuditor()
        tests_dir = os.path.dirname(os.path.abspath(__file__))
        test_file = os.path.join(tests_dir, "test_contract.rs")

        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return False

        print(f"\nAuditing file: {test_file}\n")
        issues, all_concepts = auditor.audit_file(test_file)
        
        # Group by concept
        issues_by_concept = {}
        for issue in issues:
            concept = issue.get('concept', 'unknown')
            if concept not in issues_by_concept:
                issues_by_concept[concept] = []
            issues_by_concept[concept].append(issue)
        
        total_issues = len(issues)
        if total_issues > 0:
            print(f"Found {total_issues} security issue(s):\n")
        else:
            print("Security Audit Results:\n")
        
        # Show all concepts, even with 0 issues
        for concept_name in sorted(all_concepts):
            concept_issues = issues_by_concept.get(concept_name, [])
            issue_count = len(concept_issues)
            print(f"  {concept_name.upper()} ({issue_count} issue(s)):")
            
            if issue_count > 0:
                for i, issue in enumerate(concept_issues, 1):
                    print(f"    Issue #{i}:")
                    print(f"      File: {issue['file_path']}")
                    print(f"      Line: {issue['line_number']}")
                    print(f"      Problem: {issue['issue_description']}")
                    print(f"      Recommendation: {issue['recommendation']}")
                    print()
            else:
                print(f"    ✓ No issues found for this concept")
                print()
        
        print(f"Total issues found: {total_issues}")
        print("✓ Direct audit completed successfully!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("Code Audit Functionality Test Suite")
    print("=" * 60)

    # Check if concepts directory exists
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    concepts_dir = os.path.join(project_root, "concepts")
    if not os.path.exists(concepts_dir):
        print("\n✗ ERROR: Concepts directory not found!")
        print(f"Expected: {concepts_dir}")
        return

    results = []

    # Test direct CodeAuditor
    results.append(("CodeAuditor", await test_code_auditor_directly()))

    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())
