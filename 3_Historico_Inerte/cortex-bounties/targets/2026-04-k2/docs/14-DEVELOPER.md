# K2 Lending Protocol - Developer Guide

Complete reference for development, testing, and troubleshooting of the K2 lending protocol.

---

## 1. Development Setup

### Environment Requirements

- **Rust**: 1.70+ with Soroban target
- **Soroban CLI**: Latest stable version
- **Node.js**: 18+ (for integration tests)
- **Docker**: For local network simulation
- **Git**: For version control

### Initial Setup

```bash
# Clone the repository
git clone <repo-url>
cd k2-contracts

# Install Rust Soroban target
rustup target add wasm32-unknown-unknown

# Verify Soroban installation
soroban --version
```

### Workspace Structure

```
k2-contracts/
- contracts/                    # Smart contracts
   kinetic-router/          # Main lending pool router
   a-token/                 # Collateral token (aToken)
   debt-token/              # Debt token (dToken)
   price-oracle/            # Price oracle
   shared/                  # Shared types, constants, utils
   interest-rate-strategy/  # Interest rate calculations
   incentives/              # Reward distribution
   pool-configurator/       # Reserve configuration manager
   redstone-adapter/        # Redstone oracle adapter
   flash-liquidation-helper/ # Flash liquidation validation
   soroswap-swap-adapter/   # Soroswap DEX adapter
   aquarius-swap-adapter/   # Aquarius DEX adapter
   liquidation-engine/      # Liquidation calculations
   treasury/                # Protocol fee collection
   token/                   # SEP-41 token implementation
- tests/
   unit-tests/              # Rust unit tests
- integration-tests/           # TypeScript integration tests
- docs/                        # Documentation
```

---

## 2. Local Testing

### Running Docker Network

Local testing requires a Soroban-enabled ledger:

```bash
# Start local Soroban network (Stellar Quickstart)
docker run -it --rm \
  -p 8000:8000 \
  -e PROTOCOL_VERSION=21 \
  stellar/quickstart:latest standalone

# In another terminal, confirm network is ready
curl http://localhost:8000/soroban/rpc
```

### Cargo Test

Run all Rust unit tests:

```bash
# Build and test all contracts
cargo test --workspace

# Test specific contract
cargo test -p k2-kinetic-router

# Run tests with backtrace on failure
RUST_BACKTRACE=1 cargo test

# Run with verbose output
cargo test -- --nocapture --test-threads=1
```

### Test Compilation

```bash
# Verify all contracts compile
cargo build --workspace --release

# Check WASM outputs
ls -la contracts/kinetic-router/target/wasm32-unknown-unknown/release/*.wasm
```

---

## 3. Integration Tests

### Setup Integration Test Environment

```bash
cd integration-tests

# Create .env from template
cp .env.example .env

# Configure for local network
cat > .env << 'EOF'
SOROBAN_RPC_URL=http://localhost:8000/soroban/rpc
SOROBAN_NETWORK_PASSPHRASE=Standalone Network ; February 2017
FRIENDBOT_URL=http://localhost:8000/friendbot
ADMIN_SECRET=<your-stellar-secret-key>
DEPLOYED_NETWORK=local
EOF

# Install dependencies
yarn install
```

### Deploy Contracts Locally

```bash
# From project root
./scripts/deploy_local_quick.sh

# Verify deployment
cat deployed/local_addresses.json

# Example output:
# {
#   "lending_pool": "CBBB...",
#   "token_usdc": "CBBB...",
#   "oracle": "CBBB...",
#   ...
# }
```

### Run Integration Tests

```bash
cd integration-tests

# Run all tests
yarn test

# Run specific test file
yarn test src/kinetic-router.integration.test.ts

# Watch mode (for development)
yarn test:watch

# CI mode with coverage
yarn test:ci
```

---

## 4. Test Organization

### Unit Test Structure

K2 unit tests follow this pattern:

```
tests/unit-tests/src/
- lib.rs                                # Test module exports
- kinetic_router_test.rs               # Main router tests
- kinetic_router_functional_tests.rs   # Complex scenarios
- kinetic_router_test_liquidation*.rs  # Liquidation edge cases
- kinetic_router_test_*.rs             # Feature-specific tests
- price_oracle_test.rs                 # Oracle tests
- treasury_test.rs                     # Treasury tests
- interest_rate_strategy_test.rs       # Rate strategy tests
```

### Integration Test Structure

```
integration-tests/src/
- kinetic-router.integration.test.ts   # Main test suite
- testUtils.ts                         # Helper functions
- deployments/                         # Contract addresses
- local_addresses.json             # Deployed contract IDs
```

### Naming Conventions

- **Test functions**: `test_<operation>_<scenario>` (snake_case)
  - Example: `test_supply_exceeds_supply_cap`
- **Test modules**: `<contract>_test_<feature>.rs`
  - Example: `kinetic_router_test_liquidation.rs`
- **Helper functions**: `<verb>_<noun>` (no "test" prefix)
  - Example: `create_test_env`, `init_reserve`

---

## 5. Writing Unit Tests

### Basic Test Structure

```rust
#[test]
fn test_operation_succeeds() {
    // 1. Setup test environment
    let env = Env::default();
    env.mock_all_auths();

    // 2. Create test data
    let admin = Address::generate(&env);
    let user = Address::generate(&env);

    // 3. Initialize contracts
    let (router, oracle) = initialize_kinetic_router(
        &env,
        &admin,
        &Address::generate(&env),  // emergency_admin
        &Address::generate(&env),  // router
        &Address::generate(&env),  // dex_router
    );

    // 4. Setup initial state
    let client = kinetic_router::Client::new(&env, &router);
    // ... reserve initialization ...

    // 5. Execute operation
    let result = client.supply(&user, &asset_addr, &1_000_000);

    // 6. Assert expectations
    assert!(result.is_ok());
}
```

### Mock Setup Patterns

#### Environment Mock All Authorizations

```rust
let env = Env::default();
env.mock_all_auths();  // All auth checks pass automatically
env.budget().reset_unlimited();  // For complex tests
```

#### Create Test Addresses

```rust
let admin = Address::generate(&env);
let emergency_admin = Address::generate(&env);
let user1 = Address::generate(&env);
let user2 = Address::generate(&env);
```

#### Create Stellar Asset Contract

```rust
let underlying_asset_contract = env.register_stellar_asset_contract_v2(admin.clone());
let underlying_asset = underlying_asset_contract.address();
```

#### Mint Tokens to Test User

```rust
let asset_client = stellar_asset::Client::new(&env, &underlying_asset);
asset_client.mint(&user, &1_000_000_000_000);  // 1M with 12 decimals
```

### Common Test Patterns

#### Supply and Verify

```rust
#[test]
fn test_supply_increases_atoken_balance() {
    let env = Env::default();
    env.mock_all_auths();

    // Setup
    let (router, oracle) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router);
    let (underlying, a_token_addr) = create_and_init_reserve(...);

    // Fund user
    mint_tokens(&env, &underlying, &user, 1_000_000_000_000);

    // Approve and supply
    client.supply(&user, &underlying, &1_000_000_000_000);

    // Verify
    let atoken_client = a_token::Client::new(&env, &a_token_addr);
    let balance = atoken_client.balance(&user);
    assert_eq!(balance, 1_000_000_000_000);
}
```

#### Test Expected Error

```rust
#[test]
fn test_borrow_without_collateral_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router);

    // Try to borrow without collateral
    let result = client.borrow(&user, &asset_addr, &100);

    // Expect specific error
    assert_eq!(
        result,
        Err(Ok(KineticRouterError::InsufficientCollateral))
    );
}
```

#### Multi-User Interaction

```rust
#[test]
fn test_liquidation_transfers_collateral() {
    let env = Env::default();
    env.mock_all_auths();

    let (router, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router);

    // Setup: Borrower with collateral
    setup_borrower_with_debt(&env, &client, &borrower, &collateral_asset);

    // Action: Liquidator liquidates unhealthy position
    let result = client.liquidation_call(
        &liquidator,
        &collateral_asset,
        &debt_asset,
        &borrower,
        &1_000_000,  // debt_to_cover
        &false,       // receive_a_token
    );

    // Verify: Liquidator received collateral
    assert!(result.is_ok());
    let liquidator_balance = get_token_balance(&collateral_asset, &liquidator);
    assert!(liquidator_balance > 0);
}
```

---

## 6. Test Coverage

### Coverage Targets

- **Core Operations**: 100% (supply, withdraw, borrow, repay, liquidate)
- **Error Paths**: 100% (all error codes must be tested)
- **Edge Cases**: 95%+ (zero amounts, max values, precision boundaries)
- **Oracle Integration**: 95%+ (price updates, staleness, precision)

### Generate Coverage Report

```bash
# Install tarpaulin
cargo install cargo-tarpaulin

# Generate coverage
cargo tarpaulin --workspace --out Html --output-dir coverage

# View report
open coverage/index.html
```

### Coverage Targets by Component
  Component | Target | Status |
  -----------|--------|--------|
  kinetic-router | 95%+ | Primary focus |
  a-token | 90%+ | Secondary |
  debt-token | 90%+ | Secondary |
  price-oracle | 90%+ | Secondary |
  shared/utils | 100% | Critical |
  shared/math | 100% | Critical |

---

## 7. Fuzz Testing

### Property-Based Testing with Proptest

K2 contracts use property-based testing for complex operations:

```bash
# Run all fuzz tests
cargo test --release

# Run specific contract fuzz tests
cargo test -p k2-kinetic-router --release

# Run with specific seed (for reproducibility)
PROPTEST_RNGALGORITHM=Xorshift cargo test
```

### Example Fuzz Test

```rust
#[test]
fn test_health_factor_calculation_never_panics() {
    let env = Env::default();
    env.mock_all_auths();
    env.budget().reset_unlimited();

    // Generate random but valid inputs
    let collateral_amounts: Vec<u128> = (0..10)
        .map(|_| random::<u128>() % 1_000_000_000_000)
        .collect();

    let debt_amount: u128 = random::<u128>() % 1_000_000_000_000;

    // Should never panic on valid inputs
    let result = calculate_health_factor_u256(
        &env,
        &collateral_amounts,
        &debt_amount,
        &oracle_to_wad,
    );

    // Result must be valid
    assert!(result.is_ok() || matches!(result, Err(KineticRouterError::MathOverflow)));
}
```

---

## 8. Integration Test Simulation

### Test Environment Setup

Integration tests simulate full protocol flow:

```typescript
import { KineticRouterContractClient } from '@stellar/stellar-sdk';
import { invokeContract, supply, borrow, repay } from './testUtils';

describe('Full Protocol Flow', () => {
  let env: any;
  let admin: Keypair;
  let user1: Keypair;

  before(async () => {
    // Load deployed contracts
    const addresses = loadDeployedAddresses();
    env = new SorobanClient(addresses);
  });

  it('should execute full supply->borrow->repay flow', async () => {
    // Step 1: Approve
    await supply(user1, env.lendingPool, addresses.token_usdc, 1_000_000);

    // Step 2: Borrow
    await borrow(user1, env.lendingPool, addresses.token_usdt, 500_000);

    // Step 3: Repay
    const repaid = await repay(user1, env.lendingPool, addresses.token_usdt, 250_000);
  });
});
```

---

## 9. Supply/Borrow Scenarios

### Simple Supply Test

```rust
#[test]
fn test_simple_supply() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, oracle_addr) = initialize_kinetic_router(
        &env,
        &admin,
        &emergency_admin,
        &Address::generate(&env),
        &Address::generate(&env),
    );

    let (asset, atoken_addr) = create_and_init_test_reserve_with_oracle(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
    );

    let client = kinetic_router::Client::new(&env, &router_addr);

    // Mint 100 tokens to user
    let underlying_client = stellar_asset::Client::new(&env, &asset);
    underlying_client.mint(&user, &100_000_000);  // 100 with 6 decimals

    // Supply
    client.supply(&user, &asset, &100_000_000);

    // Verify aToken balance
    let atoken_client = a_token::Client::new(&env, &atoken_addr);
    assert_eq!(atoken_client.balance(&user), 100_000_000);
}
```

### Supply with Interest Accrual

```rust
#[test]
fn test_supply_with_interest_accrual() {
    let env = Env::default();
    env.mock_all_auths();

    // Setup with time progression
    let (router_addr, oracle_addr) = initialize_kinetic_router(...);
    let (asset, atoken_addr) = create_and_init_test_reserve_with_oracle(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    // Initial supply
    client.supply(&user1, &asset, &1_000_000_000_000);

    // Borrower borrows (creates debt for lenders)
    client.borrow(&user2, &asset, &500_000_000_000);

    // Advance time by 1 year
    env.ledger().with_mut(|ledger| {
        ledger.set_timestamp(ledger.timestamp() + 31_536_000);  // +1 year
    });

    // Refresh reserve to accrue interest
    client.refresh_reserve_state(&asset);

    // User's aToken should have accrued interest
    let atoken_client = a_token::Client::new(&env, &atoken_addr);
    let balance = atoken_client.balance_scaled(&user1);
    assert!(balance > 1_000_000_000_000);  // Should increase with interest
}
```

### Borrow with Collateral Verification

```rust
#[test]
fn test_borrow_with_sufficient_collateral() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, oracle_addr) = initialize_kinetic_router(...);
    let (usdc_asset, _) = create_and_init_test_reserve_with_oracle(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
    );
    let (usdt_asset, _) = create_and_init_test_reserve_with_oracle(...);

    let client = kinetic_router::Client::new(&env, &router_addr);

    // Supply 1000 USDC as collateral (price = $1)
    mint_tokens(&env, &usdc_asset, &user, 1_000_000_000_000);
    client.supply(&user, &usdc_asset, &1_000_000_000_000);

    // Borrow 500 USDT (50% LTV)
    client.borrow(&user, &usdt_asset, &500_000_000_000);

    // Verify health factor > 1
    let account_data = client.get_user_account_data(&user);
    assert!(account_data.health_factor > WAD);  // WAD = 1e18
}
```

---

## 10. Liquidation Testing

### Basic Liquidation Test

```rust
#[test]
fn test_liquidation_seizes_collateral() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, oracle_addr) = initialize_kinetic_router(...);
    let (usdc_asset, usdc_atoken) = create_and_init_test_reserve_with_oracle(...);
    let (usdt_asset, _) = create_and_init_test_reserve_with_oracle(...);

    let client = kinetic_router::Client::new(&env, &router_addr);
    let oracle_client = price_oracle::Client::new(&env, &oracle_addr);

    // Setup: Borrower with 1000 USDC collateral, borrows 800 USDT
    mint_tokens(&env, &usdc_asset, &borrower, 1_000_000_000_000);
    client.supply(&borrower, &usdc_asset, &1_000_000_000_000);
    client.borrow(&borrower, &usdt_asset, &800_000_000_000);

    // USDT price rises to make position unhealthy
    // Liquidation threshold: 85%, so health = 1000 * 0.85 / 800 = 1.0625
    // We need health < 1, so reduce collateral value or increase debt value

    oracle_client.set_manual_override(
        &admin,
        &price_oracle::Asset::Stellar(usdt_asset.clone()),
        &Some(1_200_000_000_000_000u128),  // 1.2 USDT
        &Some(env.ledger().timestamp() + 604_800),
    );

    // Refresh to update rates
    client.refresh_reserve_state(&usdt_asset);

    // Verify position is now unhealthy
    let account_data = client.get_user_account_data(&borrower);
    assert!(account_data.health_factor < WAD);

    // Liquidator liquidates 200 USDT debt
    let liquidator = Address::generate(&env);
    mint_tokens(&env, &usdt_asset, &liquidator, 1_000_000_000_000);

    let result = client.liquidation_call(
        &liquidator,
        &usdc_asset,      // collateral_asset
        &usdt_asset,      // debt_asset
        &borrower,        // user
        &200_000_000_000, // debt_to_cover
        &false,           // receive_a_token
    );

    assert!(result.is_ok());

    // Verify liquidator received collateral
    let liquidator_usdc = underlying_client.balance(&liquidator);
    assert!(liquidator_usdc > 0);
}
```

### Liquidation with Health Factor Check

```rust
#[test]
fn test_liquidation_improves_health_factor() {
    // Setup unhealthy position
    let (borrower, collateral_asset, debt_asset) = setup_unhealthy_position(&env);

    let client = kinetic_router::Client::new(&env, &router_addr);
    let initial_hf = client.get_user_account_data(&borrower).health_factor;
    assert!(initial_hf < WAD);

    // Execute liquidation
    let debt_to_cover = get_close_factor_amount(&env, &borrower, &debt_asset);
    client.liquidation_call(
        &liquidator,
        &collateral_asset,
        &debt_asset,
        &borrower,
        &debt_to_cover,
        &false,
    );

    // Health factor should improve (or stay same, never decrease)
    let final_hf = client.get_user_account_data(&borrower).health_factor;
    assert!(final_hf >= initial_hf);
}
```

---

## 11. Edge Cases

### Zero Amount Operations

```rust
#[test]
fn test_supply_zero_fails() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    let result = client.supply(&user, &asset, &0);
    assert_eq!(result, Err(Ok(KineticRouterError::InvalidAmount)));
}

#[test]
fn test_borrow_zero_fails() {
    let result = client.borrow(&user, &asset, &0);
    assert_eq!(result, Err(Ok(KineticRouterError::InvalidAmount)));
}
```

### Maximum Value Operations

```rust
#[test]
fn test_supply_cap_enforcement() {
    let env = Env::default();
    env.mock_all_auths();

    // Supply cap: 1M tokens
    let (router_addr, _) = initialize_kinetic_router(...);
    let (asset, _) = create_and_init_test_reserve_with_oracle(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    // Supply near cap
    mint_tokens(&env, &asset, &user1, 1_000_000_000_000);  // 1M
    client.supply(&user1, &asset, &950_000_000_000);

    // Attempt to exceed cap
    mint_tokens(&env, &asset, &user2, 1_000_000_000_000);
    let result = client.supply(&user2, &asset, &100_000_000_000);

    assert_eq!(result, Err(Ok(KineticRouterError::SupplyCapExceeded)));
}

#[test]
fn test_borrow_cap_enforcement() {
    // Similar pattern for borrow cap
    let result = client.borrow(&user, &asset, &over_borrow_cap);
    assert_eq!(result, Err(Ok(KineticRouterError::BorrowCapExceeded)));
}
```

### Dust Debt Handling

```rust
#[test]
fn test_dust_debt_during_liquidation() {
    // Setup: Position with small remaining debt (dust)
    let (borrower, collateral, debt_asset) = setup_position_near_liquidation(&env);

    let client = kinetic_router::Client::new(&env, &router_addr);

    // Liquidate most debt
    client.liquidation_call(
        &liquidator,
        &collateral,
        &debt_asset,
        &borrower,
        &9_999_999,  // Almost all debt
        &false,
    );

    // Remaining dust should trigger socialization
    let remaining_debt = client.get_user_debt_balance(&borrower, &debt_asset);
    assert!(remaining_debt < MIN_REMAINING_DEBT);
}
```

---

## 12. Precision Testing

### WAD/RAY Conversion Tests

```rust
#[test]
fn test_oracle_to_wad_precision() {
    // Oracle precision: 14 decimals
    // WAD precision: 18 decimals
    // oracle_to_wad factor: 10^(18-14) = 10_000

    let oracle_price = 1_000_000_000_000_000u128;  // 1 USD with 14 decimals
    let wad_price = oracle_price * calculate_oracle_to_wad_factor(14);

    assert_eq!(wad_price, 1_000_000_000_000_000 * 10_000);
}

#[test]
fn test_ray_precision_calculations() {
    // RAY = 1e27, WAD = 1e18
    // RAY_WAD_RATIO = 1e9

    let wad_value = WAD;
    let ray_value = wad_value * RAY_WAD_RATIO;

    assert_eq!(ray_value, RAY);
}

#[test]
fn test_basis_points_to_percentage() {
    // 1 basis point = 0.01% = 1/10000

    let basis_points = 500u128;  // 5%
    let percentage = basis_points * WAD / BASIS_POINTS;

    assert_eq!(percentage, 50_000_000_000_000_000);  // 0.05 in WAD
}
```

### Rounding and Overflow Prevention

```rust
#[test]
fn test_rounding_down_in_division() {
    // When calculating withdrawal amounts, round down to prevent negative balances
    let balance_scaled = 1_000_000_000_000_000_000u128;  // 1 token
    let index = 1_050_000_000_000_000_000u128;          // 5% interest

    let balance_underlying = ray_div_down(balance_scaled, index);
    assert!(balance_underlying <= balance_scaled / index);
}

#[test]
fn test_no_overflow_in_health_factor() {
    // Health Factor: collateral * threshold * WAD / (debt * 10000)
    // Must use U256 intermediate to prevent overflow

    let max_collateral = u128::MAX;
    let max_price = 1_000_000_000_000_000u128;
    let result = calculate_health_factor_u256(
        max_collateral,
        max_price,
        &oracle_to_wad,
    );

    // Should not overflow
    assert!(result.is_ok());
}
```

---

## 13. Error Codes

Complete reference of all K2 error codes:

### KineticRouterError (1-57)
  Code | Name | Meaning | Recovery |
  ------|------|---------|----------|
  1 | InvalidAmount | Amount is zero or invalid | Use valid positive amount |
  2 | AssetNotActive | Asset is not enabled in pool | Activate asset in configuration |
  3 | AssetFrozen | Asset is frozen | Unfreeze asset |
  4 | AssetPaused | Asset is paused | Unpause asset or emergency admin |
  5 | BorrowingNotEnabled | Borrowing disabled for asset | Enable borrowing in config |
  7 | InsufficientCollateral | Insufficient collateral to borrow | Supply more collateral |
  8 | HealthFactorTooLow | Health factor below threshold | Repay debt or add collateral |
  10 | PriceOracleNotFound | Oracle not initialized | Initialize oracle first |
  11 | InvalidLiquidation | Position not liquidatable | Position must be unhealthy |
  12 | LiquidationAmountTooHigh | Liquidation exceeds max (50%) | Reduce liquidation amount |
  13 | NoDebtOfRequestedType | No debt in requested asset | Borrow the asset first |
  14 | InvalidFlashLoanParams | Flash loan params invalid | Verify assets/amounts match |
  15 | FlashLoanNotAuthorized | Caller not authorized for flash loan | Whitelist caller |
  16 | IsolationModeViolation | Isolation mode constraint violated | Respect isolation debt ceiling |
  17 | PriceOracleInvocationFailed | Oracle call failed | Check oracle connectivity |
  18 | PriceOracleError | Oracle returned error | Check oracle data |
  19 | SupplyCapExceeded | Supply would exceed cap | Reduce amount |
  20 | BorrowCapExceeded | Borrow would exceed cap | Reduce amount |
  21 | DebtCeilingExceeded | Isolation mode debt exceeded | Reduce isolated asset debt |
  22 | UserInIsolationMode | User in isolation mode | Exit isolation mode first |
  24 | ReserveNotFound | Reserve not initialized | Initialize reserve |
  25 | UserNotFound | User account not found | User must have supply/borrow |
  26 | Unauthorized | Caller not authorized | Check permissions |
  27 | AlreadyInitialized | Contract already initialized | Cannot reinitialize |
  28 | NotInitialized | Contract not initialized | Call initialize first |
  29 | ReserveAlreadyInitialized | Reserve already exists | Use different asset |
  30 | FlashLoanExecutionFailed | Callback execution failed | Check callback contract |
  31 | FlashLoanNotRepaid | Flash loan not repaid | Repay loan + fee |
  32 | InsufficientFlashLoanLiquidity | Insufficient funds for loan | Try smaller amount |
  33 | ATokenMintFailed | aToken mint failed | Check aToken contract |
  34 | DebtTokenMintFailed | Debt token mint failed | Check debt token contract |
  35 | UnderlyingTransferFailed | Token transfer failed | Check balance/allowance |
  36 | FlashLoanTransferFailed | Flash loan transfer failed | Check liquidity |
  37 | MathOverflow | Math operation overflowed | Use U256 for large numbers |
  38 | Expired | Data has expired | Refresh oracle/data |
  39 | InsufficientSwapOut | Swap output below minimum | Lower slippage tolerance |
  40 | MinProfitNotMet | Liquidation profit below min | Larger liquidation amount |
  41 | TreasuryNotSet | Treasury address not configured | Set treasury address |
  42 | InsufficientLiquidity | Not enough liquidity | Wait for repayments |
  43 | AMMRequired | DEX router required | Configure DEX router |
  44 | UnauthorizedAMM | AMM not whitelisted | Whitelist AMM address |
  45 | AdapterNotInitialized | Swap adapter not ready | Initialize adapter |
  46 | ATokenBurnFailed | aToken burn failed | Check aToken contract |
  47 | WASMHashNotSet | Contract hash not set | Set contract hash |
  48 | TokenDeploymentFailed | Token creation failed | Check parameters |
  49 | TokenInitializationFailed | Token init failed | Check init params |
  50 | AddressNotWhitelisted | Address not whitelisted | Add to whitelist |
  51 | NoPendingAdmin | No pending admin queued | Queue admin first |
  52 | InvalidPendingAdmin | Invalid pending admin address | Queue valid address |
  53 | TokenCallFailed | Token operation failed | Check token contract |

### OracleError (1-21)
  Code | Name | Meaning |
  ------|------|---------|
  1 | AssetPriceNotFound | Asset price not available |
  2 | PriceSourceNotSet | Oracle source not configured |
  3 | InvalidPriceSource | Price source address invalid |
  4 | PriceTooOld | Price exceeds staleness threshold |
  5 | PriceHeartbeatExceeded | Heartbeat interval exceeded |
  6 | NotInitialized | Oracle not initialized |
  7 | AssetNotWhitelisted | Asset not in whitelist |
  8 | AssetDisabled | Asset is disabled |
  9 | OracleQueryFailed | Query to external oracle failed |
  10 | InvalidCalculation | Price calculation error |
  11 | FallbackNotImplemented | Fallback oracle not available |
  12 | AlreadyInitialized | Oracle already initialized |
  13 | AssetAlreadyWhitelisted | Asset already whitelisted |
  14 | Unauthorized | Not authorized for operation |
  15 | PriceManipulationDetected | Price change detection triggered |
  16 | PriceChangeTooLarge | Price delta exceeds limit |
  17 | OverrideExpired | Manual override has expired |
  18 | MathOverflow | Math calculation overflow |
  19 | InvalidPrice | Price value invalid |
  20 | InvalidConfig | Configuration invalid |
  21 | OverrideDurationTooLong | Override duration exceeds max |

---

## 14. Error Testing

### Testing Expected Errors

```rust
#[test]
fn test_error_insufficient_collateral() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    // User with no collateral tries to borrow
    let result = client.borrow(&user_no_collateral, &asset, &1_000_000);

    assert_eq!(
        result,
        Err(Ok(KineticRouterError::InsufficientCollateral))
    );
}

#[test]
fn test_error_asset_paused() {
    // Setup asset in paused state
    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    // Pause asset
    client.set_pause(&emergency_admin, &asset, &true);

    // Operations fail
    let supply_result = client.supply(&user, &asset, &1_000_000);
    assert_eq!(supply_result, Err(Ok(KineticRouterError::AssetPaused)));

    let borrow_result = client.borrow(&user, &asset, &500_000);
    assert_eq!(borrow_result, Err(Ok(KineticRouterError::AssetPaused)));
}

#[test]
fn test_error_supply_cap_exceeded() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, oracle_addr) = initialize_kinetic_router(...);
    let (asset, _) = create_and_init_test_reserve_with_oracle(
        &env,
        &router_addr,
        &oracle_addr,
        &admin,
    );

    let client = kinetic_router::Client::new(&env, &router_addr);

    // Mint and try to supply beyond cap (1M tokens)
    mint_tokens(&env, &asset, &user, 2_000_000_000_000);

    let result = client.supply(&user, &asset, &1_500_000_000_000);
    assert_eq!(result, Err(Ok(KineticRouterError::SupplyCapExceeded)));
}
```

### Verifying Error Messages

```rust
#[test]
fn test_error_displays_helpful_message() {
    let error = KineticRouterError::InvalidAmount;
    let message = format!("{:?}", error);
    assert!(message.contains("InvalidAmount"));
}
```

---

## 15. Common Mistakes

### Mistake 1: Forgetting oracle_to_wad in Price Conversions

**Wrong:**
```rust
let collateral_value = collateral_amount * oracle_price / decimals;
// Missing oracle_to_wad factor!
```

**Correct:**
```rust
let collateral_value = collateral_amount * oracle_price * oracle_to_wad / decimals;
```

### Mistake 2: Not Using U256 for Intermediate Calculations

**Wrong:**
```rust
let health_factor = collateral * threshold / debt;  // Can overflow!
```

**Correct:**
```rust
let health_factor = U256::from(collateral)
    .checked_mul(U256::from(threshold))
    .and_then(|v| v.checked_div(U256::from(debt)))
    .ok_or(KineticRouterError::MathOverflow)?;
```

### Mistake 3: Using mock_all_auths() in Production Tests

**Wrong:**
```rust
env.mock_all_auths();  // Every auth check passes!
```

**Correct for Security Tests:**
```rust
// Don't mock, let real auth checks run
let result = client.withdraw(&unauthorized_user, &asset, &amount);
assert_eq!(result, Err(Ok(KineticRouterError::Unauthorized)));
```

### Mistake 4: Not Checking Health Factor Before Liquidation

**Wrong:**
```rust
let result = client.liquidation_call(&liquidator, ...);
```

**Correct:**
```rust
let account_data = client.get_user_account_data(&borrower);
assert!(account_data.health_factor < WAD);  // Verify first
let result = client.liquidation_call(&liquidator, ...);
```

### Mistake 5: Zero Amount Handling

**Wrong:**
```rust
client.supply(&user, &asset, &0);  // Don't check
```

**Correct:**
```rust
let result = client.supply(&user, &asset, &0);
assert_eq!(result, Err(Ok(KineticRouterError::InvalidAmount)));
```

### Mistake 6: Interest Index Confusion

**Wrong:**
```rust
let balance = user_balance_scaled * index;  // Incorrect direction!
```

**Correct:**
```rust
// scaled_balance tracks position: balance = scaled_balance * index
let balance = user_balance_scaled.wrapping_mul(index).wrapping_div(RAY);
```

---

## 16. Debugging Tips

### Enable Verbose Output

```bash
# Run test with backtrace and output
RUST_BACKTRACE=full cargo test -- --nocapture --test-threads=1

# See contract events
RUST_LOG=soroban_sdk=debug cargo test
```

### Inspect Contract State During Tests

```rust
#[test]
fn test_with_state_inspection() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    // Operation 1
    client.supply(&user1, &asset, &1_000_000);

    // Debug: Check state
    let user_config = client.get_user_configuration(&user1);
    println!("User config: {:?}", user_config);

    // Operation 2
    client.borrow(&user1, &asset2, &500_000);

    // Debug: Check state again
    let account_data = client.get_user_account_data(&user1);
    println!("Account data: {:?}", account_data);
}
```

### Check Contract Events

```rust
#[test]
fn test_emits_supply_event() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    client.supply(&user, &asset, &1_000_000);

    // Check events
    let events = env.events().all();
    println!("Events: {:?}", events);
    assert!(events.len() > 0);
}
```

### Breakpoint Debugging

```bash
# For VSCode debugging with CodeLLDB
# Add .vscode/launch.json:
{
  "version": "0.2.0",
  "configurations": [
    {
      "type": "lldb",
      "request": "launch",
      "name": "Test Specific",
      "cargo": {
        "args": [
          "test",
          "--lib",
          "test_name",
          "--",
          "--nocapture"
        ],
        "filter": {
          "name": "test_name",
          "kind": "test"
        }
      },
      "sourceLanguages": ["rust"]
    }
  ]
}
```

---

## 17. Contract Inspection

### Query Reserve Data

```typescript
// Integration test - read reserve state
const reserveData = await client.query('get_reserve_data', {
  reserve: addresses.token_usdc
});

console.log('Reserve:', {
  liquidity_index: reserveData.liquidity_index,
  borrow_index: reserveData.variable_borrow_index,
  utilization: reserveData.total_debt / reserveData.available_liquidity,
  rates: {
    supply: reserveData.current_liquidity_rate,
    borrow: reserveData.current_variable_borrow_rate
  }
});
```

### Query User Account

```typescript
const userAccount = await client.query('get_user_account_data', {
  user: userAddress
});

console.log('User Account:', {
  total_collateral: userAccount.total_collateral_in_wad,
  total_debt: userAccount.total_debt_in_wad,
  health_factor: userAccount.health_factor,
  can_borrow: userAccount.health_factor > 1e18
});
```

### View Contract Storage

```bash
# Query contract data via Soroban RPC
soroban contract invoke \
  --id CBBB... \
  --network standalone \
  -- \
  get_user_configuration \
  --user GBBB...
```

---

## 18. Event Inspection

### Listen for Contract Events

```typescript
// Watch for supply events
client.onSupply((event) => {
  console.log('Supply:', {
    user: event.user,
    asset: event.asset,
    amount: event.amount,
    atoken_minted: event.atoken_minted
  });
});

// Watch for borrow events
client.onBorrow((event) => {
  console.log('Borrow:', {
    user: event.user,
    asset: event.asset,
    amount: event.amount,
    debt_token_issued: event.debt_token_issued
  });
});
```

### Parse Event Data

```rust
#[test]
fn test_events_emitted() {
    let env = Env::default();
    env.mock_all_auths();

    let (router_addr, _) = initialize_kinetic_router(...);
    let client = kinetic_router::Client::new(&env, &router_addr);

    client.supply(&user, &asset, &1_000_000);

    let events = env.events().all();
    for event in &events {
        match event.data.clone() {
            soroban_sdk::EnvVal::Vec(_) => {
                println!("Event: {:?}", event);
            },
            _ => {}
        }
    }
}
```

---

## 19. Performance Analysis

### CPU Cost Profiling

```bash
# Get CPU instructions used
cargo test --release -- --nocapture 2>&1 | grep "instructions"

# Profile specific contract
soroban contract invoke --network standalone \
  --id CBBB... \
  -- supply \
  --user GBBB... \
  --asset CBBB... \
  --amount 1000000 \
  --budget \
  tail -20
```

### Optimize High-Cost Operations

```rust
// Expensive: Iterating all reserves for user HF calc
// O(reserves) complexity
let health = calculate_user_health(&env, &user, &config);

// Optimized: Use bitmap to track active reserves only
// O(user_active_positions) complexity
let active_reserves = user_config.get_active_reserves();
let health = calculate_health_from_active(&env, &user, &active_reserves);
```

---

## 20. Gas Optimization

### Key Optimization Strategies

1. **Cache Oracle Config**: Don't query on every operation
2. **Thread Reserve Data**: Pass through call stack vs. re-fetch
3. **Bitmap Iteration**: Only iterate user's active positions
4. **Lazy State Updates**: Update only what changed
5. **Batch Operations**: Combine multi-step operations

### Example: Optimized Supply Flow

```rust
// Step 1: Cache oracle config
let oracle_config = get_oracle_config(&env);  // Once

// Step 2: Fetch reserve data once
let reserve_data = get_reserve_data(&env, &asset);

// Step 3: Thread through validations
validate_user_can_supply(
    &env,
    &user,
    &reserve_data,
    &oracle_config,
    &amount,
)?;

// Step 4: Execute supply
execute_supply(
    &env,
    &user,
    &reserve_data,
    &amount,
)?;
```

---

## 21. Code Patterns

### Idiomatic Soroban Pattern: Authorization

```rust
// Always check auth at function entry
pub fn supply(
    env: Env,
    from: Address,
    asset: Address,
    amount: u128,
) -> Result<(), KineticRouterError> {
    from.require_auth();  // Must be called first

    // Then execute operation
    // ...
}
```

### Pattern: Safe Math with U256

```rust
use soroban_sdk::U256;

fn safe_multiply(a: u128, b: u128, c: u128) -> Result<u128, KineticRouterError> {
    U256::from(a)
        .checked_mul(U256::from(b))
        .and_then(|v| v.checked_mul(U256::from(c)))
        .and_then(|v| u128::try_from(v).ok())
        .ok_or(KineticRouterError::MathOverflow)
}
```

### Pattern: Error Handling

```rust
// Simple propagation
operation()
    .map_err(|e| KineticRouterError::SomeError)?;

// With custom error mapping
operation()
    .map_err(|_| KineticRouterError::OperationFailed)?;

// Multiple operations
(operation1())
    .and_then(|_| operation2())
    .and_then(|_| operation3())
    .map_err(|e| KineticRouterError::ComplexOperationFailed)?;
```

---

## 22. Security Review Checklist

Before deploying custom code, verify:

### Authorization
- [ ] All privileged operations call `require_auth()`
- [ ] Emergency admin can pause but not unpause
- [ ] Pool admin required for unpause
- [ ] No hardcoded addresses in contracts
- [ ] Treasury address validated

### Math Safety
- [ ] All price conversions include `oracle_to_wad`
- [ ] Large multiplications use U256
- [ ] Division by zero protected
- [ ] Rounding direction correct (down for withdrawal, up for fees)
- [ ] No integer overflow in bounds checks

### Liquidation
- [ ] Health factor improves after liquidation
- [ ] Close factor enforced (≤ 50%)
- [ ] Liquidation bonus respected
- [ ] Dust debt properly handled
- [ ] Post-liquidation HF validation

### Oracle Integration
- [ ] Price staleness checked
- [ ] Price precision validated (0-18 decimals)
- [ ] Circuit breaker prevents extreme moves
- [ ] Manual override expiration enforced
- [ ] Fallback oracle logic correct

### Flash Loans
- [ ] Fee calculation rounds UP
- [ ] Callback authorization checked
- [ ] Premium collected before callback
- [ ] Debt properly tracked and enforced

### Token Operations
- [ ] Recipient validation (not aToken, not debt token)
- [ ] Approval checked before transfer
- [ ] Balance updated before external call (CEI)
- [ ] Failed transfers properly handled
- [ ] Token decimals used correctly

### State Management
- [ ] No re-entrancy vulnerabilities
- [ ] State updated in correct order
- [ ] Consistency checks pass
- [ ] Reserve state always valid

---

## 23. Upgrade Testing

### Test Contract Upgrade Path

```rust
#[test]
fn test_upgrade_preserves_state() {
    let env = Env::default();
    env.mock_all_auths();

    // Deploy v1
    let router_v1 = env.register(kinetic_router_v1::WASM, ());
    let client_v1 = kinetic_router::Client::new(&env, &router_v1);

    // Initialize and create state
    client_v1.initialize(&admin, ...);
    let (asset, _) = create_and_init_test_reserve_with_oracle(...);
    client_v1.supply(&user, &asset, &1_000_000);

    // Get state before upgrade
    let account_before = client_v1.get_user_account_data(&user);

    // Upgrade to v2
    let hash_v2 = env.deployer().upload_contract_wasm(kinetic_router_v2::WASM);
    client_v1.upgrade(&admin, &hash_v2);

    // Verify state preserved
    let account_after = client_v1.get_user_account_data(&user);
    assert_eq!(account_before.total_collateral, account_after.total_collateral);

    // Verify new functionality works
    let new_feature_result = client_v1.new_feature();
    assert!(new_feature_result.is_ok());
}
```

---

## 24. Migration Procedures

### Safe Migration Pattern

1. **Deploy new version** alongside old (don't replace)
2. **Run compatibility tests** to verify old state loads
3. **Migrate user positions** gradually using helper contracts
4. **Verify completeness** with audit logs
5. **Activate new version** once migration complete
6. **Archive old version** with data preservation

### Example: Upgrading Reserve Configuration

```bash
# Step 1: Deploy new pool configurator
soroban contract deploy \
  --source admin \
  --wasm contracts/pool-configurator/target/wasm32-unknown-unknown/release/k2_pool_configurator.wasm

# Step 2: Migrate reserves one by one
for reserve in USDC USDT EURC; do
  soroban contract invoke \
    --source pool-admin \
    --id <new-configurator> \
    -- \
    update_reserve_configuration \
    --asset <asset-address> \
    --new_config <serialized-config>
done

# Step 3: Verify migration
soroban contract invoke \
  --source pool-admin \
  --id <new-configurator> \
  -- \
  get_reserves
```

---

## Summary

This developer guide covers all aspects of K2 protocol development:
- Setting up local environment
- Running tests (unit, integration, fuzz)
- Writing test scenarios
- Debugging and profiling
- Security considerations
- Upgrade procedures

For questions, refer to the main documentation and audit reports linked in the docs directory.
