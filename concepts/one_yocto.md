# Verifying User Identity with 1 YoctoNEAR

## Overview

In NEAR Protocol, verifying that a transaction actually comes from the user (not from a website with a Function Call key) is critical for security, especially when transferring valuable assets. Requiring 1 yoctoNEAR (the smallest unit of NEAR) is a simple and effective way to ensure user authorization.

**Key Concepts**: access keys, function call keys, full access keys, user verification, transaction authorization, identity verification, asset transfer security

## NEAR Access Key System

NEAR uses an access key system to simplify account management. There are two main types of keys:

### 1. Full Access Keys
- **Full control** over an account
- Can perform all actions (transfers, deployments, etc.)
- Can attach NEAR as deposit
- **Stored only in user's wallet** - never shared with websites

### 2. Function Call Keys
- **Limited permissions** - can only call specified smart contract methods
- **Cannot attach NEAR** as deposit
- Created when users sign in to websites
- **Stored in the website** - website can use them automatically

**Related Terms**: access keys, key management, wallet security, key permissions, account security

## The Security Problem

### How Website Sign-In Works

When a user signs in to a website to interact with your contract:

1. A `Function Call` key is created
2. The key is stored in the website (browser storage)
3. The website can use this key to call authorized methods **automatically**
4. No user interaction required for each transaction

### The Risk

For most operations, this is convenient and secure. However, for **valuable asset transfers** (NFTs, Fungible Tokens, large amounts of NEAR), this creates a security risk:

- **Website has the key** - can initiate transfers without user confirmation
- **No user awareness** - user might not know a transfer is happening
- **Malicious websites** - compromised or malicious sites could drain assets
- **User can't verify** - no way to ensure the user actually authorized the transfer

**Critical Scenarios**:
- Transferring NFTs
- Transferring Fungible Tokens (FTs)
- Large NEAR transfers
- Any operation involving valuable assets

**Related Terms**: asset security, transfer authorization, website security, key compromise, unauthorized transfers

## Solution: Require 1 YoctoNEAR

### How It Works

Require users to attach **1 yoctoNEAR** (1 yⓃ) to sensitive operations:

```rust
pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
    // Require 1 yoctoNEAR to ensure user authorization
    assert!(env::attached_deposit() >= 1, "Must attach at least 1 yoctoNEAR");
    
    // Proceed with transfer
}
```

### Why This Works

1. **Function Call keys cannot attach NEAR** - they can only call methods without deposits
2. **Only Full Access keys can attach NEAR** - these are stored in the user's wallet
3. **Wallet requires user confirmation** - when NEAR is attached, wallet prompts user
4. **User must approve** - transaction cannot proceed without explicit user approval

**Result**: If a transaction includes 1 yoctoNEAR, you can trust it was explicitly authorized by the user through their wallet.

**Related Terms**: yoctoNEAR, attached deposit, wallet confirmation, user approval, transaction verification

## Implementation Example

### NFT Transfer with Verification

```rust
pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
    // Verify user authorization
    assert!(
        env::attached_deposit() >= 1,
        "Must attach 1 yoctoNEAR to verify user authorization"
    );
    
    // Verify caller owns the NFT
    let owner = self.get_token_owner(&token_id);
    assert_eq!(env::predecessor_account_id(), owner, "Not the owner");
    
    // Perform transfer
    self.transfer_token(token_id, receiver_id);
}
```

### Fungible Token Transfer

```rust
pub fn transfer_ft(&mut self, amount: U128, receiver_id: AccountId) {
    // Require 1 yoctoNEAR for user verification
    assert!(env::attached_deposit() >= 1, "User verification required");
    
    // Transfer tokens
    self.internal_transfer(env::predecessor_account_id(), receiver_id, amount.0);
}
```

## When to Use This Pattern

### Use 1 YoctoNEAR Requirement For:

- ✅ NFT transfers
- ✅ Fungible Token transfers
- ✅ Large NEAR transfers
- ✅ Account ownership changes
- ✅ Permission modifications
- ✅ Any operation involving valuable assets

### Not Necessary For:

- ❌ Read-only operations (view methods)
- ❌ Low-value operations
- ❌ Operations that don't transfer assets
- ❌ Public data queries

## Best Practices

1. **Always require 1 yoctoNEAR** for asset transfers
2. **Document the requirement** - tell users why it's needed
3. **Return the yoctoNEAR** if you don't need it (optional, but user-friendly)
4. **Use consistent pattern** - apply to all sensitive operations
5. **Test with Function Call keys** - ensure they fail without deposit

## Alternative: Return the YoctoNEAR

You can return the 1 yoctoNEAR to the user after verification:

```rust
pub fn transfer_nft(&mut self, token_id: String, receiver_id: AccountId) {
    assert!(env::attached_deposit() >= 1, "Verification required");
    
    // Perform transfer
    self.transfer_token(token_id, receiver_id);
    
    // Return the yoctoNEAR (optional)
    Promise::new(env::predecessor_account_id()).transfer(1);
}
```

## Common Questions This Document Answers

- How do I verify that a user actually authorized a transaction?
- What is the difference between Full Access and Function Call keys?
- Why should I require 1 yoctoNEAR for asset transfers?
- How do Function Call keys work in NEAR?
- Can websites transfer my assets without permission?
- How do I secure NFT transfers in NEAR?
- What is a yoctoNEAR and why use it for verification?