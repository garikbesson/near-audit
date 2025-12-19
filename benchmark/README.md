# Security Audit Tool Benchmark

This directory contains tools and datasets for benchmarking the security audit tool's effectiveness in detecting vulnerabilities in NEAR smart contracts.

## Structure

```
benchmark/
├── README.md              # This file
├── run_benchmark.py       # Script to run benchmarks on all examples
└── dataset/               # Test examples with known vulnerabilities
    ├── README.md          # Dataset documentation
    ├── metadata.json      # Expected vulnerabilities for each example
    ├── private_methods_vulnerable.rs
    ├── reentrancy_vulnerable.rs
    ├── callbacks_vulnerable.rs
    ├── one_yocto_vulnerable.rs
    ├── random_vulnerable.rs
    ├── frontrunning_vulnerable.rs
    ├── sybil_vulnerable.rs
    └── storage_vulnerable.rs
```

## Quick Start

### Run All Benchmarks

```bash
python benchmark/run_benchmark.py
```

This will:
1. Run the audit tool on each example in `dataset/`
2. Compare detected vulnerabilities with expected ones
3. Calculate precision, recall, and F1 scores
4. Save results to `benchmark_results.json`

### Run Single Example

To test a specific example manually:

```bash
# Test private methods detection
python -m auditor.audit graph benchmark/dataset/private_methods_vulnerable.rs --concept-name private_methods

# Test reentrancy detection
python -m auditor.audit graph benchmark/dataset/reentrancy_vulnerable.rs --concept-name reentrancy
```

## Dataset

The `dataset/` directory contains intentionally vulnerable smart contracts covering 8 security concepts:

1. **Private Methods** - Unprotected internal methods and callbacks
2. **Reentrancy** - State updates before external calls
3. **Callbacks** - Unprotected callbacks and missing refunds
4. **1 YoctoNEAR** - Missing user verification for asset transfers
5. **Random** - Vulnerable random number generation
6. **Frontrunning** - First-come-first-served patterns
7. **Sybil** - Missing identity verification
8. **Storage** - Storage cost attacks

Each example file contains:
- Complete Rust smart contract code
- Multiple intentional vulnerabilities
- Comments marking vulnerabilities

See `dataset/README.md` for detailed information about each example.

## Metrics

The benchmark calculates:

- **Precision**: Percentage of detected vulnerabilities that are actually vulnerabilities
- **Recall**: Percentage of expected vulnerabilities that were detected
- **F1 Score**: Harmonic mean of precision and recall
- **True Positives**: Correctly detected vulnerabilities
- **False Positives**: Incorrectly flagged as vulnerabilities
- **False Negatives**: Missed vulnerabilities

## Results

Results are saved to `benchmark_results.json` with:
- Per-example results
- Comparison with expected vulnerabilities
- Overall statistics

## Improving Detection

Use benchmark results to:

1. **Identify false negatives** - Add detection rules for missed vulnerabilities
2. **Reduce false positives** - Refine rules that flag safe code
3. **Measure improvements** - Compare results across tool versions
4. **Focus efforts** - Identify which security concepts need better detection

## Notes

- These examples are intentionally vulnerable - **DO NOT deploy to mainnet**
- Some examples may have multiple vulnerabilities
- Code is simplified for clarity
- False positives are acceptable if they indicate potential issues worth reviewing

