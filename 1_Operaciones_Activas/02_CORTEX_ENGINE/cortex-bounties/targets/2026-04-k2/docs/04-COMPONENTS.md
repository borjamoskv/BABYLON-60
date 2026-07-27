# 4. System Components

Detailed technical documentation of each contract, module, and adapter in the K2 lending protocol. Each component section includes purpose, key functions, invariants, interactions, and storage considerations.

---

## 1. Kinetic Router (Core)

**Location**: `/contracts/kinetic-router/`
**Role**: Main entry point and state management for all user operations

### Purpose

The Kinetic Router is the primary contract orchestrating all protocol operations: supply, borrow, repay, withdraw, liquidate, flash loans, and swaps. It serves as the "hub" through which users and liquidators interact with the K2 protocol.

Key responsibilities:
- User authentication and authorization
- Reserve state management (interest accrual, rates)
- Supply/withdraw operations
- Borrow/repay operations
- Liquidation orchestration
- Flash loan coordination
- Collateral swapping
- Health factor validation
- Whitelist/blacklist enforcement
- Emergency pause controls

### Architecture

The router is organized into several internal modules:

| Module | Responsibility |
|--------|-----------------|
| `router.rs` | Public contract entry points |
| `operations.rs` | Supply, withdraw, borrow, repay logic |
| `liquidation.rs` | Liquidation calculations and execution |
| `swap.rs` | Collateral swap operations |
| `flash_loan.rs` | Flash loan validation and callbacks |
| `calculation.rs` | Interest accrual and rate updates |
| `reserve.rs` | Reserve initialization and configuration |
| `validation.rs` | Access control and operational checks |
| `storage.rs` | Persistent and instance state |
| `price.rs` | Price oracle interactions |
| `admin.rs` | Administrative operations |
| `emergency.rs` | Pause and emergency controls |
| `upgrade.rs` | Contract upgrades |

### Key Functions

#### Initialization

```rust
initialize(
    env: Env,
    pool_admin: Address,
    emergency_admin: Address,
    price_oracle: Address,
    treasury: Address,
    dex_router: Address,
    incentives_contract: Option<Address>,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Initialize pool parameters and set admin addresses
- **Auth Required**: `pool_admin` must sign
- **Idempotency**: Fails if already initialized
- **Safety Checks**:
  - Validates pool_admin provides authorization (H-02)
  - Sets safe default parameters
- **Events**: Emits initialization event

#### Supply Operations

```rust
supply(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    on_behalf_of: Address,
    _referral_code: u32,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Deposit assets to earn interest
- **Flow**:
  1. Validate caller authorized
  2. Validate whitelist access (M-01)
  3. Update reserve state (accrue interest)
  4. Validate supply cap
  5. Transfer tokens from caller to aToken
  6. Mint aTokens (scaled balance)
  7. Update user configuration
  8. Recalculate interest rates
- **Invariants**:
  - `supply_cap` not exceeded after operation
  - Caller and on_behalf_of both authorized
  - Recipient cannot be aToken or debt token contracts
  - Minimum first deposit enforced (M-04)
- **Events**: `SupplyEvent`

#### Withdraw Operations

```rust
withdraw(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    to: Address,
) -> Result<u128, KineticRouterError>
```

- **Purpose**: Redeem aTokens for underlying assets
- **Special Cases**:
  - `amount = u128::MAX` withdraws all available
  - Partial withdraws may fail HF check if user has debt
- **Flow**:
  1. Validate authorization
  2. Update reserve state
  3. Validate whitelist access
  4. Calculate actual withdrawal amount (considering liquidity index)
  5. Validate HF remains ≥ 1.0 after withdrawal (if borrowing)
  6. Burn aTokens
  7. Transfer underlying to recipient
  8. Update user configuration if balance becomes zero
  9. Recalculate interest rates
- **Invariants**:
  - User's HF ≥ 1.0 after operation (if debt exists)
  - Available liquidity ≥ amount
  - Actual balance ≥ requested amount
- **Events**: `WithdrawEvent`
- **Returns**: Actual amount withdrawn

#### Borrow Operations

```rust
borrow(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    interest_rate_mode: u32,
    _referral_code: u32,
    on_behalf_of: Address,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Borrow assets against collateral
- **Flow**:
  1. Validate authorization
  2. Update reserve state
  3. Validate whitelist access
  4. Check caller has sufficient collateral
  5. Validate HF remains ≥ 1.0 after borrow (fast-path includes oracle_to_wad, H-01)
  6. Mint debt tokens
  7. Transfer borrowed asset to caller
  8. Update user configuration
  9. Recalculate interest rates
- **Invariants**:
  - HF ≥ 1.0 after operation
  - Caller has non-zero collateral value
  - Borrow cap not exceeded
  - Asset enabled for borrowing
  - Borrowing not paused
- **Events**: `BorrowEvent`

#### Repay Operations

```rust
repay(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    rate_mode: u32,
    on_behalf_of: Address,
) -> Result<u128, KineticRouterError>
```

- **Purpose**: Repay borrowed assets
- **Special Cases**:
  - `amount = u128::MAX` repays entire debt
- **Flow**:
  1. Validate authorization
  2. Update reserve state (accrue interest)
  3. Validate whitelist access
  4. Calculate debt amount with current interest
  5. Burn debt tokens
  6. Transfer repayment from caller to treasury
  7. Update user configuration if debt reaches zero
  8. Recalculate interest rates
- **Invariants**:
  - Amount ≥ 0 and ≤ total debt
  - Caller/on_behalf_of authorized
- **Events**: `RepayEvent`
- **Returns**: Actual amount repaid

#### Liquidation

```rust
liquidation_call(
    env: Env,
    liquidator: Address,
    collateral_asset: Address,
    debt_asset: Address,
    user: Address,
    debt_to_cover: u128,
    _receive_a_token: bool,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Liquidate undercollateralized position (atomic, no flash loan)
- **Prerequisites**:
  - Target user's HF < 1.0
  - Liquidator has debt_to_cover amount of debt asset
- **Flow**:
  1. Validate liquidator authorized
  2. Validate liquidation whitelist (M-01)
  3. Get prices for both assets (NEW-03: oracle_to_wad hoisted)
  4. Validate target HF < 1.0
  5. Validate debt_to_cover ≤ close_factor × total_debt
  6. Calculate collateral to seize
  7. Burn debt tokens from user
  8. Transfer repayment from liquidator
  9. Seize collateral (including socialization if cap exceeded, H-05)
- **Close Factor**: Dynamic: 50% normally, 100% when HF < partial_liquidation_hf_threshold or position < MIN_CLOSE_FACTOR_THRESHOLD
- **Invariants**:
  - Debt ≤ close_factor × total_debt
  - Collateral not over-seized
  - Bad debt properly socialized (H-05)
- **Events**: `LiquidationEvent`

### Two-Step Liquidation

```rust
prepare_liquidation(
    env: Env,
    liquidator: Address,
    user: Address,
    debt_asset: Address,
    collateral_asset: Address,
    debt_to_cover: u128,
    min_swap_out: u128,
    swap_handler: Option<Address>,
) -> Result<LiquidationAuthorization, KineticRouterError>
```

- **Purpose**: (Step 1) Calculate liquidation parameters, return authorization
- **Returns**: `LiquidationAuthorization` struct with collateral amount to seize
- **No State Changes**: Pure calculation only
- **M-13 Check**: Validates minimum remaining debt (no dust debt)

```rust
execute_liquidation(
    env: Env,
    liquidator: Address,
    user: Address,
    debt_asset: Address,
    collateral_asset: Address,
    deadline: u64,
) -> Result<(), KineticRouterError>
```

- **Purpose**: (Step 2) Execute liquidation using pre-validated authorization
- **Flow**: Uses stored `LiquidationAuthorization` from `prepare_liquidation`
- **Atomicity**: Can be combined with flash loan in same transaction

### Flash Loan Operations

```rust
flash_loan(
    env: Env,
    initiator: Address,
    receiver: Address,
    assets: Vec<Address>,
    amounts: Vec<u128>,
    params: Bytes,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Atomic loan without collateral requirement
- **Flow**:
  1. Validate asset enabled for flash loans
  2. Calculate premium (basis points)
  3. Transfer amount to receiver
  4. Call receiver's callback
  5. Verify aToken balance ≥ initial + premium (balance-diff check)
  6. Verify protocol profitability
- **Premium**: Configurable (0-100 bps), rounded UP (L-10)
- **Callback Interface**: Receiver must implement `execute_operation`
- **Invariants**:
  - Premium transferred to treasury
  - Total balance ≥ borrowed + premium
  - Receiver is valid contract

### Collateral Swap

```rust
swap_collateral(
    env: Env,
    caller: Address,
    from_asset: Address,
    to_asset: Address,
    amount: u128,
    min_amount_out: u128,
    swap_handler: Option<Address>,
) -> Result<u128, KineticRouterError>
```

- **Purpose**: Swap supplied collateral to different asset
- **Flow**:
  1. Validate authorization
  2. Validate whitelist (M-01)
  3. Withdraw from_asset (may fail HF check)
  4. Execute swap via DEX adapter
  5. Supply received to_asset
  6. Verify received amount ≥ min_amount_out
  7. Validate HF after operation
- **Slippage Protection**: `min_amount_out` enforced (M-01)
- **Handler Whitelist**: Optional specific handler or default DEX router
- **Invariants**:
  - HF ≥ 1.0 after operation
  - Actual received ≥ min_amount_out
- **Events**: `SwapEvent`
- **Returns**: Actual amount received

### Pause Controls

```rust
pause(env: Env, caller: Address) -> Result<(), KineticRouterError>
```

- **Purpose**: Emergency pause all operations
- **Auth Required**: Emergency admin OR pool admin (M-04)
- **Effect**: All supply/borrow/repay/withdraw operations blocked
- **Use Case**: Emergency response to discovered vulnerabilities

```rust
unpause(env: Env, caller: Address) -> Result<(), KineticRouterError>
```

- **Purpose**: Resume protocol operations
- **Auth Required**: Pool admin only (M-04 - two-step unpause)
- **Flow**: Only pool_admin can unpause (not emergency_admin)

### Storage Considerations

**Instance Storage** (TTL: 1 year, extended every operation):
- Pool admin address
- Emergency admin address
- Price oracle address
- Treasury address
- DEX router address
- Incentives contract address (optional)
- Protocol lock flag (reentrancy guard)
- Pause flag
- Flash loan premium (basis points)
- Health factor liquidation threshold
- Partial liquidation HF threshold
- Minimum swap output bps
- Reserve ID counter

**Persistent Storage**:
- Reserve data map (keyed by asset address)
- User configuration map (keyed by user address)
- Oracle config cache (optimization)
- Reserve whitelist (per asset, per address)
- Reserve blacklist (per asset, per address)
- Liquidation whitelist
- Liquidation blacklist

**TTL Management**:
- Extends instance TTL on every entry point call via `extend_instance_ttl()`
- 1-year extension ensures long-term contract viability

---

## 2. Pool Configurator (Admin)

**Location**: `/contracts/pool-configurator/`
**Role**: Administrative reserve lifecycle and parameter management

### Purpose

The Pool Configurator manages:
- Reserve initialization and lifecycle
- Collateral configuration (LTV, liquidation threshold, bonus)
- Borrowing enablement
- Interest rate strategy assignment
- Pause and freeze controls (M-04)
- Reserve factor adjustment
- WASM code hash storage for factory deployments

### Key Functions

#### Reserve Management

```rust
init_reserve(
    env: Env,
    caller: Address,
    underlying_asset: Address,
    a_token_impl: Address,
    variable_debt_impl: Address,
    interest_rate_strategy: Address,
    treasury: Address,
    params: InitReserveParams,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Register new reserve (manual deployment)
- **Auth Required**: Pool admin
- **Validations** (detailed in reserve.rs):
  - 64-reserve hard cap (UserConfiguration bitmap limit)
  - LTV ≤ 10000 bps
  - Liquidation threshold > LTV + 50 bps (L-04 buffer)
  - Reserve factor ≤ 9999 bps
  - Liquidation bonus ≤ 9999 bps
  - Decimals ≤ 38 (prevents overflow in 10^decimals)
  - Supply/borrow caps fit in u64
- **InitReserveParams**:
  - ltv: Loan-to-value ratio (bps)
  - liquidation_threshold: HF trigger (bps)
  - liquidation_bonus: Liquidator incentive (bps)
  - reserve_factor: Protocol fee share (bps)
  - decimals: Underlying asset decimals
  - supply_cap: Max total supply (whole tokens)
  - borrow_cap: Max total borrow (whole tokens)
  - borrowing_enabled: Allow borrow operations
  - flashloan_enabled: Allow flash loans
- **Effect**: Creates ReserveData with initial indices (1.0) and zero rates
- **Events**: `ReserveInitialized`

#### Factory Deployment

```rust
deploy_and_init_reserve(
    env: Env,
    caller: Address,
    underlying_asset: Address,
    interest_rate_strategy: Address,
    treasury: Address,
    a_token_name: String,
    a_token_symbol: String,
    debt_token_name: String,
    debt_token_symbol: String,
    params: InitReserveParams,
) -> Result<(Address, Address), KineticRouterError>
```

- **Purpose**: Deploy aToken and debt token, then initialize reserve
- **Prerequisites**: WASM hashes must be pre-stored
- **Deployment**:
  - Create aToken contract with unique address
  - Create debt token contract with unique address
  - Register both in reserve
- **Returns**: Tuple of (aToken address, debt token address)

#### Collateral Configuration

```rust
configure_reserve_as_collateral(
    env: Env,
    caller: Address,
    asset: Address,
    ltv: u32,
    liquidation_threshold: u32,
    liquidation_bonus: u32,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Set/update collateral parameters
- **Auth Required**: Pool admin
- **Validations**:
  - ltv ≤ liquidation_threshold - 50 bps
  - liquidation_threshold ≤ 10000 bps
  - All values ≤ 16384 (14-bit limit in bitmap)
- **Effect**: Updates ReserveConfiguration bitmap
- **Events**: `CollateralConfigurationChanged`

#### Borrowing Enablement

```rust
enable_borrowing_on_reserve(
    env: Env,
    caller: Address,
    asset: Address,
    stable_rate_enabled: bool,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Enable/disable borrowing for asset
- **Auth Required**: Pool admin
- **Effect**: Sets borrowing_enabled bit and stable_rate_enabled bit in config
- **Note**: Stable rates not implemented (reserved for future)

#### Reserve Active/Freeze/Pause States

```rust
set_reserve_active(env: Env, caller: Address, asset: Address, active: bool)
set_reserve_freeze(env: Env, caller: Address, asset: Address, freeze: bool)
set_reserve_pause(env: Env, caller: Address, asset: Address, paused: bool)
```

- **Purpose**: Lifecycle management
- **Active**: Controls reserve participation in protocol
- **Freeze**: Prevents new supply/borrow (wind-down state)
- **Pause**: Emergency stop for all operations (M-04)
- **Auth Required**: Pool admin (with emergency_admin override for pause)

#### Interest Rate Strategy

```rust
set_reserve_interest_rate(
    env: Env,
    caller: Address,
    asset: Address,
    rate_strategy: Address,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Update interest rate strategy contract
- **Auth Required**: Pool admin
- **Effect**: Changes which contract calculates rates
- **Timing**: Becomes effective on next interest accrual

#### Reserve Factor

```rust
set_reserve_factor(
    env: Env,
    caller: Address,
    asset: Address,
    reserve_factor: u32,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Adjust protocol fee percentage
- **Auth Required**: Pool admin
- **Validation**: ≤ 10000 bps
- **Effect**: Changes treasury fee allocation
- **Timing**: Effective on next interest accrual

#### Access Control Configuration

> **Note**: These functions are on the **Kinetic Router**, not the Pool Configurator.

```rust
set_reserve_whitelist(env: Env, asset: Address, whitelist: Vec<Address>)
set_reserve_blacklist(env: Env, asset: Address, blacklist: Vec<Address>)
set_liquidation_whitelist(env: Env, whitelist: Vec<Address>)
set_liquidation_blacklist(env: Env, blacklist: Vec<Address>)
```

- **Purpose**: Restrict or grant access to operations
- **Whitelist**: If non-empty, ONLY listed addresses allowed (M-01)
- **Blacklist**: If non-empty, listed addresses BLOCKED (M-01)
- **Use Cases**:
  - Whitelist: Private pools, KYC compliance
  - Blacklist: Sanctioned addresses, remediation
- **Auth Required**: Pool admin

#### WASM Hash Storage

```rust
set_a_token_wasm_hash(env: Env, caller: Address, hash: BytesN<32>)
set_debt_token_wasm_hash(env: Env, caller: Address, hash: BytesN<32>)
```

- **Purpose**: Store WASM code hashes for factory deployment
- **Auth Required**: Pool admin
- **Usage**: Referenced by factory when deploying new instances
- **Events**: Emits hash update for off-chain indexing

### Storage Considerations

**Instance Storage**:
- Pool admin address
- Emergency admin address
- Kinetic router address
- Price oracle address
- aToken WASM hash
- Debt token WASM hash

**Persistent Storage**:
- Reserve data (per asset)
- Reserve configuration (per asset, in ReserveConfiguration bitmap)
- Interest rate strategy address (per asset)

---

## 3. Price Oracle

**Location**: `/contracts/price-oracle/`
**Role**: Centralized price discovery and circuit breaker

### Purpose

The Price Oracle provides asset prices with:
- Reflector (Stellar consensus) as primary feed
- Custom oracle support for external assets (via RedStone)
- Manual override capability for emergency situations
- Circuit breaker (max 20% price change per update)
- Staleness checking (configurable per asset)
- Fallback oracle support
- Multi-asset batch queries

### Core Concepts

**Asset Whitelist**: Assets must be explicitly registered before pricing.
**Custom Oracle**: External oracle contract address can be specified per asset.
**Precision Handling**: Oracle returns prices in its native decimal precision; router converts to WAD via `oracle_to_wad` factor (K-01).

### Key Functions

#### Initialization

```rust
initialize(
    env: Env,
    admin: Address,
    reflector_contract: Address,
    base_currency_address: Address,
    native_xlm_address: Address,
) -> Result<(), OracleError>
```

- **Purpose**: Set up oracle with Reflector as primary source
- **Auth Required**: Admin must sign
- **Parameters**:
  - reflector_contract: Stellar consensus contract
  - base_currency_address: Denomination asset (e.g. XLM)
  - native_xlm_address: Native Stellar Lumens
- **Effect**: Initializes price cache and settings
- **Idempotency**: Fails if already initialized

#### Asset Whitelist Management

```rust
add_asset(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError>
remove_asset(env: Env, caller: Address, asset: Asset) -> Result<(), OracleError>
```

- **Purpose**: Register/unregister assets for pricing
- **Auth Required**: Admin
- **Asset Type**:
  - `Asset::Stellar(Address)` for SEP-41 tokens
  - `Asset::Other(Symbol)` for external assets
- **Effect**: Add/remove from whitelist; clearing removes cached prices (M-07)

#### Price Queries

```rust
get_asset_price(
    env: Env,
    asset: Asset,
) -> Result<PriceData, OracleError>
```

- **Purpose**: Get single asset price
- **Returns**: `PriceData { price: u128, timestamp: u64 }`
- **Flow**:
  1. Check asset whitelisted
  2. Check manual override (if set and not expired)
  3. Validate circuit breaker (M-05)
  4. Query custom oracle (if configured) or Reflector
  5. Validate staleness (per-asset max age)
  6. Cache result with timestamp
- **Staleness Check**: Default 3600 seconds (1 hour), configurable (M-07)
- **Circuit Breaker**: Max 20% change from last price, rounded up

```rust
get_asset_prices_vec(
    env: Env,
    assets: Vec<Asset>,
) -> Result<Vec<PriceData>, OracleError>
```

- **Purpose**: Batch query multiple assets (optimization)
- **Returns**: Vec of PriceData in same order as input
- **Effect**: Single Reflector call instead of per-asset
- **Efficiency**: Used by liquidation to fetch both prices atomically

#### Manual Override (Emergency)

```rust
set_manual_override(
    env: Env,
    caller: Address,
    asset: Asset,
    price: Option<u128>,
    expiry_timestamp: Option<u64>,
) -> Result<(), OracleError>
```

- **Purpose**: Set emergency price when feeds fail
- **Auth Required**: Admin
- **Validations**:
  - Expiry timestamp in future
  - Duration ≤ 7 days (L-04 max override duration)
  - Circuit breaker still applied (M-05)
- **Effect**: Sets override_price, override_expiry, and override_set_timestamp (H-01)
- **None for price**: Removes override
- **Events**: `ManualOverrideSet` or `ManualOverrideRemoved`

#### Custom Oracle Setup

```rust
set_custom_oracle(
    env: Env,
    caller: Address,
    asset: Asset,
    oracle_address: Address,
    max_age: u64,
) -> Result<(), OracleError>
```

- **Purpose**: Route asset to external oracle
- **Auth Required**: Admin
- **Usage**: For assets priced by RedStone or other custom sources
- **max_age**: Staleness threshold for that oracle (in seconds)
- **Effect**: Next price query uses oracle_address instead of Reflector

#### Price Freshness Validation

Internal function used by liquidation:

```rust
validate_price_freshness(
    env: &Env,
    timestamp: u64,
    asset: Option<&Address>,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Ensure price isn't stale (N-04, M-07)
- **Max Age**: Configurable per asset, defaults to 3600 seconds (1 hour)
- **Circuit Breaker Validation**:
  - Retrieves last cached price
  - Ensures new price doesn't jump > 20%
  - Validates circuit breaker (M-05, O-02)

### Storage Considerations

**Instance Storage**:
- Admin address
- Reflector contract address
- Base currency (usually XLM)
- Native XLM address
- Protocol pause flag
- Fallback oracle address (optional)

**Persistent Storage**:
- Asset whitelist (map of Asset  -> AssetConfig)
- Asset list (ordered Vec for iteration)
- Last prices cache (map of Asset  -> PriceData)
- Reflector precision (cached once at init)
- Configuration per asset:
  - enabled: bool
  - manual_override_price: Option<u128>
  - override_expiry_timestamp: Option<u64>
  - override_set_timestamp: Option<u64> (H-01)
  - custom_oracle: Option<Address>
  - custom_oracle_max_age: Option<u64>

---

## 4. Interest Rate Strategy

**Location**: `/contracts/interest-rate-strategy/`
**Role**: Parameterized interest rate calculation

### Purpose

Calculates borrow and supply interest rates based on utilization curve. Uses linear piecewise segments similar to Aave V3.

### Rate Curve Model

**Utilization** = Total Borrow / (Total Supply + Available Liquidity)

**Borrow Rate** = Base Rate + Slope₁ × Utilization (if U ≤ Optimal)
**Borrow Rate** = Base Rate + Slope₁ × Optimal + Slope₂ × (U - Optimal) (if U > Optimal)

**Supply Rate** = Borrow Rate × Utilization × (1 - Reserve Factor)

### Key Functions

#### Configuration

```rust
set_params(
    env: Env,
    caller: Address,
    asset: Address,
    params: InterestRateParams,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Configure rate curve for asset
- **Auth Required**: Pool admin (via Kinetic Router)
- **Parameters**:
  - base_rate: Initial borrowing cost (WAD)
  - slope1: Rate below optimal utilization (WAD)
  - slope2: Rate above optimal utilization (WAD)
  - optimal_utilization: Inflection point (WAD, e.g. 0.8)

#### Rate Calculation

```rust
calculate_interest_rates(
    env: Env,
    asset: Address,
    available_liquidity: u128,
    total_debt: u128,
    total_supply_scaled: u128,
    liquidity_index: u128,
    variable_borrow_index: u128,
    reserve_factor: u32,
) -> Result<CalculatedRates, KineticRouterError>
```

- **Purpose**: Calculate current borrow and supply rates
- **Returns**: `CalculatedRates { current_liquidity_rate, current_variable_borrow_rate }`
- **Flow**:
  1. Calculate utilization: `debt / (debt + liquidity)`
  2. Apply piecewise linear curve
  3. Calculate supply rate based on borrow rate and reserve factor
  4. Return both rates
- **Ray Precision**: All rates in ray format (1e27)

### Storage Considerations

**Persistent Storage**:
- Interest rate parameters per asset (base_rate, slopes, optimal_utilization)
- No global state (parameters per asset)

---

## 5. aToken (Supply Position Token)

**Location**: `/contracts/a-token/`
**Role**: Scalable position representation for supplied assets

### Purpose

aToken represents a user's share of supplied liquidity. Uses scaled balance accounting to handle interest accrual without iterating over all balances.

**Key Innovation**: Scaled balance × liquidity_index = actual balance
- Liquidity index grows with each block due to interest
- Users automatically accrue interest without explicit updates
- O(1) interest calculation instead of O(n)

### Key Functions

#### Balance Queries

```rust
balance(env: Env, id: Address) -> i128
balance_of_with_index(env: Env, id: Address, liquidity_index: u128) -> i128
```

- **Purpose**: Get actual balance (including interest)
- **Formula**: `scaled_balance × liquidity_index / RAY`
- **Rounding**: Floor (conservative for users)
- **Returns**: i128 for SEP-41 compatibility

#### Transfer

```rust
transfer(env: Env, from: Address, to: Address, amount: i128) -> Result<(), TokenError>
```

- **Purpose**: Transfer aToken between users
- **Flow**:
  1. Authorize `from`
  2. Validate amount > 0
  3. Check allowance (if spender ≠ from)
  4. Calculate scaled amounts
  5. Update scaled balances
  6. Emit transfer event
- **Note**: Emits dual events for indexing

#### Mint (Called by Router on Supply)

```rust
mint_scaled(
    env: Env,
    _from: Address,
    to: Address,
    amount: u128,
    liquidity_index: u128,
) -> Result<(bool, i128, i128), TokenError>
```

- **Purpose**: Issue aTokens when user supplies
- **Auth Required**: Called by router only (require_auth on router)
- **Calculation**: `scaled_amount = amount / liquidity_index`
- **Returns**: Tuple of `(is_first_supply, user_new_scaled_balance, total_supply_scaled)`
- **Flow**:
  1. Calculate scaled balance
  2. Mint to user
  3. Emit incentives callback (if configured)
  4. Return is_first_supply flag, updated balances
- **Incentives Integration**: Calls `handle_action()` on incentives contract

#### Burn (Called by Router on Withdraw)

```rust
burn_scaled(
    env: Env,
    _from: Address,
    user: Address,
    amount: u128,
    index: u128,
) -> Result<(bool, i128), TokenError>
```

- **Purpose**: Destroy aTokens when user withdraws
- **Calculation**: `scaled_amount = amount / index`
- **Returns**: Tuple of `(is_balance_zero, total_supply_scaled)`
- **Effect**: Reduces user's scaled balance and total supply
- **Incentives**: Calls incentives callback

#### Transfer Underlying (Called by Router)

```rust
transfer_underlying_to(
    env: Env,
    caller: Address,
    target: Address,
    amount: u128,
) -> bool
```

- **Purpose**: Send underlying asset to recipient (withdrawal)
- **Returns**: `true` on success
- **Effect**: Transfers from aToken contract's underlying balance
- **Security**: Only callable by router (require_auth on caller)

#### Additional Public Functions

```rust
burn_scaled_and_transfer_to(env, caller, from, target, amount, index) -> Result<(bool, i128), TokenError>
```
- **Purpose**: Burn aTokens from `from` and transfer underlying to `target` in one call (used by liquidation)

```rust
transfer_on_liquidation(env, caller, from, to, amount) -> Result<(), TokenError>
```
- **Purpose**: Transfer aTokens between users during liquidation (when `receive_a_token` is true)

```rust
scaled_balance_of(env, id) -> i128
scaled_total_supply(env) -> i128
get_liquidity_index(env) -> u128
get_underlying_asset(env) -> Address
get_pool_address(env) -> Address
set_incentives_contract(env, caller, incentives_contract) -> Result<(), TokenError>
get_incentives_contract(env) -> Address
```
- **Purpose**: Query functions for scaled balances, indices, configuration, and incentives management

### Storage Considerations

**Instance Storage**:
- Underlying asset address (SEP-41 token)
- Reserve address (for callbacks)
- Lending pool (Kinetic Router) address
- Treasury address (not used)
- Incentives contract address (optional)

**Persistent Storage**:
- Scaled balances per user (map)
- Total scaled supply (counter)
- Allowances (map: from  -> spender  -> amount + expiration)

**Invariants**:
- `sum(user_scaled_balances) ≤ total_scaled_supply`
- `actual_supply = total_scaled_supply × liquidity_index / RAY`
- Actual supply ≤ underlying asset balance in aToken contract

---

## 6. Debt Token (Borrow Position Token)

**Location**: `/contracts/debt-token/`
**Role**: Scalable position representation for borrowed assets

### Purpose

Debt token mirrors aToken design but for borrowed amounts. Users cannot transfer debt tokens (borrow positions).

### Key Differences from aToken

- **Non-transferable**: `transfer()` and `transfer_from()` exist for SEP-41 compliance but return `Err(TokenError::UnsupportedOperation)`
- **Mint-only**: Only router can mint (on borrow)
- **Burn-only**: Only router can burn (on repay)
- **No Allowances**: No approval mechanism needed
- **Same Scaling**: Scaled balance × variable_borrow_index = actual debt

### Key Functions

#### Balance Queries

```rust
balance_of(env: Env, id: Address) -> i128
balance_of_with_index(env: Env, id: Address, variable_borrow_index: u128) -> i128
```

- **Purpose**: Get actual debt amount (with accrued interest)
- **Formula**: `scaled_balance × variable_borrow_index / RAY`

#### Mint (Called by Router on Borrow)

```rust
mint_scaled(
    env: Env,
    _from: Address,
    user: Address,
    amount: u128,
    variable_borrow_index: u128,
) -> Result<(bool, i128, i128), TokenError>
```

- **Purpose**: Issue debt tokens when user borrows
- **Calculation**: `scaled_amount = amount / variable_borrow_index`
- **Returns**: Tuple of `(is_first_borrow, user_new_scaled_debt, total_debt_scaled)`

#### Burn (Called by Router on Repay)

```rust
burn_scaled(
    env: Env,
    _from: Address,
    user: Address,
    amount: u128,
    index: u128,
) -> Result<(bool, i128, i128), TokenError>
```

- **Purpose**: Destroy debt tokens when user repays
- **Calculation**: `scaled_amount = amount / index`
- **Returns**: Tuple of `(is_debt_zero, user_new_scaled_debt, total_debt_scaled)`

#### Incentives Integration

- **Internal**: Mint/burn operations call `handle_incentives_action` internally to notify the incentives contract of balance changes
- **Reward Type**: `REWARD_TYPE_BORROW` (1)

### Storage Considerations

**Instance Storage**:
- Underlying asset address (for reference)
- Reserve address (for callbacks)
- Lending pool address
- Incentives contract address

**Persistent Storage**:
- Scaled balances per user
- Total scaled supply (total debt)

---

## 7. Treasury

**Location**: `/contracts/treasury/`
**Role**: Protocol fee collection and management

### Purpose

Collects protocol fees from interest and flash loans. Allows admin to withdraw accumulated fees.

### Collected Fees

1. **Interest Fees**: `accrued_interest × reserve_factor`
2. **Flash Loan Premiums**: 0-100 bps on borrowed amount

> **Note**: Liquidation bonuses go to the liquidator, not the treasury.

### Key Functions

#### Initialization

```rust
initialize(env: Env, admin: Address) -> Result<(), TreasuryError>
```

- **Purpose**: Set treasury admin
- **Auth Required**: Admin must sign
- **Idempotency**: Fails if already initialized

#### Recording Deposits

```rust
deposit(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    from: Address,
) -> Result<(), TreasuryError>
```

- **Purpose**: Record fee receipt
- **Auth Required**: Admin or authorized contract
- **Validations**:
  - Amount > 0
  - Actual contract balance ≥ internal tracking + amount (S-04)
  - Prevents balance fabrication
- **Effect**: Increments internal balance tracking for asset

#### Withdrawals

```rust
withdraw(
    env: Env,
    caller: Address,
    asset: Address,
    amount: u128,
    to: Address,
) -> Result<(), TreasuryError>
```

- **Purpose**: Admin withdraws accumulated fees
- **Auth Required**: Admin
- **Validations**:
  - Internal balance ≥ amount
  - Underlying asset has sufficient liquidity
- **Effect**: Transfers tokens and decrements internal balance

#### Balance Queries

```rust
get_balance(env: Env, asset: Address) -> u128
```

- **Purpose**: Query accumulated fees for asset
- **Returns**: Internal balance tracking (U128)

### Storage Considerations

**Instance Storage**:
- Admin address

**Persistent Storage**:
- Asset balances (map: asset  -> u128)

**Design Note**: Uses internal balance tracking (not contract balance) to separate protocol fees from other holdings.

---

## 8. Incentives

**Location**: `/contracts/incentives/`
**Role**: Reward distribution for supply and borrow positions

### Purpose

Distributes rewards for liquidity provision and borrowing. Uses index-based system for efficient gas usage.

**Key Feature**: Lazy evaluation - rewards only calculated when users interact.

### Core Concepts

**Reward Index**: Tracks cumulative rewards per unit of supply/borrow. User reward = (current_index - user_last_index) × user_balance.

**Dual Incentivization**: Assets can have separate reward emissions for:
- Supply side (aToken holders)
- Borrow side (debt token holders)

**Multiple Reward Tokens**: Each asset can have multiple reward token emissions.

### Key Functions

#### Initialization

```rust
initialize(
    env: Env,
    emission_manager: Address,
    lending_pool: Address,
) -> Result<(), IncentivesError>
```

- **Purpose**: Set up incentives system
- **Auth Required**: None (no `require_auth` call)
- **Parameters**:
  - emission_manager: Can configure rewards
  - lending_pool: Authorized to call handle_action

#### Balance Change Callback

```rust
handle_action(
    env: Env,
    token_address: Address,
    user: Address,
    total_supply: u128,
    user_balance: u128,
    reward_type: u32,
) -> Result<(), IncentivesError>
```

- **Purpose**: Update rewards when aToken/debtToken balance changes
- **Called By**: aToken/debtToken mint_scaled/burn_scaled
- **Auth Required**: token_address (the token contract itself)
- **Flow**:
  1. Skip if no rewards configured for this asset
  2. For each reward token:
     - Calculate new index
     - Update user's pending rewards
     - Store updated user index
- **reward_type**: 0 = supply (aToken), 1 = borrow (debtToken)
- **No-op**: If asset has no configured rewards

#### Reward Configuration

```rust
configure_asset_rewards(
    env: Env,
    caller: Address,
    asset: Address,
    reward_token: Address,
    reward_type: u32,
    emission_per_second: u128,
    end_timestamp: u64,
) -> Result<(), IncentivesError>
```

- **Purpose**: Set up reward emission for asset
- **Auth Required**: Emission manager
- **Parameters**:
  - emission_per_second: Tokens per second to distribute
  - end_timestamp: When emissions stop
- **Effect**: Creates or updates reward configuration

#### Reward Claims

```rust
claim_rewards(
    env: Env,
    caller: Address,
    assets: Vec<Address>,
    reward_token: Address,
    amount: u128,
    to: Address,
) -> u128
```

- **Purpose**: Claim accumulated rewards for a specific reward token
- **Auth Required**: Caller must sign
- **Returns**: `u128` — actual amount claimed
- **Flow**:
  1. For each asset:
     - Update indices for supply and borrow
     - Accumulate pending rewards
     - Reset pending to zero
  2. Transfer rewards to recipient
  3. Emit claim event
- **M-15 Cap**: Maximum 10 assets per call (prevents out-of-gas)

```rust
claim_all_rewards(
    env: Env,
    caller: Address,
    assets: Vec<Address>,
    to: Address,
)
```

- **Purpose**: Claim all configured rewards
- **M-15**: Capped at 10 assets to prevent unbounded iteration

#### Reward Queries

```rust
get_user_accrued_rewards(
    env: Env,
    asset: Address,
    reward_token: Address,
    user: Address,
    reward_type: u32,
) -> u128
```

- **Purpose**: Query accrued (unclaimed) rewards for a user on a specific asset/reward/type
- **Returns**: Accrued reward amount
- **No State Change**: View function

### Funding Requirements

**CRITICAL**: Contract must be funded with reward tokens before users claim:

```rust
fund_rewards(
    env: Env,
    caller: Address,
    reward_token: Address,
    amount: u128,
) -> Result<(), IncentivesError>
```

- **Purpose**: Deposit reward tokens to contract
- **Auth Required**: Caller must sign (the contract performs `token.transfer(&caller, ...)` internally)
- **Effect**: Transfers tokens from caller to contract and increases available balance for claims
- **Verification**: Internal balance tracking ensures contract solvency

### Storage Considerations

**Instance Storage**:
- Emission manager address
- Lending pool address
- Initialized flag

**Persistent Storage**:
- Reward configurations (per asset, per reward token)
  - emission_per_second
  - end_timestamp
  - current_index
  - last_update_timestamp
- User reward state (per user, per asset, per reward token)
  - user_index
  - pending_rewards
- Reward token balances (for funding)

---

## 9. RedStone Adapter

**Location**: `/contracts/redstone-adapter/`
**Role**: External price feed integration via RedStone

### Purpose

Provides prices for assets not available on Stellar consensus. Integrates with RedStone protocol for bringing off-chain prices (BTC, ETH, etc.) into Stellar.

### Key Concepts

**Payload**: Signed RedStone data bundle containing multiple price feeds and timestamps.
**Feed ID**: Human-readable identifier (e.g., "BTC", "ETH:USD").
**Verification**: Cryptographic proof that updater is authorized and data is fresh.

### Key Functions

#### Initialization

```rust
init(env: &Env, owner: Address) -> Result<(), Error>
```

- **Purpose**: Set owner address
- **Owner**: Can update owner, upgrade contract, write prices

#### Write Prices

```rust
write_prices(
    env: &Env,
    updater: Address,
    feed_ids: Vec<String>,
    payload: Bytes,
) -> Result<(), Error>
```

- **Purpose**: Store prices from RedStone payload
- **Auth Required**: updater.require_auth()
- **Updater Verification**: Must be in trusted updaters list
- **Flow**:
  1. Parse RedStone payload
  2. Verify signature and timestamps
  3. Extract prices for requested feed_ids
  4. Validate staleness (within DATA_STALENESS window)
  5. Store prices with timestamp
  6. Emit `WritePrices` event
- **TTL Management**: Extends contract TTL

#### Get Prices

```rust
get_prices(
    env: &Env,
    feed_ids: Vec<String>,
    payload: Bytes,
) -> Result<(u64, Vec<U256>), Error>
```

- **Purpose**: Extract prices from payload (view function)
- **Returns**: (timestamp, prices)
- **No State Change**: Pure calculation
- **Usage**: Off-chain verification before write_prices

#### Access Control

```rust
change_owner(env: &Env, new_owner: Address) -> Result<(), Error>
accept_ownership(env: &Env) -> Result<(), Error>
cancel_ownership_transfer(env: &Env) -> Result<(), Error>
```

- **Purpose**: Two-step ownership transfer
- **Prevents Accidental Lock**: New owner must accept

#### Contract Upgrade

```rust
upgrade(env: &Env, new_wasm_hash: BytesN<32>) -> Result<(), Error>
```

- **Purpose**: Upgrade contract code
- **Auth Required**: Owner + Pool Admin (dual-auth, M-02)
- **Usage**: Deploy improvements without redeploying infrastructure

### Integration with Price Oracle

The K2 Price Oracle can be configured to use RedStone adapter:
- Set via `set_custom_oracle(asset, redstone_address, max_age)`
- Oracle queries RedStone for prices
- Prices then flow through circuit breaker and staleness checks

### Storage Considerations

**Instance Storage**:
- Owner address
- Pending owner (for two-step transfer)

**Persistent Storage**:
- Prices per feed_id (map: feed_id  -> U256)
- Price timestamps (map: feed_id  -> u64)

---

## 10. Soroswap Adapter

**Location**: `/contracts/soroswap-swap-adapter/`
**Role**: Integration with Soroswap DEX

### Purpose

Enables liquidation and collateral swapping via Soroswap DEX. Abstracts Soroswap's swap interface.

### Key Functions

#### Initialization

```rust
initialize(env: Env, admin: Address, router: Address, factory: Option<Address>) -> Result<(), Error>
```

- **Purpose**: Configure Soroswap router and factory
- **Auth Required**: admin.require_auth()
- **Idempotency**: Fails if already initialized

#### Swap Execution

```rust
swap_exact_tokens_for_tokens(
    env: Env,
    caller: Address,
    amount_in: u128,
    amount_out_min: u128,
    path: Vec<Address>,
) -> Result<Vec<u128>, Error>
```

- **Purpose**: Swap using Soroswap router
- **Auth Required**: caller
- **Path**: [from_token, to_token] (or multi-hop)
- **Returns**: Amounts received for each step
- **Slippage**: Enforced via amount_out_min
- **Flow**:
  1. Call soroswap router
  2. Decode result
  3. Verify received ≥ amount_out_min
  4. Return actual amounts

#### Get Quote

```rust
get_quote(
    env: Env,
    amount_in: u128,
    path: Vec<Address>,
) -> Result<u128, Error>
```

- **Purpose**: Quote expected output (view function)
- **Returns**: Expected amount_out
- **No State Change**: Read-only query

#### Configuration Updates

```rust
set_router(env: Env, caller: Address, router: Address) -> Result<(), Error>
set_factory(env: Env, caller: Address, factory: Address) -> Result<(), Error>
```

- **Purpose**: Update DEX addresses
- **Auth Required**: Admin (caller.require_auth() + admin check)

### Storage Considerations

**Instance Storage**:
- Admin address
- Soroswap router address
- Soroswap factory address (optional)
- Initialized flag

---

## 11. Aquarius Adapter

**Location**: `/contracts/aquarius-swap-adapter/`
**Role**: Integration with Aquarius DEX (alternative to Soroswap)

### Purpose

Provides alternative swap provider for liquidations and swaps. Follows same interface as Soroswap adapter for interchangeability.

### Key Functions

Similar interface to Soroswap Adapter:
- `initialize(env, admin, router, factory)`
- `swap_exact_tokens_for_tokens(env, caller, amount_in, amount_out_min, path)`
- `get_quote(env, amount_in, path)`
- `set_router(env, caller, router)`

### Storage Considerations

Same as Soroswap Adapter

---

## 12. Flash Liquidation Helper

**Location**: `/contracts/flash-liquidation-helper/`
**Role**: Validation for flash loan liquidation workflows

### Purpose

Stateless validator for two-step liquidation parameters. Ensures collateral amount and debt coverage are valid before flash loan execution.

### Key Function

```rust
validate(
    env: Env,
    params: FlashLiquidationValidationParams,
) -> Result<FlashLiquidationValidationResult, Error>
```

- **Purpose**: Validate flash liquidation parameters
- **Parameters**:
  - collateral_asset: Asset to seize
  - debt_asset: Asset to repay
  - user: Borrower being liquidated
  - debt_to_cover: Amount of debt to repay
  - collateral_amount: Amount of collateral to seize
  - Other oracle and health data
- **Returns**: `FlashLiquidationValidationResult { valid: bool }`
- **No State Change**: Pure validation logic
- **Usage**: Off-chain or in flash loan callback to verify parameters

### Validation Checks

- User HF < 1.0 (undercollateralized)
- Debt to cover ≤ close_factor × total debt (dynamic: 50% or 100%)
- Collateral amount matches expected liquidation calculation
- No bad debt beyond acceptable threshold

### Storage Considerations

None (stateless)

---

## 13. Liquidation Engine

**Location**: `/contracts/liquidation-engine/`
**Role**: Dedicated liquidation calculation and execution

### Purpose

Separates liquidation logic into standalone contract for code clarity and testing. Calculates seizable collateral and validates liquidation prerequisites.

### Key Functions

#### Liquidation Calculation

```rust
calculate_liquidation(
    collateral_price: u128,
    debt_price: u128,
    collateral_balance: u128,
    debt_to_cover: u128,
    liquidation_bonus: u32,
    decimals: u32,
) -> Result<u128, KineticRouterError>
```

- **Purpose**: Calculate collateral to seize for debt repayment
- **Formula**: `collateral_to_seize = (debt_to_cover × debt_price × (1 + bonus)) / collateral_price`
- **Bonus**: e.g. 5-10%, incentivizes liquidators
- **Rounding**: Rounds up to ensure collateral value ≥ debt value
- **Returns**: Scaled amount in collateral's decimals

#### Validation

```rust
validate_liquidation_prerequisites(
    user_health_factor: u128,
    debt_to_cover: u128,
    total_user_debt: u128,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Ensure user is liquidatable
- **HF Check**: HF < 1.0 (expressed in WAD)
- **Close Factor**: debt_to_cover ≤ 50% × total_user_debt
- **Returns**: Error if not liquidatable

### Storage Considerations

None (stateless calculations)

---

## 14. Reserve Logic Module

**Location**: `/contracts/kinetic-router/src/reserve.rs`
**Role**: Reserve state management and initialization

### Purpose

Manages reserve lifecycle:
- Initialization with validation
- Configuration updates
- State transitions (active/freeze/pause)
- Factory deployment

### Key Structures

**ReserveData**:
- liquidity_index: u128 (tracks accrued interest for supplies)
- variable_borrow_index: u128 (tracks accrued interest for borrows)
- current_liquidity_rate: u128 (supply rate)
- current_variable_borrow_rate: u128 (borrow rate)
- last_update_timestamp: u64
- a_token_address: Address
- debt_token_address: Address
- interest_rate_strategy_address: Address
- id: u32 (reserve index, 0-63)

**ReserveConfiguration**: Bit-packed (128 + 128 bits)
- Bits 0-13: LTV
- Bits 14-27: Liquidation threshold
- Bits 28-41: Liquidation bonus
- Bits 42-49: Decimals
- Bit 50: Active
- Bit 51: Frozen
- Bit 52: Borrowing enabled
- Bit 53: Paused
- Bit 56: Flash loan enabled
- Bits 57-70: Reserve factor
- data_high bits 0-63: Borrow cap
- data_high bits 64-127: Supply cap

### Functions

#### Initialize Reserve

Validates all parameters before creating ReserveData:
- LTV ≤ 10000 bps
- Liquidation threshold > LTV + 50 bps (L-04)
- Liquidation bonus ≤ 9999 bps
- Reserve factor ≤ 9999 bps
- Decimals ≤ 38 (prevents overflow)
- Supply/borrow caps ≤ u64::MAX
- 64-reserve hard cap (UserConfiguration)

#### Update Reserve State

```rust
fn update_reserve_state(
    env: &Env,
    asset: &Address,
    current_reserve_data: &ReserveData,
) -> Result<ReserveData, KineticRouterError>
```

- **Purpose**: Accrue interest since last update
- **Flow**:
  1. Calculate time elapsed
  2. Fetch interest rates from strategy
  3. Calculate accrued interest
  4. Update indices
  5. Recalculate rates based on new utilization
  6. Return updated ReserveData
- **Frequency**: Called before every operation affecting reserve state

#### Update Interest Rates

```rust
fn update_interest_rates(
    env: &Env,
    asset: &Address,
    updated_reserve_data: &ReserveData,
) -> Result<(), KineticRouterError>
```

- **Purpose**: Calculate and store new rates
- **Calls**: Interest rate strategy contract
- **Storage**: Updates ReserveData with new rates

### Storage Considerations

**Persistent Storage**:
- Reserve data (per asset)
- Reserve ID counter (0-63 range)
- Reserve configuration (per asset, in bitmap)

---

## 15. User Configuration Module

**Location**: `/contracts/kinetic-router/src/` (validation.rs, operations.rs)
**Role**: Position tracking per user

### Purpose

Tracks which reserves each user interacts with via bit mask. Enables efficient:
- Collateral validation (only check assets user uses)
- Health factor calculation (iterate only active positions)
- Configuration updates (mark/unmark as using collateral)

### UserConfiguration Structure

Bitmap with 64 bits, each representing one reserve:
- Bits 0-63: Reserve usage flags
- `user_config.is_using_as_collateral(reserve_id)`  -> bool
- `user_config.set_using_as_collateral(reserve_id)`  -> updated config
- `user_config.unset_using_as_collateral(reserve_id)`  -> updated config

### Bounds Checking

```rust
validate_reserve_index(reserve_index: u8) -> Result<(), KineticRouterError>
```

- **Check**: reserve_index < 64 (L-14)
- **Prevents**: Bitmap overflow attacks
- **Applied**: When reading/writing user configuration

### Functions

#### Mark Using Reserve

Called during first supply to new asset:

```rust
user_config.set_using_as_collateral(safe_reserve_id(reserve_id))
```

- **Effect**: User marked as using this reserve
- **Safety**: Validates reserve_id < 64 (L-14)

#### Unmark Using Reserve

Called when balance reaches zero:

```rust
user_config.unset_using_as_collateral(safe_reserve_id(reserve_id))
```

- **Effect**: User no longer marked as using
- **Benefit**: Reduces gas in subsequent operations

### Storage Considerations

**Persistent Storage**:
- User configuration bitmap (u64) per user

---

## 16. Operations Module

**Location**: `/contracts/kinetic-router/src/operations.rs`
**Role**: Core supply/borrow/repay/withdraw logic

### Purpose

Implements the complete flow for user operations:
1. Supply (deposit assets)
2. Withdraw (redeem supplied assets)
3. Borrow (draw against collateral)
4. Repay (pay back debt)

### Design Pattern

Each operation:
- Checks authorization (require_auth)
- Validates whitelist/blacklist (M-01)
- Updates reserve state (accrue interest)
- Validates prerequisites
- Executes transfers/position updates
- Updates user configuration
- Recalculates rates
- Returns result with event

### Key Invariants Maintained

**Supply**:
- supply_cap not exceeded
- Caller authorized
- Amount > 0

**Withdraw**:
- User has sufficient balance
- HF ≥ 1.0 after (if borrowing)
- Sufficient liquidity available

**Borrow**:
- Caller has collateral
- HF ≥ 1.0 after borrow
- Asset borrowing enabled
- Borrow cap not exceeded

**Repay**:
- Caller/on_behalf_of authorized
- Amount ≤ total debt
- Sufficient underlying balance

### Gas Optimization

**F-01/F-03**: Reserve data threaded through operations to avoid redundant reads
**NEW-01**: validate_user_can_borrow accepts oracle_to_wad parameter
**NEW-02**: Borrow validation includes oracle factor in HF calculation

---

## 17. Admin Module

**Location**: `/contracts/kinetic-router/src/admin.rs`
**Role**: Administrative operations

### Purpose

Handles administrative functions:
- Parameter updates (premium rates, thresholds)
- DEX router configuration
- Oracle configuration
- Whitelist/blacklist management
- Two-step admin transfers

### Key Functions

#### Parameter Updates

- `set_flash_loan_premium_max()`: Max flash loan fee
- `set_health_factor_liquidation_threshold()`: HF cutoff for liquidation
- `set_min_swap_output_bps()`: Slippage tolerance for swaps
- `set_partial_liquidation_hf_threshold()`: When to allow partial liquidation

#### DEX Configuration

- `set_dex_router()`: Change primary DEX
- `set_dex_factory()`: Change DEX factory address

#### Two-Step Admin Transfer

```rust
begin_admin_transfer(new_admin: Address)
accept_admin_transfer()
```

- **Safety**: Prevents accidental loss of admin rights
- **Flow**: Current admin initiates  -> new admin accepts

### Storage Considerations

**Instance Storage**:
- All admin parameters
- Admin addresses (current and pending)

---

## 18. Emergency Controls

**Location**: `/contracts/kinetic-router/src/emergency.rs`
**Role**: Rapid incident response

### Purpose

Provides emergency pause mechanisms for quick response to discovered vulnerabilities.

### Key Concepts

**Protocol Pause**: Blocks all supply/borrow/repay/withdraw operations
**Per-Asset Pause**: Can pause specific assets while allowing others
**Reserve Freeze**: Prevents new supply/borrow but allows repay/withdraw

### Key Functions

#### Protocol Pause

```rust
pause(env: Env, caller: Address) -> Result<(), KineticRouterError>
```

- **Auth Required**: Emergency admin OR pool admin (M-04)
- **Effect**: Blocks all state-changing operations
- **Use Case**: Discovery of critical vulnerability
- **Reversibility**: Pool admin can unpause

#### Unpause

```rust
unpause(env: Env, caller: Address) -> Result<(), KineticRouterError>
```

- **Auth Required**: Pool admin only (M-04, two-step)
- **Effect**: Resumes normal operations
- **Note**: Emergency admin cannot unpause (prevents abuse)

#### Per-Asset Pause

```rust
set_reserve_pause(env: Env, asset: Address, paused: bool)
```

- **Purpose**: Pause specific asset
- **Use Case**: Single-asset issue (e.g., oracle failure)
- **Effect**: That asset cannot be used for supply/borrow

#### Per-Asset Freeze

```rust
set_reserve_freeze(env: Env, asset: Address, freeze: bool)
```

- **Purpose**: Prevent new supply/borrow
- **Effect**: Users can repay/withdraw but not increase positions
- **Use Case**: Graceful asset deprecation

### Pause State Validation

Every operation checks pause state:

```rust
if storage::is_paused(env) {
    return Err(KineticRouterError::AssetPaused);
}
```

Also per-asset:

```rust
if reserve_data.configuration.is_paused() {
    return Err(KineticRouterError::AssetPaused);
}
```

### Storage Considerations

**Instance Storage**:
- Protocol pause flag

**Persistent Storage**:
- Per-asset pause flag (in ReserveConfiguration bitmap)
- Per-asset freeze flag (in ReserveConfiguration bitmap)

---

## Cross-Component Interactions

### Supply Flow

```
**Supply Flow**:
1. User → Kinetic Router (supply)
2. Validation (whitelist/blacklist)
3. Reserve Logic (update_state)
4. Interest Rate Strategy (calculate_rates)
5. Underlying Asset (transfer_from)
6. aToken (mint_scaled)
   - Incentives (handle_action)
   - Event emission
7. User Configuration (mark_using)
8. Price Oracle (optional, for rate calc)
```

### Borrow Flow

**Borrow Flow**:
1. User → Kinetic Router (borrow)
2. Validation (whitelist/blacklist, collateral check)
3. Reserve Logic (update_state)
4. Price Oracle (get_asset_prices_vec)
   - Reflector (if native asset)
   - RedStone Adapter (if external)
5. Calculation (HF check with oracle_to_wad)
6. Debt Token (mint_scaled)
   - Incentives (handle_action)
   - Event emission
7. Underlying Asset (transfer)
8. User Configuration (mark_using)

### Liquidation Flow

**Liquidation Flow**:
1. Liquidator → Kinetic Router (liquidation_call)
2. Validation (liquidation whitelist)
3. Price Oracle (get_asset_prices_vec for both assets)
4. Liquidation Engine (calculate_liquidation)
5. Reserve Logic (update_state)
6. Close Factor Validation (dynamic: 50% or 100%)
7. Debt Token (burn_scaled from user)
8. Underlying Asset (transfer_from liquidator)
9. aToken (burn or transfer collateral)
   - Bad Debt Socialization (H-05)
   - Incentives (handle_action)
10. Treasury (deposit fee if applicable)
11. Event emission

### Flash Loan + Liquidation

**Flash Loan + Liquidation Flow**:
1. Liquidator → Kinetic Router (flash_loan)
2. Validation (asset enabled, amount)
3. Underlying Asset (transfer amount)
4. Receiver Contract (execute_operation callback)
   - Usually calls execute_liquidation
5. Underlying Asset (transfer back amount + premium)
6. Treasury (deposit premium)

---

## Performance Considerations

### Storage Optimization (F-series)

- **F-01/F-03**: Thread reserve data to avoid redundant reads
- **F-02**: Cache oracle config in instance storage
- **F-04**: Centralize TTL extension to entry points
- **F-05**: Inline flash loan validation
- **NEW-01/NEW-02**: Thread oracle_to_wad through calculations
- **F-18/NEW-04/05**: Use bitmap iteration for view functions (O(active) not O(all))

### Ledger Operation Limits

Soroban: 40 reads, 25 writes per transaction

K2 accounts for this in:
- Batched state updates (combine multiple changes)
- Deferred updates (e.g., interest rates calculated once, stored once)
- Persistent vs instance storage decisions

---

## Upgrade Mechanisms

All contracts support:

```rust
pub fn upgrade(env: Env, new_wasm_hash: BytesN<32>) -> Result<(), KineticRouterError>
```

- **Auth Required**: Upgrade admin (set via `upgrade::initialize_admin`)
- **Effect**: Replaces contract code
- **Safety**: New code must implement same interface
- **State Preservation**: All persistent data preserved

Upgrade admin is set to pool admin on initialization.

---

## Summary

K2 consists of 18 interconnected components:

**Core** (5): Kinetic Router, Pool Configurator, Price Oracle, Interest Rate Strategy, Reserve Logic
**Tokens** (2): aToken, Debt Token
**Supporting** (4): Treasury, Incentives, User Configuration, Operations
**External Integrations** (3): RedStone Adapter, Soroswap Adapter, Aquarius Adapter
**Helpers** (2): Flash Liquidation Helper, Liquidation Engine
**Admin** (1): Emergency Controls
**Framework** (1): Admin Module

Each component enforces invariants, validates inputs, and maintains protocol security. Security audit findings (H-01 through H-05, M-01 through M-15, L-01 through L-14) are integrated throughout.

See [Execution Flows](05-FLOWS.md) for detailed operation sequences and [Storage Architecture](10-STORAGE.md) for persistent state design.
