# Benchmark Scripts

This directory contains utility scripts for working with the benchmark dataset.

## Scripts

### `build_all_projects.py`

Builds all vulnerable contract projects in the dataset.

**Usage:**
```bash
python benchmark/scripts/build_all_projects.py
```

**What it does:**
1. Finds all project directories ending with `_vulnerable` in `benchmark/dataset/`
2. Attempts to compile each project using `cargo near build non-reproducible-wasm`
3. Stops on first compilation error and displays the error
4. Reports success if all projects compile

**Requirements:**
- `cargo-near` must be installed and available in PATH
- Each project must have a valid `Cargo.toml` file

**Example output:**
```
================================================================================
Building All Vulnerable Contract Projects
================================================================================

Found 8 projects:
  - callbacks_vulnerable
  - frontrunning_vulnerable
  - one_yocto_vulnerable
  - private_methods_vulnerable
  - random_vulnerable
  - reentrancy_vulnerable
  - storage_vulnerable
  - sybil_vulnerable

[1/8] Processing callbacks_vulnerable...

================================================================================
Building: callbacks_vulnerable
Path: /path/to/benchmark/dataset/callbacks_vulnerable
================================================================================

✅ BUILD SUCCESS: callbacks_vulnerable
...
```

