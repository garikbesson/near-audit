#!/usr/bin/env python3
"""
Command-line tool for auditing NEAR smart contract code

Usage:
    python auditor/audit.py <file_path>
    
Example:
    python auditor/audit.py /path/to/contract.rs
    python auditor/audit.py ./tests/test_contract.rs
"""

import sys
import os
import argparse
import importlib.util

# Import CodeAuditor from the same directory
auditor_path = os.path.join(os.path.dirname(__file__), 'auditor.py')
spec = importlib.util.spec_from_file_location("auditor_module", auditor_path)
auditor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor_module)
CodeAuditor = auditor_module.CodeAuditor


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Audit NEAR smart contract code for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python auditor/audit.py contract.rs
  python auditor/audit.py /absolute/path/to/contract.rs
  python auditor/audit.py ./src/lib.rs
        """
    )

    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the code file to audit (absolute or relative)"
    )

    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )

    args = parser.parse_args()

    # Resolve file path
    file_path = os.path.abspath(args.file_path)

    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        print("   Please check the path and try again.")
        sys.exit(1)

    # Check if concepts directory exists
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    concepts_dir = os.path.join(project_root, "concepts")
    if not os.path.exists(concepts_dir):
        print("❌ Error: Concepts directory not found!")
        print(f"   Expected: {concepts_dir}")
        sys.exit(1)

    print("=" * 70)
    print("NEAR Smart Contract Security Audit")
    print("=" * 70)
    print(f"\n📁 File: {file_path}")
    print("📊 Analyzing code against all security concepts...\n")

    try:
        # Initialize auditor
        auditor = CodeAuditor()

        # Audit the file
        issues, all_concepts = auditor.audit_file(file_path)

        # Group issues by concept
        issues_by_concept = {}
        for issue in issues:
            concept = issue.get('concept', 'unknown')
            if concept not in issues_by_concept:
                issues_by_concept[concept] = []
            issues_by_concept[concept].append(issue)

        # Display results grouped by concept (show all concepts)
        print("=" * 70)
        total_issues = len(issues)

        if total_issues > 0:
            print(f"⚠️  Found {total_issues} security issue(s):\n")
        else:
            print("✅ Security Audit Results:\n")

        issue_num = 1
        for concept_name in sorted(all_concepts):
            concept_issues = issues_by_concept.get(concept_name, [])
            issue_count = len(concept_issues)

            print(f"📋 {concept_name.upper()} ({issue_count} issue(s)):")
            print("-" * 70)

            if issue_count > 0:
                for issue in concept_issues:
                    print(f"🔴 Issue #{issue_num}")
                    print(f"   File:    {issue['file_path']}")
                    print(f"   Line:    {issue['line_number']}")
                    print(f"   Problem: {issue['issue_description']}")
                    print(f"   Fix:     {issue['recommendation']}")
                    print()
                    issue_num += 1
            else:
                print("   ✓ No issues found for this concept")
                print()

        print("=" * 70)
        print(f"⚠️  Total issues found: {total_issues}")
        print("=" * 70)
        if total_issues > 0:
            sys.exit(1)  # Exit with error code if issues found
        else:
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during audit: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
