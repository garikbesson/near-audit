#!/usr/bin/env python3
"""
Benchmark script for testing security audit tool on dataset examples.

This script runs the audit tool on each example in the dataset and collects results.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Any

# Add parent directory to path to import auditor
sys.path.insert(0, str(Path(__file__).parent.parent))

from auditor.auditor import CodeAuditor


def load_metadata() -> Dict[str, Any]:
    """Load metadata.json with expected vulnerabilities."""
    metadata_path = Path(__file__).parent / "dataset" / "metadata.json"
    with open(metadata_path, "r") as f:
        return json.load(f)


def run_audit(example_file: str, concept_name: str) -> Dict[str, Any]:
    """Run audit on a single example file."""
    example_path = Path(__file__).parent / "dataset" / example_file
    
    if not example_path.exists():
        return {
            "success": False,
            "error": f"File not found: {example_path}"
        }
    
    # Create a temporary project directory with the example file
    project_dir = example_path.parent / f"temp_{example_file.replace('.rs', '')}"
    project_dir.mkdir(exist_ok=True)
    
    # Copy file to project directory as src/lib.rs
    src_dir = project_dir / "src"
    src_dir.mkdir(exist_ok=True)
    
    import shutil
    shutil.copy(example_path, src_dir / "lib.rs")
    
    try:
        auditor = CodeAuditor()
        
        # Step 1: Index project
        print(f"[{example_file}] Step 1: Indexing project...")
        project_index = auditor.index_project(str(project_dir))
        
        # Step 2: Build method graph
        print(f"[{example_file}] Step 2: Building method graph...")
        method_graph = auditor.build_method_graph(str(project_dir), project_index)
        
        # Step 3: Find relevant methods
        print(f"[{example_file}] Step 3: Finding relevant methods...")
        relevant_methods = auditor.find_relevant_methods(
            concept_name, project_index, method_graph
        )
        
        # Step 4: Audit relevant methods
        print(f"[{example_file}] Step 4: Auditing relevant methods...")
        audit_results = auditor.audit_relevant_methods(
            concept_name, relevant_methods, str(project_dir)
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
    finally:
        # Cleanup
        if project_dir.exists():
            shutil.rmtree(project_dir)


def compare_results(
    audit_results: List[Dict[str, Any]],
    expected_vulnerabilities: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Compare audit results with expected vulnerabilities."""
    detected_methods = set()
    
    for result in audit_results:
        if isinstance(result, dict) and "method" in result:
            detected_methods.add(result["method"])
    
    expected_methods = {vuln["method"] for vuln in expected_vulnerabilities}
    
    true_positives = detected_methods & expected_methods
    false_positives = detected_methods - expected_methods
    false_negatives = expected_methods - detected_methods
    
    precision = len(true_positives) / len(detected_methods) if detected_methods else 0
    recall = len(true_positives) / len(expected_methods) if expected_methods else 0
    f1_score = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )
    
    return {
        "true_positives": list(true_positives),
        "false_positives": list(false_positives),
        "false_negatives": list(false_negatives),
        "precision": precision,
        "recall": recall,
        "f1_score": f1_score,
        "total_detected": len(detected_methods),
        "total_expected": len(expected_methods),
    }


def main():
    """Run benchmark on all examples."""
    metadata = load_metadata()
    results = {}
    
    print("=" * 80)
    print("Security Audit Tool Benchmark")
    print("=" * 80)
    print()
    
    for example in metadata["examples"]:
        example_file = example["file"]
        concept_name = example["concept"]
        expected_vulns = example.get("expected_vulnerabilities", [])
        
        print(f"\n{'=' * 80}")
        print(f"Testing: {example_file}")
        print(f"Concept: {concept_name}")
        print(f"Expected vulnerabilities: {len(expected_vulns)}")
        print(f"{'=' * 80}\n")
        
        audit_output = run_audit(example_file, concept_name)
        
        if audit_output["success"]:
            audit_results = audit_output.get("audit_results", [])
            comparison = compare_results(audit_results, expected_vulns)
            
            results[example_file] = {
                "success": True,
                "concept": concept_name,
                "audit_results_count": len(audit_results),
                "comparison": comparison,
                "expected_vulnerabilities": expected_vulns,
                "detected_issues": audit_results,
            }
            
            print(f"\nResults for {example_file}:")
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
            results[example_file] = {
                "success": False,
                "error": audit_output.get("error", "Unknown error"),
            }
            print(f"  ERROR: {audit_output.get('error', 'Unknown error')}")
    
    # Save results
    results_path = Path(__file__).parent / "benchmark_results.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n{'=' * 80}")
    print("Benchmark complete!")
    print(f"Results saved to: {results_path}")
    print(f"{'=' * 80}\n")
    
    # Summary
    successful = sum(1 for r in results.values() if r.get("success"))
    total = len(results)
    
    print(f"Summary: {successful}/{total} tests completed successfully")
    
    if successful > 0:
        avg_precision = sum(
            r["comparison"]["precision"]
            for r in results.values()
            if r.get("success") and "comparison" in r
        ) / successful
        
        avg_recall = sum(
            r["comparison"]["recall"]
            for r in results.values()
            if r.get("success") and "comparison" in r
        ) / successful
        
        avg_f1 = sum(
            r["comparison"]["f1_score"]
            for r in results.values()
            if r.get("success") and "comparison" in r
        ) / successful
        
        print(f"Average Precision: {avg_precision:.2%}")
        print(f"Average Recall: {avg_recall:.2%}")
        print(f"Average F1 Score: {avg_f1:.2%}")


if __name__ == "__main__":
    main()

