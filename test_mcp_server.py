#!/usr/bin/env python3
"""
Test script for MCP Server

This script tests the MCP server functionality by directly calling
the server functions to verify they work correctly.
"""

import asyncio
import os
from mcp_server import get_collection


async def test_get_collection():
    """Test that we can get the collection."""
    print("Testing get_collection()...")
    try:
        collection = get_collection()
        print("✓ Collection retrieved successfully")
        return collection
    except Exception as e:
        print(f"✗ Error getting collection: {e}")
        return None


async def test_list_tools():
    """Test listing tools."""
    print("\nTesting list_tools()...")
    try:
        # Call the handler function directly
        from mcp_server import list_tools
        tools = await list_tools()
        print(f"✓ Found {len(tools)} tools:")
        for tool in tools:
            print(f"  - {tool.name}: {tool.description[:60]}...")
        return tools
    except Exception as e:
        print(f"✗ Error listing tools: {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_query_security_docs():
    """Test query_security_docs tool."""
    print("\nTesting query_security_docs tool...")
    try:
        from mcp_server import call_tool
        result = await call_tool(
            "query_security_docs",
            {"query": "reentrancy", "n_results": 2}
        )
        if result and len(result) > 0:
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            print(f"✓ Query successful, returned {len(text)} characters")
            print(f"  Preview: {text[:200]}...")
            return True
        else:
            print("✗ Query returned no results")
            return False
    except Exception as e:
        print(f"✗ Error querying: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_get_all_concepts():
    """Test get_all_concepts tool."""
    print("\nTesting get_all_concepts tool...")
    try:
        from mcp_server import call_tool
        result = await call_tool("get_all_concepts", {})
        if result and len(result) > 0:
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            print("✓ Retrieved concepts list")
            print(f"  Result: {text[:300]}...")
            return True
        else:
            print("✗ No concepts returned")
            return False
    except Exception as e:
        print(f"✗ Error getting concepts: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_resources():
    """Test listing resources."""
    print("\nTesting list_resources()...")
    try:
        from mcp_server import list_resources
        resources = await list_resources()
        print(f"✓ Found {len(resources)} resources:")
        for resource in resources[:5]:  # Show first 5
            print(f"  - {resource.uri}: {resource.name}")
        if len(resources) > 5:
            print(f"  ... and {len(resources) - 5} more")
        return True
    except Exception as e:
        print(f"✗ Error listing resources: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_read_resource():
    """Test reading a resource."""
    print("\nTesting read_resource()...")
    try:
        # Try to read the first available resource
        from mcp_server import list_resources, read_resource
        resources = await list_resources()
        if resources:
            uri = resources[0].uri
            content = await read_resource(uri)
            print(f"✓ Successfully read resource: {uri}")
            print(f"  Content length: {len(content)} characters")
            print(f"  Preview: {content[:200]}...")
            return True
        else:
            print("✗ No resources available to test")
            return False
    except Exception as e:
        print(f"✗ Error reading resource: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_list_prompts():
    """Test listing prompts."""
    print("\nTesting list_prompts()...")
    try:
        from mcp_server import list_prompts
        prompts = await list_prompts()
        print(f"✓ Found {len(prompts)} prompts:")
        for prompt in prompts:
            print(f"  - {prompt.name}: {prompt.description}")
        return True
    except Exception as e:
        print(f"✗ Error listing prompts: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_audit_contract_code():
    """Test audit_contract_code tool."""
    print("\nTesting audit_contract_code tool...")
    try:
        from mcp_server import call_tool
        import os
        
        # Check if test contract exists
        test_file = os.path.abspath("test_contract.rs")
        if not os.path.exists(test_file):
            print(f"  ⚠ Test file not found: {test_file}")
            print("  Skipping audit test (create test_contract.rs to test)")
            return True  # Not a failure, just missing test file
        
        result = await call_tool(
            "audit_contract_code",
            {"file_path": test_file}
        )
        
        if result and len(result) > 0:
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            # Check if we got meaningful results
            if "security issue" in text.lower() or "no security issues" in text.lower():
                print(f"✓ Audit completed, found issues or confirmed no issues")
                print(f"  Result length: {len(text)} characters")
                return True
            else:
                print(f"✗ Unexpected result format")
                return False
        else:
            print("✗ No results returned")
            return False
    except Exception as e:
        print(f"✗ Error auditing code: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_direct_collection_query():
    """Test direct ChromaDB collection query."""
    print("\nTesting direct ChromaDB collection query...")
    try:
        collection = get_collection()
        # Get all documents
        all_data = collection.get()
        print(f"✓ Collection contains {len(all_data.get('ids', []))} documents")
        
        # Test a query
        results = collection.query(query_texts=["security"], n_results=3)
        if results['documents'] and len(results['documents'][0]) > 0:
            print(f"✓ Query returned {len(results['documents'][0])} results")
            print(f"  First result ID: {results['ids'][0][0]}")
            print(f"  First result preview: {results['documents'][0][0][:150]}...")
            return True
        else:
            print("✗ Query returned no results")
            return False
    except Exception as e:
        print(f"✗ Error querying collection: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("=" * 60)
    print("MCP Server Test Suite")
    print("=" * 60)
    
    # Check if vector store exists
    if not os.path.exists("./chroma/"):
        print("\n✗ ERROR: Vector store not found!")
        print("Please run 'python create-vector.py' first to create the vector store.")
        return
    
    results = []
    
    # Run tests
    results.append(("Direct Collection Query", await test_direct_collection_query()))
    results.append(("Get Collection", await test_get_collection() is not None))
    results.append(("List Tools", await test_list_tools() is not None))
    results.append(("Query Security Docs", await test_query_security_docs()))
    results.append(("Get All Concepts", await test_get_all_concepts()))
    results.append(("List Resources", await test_list_resources()))
    results.append(("Read Resource", await test_read_resource()))
    results.append(("List Prompts", await test_list_prompts()))
    results.append(("Audit Contract Code", await test_audit_contract_code()))
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 All tests passed! The MCP server is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())

