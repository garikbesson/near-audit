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
            api_key="fw_3ZhJ7fyeBwaWGbPYn1tANbDg",
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

    def get_all_concept_files(
        self, concept_name: str = None
    ) -> List[tuple[str, str]]:
        """
        Get concept documentation files.

        Args:
            concept_name: Optional name of specific concept file
                         (without .md or .json extension).
                         If None, returns all concept files (.md and .json).

        Returns:
            List of tuples (concept_name, file_path)
        """
        if concept_name:
            # Try to find concept file with .md or .json extension
            md_path = os.path.join(self.concepts_dir, f"{concept_name}.md")
            json_path = os.path.join(self.concepts_dir, f"{concept_name}.json")
            
            if os.path.exists(md_path):
                return [(concept_name, md_path)]
            elif os.path.exists(json_path):
                return [(concept_name, json_path)]
            else:
                raise FileNotFoundError(
                    f"Concept file not found: {concept_name}\n"
                    f"Expected path: {md_path} or {json_path}"
                )
        else:
            # Get all concept files (.md and .json)
            md_files = glob(os.path.join(self.concepts_dir, "*.md"))
            json_files = glob(os.path.join(self.concepts_dir, "*.json"))
            concepts = []

            for file_path in md_files:
                # Get concept name from filename (without .md extension)
                concept_name = os.path.basename(file_path).replace('.md', '')
                concepts.append((concept_name, file_path))

            for file_path in json_files:
                # Get concept name from filename (without .json extension)
                concept_name = os.path.basename(file_path).replace('.json', '')
                # Only add if not already added
                # (avoid duplicates if both .md and .json exist)
                if not any(name == concept_name for name, _ in concepts):
                    concepts.append((concept_name, file_path))

            return concepts

    def read_concept_file(self, file_path: str) -> str:
        """
        Read a concept documentation file.
        Supports both .md (markdown) and .json formats.
        For JSON files, converts to a readable text format for LLM.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if it's a JSON file
        if file_path.endswith('.json'):
            try:
                json_data = json.loads(content)
                return self._format_json_concept(json_data)
            except json.JSONDecodeError as e:
                raise ValueError(
                    f"Invalid JSON in concept file {file_path}: {e}"
                )
        
        # For .md files, return as-is
        return content
    
    def _format_json_concept(self, json_data: Dict[str, Any]) -> str:
        """
        Convert JSON concept file to readable text format for LLM.
        """
        lines = []
        
        # Add concept name
        concept_name = json_data.get('concept', 'unknown')
        lines.append(f"# {concept_name.upper()}")
        lines.append("")
        
        # Add rules
        if 'rules' in json_data and json_data['rules']:
            lines.append("## Rules")
            lines.append("")
            for rule in json_data['rules']:
                rule_id = rule.get('id', '')
                description = rule.get('description', '')
                check = rule.get('check', '')
                lines.append(f"**{rule_id}**: {description}")
                if check:
                    lines.append(f"  - Check: {check}")
                lines.append("")
        
        # Add bad examples
        if 'bad_examples' in json_data and json_data['bad_examples']:
            lines.append("## Bad Examples (Vulnerabilities)")
            lines.append("")
            for example in json_data['bad_examples']:
                rule_id = example.get('rule_id', '')
                code = example.get('code', '')
                explanation = example.get('explanation', '')
                lines.append(f"**Rule {rule_id} - Vulnerable Code:**")
                lines.append("```rust")
                lines.append(code)
                lines.append("```")
                lines.append(f"*Explanation*: {explanation}")
                lines.append("")
        
        # Add good examples
        if 'good_examples' in json_data and json_data['good_examples']:
            lines.append("## Good Examples (Secure Code)")
            lines.append("")
            for example in json_data['good_examples']:
                rule_id = example.get('rule_id', '')
                code = example.get('code', '')
                explanation = example.get('explanation', '')
                lines.append(f"**Rule {rule_id} - Secure Code:**")
                lines.append("```rust")
                lines.append(code)
                lines.append("```")
                lines.append(f"*Explanation*: {explanation}")
                lines.append("")
        
        # Add do_not_flag patterns
        if 'do_not_flag' in json_data and json_data['do_not_flag']:
            lines.append("## What NOT to Flag")
            lines.append("")
            for item in json_data['do_not_flag']:
                pattern = item.get('pattern', '')
                explanation = item.get('explanation', '')
                lines.append(f"- **{pattern}**: {explanation}")
            lines.append("")
        
        return "\n".join(lines)

    def analyze_code_with_concept(
        self, 
        code: str, 
        file_path: str, 
        concept_name: str, 
        concept_content: str
    ) -> List[Dict[str, Any]]:
        """
        Analyze code for security issues related to a specific concept.
        Uses two-pass approach: first enumerate potential locations, then check each.

        Args:
            code: The code to analyze
            file_path: Path to the code file
            concept_name: Name of the security concept
            concept_content: Content of the concept documentation

        Returns:
            List of issues found for this concept
        """
        # PASS 1: Enumerate all locations where issues COULD exist
        print(f"\n[PASS 1] Analyzing {concept_name} - Enumerating potential locations...")
        potential_locations = self._pass1_enumerate_locations(
            code, file_path, concept_name, concept_content
        )
        
        print(f"[PASS 1] Found {len(potential_locations)} potential location(s) to check")
        if potential_locations:
            for i, loc in enumerate(potential_locations, 1):
                print(
                    f"  {i}. {loc.get('function_name', 'unknown')} "
                    f"(lines {loc.get('line_range', 'unknown')})"
                )
        
        if not potential_locations:
            print(f"[PASS 1] No potential locations found for {concept_name}")
            return []
        
        # PASS 2: Check each location for actual vulnerabilities
        print(f"\n[PASS 2] Checking {len(potential_locations)} location(s) for vulnerabilities...")
        issues = self._pass2_check_locations(
            code, file_path, concept_name, concept_content, potential_locations
        )
        
        print(f"[PASS 2] Found {len(issues)} actual vulnerability/vulnerabilities")
        if issues:
            for i, issue in enumerate(issues, 1):
                print(
                    f"  {i}. Line {issue.get('line_number', 'unknown')}: "
                    f"{issue.get('issue_description', 'No description')[:60]}..."
                )
        
        # Add file_path and concept_name to each issue
        for issue in issues:
            issue['file_path'] = file_path
            issue['concept'] = concept_name
        
        return issues

    def _pass1_enumerate_locations(
        self,
        code: str,
        file_path: str,
        concept_name: str,
        concept_content: str
    ) -> List[Dict[str, Any]]:
        """
        Pass 1: Enumerate all methods and code locations where issues COULD exist.
        This increases recall by ensuring we don't miss potential problem areas.
        """
        system_prompt = (
            f"You are a security expert for NEAR Protocol smart contracts. "
            f"Your task is to LIST all methods and code locations where issues related to {concept_name} COULD exist according to the documentation.\n\n"
            f"IMPORTANT: Do NOT check if the issue actually exists yet. Just enumerate ALL locations where it COULD exist.\n\n"
            f"Use the provided security documentation to identify:\n"
            f"- Methods with specific naming patterns (e.g., internal_*, *_helper, callback_*, on_*, after_*)\n"
            f"- Methods that match vulnerability patterns described in the documentation\n"
            f"- Code locations mentioned in the documentation as potential problem areas\n\n"
            f"Return a JSON array. Each item should have:\n"
            f"- function_name: string (the name of the function/method)\n"
            f"- line_range: string (e.g., '100-105' or '100' for single line)\n"
            f"- why_this_location_is_relevant: string (why this location matches patterns from the documentation)\n\n"
            f"If no relevant locations are found, return an empty array []."
        )

        user_prompt = f"""Task: List all methods and code locations where issues related to {concept_name} COULD exist.

File: {file_path}

Code:
```rust
{code}
```

Security Documentation ({concept_name}):
{concept_content}

IMPORTANT: You must return a JSON array. Even if you find no locations, return an empty array [].

Look for:
- Methods with names matching patterns from documentation (e.g., internal_*, *_helper, callback_*, on_*, after_*)
- Methods that match vulnerability patterns described in the documentation
- Any code locations mentioned in the documentation as potential problem areas

Return a JSON array of potential locations. Format:
[
  {{
    "function_name": "method_name",
    "line_range": "100-105",
    "why_this_location_is_relevant": "Matches pattern: pub fn internal_* without protection"
  }}
]

Example response:
[
  {{
    "function_name": "internal_stake_from_account",
    "line_range": "561",
    "why_this_location_is_relevant": "Method name contains 'internal' and is declared as pub fn"
  }},
  {{
    "function_name": "sign_helper",
    "line_range": "200-205",
    "why_this_location_is_relevant": "Method name contains 'helper' and is declared as pub fn"
  }}
]

Return ONLY valid JSON array, no additional text or explanation."""

        try:
            print(f"[PASS 1] Sending request to LLM for {concept_name}...")
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for consistent analysis
                top_p=0.9,
                presence_penalty=0.0,
            )

            response_text = response.choices[0].message.content.strip()
            print("[PASS 1] Received response, parsing locations...")
            print(f"[PASS 1] Raw response (first 500 chars): {response_text[:500]}")
            locations = self._parse_locations_response(response_text)
            print(f"[PASS 1] Successfully parsed {len(locations)} location(s)")
            if len(locations) == 0 and len(response_text) > 0:
                print(
                    "[PASS 1] WARNING: Response received but no locations parsed. "
                    "Check if response format is correct."
                )
            return locations

        except Exception as e:
            print(
                f"[PASS 1] ERROR: Error in Pass 1 for {concept_name}: {e}"
            )
            return []

    def _pass2_check_locations(
        self,
        code: str,
        file_path: str,
        concept_name: str,
        concept_content: str,
        locations: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Pass 2: Check each location from Pass 1 to see if security protection is present or missing.
        """
        if not locations:
            return []

        # Format locations for the prompt
        locations_text = "\n".join([
            (
                f"- {loc.get('function_name', 'unknown')} "
                f"(lines {loc.get('line_range', 'unknown')}): "
                f"{loc.get('why_this_location_is_relevant', '')}"
            )
            for loc in locations
        ])

        system_prompt = (
            "You are a security expert for NEAR Protocol smart contracts. "
            "Your task is to check each location listed below to determine "
            "if the security protection described in the documentation is "
            "PRESENT or MISSING.\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "- You MUST evaluate every function listed.\n"
            "- You MUST explicitly state \"SAFE\" or \"VULNERABLE\" for each "
            "function.\n"
            "- If no issues are found, you MUST return a list of checked "
            "locations with an explicit explanation why each is safe.\n\n"
            "CRITICAL RULES:\n"
            "- If a method has 'internal' or 'helper' in its name and is "
            "declared as 'pub fn' WITHOUT '#[private]' or 'pub(crate)' → "
            "this is ALWAYS a vulnerability. Report it.\n"
            "- If a method has callback-indicating names (callback_*, on_*, "
            "after_*) and is declared as 'pub fn' WITHOUT '#[private]' → "
            "this is ALWAYS a vulnerability. Report it.\n"
            "- If protection is PRESENT (method has '#[private]' or is "
            "'pub(crate) fn') → do NOT report it (it's safe)\n\n"
            "For each location:\n"
            "1. Find the method in the code\n"
            "2. Check its declaration (pub fn, pub(crate) fn, #[private])\n"
            "3. If it matches vulnerability patterns from documentation "
            "AND protection is MISSING → report as issue\n"
            "4. If protection is PRESENT → skip (do not report)\n\n"
            "Return a JSON array. Each item should be either:\n"
            "- An issue object (if VULNERABLE) with:\n"
            "  * line_number: integer (the line number where the issue is "
            "found)\n"
            "  * issue_description: string (description of the security "
            "problem)\n"
            "  * recommendation: string (how to fix the issue)\n"
            "- A safe_location object (if SAFE) with:\n"
            "  * function_name: string (the name of the function)\n"
            "  * line_range: string (e.g., '100-105' or '100')\n"
            "  * safety_explanation: string (explicit explanation why this "
            "location is safe)\n\n"
            "If no issues are found, return a list of checked locations "
            "with an explicit explanation why each is safe."
        )

        user_prompt = f"""Check each location below to see if security protection is PRESENT or MISSING.

File: {file_path}

Code:
```rust
{code}
```

Security Documentation ({concept_name}):
{concept_content}

Locations to check:
{locations_text}

CRITICAL REQUIREMENTS:
- You MUST evaluate every function listed.
- You MUST explicitly state "SAFE" or "VULNERABLE" for each function.
- If no issues are found, you MUST return a list of checked locations with an explicit explanation why each is safe.

IMPORTANT: For each location, you MUST:
1. Find the exact method in the code (use the function_name and line_range provided)
2. Check the method declaration:
   - Look for 'pub fn' (public function)
   - Look for '#[private]' decorator
   - Look for 'pub(crate) fn' (internal function)
3. Apply the rules from documentation:
   - If method name contains 'internal' or 'helper' AND it's 'pub fn' WITHOUT '#[private]' or 'pub(crate)' → VULNERABLE
   - If method name contains 'callback', 'on_', 'after_' AND it's 'pub fn' WITHOUT '#[private]' → VULNERABLE
4. If vulnerability found → report with line_number, issue_description, recommendation
5. If protection is present → SAFE (do not report)

Examples:
- 'pub fn sign_helper(...)' without '#[private]' or 'pub(crate)' → VULNERABLE (must report)
- 'pub fn internal_stake_from_account(...)' without '#[private]' or 'pub(crate)' → VULNERABLE (must report)
- 'pub(crate) fn sign_helper(...)' → SAFE (do not report)
- '#[private] pub fn callback_after_staking(...)' → SAFE (do not report)

Return a JSON array. Format depends on findings:

If vulnerabilities found:
[
  {{
    "line_number": 745,
    "issue_description": "Method sign_helper is declared as pub fn without #[private] or pub(crate). Methods with 'helper' in name should not be publicly accessible.",
    "recommendation": "Change to 'pub(crate) fn sign_helper(...)' for internal use, or add '#[private]' if it needs to be a callback"
  }}
]

If all locations are SAFE (no issues found):
[
  {{
    "function_name": "sign_helper",
    "line_range": "200-205",
    "safety_explanation": "Method is declared as 'pub(crate) fn', which prevents external calls. This is the correct protection for internal helper methods."
  }},
  {{
    "function_name": "callback_handler",
    "line_range": "300-310",
    "safety_explanation": "Method has '#[private]' decorator, which ensures only the contract itself can call it. This is the correct protection for callback methods."
  }}
]

Return ONLY valid JSON, no additional text."""

        # Perform self-consistency: analyze twice independently
        print(f"[PASS 2] Performing self-consistency check: analyzing {len(locations)} location(s) twice independently...")
        
        try:
            # First independent analysis
            print("[PASS 2] Analysis 1/2: Starting first independent analysis...")
            issues_1 = self._single_analysis(
                system_prompt, user_prompt, "1/2"
            )
            print(f"[PASS 2] Analysis 1/2: Found {len(issues_1)} issue(s)")
            
            # Second independent analysis
            print("[PASS 2] Analysis 2/2: Starting second independent analysis...")
            issues_2 = self._single_analysis(
                system_prompt, user_prompt, "2/2"
            )
            print(f"[PASS 2] Analysis 2/2: Found {len(issues_2)} issue(s)")
            
            # Compare results
            if self._results_match(issues_1, issues_2):
                print("[PASS 2] Self-consistency: Both analyses agree. Using result.")
                return issues_1
            else:
                print("[PASS 2] Self-consistency: Results differ. Reconciling...")
                reconciled_issues = self._reconcile_results(
                    issues_1, issues_2, code, file_path, concept_name,
                    concept_content, locations_text, system_prompt, user_prompt
                )
                print(f"[PASS 2] Self-consistency: Reconciled to {len(reconciled_issues)} issue(s)")
                return reconciled_issues

        except Exception as e:
            print(
                f"[PASS 2] ERROR: Error in Pass 2 for {concept_name}: {e}"
            )
            return []

    def _single_analysis(
        self, system_prompt: str, user_prompt: str, analysis_label: str
    ) -> List[Dict[str, Any]]:
        """
        Perform a single independent analysis.
        
        Args:
            system_prompt: System prompt for the LLM
            user_prompt: User prompt for the LLM
            analysis_label: Label for logging (e.g., "1/2", "2/2")
        
        Returns:
            List of issues found
        """
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,  # Lower temperature for consistent analysis
                top_p=0.9,
                presence_penalty=0.0,
            )

            response_text = response.choices[0].message.content.strip()
            print(f"[PASS 2] Analysis {analysis_label}: Received response, parsing...")
            print(f"[PASS 2] Analysis {analysis_label}: Raw response (first 500 chars): {response_text[:500]}")
            issues = self._parse_response(response_text)
            print(f"[PASS 2] Analysis {analysis_label}: Successfully parsed {len(issues)} issue(s)")
            if len(issues) == 0 and len(response_text) > 0:
                print(
                    f"[PASS 2] Analysis {analysis_label}: WARNING: Response received but no issues parsed. "
                    "Check if response format is correct or if LLM determined "
                    "all locations are safe."
                )
            return issues

        except Exception as e:
            print(f"[PASS 2] Analysis {analysis_label}: ERROR: {e}")
            return []

    def _results_match(
        self, issues_1: List[Dict[str, Any]], issues_2: List[Dict[str, Any]]
    ) -> bool:
        """
        Check if two analysis results match.
        
        Args:
            issues_1: First analysis results
            issues_2: Second analysis results
        
        Returns:
            True if results match, False otherwise
        """
        # Normalize results for comparison (sort by line_number)
        def normalize(issues):
            normalized = []
            for issue in issues:
                normalized.append({
                    'line_number': issue.get('line_number'),
                    'issue_description': issue.get('issue_description', '').strip(),
                    'recommendation': issue.get('recommendation', '').strip()
                })
            return sorted(normalized, key=lambda x: x['line_number'] or 0)
        
        norm_1 = normalize(issues_1)
        norm_2 = normalize(issues_2)
        
        if len(norm_1) != len(norm_2):
            print(f"[PASS 2] Self-consistency: Different number of issues ({len(norm_1)} vs {len(norm_2)})")
            return False
        
        for i, (issue_1, issue_2) in enumerate(zip(norm_1, norm_2)):
            if (issue_1['line_number'] != issue_2['line_number'] or
                    issue_1['issue_description'] !=
                    issue_2['issue_description']):
                print(
                    f"[PASS 2] Self-consistency: Issue {i} differs: "
                    f"line {issue_1['line_number']} vs "
                    f"{issue_2['line_number']}"
                )
                return False
        
        return True

    def _reconcile_results(
        self,
        issues_1: List[Dict[str, Any]],
        issues_2: List[Dict[str, Any]],
        code: str,
        file_path: str,
        concept_name: str,
        concept_content: str,
        locations_text: str,
        system_prompt: str,
        user_prompt: str
    ) -> List[Dict[str, Any]]:
        """
        Reconcile two different analysis results by asking LLM to merge them.
        
        Args:
            issues_1: First analysis results
            issues_2: Second analysis results
            code: The code being analyzed
            file_path: Path to the code file
            concept_name: Name of the security concept
            concept_content: Content of the concept documentation
            locations_text: Formatted text of locations to check
            system_prompt: Original system prompt
            user_prompt: Original user prompt
        
        Returns:
            Reconciled list of issues
        """
        # Format issues for comparison
        def format_issues(issues, label):
            if not issues:
                return f"Analysis {label}: No issues found (all locations are SAFE)."
            result = f"Analysis {label} found {len(issues)} issue(s):\n"
            for i, issue in enumerate(issues, 1):
                result += f"\n{i}. Line {issue.get('line_number', 'unknown')}:\n"
                result += f"   Description: {issue.get('issue_description', '')}\n"
                result += f"   Recommendation: {issue.get('recommendation', '')}\n"
            return result
        
        issues_1_text = format_issues(issues_1, "1/2")
        issues_2_text = format_issues(issues_2, "2/2")
        
        reconcile_system_prompt = (
            "You are a security expert for NEAR Protocol smart contracts. "
            "Two independent analyses of the same code were performed, and "
            "they produced different results. Your task is to reconcile these "
            "differences and provide the final, correct analysis.\n\n"
            "Compare the two analyses carefully:\n"
            "1. Check which issues are present in both analyses (these are "
            "likely correct)\n"
            "2. Check which issues are present in only one analysis (these "
            "need careful review)\n"
            "3. For each location, determine the correct assessment based on "
            "the security documentation\n"
            "4. Return the final merged result with only the correct issues\n\n"
            "Return a JSON array with the same format as the original analyses."
        )
        
        reconcile_user_prompt = f"""Reconcile the differences between two independent analyses.

File: {file_path}

Code:
```rust
{code}
```

Security Documentation ({concept_name}):
{concept_content}

Locations checked:
{locations_text}

{issues_1_text}

{issues_2_text}

Task: Compare these two analyses and provide the final, correct result.

Instructions:
1. Review each issue from both analyses
2. For issues present in both analyses → include them (they're likely correct)
3. For issues present in only one analysis → carefully verify against the code and documentation
4. Return the final merged JSON array with only the correct issues

Return a JSON array in the same format:
[
  {{
    "line_number": 745,
    "issue_description": "...",
    "recommendation": "..."
  }}
]

If no issues are found after reconciliation, return a list of safe_location objects:
[
  {{
    "function_name": "...",
    "line_range": "...",
    "safety_explanation": "..."
  }}
]

Return ONLY valid JSON, no additional text."""
        
        try:
            print("[PASS 2] Self-consistency: Sending reconciliation request to LLM...")
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": reconcile_system_prompt},
                    {"role": "user", "content": reconcile_user_prompt}
                ],
                temperature=0.2,  # Lower temperature for consistent analysis
                top_p=0.9,
                presence_penalty=0.0,
            )
            
            response_text = response.choices[0].message.content.strip()
            print("[PASS 2] Self-consistency: Received reconciliation response")
            print(f"[PASS 2] Self-consistency: Raw response (first 500 chars): {response_text[:500]}")
            reconciled_issues = self._parse_response(response_text)
            print(f"[PASS 2] Self-consistency: Parsed {len(reconciled_issues)} issue(s) from reconciliation")
            return reconciled_issues
            
        except Exception as e:
            print(f"[PASS 2] Self-consistency: ERROR during reconciliation: {e}")
            # Fallback: return the union of both analyses (more conservative)
            print("[PASS 2] Self-consistency: Falling back to union of both analyses")
            return self._merge_issues(issues_1, issues_2)

    def _merge_issues(
        self, issues_1: List[Dict[str, Any]], issues_2: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Merge two issue lists, removing duplicates.
        
        Args:
            issues_1: First list of issues
            issues_2: Second list of issues
        
        Returns:
            Merged list without duplicates
        """
        merged = []
        seen = set()
        
        for issue in issues_1 + issues_2:
            # Use line_number as key for deduplication
            line_num = issue.get('line_number')
            if line_num is not None:
                key = line_num
                if key not in seen:
                    seen.add(key)
                    merged.append(issue)
            else:
                # If no line_number, add anyway (shouldn't happen)
                merged.append(issue)
        
        # Sort by line_number
        merged.sort(key=lambda x: x.get('line_number', 0))
        return merged

    def _parse_locations_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse Pass 1 response to extract potential locations."""
        if not response_text or not response_text.strip():
            print("[PASS 1] WARNING: Empty response received")
            return []
        
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            print("[PASS 1] Found JSON in code block")
        else:
            # Try to find JSON array - use greedy match to get complete JSON
            # Look for array that starts with [ and ends with ]
            # Count brackets to find the matching closing bracket
            bracket_count = 0
            start_idx = response_text.find('[')
            if start_idx != -1:
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '[':
                        bracket_count += 1
                    elif response_text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_str = response_text[start_idx:i+1]
                            print("[PASS 1] Found JSON array in response")
                            break
                else:
                    # No matching closing bracket found, try parsing from start
                    json_str = response_text[start_idx:]
                    print("[PASS 1] No matching closing bracket, using from [ to end")
            else:
                # Try to parse the whole response as JSON
                json_str = response_text
                print("[PASS 1] Attempting to parse entire response as JSON")

        try:
            locations = json.loads(json_str)
            if not isinstance(locations, list):
                print(
                    f"[PASS 1] WARNING: Parsed JSON is not a list, got: "
                    f"{type(locations).__name__}"
                )
                return []

            # Validate and clean locations
            validated_locations = []
            for i, loc in enumerate(locations):
                if isinstance(loc, dict):
                    if 'function_name' in loc:
                        validated_locations.append({
                            'function_name': str(loc.get('function_name', '')),
                            'line_range': str(loc.get('line_range', '')),
                            'why_this_location_is_relevant': str(
                                loc.get('why_this_location_is_relevant', '')
                            )
                        })
                    else:
                        print(
                            f"[PASS 1] WARNING: Location {i} missing "
                            f"'function_name' field: {loc.keys()}"
                        )
                else:
                    print(
                        f"[PASS 1] WARNING: Location {i} is not a dict, "
                        f"got: {type(loc).__name__}"
                    )

            return validated_locations

        except json.JSONDecodeError as e:
            print(f"[PASS 1] ERROR: Failed to parse JSON: {e}")
            print(f"[PASS 1] JSON string length: {len(json_str)}")
            print(f"[PASS 1] JSON string (first 500 chars): {json_str[:500]}")
            if len(json_str) > 500:
                print(f"[PASS 1] JSON string (last 200 chars): {json_str[-200:]}")
            # Try to fix common JSON issues
            try:
                # Try removing trailing incomplete parts
                fixed_json = json_str.rstrip().rstrip(',').rstrip()
                if not fixed_json.endswith(']'):
                    # Try to find the last complete object
                    last_brace = fixed_json.rfind('}')
                    if last_brace != -1:
                        fixed_json = fixed_json[:last_brace+1] + ']'
                locations = json.loads(fixed_json)
                print("[PASS 1] Successfully parsed after fixing JSON")
                if isinstance(locations, list):
                    return self._validate_locations(locations)
            except Exception as e2:
                print(f"[PASS 1] Failed to fix JSON: {e2}")
            return []

    def _validate_locations(self, locations: List[Any]) -> List[Dict[str, Any]]:
        """Validate and clean locations list."""
        validated_locations = []
        for i, loc in enumerate(locations):
            if isinstance(loc, dict):
                if 'function_name' in loc:
                    validated_locations.append({
                        'function_name': str(loc.get('function_name', '')),
                        'line_range': str(loc.get('line_range', '')),
                        'why_this_location_is_relevant': str(
                            loc.get('why_this_location_is_relevant', '')
                        )
                    })
                else:
                    print(
                        f"[PASS 1] WARNING: Location {i} missing "
                        f"'function_name' field: {list(loc.keys())}"
                    )
            else:
                print(
                    f"[PASS 1] WARNING: Location {i} is not a dict, "
                    f"got: {type(loc).__name__}"
                )
        return validated_locations

    def _parse_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse LLM response to extract issues."""
        if not response_text or not response_text.strip():
            print("[PASS 2] WARNING: Empty response received")
            return []
        
        # Try to find JSON in code blocks first
        json_match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
            print("[PASS 2] Found JSON in code block")
        else:
            # Try to find JSON array - use bracket counting to get complete JSON
            bracket_count = 0
            start_idx = response_text.find('[')
            if start_idx != -1:
                for i in range(start_idx, len(response_text)):
                    if response_text[i] == '[':
                        bracket_count += 1
                    elif response_text[i] == ']':
                        bracket_count -= 1
                        if bracket_count == 0:
                            json_str = response_text[start_idx:i+1]
                            print("[PASS 2] Found JSON array in response")
                            break
                else:
                    # No matching closing bracket found
                    json_str = response_text[start_idx:]
                    print("[PASS 2] No matching closing bracket, using from [ to end")
            else:
                # Try to parse the whole response as JSON
                json_str = response_text
                print("[PASS 2] Attempting to parse entire response as JSON")

        try:
            issues = json.loads(json_str)
            if not isinstance(issues, list):
                print(
                    f"[PASS 2] WARNING: Parsed JSON is not a list, got: "
                    f"{type(issues).__name__}"
                )
                return []

            # Validate and clean issues
            # Filter out safe_location objects and keep only issue objects
            validated_issues = []
            for i, item in enumerate(issues):
                if isinstance(item, dict):
                    # Check if it's an issue object (has vulnerability info)
                    issue_keys = ['line_number', 'issue_description', 'recommendation']
                    # Check if it's a safe_location object (has safety info)
                    safe_keys = ['function_name', 'line_range', 'safety_explanation']
                    
                    if all(key in item for key in issue_keys):
                        # This is an issue object
                        try:
                            validated_issues.append({
                                'line_number': int(item['line_number']),
                                'issue_description': str(item['issue_description']),
                                'recommendation': str(item['recommendation'])
                            })
                        except (ValueError, KeyError) as e:
                            print(
                                f"[PASS 2] WARNING: Issue {i} has invalid data: {e}"
                            )
                    elif all(key in item for key in safe_keys):
                        # This is a safe_location object - skip it (not an issue)
                        print(
                            f"[PASS 2] Found safe_location for {item.get('function_name', 'unknown')}: "
                            f"{item.get('safety_explanation', '')[:60]}..."
                        )
                    else:
                        # Unknown format
                        missing_issue = [k for k in issue_keys if k not in item]
                        missing_safe = [k for k in safe_keys if k not in item]
                        print(
                            f"[PASS 2] WARNING: Item {i} doesn't match expected format. "
                            f"Missing issue keys: {missing_issue}, "
                            f"missing safe keys: {missing_safe}, "
                            f"got: {list(item.keys())}"
                        )
                else:
                    print(
                        f"[PASS 2] WARNING: Item {i} is not a dict, "
                        f"got: {type(item).__name__}"
                    )

            return validated_issues

        except json.JSONDecodeError as e:
            print(f"[PASS 2] ERROR: Failed to parse JSON: {e}")
            print(f"[PASS 2] JSON string length: {len(json_str)}")
            print(f"[PASS 2] JSON string (first 500 chars): {json_str[:500]}")
            if len(json_str) > 500:
                print(f"[PASS 2] JSON string (last 200 chars): {json_str[-200:]}")
            # Try to fix common JSON issues
            try:
                # Try removing trailing incomplete parts
                fixed_json = json_str.rstrip().rstrip(',').rstrip()
                if not fixed_json.endswith(']'):
                    # Try to find the last complete object
                    last_brace = fixed_json.rfind('}')
                    if last_brace != -1:
                        fixed_json = fixed_json[:last_brace+1] + ']'
                issues = json.loads(fixed_json)
                print("[PASS 2] Successfully parsed after fixing JSON")
                if isinstance(issues, list):
                    return self._validate_issues(issues)
            except Exception as e2:
                print(f"[PASS 2] Failed to fix JSON: {e2}")
            # If JSON parsing fails, try to extract issues manually
            return self._extract_issues_from_text(response_text)

    def _validate_issues(self, issues: List[Any]) -> List[Dict[str, Any]]:
        """Validate and clean issues list."""
        validated_issues = []
        for i, issue in enumerate(issues):
            if isinstance(issue, dict):
                required_keys = ['line_number', 'issue_description', 'recommendation']
                if all(key in issue for key in required_keys):
                    try:
                        validated_issues.append({
                            'line_number': int(issue['line_number']),
                            'issue_description': str(issue['issue_description']),
                            'recommendation': str(issue['recommendation'])
                        })
                    except (ValueError, KeyError) as e:
                        print(
                            f"[PASS 2] WARNING: Issue {i} has invalid data: {e}"
                        )
                else:
                    missing = [k for k in required_keys if k not in issue]
                    print(
                        f"[PASS 2] WARNING: Issue {i} missing required keys: "
                        f"{missing}"
                    )
            else:
                print(
                    f"[PASS 2] WARNING: Issue {i} is not a dict, "
                    f"got: {type(issue).__name__}"
                )
        return validated_issues

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

    def audit_file(
        self, file_path: str, concept_name: str = None
    ) -> tuple[List[Dict[str, Any]], List[str]]:
        """
        Audit a code file for security issues by checking against concepts.

        Args:
            file_path: Path to the code file to audit
            concept_name: Optional name of specific concept to check
                         (without .md extension).
                         If None, checks against all concepts.

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

        # Get concept files (all or specific one)
        concepts = self.get_all_concept_files(concept_name)
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
