#!/usr/bin/env python3
"""
Code Auditor Module

This module provides functionality to audit NEAR smart contract code
using RAG (Retrieval Augmented Generation) with the security vector store.
"""

import json
import os
import re
from typing import List, Dict, Any, Optional

import chromadb
import openai


class CodeAuditor:
    """Audits NEAR smart contract code for security issues."""
    
    def __init__(self):
        """Initialize the code auditor with vector store and LLM client."""
        if not os.path.exists("./chroma/"):
            raise ValueError("Vector store not found. Please run `python create-vector.py` first")
        
        self.chroma_client = chromadb.PersistentClient(path="./chroma/")
        self.collection = self.chroma_client.get_collection(name='concepts')
        
        self.client = openai.OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key="fw_3ZQM5aAfHYH3obNHgjDZbBRc",
        )
    
    def read_code_file(self, file_path: str) -> str:
        """Read code from a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def get_relevant_security_docs(self, code: str, n_results: int = 5) -> str:
        """Get relevant security documentation for the code."""
        # Extract key terms from code for better querying
        # Look for common NEAR patterns and security-related terms
        query_terms = []
        
        # Check for common security-related patterns
        if 'callback' in code.lower() or 'Promise' in code:
            query_terms.append("callbacks cross-contract security")
        if 'reentrancy' in code.lower() or 'external' in code.lower():
            query_terms.append("reentrancy attacks")
        if 'storage' in code.lower() or 'Storage' in code:
            query_terms.append("storage cost attacks")
        if 'deposit' in code.lower() or 'attached_deposit' in code:
            query_terms.append("storage deposit verification")
        if 'random' in code.lower() or 'random_seed' in code:
            query_terms.append("random number generation security")
        if 'predecessor' in code.lower() or 'signer' in code.lower():
            query_terms.append("access keys user verification")
        
        # Default query if no specific terms found
        if not query_terms:
            query_terms.append("NEAR smart contract security best practices")
        
        # Query vector store with combined terms
        query = " ".join(query_terms[:3])  # Use top 3 terms
        results = self.collection.query(query_texts=[query], n_results=n_results)
        
        if results['documents'] and len(results['documents'][0]) > 0:
            return "\n\n".join(results['documents'][0])
        else:
            # Fallback to general security docs
            results = self.collection.query(
                query_texts=["security checklist best practices"],
                n_results=n_results
            )
            if results['documents'] and len(results['documents'][0]) > 0:
                return "\n\n".join(results['documents'][0])
            return ""
    
    def analyze_code(self, code: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Analyze code for security issues.
        
        Returns a list of issues, each containing:
        - file_path: path to the file
        - line_number: line number where issue was found
        - issue_description: description of the problem
        - recommendation: recommendation for fixing the issue
        """
        # Get relevant security documentation
        security_docs = self.get_relevant_security_docs(code)
        
        # Prepare system prompt for code analysis
        system_prompt = (
            "You are a security expert for NEAR Protocol smart contracts. "
            "Analyze the provided Rust code for security vulnerabilities and issues.\n\n"
            "Use the provided security documentation to identify problems.\n\n"
            "For each issue you find, provide:\n"
            "- The exact line number where the issue occurs\n"
            "- A clear description of the security problem\n"
            "- A specific recommendation for how to fix it\n\n"
            "Focus on:\n"
            "- Reentrancy vulnerabilities\n"
            "- Callback security issues\n"
            "- Storage cost attacks\n"
            "- Access control problems\n"
            "- User verification issues\n"
            "- Random number generation problems\n"
            "- Frontrunning vulnerabilities\n"
            "- Any other NEAR-specific security concerns\n\n"
            "Return your analysis as a JSON array of issues. Each issue should have:\n"
            "- line_number: integer (the line number where the issue is found)\n"
            "- issue_description: string (description of the security problem)\n"
            "- recommendation: string (how to fix the issue)\n\n"
            "If no issues are found, return an empty array []."
        )
        
        # Prepare user prompt with code and documentation
        user_prompt = f"""Analyze the following NEAR smart contract code for security issues:

File: {file_path}

Code:
```rust
{code}
```

Security Documentation:
{security_docs}

Provide your analysis as a JSON array. Format:
[
  {{
    "line_number": <number>,
    "issue_description": "<description>",
    "recommendation": "<recommendation>"
  }}
]

Return ONLY valid JSON, no additional text."""
        
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent analysis
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Try to extract JSON from response
            issues = self._parse_response(response_text)
            
            # Add file_path to each issue
            for issue in issues:
                issue['file_path'] = file_path
            
            return issues
            
        except Exception as e:
            raise Exception(f"Error analyzing code: {str(e)}")
    
    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract issues."""
        # Try to find JSON in the response
        # Sometimes LLM wraps JSON in markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r'(\[.*?\])', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to parse the whole response as JSON
                json_str = response_text
        
        try:
            issues = json.loads(json_str)
            if not isinstance(issues, list):
                return []
            
            # Validate and clean issues
            validated_issues = []
            for issue in issues:
                if isinstance(issue, dict) and all(key in issue for key in ['line_number', 'issue_description', 'recommendation']):
                    validated_issues.append({
                        'line_number': int(issue['line_number']),
                        'issue_description': str(issue['issue_description']),
                        'recommendation': str(issue['recommendation'])
                    })
            
            return validated_issues
            
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract issues manually
            return self._extract_issues_from_text(response_text)
    
    def _extract_issues_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Fallback: try to extract issues from unstructured text."""
        issues = []
        
        # Look for patterns like "Line X:" or "Line X -" or similar
        line_pattern = r'(?:line|Line)\s+(\d+)[:\-]\s*(.+?)(?=(?:line|Line)\s+\d+[:\-]|$)'
        matches = re.finditer(line_pattern, text, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            line_num = int(match.group(1))
            content = match.group(2).strip()
            
            # Try to split description and recommendation
            if 'recommendation' in content.lower() or 'fix' in content.lower():
                parts = re.split(r'(?:recommendation|fix|solution)[:\-]', content, flags=re.IGNORECASE)
                if len(parts) >= 2:
                    issue_desc = parts[0].strip()
                    recommendation = parts[1].strip()
                else:
                    issue_desc = content
                    recommendation = "Review the code and apply security best practices."
            else:
                issue_desc = content
                recommendation = "Review the code and apply security best practices."
            
            issues.append({
                'line_number': line_num,
                'issue_description': issue_desc,
                'recommendation': recommendation
            })
        
        return issues
    
    def audit_file(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Audit a code file for security issues.
        
        Args:
            file_path: Path to the code file to audit
            
        Returns:
            List of issues found, each containing:
            - file_path: path to the file
            - line_number: line number where issue was found
            - issue_description: description of the problem
            - recommendation: recommendation for fixing the issue
        """
        code = self.read_code_file(file_path)
        return self.analyze_code(code, file_path)

