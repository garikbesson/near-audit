#!/usr/bin/env python3
"""
Run all tests in the tests directory

Usage:
    python tests/run_tests.py
    python -m tests.run_tests
"""

import os
import sys
import subprocess
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test(test_file, test_name):
    """Run a single test file and return success status."""
    print("\n" + "=" * 70)
    print(f"Running: {test_name}")
    print("=" * 70)

    test_path = os.path.join(os.path.dirname(__file__), test_file)

    if not os.path.exists(test_path):
        print(f"❌ Test file not found: {test_path}")
        return False

    try:
        start_time = time.time()
        result = subprocess.run(
            [sys.executable, test_path],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            capture_output=False,
            text=True
        )
        elapsed_time = time.time() - start_time

        if result.returncode == 0:
            print(f"\n✓ {test_name} passed ({elapsed_time:.2f}s)")
            return True
        else:
            print(f"\n✗ {test_name} failed ({elapsed_time:.2f}s)")
            return False
    except Exception as e:
        print(f"❌ Error running {test_name}: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 70)
    print("Running All Tests")
    print("=" * 70)

    # Check if concepts directory exists
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    concepts_dir = os.path.join(project_root, "concepts")
    if not os.path.exists(concepts_dir):
        print("\n❌ ERROR: Concepts directory not found!")
        print(f"Expected: {concepts_dir}")
        sys.exit(1)

    # List of tests to run
    tests = [
        ("test_code_audit.py", "Code Audit Tests"),
    ]

    results = []
    start_time = time.time()

    for test_file, test_name in tests:
        success = run_test(test_file, test_name)
        results.append((test_name, success))

    # Print summary
    total_time = time.time() - start_time
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for test_name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} test suites passed")
    print(f"Time: {total_time:.2f}s")

    if passed == total:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - passed} test suite(s) failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
