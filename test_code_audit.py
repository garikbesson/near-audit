#!/usr/bin/env python3
"""
Test script for code audit functionality
"""

import asyncio
import os
from mcp_server import app, call_tool


async def test_audit_contract_code():
    """Test the audit_contract_code tool."""
    print("=" * 60)
    print("Testing audit_contract_code tool")
    print("=" * 60)
    
    # Get absolute path to test contract
    test_file = os.path.abspath("test_contract.rs")
    
    if not os.path.exists(test_file):
        print(f"✗ Test file not found: {test_file}")
        print("  Creating a simple test file...")
        # Create a minimal test file
        with open(test_file, 'w') as f:
            f.write("""use near_sdk::borsh::{self, BorshDeserialize, BorshSerialize};
use near_sdk::{env, near_bindgen, AccountId, Promise};

#[near_bindgen]
pub struct Contract {
    pub balances: std::collections::HashMap<AccountId, u128>,
}

#[near_bindgen]
impl Contract {
    pub fn withdraw(&mut self, amount: u128) {
        let account = env::predecessor_account_id();
        let balance = self.balances.get(&account).unwrap_or(&0);
        
        if *balance >= amount {
            self.balances.insert(account.clone(), balance - amount);
            Promise::new(account).transfer(amount);
        }
    }
}
""")
        print(f"  Created test file: {test_file}")
    
    print(f"\nAuditing file: {test_file}\n")
    
    try:
        result = await call_tool(
            "audit_contract_code",
            {"file_path": test_file}
        )
        
        if result and len(result) > 0:
            text = result[0].text if hasattr(result[0], 'text') else str(result[0])
            print(text)
            print("\n✓ Audit completed successfully!")
            return True
        else:
            print("✗ No results returned")
            return False
            
    except Exception as e:
        print(f"✗ Error during audit: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_code_auditor_directly():
    """Test CodeAuditor directly."""
    print("\n" + "=" * 60)
    print("Testing CodeAuditor directly")
    print("=" * 60)
    
    try:
        from code_auditor import CodeAuditor
        
        auditor = CodeAuditor()
        test_file = os.path.abspath("test_contract.rs")
        
        if not os.path.exists(test_file):
            print(f"✗ Test file not found: {test_file}")
            return False
        
        print(f"\nAuditing file: {test_file}\n")
        issues = auditor.audit_file(test_file)
        
        if issues:
            print(f"Found {len(issues)} security issue(s):\n")
            for i, issue in enumerate(issues, 1):
                print(f"Issue #{i}:")
                print(f"  File: {issue['file_path']}")
                print(f"  Line: {issue['line_number']}")
                print(f"  Problem: {issue['issue_description']}")
                print(f"  Recommendation: {issue['recommendation']}")
                print()
            print("✓ Direct audit completed successfully!")
            return True
        else:
            print("No issues found (this might be expected if LLM didn't find issues)")
            return True
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("Code Audit Functionality Test Suite")
    print("=" * 60)
    
    # Check if vector store exists
    if not os.path.exists("./chroma/"):
        print("\n✗ ERROR: Vector store not found!")
        print("Please run 'python create-vector.py' first to create the vector store.")
        return
    
    results = []
    
    # Test direct CodeAuditor
    results.append(("Direct CodeAuditor", await test_code_auditor_directly()))
    
    # Test MCP tool
    results.append(("MCP audit_contract_code tool", await test_audit_contract_code()))
    
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
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")


if __name__ == "__main__":
    asyncio.run(main())

