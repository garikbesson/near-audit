# Testing the MCP Server

This guide explains how to test and verify that the MCP server is working correctly and returning data from the vector store.

## Prerequisites

1. Make sure you have created the vector store:
   ```bash
   python create-vector.py
   ```

2. Install dependencies (if not already installed):
   ```bash
   pip install -r requirements.txt
   ```

## Quick Test

Run the test script to verify all functionality:

```bash
# Activate virtual environment (if using one)
source venv/bin/activate

# Run the test suite
python test_mcp_server.py
```

This will test:
- ✓ Direct ChromaDB collection access
- ✓ Getting the collection
- ✓ Listing available tools
- ✓ Querying security documentation
- ✓ Getting all concepts
- ✓ Listing resources
- ✓ Reading resources
- ✓ Listing prompts

## Manual Testing

### 1. Test Direct Collection Access

You can test the ChromaDB collection directly:

```python
import chromadb

client = chromadb.PersistentClient(path="./chroma/")
collection = client.get_collection(name='concepts')

# Get all documents
all_data = collection.get()
print(f"Total documents: {len(all_data['ids'])}")

# Query the collection
results = collection.query(query_texts=["reentrancy"], n_results=3)
print(f"Found {len(results['documents'][0])} results")
```

### 2. Test MCP Server Functions

You can test individual MCP server functions:

```python
import asyncio
from mcp_server import get_collection, list_tools, call_tool

async def test():
    # Test getting collection
    collection = get_collection()
    print(f"Collection: {collection.name}")
    
    # Test listing tools
    tools = await list_tools()
    print(f"Tools: {[t.name for t in tools]}")
    
    # Test querying
    result = await call_tool("query_security_docs", {
        "query": "storage attacks",
        "n_results": 2
    })
    print(f"Query result: {result[0].text[:200]}...")

asyncio.run(test())
```

### 3. Test MCP Server via stdio (Full Integration)

To test the full MCP server integration, you can use the MCP client test script:

```bash
python test_mcp_client.py
```

**Note**: This requires the MCP client library and may need additional setup depending on your MCP client implementation.

## Expected Results

When running `test_mcp_server.py`, you should see:

```
============================================================
MCP Server Test Suite
============================================================

Testing direct ChromaDB collection query...
✓ Collection contains 10 documents
✓ Query returned 3 results

Testing get_collection()...
✓ Collection retrieved successfully

Testing list_tools()...
✓ Found 2 tools:
  - query_security_docs: Query the NEAR Protocol security documentation...
  - get_all_concepts: Get a list of all available security concepts...

Testing query_security_docs tool...
✓ Query successful, returned 15726 characters

Testing get_all_concepts tool...
✓ Retrieved concepts list
  Result: Available security concepts (10 total):
  - ./concepts/callbacks.md
  - ./concepts/storage.md
  ...

Testing list_resources()...
✓ Found 10 resources:
  - near-security://concept/callbacks: callbacks
  - near-security://concept/storage: storage
  ...

Testing read_resource()...
✓ Successfully read resource: near-security://concept/callbacks
  Content length: 6032 characters

Testing list_prompts()...
✓ Found 2 prompts:
  - security_audit_checklist: Get a security audit checklist...
  - explain_security_concept: Explain a specific NEAR security concept...

============================================================
Test Summary
============================================================
✓ PASS: Direct Collection Query
✓ PASS: Get Collection
✓ PASS: List Tools
✓ PASS: Query Security Docs
✓ PASS: Get All Concepts
✓ PASS: List Resources
✓ PASS: Read Resource
✓ PASS: List Prompts

Total: 8/8 tests passed
🎉 All tests passed! The MCP server is working correctly.
```

## Troubleshooting

### Error: "Vector store not found"
- Run `python create-vector.py` to create the vector store first

### Error: "ModuleNotFoundError: No module named 'mcp'"
- Install dependencies: `pip install -r requirements.txt`

### Error: "Collection 'concepts' not found"
- The vector store may not have been created properly
- Delete the `./chroma/` directory and run `python create-vector.py` again

### Tests fail with import errors
- Make sure you're running from the project root directory
- Activate the virtual environment if you're using one: `source venv/bin/activate`

## Verifying Data

To verify that the server is actually returning data from the collection:

1. Check the collection size:
   ```python
   collection = get_collection()
   all_data = collection.get()
   print(f"Documents in collection: {len(all_data['ids'])}")
   ```

2. Test a query:
   ```python
   results = collection.query(query_texts=["security"], n_results=5)
   print(f"Query returned {len(results['documents'][0])} results")
   for i, doc in enumerate(results['documents'][0][:3]):
       print(f"\nResult {i+1}: {doc[:200]}...")
   ```

3. Verify through MCP tools:
   ```python
   result = await call_tool("get_all_concepts", {})
   print(result[0].text)
   ```

## Next Steps

Once testing is complete, you can:
- Integrate the MCP server with Claude Desktop (see `MCP_README.md`)
- Use the server with other MCP-compatible clients
- Extend the server with additional tools or resources

