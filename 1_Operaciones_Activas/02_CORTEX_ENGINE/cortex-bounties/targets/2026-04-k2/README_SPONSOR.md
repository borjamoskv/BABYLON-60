# K2 Lending Protocol

A decentralized borrowing and lending protocol on Stellar's Soroban smart-contract platform.

## What is K2?

K2 allows users to:

- **Supply** assets to earn interest (receive aTokens)
- **Borrow** assets against collateral (variable rates)
- **Liquidate** undercollateralized positions
- **Flash loan** assets for atomic operations

## Architecture

```
contracts/
  kinetic-router/       Main pool contract (entry point for all operations)
  a-token/              Interest-bearing supply position tokens
  debt-token/           Non-transferable borrow position tokens
  price-oracle/         Price feeds with circuit breaker protection
  pool-configurator/    Reserve deployment and configuration
  interest-rate-strategy/  Utilization-based rate curves
  incentives/           Reward distribution
  treasury/             Protocol fee collection
  flash-liquidation-helper/  Flash liquidation validation
  soroswap-swap-adapter/     Soroswap DEX integration
  aquarius-swap-adapter/     Aquarius DEX integration
  redstone-feed-wrapper/     RedStone oracle adapter
  shared/               Shared math, types, and utilities
```

## Quick Start

### Prerequisites

- [Rust](https://rustup.rs/) (stable)
- [Stellar CLI](https://developers.stellar.org/docs/tools/developer-tools/cli/stellar-cli)

### Build

```bash
# Build all contracts (recommended)
./deployment/build.sh

# Or manually
stellar contract build
```

### Test

```bash
# Unit tests
cargo test --package k2-unit-tests

# Integration tests (requires --release)
stellar contract build --release
cargo test --package k2-integration-tests --release
```

### Deploy

```bash
# Automated deployment to testnet
./deployment/deploy.sh

# Skip build if already built
./deployment/deploy.sh --skip-build
```

See [Deployment Guide](docs/12-DEPLOYMENT.md) for full instructions.

## TypeScript Client

```bash
npm install @shapeshifter-technologies/k2-contracts-client
```

```typescript
import { KineticRouterClient } from '@shapeshifter-technologies/k2-contracts-client';

const client = new KineticRouterClient({
  contractId: '<CONTRACT_ID>',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
});

const accountData = await client.get_user_account_data({ user: userAddress });
console.log('Health Factor:', accountData.health_factor);
```

See [Integration Reference](docs/13-INTEGRATION.md) for full API documentation.

## Documentation

Comprehensive protocol documentation is in [`docs/`](docs/00-INDEX.md):

| Doc | Topic |
|-----|-------|
| [01-OVERVIEW](docs/01-OVERVIEW.md) | Protocol introduction and principles |
| [02-ARCHITECTURE](docs/02-ARCHITECTURE.md) | System design and contract interactions |
| [03-CORE-CONCEPTS](docs/03-CORE-CONCEPTS.md) | Reserves, collateral, debt, health factor |
| [04-COMPONENTS](docs/04-COMPONENTS.md) | Detailed contract documentation |
| [05-FLOWS](docs/05-FLOWS.md) | Step-by-step execution flows (supply, borrow, repay, etc.) |
| [06-LIQUIDATION](docs/06-LIQUIDATION.md) | Liquidation mechanics, two-step process, flash liquidation |
| [07-INTEREST-MODEL](docs/07-INTEREST-MODEL.md) | Interest rate curves and APY calculations |
| [08-DEX-INTEGRATION](docs/08-DEX-INTEGRATION.md) | Swap adapters, collateral exchange, slippage protection |
| [08-ORACLE](docs/08-ORACLE.md) | Price feeds, staleness checks, circuit breaker |
| [09-SECURITY](docs/09-SECURITY.md) | Authorization, invariants, emergency controls |
| [10-STORAGE](docs/10-STORAGE.md) | Storage layout and bitmap design |
| [11-ADMIN](docs/11-ADMIN.md) | Administrative operations and governance |
| [12-DEPLOYMENT](docs/12-DEPLOYMENT.md) | Build, deploy, and initialize contracts |
| [13-INTEGRATION](docs/13-INTEGRATION.md) | Developer integration guide and API reference |
| [14-DEVELOPER](docs/14-DEVELOPER.md) | Developer guide and conventions |
| [15-GLOSSARY](docs/15-GLOSSARY.md) | Terms and definitions |

## Key Design Decisions

- **Router pattern**: Single entry point (`kinetic-router`) coordinates all operations
- **Scaled balances**: aToken/debtToken use scaled balances divided by their respective indices
- **U256 intermediate math**: Prevents overflow in `balance * price * oracle_to_wad / decimals`
- **Bitmap user config**: 2 bits per reserve (collateral + borrowing) for up to 64 reserves
- **Two-step liquidation**: Splits validation (~60M CPU) and execution (~60M CPU) to fit Soroban's 100M limit
- **Oracle cascade**: Manual Override > Custom Oracle > Reflector > Fallback

## Security

- Post-liquidation health factor improvement enforced
- Bad debt socialization via deficit tracking
- Oracle circuit breaker (20% max price change)
- Reentrancy protection on all state-changing operations
- Emergency pause/unpause with separated admin roles
