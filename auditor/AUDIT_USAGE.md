# Manual Code Audit Usage

This guide explains how to manually audit NEAR smart contract code from the command line.

## Quick Start

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run audit on a contract file
python auditor/audit.py <path_to_file>
```

## Examples

### Audit a file in the tests directory:
```bash
python auditor/audit.py tests/test_contract.rs
```

### Audit a file with absolute path:
```bash
python auditor/audit.py /path/to/your/contract.rs
```

### Audit a file with relative path:
```bash
python auditor/audit.py ./src/lib.rs
python auditor/audit.py ../contracts/my_contract.rs
```

### Verbose output (for debugging):
```bash
python auditor/audit.py -v tests/test_contract.rs
```

## Output Format

The audit tool will display:

1. **File information** - Path to the analyzed file
2. **Analysis progress** - Status message during analysis
3. **Issues found** - Each issue includes:
   - Issue number
   - File path
   - Line number where the issue occurs
   - Problem description
   - Recommendation for fixing

### Example Output:

```
======================================================================
NEAR Smart Contract Security Audit
======================================================================

📁 File: /path/to/contract.rs
📊 Analyzing code for security vulnerabilities...

======================================================================
⚠️  Found 3 security issue(s):

🔴 Issue #1
   File:    /path/to/contract.rs
   Line:    24
   Problem: The deposit function does not check for attached deposit...
   Fix:     Implement a check for attached deposit and user verification...

🔴 Issue #2
   File:    /path/to/contract.rs
   Line:    37
   Problem: The withdraw function updates state before external call...
   Fix:     Follow the checks-effects-interactions pattern...

======================================================================
⚠️  Total issues found: 3
======================================================================
```

## Exit Codes

- **0** - No security issues found (code is secure)
- **1** - Security issues found OR error occurred

This allows you to use the tool in scripts:

```bash
if python auditor/audit.py contract.rs; then
    echo "Code is secure!"
else
    echo "Security issues found!"
fi
```

## Requirements

1. Concepts directory must exist with security documentation:
   - `concepts/` directory with `.md` files
   - Each file describes a security concept

2. Dependencies must be installed:
   ```bash
   pip install -r requirements.txt
   ```

## Troubleshooting

### Error: "File not found"
- Check that the file path is correct
- Use absolute path if relative path doesn't work
- Make sure the file exists and is readable

### Error: "Concepts directory not found"
- Make sure `concepts/` directory exists with security documentation files

### Error: "ModuleNotFoundError"
- Activate virtual environment: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

### No issues found but you expect issues
- The LLM might not have detected the issue
- Try being more explicit in code comments
- Check that all relevant concept files exist in `concepts/` directory

## What Gets Checked

The audit tool checks for:

- ✅ Reentrancy vulnerabilities
- ✅ Callback security issues
- ✅ Storage cost attacks
- ✅ Access control problems
- ✅ User verification issues
- ✅ Random number generation problems
- ✅ Frontrunning vulnerabilities
- ✅ Cross-contract call security
- ✅ State management issues
- ✅ Gas allocation problems

All checks are based on NEAR Protocol security best practices from the concept documentation files in `concepts/` directory. The audit checks code against ALL security concepts, not just "relevant" ones.

