# Sybil Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates Sybil attack vulnerabilities in NEAR smart contracts:

1. **One-Account-One-Vote**: Attacker can create multiple accounts to control voting
2. **Airdrop Without Protection**: Attacker can claim multiple airdrops with different accounts
3. **Reputation System Without Protection**: Attacker can boost/attack reputation with multiple accounts

## Vulnerabilities

### Vulnerability 1: One-Account-One-Vote (SY-1)

```rust
pub fn vote(&mut self, proposal_id: String, vote: bool) {
    let voter = env::signer_account_id();

    // No checks for multiple accounts from same person
    // Attacker can create 100 accounts and vote 100 times

    if !self.votes.contains_key(&voter) {
        self.votes.insert(&voter, &vote);
        // Update vote counts
    }
}
```

**Problem**: Single person can create multiple NEAR accounts and vote multiple times, controlling governance decisions.

**Fix**: Use token-weighted voting, identity verification, or reputation systems.

### Vulnerability 2: Airdrop Without Sybil Protection (SY-2)

```rust
pub fn claim_airdrop(&mut self) {
    let account = env::signer_account_id();

    // No identity verification - attacker can claim multiple times
    if !self.has_claimed(&account) {
        self.mark_as_claimed(&account);
        // Distribute tokens
    }
}
```

**Problem**: Attacker can create multiple accounts and claim airdrops multiple times.

**Fix**: Require proof of humanity, token holdings, or account age requirements.

### Vulnerability 3: Reputation System Without Protection (SY-3)

```rust
pub fn rate_user(&mut self, target: AccountId, rating: u8) {
    let rater = env::signer_account_id();

    // Attacker can create multiple accounts to boost/attack reputation
    self.add_rating(&target, &rater, rating);
}
```

**Problem**: Attacker can create multiple accounts to manipulate reputation scores.

**Fix**: Require minimum account age, activity requirements, or identity verification.

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/sybil.md` for detailed information about Sybil attacks in NEAR Protocol.

