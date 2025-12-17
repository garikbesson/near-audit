# Code Audit Architecture and Workflow

This document describes how the code audit system works, from initialization to result generation.

## Overview

The code audit system analyzes NEAR smart contract code for security vulnerabilities by checking the code against all security concept documentation. It combines:
- **Security Concepts** (Markdown files in `concepts/`) - Contains security documentation
- **LLM** (Fireworks AI) - Analyzes code with context from each concept document
- **Code Auditor Module** - Orchestrates the audit process

## Architecture Components

### 1. CodeAuditor Class (`auditor/auditor.py`)

The main class that orchestrates the audit process.

#### Initialization (`__init__`)

```python
CodeAuditor()
```

**What happens:**
1. Initializes OpenAI client (Fireworks AI) for LLM access
2. Sets up path to `concepts/` directory

**Dependencies:**
- Fireworks AI API key (via `FIREWORKS_API_KEY` environment variable)
- `concepts/` directory with markdown documentation files

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

#### Step 2: Get All Concepts (`get_all_concept_files`)

```python
concepts = auditor.get_all_concept_files()
```

**Process:**
- Scans `concepts/` directory for all `.md` files
- Returns list of tuples: `(concept_name, file_path)`

**Example:**
```python
[
    ("reentrancy", "/path/to/concepts/reentrancy.md"),
    ("storage", "/path/to/concepts/storage.md"),
    ...
]
```

---

#### Step 3: Analyze Code with Each Concept (`analyze_code_with_concept`)

For each concept document, the system:

1. **Reads the concept documentation**
   ```python
   concept_content = auditor.read_concept_file(concept_path)
   ```

2. **Sends code + concept to LLM**
   - System prompt: Focus on issues related to this specific concept
   - User prompt: Code + concept documentation
   - LLM analyzes code for issues related to this concept

3. **Parses LLM response**
   - Extracts JSON array of issues
   - Each issue contains: `line_number`, `issue_description`, `recommendation`
   - Adds `concept` name to each issue

**Process:**
- Creates focused prompt for each concept
- LLM analyzes code specifically for issues related to that concept
- Returns list of issues found for this concept

**Error handling:**
- If LLM fails for one concept, continues with other concepts
- Logs warning but doesn't stop the audit

---

#### Step 4: Collect and Group Results (`audit_file`)

```python
issues = auditor.audit_file(file_path)
```

**Process:**
1. Reads code file
2. Gets all concept files from `concepts/` directory
3. For each concept:
   - Reads concept documentation
   - Analyzes code with this concept
   - Collects issues
4. Returns all issues with `concept` field

**Returns:**
List of issues, each containing:
- `file_path`: path to the audited file
- `line_number`: line number where issue was found
- `issue_description`: description of the problem
- `recommendation`: how to fix the issue
- `concept`: name of the security concept this issue relates to

---

### 3. Result Formatting

#### Grouping by Concept

The CLI tool (`audit.py`) groups issues by concept:

```python
issues_by_concept = {}
for issue in issues:
    concept = issue['concept']
    if concept not in issues_by_concept:
        issues_by_concept[concept] = []
    issues_by_concept[concept].append(issue)
```

**Output format:**
```
📋 REENTRANCY (2 issue(s)):
🔴 Issue #1
   File:    /path/to/contract.rs
   Line:    35
   Problem: ...
   Fix:     ...

📋 STORAGE (1 issue(s)):
🔴 Issue #2
   ...
```

---

## Complete Workflow Diagram

```
┌─────────────────┐
│  audit_file()   │
└────────┬────────┘
         │
         ├──► Read code file
         │
         ├──► Get all concepts from concepts/
         │
         ├──► For each concept:
         │    │
         │    ├──► Read concept.md
         │    │
         │    ├──► analyze_code_with_concept()
         │    │    │
         │    │    ├──► Prepare prompt with code + concept
         │    │    │
         │    │    ├──► Send to LLM
         │    │    │
         │    │    └──► Parse JSON response
         │    │
         │    └──► Collect issues (with concept name)
         │
         └──► Return all issues grouped by concept
```

---

## Error Handling

### File Not Found
- **When:** Code file doesn't exist
- **Error:** `FileNotFoundError`
- **Handled by:** CLI tool shows error message

### Concepts Directory Missing
- **When:** `concepts/` directory doesn't exist
- **Error:** CLI tool checks and exits with error
- **Message:** "Concepts directory not found!"

### LLM API Error
- **When:** API call fails for a specific concept
- **Error:** Exception caught per concept
- **Handled by:** Logs warning, continues with other concepts

### No Issues Found
- **When:** LLM doesn't find any issues
- **Result:** Returns empty list `[]`
- **Display:** "Found 0 security issues."

---

## Key Differences from Previous Version

### Before (Vector Store Approach):
- Used ChromaDB vector store
- Searched for relevant documents using semantic search
- Single LLM call with combined relevant docs
- Results not grouped by concept

### Now (Concept-by-Concept Approach):
- Reads all `.md` files from `concepts/` directory
- One LLM call per concept document
- Each issue tagged with concept name
- Results grouped by concept in output
- More thorough: checks against ALL concepts, not just "relevant" ones

---

## Performance Considerations

- **Number of LLM calls:** Equal to number of concept files (typically 10)
- **Time:** ~10-30 seconds depending on number of concepts
- **Cost:** Higher than before (more LLM calls), but more thorough
- **Accuracy:** Better coverage - checks all security concepts, not just "relevant" ones

---

## Example Output

```
======================================================================
NEAR Smart Contract Security Audit
======================================================================

📁 File: /path/to/contract.rs
📊 Analyzing code against all security concepts...

======================================================================
⚠️  Found 5 security issue(s):

📋 REENTRANCY (2 issue(s)):
----------------------------------------------------------------------
🔴 Issue #1
   File:    /path/to/contract.rs
   Line:    35
   Problem: The withdraw function updates state before external call
   Fix:     Follow checks-effects-interactions pattern

🔴 Issue #2
   File:    /path/to/contract.rs
   Line:    42
   Problem: Cross-contract call without reentrancy guard
   Fix:     Add reentrancy guard

📋 STORAGE (1 issue(s)):
----------------------------------------------------------------------
🔴 Issue #3
   File:    /path/to/contract.rs
   Line:    25
   Problem: No storage cost check in deposit function
   Fix:     Verify attached deposit covers storage costs

📋 CALLBACKS (2 issue(s)):
----------------------------------------------------------------------
🔴 Issue #4
   File:    /path/to/contract.rs
   Line:    50
   Problem: Callback doesn't verify caller
   Fix:     Add callback verification

🔴 Issue #5
   File:    /path/to/contract.rs
   Line:    55
   Problem: Callback can be called multiple times
   Fix:     Add callback guard

======================================================================
⚠️  Total issues found: 5
======================================================================
```

---

## Configuration

### Required Files
- `concepts/*.md` - Security concept documentation files

### API Configuration
- Fireworks AI API key (set via `FIREWORKS_API_KEY` environment variable)
- Model: `accounts/fireworks/models/llama4-maverick-instruct-basic`

### Temperature
- Set to `0.3` for consistent, deterministic analysis
