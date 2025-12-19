#!/usr/bin/env python3
"""
Command-line tool for auditing NEAR smart contract code

Usage:
    python auditor/audit.py <file_path> [concept_name]
    python auditor/audit.py index <project_directory>
    python auditor/audit.py graph <project_directory> [concept_name] [--index-file <index.json>] [--output-index <idx.json>] [--output-graph <graph.json>] [--output-relevant <relevant.json>] [--output-audit <audit.json>]

Examples:
    # Audit a single file
    python auditor/audit.py /path/to/contract.rs
    python auditor/audit.py ./tests/test_contract.rs private_methods
    
    # Index a project (standalone)
    python auditor/audit.py index /path/to/contract/project
    
    # Build index and graph (2-step process)
    python auditor/audit.py graph /path/to/contract/project
    
    # Build index, graph, find relevant methods, and audit (4-step process)
    python auditor/audit.py graph ./my-contract private_methods
    python auditor/audit.py graph ./my-contract callbacks --index-file index.json
    python auditor/audit.py graph ./my-contract reentrancy --output-index idx.json --output-graph graph.json --output-relevant relevant.json --output-audit audit.json
"""

import sys
import os
import argparse
import json
import importlib.util

# Import CodeAuditor from the same directory
auditor_path = os.path.join(os.path.dirname(__file__), 'auditor.py')
spec = importlib.util.spec_from_file_location("auditor_module", auditor_path)
auditor_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auditor_module)
CodeAuditor = auditor_module.CodeAuditor


def get_next_audit_dir():
    """Get the next available audit directory number."""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    audits_dir = os.path.join(project_root, "audits")
    
    # Create audits directory if it doesn't exist
    if not os.path.exists(audits_dir):
        os.makedirs(audits_dir)
    
    # Find the next available number
    existing_dirs = []
    if os.path.exists(audits_dir):
        for item in os.listdir(audits_dir):
            item_path = os.path.join(audits_dir, item)
            if os.path.isdir(item_path) and item.isdigit():
                existing_dirs.append(int(item))
    
    if existing_dirs:
        next_num = max(existing_dirs) + 1
    else:
        next_num = 0
    
    return os.path.join(audits_dir, str(next_num))


def cmd_graph(project_dir: str, concept_name: str = None, index_file: str = None, output_index: str = None, output_graph: str = None, output_relevant: str = None, output_audit: str = None):
    """Command to build project index, method relationship graph, find relevant methods, and audit them."""
    print("=" * 70)
    print("NEAR Smart Contract Analysis")
    print("Step 1: Project Indexing")
    print("Step 2: Method Relationship Graph")
    if concept_name:
        print(f"Step 3: Finding Relevant Methods ({concept_name})")
        print(f"Step 4: Auditing Relevant Methods ({concept_name})")
    print("=" * 70)
    print(f"\n📁 Project Directory: {project_dir}")
    
    # Get or create audit directory
    audit_dir = get_next_audit_dir()
    os.makedirs(audit_dir, exist_ok=True)
    print(f"📂 Audit results will be saved to: {audit_dir}")

    # Resolve directory path
    project_dir = os.path.abspath(project_dir)

    # Check if directory exists
    if not os.path.exists(project_dir):
        print(f"❌ Error: Directory not found: {project_dir}")
        print("   Please check the path and try again.")
        sys.exit(1)

    if not os.path.isdir(project_dir):
        print(f"❌ Error: Path is not a directory: {project_dir}")
        sys.exit(1)

    try:
        # Initialize auditor
        auditor = CodeAuditor()

        # Step 1: Build or load project index
        project_index = None
        if index_file:
            index_path = os.path.abspath(index_file)
            if not os.path.exists(index_path):
                print(f"❌ Error: Index file not found: {index_path}")
                sys.exit(1)
            print(f"\n📋 Step 1: Loading project index from: {index_path}")
            with open(index_path, 'r', encoding='utf-8') as f:
                project_index = json.load(f)
            print("✅ Index loaded successfully")
        else:
            print("\n📋 Step 1: Building project index...")
            project_index = auditor.index_project(project_dir)
            print("✅ Project index generated")

        # Save index (always save to audit directory, optionally to custom path)
        index_path = os.path.join(audit_dir, "index.json")
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(project_index, f, indent=2)
        print(f"💾 Index saved to: {index_path}")
        
        if output_index:
            with open(output_index, 'w', encoding='utf-8') as f:
                json.dump(project_index, f, indent=2)
            print(f"💾 Index also saved to: {output_index}")

        # Step 2: Build method relationship graph
        print("\n" + "=" * 70)
        print("📊 Step 2: Building method relationship graph...")
        print("=" * 70)
        method_graph = auditor.build_method_graph(project_dir, project_index)

        # Save graph (always save to audit directory, optionally to custom path)
        graph_path = os.path.join(audit_dir, "graph.json")
        with open(graph_path, 'w', encoding='utf-8') as f:
            json.dump(method_graph, f, indent=2)
        print(f"💾 Graph saved to: {graph_path}")
        
        if output_graph:
            with open(output_graph, 'w', encoding='utf-8') as f:
                json.dump(method_graph, f, indent=2)
            print(f"💾 Graph also saved to: {output_graph}")

        # Step 3: Find relevant methods (if concept_name provided)
        relevant_methods = None
        if concept_name:
            print("\n" + "=" * 70)
            print(f"🔍 Step 3: Finding relevant methods for: {concept_name}")
            print("=" * 70)
            try:
                relevant_methods = auditor.find_relevant_methods(
                    concept_name, project_index, method_graph
                )
                print("✅ Relevant methods identified")

                # Save relevant methods (always save to audit directory, optionally to custom path)
                relevant_path = os.path.join(audit_dir, "relevant.json")
                with open(relevant_path, 'w', encoding='utf-8') as f:
                    json.dump(relevant_methods, f, indent=2)
                print(f"💾 Relevant methods saved to: {relevant_path}")
                
                if output_relevant:
                    with open(output_relevant, 'w', encoding='utf-8') as f:
                        json.dump(relevant_methods, f, indent=2)
                    print(f"💾 Relevant methods also saved to: {output_relevant}")
            except FileNotFoundError as e:
                print(f"⚠️  Warning: {str(e)}")
                print("   Skipping Steps 3-4: Finding and auditing relevant methods")
                relevant_methods = None
            except Exception as e:
                print(f"⚠️  Warning: Error finding relevant methods: {str(e)}")
                print("   Skipping Steps 3-4: Finding and auditing relevant methods")
                relevant_methods = None

        # Step 4: Audit relevant methods (if concept_name and relevant_methods provided)
        audit_issues = None
        if concept_name and relevant_methods:
            print("\n" + "=" * 70)
            print(f"🔒 Step 4: Auditing relevant methods for: {concept_name}")
            print("=" * 70)
            try:
                audit_issues = auditor.audit_relevant_methods(
                    concept_name, relevant_methods, project_dir
                )
                print(f"✅ Audit complete - found {len(audit_issues)} issue(s)")

                # Save audit results (always save to audit directory, optionally to custom path)
                audit_path = os.path.join(audit_dir, "audit.json")
                with open(audit_path, 'w', encoding='utf-8') as f:
                    json.dump(audit_issues, f, indent=2)
                print(f"💾 Audit results saved to: {audit_path}")
                
                if output_audit:
                    with open(output_audit, 'w', encoding='utf-8') as f:
                        json.dump(audit_issues, f, indent=2)
                    print(f"💾 Audit results also saved to: {output_audit}")
            except Exception as e:
                print(f"⚠️  Warning: Error auditing relevant methods: {str(e)}")
                print("   Skipping Step 4: Auditing relevant methods")
                audit_issues = None

        # Display results
        print("\n" + "=" * 70)
        print("✅ Analysis Complete")
        print("=" * 70)

        # Pretty print the graph
        print("\n📊 Method Relationship Graph:")
        print(json.dumps(method_graph, indent=2))

        # Pretty print relevant methods if found
        if relevant_methods:
            print("\n🔍 Relevant Methods:")
            print(json.dumps(relevant_methods, indent=2))

        # Pretty print audit issues if found
        if audit_issues is not None:
            print("\n🔒 Security Audit Results:")
            if len(audit_issues) > 0:
                print(json.dumps(audit_issues, indent=2))
            else:
                print("   ✅ No security issues found - code is safe")

        print("\n📊 Summary:")
        print(f"   - Total relationships found: {len(method_graph)}")
        if relevant_methods and "relevant_methods" in relevant_methods:
            print(f"   - Relevant methods found: {len(relevant_methods.get('relevant_methods', []))}")
        if audit_issues is not None:
            print(f"   - Security issues found: {len(audit_issues)}")
        print(f"\n📂 All results saved to: {audit_dir}")
        print("=" * 70)
        
        # Exit with error code if issues found
        if audit_issues and len(audit_issues) > 0:
            sys.exit(1)
        else:
            sys.exit(0)

    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_index(project_dir: str, output_file: str = None):
    """Command to index a project directory."""
    print("=" * 70)
    print("NEAR Smart Contract Project Index")
    print("=" * 70)
    print(f"\n📁 Project Directory: {project_dir}")

    # Resolve directory path
    project_dir = os.path.abspath(project_dir)

    # Check if directory exists
    if not os.path.exists(project_dir):
        print(f"❌ Error: Directory not found: {project_dir}")
        print("   Please check the path and try again.")
        sys.exit(1)

    if not os.path.isdir(project_dir):
        print(f"❌ Error: Path is not a directory: {project_dir}")
        sys.exit(1)

    try:
        # Initialize auditor
        auditor = CodeAuditor()

        # Build project index
        print("\n📊 Building project index...\n")
        project_index = auditor.index_project(project_dir)

        # Display results
        print("\n" + "=" * 70)
        print("✅ Project Index Generated")
        print("=" * 70)

        # Pretty print the index
        print("\n" + json.dumps(project_index, indent=2))

        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(project_index, f, indent=2)
            print(f"\n💾 Index saved to: {output_file}")

        print("\n" + "=" * 70)
        sys.exit(0)

    except ValueError as e:
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during indexing: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def cmd_audit(file_path: str, concept_name: str = None, verbose: bool = False):
    """Command to audit a single file."""
    # Resolve file path
    file_path = os.path.abspath(file_path)

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

    if concept_name:
        print(f"📋 Concept: {concept_name}")
        print("📊 Analyzing code against specified security concept...\n")
    else:
        print("📊 Analyzing code against all security concepts...\n")

    try:
        # Initialize auditor
        auditor = CodeAuditor()

        # Audit the file
        issues, all_concepts = auditor.audit_file(
            file_path, concept_name=concept_name
        )

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
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during audit: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main():
    """Main function for command-line interface."""
    # Check if first argument is 'index' or 'graph' command
    if len(sys.argv) > 1 and sys.argv[1] == 'index':
        # Index command
        parser = argparse.ArgumentParser(
            description="Build a structured index of a NEAR smart contract project",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python auditor/audit.py index /path/to/contract/project
  python auditor/audit.py index ./my-contract --output index.json
            """
        )
        parser.add_argument(
            "index",
            type=str,
            help="Index command (use 'index' as first argument)"
        )
        parser.add_argument(
            "project_dir",
            type=str,
            help="Path to the project directory containing Rust files"
        )
        parser.add_argument(
            "-o", "--output",
            type=str,
            default=None,
            help="Output file path for JSON index (optional)"
        )
        args = parser.parse_args()
        cmd_index(args.project_dir, args.output)
    elif len(sys.argv) > 1 and sys.argv[1] == 'graph':
        # Graph command (builds index, graph, and finds relevant methods)
        parser = argparse.ArgumentParser(
            description="Build project index, method relationship graph, and find relevant methods",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
This command performs four steps:
  1. Builds a project index (or loads existing one)
  2. Builds a method relationship graph using the index
  3. Finds relevant methods for security analysis (if concept_name provided)
  4. Audits relevant methods for security issues (if concept_name provided)

Examples:
  python auditor/audit.py graph /path/to/contract/project
  python auditor/audit.py graph ./my-contract private_methods
  python auditor/audit.py graph ./my-contract callbacks --index-file index.json
  python auditor/audit.py graph ./my-contract reentrancy --output-index idx.json --output-graph graph.json --output-relevant relevant.json --output-audit audit.json
            """
        )
        parser.add_argument(
            "graph",
            type=str,
            help="Graph command (use 'graph' as first argument)"
        )
        parser.add_argument(
            "project_dir",
            type=str,
            help="Path to the project directory containing Rust files"
        )
        parser.add_argument(
            "concept_name",
            type=str,
            nargs="?",
            default=None,
            help=(
                "Name of the security concept to analyze "
                "(without .md or .json extension). "
                "If provided, Step 3 will find relevant methods for this concept."
            )
        )
        parser.add_argument(
            "--index-file",
            type=str,
            default=None,
            help="Path to existing project index JSON file (optional, will build if not provided)"
        )
        parser.add_argument(
            "--output-index",
            type=str,
            default=None,
            help="Output file path for project index JSON (optional)"
        )
        parser.add_argument(
            "--output-graph",
            type=str,
            default=None,
            help="Output file path for method relationship graph JSON (optional)"
        )
        parser.add_argument(
            "--output-relevant",
            type=str,
            default=None,
            help="Output file path for relevant methods JSON (optional, requires concept_name)"
        )
        parser.add_argument(
            "--output-audit",
            type=str,
            default=None,
            help="Output file path for audit results JSON (optional, requires concept_name)"
        )
        args = parser.parse_args()
        cmd_graph(args.project_dir, args.concept_name, args.index_file, args.output_index, args.output_graph, args.output_relevant, args.output_audit)
    else:
        # Audit command (backward compatibility)
        parser = argparse.ArgumentParser(
            description="Audit NEAR smart contract code for security vulnerabilities",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python auditor/audit.py contract.rs
  python auditor/audit.py /absolute/path/to/contract.rs
  python auditor/audit.py ./src/lib.rs
  python auditor/audit.py contract.rs private_methods
            """
        )

        parser.add_argument(
            "file_path",
            type=str,
            help="Path to the code file to audit (absolute or relative)"
        )

        parser.add_argument(
            "concept_name",
            type=str,
            nargs="?",
            default=None,
            help=(
                "Name of the concept file to use "
                "(without .md or .json extension). "
                "If not specified, all concepts will be checked."
            )
        )

        parser.add_argument(
            "-v", "--verbose",
            action="store_true",
            help="Show verbose output"
        )

        args = parser.parse_args()
        cmd_audit(args.file_path, args.concept_name, args.verbose)

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

    if args.concept_name:
        print(f"📋 Concept: {args.concept_name}")
        print("📊 Analyzing code against specified security concept...\n")
    else:
        print("📊 Analyzing code against all security concepts...\n")

    try:
        # Initialize auditor
        auditor = CodeAuditor()

        # Audit the file
        issues, all_concepts = auditor.audit_file(
            file_path, concept_name=args.concept_name
        )

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
        print(f"❌ Error: {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during audit: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
