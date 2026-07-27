# Fuzz Corpus

This directory contains seed inputs for fuzzing. The corpus helps guide fuzzing toward interesting code paths and edge cases.

## Purpose

A corpus provides:
- **Starting points**: Known interesting inputs that exercise different code paths
- **Reproducibility**: Seed inputs that can be reused for consistent testing
- **Coverage**: Examples that hit edge cases and boundary conditions

## Structure

```
corpus/
├── README.md          # This file
└── seeds/             # Seed input files (to be added)
```

## Adding Seeds

Seed files should contain:
- Input parameters for operations
- Expected outcomes (if known)
- Description of why this seed is interesting

Example seed format (JSON):
```json
{
  "description": "Large swap that crosses multiple bins",
  "operation": "swap-x-for-y",
  "parameters": {
    "amount": "1000000000",
    "binId": 0
  },
  "expectedBehavior": "Should traverse bins correctly"
}
```

## Using Seeds

Fuzz tests can load seeds from this directory to initialize their random state or use as starting points for mutation-based fuzzing.

## Best Practices

- Include seeds that hit edge cases (zero amounts, maximum amounts, boundary values)
- Include seeds for different operation types
- Document why each seed is valuable
- Keep seeds minimal but representative

