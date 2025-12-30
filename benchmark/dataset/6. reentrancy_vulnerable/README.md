# Reentrancy Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates reentrancy attack vulnerabilities in NEAR smart contracts:

1. **State Updated Before External Call**: Balance is updated before cross-contract call completes
2. **Reentrancy Window**: `withdraw` can be called between `deposit_and_stake` and its callback

## Vulnerabilities

### Vulnerability 1: State Updated Before External Call (RE-1)

```rust
pub fn deposit_and_stake(&mut self) {
    let amount = env::attached_deposit();
    let user = env::signer_account_id();

    // VULNERABILITY: Updates balance BEFORE external call completes
    let mut balance = self.balances.get(&user).unwrap_or(0);
    balance += amount;
    self.balances.insert(&user, &balance);

    // External call - attacker can call withdraw() before callback executes
    Promise::new(validator_id)
        .function_call("stake", ...)
        .then(...);
}
```

**Attack Scenario**:
1. Attacker calls `deposit_and_stake` with 10 NEAR
2. Contract adds 10 NEAR to attacker's balance
3. Contract initiates cross-contract call
4. **Before callback executes**, attacker calls `withdraw(10)`
5. Attacker successfully withdraws 10 NEAR
6. If staking fails, callback tries to rollback, but attacker already withdrew

**Fix**: Delay state updates until callback confirms success:
```rust
pub fn deposit_and_stake(&mut self) {
    let amount = env::attached_deposit();
    let user = env::signer_account_id();

    // Store in temporary state, don't update balance yet
    self.pending_user = user;
    self.pending_amount = amount;

    Promise::new(validator_id)
        .function_call("stake", ...)
        .then(...);
}

#[private]
pub fn callback_after_stake(&mut self, result: Result<(), String>) {
    match result {
        Ok(_) => {
            // Only update balance if staking succeeded
            let mut balance = self.balances.get(&self.pending_user).unwrap_or(0);
            balance += self.pending_amount;
            self.balances.insert(&self.pending_user, &balance);
        }
        Err(_) => {
            // Refund user
            Promise::new(self.pending_user.clone()).transfer(self.pending_amount);
        }
    }
}
```

### Vulnerability 2: Reentrancy Window (RE-2)

The `withdraw` method can be called between `deposit_and_stake` and its callback, allowing attackers to withdraw funds before the external operation completes.

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/reentrancy.md` for detailed information about reentrancy attacks in NEAR Protocol.

