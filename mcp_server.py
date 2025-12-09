#!/usr/bin/env python3
"""
MCP Server for NEAR Protocol Security Vector Store

This server provides access to the security documentation vector store
through the Model Context Protocol (MCP).
"""

import asyncio
import os
from typing import Any, Sequence

import chromadb
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    Resource,
    Prompt,
    PromptArgument,
)

from code_auditor import CodeAuditor


# Initialize ChromaDB client and collection
def get_collection():
    """Get the ChromaDB collection for concepts."""
    if not os.path.exists("./chroma/"):
        raise ValueError("Vector store not found. Please run `python create-vector.py` first")
    
    chroma_client = chromadb.PersistentClient(path="./chroma/")
    return chroma_client.get_collection(name='concepts')


# Create MCP server instance
app = Server("near-security-vector-store")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available tools for querying the vector store."""
    return [
        Tool(
            name="query_security_docs",
            description=(
                "Query the NEAR Protocol security documentation vector store. "
                "Returns relevant security concepts and documentation based on the query. "
                "Useful for finding information about security vulnerabilities, best practices, "
                "and attack vectors in NEAR smart contracts."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to find relevant security documentation"
                    },
                    "n_results": {
                        "type": "integer",
                        "description": "Number of results to return (default: 3, max: 10)",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="get_all_concepts",
            description=(
                "Get a list of all available security concepts in the vector store. "
                "Returns the IDs (file paths) of all stored documents."
            ),
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="audit_contract_code",
            description=(
                "Audit NEAR smart contract code for security vulnerabilities. "
                "Analyzes the provided code file using security documentation from the vector store "
                "and returns a list of security issues with line numbers, descriptions, and recommendations."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Path to the code file to audit (absolute or relative path)"
                    }
                },
                "required": ["file_path"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any] | None) -> Sequence[TextContent]:
    """Handle tool calls."""
    collection = get_collection()
    
    if name == "query_security_docs":
        if not arguments or "query" not in arguments:
            return [TextContent(
                type="text",
                text="Error: 'query' parameter is required"
            )]
        
        query = arguments["query"]
        n_results = arguments.get("n_results", 3)
        
        # Clamp n_results to valid range
        n_results = max(1, min(10, n_results))
        
        try:
            # Query the vector store
            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )
            
            # Format results
            if results['documents'] and len(results['documents'][0]) > 0:
                formatted_results = []
                for i, (doc, doc_id, distance) in enumerate(zip(
                    results['documents'][0],
                    results['ids'][0],
                    results['distances'][0] if results.get('distances') else [None] * len(results['documents'][0])
                ), 1):
                    result_text = f"=== Result {i} ===\n"
                    result_text += f"Source: {doc_id}\n"
                    if distance is not None:
                        result_text += f"Similarity: {1 - distance:.4f}\n"
                    result_text += f"\n{doc}\n\n"
                    formatted_results.append(result_text)
                
                return [TextContent(
                    type="text",
                    text="\n".join(formatted_results)
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"No results found for query: {query}"
                )]
                
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error querying vector store: {str(e)}"
            )]
    
    elif name == "get_all_concepts":
        try:
            # Get all documents from the collection
            all_data = collection.get()
            
            if all_data['ids']:
                concepts_list = "\n".join([
                    f"- {doc_id}" for doc_id in all_data['ids']
                ])
                return [TextContent(
                    type="text",
                    text=f"Available security concepts ({len(all_data['ids'])} total):\n\n{concepts_list}"
                )]
            else:
                return [TextContent(
                    type="text",
                    text="No concepts found in the vector store"
                )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error retrieving concepts: {str(e)}"
            )]
    
    elif name == "audit_contract_code":
        if not arguments or "file_path" not in arguments:
            return [TextContent(
                type="text",
                text="Error: 'file_path' parameter is required"
            )]
        
        file_path = arguments["file_path"]
        
        try:
            # Initialize code auditor
            auditor = CodeAuditor()
            
            # Audit the file
            issues = auditor.audit_file(file_path)
            
            # Format results
            if issues:
                result_text = f"Security Audit Results for: {file_path}\n"
                result_text += "=" * 60 + "\n\n"
                result_text += f"Found {len(issues)} security issue(s):\n\n"
                
                for i, issue in enumerate(issues, 1):
                    result_text += f"Issue #{i}:\n"
                    result_text += f"  File: {issue['file_path']}\n"
                    result_text += f"  Line: {issue['line_number']}\n"
                    result_text += f"  Problem: {issue['issue_description']}\n"
                    result_text += f"  Recommendation: {issue['recommendation']}\n"
                    result_text += "\n" + "-" * 60 + "\n\n"
                
                return [TextContent(
                    type="text",
                    text=result_text
                )]
            else:
                return [TextContent(
                    type="text",
                    text=f"Security Audit Results for: {file_path}\n\nNo security issues found. The code appears to be secure based on the security documentation."
                )]
                
        except FileNotFoundError as e:
            return [TextContent(
                type="text",
                text=f"Error: File not found - {str(e)}"
            )]
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error auditing code: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


@app.list_resources()
async def list_resources() -> list[Resource]:
    """List available resources."""
    try:
        collection = get_collection()
        all_data = collection.get()
        
        resources = []
        for doc_id in all_data.get('ids', []):
            # Extract concept name from file path
            concept_name = os.path.basename(doc_id).replace('.md', '')
            resources.append(
                Resource(
                    uri=f"near-security://concept/{concept_name}",
                    name=concept_name,
                    description=f"Security concept: {concept_name}",
                    mimeType="text/markdown"
                )
            )
        
        return resources
    except Exception as e:
        # Return empty list if there's an error
        return []


@app.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    # Convert URI to string if it's an object
    uri_str = str(uri)
    
    if not uri_str.startswith("near-security://concept/"):
        raise ValueError(f"Invalid resource URI: {uri_str}")
    
    concept_name = uri_str.replace("near-security://concept/", "")
    file_path = f"./concepts/{concept_name}.md"
    
    if not os.path.exists(file_path):
        raise ValueError(f"Concept not found: {concept_name}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()


@app.list_prompts()
async def list_prompts() -> list[Prompt]:
    """List available prompts."""
    return [
        Prompt(
            name="security_audit_checklist",
            description="Get a security audit checklist for NEAR smart contracts",
            arguments=[
                PromptArgument(
                    name="contract_type",
                    description="Type of contract (e.g., 'NFT', 'FT', 'DeFi', 'general')",
                    required=False
                )
            ]
        ),
        Prompt(
            name="explain_security_concept",
            description="Explain a specific NEAR security concept in detail",
            arguments=[
                PromptArgument(
                    name="concept",
                    description="Name of the security concept to explain (e.g., 'reentrancy', 'frontrunning', 'storage')",
                    required=True
                )
            ]
        )
    ]


@app.get_prompt()
async def get_prompt(name: str, arguments: dict[str, Any] | None) -> Prompt:
    """Get a prompt by name."""
    collection = get_collection()
    
    if name == "security_audit_checklist":
        # Query for checklist document
        query = "security audit checklist"
        if arguments and "contract_type" in arguments:
            query = f"{query} {arguments['contract_type']}"
        
        results = collection.query(query_texts=[query], n_results=1)
        
        if results['documents'] and len(results['documents'][0]) > 0:
            content = results['documents'][0][0]
        else:
            content = "Security audit checklist not found in vector store."
        
        return Prompt(
            name=name,
            description="Security audit checklist for NEAR smart contracts",
            arguments=[
                PromptArgument(
                    name="contract_type",
                    description="Type of contract",
                    required=False
                )
            ],
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": content
                    }
                }
            ]
        )
    
    elif name == "explain_security_concept":
        if not arguments or "concept" not in arguments:
            raise ValueError("'concept' argument is required")
        
        concept = arguments["concept"]
        results = collection.query(query_texts=[concept], n_results=3)
        
        if results['documents'] and len(results['documents'][0]) > 0:
            content = "\n\n".join(results['documents'][0])
        else:
            content = f"Information about '{concept}' not found in vector store."
        
        return Prompt(
            name=name,
            description=f"Explanation of {concept} security concept",
            arguments=[
                PromptArgument(
                    name="concept",
                    description="Name of the security concept",
                    required=True
                )
            ],
            messages=[
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": content
                    }
                }
            ]
        )
    
    else:
        raise ValueError(f"Unknown prompt: {name}")


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream
        )


if __name__ == "__main__":
    asyncio.run(main())

