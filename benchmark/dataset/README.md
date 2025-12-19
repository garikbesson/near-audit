# Security Dataset for Benchmarking

This directory contains vulnerable code examples for testing and measuring the effectiveness of security vulnerability detection in NEAR smart contracts.

## Structure

Each file contains a complete Rust smart contract with intentional security vulnerabilities. The files are named as `{concept_name}_vulnerable.rs` where `concept_name` corresponds to a security concept from the `concepts/` directory.

## Files

### 1. `private_methods_vulnerable.rs`
**Concept**: Private methods security

**Expected Vulnerabilities**:
- PM-1: `pub fn internal_update_balance` - method with 'internal' in name but publicly accessible
- PM-2: `pub fn calculate_helper` - method with 'helper' in name but publicly accessible
- PM-3: `pub fn callback_after_staking` - callback method without `#[private]`
- PM-3: `pub fn on_transfer_complete` - method with 'on_' prefix but unprotected
- PM-3: `pub fn after_deposit` - method with 'after_' prefix but unprotected
- PM-4: Callback `callback_after_staking` called via `.then()` but not protected
- PM-5: `pub fn internal_process` - uses manual predecessor check instead of `#[private]`

**Should NOT flag**:
- Methods in undecorated `impl Contract {}` block (`internal_helper`, `helper_calculate`)

### 2. `reentrancy_vulnerable.rs`
**Concept**: Reentrancy attacks

**Expected Vulnerabilities**:
- State updated before external call in `deposit_and_stake`
- `withdraw` can be called between `deposit_and_stake` and its callback
- Balance updated immediately, allowing reentrancy attack

### 3. `callbacks_vulnerable.rs`
**Concept**: Callback security

**Expected Vulnerabilities**:
- `callback_after_stake` - callback without `#[private]` decorator
- `callback_without_refund` - callback doesn't refund user if external call fails

### 4. `one_yocto_vulnerable.rs`
**Concept**: 1 yoctoNEAR verification

**Expected Vulnerabilities**:
- `transfer_nft` - missing 1 yoctoNEAR check (Function Call keys can transfer)
- `transfer_ft` - missing 1 yoctoNEAR check
- `transfer_large_amount` - missing 1 yoctoNEAR check

### 5. `random_vulnerable.rs`
**Concept**: Random number generation security

**Expected Vulnerabilities**:
- `guess_number` - "gaming the input" attack (user input and random seed in same block)
- `bet_heads_or_tails` + `resolve_bet` - "refusing to mine" attack (validator can skip losing blocks)

### 6. `frontrunning_vulnerable.rs`
**Concept**: Frontrunning attacks

**Expected Vulnerabilities**:
- `solve_puzzle` - first-come-first-served pattern vulnerable to frontrunning
- `place_bid` - auction without commit-reveal scheme, validator can see bids

### 7. `sybil_vulnerable.rs`
**Concept**: Sybil attacks

**Expected Vulnerabilities**:
- `vote` - one-account-one-vote without identity verification
- `claim_airdrop` - airdrop without Sybil protection
- `rate_user` - reputation system without Sybil protection

### 8. `storage_vulnerable.rs`
**Concept**: Storage cost attacks

**Expected Vulnerabilities**:
- `add_message` - storage cost not covered by user (contract pays)
- `store_user_data` - user data storage without deposit requirement
- `add_item` - collection growth attack (no storage cost check)

## Usage

These files can be used to:

1. **Test the audit tool**: Run the audit tool on each file and verify it detects the expected vulnerabilities
2. **Measure effectiveness**: Calculate precision, recall, and F1 scores for each security concept
3. **Improve detection**: Use false positives/negatives to refine detection rules
4. **Benchmark performance**: Compare different versions of the audit tool

## Running Tests

To test the audit tool on these examples:

```bash
# Test private methods detection
python -m auditor.audit graph /path/to/benchmark/dataset/private_methods_vulnerable.rs --concept-name private_methods

# Test reentrancy detection
python -m auditor.audit graph /path/to/benchmark/dataset/reentrancy_vulnerable.rs --concept-name reentrancy

# ... and so on for each concept
```

## Expected Results

Each test should:
1. Successfully index the project
2. Build a method call graph
3. Identify relevant methods for the security concept
4. Detect the expected vulnerabilities in the audit step

## Notes

- These are intentionally vulnerable examples - DO NOT deploy to mainnet
- Some examples may have multiple vulnerabilities
- The code is simplified for clarity - real contracts may have more complex patterns
- False positives are acceptable if they indicate potential issues that should be reviewed

