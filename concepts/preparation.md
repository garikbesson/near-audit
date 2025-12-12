# Code Preparation for Security Audit

## Overview

Preparing your code properly before a security audit significantly improves the effectiveness of automated analysis tools and human reviewers. Well-structured, well-documented code helps both LLMs and security auditors understand the code's intent, identify potential vulnerabilities, and verify that security best practices are followed.

**Key Concepts**: code documentation, code readability, security audit preparation, code comments, variable naming, code structure, intent clarification, vulnerability detection

## Why Code Preparation Matters

### For LLM-Based Audits

Large Language Models (LLMs) analyze code by understanding:
- **Intent**: What the code is supposed to do
- **Context**: How different parts interact
- **Patterns**: Common security vulnerabilities and their indicators

Clear, well-documented code helps LLMs:
- Distinguish between intentional design choices and potential vulnerabilities
- Understand the business logic and security requirements
- Identify discrepancies between intended behavior and actual implementation
- Recognize security patterns and anti-patterns more accurately

### For Human Auditors

Well-prepared code:
- Reduces time spent understanding the codebase
- Makes it easier to trace data flow and identify attack vectors
- Helps distinguish bugs from intentional features
- Enables more thorough and accurate security reviews

## Essential Preparation Practices

### 1. Meaningful Variable and Function Names

**Why it matters**: Clear names communicate intent and make security issues more obvious.

**Good practices**:
- Use descriptive names that explain purpose, not just type
- Follow consistent naming conventions (e.g., `snake_case` for Rust)
- Avoid abbreviations unless they're widely understood
- Use names that indicate security-sensitive operations

**Examples**:

```rust
// ❌ Bad: Unclear intent
let a = env::attached_deposit();
let b = self.balances.get(&user);

// ✅ Good: Clear intent
let user_deposit = env::attached_deposit();
let user_balance = self.balances.get(&user);

// ✅ Better: Security intent is clear
let attached_deposit = env::attached_deposit();
let current_user_balance = self.balances.get(&user_id);
```

**Security-specific naming**:
- Prefix sensitive operations: `verify_user_authorization()`, `validate_deposit_amount()`
- Use names that indicate access control: `is_authorized()`, `check_permissions()`
- Make ownership clear: `owner_account_id`, `authorized_caller_id`

### 2. Comprehensive Comments

**Why it matters**: Comments explain the "why" behind code, helping auditors understand if security measures are intentional or missing.

**What to document**:

#### Security-Critical Sections
```rust
/// Verifies that the caller has attached at least 1 yoctoNEAR.
/// This prevents unauthorized calls via Function Call keys, which cannot attach NEAR.
/// Function Call keys are commonly used by websites and cannot be trusted for
/// operations that modify state or transfer assets.
assert!(
    env::attached_deposit() >= 1,
    "Must attach at least 1 yoctoNEAR to verify user authorization"
);
```

#### Business Logic and Assumptions
```rust
/// Calculates storage cost for a new balance entry.
/// Assumes: balance entry size is ~40 bytes (account_id + u128 balance)
/// Storage cost: 10^19 yoctoNEAR per byte
/// This check prevents storage drain attacks where attackers create many
/// small balance entries to drain the contract's balance.
let storage_cost = calculate_storage_cost_for_balance_entry();
```

#### Intentional Security Trade-offs
```rust
/// Note: We intentionally update state before the external call to prevent
/// reentrancy attacks. This follows the checks-effects-interactions pattern.
/// The state change happens first, then the external call, ensuring that
/// any reentrant call will see the updated state.
self.balances.insert(&user_id, &new_balance);
Promise::new(recipient_id).transfer(amount);
```

#### Complex Security Logic
```rust
/// Implements commit-reveal scheme to prevent frontrunning:
/// 1. User commits to a value (hash of value + secret)
/// 2. After reveal period, user reveals the value and secret
/// 3. Contract verifies hash matches committed value
/// This prevents validators from seeing the actual value before execution
/// and frontrunning the transaction.
```

### 3. Code Structure and Organization

**Why it matters**: Well-organized code makes it easier to trace data flow and identify security boundaries.

**Best practices**:

#### Separate Concerns
- Keep access control logic separate from business logic
- Isolate security checks in dedicated functions
- Group related security measures together

```rust
// ✅ Good: Security checks are isolated and reusable
impl Contract {
    fn verify_user_authorization(&self) {
        assert!(
            env::attached_deposit() >= 1,
            "Must attach at least 1 yoctoNEAR"
        );
    }
    
    fn verify_storage_payment(&self, data_size: u64) {
        let required_deposit = self.calculate_storage_cost(data_size);
        assert!(
            env::attached_deposit() >= required_deposit,
            "Insufficient deposit for storage"
        );
    }
    
    pub fn deposit(&mut self) {
        self.verify_user_authorization();
        self.verify_storage_payment(40); // balance entry size
        // ... business logic
    }
}
```

#### Clear Function Boundaries
- One function = one responsibility
- Make security checks explicit and visible
- Avoid deeply nested security logic

### 4. Document Security Assumptions

**Why it matters**: Explicit assumptions help auditors verify that security measures are appropriate for the use case.

**What to document**:

#### Access Control Assumptions
```rust
/// Security assumption: This function is safe to call publicly because:
/// 1. It only reads state (view function)
/// 2. It doesn't modify any state
/// 3. It doesn't transfer assets
/// If this assumption changes, add access control checks.
pub fn get_balance(&self, user_id: AccountId) -> Balance {
    self.balances.get(&user_id).unwrap_or(0)
}
```

#### Trust Boundaries
```rust
/// Security boundary: This function accepts input from untrusted sources.
/// All inputs must be validated before use:
/// - Account IDs must be valid NEAR account IDs
/// - Amounts must be positive and within reasonable bounds
/// - Strings must not exceed maximum length
pub fn transfer(&mut self, recipient: AccountId, amount: Balance) {
    // Input validation happens here
}
```

#### External Dependencies
```rust
/// Security consideration: This function makes a cross-contract call.
/// The called contract is trusted, but we still need to:
/// 1. Handle callback to verify success
/// 2. Implement rollback logic if call fails
/// 3. Prevent reentrancy by updating state before the call
```

### 5. Explicit Error Handling

**Why it matters**: Clear error messages help auditors understand failure modes and potential attack vectors.

**Good practices**:
- Use descriptive error messages that explain the security reason
- Distinguish between different failure types
- Make security-related errors distinct from business logic errors

```rust
// ❌ Bad: Generic error
assert!(amount > 0, "Invalid amount");

// ✅ Good: Security-focused error
assert!(
    amount > 0,
    "Transfer amount must be positive to prevent negative balance attacks"
);

// ✅ Better: Distinguishes security from business logic
if amount == 0 {
    env::panic_str("Transfer amount cannot be zero");
}
if amount > self.balances.get(&sender).unwrap_or(0) {
    env::panic_str("Insufficient balance: transfer would create negative balance");
}
```

### 6. Type Safety and Validation

**Why it matters**: Strong types and explicit validation make security boundaries clear.

**Best practices**:
- Use custom types for security-sensitive values
- Validate inputs at function boundaries
- Make validation logic explicit and documented

```rust
// ✅ Good: Type-safe approach
pub struct VerifiedUser {
    account_id: AccountId,
    // This type can only be created through verification
}

impl VerifiedUser {
    pub fn new(account_id: AccountId) -> Result<Self, String> {
        // Verification logic here
        if env::attached_deposit() < 1 {
            return Err("User not verified".to_string());
        }
        Ok(VerifiedUser { account_id })
    }
}
```

### 7. Document Security Patterns

**Why it matters**: Explicitly stating which security patterns you're using helps auditors verify correct implementation.

**Examples**:

```rust
/// Security pattern: Checks-Effects-Interactions
/// 1. CHECK: Verify preconditions (balance, permissions)
/// 2. EFFECTS: Update contract state
/// 3. INTERACTIONS: Make external calls
/// This order prevents reentrancy attacks.
pub fn withdraw(&mut self, amount: Balance) {
    // CHECK
    let balance = self.balances.get(&env::predecessor_account_id())
        .unwrap_or(0);
    assert!(balance >= amount, "Insufficient balance");
    
    // EFFECTS
    self.balances.insert(
        &env::predecessor_account_id(),
        &(balance - amount)
    );
    
    // INTERACTIONS
    Promise::new(env::predecessor_account_id()).transfer(amount);
}
```

### 8. Include Test Context

**Why it matters**: Tests document expected behavior and help auditors understand edge cases.

**Best practices**:
- Add comments explaining why certain test cases are important
- Document security-related test scenarios
- Explain what each test verifies

```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_withdraw_requires_1_yocto() {
        // Security test: Verifies that Function Call keys cannot withdraw
        // Function Call keys cannot attach NEAR, so this test ensures
        // only full access keys (user wallets) can withdraw funds.
        // ...
    }
    
    #[test]
    fn test_reentrancy_protection() {
        // Security test: Verifies that state is updated before external call
        // This prevents reentrancy attacks where a malicious contract
        // calls back into this contract during the external call.
        // ...
    }
}
```

## Checklist for Code Preparation

Before submitting code for security audit, ensure:

- [ ] All functions have clear, descriptive names
- [ ] Security-critical sections have explanatory comments
- [ ] Access control logic is explicit and documented
- [ ] Security assumptions are stated in comments
- [ ] Error messages explain security reasons
- [ ] Input validation is explicit and documented
- [ ] Security patterns (checks-effects-interactions, etc.) are identified
- [ ] Trust boundaries are clearly marked
- [ ] External dependencies and their trust levels are documented
- [ ] Complex business logic includes comments explaining intent
- [ ] Test cases document security scenarios

## Common Mistakes to Avoid

### ❌ Don't: Assume context is obvious
```rust
// Bad: No explanation of why this check exists
assert!(env::attached_deposit() >= 1);
```

### ✅ Do: Explain the security reason
```rust
// Good: Explains why 1 yoctoNEAR is required
// This prevents unauthorized calls via Function Call keys
assert!(env::attached_deposit() >= 1, "Must attach 1 yoctoNEAR");
```

### ❌ Don't: Use generic names for security operations
```rust
// Bad: Unclear what this does
fn check(&self) -> bool;
```

### ✅ Do: Use security-specific names
```rust
// Good: Clear security intent
fn verify_user_authorization(&self) -> bool;
```

### ❌ Don't: Hide security logic in complex expressions
```rust
// Bad: Security check is buried
if self.balances.get(&user).unwrap_or(0) >= amount && 
   env::attached_deposit() >= 1 && 
   self.is_authorized(&user) {
    // ...
}
```

### ✅ Do: Make security checks explicit
```rust
// Good: Each security check is clear
self.verify_user_authorization();
self.verify_sufficient_balance(&user, amount);
self.verify_user_permissions(&user);
// ... proceed with operation
```

## Impact on Audit Effectiveness

Well-prepared code significantly improves audit results by:

1. **Reducing false positives**: Clear intent helps distinguish vulnerabilities from intentional design
2. **Finding more real issues**: Better context helps identify subtle security problems
3. **Faster reviews**: Less time spent understanding code means more time finding issues
4. **Better recommendations**: Understanding intent leads to more relevant fix suggestions
5. **Comprehensive coverage**: Clear structure helps ensure all security aspects are reviewed

## Summary

Preparing code for security audit is not just about making it readable—it's about making security properties explicit and verifiable. Well-documented, well-structured code helps both automated tools and human auditors:

- Understand what the code is supposed to do
- Identify where security measures should be applied
- Verify that security measures are correctly implemented
- Distinguish between bugs and intentional design choices
- Provide accurate and actionable security recommendations

Investing time in code preparation pays off with more effective security audits and better security outcomes.

