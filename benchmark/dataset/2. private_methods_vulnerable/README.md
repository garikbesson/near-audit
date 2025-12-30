# Private Methods Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates common private methods security vulnerabilities in NEAR smart contracts:

1. **Unprotected Internal Methods**: Methods with "internal" in name but publicly accessible
2. **Unprotected Helper Methods**: Methods with "helper" in name but publicly accessible
3. **Unprotected Callbacks**: Callback methods without `#[private]` decorator
4. **Manual Predecessor Checks**: Using manual checks instead of `#[private]` decorator

## Vulnerabilities

### Vulnerability 1: Unprotected Internal Method (PM-1)

```rust
pub fn internal_update_balance(&mut self, account_id: &AccountId, amount: u128) {
    // Anyone can call this! Should be pub(crate) fn
}
```

**Fix**: Use `pub(crate) fn` for internal helpers:
```rust
pub(crate) fn internal_update_balance(&mut self, account_id: &AccountId, amount: u128) {
    // Cannot be called externally
}
```

### Vulnerability 2: Unprotected Helper Method (PM-2)

```rust
pub fn calculate_helper(&self, amount: u128) -> u128 {
    // Anyone can call this! Should be pub(crate) fn
}
```

**Fix**: Use `pub(crate) fn`:
```rust
pub(crate) fn calculate_helper(&self, amount: u128) -> u128 {
    // Cannot be called externally
}
```

### Vulnerability 3: Unprotected Callback (PM-3, PM-4)

```rust
pub fn callback_after_staking(&mut self, result: Result<u128, String>) {
    // Attacker can call this directly!
}
```

**Fix**: Add `#[private]` decorator:
```rust
#[private]
pub fn callback_after_staking(&mut self, result: Result<u128, String>) {
    // Only contract can call
}
```

### Vulnerability 4: Manual Predecessor Check (PM-5)

```rust
pub fn internal_process(&mut self) {
    assert_eq!(
        env::predecessor_account_id(),
        env::current_account_id(),
        "Only contract can call this method"
    );
}
```

**Fix**: Use `#[private]` decorator:
```rust
#[private]
pub fn internal_process(&mut self) {
    // Automatically protected
}
```

## Safe Code

Methods in undecorated `impl Contract {}` blocks are NOT part of the public interface and should NOT be flagged:

```rust
// ✅ SAFE - not in #[near] impl block
impl Contract {
    pub fn internal_helper(&self) -> u128 {
        // DO NOT FLAG - not accessible externally
    }
}
```

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/private_methods.md` for detailed information about private methods security in NEAR Protocol.

