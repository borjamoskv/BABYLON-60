## Overview

DLMM is an orderbook style AMM for concentrated liquidity. This repository provides comprehensive fuzzing targets, invariant checks, and property-based tests to validate contract correctness through randomized transaction sequences, invariant verification, and quote engine validation.

## Quick Start

```bash
# Navigate to the clarity directory
cd clarity

# Install dependencies
npm install

# Run all tests (unit tests + fuzz tests)
npm run test:all

# Or run separately:
npm run test:unit  # Run all unit tests
npm run fuzz       # Run all fuzz targets
```

**All commands must be run from the `clarity/` directory.**

## Project Structure

```
.bitflow-dlmm/
├── clarity/              # Main testing and fuzzing code
│   ├── fuzz/            # Fuzz targets and properties
│   ├── tests/           # Unit tests
│   ├── contracts/       # Smart contracts
│   └── scripts/         # Utility scripts
├── docs/                # Documentation
│   ├── architecture.md  # System architecture
│   ├── invariants.md    # Invariant explanations
│   ├── fuzzing-guide.md # Fuzzing methodology
│   └── [contract-*.md]  # Auto-generated contract API docs (e.g., dlmm-core-v-1-1.md)
└── external-test-context/  # External test contexts
```

## Documentation

- **[clarity/README.md](clarity/README.md)** - Detailed testing and fuzzing documentation, getting started guide, and configuration options
- **[docs/](docs/)** - Contract API documentation (auto-generated) and project documentation
  - [docs/architecture.md](docs/architecture.md) - System architecture
  - [docs/invariants.md](docs/invariants.md) - Detailed invariant explanations
  - [docs/fuzzing-guide.md](docs/fuzzing-guide.md) - Fuzzing methodology

## Contributing

See [clarity/CONTRIBUTING.md](clarity/CONTRIBUTING.md) for guidelines on adding new fuzz targets and invariants.



