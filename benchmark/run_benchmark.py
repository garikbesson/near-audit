#!/usr/bin/env python3
"""
Benchmark script for testing security audit tool on dataset examples.

This script runs the audit tool on each example in the dataset and collects results.

Usage:
    python run_benchmark.py                    # Run all projects
    python run_benchmark.py --project <name>   # Run specific project
    python run_benchmark.py -p <name>          # Run specific project (short form)
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any
from auditor.auditor import CodeAuditor

# Add parent directory to path to import auditor
sys.path.insert(0, str(Path(__file__).parent.parent))


def load_metadata() -> Dict[str, Any]:
    """Load metadata.json with expected vulnerabilities."""
    metadata_path = Path(__file__).parent / "dataset" / "metadata.json"
    with open(metadata_path, "r") as f:
        return json.load(f)


def run_audit(project_name: str, concept_name: str) -> Dict[str, Any]:
    """Run audit on a single project directory."""
    project_path = Path(__file__).parent / "dataset" / project_name

    if not project_path.exists():
        return {
            "success": False,
            "error": f"Project directory not found: {project_path}"
        }

    if not project_path.is_dir():
        return {
            "success": False,
            "error": f"Expected directory, got file: {project_path}"
        }

    try:
        auditor = CodeAuditor()

        # Step 1: Index project
        print(f"[{project_name}] Step 1: Indexing project...")
        project_index = auditor.index_project(str(project_path))

        # Step 2: Build method graph
        print(f"[{project_name}] Step 2: Building method graph...")
        method_graph = auditor.build_method_graph(str(project_path), project_index)

        # Step 3: Find relevant methods
        print(f"[{project_name}] Step 3: Finding relevant methods...")
        relevant_methods = auditor.find_relevant_methods(
            concept_name, project_index, method_graph
        )

        # Step 4: Audit relevant methods
        print(f"[{project_name}] Step 4: Auditing relevant methods...")
        audit_results = auditor.audit_relevant_methods(
            concept_name, relevant_methods, str(project_path)
        )

        return {
            "success": True,
            "index": project_index,
            "graph": method_graph,
            "relevant": relevant_methods,
            "audit_results": audit_results
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def compare_results(
    audit_results: List[Dict[str, Any]],
    expected_vulnerabilities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare audit results with expected vulnerabilities."""
    # Create sets of (file, method) tuples for more precise matching
    detected_issues = set()

    for result in audit_results:
        if isinstance(result, dict) and "method" in result:
            file_path = result.get("file", "unknown")
            method = result["method"]
            detected_issues.add((file_path, method))

    expected_issues = {
        (vuln.get("file", "unknown"), vuln["method"])
        for vuln in expected_vulnerabilities
    }

    true_positives = detected_issues & expected_issues
    false_positives = detected_issues - expected_issues
    false_negatives = expected_issues - detected_issues

    precision = len(true_positives) / len(detected_issues) if detected_issues else 0
    recall = len(true_positives) / len(expected_issues) if expected_issues else 0
    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "true_positives": [{"file": f, "method": m} for f, m in true_positives],
        "false_positives": [{"file": f, "method": m} for f, m in false_positives],
        "false_negatives": [{"file": f, "method": m} for f, m in false_negatives],
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "total_detected": len(detected_issues),
        "total_expected": len(expected_issues),
    }


def calculate_summary(results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall summary statistics from all project results."""
    successful_projects = [
        r for r in results.values()
        if r.get("success") and "comparison" in r
    ]
    failed_projects = [
        name for name, r in results.items()
        if not r.get("success")
    ]

    total_projects = len(results)
    successful_count = len(successful_projects)
    failed_count = len(failed_projects)

    # Aggregate metrics across all successful projects
    total_true_positives = 0
    total_false_positives = 0
    total_false_negatives = 0
    total_detected = 0
    total_expected = 0

    for project_result in successful_projects:
        comp = project_result["comparison"]
        total_true_positives += len(comp["true_positives"])
        total_false_positives += len(comp["false_positives"])
        total_false_negatives += len(comp["false_negatives"])
        total_detected += comp["total_detected"]
        total_expected += comp["total_expected"]

    # Calculate overall precision, recall, F1
    overall_precision = (
        total_true_positives / total_detected
        if total_detected > 0
        else 0
    )
    overall_recall = (
        total_true_positives / total_expected
        if total_expected > 0
        else 0
    )
    overall_f1 = (
        2 * overall_precision * overall_recall / (overall_precision + overall_recall)
        if (overall_precision + overall_recall) > 0
        else 0
    )

    # Calculate average metrics (per-project averages)
    avg_precision = (
        sum(r["comparison"]["precision"] for r in successful_projects) / successful_count
        if successful_count > 0
        else 0
    )
    avg_recall = (
        sum(r["comparison"]["recall"] for r in successful_projects) / successful_count
        if successful_count > 0
        else 0
    )
    avg_f1 = (
        sum(r["comparison"]["f1_score"] for r in successful_projects) / successful_count
        if successful_count > 0
        else 0
    )

    return {
        "total_projects": total_projects,
        "successful_projects": successful_count,
        "failed_projects": failed_count,
        "failed_project_names": failed_projects,
        "overall_metrics": {
            "precision": overall_precision,
            "recall": overall_recall,
            "f1_score": overall_f1,
            "true_positives": total_true_positives,
            "false_positives": total_false_positives,
            "false_negatives": total_false_negatives,
            "total_detected": total_detected,
            "total_expected": total_expected,
        },
        "average_metrics": {
            "precision": avg_precision,
            "recall": avg_recall,
            "f1_score": avg_f1,
        },
    }


def main():
    """Run benchmark on all examples or a specific project."""
    parser = argparse.ArgumentParser(
        description="Run security audit benchmark on dataset examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_benchmark.py                           # Run all projects
  python run_benchmark.py --project "0. callbacks_vulnerable"  # Run specific project
  python run_benchmark.py -p "2. private_methods_vulnerable"    # Short form
        """
    )
    parser.add_argument(
        "-p", "--project",
        type=str,
        help="Run benchmark for a specific project (project name from metadata.json)"
    )

    args = parser.parse_args()

    metadata = load_metadata()
    results = {}

    print("=" * 80)
    print("Security Audit Tool Benchmark")
    print("=" * 80)
    print()

    # Filter examples if specific project is requested
    examples_to_run = metadata["examples"]
    if args.project:
        examples_to_run = [
            ex for ex in metadata["examples"]
            if ex["project"] == args.project
        ]
        if not examples_to_run:
            print(f"ERROR: Project '{args.project}' not found in metadata.json")
            print(f"\nAvailable projects:")
            for ex in metadata["examples"]:
                print(f"  - {ex['project']}")
            sys.exit(1)
        print(f"Running benchmark for project: {args.project}\n")

    for example in examples_to_run:
        project_name = example["project"]
        concept_name = example["concept"]
        all_expected_vulns = example.get("expected_vulnerabilities", [])

        # Filter only active vulnerabilities (active: true or missing active field for backward compatibility)
        expected_vulns = [
            vuln for vuln in all_expected_vulns
            if vuln.get("active", True)  # Default to True if "active" field is missing
        ]

        print(f"\n{'=' * 80}")
        print(f"Testing: {project_name}")
        print(f"Concept: {concept_name}")
        print(f"Expected vulnerabilities (active): {len(expected_vulns)} (total: {len(all_expected_vulns)})")
        print(f"{'=' * 80}\n")

        audit_output = run_audit(project_name, concept_name)

        if audit_output["success"]:
            audit_results = audit_output.get("audit_results", [])
            comparison = compare_results(audit_results, expected_vulns)

            results[project_name] = {
                "success": True,
                "concept": concept_name,
                "audit_results_count": len(audit_results),
                "comparison": comparison,
                "expected_vulnerabilities": expected_vulns,
                "detected_issues": audit_results,
            }

            print(f"\nResults for {project_name}:")
            print(f"  Precision: {comparison['precision']:.2%}")
            print(f"  Recall: {comparison['recall']:.2%}")
            print(f"  F1 Score: {comparison['f1_score']:.2%}")
            print(f"  True Positives: {len(comparison['true_positives'])}")
            print(f"  False Positives: {len(comparison['false_positives'])}")
            print(f"  False Negatives: {len(comparison['false_negatives'])}")

            if comparison["false_positives"]:
                print(f"  False Positives: {comparison['false_positives']}")
            if comparison["false_negatives"]:
                print(f"  False Negatives: {comparison['false_negatives']}")
        else:
            results[project_name] = {
                "success": False,
                "error": audit_output.get("error", "Unknown error"),
            }
            print(f"  ERROR: {audit_output.get('error', 'Unknown error')}")

    # Calculate summary
    summary = calculate_summary(results)

    # Save results with summary
    results_path = Path(__file__).parent / "benchmark_results.json"
    output = {
        "summary": summary,
        "projects": results,
    }
    with open(results_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'=' * 80}")
    print("Benchmark complete!")
    print(f"Results saved to: {results_path}")
    print(f"{'=' * 80}\n")

    # Print summary
    print(f"\n{'=' * 80}")
    print("SUMMARY")
    print(f"{'=' * 80}")
    print(f"Total Projects: {summary['total_projects']}")
    print(f"Successful: {summary['successful_projects']}")
    print(f"Failed: {summary['failed_projects']}")
    if summary['failed_project_names']:
        print(f"Failed Projects: {', '.join(summary['failed_project_names'])}")

    if summary['successful_projects'] > 0:
        print(f"\nOverall Metrics (aggregated across all projects):")
        print(f"  Precision: {summary['overall_metrics']['precision']:.2%}")
        print(f"  Recall: {summary['overall_metrics']['recall']:.2%}")
        print(f"  F1 Score: {summary['overall_metrics']['f1_score']:.2%}")
        print(f"  True Positives: {summary['overall_metrics']['true_positives']}")
        print(f"  False Positives: {summary['overall_metrics']['false_positives']}")
        print(f"  False Negatives: {summary['overall_metrics']['false_negatives']}")
        print(f"  Total Detected: {summary['overall_metrics']['total_detected']}")
        print(f"  Total Expected: {summary['overall_metrics']['total_expected']}")

        print(f"\nAverage Metrics (per-project averages):")
        print(f"  Precision: {summary['average_metrics']['precision']:.2%}")
        print(f"  Recall: {summary['average_metrics']['recall']:.2%}")
        print(f"  F1 Score: {summary['average_metrics']['f1_score']:.2%}")


if __name__ == "__main__":
    main()
