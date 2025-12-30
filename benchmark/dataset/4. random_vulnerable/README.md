# Random Vulnerable Contract

⚠️ **WARNING**: This contract contains intentional security vulnerabilities. **DO NOT deploy to mainnet.**

## Purpose

This contract demonstrates random number generation vulnerabilities in NEAR smart contracts:

1. **Gaming the Input**: User input and random seed generated in same block - validator can predict and win
2. **Refusing to Mine**: Validator can skip blocks where they would lose

## Vulnerabilities

### Vulnerability 1: Gaming the Input (RN-1)

```rust
pub fn guess_number(&mut self, guess: u8) {
    let user = env::signer_account_id();
    self.bets.insert(&user, &guess.to_string());

    // Generate random number in SAME block - validator knows it!
    let random_seed = env::random_seed();
    let random_number = (random_seed[0] % 100) as u8;

    // Validator can see user's guess and create winning transaction
    if guess == random_number {
        // Reward user
    }
}
```

**Problem**: Validator knows the random seed before the block is mined, so they can:
1. See user's guess in transaction pool
2. Calculate the winning number
3. Create their own transaction with the winning number
4. Include their transaction in the block
5. Win every time

**Fix**: Use commit-reveal scheme or separate bet and resolve into different blocks.

### Vulnerability 2: Refusing to Mine (RN-2)

```rust
pub fn bet_heads_or_tails(&mut self, choice: String) {
    // User makes bet
}

pub fn resolve_bet(&mut self) {
    // Validator knows random seed and can skip this if they'd lose
    let random_seed = env::random_seed();
    // ...
}
```

**Problem**: Validator can:
1. Create a bet transaction
2. When it's their turn to validate:
   - Check what random seed will be generated
   - If their bet would win, include the "resolve" transaction
   - If their bet would lose, skip the "resolve" transaction
3. Improves their win rate significantly

**Fix**: Use commit-reveal schemes or external oracles.

## How to Build

```bash
cargo near build
```

## How to Test

```bash
cargo test
```

## Related Security Concepts

See `concepts/random.md` for detailed information about random number generation security in NEAR Protocol.

