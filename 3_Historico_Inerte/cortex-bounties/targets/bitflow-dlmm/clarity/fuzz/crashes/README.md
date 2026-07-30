# Crash Examples

This directory contains examples of crashes, bugs, or invariant violations found during fuzzing.

## Purpose

Crash examples serve as:
- **Reproducible test cases**: Exact inputs that trigger bugs
- **Regression tests**: Prevent previously found bugs from reoccurring
- **Documentation**: Record of issues found and fixed

## Structure

```
crashes/
├── README.md          # This file
└── [timestamp]-[description].json  # Crash examples
```

## Crash File Format

Each crash file should contain:
- **Input**: The exact inputs that triggered the crash
- **Expected behavior**: What should have happened
- **Actual behavior**: What actually happened
- **Reproduction steps**: How to reproduce the issue
- **Severity**: Critical, high, medium, low
- **Status**: Fixed, open, duplicate

Example format:
```json
{
  "timestamp": "2025-01-01T00:00:00Z",
  "description": "Negative balance after swap",
  "severity": "critical",
  "status": "fixed",
  "inputs": {
    "operation": "swap-x-for-y",
    "amount": "1000000",
    "binId": 0
  },
  "expected": "Bin balance should remain non-negative",
  "actual": "Bin Y balance became negative",
  "reproduction": "Run fuzz test with seed 12345, transaction 42",
  "fix": "Fixed in commit abc123"
}
```

## Adding Crash Examples

When a fuzz test finds a bug:

1. **Capture the exact inputs** that triggered it
2. **Document the expected vs actual behavior**
3. **Save to a crash file** with descriptive name
4. **Update status** as the bug is fixed

## Reproducing Crashes

To reproduce a crash:

```bash
# Use the seed and transaction number from the crash file
RANDOM_SEED=12345 FUZZ_SIZE=100 npm run fuzz:comprehensive

# Or use the exact inputs from the crash file in a unit test
```

## Best Practices

- **Keep crash files**: Even after bugs are fixed, they serve as regression tests
- **Be specific**: Include exact inputs, not approximations
- **Document fixes**: Link to commits or PRs that fixed the issue
- **Categorize**: Use severity levels to prioritize fixes

