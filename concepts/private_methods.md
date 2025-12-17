# Private Methods in NEAR Smart Contracts - Security Audit Guide

## Overview

In NEAR Protocol smart contracts, **private methods** are functions that should only be callable by the contract itself, not by external users or other contracts. These methods are critical for security, especially for internal logic, callbacks from cross-contract calls, and state management operations.

**Key Security Principle**: Any method that performs sensitive operations or should only be invoked internally MUST be protected from external calls.

## ⚠️ CRITICAL RULES FOR AUDITORS

**ALWAYS FLAG AS VULNERABILITY:**

1. **`pub fn internal_*` without `#[private]`** - Any method with "internal" in its name declared as `pub fn` WITHOUT `#[private]` is ALWAYS a vulnerability. It must be `pub(crate) fn` (preferred) or `#[private] pub fn` (only if callback).
   - Example: `pub fn internal_stake_from_account(...)` → Should be `pub(crate) fn internal_stake_from_account(...)`

2. **`pub fn *_helper` or `pub fn helper_*` without `#[private]`** - Any method with "helper" in its name declared as `pub fn` WITHOUT `#[private]` is ALWAYS a vulnerability. It must be `pub(crate) fn` (preferred) or `#[private] pub fn` (only if callback).
   - Example: `pub fn sign_helper(...)` → Should be `pub(crate) fn sign_helper(...)` or `#[private] pub fn sign_helper(...)` if it's a callback

3. **`pub fn callback_*`, `pub fn on_*`, `pub fn after_*`, `pub fn *_callback` without `#[private]`** - Any method with callback-indicating names declared as `pub fn` WITHOUT `#[private]` is ALWAYS a vulnerability.

**DO NOT FLAG:**
- `pub(crate) fn` methods - These are already correctly protected
- `#[private] pub fn` methods - These are already correctly protected
- Public methods without "internal", "helper", or callback names - May be intentionally public

## What Are Private Methods?

Private methods in NEAR contracts are methods that can only be called by the contract itself. There are two types:

### Type 1: `pub fn` with `#[private]` Decorator
- Part of the contract's public interface but protected from external calls
- Can be called via cross-contract callbacks (`.then()`)
- Must be protected using the `#[private]` decorator (preferred) or manual predecessor checks (not recommended)
- Used for callbacks and methods that need runtime access control

### Type 2: `pub(crate) fn` Internal Methods
- NOT part of the contract's public interface
- Cannot be called externally at all (compile-time protection)
- Do NOT require the `#[private]` decorator
- Used for internal helper functions and utilities
- Can only be called from within the same contract code

**Key Difference**: `pub(crate)` methods are excluded from the contract interface at compile time, while `#[private] pub fn` methods are part of the interface but protected at runtime.

## Why Private Methods Matter

**Security Risks Without Private Methods:**
1. **Unauthorized Access**: External actors can call internal methods directly
2. **Callback Exploitation**: Attackers can call callback methods and bypass security checks
3. **State Manipulation**: Internal state management methods can be exploited
4. **Reentrancy Attacks**: Unprotected callbacks can be used in reentrancy attacks
5. **Bypass Validation**: Attackers can skip validation logic by calling internal methods directly

## Implementation: The `#[private]` Decorator

### Correct Implementation

In Rust NEAR contracts, use the `#[private]` decorator macro:

```rust
// ✅ CORRECT - Private method with #[private] decorator
#[private]
pub fn internal_method(&mut self) {
    // Only the contract itself can call this
    // The #[private] decorator automatically checks:
    // env::predecessor_account_id() == env::current_account_id()
}

// ✅ CORRECT - Private callback method
#[private]
pub fn callback_after_external_call(&mut self, result: Result<(), String>) {
    match result {
        Ok(_) => {
            // External call succeeded, commit state
            self.commit_state();
        }
        Err(_) => {
            // External call failed, rollback state
            self.rollback_state();
        }
    }
}
```

### Manual Implementation (Not Recommended - Use `#[private]` Instead)

**⚠️ IMPORTANT**: Manual predecessor checks are **NOT recommended**. Always prefer the `#[private]` decorator. If you find manual checks in code, they should be refactored to use `#[private]`.

**Why `#[private]` is better:**
- Less error-prone (no risk of typos or wrong comparisons)
- More readable and maintainable
- Standard NEAR pattern that other developers expect
- Automatically handles the check correctly

**If you encounter manual checks in audited code**, recommend replacing them with `#[private]`:

```rust
// ❌ NOT RECOMMENDED - Manual predecessor check (should be replaced)
pub fn internal_method(&mut self) {
    assert_eq!(
        env::predecessor_account_id(),
        env::current_account_id(),
        "Only contract can call this method"
    );
    // Method implementation
}

// ✅ RECOMMENDED - Replace with #[private] decorator
#[private]
pub fn internal_method(&mut self) {
    // Method implementation
    // The #[private] decorator automatically performs the same check
}
```

**When auditing**: If you find manual `assert_eq!(env::predecessor_account_id(), env::current_account_id(), ...)` checks, flag them as code that should be refactored to use `#[private]` for better maintainability and consistency.

## Internal Methods: `pub(crate)` Functions

### Understanding `pub(crate)` vs `pub` Methods

In Rust NEAR contracts, there are two ways to create internal methods:

1. **`pub fn` with `#[private]` decorator** - Methods that are part of the contract's public interface but protected from external calls
2. **`pub(crate) fn`** - Methods that are NOT part of the contract's public interface and cannot be called externally at all

### `pub(crate)` Methods - True Internal Methods

**Key Characteristics:**
- `pub(crate)` methods are **NOT exported** to the NEAR contract interface
- They **cannot be called** by external users or other contracts
- They can **only be called** from within the same contract code (same crate)
- They **do NOT require** the `#[private]` decorator
- They are truly internal helper methods

**When to Use `pub(crate)`:**
- Internal helper functions that should never be part of the contract interface
- Utility methods used only within the contract
- Methods that are called by other internal methods but not by callbacks or external code
- Internal state management functions that don't need to be accessible via cross-contract calls

**Correct Implementation:**
```rust
impl Contract {
    // ✅ CORRECT - pub(crate) method, no #[private] needed
    // This method is NOT part of the contract interface
    pub(crate) fn internal_calculate_fee(&self, amount: u128) -> u128 {
        amount * self.fee_rate / 10000
    }
    
    // ✅ CORRECT - pub(crate) method for internal state management
    pub(crate) fn internal_update_balance(
        &mut self,
        account_id: &AccountId,
        amount: u128,
    ) {
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }
    
    // ✅ CORRECT - Public method that uses internal helper
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let fee = self.internal_calculate_fee(amount); // Can call pub(crate) method
        let net_amount = amount - fee;
        self.internal_update_balance(&env::signer_account_id(), net_amount);
    }
}
```

### When to Use `#[private] pub fn` vs `pub(crate) fn`

**Use `#[private] pub fn` when:**
- The method needs to be callable via cross-contract callbacks (`.then()`)
- The method must be accessible to the NEAR runtime but protected from external calls
- The method is a callback handler that receives results from external contracts

**Use `pub(crate) fn` when:**
- The method is a pure internal helper function
- The method should never be part of the contract's public interface
- The method is only called from within the contract's own code
- You want compile-time guarantee that the method cannot be called externally

**Comparison Example:**
```rust
impl Contract {
    // ✅ Use pub(crate) for internal helpers
    pub(crate) fn validate_amount(&self, amount: u128) -> bool {
        amount >= self.min_deposit && amount <= self.max_deposit
    }
    
    // ✅ Use #[private] pub fn for callbacks
    #[private]
    pub fn callback_after_staking(&mut self, result: Result<(), String>) {
        // This must be pub because it's called via .then() in cross-contract calls
        // But it's protected with #[private] to prevent direct external calls
        match result {
            Ok(_) => {
                // Use internal helper
                if self.validate_amount(self.pending_amount) {
                    self.commit_deposit();
                }
            }
            Err(_) => {
                self.rollback_deposit();
            }
        }
    }
    
    // ✅ Public method that uses internal helper
    pub fn stake(&mut self) {
        let amount = env::attached_deposit();
        if !self.validate_amount(amount) { // Can call pub(crate) method
            env::panic_str("Invalid amount");
        }
        // Make cross-contract call
        Promise::new(validator_id.clone())
            .function_call("stake", ...)
            .then(env::current_account_id(), "callback_after_staking", ...);
    }
}
```

### Common Mistakes with `pub(crate)` Methods

**Mistake 1: Using `#[private]` with `pub(crate)`**
```rust
// ❌ WRONG - pub(crate) doesn't need #[private]
#[private]
pub(crate) fn internal_method(&mut self) {
    // This is redundant - pub(crate) already prevents external calls
}

// ✅ CORRECT - Just use pub(crate) without decorator
pub(crate) fn internal_method(&mut self) {
    // No decorator needed
}
```

**Mistake 2: Using `pub(crate)` for Callbacks**
```rust
// ❌ WRONG - Callbacks must be pub to receive cross-contract call results
pub(crate) fn callback_after_external_call(&mut self, result: Result<(), String>) {
    // This won't work! Callbacks need to be pub
}

// ✅ CORRECT - Callbacks must be pub with #[private]
#[private]
pub fn callback_after_external_call(&mut self, result: Result<(), String>) {
    // This works correctly
}
```

**Mistake 3: Making Internal Helpers Public**
```rust
// ❌ WRONG - Internal helper shouldn't be part of contract interface
pub fn internal_calculate_fee(&self, amount: u128) -> u128 {
    // External users can call this directly!
    amount * self.fee_rate / 10000
}

// ✅ CORRECT - Use pub(crate) for internal helpers
pub(crate) fn internal_calculate_fee(&self, amount: u128) -> u128 {
    // Not accessible externally
    amount * self.fee_rate / 10000
}
```

## Common Vulnerabilities to Look For

### Vulnerability 1: Missing `#[private]` on Internal Methods

**⚠️ CRITICAL RULE**: Any method with "internal" or "helper" in its name that is declared as `pub fn` WITHOUT `#[private]` is ALWAYS a security vulnerability. It must be either `pub(crate) fn` or `#[private] pub fn` (if it's a callback).

**What to Look For:**
- Methods that perform internal operations but lack the `#[private]` decorator
- Methods that modify contract state but are callable externally
- Internal helper methods that should not be public
- **Methods with "internal" in their name** - These are strong indicators that the method should NOT be publicly accessible. Methods with names like `internal_*`, `*_internal`, `internal_*_internal` should be either:
  - `pub(crate) fn` (preferred for pure internal helpers - NOT callbacks)
  - `#[private] pub fn` (ONLY if they need to be callbacks for cross-contract calls)
  - **ALWAYS FLAG AS VULNERABILITY**: Any `pub fn internal_*` method WITHOUT `#[private]` decorator - even if it's not a callback, it should be `pub(crate) fn` instead
  - **Example**: `pub fn internal_stake_from_account(...)` is a vulnerability - should be `pub(crate) fn internal_stake_from_account(...)`
- **Methods with "helper" in their name** - These are strong indicators that the method is an internal utility function and should NOT be publicly accessible. Methods with names like `*_helper`, `helper_*`, `*_helper_*` should be either:
  - `pub(crate) fn` (preferred for pure internal helpers - NOT callbacks)
  - `#[private] pub fn` (ONLY if they need to be callbacks for cross-contract calls)
  - **ALWAYS FLAG AS VULNERABILITY**: Any `pub fn *_helper` or `pub fn helper_*` method WITHOUT `#[private]` decorator - even if it's not a callback, it should be `pub(crate) fn` instead
  - **Example**: `pub fn sign_helper(...)` is a vulnerability - should be `pub(crate) fn sign_helper(...)` or `#[private] pub fn sign_helper(...)` if it's a callback

**Vulnerable Code:**
```rust
// ❌ VULNERABLE - Method with "internal" in name but publicly accessible
pub fn internal_state_update(&mut self, user_id: AccountId) {
    // Anyone can call this and manipulate state!
    // The name "internal" indicates this should NOT be public!
    self.balances.insert(&user_id, &1000);
}

// ❌ VULNERABLE - Another example of unprotected internal method
pub fn internal_calculate_fee(&self, amount: u128) -> u128 {
    // External users can call this directly!
    // Should be pub(crate) fn instead
    amount * self.fee_rate / 10000
}

// ❌ VULNERABLE - Internal method without protection
pub fn reset_contract_state(&mut self) {
    // Attacker can call this and reset everything!
    self.state.clear();
}

// ❌ VULNERABLE - Method with "internal" in name but publicly accessible (should be pub(crate))
pub fn internal_stake_from_account(&mut self, account_id: &AccountId, amount: u128) -> u128 {
    // Anyone can call this! The name "internal" indicates this should NOT be public!
    // Should be pub(crate) fn instead, NOT pub fn
    let mut acc = self.get_account(account_id);
    let shares = self.calculate_shares(amount);
    acc.add_shares(shares);
    self.update_account(account_id, &acc);
    shares
}

// ❌ VULNERABLE - Method with "helper" in name but publicly accessible (should be pub(crate) or #[private])
pub fn sign_helper(&mut self, data: &[u8]) -> Vec<u8> {
    // Anyone can call this! The name "helper" indicates this should NOT be public!
    // Should be pub(crate) fn instead (or #[private] pub fn if it's a callback)
    self.sign_data(data)
}

// ❌ VULNERABLE - Another example of unprotected helper method
pub fn calculate_helper(&self, amount: u128) -> u128 {
    // External users can call this directly!
    // Should be pub(crate) fn instead
    amount * self.fee_rate / 10000
}
```

**Secure Code:**
```rust
// ✅ SECURE - Internal method using pub(crate) (preferred for non-callback internal methods)
pub(crate) fn internal_stake_from_account(&mut self, account_id: &AccountId, amount: u128) -> u128 {
    // Cannot be called externally - compile-time protection
    // This is the correct way for internal methods that are NOT callbacks
    let mut acc = self.get_account(account_id);
    let shares = self.calculate_shares(amount);
    acc.add_shares(shares);
    self.update_account(account_id, &acc);
    shares
}

// ✅ SECURE - Internal helper using pub(crate) (preferred for pure helpers)
pub(crate) fn internal_calculate_fee(&self, amount: u128) -> u128 {
    // Cannot be called externally - compile-time protection
    amount * self.fee_rate / 10000
}

// ✅ SECURE - Protected with #[private] (ONLY if it needs to be a callback)
#[private]
pub fn internal_state_update(&mut self, user_id: AccountId) {
    // Only contract can call this
    // Use #[private] ONLY if this is called via .then() in cross-contract calls
    self.balances.insert(&user_id, &1000);
}

#[private]
pub fn reset_contract_state(&mut self) {
    // Only contract can call this
    self.state.clear();
}

// ✅ SECURE - Helper method using pub(crate) (preferred for non-callback helpers)
pub(crate) fn sign_helper(&mut self, data: &[u8]) -> Vec<u8> {
    // Cannot be called externally - compile-time protection
    // This is the correct way for helper methods that are NOT callbacks
    self.sign_data(data)
}

// ✅ SECURE - Helper method using pub(crate)
pub(crate) fn calculate_helper(&self, amount: u128) -> u128 {
    // Cannot be called externally - compile-time protection
    amount * self.fee_rate / 10000
}

// ✅ SECURE - Helper method with #[private] (ONLY if it's a callback)
#[private]
pub fn helper_callback(&mut self, result: Result<(), String>) {
    // Use #[private] ONLY if this is called via .then() in cross-contract calls
    // Otherwise, use pub(crate) fn
    match result {
        Ok(_) => self.commit(),
        Err(_) => self.rollback(),
    }
}
```

### Vulnerability 2: Unprotected Callback Methods

**What to Look For:**
- Callback methods (methods that handle results from cross-contract calls) without `#[private]`
- **Methods with callback-indicating names** - These are strong indicators that the method should be protected. Methods with names like:
  - `callback_*` (e.g., `callback_after_staking`, `callback_on_success`, `callback_handler`)
  - `on_*` (e.g., `on_stake_complete`, `on_transfer_done`, `on_error`)
  - `after_*` (e.g., `after_staking`, `after_transfer`, `after_external_call`)
  - `*_callback` (e.g., `staking_callback`, `transfer_callback`)
  - `*_on_*` (e.g., `handle_on_success`, `process_on_error`)
  - If a method has these callback-indicating names but is declared as `pub fn` without `#[private]`, this is a **critical security vulnerability**
- Any method that is called via `.then()` in cross-contract calls
- Methods that accept `Result<...>` or similar error-handling types as parameters (common callback signature)

**Vulnerable Code:**
```rust
// ❌ VULNERABLE - Callback with "callback" in name but unprotected
pub fn callback_after_staking(&mut self, result: Result<(), String>) {
    // Attacker can call this directly! Name indicates it's a callback.
    match result {
        Ok(_) => {
            self.user_balances.insert(&self.pending_user, &self.pending_amount);
        }
        Err(_) => {
            // Attacker can trigger this to rollback legitimate operations
        }
    }
}

// ❌ VULNERABLE - Method with "on_" prefix but unprotected
pub fn on_stake_complete(&mut self, result: Result<u128, String>) {
    // Name indicates callback but no protection!
    if let Ok(shares) = result {
        self.user_shares.insert(&self.pending_user, &shares);
    }
}

// ❌ VULNERABLE - Method with "after_" prefix but unprotected
pub fn after_transfer(&mut self, success: bool) {
    // Name indicates callback but no protection!
    if success {
        self.commit_transfer();
    } else {
        self.rollback_transfer();
    }
}

// In another method:
Promise::new(validator_id)
    .function_call("stake", ...)
    .then(env::current_account_id(), "callback_after_staking", ...);
```

**Secure Code:**
```rust
// ✅ SECURE - Protected callback with #[private]
#[private]
pub fn callback_after_staking(&mut self, result: Result<(), String>) {
    // Only the contract can call this after the cross-contract call
    match result {
        Ok(_) => {
            self.user_balances.insert(&self.pending_user, &self.pending_amount);
        }
        Err(_) => {
            // Rollback state and refund user
            Promise::new(self.pending_user.clone()).transfer(self.pending_amount);
        }
    }
}

// ✅ SECURE - Protected callback with "on_" prefix
#[private]
pub fn on_stake_complete(&mut self, result: Result<u128, String>) {
    // Protected - only contract can call
    if let Ok(shares) = result {
        self.user_shares.insert(&self.pending_user, &shares);
    }
}

// ✅ SECURE - Protected callback with "after_" prefix
#[private]
pub fn after_transfer(&mut self, success: bool) {
    // Protected - only contract can call
    if success {
        self.commit_transfer();
    } else {
        self.rollback_transfer();
    }
}
```

### Vulnerability 3: Incorrect Predecessor Check

**What to Look For:**
- Manual checks that use `signer` instead of `predecessor` for private methods
- Checks that compare against wrong account IDs
- Missing checks entirely

**Vulnerable Code:**
```rust
// ❌ VULNERABLE - Wrong check (using signer instead of predecessor)
pub fn internal_method(&mut self) {
    // This is wrong! signer is the human who signed, not who called
    assert_eq!(
        env::signer_account_id(),
        env::current_account_id(),
        "Only contract"
    );
}

// ❌ VULNERABLE - Missing check
pub fn internal_method(&mut self) {
    // No check at all - anyone can call this!
    self.perform_sensitive_operation();
}

// ⚠️ NOT RECOMMENDED - Manual check (should use #[private] instead)
pub fn internal_method(&mut self) {
    assert_eq!(
        env::predecessor_account_id(),
        env::current_account_id(),
        "Only contract can call this method"
    );
    self.perform_sensitive_operation();
}
```

**Secure Code:**
```rust
// ✅ SECURE - Use #[private] decorator (preferred method)
#[private]
pub fn internal_method(&mut self) {
    // The #[private] decorator automatically checks:
    // env::predecessor_account_id() == env::current_account_id()
    self.perform_sensitive_operation();
}
```

## Audit Checklist: What to Verify

When auditing a NEAR smart contract, check the following:

### 1. All Internal Methods Are Protected
- [ ] Every `pub fn` method that should only be callable by the contract has `#[private]` decorator
- [ ] **Methods with "internal" in their name** are checked:
  - All `pub fn internal_*` methods have either `#[private]` or are `pub(crate) fn`
  - No unprotected `pub fn internal_*` methods exist
  - Methods with "internal" in name that are `pub fn` without protection are flagged as critical vulnerabilities
- [ ] **Methods with "helper" in their name** are checked:
  - All `pub fn *_helper` methods have either `#[private]` or are `pub(crate) fn`
  - All `pub fn helper_*` methods have either `#[private]` or are `pub(crate) fn`
  - No unprotected `pub fn *_helper` or `pub fn helper_*` methods exist
  - Methods with "helper" in name that are `pub fn` without protection are flagged as critical vulnerabilities
- [ ] Internal helper methods use `pub(crate) fn` (preferred) or `#[private] pub fn` (for callbacks)
- [ ] State modification methods are protected (either `pub(crate)` or `#[private] pub fn`)
- [ ] Methods that perform sensitive operations are protected
- [ ] No `pub(crate)` methods have `#[private]` decorator (it's redundant)

### 2. All Callback Methods Are Protected
- [ ] **Methods with callback-indicating names** are checked:
  - All `pub fn callback_*` methods have `#[private]` decorator
  - All `pub fn on_*` methods have `#[private]` decorator
  - All `pub fn after_*` methods have `#[private]` decorator
  - All `pub fn *_callback` methods have `#[private]` decorator
  - Methods with callback-indicating names that are `pub fn` without `#[private]` are flagged as critical vulnerabilities
- [ ] Every callback method (methods called via `.then()`) has `#[private]` decorator
- [ ] Callback methods cannot be called directly by external users
- [ ] Callback methods properly handle errors and rollback state

### 3. Manual Checks Are Replaced with `#[private]`
- [ ] Any manual `assert_eq!(env::predecessor_account_id(), env::current_account_id(), ...)` checks are replaced with `#[private]` decorator
- [ ] If manual checks exist, they use `predecessor_account_id()` not `signer_account_id()`
- [ ] If manual checks exist, they compare against `current_account_id()`
- [ ] Flag manual checks as code that should be refactored to use `#[private]`

### 4. Proper Use of `pub(crate)` vs `#[private] pub fn`
- [ ] Internal helper methods that don't need to be callbacks use `pub(crate) fn`
- [ ] Callback methods use `#[private] pub fn` (not `pub(crate) fn`)
- [ ] No `pub(crate)` methods are incorrectly used as callbacks
- [ ] Internal helpers are not unnecessarily exposed as `pub fn` methods

### 5. No Bypass Opportunities
- [ ] There are no public methods that allow calling private functionality indirectly
- [ ] Internal methods cannot be accessed through other public methods
- [ ] Callback methods cannot be exploited to bypass validation

## Common Patterns to Identify

### Pattern 1: Methods with Callback-Indicating Names

**Look for:**
- Methods with names that indicate they are callbacks:
  - `callback_*` (e.g., `callback_after_staking`, `callback_on_success`, `callback_handler`)
  - `on_*` (e.g., `on_stake_complete`, `on_transfer_done`, `on_error`, `on_success`)
  - `after_*` (e.g., `after_staking`, `after_transfer`, `after_external_call`, `after_deposit`)
  - `*_callback` (e.g., `staking_callback`, `transfer_callback`, `deposit_callback`)
  - `*_on_*` (e.g., `handle_on_success`, `process_on_error`, `execute_on_complete`)

**Why this matters:**
- These naming patterns are strong semantic indicators that the method is a callback handler
- Callbacks are one of the most common attack vectors in NEAR contracts
- If a method has a callback-indicating name but is declared as `pub fn` without `#[private]`, attackers can call it directly and manipulate state
- Developers use these naming patterns to indicate methods that handle asynchronous cross-contract call results

**Verify:**
- All methods with callback-indicating names must have `#[private]` decorator
- **Flag as critical vulnerability**: Any `pub fn callback_*`, `pub fn on_*`, `pub fn after_*`, or `pub fn *_callback` without `#[private]`
- Check if the method signature includes `Result<...>` or error-handling types (common callback pattern)
- Verify the method is actually used as a callback (check for `.then()` calls referencing it)

**Example patterns to search for:**
```rust
// Search for these patterns in code:
pub fn callback_*
pub fn on_*
pub fn after_*
pub fn *_callback
pub fn *_on_*
```

### Pattern 2: Cross-Contract Call Callbacks (Usage Pattern)

**Look for:**
```rust
Promise::new(target_account)
    .function_call(...)
    .then(env::current_account_id(), "callback_method_name", ...);
```

**Verify:**
- The `callback_method_name` method exists and has `#[private]`
- The callback properly handles success and failure cases
- The callback rolls back state if the external call failed
- If the callback method name matches callback-indicating patterns (see Pattern 1), ensure it's protected

### Pattern 3: Methods with "internal" in Name

**⚠️ CRITICAL RULE**: Any `pub fn internal_*` method WITHOUT `#[private]` is ALWAYS a vulnerability. It must be either `pub(crate) fn` (preferred) or `#[private] pub fn` (only if it's a callback).

**Look for:**
- Methods with names containing "internal" (e.g., `internal_*`, `*_internal`, `internal_*_internal`)
- Common patterns: `internal_stake`, `internal_stake_from_account`, `internal_update`, `internal_get_account`, `internal_calculate_*`, etc.

**Why this matters:**
- The name "internal" is a strong semantic indicator that the method should NOT be publicly accessible
- If a method is named "internal" but is declared as `pub fn` without protection, it's ALWAYS a security vulnerability
- Developers use "internal" in method names to indicate these are implementation details, not part of the public API

**Verify:**
- Methods with "internal" in name should be either:
  - `pub(crate) fn` (preferred for non-callback internal methods - compile-time protection, not part of contract interface)
  - `#[private] pub fn` (ONLY if they need to be callbacks for cross-contract calls)
- **ALWAYS FLAG AS VULNERABILITY**: Any `pub fn internal_*` method WITHOUT `#[private]` decorator
  - Example: `pub fn internal_stake_from_account(...)` → Should be `pub(crate) fn internal_stake_from_account(...)`
  - Even if the method is not a callback, it should be `pub(crate) fn`, NOT `pub fn`
- Check if the method is actually used only internally or if it needs to be a callback

**Example patterns to search for:**
```rust
// Search for these patterns in code - ALL of these are vulnerabilities if found:
pub fn internal_*
pub fn *_internal
pub fn *_internal_*

// Examples of vulnerable code:
pub fn internal_stake_from_account(...)  // ❌ VULNERABLE - should be pub(crate) fn
pub fn internal_update(...)              // ❌ VULNERABLE - should be pub(crate) fn
pub fn internal_calculate_fee(...)       // ❌ VULNERABLE - should be pub(crate) fn
```

### Pattern 4: Methods with "helper" in Name

**⚠️ CRITICAL RULE**: Any `pub fn *_helper` or `pub fn helper_*` method WITHOUT `#[private]` is ALWAYS a vulnerability. It must be either `pub(crate) fn` (preferred) or `#[private] pub fn` (only if it's a callback).

**Look for:**
- Methods with names containing "helper" (e.g., `*_helper`, `helper_*`, `*_helper_*`)
- Common patterns: `sign_helper`, `calculate_helper`, `helper_function`, `validate_helper`, `format_helper`, etc.

**Why this matters:**
- The name "helper" is a strong semantic indicator that the method is an internal utility function and should NOT be publicly accessible
- Helper methods are typically implementation details used to support other methods, not part of the public API
- If a method is named "helper" but is declared as `pub fn` without protection, it's ALWAYS a security vulnerability
- Developers use "helper" in method names to indicate these are utility functions, not public interface methods

**Verify:**
- Methods with "helper" in name should be either:
  - `pub(crate) fn` (preferred for non-callback helper methods - compile-time protection, not part of contract interface)
  - `#[private] pub fn` (ONLY if they need to be callbacks for cross-contract calls)
- **ALWAYS FLAG AS VULNERABILITY**: Any `pub fn *_helper`, `pub fn helper_*`, or `pub fn *_helper_*` method WITHOUT `#[private]` decorator
  - Example: `pub fn sign_helper(...)` → Should be `pub(crate) fn sign_helper(...)` or `#[private] pub fn sign_helper(...)` if it's a callback
  - Even if the method is not a callback, it should be `pub(crate) fn`, NOT `pub fn`
- Check if the method is actually used only internally or if it needs to be a callback

**Example patterns to search for:**
```rust
// Search for these patterns in code - ALL of these are vulnerabilities if found:
pub fn *_helper
pub fn helper_*
pub fn *_helper_*

// Examples of vulnerable code:
pub fn sign_helper(...)        // ❌ VULNERABLE - should be pub(crate) fn or #[private] pub fn
pub fn calculate_helper(...)   // ❌ VULNERABLE - should be pub(crate) fn
pub fn format_helper(...)      // ❌ VULNERABLE - should be pub(crate) fn
```

### Pattern 5: Internal State Management

**Look for:**
- Methods that update balances, state, or internal data structures
- Methods that perform cleanup or reset operations
- Methods that modify contract configuration

**Verify:**
- All such methods are either `pub(crate) fn` (for internal helpers) or `#[private] pub fn` (if they need to be callbacks)
- These methods are only called from within the contract
- Internal state management helpers use `pub(crate)` when possible

### Pattern 6: Reentrancy Protection

**Look for:**
- Methods that make cross-contract calls
- Methods that update state before external calls
- Callback methods that update state

**Verify:**
- State updates happen AFTER callbacks confirm success
- Callbacks are protected with `#[private]`
- No state is committed before external operations complete

## Environment Variables Reference

Understanding these is crucial for private method security:

- **`env::predecessor_account_id()`**: The account that called the current method (could be a contract or user)
  - Use this for checking if the contract itself called the method
  - For private methods: `predecessor == current_account_id`

- **`env::current_account_id()`**: The account ID of the contract itself
  - Use this as the comparison target for private method checks

- **`env::signer_account_id()`**: The account that signed the transaction (always a human/account, never a contract)
  - Use this for user authorization, NOT for private method checks
  - Do NOT use this to verify if the contract called itself

## Examples: Complete Vulnerable vs Secure Patterns

### Example 1: Deposit with Staking

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE
impl Contract {
    pub fn deposit_and_stake(&mut self, user_id: AccountId) {
        let amount = env::attached_deposit();
        // VULNERABILITY: Updates state before external call
        self.balances.insert(&user_id, &amount);
        
        Promise::new(validator_id.clone())
            .function_call("stake", ...)
            .then(env::current_account_id(), "callback_after_stake", ...);
    }
    
    // VULNERABILITY: Callback not protected
    pub fn callback_after_stake(&mut self, result: Result<(), String>) {
        match result {
            Err(_) => {
                // VULNERABILITY: Attacker can call this directly to manipulate state
                self.balances.remove(&user_id);
            }
            Ok(_) => {}
        }
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE
impl Contract {
    pub fn deposit_and_stake(&mut self, user_id: AccountId) {
        let amount = env::attached_deposit();
        // SECURE: Store in temporary state, don't update balance yet
        self.pending_deposits.insert(&user_id, &amount);
        
        Promise::new(validator_id.clone())
            .function_call("stake", ...)
            .then(env::current_account_id(), "callback_after_stake", ...);
    }
    
    // SECURE: Protected callback
    #[private]
    pub fn callback_after_stake(&mut self, result: Result<(), String>) {
        match result {
            Ok(_) => {
                // Only update balance if staking succeeded
                let user_id = self.pending_user.clone();
                let amount = self.pending_deposits.get(&user_id).unwrap();
                self.balances.insert(&user_id, &amount);
                self.pending_deposits.remove(&user_id);
            }
            Err(_) => {
                // Rollback: refund user
                let user_id = self.pending_user.clone();
                let amount = self.pending_deposits.get(&user_id).unwrap();
                Promise::new(user_id).transfer(amount);
                self.pending_deposits.remove(&user_id);
            }
        }
    }
}
```

### Example 2: Internal Configuration Update

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE
impl Contract {
    // VULNERABILITY: Anyone can change contract configuration
    pub fn update_config(&mut self, new_fee: u128) {
        self.fee_rate = new_fee;
    }
    
    // VULNERABILITY: Anyone can reset the contract
    pub fn reset(&mut self) {
        self.balances.clear();
        self.users.clear();
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE
impl Contract {
    // SECURE: Only contract can update config (if called internally)
    // Or use owner check for admin functions
    #[private]
    pub fn update_config_internal(&mut self, new_fee: u128) {
        self.fee_rate = new_fee;
    }
    
    // SECURE: Protected reset method
    #[private]
    pub fn reset(&mut self) {
        self.balances.clear();
        self.users.clear();
    }
}
```

### Example 3: Methods with "internal" in Name

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE - Methods with "internal" in name but publicly accessible
impl Contract {
    // CRITICAL VULNERABILITY: Name contains "internal" but is public!
    pub fn internal_stake_from_account(
        &mut self,
        account_id: &AccountId,
        amount: u128,
    ) -> u128 {
        // Anyone can call this! The name "internal" indicates it shouldn't be public
        let mut acc = self.get_account(account_id);
        let shares = self.calculate_shares(amount);
        acc.add_shares(shares);
        self.update_account(account_id, &acc);
        shares
    }
    
    // CRITICAL VULNERABILITY: Another unprotected internal method
    pub fn internal_update_balance(&mut self, account_id: &AccountId, amount: u128) {
        // External users can manipulate balances directly!
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }
    
    // CRITICAL VULNERABILITY: Internal helper exposed
    pub fn internal_calculate_fee(&self, amount: u128) -> u128 {
        // Should not be accessible externally
        amount * self.fee_rate / 10000
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE - Methods with "internal" in name properly protected
impl Contract {
    // SECURE: Internal method using pub(crate) - not part of contract interface
    pub(crate) fn internal_stake_from_account(
        &mut self,
        account_id: &AccountId,
        amount: u128,
    ) -> u128 {
        // Cannot be called externally - compile-time protection
        let mut acc = self.get_account(account_id);
        let shares = self.calculate_shares(amount);
        acc.add_shares(shares);
        self.update_account(account_id, &acc);
        shares
    }
    
    // SECURE: Internal helper using pub(crate)
    pub(crate) fn internal_update_balance(
        &mut self,
        account_id: &AccountId,
        amount: u128,
    ) {
        // Cannot be called externally
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }
    
    // SECURE: Internal helper using pub(crate)
    pub(crate) fn internal_calculate_fee(&self, amount: u128) -> u128 {
        // Cannot be called externally
        amount * self.fee_rate / 10000
    }
    
    // SECURE: Public method that uses internal helpers
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let fee = self.internal_calculate_fee(amount);
        self.internal_update_balance(&env::signer_account_id(), amount - fee);
    }
}
```

### Example 4: Methods with Callback-Indicating Names

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE - Methods with callback-indicating names but unprotected
impl Contract {
    // CRITICAL VULNERABILITY: Name contains "callback" but is public!
    pub fn callback_after_staking(&mut self, result: Result<u128, String>) {
        // Anyone can call this! The name "callback" indicates it's a callback.
        match result {
            Ok(shares) => {
                self.user_shares.insert(&self.pending_user, &shares);
                self.user_balances.insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Attacker can trigger this to manipulate state
                self.rollback_deposit();
            }
        }
    }
    
    // CRITICAL VULNERABILITY: Method with "on_" prefix but unprotected
    pub fn on_transfer_complete(&mut self, success: bool) {
        // Name indicates callback but no protection!
        if success {
            self.commit_transfer();
        } else {
            self.rollback_transfer();
        }
    }
    
    // CRITICAL VULNERABILITY: Method with "after_" prefix but unprotected
    pub fn after_deposit(&mut self, result: Result<(), String>) {
        // Name indicates callback but no protection!
        match result {
            Ok(_) => {
                self.balances.insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Attacker can call this to rollback legitimate deposits
            }
        }
    }
    
    // In another method:
    pub fn stake(&mut self) {
        let amount = env::attached_deposit();
        self.pending_user = env::signer_account_id();
        self.pending_amount = amount;
        
        Promise::new(validator_id.clone())
            .function_call("stake", ...)
            .then(env::current_account_id(), "callback_after_staking", ...);
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE - Methods with callback-indicating names properly protected
impl Contract {
    // SECURE: Callback with #[private] decorator
    #[private]
    pub fn callback_after_staking(&mut self, result: Result<u128, String>) {
        // Only the contract can call this after the cross-contract call
        match result {
            Ok(shares) => {
                self.user_shares.insert(&self.pending_user, &shares);
                self.user_balances.insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Rollback and refund user
                Promise::new(self.pending_user.clone()).transfer(self.pending_amount);
                self.pending_user = AccountId::new_unchecked("".to_string());
                self.pending_amount = 0;
            }
        }
    }
    
    // SECURE: Callback with "on_" prefix protected
    #[private]
    pub fn on_transfer_complete(&mut self, success: bool) {
        // Protected - only contract can call
        if success {
            self.commit_transfer();
        } else {
            self.rollback_transfer();
        }
    }
    
    // SECURE: Callback with "after_" prefix protected
    #[private]
    pub fn after_deposit(&mut self, result: Result<(), String>) {
        // Protected - only contract can call
        match result {
            Ok(_) => {
                self.balances.insert(&self.pending_user, &self.pending_amount);
            }
            Err(_) => {
                // Rollback state
                Promise::new(self.pending_user.clone()).transfer(self.pending_amount);
            }
        }
    }
    
    pub fn stake(&mut self) {
        let amount = env::attached_deposit();
        self.pending_user = env::signer_account_id();
        self.pending_amount = amount;
        
        Promise::new(validator_id.clone())
            .function_call("stake", ...)
            .then(env::current_account_id(), "callback_after_staking", ...);
    }
}
```

### Example 5: Methods with "helper" in Name

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE - Methods with "helper" in name but publicly accessible
impl Contract {
    // CRITICAL VULNERABILITY: Name contains "helper" but is public!
    pub fn sign_helper(&mut self, data: &[u8]) -> Vec<u8> {
        // Anyone can call this! The name "helper" indicates it shouldn't be public
        // Should be pub(crate) fn instead
        self.sign_data(data)
    }
    
    // CRITICAL VULNERABILITY: Another unprotected helper method
    pub fn calculate_helper(&self, amount: u128) -> u128 {
        // External users can call this directly!
        // Should be pub(crate) fn instead
        amount * self.fee_rate / 10000
    }
    
    // CRITICAL VULNERABILITY: Helper method exposed
    pub fn format_helper(&self, value: u128) -> String {
        // Should not be accessible externally
        format!("{}", value)
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE - Methods with "helper" in name properly protected
impl Contract {
    // SECURE: Helper method using pub(crate) - not part of contract interface
    pub(crate) fn sign_helper(&mut self, data: &[u8]) -> Vec<u8> {
        // Cannot be called externally - compile-time protection
        self.sign_data(data)
    }
    
    // SECURE: Helper method using pub(crate)
    pub(crate) fn calculate_helper(&self, amount: u128) -> u128 {
        // Cannot be called externally
        amount * self.fee_rate / 10000
    }
    
    // SECURE: Helper method using pub(crate)
    pub(crate) fn format_helper(&self, value: u128) -> String {
        // Cannot be called externally
        format!("{}", value)
    }
    
    // SECURE: Public method that uses helper methods
    pub fn process_transaction(&mut self, amount: u128) {
        let formatted = self.format_helper(amount);
        let fee = self.calculate_helper(amount);
        // Use helpers internally
    }
}
```

### Example 6: Using `pub(crate)` for Internal Helpers

**Vulnerable Implementation:**
```rust
// ❌ VULNERABLE
impl Contract {
    // VULNERABILITY: Internal helper exposed as public method
    pub fn calculate_fee(&self, amount: u128) -> u128 {
        // External users can call this directly!
        amount * self.fee_rate / 10000
    }
    
    // VULNERABILITY: Internal state update exposed
    pub fn update_user_balance(&mut self, account_id: &AccountId, amount: u128) {
        // Anyone can manipulate balances!
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }
    
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let fee = self.calculate_fee(amount);
        self.update_user_balance(&env::signer_account_id(), amount - fee);
    }
}
```

**Secure Implementation:**
```rust
// ✅ SECURE
impl Contract {
    // SECURE: Internal helper using pub(crate) - not part of contract interface
    pub(crate) fn calculate_fee(&self, amount: u128) -> u128 {
        // Cannot be called externally - compile-time protection
        amount * self.fee_rate / 10000
    }
    
    // SECURE: Internal state update using pub(crate)
    pub(crate) fn update_user_balance(&mut self, account_id: &AccountId, amount: u128) {
        // Cannot be called externally - compile-time protection
        let mut balance = self.balances.get(account_id).unwrap_or(0);
        balance += amount;
        self.balances.insert(account_id, &balance);
    }
    
    // SECURE: Public method that uses internal helpers
    pub fn deposit(&mut self) {
        let amount = env::attached_deposit();
        let fee = self.calculate_fee(amount); // Can call pub(crate) method internally
        self.update_user_balance(&env::signer_account_id(), amount - fee);
    }
}
```

## Key Takeaways for Auditors

1. **ALWAYS flag `pub fn internal_*` without `#[private]`** - Methods containing "internal" in their name (e.g., `internal_*`, `*_internal`) declared as `pub fn` WITHOUT `#[private]` are ALWAYS vulnerabilities. They must be either `pub(crate) fn` (preferred) or `#[private] pub fn` (only if callback). Example: `pub fn internal_stake_from_account(...)` → Should be `pub(crate) fn internal_stake_from_account(...)`.

2. **ALWAYS flag `pub fn *_helper` without `#[private]`** - Methods containing "helper" in their name (e.g., `*_helper`, `helper_*`) declared as `pub fn` WITHOUT `#[private]` are ALWAYS vulnerabilities. They must be either `pub(crate) fn` (preferred) or `#[private] pub fn` (only if callback). Example: `pub fn sign_helper(...)` → Should be `pub(crate) fn sign_helper(...)` or `#[private] pub fn sign_helper(...)` if it's a callback.
3. **Check methods with callback-indicating names** - Methods with names like `callback_*`, `on_*`, `after_*`, `*_callback` are strong indicators they are callbacks and MUST have `#[private]`. Any `pub fn callback_*`, `pub fn on_*`, `pub fn after_*`, or `pub fn *_callback` without `#[private]` is a critical vulnerability.
4. **Use `pub(crate) fn` for internal helpers** - Internal helper methods that don't need to be callbacks should use `pub(crate) fn` (no decorator needed)
5. **Use `#[private] pub fn` for callbacks** - Callback methods must be `pub` to receive cross-contract call results, but protected with `#[private]`
6. **Never use `#[private]` with `pub(crate)`** - `pub(crate)` methods don't need `#[private]` decorator (it's redundant)
7. **Every callback method MUST have `#[private]`** - Callbacks are the most common attack vector
8. **Replace manual checks with `#[private]`** - If you find `assert_eq!(env::predecessor_account_id(), env::current_account_id(), ...)` in code, recommend refactoring to use `#[private]` decorator
9. **Look for state updates before external calls** - This is a reentrancy vulnerability pattern
10. **Verify callback error handling** - Callbacks must rollback state on failure
11. **Check all `.then()` calls** - Every cross-contract call with a callback must have a protected callback method
12. **Verify internal helpers use `pub(crate)`** - Internal helper methods should not be part of the contract interface

## Related Security Concepts

- **Reentrancy Attacks**: Unprotected callbacks enable reentrancy attacks
- **Access Control**: Private methods are a fundamental access control mechanism
- **State Consistency**: Private methods help maintain state consistency
- **Cross-Contract Calls**: Private methods are essential for secure cross-contract interactions

## Summary

Private methods in NEAR contracts are a critical security feature. There are two types:

1. **`pub(crate) fn` methods** - True internal methods that are NOT part of the contract interface. They cannot be called externally and don't require any decorator. Use these for internal helper functions.

2. **`#[private] pub fn` methods** - Methods that are part of the contract interface but protected from external calls. Use these for callbacks that receive results from cross-contract calls.

They ensure that:
- Internal logic cannot be exploited by external actors
- Callbacks from cross-contract calls are secure
- State management operations are protected
- The contract maintains control over its own internal operations

**The Golden Rules**: 
- For internal helper methods: Use `pub(crate) fn` (no decorator needed)
- For callback methods: Use `#[private] pub fn` (must be `pub` to receive callbacks, protected with `#[private]`)
- Always prefer `#[private]` over manual predecessor checks. If you find manual checks in code, recommend refactoring them to use `#[private]` for better maintainability and consistency.

