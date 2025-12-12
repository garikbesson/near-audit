# Testing the Code Auditor

This guide explains how to test and verify that the code auditor is working correctly.

## Prerequisites

1. Make sure the `concepts/` directory exists with security documentation files

2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

## Quick Test

### Run All Tests

To run all tests at once:

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run all tests
python tests/run_tests.py
```

This will run:
- Code Audit Tests

### Run Individual Tests

Run a specific test script to verify functionality:

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run code audit tests
python tests/test_code_audit.py
```

## Manual Testing

### 1. Test Concepts Directory

You can verify that all concept files are available:

```python
import os
from glob import glob

concepts_dir = "./concepts"
md_files = glob(os.path.join(concepts_dir, "*.md"))
print(f"Total concept files: {len(md_files)}")
for f in md_files:
    print(f"  - {os.path.basename(f)}")
```

### 2. Test Code Auditor Directly

You can test the CodeAuditor class directly:

```python
from auditor.auditor import CodeAuditor

auditor = CodeAuditor()
issues = auditor.audit_file("path/to/contract.rs")

if issues:
    print(f"Found {len(issues)} issues:")
    for issue in issues:
        print(f"Line {issue['line_number']}: {issue['issue_description']}")
```

### 3. Test CLI Tool

You can test the command-line tool:

```bash
python auditor/audit.py tests/test_contract.rs
```

## Expected Results

When running `tests/test_code_audit.py`, you should see:

```
============================================================
Code Audit Functionality Test Suite
============================================================

Testing CodeAuditor directly...
✓ Found X security issue(s)
✓ Direct audit completed successfully!

============================================================
Test Summary
============================================================
✓ PASS: CodeAuditor

Total: 1/1 tests passed
🎉 All tests passed!
```

## Troubleshooting

### Error: "Concepts directory not found"
- Make sure `concepts/` directory exists with security documentation files

### Error: "ModuleNotFoundError"
- Install dependencies: `pip install -r requirements.txt`
- Activate virtual environment: `source venv/bin/activate`

### Error: "No concept files found"
- Make sure `concepts/` directory contains `.md` files with security documentation

### Tests fail with import errors
- Make sure you're running from the project root directory
- Activate the virtual environment if you're using one: `source venv/bin/activate`
- Tests are located in the `tests/` directory and should be run from the project root

## Verifying Data

To verify that the auditor is working correctly:

1. Check that concept files exist:
   ```python
   import os
   from glob import glob
   
   concepts_dir = "./concepts"
   md_files = glob(os.path.join(concepts_dir, "*.md"))
   print(f"Found {len(md_files)} concept files")
   for f in md_files:
       print(f"  - {os.path.basename(f)}")
   ```

2. Test reading a concept file:
   ```python
   with open("./concepts/reentrancy.md", 'r') as f:
       content = f.read()
       print(f"Reentrancy concept: {len(content)} characters")
   ```

3. Test the auditor:
   ```python
   from auditor.auditor import CodeAuditor
   auditor = CodeAuditor()
   issues = auditor.audit_file("tests/test_contract.rs")
   print(f"Found {len(issues)} issues")
   # Issues are grouped by concept
   for issue in issues:
       print(f"  - {issue.get('concept', 'unknown')}: Line {issue['line_number']}")
   ```
