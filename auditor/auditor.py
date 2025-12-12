#!/usr/bin/env python3
"""
Code Auditor Module

This module provides functionality to audit NEAR smart contract code
by checking against all security documentation concepts.
"""

import json
import os
import re
from glob import glob
from typing import List, Dict, Any

import openai


class CodeAuditor:
    """Audits NEAR smart contract code for security issues."""

    def __init__(self):
        """Initialize the code auditor with LLM client."""
        self.client = openai.OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key="",
        )

        # Get project root and concepts directory
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.concepts_dir = os.path.join(project_root, "concepts")

    def read_code_file(self, file_path: str) -> str:
        """Read code from a file."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def get_all_concept_files(self) -> List[tuple[str, str]]:
        """
        Get all concept documentation files.

        Returns:
            List of tuples (concept_name, file_path)
        """
        md_files = glob(os.path.join(self.concepts_dir, "*.md"))
        concepts = []

        for file_path in md_files:
            # Get concept name from filename (without .md extension)
            concept_name = os.path.basename(file_path).replace('.md', '')
            concepts.append((concept_name, file_path))

        return concepts

    def read_concept_file(self, file_path: str) -> str:
        """Read a concept documentation file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()

    def analyze_code_with_concept(
        self, 
        code: str, 
        file_path: str, 
        concept_name: str, 
        concept_content: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze code for security issues related to a specific concept.

        Args:
            code: The code to analyze
            file_path: Path to the code file
            concept_name: Name of the security concept
            concept_content: Content of the concept documentation

        Returns:
            List of issues found for this concept
        """
        # Prepare system prompt for code analysis
        system_prompt = (
            f"You are a security expert for NEAR Protocol smart contracts. "
            f"Analyze the provided Rust code for security vulnerabilities related to: {concept_name}\n\n"
            f"Use the provided security documentation about {concept_name} to identify specific problems.\n\n"
            f"For each issue you find, provide:\n"
            f"- The exact line number where the issue occurs\n"
            f"- A clear description of the security problem related to {concept_name}\n"
            f"- A specific recommendation for how to fix it\n\n"
            f"Focus ONLY on issues related to {concept_name} as described in the documentation.\n\n"
            f"Pay attention to the code examples provided in the documentation.\n\n"
            f"Return your analysis as a JSON array of issues. Each issue should have:\n"
            f"- line_number: integer (the line number where the issue is found)\n"
            f"- issue_description: string (description of the security problem)\n"
            f"- recommendation: string (how to fix the issue)\n\n"
            f"If no issues related to {concept_name} are found, return an empty array []."
        )

        # Prepare user prompt with code and concept documentation
        user_prompt = f"""Analyze the following NEAR smart contract code for security issues related to {concept_name}:

File: {file_path}

Code:
```rust
{code}
```

Security Documentation ({concept_name}):
{concept_content}

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

            # Add file_path and concept_name to each issue
            for issue in issues:
                issue['file_path'] = file_path
                issue['concept'] = concept_name

            return issues

        except Exception as e:
            raise Exception(f"Error analyzing code with concept {concept_name}: {str(e)}")

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

    def audit_file(self, file_path: str) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Audit a code file for security issues by checking against all concepts.

        Args:
            file_path: Path to the code file to audit

        Returns:
            Tuple of:
            - List of issues found, each containing:
              - file_path: path to the file
              - line_number: line number where issue was found
              - issue_description: description of the problem
              - recommendation: recommendation for fixing the issue
              - concept: name of the security concept this issue relates to
            - List of all concept names that were checked
        """
        code = self.read_code_file(file_path)

        # Get all concept files
        concepts = self.get_all_concept_files()
        all_concept_names = [name for name, _ in concepts]

        all_issues = []

        # Check code against each concept
        for concept_name, concept_path in concepts:
            try:
                concept_content = self.read_concept_file(concept_path)
                issues = self.analyze_code_with_concept(
                    code,
                    file_path,
                    concept_name,
                    concept_content
                )
                all_issues.extend(issues)
            except Exception as e:
                # Log error but continue with other concepts
                print(f"Warning: Error checking concept {concept_name}: {e}")
                continue

        return all_issues, all_concept_names
