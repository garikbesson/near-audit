# Frontrunning Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates frontrunning attack vulnerabilities in NEAR smart contracts:

1. **First-Come-First-Served Pattern**: Validator can see solutions in transaction pool and frontrun
2. **Auction Without Commit-Reveal**: Validator can see all bids and place higher bid first

## Vulnerabilities

### Vulnerability 1: First-Come-First-Served (FR-1)

```rust
pub fn solve_puzzle(&mut self, puzzle_id: String, solution: String) {
    let correct_answer = self.get_puzzle_answer(&puzzle_id);

    if solution == correct_answer {
        // First solver gets reward - validator can frontrun!
        if !self.solved_puzzles.contains_key(&puzzle_id) {
            // Reward solver
        }
    }
}
```

**Problem**: Validator can:
1. See user's solution in transaction pool
2. Extract the correct answer
3. Create their own transaction with the same answer
4. Include their transaction before user's transaction
5. Claim the reward

**Fix**: Use commit-reveal scheme:
1. Users commit to their answer (hash of answer + secret)
2. After commit period, users reveal answer and secret
3. Contract verifies hash matches revealed answer
4. Winner determined after all reveals

### Vulnerability 2: Auction Without Commit-Reveal (FR-2)

```rust
pub fn place_bid(&mut self, item_id: String, bid_amount: u128) {
    // Validator can see all bids in transaction pool
    // Can place higher bid before user's transaction executes
    if bid_amount > current_bid {
        self.set_bid(&item_id, &bidder, bid_amount);
    }
}
```

**Problem**: Validator can see all bids and place a higher bid before user's transaction executes.

**Fix**: Use commit-reveal scheme for bids.

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/frontrunning.md` for detailed information about frontrunning attacks in NEAR Protocol.

