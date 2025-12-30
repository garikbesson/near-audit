# Callbacks Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates common callback security vulnerabilities in NEAR smart contracts:

1. **Unprotected Callback**: `callback_after_stake` is missing the `#[private]` decorator, allowing attackers to call it directly and manipulate state.

## Vulnerabilities

### Vulnerability 1: Unprotected Callback

```rust
// ❌ VULNERABILITY: Callback without #[private] - attacker can call directly
pub fn callback_after_stake(&mut self, result: Result<(), String>) {
    // Attacker can call this and manipulate state!
    match result {
        Ok(_) => {
            self.balances.insert(&self.pending_user, &self.pending_amount);
        }
        Err(_) => {
            // Attacker can trigger this to rollback legitimate operations
        }
    }
}
```

**Fix**: Add `#[private]` decorator:
```rust
#[private]
pub fn callback_after_stake(&mut self, result: Result<(), String>) {
    // ...
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

See `concepts/callbacks.md` for detailed information about callback security in NEAR Protocol.

