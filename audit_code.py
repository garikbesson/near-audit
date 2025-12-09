#!/usr/bin/env python3
"""
Command-line tool for auditing NEAR smart contract code

Usage:
    python audit_code.py <file_path>
    
Example:
    python audit_code.py /path/to/contract.rs
    python audit_code.py ./test_contract.rs
"""

import sys
import os
import argparse
from code_auditor import CodeAuditor


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="Audit NEAR smart contract code for security vulnerabilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python audit_code.py contract.rs
  python audit_code.py /absolute/path/to/contract.rs
  python audit_code.py ./src/lib.rs
        """
    )
    
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the code file to audit (absolute or relative)"
    )
    
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Show verbose output"
    )
    
    args = parser.parse_args()
    
    # Resolve file path
    file_path = os.path.abspath(args.file_path)
    
    # Check if file exists
    if not os.path.exists(file_path):
        print(f"❌ Error: File not found: {file_path}")
        print(f"   Please check the path and try again.")
        sys.exit(1)
    
    # Check if vector store exists
    if not os.path.exists("./chroma/"):
        print("❌ Error: Vector store not found!")
        print("   Please run 'python create-vector.py' first to create the vector store.")
        sys.exit(1)
    
    print("=" * 70)
    print("NEAR Smart Contract Security Audit")
    print("=" * 70)
    print(f"\n📁 File: {file_path}")
    print(f"📊 Analyzing code for security vulnerabilities...\n")
    
    try:
        # Initialize auditor
        auditor = CodeAuditor()
        
        # Audit the file
        issues = auditor.audit_file(file_path)
        
        # Display results
        print("=" * 70)
        if issues:
            print(f"⚠️  Found {len(issues)} security issue(s):\n")
            
            for i, issue in enumerate(issues, 1):
                print(f"🔴 Issue #{i}")
                print(f"   File:    {issue['file_path']}")
                print(f"   Line:    {issue['line_number']}")
                print(f"   Problem: {issue['issue_description']}")
                print(f"   Fix:     {issue['recommendation']}")
                print()
            
            print("=" * 70)
            print(f"⚠️  Total issues found: {len(issues)}")
            print("=" * 70)
            sys.exit(1)  # Exit with error code if issues found
        else:
            print("✅ No security issues found!")
            print("   The code appears to be secure based on the security documentation.")
            print("=" * 70)
            sys.exit(0)
            
    except FileNotFoundError as e:
        print(f"❌ Error: File not found - {str(e)}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error during audit: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

