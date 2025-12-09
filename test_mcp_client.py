#!/usr/bin/env python3
"""
Simple MCP Client for Testing

This script tests the MCP server by sending requests through stdio.
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_server():
    """Test the MCP server through stdio."""
    # Get the path to the server script
    server_path = "/Users/garikbesson/Documents/work/near/devhub/tools/python/security-vector-store/mcp_server.py"
    
    server_params = StdioServerParameters(
        command="python",
        args=[server_path],
        env={"TOKENIZERS_PARALLELISM": "false"}
    )
    
    print("Connecting to MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✓ Connected to MCP server\n")
            
            # Test 1: List tools
            print("=" * 60)
            print("Test 1: Listing available tools")
            print("=" * 60)
            tools = await session.list_tools()
            print(f"Found {len(tools.tools)} tools:\n")
            for tool in tools.tools:
                print(f"  - {tool.name}")
                print(f"    Description: {tool.description[:80]}...")
                print()
            
            # Test 2: Call query_security_docs
            print("=" * 60)
            print("Test 2: Querying security docs for 'reentrancy'")
            print("=" * 60)
            result = await session.call_tool(
                "query_security_docs",
                arguments={"query": "reentrancy", "n_results": 2}
            )
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        text = content.text
                        print(f"Result ({len(text)} characters):")
                        print(text[:500] + "..." if len(text) > 500 else text)
                        print()
            
            # Test 3: Get all concepts
            print("=" * 60)
            print("Test 3: Getting all concepts")
            print("=" * 60)
            result = await session.call_tool("get_all_concepts", arguments={})
            if result.content:
                for content in result.content:
                    if hasattr(content, 'text'):
                        print(content.text)
                        print()
            
            # Test 4: List resources
            print("=" * 60)
            print("Test 4: Listing resources")
            print("=" * 60)
            resources = await session.list_resources()
            print(f"Found {len(resources.resources)} resources:\n")
            for resource in resources.resources[:5]:  # Show first 5
                print(f"  - {resource.uri}")
                print(f"    Name: {resource.name}")
                print(f"    Description: {resource.description}")
                print()
            if len(resources.resources) > 5:
                print(f"  ... and {len(resources.resources) - 5} more\n")
            
            # Test 5: Read a resource
            if resources.resources:
                print("=" * 60)
                print(f"Test 5: Reading resource {resources.resources[0].uri}")
                print("=" * 60)
                content = await session.read_resource(resources.resources[0].uri)
                print(f"Content ({len(content.contents[0].text)} characters):")
                print(content.contents[0].text[:500] + "..." if len(content.contents[0].text) > 500 else content.contents[0].text)
                print()
            
            # Test 6: List prompts
            print("=" * 60)
            print("Test 6: Listing prompts")
            print("=" * 60)
            prompts = await session.list_prompts()
            print(f"Found {len(prompts.prompts)} prompts:\n")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}")
                print(f"    Description: {prompt.description}")
                print()
            
            print("=" * 60)
            print("✓ All tests completed successfully!")
            print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_mcp_server())
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

