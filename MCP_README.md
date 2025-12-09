# MCP Server for NEAR Protocol Security Vector Store

This MCP (Model Context Protocol) server provides access to the NEAR Protocol security documentation vector store.

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure the vector store is created:
```bash
python create-vector.py
```

## Usage

### Running the Server

The server uses stdio transport and can be run directly:

```bash
python mcp_server.py
```

### Integration with Claude Desktop

To use with Claude Desktop, add the configuration to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or the equivalent file on your system:

```json
{
  "mcpServers": {
    "near-security-vector-store": {
      "command": "python",
      "args": [
        "/absolute/path/to/mcp_server.py"
      ],
      "env": {
        "TOKENIZERS_PARALLELISM": "false"
      }
    }
  }
}
```

**Important**: Replace `/absolute/path/to/mcp_server.py` with the absolute path to the `mcp_server.py` file in your project.

### Integration with Cursor IDE

In Cursor IDE, MCP servers are configured through IDE settings. Add the server to the MCP configuration.

## Available Tools

### 1. `query_security_docs`

Queries security documentation from the vector store.

**Parameters:**
- `query` (required): Search query to find relevant security documentation
- `n_results` (optional): Number of results to return (default: 3, max: 10)

**Usage example:**
```json
{
  "query": "reentrancy attacks",
  "n_results": 5
}
```

### 2. `get_all_concepts`

Gets a list of all available security concepts in the vector store.

**Parameters:** None

### 3. `audit_contract_code`

Audits NEAR smart contract code for security vulnerabilities. Analyzes the provided code file using security documentation from the vector store and returns a list of security issues with line numbers, descriptions, and recommendations.

**Parameters:**
- `file_path` (required): Path to the code file to audit (absolute or relative path)

**Usage example:**
```json
{
  "file_path": "/path/to/contract.rs"
}
```

**Returns:**
A structured report containing:
- File path
- Line number for each issue
- Description of the security problem
- Recommendation for fixing the issue

**Example response:**
```
Security Audit Results for: /path/to/contract.rs
============================================================

Found 3 security issue(s):

Issue #1:
  File: /path/to/contract.rs
  Line: 24
  Problem: The deposit function does not check for attached deposit...
  Recommendation: Implement a check for attached deposit...

Issue #2:
  File: /path/to/contract.rs
  Line: 37
  Problem: The withdraw function updates state before making an external call...
  Recommendation: Follow the checks-effects-interactions pattern...
```

## Resources

The server provides access to each document as a resource through URIs in the format:
```
near-security://concept/{concept_name}
```

Examples:
- `near-security://concept/reentrancy`
- `near-security://concept/frontrunning`
- `near-security://concept/storage`

## Prompts

### 1. `security_audit_checklist`

Gets a security audit checklist for NEAR smart contracts.

**Arguments:**
- `contract_type` (optional): Type of contract (e.g., 'NFT', 'FT', 'DeFi', 'general')

### 2. `explain_security_concept`

Explains a specific NEAR security concept in detail.

**Arguments:**
- `concept` (required): Name of the security concept (e.g., 'reentrancy', 'frontrunning', 'storage')

## Project Structure

```
.
├── mcp_server.py          # MCP server
├── code_auditor.py         # Code audit module using RAG
├── mcp_config.json        # Configuration example
├── rag-agent.py           # Original RAG agent
├── create-vector.py       # Script to create vector store
├── test_contract.rs       # Example contract for testing
├── chroma/                # Vector store directory
└── concepts/              # Markdown documentation files
```

## Code Audit Feature

The MCP server includes a code audit feature that analyzes NEAR smart contract code for security vulnerabilities. The audit process:

1. **Reads the code file** - Loads the contract code from the specified path
2. **Queries vector store** - Retrieves relevant security documentation based on code patterns
3. **Analyzes with LLM** - Uses the RAG agent to identify security issues
4. **Returns structured results** - Provides line numbers, problem descriptions, and recommendations

The audit checks for common NEAR security issues including:
- Reentrancy vulnerabilities
- Callback security issues
- Storage cost attacks
- Access control problems
- User verification issues
- Random number generation problems
- Frontrunning vulnerabilities

## Requirements

- Python 3.8+
- chromadb
- openai
- mcp

## Notes

- Make sure the vector store is created before running the server
- The server uses stdio transport for communication
- All requests are processed asynchronously
