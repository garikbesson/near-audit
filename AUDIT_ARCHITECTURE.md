# Code Audit Architecture and Workflow

This document describes how the code audit system works, from initialization to result generation.

## Overview

The code audit system uses **RAG (Retrieval Augmented Generation)** to analyze NEAR smart contract code for security vulnerabilities. It combines:
- **Vector Store** (ChromaDB) - Contains security documentation
- **LLM** (Fireworks AI) - Analyzes code with context from documentation
- **Code Auditor Module** - Orchestrates the audit process

## Architecture Components

### 1. CodeAuditor Class (`code_auditor.py`)

The main class that orchestrates the audit process.

#### Initialization (`__init__`)

```python
CodeAuditor()
```

**What happens:**
1. Checks if vector store exists (`./chroma/`)
2. Connects to ChromaDB and loads the `concepts` collection
3. Initializes OpenAI client (Fireworks AI) for LLM access

**Dependencies:**
- ChromaDB vector store must be created (`python create-vector.py`)
- Fireworks AI API key configured

---

### 2. Main Audit Workflow

#### Step 1: Read Code File (`read_code_file`)

```python
code = auditor.read_code_file(file_path)
```

**Process:**
- Validates file exists
- Reads file content as UTF-8 text
- Returns code as string

**Error handling:**
- Raises `FileNotFoundError` if file doesn't exist

---

#### Step 2: Extract Security Context (`get_relevant_security_docs`)

```python
security_docs = auditor.get_relevant_security_docs(code, n_results=5)
```

**Process:**

1. **Pattern Detection** - Scans code for security-related keywords:
   - `callback` or `Promise` → "callbacks cross-contract security"
   - `reentrancy` or `external` → "reentrancy attacks"
   - `storage` or `Storage` → "storage cost attacks"
   - `deposit` or `attached_deposit` → "storage deposit verification"
   - `random` or `random_seed` → "random number generation security"
   - `predecessor` or `signer` → "access keys user verification"

2. **Query Construction** - Combines top 3 detected patterns into query

3. **Vector Store Query** - Searches ChromaDB for relevant documentation:
   ```python
   results = collection.query(query_texts=[query], n_results=5)
   ```

4. **Fallback** - If no specific patterns found:
   - Uses default query: "NEAR smart contract security best practices"
   - If that fails: "security checklist best practices"

5. **Documentation Aggregation** - Combines top 5 results into single text

**Output:** Relevant security documentation as string

---

#### Step 3: Code Analysis (`analyze_code`)

```python
issues = auditor.analyze_code(code, file_path)
```

**Process:**

1. **System Prompt Creation** - Defines LLM role and instructions:
   - Role: Security expert for NEAR Protocol
   - Task: Analyze Rust code for vulnerabilities
   - Focus areas: Reentrancy, callbacks, storage, access control, etc.
   - Output format: JSON array with line numbers, descriptions, recommendations

2. **User Prompt Creation** - Combines:
   - File path
   - Full code (in Rust code block)
   - Security documentation from vector store
   - JSON format specification

3. **LLM Request** - Sends to Fireworks AI:
   ```python
   response = client.chat.completions.create(
       model="llama4-maverick-instruct-basic",
       messages=[system_prompt, user_prompt],
       temperature=0.3  # Low temperature for consistent analysis
   )
   ```

4. **Response Parsing** - Extracts issues from LLM response:
   - Calls `_parse_response()` to extract JSON
   - Adds file_path to each issue
   - Returns list of issues

**Output:** List of issues, each with:
- `file_path`: Path to analyzed file
- `line_number`: Line where issue occurs
- `issue_description`: Description of problem
- `recommendation`: How to fix it

---

#### Step 4: Response Parsing (`_parse_response`)

```python
issues = auditor._parse_response(response_text)
```

**Process:**

1. **JSON Extraction** - Multiple strategies:
   - Try to find JSON in markdown code blocks: ` ```json [...] ``` `
   - Try to find JSON array directly: `[...]`
   - Try parsing entire response as JSON

2. **Validation** - Checks each issue has required fields:
   - `line_number` (converted to int)
   - `issue_description` (string)
   - `recommendation` (string)

3. **Fallback** - If JSON parsing fails:
   - Calls `_extract_issues_from_text()` to parse unstructured text
   - Uses regex to find "Line X:" patterns
   - Extracts descriptions and recommendations

**Output:** Validated list of issues

---

### 3. Public API (`audit_file`)

```python
issues = auditor.audit_file(file_path)
```

**Complete workflow:**
1. Reads code file
2. Analyzes code with security context
3. Returns structured list of issues

**Returns:** List of dictionaries, each containing:
```python
{
    'file_path': '/path/to/file.rs',
    'line_number': 24,
    'issue_description': 'Problem description...',
    'recommendation': 'How to fix...'
}
```

---

## Integration Points

### 1. MCP Server Integration

**Location:** `mcp_server.py`

**Tool:** `audit_contract_code`

**Process:**
1. Receives `file_path` parameter from MCP client
2. Creates `CodeAuditor` instance
3. Calls `audit_file(file_path)`
4. Formats results as MCP `TextContent`
5. Returns to MCP client

**Example:**
```python
result = await call_tool("audit_contract_code", {
    "file_path": "/path/to/contract.rs"
})
```

---

### 2. CLI Tool Integration

**Location:** `audit_code.py`

**Process:**
1. Parses command-line arguments
2. Validates file exists
3. Creates `CodeAuditor` instance
4. Calls `audit_file(file_path)`
5. Formats and displays results
6. Exits with code 0 (no issues) or 1 (issues found)

**Usage:**
```bash
python audit_code.py contract.rs
```

---

## Data Flow Diagram

```
┌─────────────┐
│  User Input │
│ (file_path) │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│  CodeAuditor    │
│  audit_file()   │
└──────┬──────────┘
       │
       ├──► read_code_file()
       │    └──► Returns: code (string)
       │
       ├──► get_relevant_security_docs(code)
       │    ├──► Pattern detection
       │    ├──► Query vector store (ChromaDB)
       │    └──► Returns: security_docs (string)
       │
       └──► analyze_code(code, file_path)
            ├──► Build prompts (system + user)
            ├──► Call LLM (Fireworks AI)
            ├──► Parse response (_parse_response)
            └──► Returns: issues (list of dicts)
                 │
                 └──► Format & return to user
```

---

## Key Design Decisions

### 1. Pattern-Based Query Selection

**Why:** Instead of querying with the entire code, we detect patterns to get more relevant documentation.

**Benefits:**
- Faster queries (smaller search space)
- More relevant results
- Better context for LLM

### 2. Multiple Parsing Strategies

**Why:** LLMs sometimes return JSON in different formats (markdown blocks, plain JSON, etc.)

**Benefits:**
- Robust to LLM output variations
- Fallback to text parsing if JSON fails
- Higher success rate

### 3. Low Temperature (0.3)

**Why:** Code analysis should be consistent and deterministic.

**Benefits:**
- More consistent results
- Less creative/hallucinated issues
- Focused on actual security problems

### 4. Structured Output Format

**Why:** Each issue must have line number, description, and recommendation.

**Benefits:**
- Easy to display in UI
- Can be used in CI/CD pipelines
- Machine-readable format

---

## Error Handling

### File Not Found
- **Location:** `read_code_file()`
- **Action:** Raises `FileNotFoundError`
- **Handled by:** CLI tool and MCP server return error message

### Vector Store Missing
- **Location:** `__init__()`
- **Action:** Raises `ValueError`
- **Message:** "Vector store not found. Please run `python create-vector.py` first"

### LLM API Error
- **Location:** `analyze_code()`
- **Action:** Raises `Exception` with error message
- **Handled by:** Error message returned to user

### JSON Parsing Failure
- **Location:** `_parse_response()`
- **Action:** Falls back to `_extract_issues_from_text()`
- **Result:** Attempts to extract issues from unstructured text

---

## Performance Considerations

### Vector Store Query
- **Time:** ~100-500ms (depends on collection size)
- **Optimization:** Uses top 3 patterns, limits to 5 results

### LLM Request
- **Time:** ~2-10 seconds (depends on code size and API latency)
- **Optimization:** Low temperature for faster, more consistent responses

### Total Audit Time
- **Small file (< 500 lines):** ~3-12 seconds
- **Large file (> 1000 lines):** ~5-20 seconds

---

## Limitations

1. **Line Number Accuracy**
   - LLM may not always identify exact line numbers correctly
   - Depends on code formatting and LLM understanding

2. **False Positives**
   - LLM may flag non-issues as problems
   - Requires human review

3. **Language Support**
   - Optimized for Rust (NEAR smart contracts)
   - May work with other languages but not optimized

4. **Context Window**
   - Very large files may exceed LLM context limits
   - May need to split into smaller chunks

5. **Documentation Coverage**
   - Only finds issues covered in vector store documentation
   - May miss novel attack vectors

---

## Future Improvements

1. **Incremental Analysis** - Split large files into functions/modules
2. **Confidence Scores** - Add confidence level to each issue
3. **Issue Categorization** - Classify issues by severity/type
4. **Code Context** - Include surrounding code context in analysis
5. **Multi-file Analysis** - Analyze entire projects, not just single files
6. **Custom Rules** - Allow users to define custom security rules

