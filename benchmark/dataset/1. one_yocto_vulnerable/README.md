# One YoctoNEAR Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates missing 1 yoctoNEAR verification vulnerabilities in NEAR smart contracts:

1. **NFT Transfer Without Verification**: Function Call keys can transfer NFTs without user approval
2. **Fungible Token Transfer Without Verification**: Missing user verification for FT transfers
3. **Large NEAR Transfer Without Verification**: Missing user verification for large transfers

## Vulnerabilities

### Vulnerability 1: NFT Transfer Without 1 YoctoNEAR Check (OY-1)

```rust
pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
    let owner = self.get_token_owner(&token_id);
    assert_eq!(env::predecessor_account_id(), owner, "Not the owner");

    // Missing: assert!(env::attached_deposit() >= 1, "Must attach 1 yoctoNEAR");

    self.transfer_token(token_id, receiver_id);
}
```

**Problem**: Website with Function Call key can transfer NFTs without user approval.

**Fix**: Require 1 yoctoNEAR:
```rust
pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
    assert!(env::attached_deposit() >= 1, "Must attach 1 yoctoNEAR");
    
    let owner = self.get_token_owner(&token_id);
    assert_eq!(env::predecessor_account_id(), owner, "Not the owner");
    
    self.transfer_token(token_id, receiver_id);
}
```

### Vulnerability 2: Fungible Token Transfer Without Verification (OY-2)

```rust
pub fn transfer_ft(&mut self, amount: u128, receiver_id: AccountId) {
    // Missing: assert!(env::attached_deposit() >= 1, "User verification required");
    // ...
}
```

**Fix**: Add 1 yoctoNEAR check.

### Vulnerability 3: Large NEAR Transfer Without Verification (OY-3)

```rust
pub fn transfer_large_amount(&mut self, receiver_id: AccountId, amount: u128) {
    // Missing: assert!(env::attached_deposit() >= 1, "User verification required");
    // ...
}
```

**Fix**: Add 1 yoctoNEAR check.

## Why 1 YoctoNEAR Works

- Function Call keys **cannot attach NEAR** - they can only call methods without deposits
- Only Full Access keys can attach NEAR - these are stored in the user's wallet
- Wallet requires user confirmation when NEAR is attached
- Result: If a transaction includes 1 yoctoNEAR, it was explicitly authorized by the user

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/one_yocto.md` for detailed information about 1 yoctoNEAR verification in NEAR Protocol.

