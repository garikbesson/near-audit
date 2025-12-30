#!/usr/bin/env python3
"""
Script to build all vulnerable contract projects in the dataset.

This script attempts to compile each project using `cargo near build non-reproducible-wasm`.
If a project fails to compile, execution stops and the error is displayed.
"""

import os
import sys
import subprocess
from pathlib import Path

def find_projects(dataset_dir: Path):
    """Find all project directories in the dataset."""
    projects = []
    for item in dataset_dir.iterdir():
        if item.is_dir():
            # Match pattern: "number. name_vulnerable" or just "name_vulnerable"
            name = item.name
            if (name.endswith("_vulnerable") or 
                (". " in name and name.split(". ", 1)[1].endswith("_vulnerable"))):
                # Check if it's a valid Rust project (has Cargo.toml)
                if (item / "Cargo.toml").exists():
                    projects.append(item)
    # Sort by directory name (numbers will sort correctly)
    return sorted(projects, key=lambda p: p.name)

def build_project(project_dir: Path):
    """Build a single project using cargo near."""
    print(f"\n{'=' * 80}")
    print(f"Building: {project_dir.name}")
    print(f"Path: {project_dir}")
    print(f"{'=' * 80}\n")
    
    # Change to project directory
    original_cwd = os.getcwd()
    try:
        os.chdir(project_dir)
        
        # Run cargo near build
        result = subprocess.run(
            ["cargo", "near", "build", "non-reproducible-wasm"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print(f"❌ BUILD FAILED: {project_dir.name}")
            print("\nSTDOUT:")
            print(result.stdout)
            print("\nSTDERR:")
            print(result.stderr)
            print(f"\n{'=' * 80}")
            print(f"ERROR: Project {project_dir.name} failed to compile!")
            print(f"{'=' * 80}\n")
            return False
        
        print(f"✅ BUILD SUCCESS: {project_dir.name}")
        return True
        
    finally:
        os.chdir(original_cwd)

def main():
    """Main function to build all projects."""
    # Get the script directory and find dataset
    script_dir = Path(__file__).parent
    benchmark_dir = script_dir.parent
    dataset_dir = benchmark_dir / "dataset"
    
    if not dataset_dir.exists():
        print(f"ERROR: Dataset directory not found: {dataset_dir}")
        sys.exit(1)
    
    projects = find_projects(dataset_dir)
    
    if not projects:
        print(f"ERROR: No projects found in {dataset_dir}")
        sys.exit(1)
    
    print("=" * 80)
    print("Building All Vulnerable Contract Projects")
    print("=" * 80)
    print(f"\nFound {len(projects)} projects:")
    for project in projects:
        print(f"  - {project.name}")
    
    # Build each project
    for i, project in enumerate(projects, 1):
        print(f"\n[{i}/{len(projects)}] Processing {project.name}...")
        
        success = build_project(project)
        
        if not success:
            print(f"\n❌ Build stopped at project: {project.name}")
            print(f"Fix the compilation errors and run the script again.")
            sys.exit(1)
    
    print("\n" + "=" * 80)
    print("✅ ALL PROJECTS BUILT SUCCESSFULLY!")
    print("=" * 80)
    print(f"\nTotal projects built: {len(projects)}")

if __name__ == "__main__":
    main()

