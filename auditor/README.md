# Code Auditor Directory

This directory contains all files related to code auditing functionality.

## Contents

- `auditor.py` - Main code auditor module using RAG (contains CodeAuditor class)
- `audit.py` - Command-line tool for auditing code
- `AUDIT_USAGE.md` - Usage documentation
- `AUDIT_ARCHITECTURE.md` - Architecture documentation

## Quick Start

### Audit a contract file:

```bash
python auditor/audit.py <path_to_file>
```

### Examples:

```bash
# Audit a test contract
python auditor/audit.py tests/test_contract.rs

# Audit with absolute path
python auditor/audit.py /path/to/contract.rs

# Verbose output
python auditor/audit.py -v tests/test_contract.rs
```

## Usage

See `AUDIT_USAGE.md` for detailed usage instructions.

## Architecture

See `AUDIT_ARCHITECTURE.md` for detailed architecture documentation.

## Dependencies

- Requires `concepts/` directory with security documentation (`.md` files)
- Uses OpenAI (Fireworks AI) for LLM analysis
- Each concept file is checked against the code separately

## Environment Variables

- `FIREWORKS_API_KEY` - Required. Your Fireworks AI API key for LLM access.
  
  You can set it in two ways:
  
  **Option 1: Using .env file (recommended)**
  ```bash
  # Copy the example file
  cp .env.example .env
  # Edit .env and add your API key
  ```
  
  **Option 2: Export as environment variable**
  ```bash
  export FIREWORKS_API_KEY="your_api_key_here"
  ```

