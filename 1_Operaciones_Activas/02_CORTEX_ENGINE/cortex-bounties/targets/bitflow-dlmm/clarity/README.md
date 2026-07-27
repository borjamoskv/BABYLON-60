# DLMM Smart Contract Fuzzing Suite

[![License: ISC](https://img.shields.io/badge/License-ISC-blue.svg)](https://opensource.org/licenses/ISC)

Professional fuzzing and property-based testing suite for DLMM (Dynamic Liquidity Market Maker) smart contracts on Stacks/Clarity.

## Overview

DLMM is an orderbook style AMM for concentrated liquidity. This repository provides comprehensive fuzzing targets, invariant checks, and property-based tests for the DLMM protocol. It validates contract correctness through randomized transaction sequences, invariant verification, and quote engine validation.

## Quick Start

**All commands should be run from the `clarity/` directory:**

```bash
cd .bitflow-dlmm/clarity

# Install dependencies
npm install

# Run all tests (unit tests + fuzz tests)
npm run test:all

# Or run separately:
npm run test:unit  # Run all unit tests
npm run fuzz       # Run all fuzz targets
```

## Getting Started

### Prerequisites

- **Node.js 20+** (required - we recommend using [nvm](https://github.com/nvm-sh/nvm))
- npm or yarn
- Git

**Important**: Node.js 20+ is required. If you're using nvm:
```bash
nvm install 20
nvm use 20
```

**Tool Versions** (installed automatically via npm):
- Clarigen: 4.0.0
- Clarinet SDK: 3.9.2 (includes Clarinet)
- Vitest: ^4.0.7
- TypeScript: 5.9.2

All dependencies are specified in `package.json` and will be installed automatically with `npm install`. You don't need to install these tools separately.

### Installation

1. **Clone the repository** (if you haven't already):
   ```bash
   git clone <repository-url>
   cd .bitflow-dlmm/clarity
   ```

2. **Install dependencies**:
   ```bash
   npm install
   ```

3. **Verify installation**:
   ```bash
   npm run test:unit
   ```

**Note**: All npm commands must be run from the `clarity/` directory where `package.json` is located.

### Running Fuzz Tests

**Quick Start (Single Command)**:
```bash
cd .bitflow-dlmm/clarity  # If not already there
npm run fuzz              # Run all fuzz targets with defaults
npm run fuzz --size 10    # Run with custom size
```

**Individual Fuzz Targets**:
```bash
npm run fuzz:comprehensive    # Main comprehensive fuzz test
npm run fuzz:quote-engine     # Quote engine validation
npm run fuzz:bin-traversal    # Bin traversal tests
npm run fuzz:zero-fee         # Zero-fee exploit test
npm run fuzz:basic            # Basic fuzz test
```

**Customizing Fuzz Runs** (using CLI arguments - recommended):
```bash
# Set number of transactions (default: 100)
npm run fuzz:comprehensive --size 1000

# Set random seed for reproducibility
npm run fuzz:quote-engine --size 100 --seed 12345

# Enable multi-bin mode
npm run fuzz:quote-engine --multi-bin

# Combine options
npm run fuzz:quote-engine --size 1000 --seed 12345 --multi-bin
```

**Alternative: Environment Variables** (still supported):
```bash
# Environment variables work as fallback
FUZZ_SIZE=1000 npm run fuzz:comprehensive
RANDOM_SEED=12345 FUZZ_SIZE=100 npm run fuzz:quote-engine
MULTI_BIN_MODE=true npm run fuzz:quote-engine
```

**Note**: CLI arguments take precedence over environment variables. If both are provided, CLI args are used.

**Using Helper Scripts** (from `clarity/` directory):
```bash
./scripts/fuzz/run-all.sh      # Run all fuzz tests with monitoring
./scripts/fuzz/monitor.sh      # Monitor fuzz test progress
./scripts/fuzz/view-results.sh # View fuzz test results
```

### Running All Tests

**Run everything (unit tests + fuzz tests)**:
```bash
cd .bitflow-dlmm/clarity  # If not already there
npm run test:all         # Runs: clarigen && clarigen docs && test:unit && fuzz
```

### Running Unit Tests

```bash
cd .bitflow-dlmm/clarity  # If not already there
npm run test:unit        # Run all unit tests
npm run test:report      # Run with coverage
npm run test:watch       # Watch mode (auto-rerun on changes)
```

### Configuration Options

Fuzz tests can be configured using CLI arguments (recommended) or environment variables:

| Option | CLI Argument | Environment Variable | Description | Default |
|--------|--------------|---------------------|-------------|---------|
| Size | `--size <number>` | `FUZZ_SIZE` | Number of transactions to run | 100 |
| Seed | `--seed <number>` | `RANDOM_SEED` | Random seed for reproducibility | `Date.now()` |
| Multi-bin | `--multi-bin` | `MULTI_BIN_MODE=true` | Enable multi-bin swap testing | `false` |

**Examples**:
```bash
# CLI arguments (recommended)
npm run fuzz:comprehensive --size 1000 --seed 12345

# Environment variables (alternative)
FUZZ_SIZE=1000 RANDOM_SEED=12345 npm run fuzz:comprehensive

# CLI args override env vars
FUZZ_SIZE=500 npm run fuzz:comprehensive --size 1000  # Uses 1000
```

### Understanding Output

Fuzz tests generate:
- **Console output**: Real-time progress and statistics
- **Log files**: Detailed logs in `logs/` directory
  - `logs/fuzz-test-results/` - Comprehensive fuzz test results
  - `logs/quote-engine-validation/` - Quote engine validation results
  - `logs/bin-traversal/` - Bin traversal logs
- **Summary files**: Markdown summaries with key findings

### Troubleshooting

**Tests fail to run**:
1. **Ensure Node.js version is 20+**: `node --version`
   - If using nvm: `nvm install 20 && nvm use 20`
   - The error "yargs parser supports a minimum Node.js version of 20" means you need Node.js 20+
2. **Reinstall dependencies**: `rm -rf node_modules package-lock.json && npm install`
   - This ensures you have the correct versions of Clarigen, Clarinet SDK, and other tools
3. **Version mismatches**: If you see errors related to Clarigen or Clarinet, ensure you're using the versions specified in `package.json`

**Progress bar doesn't display**: Run tests in a separate terminal (not IDE integrated terminal)

**Out of memory errors**: Increase Node.js memory: `NODE_OPTIONS="--max-old-space-size=4096" npm run fuzz:comprehensive`

## Architecture

```
clarity/
├── fuzz/                    # Fuzzing targets and properties
│   ├── comprehensive.test.ts
│   ├── quote-engine-validation.test.ts
│   ├── bin-traversal.test.ts
│   ├── zero-fee-exploit.test.ts
│   ├── properties/          # Invariant definitions
│   └── harnesses/           # Fuzzing-specific helpers
├── tests/                   # Unit tests
│   ├── core/               # Core contract tests
│   ├── routers/            # Router tests
│   └── helpers/            # Shared test utilities
├── contracts/              # Smart contracts
└── scripts/                # Utility scripts
```

## Fuzz Targets

- **comprehensive**: Main fuzz test with randomized operations (swaps, liquidity, migrations)
- **quote-engine-validation**: Validates swap calculations against production quote engine
- **bin-traversal**: Tests bin traversal and edge cases
- **zero-fee-exploit**: Tests for rounding exploits in zero-fee scenarios
- **basic**: Basic fuzzing with simple operations

## Invariants

Key invariants verified:
- LP supply remains unchanged during swaps
- Balance changes match expected amounts
- Protocol fees accumulate correctly
- No negative balances
- Liquidity operations maintain pool consistency

See [fuzz/properties/README.md](./fuzz/properties/README.md) for detailed invariant documentation.

## Bugs Found

| Severity | Description | Status |
|----------|-------------|--------|
| - | - | - |

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for guidelines on adding new fuzz targets and invariants.

## Documentation

- [CONTRIBUTING.md](./CONTRIBUTING.md) - Contribution guidelines
- [../docs/architecture.md](../docs/architecture.md) - System architecture
- [../docs/invariants.md](../docs/invariants.md) - Detailed invariant explanations
- [../docs/fuzzing-guide.md](../docs/fuzzing-guide.md) - Fuzzing methodology
- [../docs/README.md](../docs/README.md) - Contract API documentation

## License

ISC
