# Storage Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates storage cost attack vulnerabilities in NEAR smart contracts:

1. **Storage Cost Not Covered by User**: Contract pays for storage, attacker can drain balance
2. **User Data Storage Without Deposit**: Missing deposit requirement allows storage drain
3. **Collection Growth Attack**: No storage cost check allows adding unlimited items

## Vulnerabilities

### Vulnerability 1: Storage Cost Not Covered (ST-1)

```rust
pub fn add_message(&mut self, message: String) {
    let user = env::signer_account_id();

    // Missing: assert!(env::attached_deposit() >= storage_cost, "Insufficient deposit");
    // Contract pays storage cost - attacker can spam and drain balance

    let mut user_messages = self.messages.get(&user).unwrap_or(Vec::new());
    user_messages.push(message);
    self.messages.insert(&user, &user_messages);
}
```

**Problem**: 
- Attacker sends thousands of small messages
- Each message costs attacker minimal gas fees
- Each message forces contract to lock NEAR for storage
- Contract balance is drained/locked
- Contract becomes unusable

**Fix**: Require users to cover storage costs:
```rust
pub fn add_message(&mut self, message: String) {
    let storage_cost = self.calculate_storage_cost(&message);
    assert!(env::attached_deposit() >= storage_cost, "Insufficient deposit for storage");
    
    let user = env::signer_account_id();
    let mut user_messages = self.messages.get(&user).unwrap_or(Vec::new());
    user_messages.push(message);
    self.messages.insert(&user, &user_messages);
}
```

### Vulnerability 2: User Data Storage Without Deposit (ST-2)

```rust
pub fn store_user_data(&mut self, data: String) {
    // Missing: Check for attached deposit to cover storage
    self.user_data.insert(&user, &data);
}
```

**Fix**: Calculate and require storage cost deposit.

### Vulnerability 3: Collection Growth Attack (ST-3)

```rust
pub fn add_item(&mut self, item: String) {
    // Missing: Storage cost check
    // Attacker can add thousands of items, draining contract balance
    let mut items = self.messages.get(&user).unwrap_or(Vec::new());
    items.push(item);
    self.messages.insert(&user, &items);
}
```

**Fix**: Require storage cost deposit for each item.

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/storage.md` for detailed information about storage cost attacks in NEAR Protocol.

