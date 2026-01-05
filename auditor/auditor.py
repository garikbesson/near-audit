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

from dotenv import load_dotenv
import openai

# Load environment variables from .env file
load_dotenv()


class CodeAuditor:
    """Audits NEAR smart contract code for security issues."""

    def __init__(self):
        """Initialize the code auditor with LLM client."""
        api_key = os.getenv("FIREWORKS_API_KEY")
        if not api_key:
            raise ValueError(
                "FIREWORKS_API_KEY environment variable is not set. "
                "Please set it before running the auditor."
            )
        self.client = openai.OpenAI(
            base_url="https://api.fireworks.ai/inference/v1",
            api_key=api_key,
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
            f"CRITICAL: Only list methods that are in impl Contract {{}} blocks that ARE decorated with #[near] or #[near_bindgen]. "
            f"Methods in impl Contract {{}} blocks WITHOUT #[near] or #[near_bindgen] decorators are NOT part of the contract's public interface and should NOT be listed.\n\n"
            f"Use the provided security documentation to identify:\n"
            f"- Methods with specific naming patterns (e.g., internal_*, *_helper, callback_*, on_*, after_*)\n"
            f"- Methods that match vulnerability patterns described in the documentation\n"
            f"- Code locations mentioned in the documentation as potential problem areas\n"
            f"- BUT ONLY if they are in decorated impl blocks (#[near] or #[near_bindgen])\n\n"
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

CRITICAL RULE: Only list methods that are in impl Contract {{}} blocks that ARE decorated with #[near] or #[near_bindgen].
- If an impl Contract {{}} block does NOT have #[near] or #[near_bindgen] decorator, methods inside it are NOT part of the contract's public interface
- DO NOT list methods from undecorated impl Contract {{}} blocks, even if they match naming patterns

Look for:
- Methods with names matching patterns from documentation (e.g., internal_*, *_helper, callback_*, on_*, after_*)
- Methods that match vulnerability patterns described in the documentation
- Any code locations mentioned in the documentation as potential problem areas
- BUT ONLY if they are in impl Contract {{}} blocks decorated with #[near] or #[near_bindgen]

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
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Check if response was truncated
            if finish_reason == "length":
                print("[PASS 1] WARNING: Response was truncated. Results may be incomplete.")

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
            "- FIRST: Check if the method is in an impl Contract {{}} block "
            "that is decorated with #[near] or #[near_bindgen]. If NOT "
            "decorated, the method is NOT part of the contract interface "
            "and is SAFE (do NOT report).\n"
            "- If a method has 'internal' or 'helper' in its name and is "
            "declared as 'pub fn' WITHOUT '#[private]' or 'pub(crate)' → "
            "this is ALWAYS a vulnerability. Report it.\n"
            "- If a method has callback-indicating names (callback_*, on_*, "
            "after_*) and is declared as 'pub fn' WITHOUT '#[private]' → "
            "this is ALWAYS a vulnerability. Report it.\n"
            "- If protection is PRESENT (method has '#[private]' or is "
            "'pub(crate) fn') → do NOT report it (it's safe)\n"
            "- If method is in impl Contract {{}} block WITHOUT #[near] or "
            "#[near_bindgen] decorator → do NOT report it (it's safe, not "
            "part of contract interface)\n\n"
            "For each location:\n"
            "1. Find the method in the code\n"
            "2. Check if it's in an impl Contract {{}} block decorated with "
            "#[near] or #[near_bindgen]. If NOT decorated → SAFE (do not "
            "report)\n"
            "3. Check its declaration (pub fn, pub(crate) fn, #[private])\n"
            "4. If it matches vulnerability patterns from documentation "
            "AND protection is MISSING → report as issue\n"
            "5. If protection is PRESENT → skip (do not report)\n\n"
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
2. FIRST: Check if the method is in an impl Contract {{}} block decorated with #[near] or #[near_bindgen]:
   - If the impl block is NOT decorated → SAFE (do not report, not part of contract interface)
   - If the impl block IS decorated → continue to step 3
3. Check the method declaration:
   - Look for 'pub fn' (public function)
   - Look for '#[private]' decorator
   - Look for 'pub(crate) fn' (internal function)
4. Apply the rules from documentation:
   - If method name contains 'internal' or 'helper' AND it's 'pub fn' WITHOUT '#[private]' or 'pub(crate)' → VULNERABLE
   - If method name contains 'callback', 'on_', 'after_' AND it's 'pub fn' WITHOUT '#[private]' → VULNERABLE
5. If vulnerability found → report with line_number, issue_description, recommendation
6. If protection is present OR method is in undecorated impl block → SAFE (do not report)

Examples:
- Method in impl Contract {{}} WITHOUT #[near] decorator → SAFE (do not report, not part of contract interface)
- 'pub fn sign_helper(...)' in #[near] impl block without '#[private]' or 'pub(crate)' → VULNERABLE (must report)
- 'pub fn internal_stake_from_account(...)' in #[near] impl block without '#[private]' or 'pub(crate)' → VULNERABLE (must report)
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
  }},
  {{
    "function_name": "internal_helper",
    "line_range": "100-105",
    "safety_explanation": "Method is in impl Contract {{}} block without #[near] or #[near_bindgen] decorator, so it is NOT part of the contract's public interface and cannot be called externally."
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
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Check if response was truncated
            if finish_reason == "length":
                print(f"[PASS 2] Analysis {analysis_label}: WARNING: Response was truncated. Results may be incomplete.")

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
                max_tokens=4096,  # Increased for reconciliation
            )

            response_text = response.choices[0].message.content.strip()

            # Check if response was truncated
            if finish_reason == "length":
                print("[PASS 2] Self-consistency: WARNING: Response was truncated. Results may be incomplete.")

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

    def index_project(self, project_dir: str) -> Dict[str, Any]:
        """
        Build a structured project index by analyzing all Rust files in a directory.

        Args:
            project_dir: Path to the project directory containing Rust files

        Returns:
            Dictionary containing the project index with file analysis
        """
        # Find all .rs files recursively
        rust_files = []
        for root, dirs, files in os.walk(project_dir):
            # Skip target directory (Rust build artifacts)
            if 'target' in root:
                continue
            for file in files:
                if file.endswith('.rs'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_dir)
                    rust_files.append((rel_path, full_path))

        if not rust_files:
            raise ValueError(f"No Rust files found in {project_dir}")

        # Read all files
        files_content = {}
        for rel_path, full_path in rust_files:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    files_content[rel_path] = f.read()
            except Exception as e:
                print(f"Warning: Could not read {full_path}: {e}")

        # Build user prompt
        files_section = ""
        for rel_path, content in files_content.items():
            files_section += f"---\nFILE: {rel_path}\n\nCODE:\n\n{content}\n\n"

        user_prompt = f"""PROJECT_ROOT: {os.path.abspath(project_dir)}

FILES:

{files_section}TASK:

For each Rust file, identify:

- public contract methods (#[near_bindgen] pub fn)

- private helper methods

- callback methods (Promise::then, ext_* callbacks)

- whether the file mutates contract state

- whether the file performs cross-contract calls

Return ONLY JSON in the following format:

{{
  "files": {{
    "file_name.rs": {{
      "public_methods": [],
      "private_methods": [],
      "callbacks": [],
      "mutates_state": true|false,
      "cross_contract_calls": true|false
    }}
  }}
}}
"""

        system_prompt = """SYSTEM:

You are analyzing a NEAR Protocol smart contract project written in Rust.

You are NOT allowed to scan the filesystem yourself.

You can only use the files explicitly provided below.

Your task is to build a structured project index.

Do NOT analyze security yet.
"""

        # Send request to LLM
        print(f"[INDEX] Analyzing {len(rust_files)} Rust file(s)...")
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.9,
                presence_penalty=0.0,
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Log full LLM response before parsing
            print(f"[INDEX] Full LLM response ({len(response_text)} characters):")
            print("=" * 80)
            print(response_text)
            print("=" * 80)

            # Check if response was truncated
            if finish_reason == "length":
                print("[INDEX] WARNING: Response was truncated. Attempting to parse partial JSON...")

            # Try to extract JSON from response
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            try:
                project_index = json.loads(response_text)
                print("[INDEX] Successfully parsed project index")
                return project_index
            except json.JSONDecodeError as e:
                # Try to fix incomplete JSON by closing brackets
                if "Unterminated string" in str(e) or "Expecting" in str(e):
                    print("[INDEX] WARNING: JSON appears incomplete. Attempting to fix...")
                    # Try to close the JSON structure
                    try:
                        # Count open/close braces
                        open_braces = response_text.count('{')
                        close_braces = response_text.count('}')
                        open_brackets = response_text.count('[')
                        close_brackets = response_text.count(']')

                        # Try to close incomplete JSON
                        fixed_text = response_text
                        if open_braces > close_braces:
                            fixed_text += '\n' + '}' * (open_braces - close_braces)
                        if open_brackets > close_brackets:
                            fixed_text += '\n' + ']' * (open_brackets - close_brackets)

                        project_index = json.loads(fixed_text)
                        print("[INDEX] Successfully parsed project index (after fixing incomplete JSON)")
                        return project_index
                    except:
                        pass

                print(f"[INDEX] ERROR: Failed to parse JSON response: {e}")
                print(f"[INDEX] Response length: {len(response_text)} characters")
                print(f"[INDEX] Response text (first 1000 chars): {response_text[:1000]}")
                if len(response_text) > 1000:
                    print(f"[INDEX] Response text (last 500 chars): {response_text[-500:]}")
                raise ValueError(f"LLM response is not valid JSON: {e}")

        except Exception as e:
            print(f"[INDEX] ERROR: Failed to get response from LLM: {e}")
            raise

    def build_method_graph(
        self, project_dir: str, project_index: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Build a graph of method relationships across files in the project.

        Args:
            project_dir: Path to the project directory containing Rust files
            project_index: Optional pre-built project index. If None, will build it.

        Returns:
            List of relationship dictionaries
        """
        # Build index if not provided
        if project_index is None:
            print("[GRAPH] Building project index first...")
            project_index = self.index_project(project_dir)

        # Find all .rs files recursively
        rust_files = []
        for root, dirs, files in os.walk(project_dir):
            # Skip target directory (Rust build artifacts)
            if 'target' in root:
                continue
            for file in files:
                if file.endswith('.rs'):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, project_dir)
                    rust_files.append((rel_path, full_path))

        if not rust_files:
            raise ValueError(f"No Rust files found in {project_dir}")

        # Read all files
        files_content = {}
        for rel_path, full_path in rust_files:
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    files_content[rel_path] = f.read()
            except Exception as e:
                print(f"Warning: Could not read {full_path}: {e}")

        # Build user prompt
        files_section = ""
        for rel_path, content in files_content.items():
            files_section += f"---\nFILE: {rel_path}\n\nCODE:\n\n{content}\n\n"

        # Convert project_index to JSON string
        index_json = json.dumps(project_index, indent=2)

        user_prompt = f"""PROJECT_INDEX:

{index_json}

FILES:

{files_section}TASK:

Identify relationships between methods across files.

Return a JSON array:

[
  {{
    "from_method": "withdraw",
    "from_file": "src/lib.rs",
    "to_method": "on_withdraw_complete",
    "to_file": "src/callbacks.rs",
    "type": "promise_callback | direct_call | ext_contract_call"
  }}
]

CRITICAL RULES:
1. Only include relationships where there is an EXPLICIT CALL in the source code.
2. Look for actual method invocations like:
   - self.method_name(...)
   - Contract::method_name(...)
   - Promise::then(..., "method_name", ...)
   - ext_contract.method_name(...)
3. Do NOT include relationships just because methods exist in the same file or project.
4. Do NOT assume relationships based on method names or project index alone.
5. If a method exists but is never called, do NOT include it in relationships.
6. If unsure whether a relationship exists, OMIT it.
7. Only include relationships you can see EXPLICITLY in the code provided above.

Examples of what to INCLUDE:
- Method A calls self.method_b() → include relationship A → B
- Method A uses Promise::then(..., "callback_method", ...) → include relationship A → callback_method (type: promise_callback)
- Method A calls ext_contract.method_b() → include relationship A → B (type: ext_contract_call)

Examples of what to OMIT:
- Method A and method B exist in same file but A never calls B → OMIT
- Method A and method B have similar names but no actual call → OMIT
- You think methods might be related but see no explicit call → OMIT
"""

        system_prompt = """SYSTEM:

You are analyzing method relationships in a NEAR smart contract project.

You MUST only identify relationships where there is an EXPLICIT METHOD CALL in the source code.

You MUST NOT guess or assume relationships based on:
- Method names
- File structure
- Project index
- Similar functionality

You MUST verify each relationship by finding the actual call in the code.

If you cannot find an explicit call, DO NOT include the relationship.
"""

        # Send request to LLM
        print(f"[GRAPH] Analyzing method relationships in {len(rust_files)} file(s)...")
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.9,
                presence_penalty=0.0,
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Log full LLM response before parsing
            print(f"[GRAPH] Full LLM response ({len(response_text)} characters):")
            print("=" * 80)
            print(response_text)
            print("=" * 80)

            # Check if response was truncated
            if finish_reason == "length":
                print("[GRAPH] WARNING: Response was truncated. Attempting to parse partial JSON...")

            # Try to extract JSON from response
            # Remove markdown code blocks if present
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            # Parse JSON
            try:
                method_graph = json.loads(response_text)
                if not isinstance(method_graph, list):
                    # If LLM returned object with array inside, extract it
                    if isinstance(method_graph, dict) and "relationships" in method_graph:
                        method_graph = method_graph["relationships"]
                    else:
                        raise ValueError("Response is not a JSON array")
                print(f"[GRAPH] Successfully parsed {len(method_graph)} relationship(s)")
                return method_graph
            except json.JSONDecodeError as e:
                # Try to fix incomplete JSON
                if "Unterminated string" in str(e) or "Expecting" in str(e):
                    print("[GRAPH] WARNING: JSON appears incomplete. Attempting to fix...")
                    try:
                        open_brackets = response_text.count('[')
                        close_brackets = response_text.count(']')
                        if open_brackets > close_brackets:
                            fixed_text = response_text + '\n' + ']' * (open_brackets - close_brackets)
                            method_graph = json.loads(fixed_text)
                            if isinstance(method_graph, list):
                                print(f"[GRAPH] Successfully parsed {len(method_graph)} relationship(s) (after fixing)")
                                return method_graph
                    except:
                        pass

                print(f"[GRAPH] ERROR: Failed to parse JSON response: {e}")
                print(f"[GRAPH] Response length: {len(response_text)} characters")
                print(f"[GRAPH] Response text (first 500 chars): {response_text[:500]}")
                raise ValueError(f"LLM response is not valid JSON: {e}")

        except Exception as e:
            print(f"[GRAPH] ERROR: Failed to get response from LLM: {e}")
            raise

    def find_relevant_methods(
        self,
        concept_name: str,
        project_index: Dict[str, Any],
        method_graph: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Find methods and files relevant for analyzing a specific security concept.

        Args:
            concept_name: Name of the security concept (without extension)
            project_index: Project index dictionary
            method_graph: Method relationship graph

        Returns:
            Dictionary with relevant methods and their relationships
        """
        # Read concept file
        concepts = self.get_all_concept_files(concept_name)
        if not concepts:
            raise FileNotFoundError(f"Concept file not found: {concept_name}")

        concept_name_found, concept_path = concepts[0]
        concept_content = self.read_concept_file(concept_path)

        # Convert project_index and method_graph to JSON strings
        index_json = json.dumps(project_index, indent=2)
        graph_json = json.dumps(method_graph, indent=2)

        user_prompt = f"""SECURITY_CONCEPT: {concept_name_found}

CONCEPT_DOCUMENTATION:

{concept_content}

PROJECT_INDEX:

{index_json}

CALL_GRAPH:

{graph_json}

TASK:

Analyze the PROJECT_INDEX and CALL_GRAPH above to identify which methods and files are relevant for analyzing security issues related to {concept_name_found}.

INSTRUCTIONS:

1. Read the CONCEPT_DOCUMENTATION carefully to understand:
   - What types of security vulnerabilities this concept addresses
   - What patterns or code structures indicate potential vulnerabilities
   - What methods or code sections are typically involved in these vulnerabilities

2. Analyze the PROJECT_INDEX to find methods that:
   - Match the vulnerability patterns described in the concept documentation
   - Perform operations related to the security concerns mentioned in the documentation
   - Have characteristics that make them relevant for this type of security analysis

3. Use the CALL_GRAPH to identify:
   - Methods that call other methods relevant to this security concept
   - Callback relationships (promise_callback) that may be relevant
   - Cross-contract calls (ext_contract_call) that may introduce vulnerabilities
   - Methods that must be analyzed together due to their relationships

4. For each relevant method, determine:
   - The method name (from PROJECT_INDEX)
   - The file where it's located (from PROJECT_INDEX)
   - A brief reason why it's relevant based on the concept documentation
   - Any related methods from CALL_GRAPH that must be analyzed together (use must_include field)

5. Be comprehensive but accurate:
   - Include all methods that match the patterns from the concept documentation
   - Include methods that are called by or call relevant methods (from CALL_GRAPH)
   - Do NOT include methods that are clearly unrelated to this security concept

CRITICAL: You MUST return ONLY valid JSON. Do NOT include any explanatory text before or after the JSON.

Return ONLY this JSON structure (no other text):

{{
  "relevant_methods": [
    {{
      "method": "method_name",
      "file": "src/lib.rs",
      "reason": "Brief explanation why this method is relevant based on the concept documentation",
      "must_include": [
        {{ "method": "related_method", "file": "src/callbacks.rs" }}
      ]
    }}
  ]
}}

If no relevant methods are found, return:
{{
  "relevant_methods": []
}}

IMPORTANT: Return ONLY the JSON object. Do NOT add any text before or after it.
"""

        system_prompt = """SYSTEM:

You are selecting relevant code for a focused security analysis.

Your task is to identify methods that are relevant for analyzing a specific security concept.

CRITICAL REQUIREMENTS:
1. You MUST return ONLY valid JSON - no explanatory text, no markdown, no code blocks
2. Your response must start with { and end with }
3. Do NOT include any text before or after the JSON
4. Do NOT wrap JSON in markdown code blocks
5. Carefully read the CONCEPT_DOCUMENTATION to understand what patterns to look for
6. Analyze the PROJECT_INDEX to find methods matching those patterns
7. Use the CALL_GRAPH to identify related methods that should be analyzed together
8. Be thorough: include all methods that match the vulnerability patterns from the documentation
9. If you cannot find relevant methods, return {"relevant_methods": []}

Be conservative: include more rather than less, but only methods that actually match the patterns described in the concept documentation.
"""

        # Send request to LLM
        print(f"[RELEVANCE] Finding relevant methods for concept: {concept_name_found}...")
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.9,
                presence_penalty=0.0,
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Log full LLM response before parsing
            print(f"[RELEVANCE] Full LLM response ({len(response_text)} characters):")
            print("=" * 80)
            print(response_text)
            print("=" * 80)

            # Check if response was truncated
            if finish_reason == "length":
                print("[RELEVANCE] WARNING: Response was truncated. Attempting to parse partial JSON...")

            # Try to extract JSON from response using more robust method
            json_str = None

            # First, try to find JSON in code blocks
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
                print("[RELEVANCE] Found JSON in code block")
            else:
                # Try to find JSON object - use brace counting to get complete JSON
                brace_count = 0
                start_idx = response_text.find('{')
                if start_idx != -1:
                    for i in range(start_idx, len(response_text)):
                        if response_text[i] == '{':
                            brace_count += 1
                        elif response_text[i] == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = response_text[start_idx:i+1]
                                print("[RELEVANCE] Found JSON object in response")
                                break
                    else:
                        # No matching closing brace found - try to fix
                        json_str = response_text[start_idx:]
                        print("[RELEVANCE] No matching closing brace, attempting to fix...")
                else:
                    # Try to parse the whole response as JSON
                    json_str = response_text
                    print("[RELEVANCE] Attempting to parse entire response as JSON")

            # Parse JSON
            try:
                relevant_methods = json.loads(json_str)
                if not isinstance(relevant_methods, dict):
                    raise ValueError("Response is not a JSON object")
                print("[RELEVANCE] Successfully found relevant methods")
                return relevant_methods
            except json.JSONDecodeError as e:
                # Try to fix incomplete JSON
                if "Unterminated string" in str(e) or "Expecting" in str(e):
                    print("[RELEVANCE] WARNING: JSON appears incomplete. Attempting to fix...")
                    try:
                        open_braces = json_str.count('{')
                        close_braces = json_str.count('}')
                        if open_braces > close_braces:
                            fixed_text = json_str.rstrip().rstrip(',').rstrip()
                            fixed_text += '\n' + '}' * (open_braces - close_braces)
                            relevant_methods = json.loads(fixed_text)
                            if isinstance(relevant_methods, dict):
                                print("[RELEVANCE] Successfully found relevant methods (after fixing)")
                                return relevant_methods
                    except Exception as e2:
                        print(f"[RELEVANCE] Failed to fix JSON: {e2}")

                print(f"[RELEVANCE] ERROR: Failed to parse JSON response: {e}")
                print(f"[RELEVANCE] JSON string length: {len(json_str) if json_str else 0} characters")
                print(f"[RELEVANCE] JSON string (first 1000 chars): {json_str[:1000] if json_str else 'None'}")
                if json_str and len(json_str) > 1000:
                    print(f"[RELEVANCE] JSON string (last 500 chars): {json_str[-500:]}")
                print(f"[RELEVANCE] Full response text (first 500 chars): {response_text[:500]}")
                raise ValueError(f"LLM response is not valid JSON: {e}")

        except Exception as e:
            print(f"[RELEVANCE] ERROR: Failed to get response from LLM: {e}")
            raise

    def audit_relevant_methods(
        self,
        concept_name: str,
        relevant_methods: Dict[str, Any],
        project_dir: str
    ) -> List[Dict[str, Any]]:
        """
        Audit relevant methods for security issues based on a specific concept.

        Args:
            concept_name: Name of the security concept (without extension)
            relevant_methods: Dictionary with relevant methods from find_relevant_methods
            project_dir: Path to the project directory

        Returns:
            List of security issues found
        """
        # Read concept file
        concepts = self.get_all_concept_files(concept_name)
        if not concepts:
            raise FileNotFoundError(f"Concept file not found: {concept_name}")

        concept_name_found, concept_path = concepts[0]
        concept_content = self.read_concept_file(concept_path)

        # Extract unique files from relevant_methods
        files_to_read = set()
        if "relevant_methods" in relevant_methods:
            for method_info in relevant_methods["relevant_methods"]:
                if "file" in method_info:
                    files_to_read.add(method_info["file"])
                # Also include must_include files
                if "must_include" in method_info:
                    for must_include in method_info["must_include"]:
                        if "file" in must_include:
                            files_to_read.add(must_include["file"])

        # Read only relevant files
        files_content = {}
        for rel_path in files_to_read:
            # Normalize the path - remove leading slashes and normalize separators
            rel_path_normalized = rel_path.lstrip('/').replace('\\', '/')

            # Check if project_dir ends with a directory that's also in rel_path
            # For example: project_dir = ".../metapool/src", rel_path = "src/lib.rs"
            # We should use "lib.rs" instead
            project_dir_basename = os.path.basename(os.path.normpath(project_dir))
            if rel_path_normalized.startswith(project_dir_basename + '/'):
                rel_path_normalized = rel_path_normalized[len(project_dir_basename) + 1:]

            # Also try without the first directory component if it matches project_dir basename
            # For example: if rel_path = "src/lib.rs" and project_dir ends with "src", try "lib.rs"
            path_parts = rel_path_normalized.split('/')
            if len(path_parts) > 1 and path_parts[0] == project_dir_basename:
                rel_path_without_prefix = '/'.join(path_parts[1:])
            else:
                rel_path_without_prefix = None

            # Try multiple path combinations
            possible_paths = []

            # Try with normalized path
            possible_paths.append(os.path.join(project_dir, rel_path_normalized))

            # Try without prefix if applicable
            if rel_path_without_prefix:
                possible_paths.append(os.path.join(project_dir, rel_path_without_prefix))

            # Try original path
            possible_paths.append(os.path.join(project_dir, rel_path))

            # Also try if rel_path is already absolute
            if os.path.isabs(rel_path):
                possible_paths.insert(0, rel_path)

            # Try to find file by checking each possible path
            found_path = None
            for path in possible_paths:
                if os.path.exists(path) and os.path.isfile(path):
                    found_path = path
                    break

            # If not found, search recursively in project_dir by filename
            if not found_path:
                filename = os.path.basename(rel_path_normalized)
                for root, dirs, files in os.walk(project_dir):
                    # Skip target directory
                    if 'target' in root:
                        continue
                    if filename in files:
                        found_path = os.path.join(root, filename)
                        break

            if found_path:
                try:
                    with open(found_path, 'r', encoding='utf-8') as f:
                        files_content[rel_path] = f.read()
                except Exception as e:
                    print(f"Warning: Could not read {found_path}: {e}")
            else:
                print(f"Warning: File not found: {rel_path}")
                print(f"  Searched in: {project_dir}")
                print(f"  Tried paths: {', '.join(possible_paths[:3])}")

        # Build files section
        files_section = ""
        for rel_path, content in files_content.items():
            files_section += f"---\nFILE: {rel_path}\n\nCODE:\n\n{content}\n\n"

        # Convert relevant_methods to JSON string
        relevant_json = json.dumps(relevant_methods, indent=2)

        user_prompt = f"""SECURITY_CONCEPT: {concept_name_found}

RELEVANT_METHODS:

{relevant_json}

SECURITY_DOCUMENTATION:

{concept_content}

FILES:

{files_section}TASK:

Analyze the combined behavior of these methods.

For each issue found, return:

{{
  "method": "...",
  "file": "...",
  "line_number": ...,
  "issue_description": "...",
  "recommendation": "..."
}}

If no issues are found:
- Explicitly explain why the combined behavior is safe.
"""

        system_prompt = """SYSTEM:

You are a NEAR Protocol smart contract security auditor.

You MUST analyze interactions across multiple files.

You MUST consider async boundaries and callbacks.

Do NOT analyze unrelated code.
"""

        # Send request to LLM
        print(f"[AUDIT] Auditing relevant methods for concept: {concept_name_found}...")
        try:
            response = self.client.chat.completions.create(
                model="accounts/fireworks/models/llama4-maverick-instruct-basic",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                top_p=0.9,
                presence_penalty=0.0,
                max_tokens=5000,  # Maximum allowed with streaming
                stream=True,
            )

            # Collect streaming response
            response_text = ""
            finish_reason = None
            for chunk in response:
                if chunk.choices[0].delta.content:
                    response_text += chunk.choices[0].delta.content
                if chunk.choices[0].finish_reason:
                    finish_reason = chunk.choices[0].finish_reason

            response_text = response_text.strip()

            # Log full LLM response before parsing
            print(f"[AUDIT] Full LLM response ({len(response_text)} characters):")
            print("=" * 80)
            print(response_text)
            print("=" * 80)

            # Check if response was truncated
            if finish_reason == "length":
                print("[AUDIT] WARNING: Response was truncated. Attempting to parse partial JSON...")

            # Try to extract JSON from response using more robust method
            json_str = None
            
            # First, try to find JSON in markdown code blocks
            # Look for ```json ... ``` or ``` ... ``` containing JSON
            code_block_match = re.search(r'```(?:json)?\s*(.*?)\s*```', response_text, re.DOTALL)
            if code_block_match:
                code_block_content = code_block_match.group(1).strip()
                # Try to extract JSON from code block (could be array or object)
                if code_block_content.startswith('['):
                    # It's a JSON array - use bracket counting
                    bracket_count = 0
                    for i, char in enumerate(code_block_content):
                        if char == '[':
                            bracket_count += 1
                        elif char == ']':
                            bracket_count -= 1
                            if bracket_count == 0:
                                json_str = code_block_content[:i+1]
                                print("[AUDIT] Found JSON array in code block")
                                break
                elif code_block_content.startswith('{'):
                    # It's a JSON object - use brace counting
                    brace_count = 0
                    for i, char in enumerate(code_block_content):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                json_str = code_block_content[:i+1]
                                print("[AUDIT] Found JSON object in code block")
                                break
            
            # If not found in code blocks, try to find JSON directly in response
            if not json_str:
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
                                    print("[AUDIT] Found JSON array in response")
                                    break
                        else:
                            # No matching closing bracket found - try to fix
                            json_str = response_text[start_idx:]
                            print("[AUDIT] No matching closing bracket, attempting to fix...")
                    else:
                        # Try to find JSON object instead
                        brace_count = 0
                        start_idx = response_text.find('{')
                        if start_idx != -1:
                            for i in range(start_idx, len(response_text)):
                                if response_text[i] == '{':
                                    brace_count += 1
                                elif response_text[i] == '}':
                                    brace_count -= 1
                                    if brace_count == 0:
                                        json_str = response_text[start_idx:i+1]
                                        print("[AUDIT] Found JSON object in response")
                                        break
                            else:
                                json_str = response_text[start_idx:]
                                print("[AUDIT] No matching closing brace, attempting to fix...")
                        else:
                            # Try to parse the whole response as JSON
                            json_str = response_text
                            print("[AUDIT] Attempting to parse entire response as JSON")

            # Parse JSON
            try:
                # Try to parse as array of issues
                issues = json.loads(json_str)
                if isinstance(issues, list):
                    # Filter out empty lists or non-issue items
                    valid_issues = []
                    for item in issues:
                        if isinstance(item, dict) and any(key in item for key in ["method", "line_number", "issue_description"]):
                            valid_issues.append(item)
                    if valid_issues:
                        print(f"[AUDIT] Successfully found {len(valid_issues)} issue(s)")
                        return valid_issues
                    else:
                        print("[AUDIT] No security issues found - code is safe")
                        return []
                elif isinstance(issues, dict):
                    # If it's a dict, check for common keys
                    if "issues" in issues:
                        issues_list = issues["issues"]
                        if isinstance(issues_list, list) and len(issues_list) > 0:
                            print(f"[AUDIT] Successfully found {len(issues_list)} issue(s)")
                            return issues_list
                        else:
                            print("[AUDIT] No security issues found - code is safe")
                            return []
                    # Check for "no_issues" or "safe" indicators
                    elif "no_issues" in issues:
                        print("[AUDIT] No security issues found - code is safe")
                        return []
                    elif "message" in issues and isinstance(issues["message"], str):
                        message_lower = issues["message"].lower()
                        if "no issues" in message_lower or "safe" in message_lower:
                            print("[AUDIT] No security issues found - code is safe")
                            return []
                    # Check if it's a single issue object
                    elif any(key in issues for key in ["method", "line_number", "issue_description"]):
                        print("[AUDIT] Successfully found 1 issue")
                        return [issues]
                    else:
                        # Unknown dict format, treat as no issues
                        print("[AUDIT] No security issues found - code is safe")
                        return []
                else:
                    raise ValueError("Response is not a JSON array or object")
            except json.JSONDecodeError as e:
                # Try to fix incomplete JSON by closing brackets/braces
                if "Unterminated string" in str(e) or "Expecting" in str(e):
                    print("[AUDIT] WARNING: JSON appears incomplete. Attempting to fix...")
                    try:
                        # Count open/close brackets and braces
                        open_braces = json_str.count('{')
                        close_braces = json_str.count('}')
                        open_brackets = json_str.count('[')
                        close_brackets = json_str.count(']')

                        # Try to close incomplete JSON
                        fixed_text = json_str.rstrip().rstrip(',').rstrip()
                        if open_braces > close_braces:
                            fixed_text += '\n' + '}' * (open_braces - close_braces)
                        if open_brackets > close_brackets:
                            fixed_text += '\n' + ']' * (open_brackets - close_brackets)

                        issues = json.loads(fixed_text)
                        print("[AUDIT] Successfully parsed after fixing incomplete JSON")
                        # Continue with normal processing
                        if isinstance(issues, list):
                            valid_issues = []
                            for item in issues:
                                if isinstance(item, dict) and any(key in item for key in ["method", "line_number", "issue_description"]):
                                    valid_issues.append(item)
                            if valid_issues:
                                print(f"[AUDIT] Successfully found {len(valid_issues)} issue(s)")
                                return valid_issues
                            else:
                                print("[AUDIT] No security issues found - code is safe")
                                return []
                        elif isinstance(issues, dict):
                            # Handle dict as before
                            if "issues" in issues and isinstance(issues["issues"], list):
                                print(f"[AUDIT] Successfully found {len(issues['issues'])} issue(s)")
                                return issues["issues"]
                            elif any(key in issues for key in ["method", "line_number", "issue_description"]):
                                print("[AUDIT] Successfully found 1 issue")
                                return [issues]
                            else:
                                print("[AUDIT] No security issues found - code is safe")
                                return []
                    except Exception as e2:
                        print(f"[AUDIT] Failed to fix JSON: {e2}")

                # If JSON parsing fails, check if it's a text explanation
                if "no issues" in response_text.lower() or "safe" in response_text.lower():
                    print("[AUDIT] No security issues found - code is safe")
                    return []

                print(f"[AUDIT] ERROR: Failed to parse JSON response: {e}")
                print(f"[AUDIT] JSON string length: {len(json_str) if json_str else 0} characters")
                print(f"[AUDIT] JSON string (first 1000 chars): {json_str[:1000] if json_str else 'None'}")
                if json_str and len(json_str) > 1000:
                    print(f"[AUDIT] JSON string (last 500 chars): {json_str[-500:]}")
                print(f"[AUDIT] Full response text (first 500 chars): {response_text}")
                raise ValueError(f"LLM response is not valid JSON: {e}")

        except Exception as e:
            print(f"[AUDIT] ERROR: Failed to get response from LLM: {e}")
            raise
