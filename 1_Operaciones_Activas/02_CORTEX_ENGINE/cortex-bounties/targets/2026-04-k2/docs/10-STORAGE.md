# K2 Lending Protocol - Storage Architecture (10-STORAGE.md)

## Overview

The K2 lending protocol employs Soroban's three-tier storage model to optimize costs, TTL management, and access patterns. Data is classified into three categories:

- **Instance Storage**: Configuration and admin settings; subject to 4MB limit
- **Persistent Storage**: Reserve data, user positions, and whitelist/blacklist lists
- **Temporary Storage**: Authorization tokens and callback parameters (5-10 minutes TTL)

All storage keys extend their TTL automatically when read or written. The protocol uses a **30-day threshold with 365-day renewal** to maintain accessibility across the 6-month Soroban maximum TTL. The incentives contract is an exception, using a **28-day threshold** (4 weeks) to reduce fee overhead from frequent TTL bumps.

---

## Storage Types and Tiers

### Instance Storage
- **Scope**: Contract-level configuration valid across all users and reserves
- **Accessed via**: `env.storage().instance()`
- **TTL**: Actively renewed; extends to 365 days when threshold crossed
- **Limit**: 4MB per contract instance (shared with all keys)
- **Examples**: Admin addresses, oracle address, flash loan premiums, paused flag, swap router addresses

### Persistent Storage
- **Scope**: Long-term data per reserve, user, or global list
- **Accessed via**: `env.storage().persistent()`
- **TTL**: Actively renewed; extends to 365 days when threshold crossed
- **Cost**: Cheaper than instance (no 4MB limit)
- **Examples**: ReserveData, UserConfiguration, reserve lists, whitelists, reserve-specific deficit tracking

### Temporary Storage
- **Scope**: Ephemeral data tied to active operations (flash loans, 2-step liquidations)
- **Accessed via**: `env.storage().temporary()`
- **TTL**: 5-10 minutes (300-600 ledgers at ~1 ledger/second)
- **Auto-expiry**: Data automatically purged; no manual cleanup required
- **Examples**: Liquidation authorization, liquidation callback parameters

---

## Soroban TTL Model

All Soroban storage entries have a "time-to-live" (TTL) measured in ledgers. When a ledger number reaches the TTL boundary, the entry is automatically deleted.

### Ledger Math
- **Target block time**: ~5 seconds (network target)
- **Actual variance**: 2-10 seconds (network dependent)
- **Ledgers per day**: ~17,280 (calculated as 86,400 seconds / 5 seconds)
- **6-month maximum**: Soroban enforces 1-year max TTL (~6,307,200 ledgers)

### TTL Extension Mechanics

When data is read or written, Soroban allows extending the TTL:

```rust
env.storage().persistent().extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
// Parameters:
// TTL_THRESHOLD: 30 * 17280 = 518,400 ledgers (30 days)
// TTL_EXTENSION: 365 * 17280 = 6,307,200 ledgers (365 days, the maximum)
```

**Effect**: If remaining TTL is below threshold (30 days), extend to maximum (365 days).

---

## TTL Management Strategy

### Global TTL Constants

```rust
// From kinetic-router/src/storage.rs (also used by a-token, debt-token)
pub const TTL_THRESHOLD: u32 = 30 * 17280;      // 30 days in ledgers
pub const TTL_EXTENSION: u32 = 365 * 17280;     // 1 year in ledgers

// From incentives/src/storage.rs (exception: uses 28-day threshold)
pub const TTL_THRESHOLD: u32 = 28 * 17280;      // 28 days (4 weeks) in ledgers
pub const TTL_EXTENSION: u32 = 365 * 17280;     // 1 year in ledgers
```

### Auto-Renewal on Access

Every public entry point in the protocol extends instance TTL:

```rust
pub fn extend_instance_ttl(env: &Env) {
    env.storage().instance().extend_ttl(TTL_THRESHOLD, TTL_EXTENSION);
}
```

This is called at the **start of every router entry point** (F-04 optimization) to ensure all instance keys remain available.

### Per-Key Renewal

Persistent keys are renewed when accessed:

```rust
pub fn get_reserve_data(env: &Env, asset: &Address) -> Result<ReserveData, KineticRouterError> {
    let key = (RESERVE_DATA, asset.clone());
    if env.storage().persistent().has(&key) {
        env.storage().persistent().extend_ttl(&key, TTL_THRESHOLD, TTL_EXTENSION);
    }
    env.storage().persistent().get(&key).ok_or(KineticRouterError::ReserveNotFound)
}
```

### Explicit Extension (F-04 Optimization)

TTL renewal is **centralized at router entry points**. All operations within a single user transaction benefit from one `extend_instance_ttl()` call, reducing redundant renewals.

---

## Kinetic Router Storage Keys

The router uses symbolic keys for all instance and persistent data. Keys are designed to fit Soroban's constraint of ≤32 characters for Symbol types.

### Instance Storage Keys (Configuration)
  Symbol | Purpose | Type | Default |
  --------|---------|------|---------|
  `INIT` | Initialization flag | `bool` | `false` |
  `PADMIN` | Pool admin address | `Address` | Required |
  `PPADMIN` | Pending pool admin (2-step transfer) | `Address` | None |
  `EADMIN` | Emergency admin address | `Address` | None |
  `PEADMIN` | Pending emergency admin | `Address` | None |
  `ORACLE` | Price oracle contract | `Address` | Required |
  `ORACFG` | Cached oracle config (F-02) | `OracleConfig` | None |
  `TREASURY` | Protocol treasury address | `Address` | None |
  `PAUSED` | Global pause flag | `bool` | `false` |
  `DEXROUTE` | DEX router address | `Address` | None |
  `DEXFACT` | DEX factory address | `Address` | None |
  `INCENT` | Incentives contract | `Address` | None |
  `FLIQHELP` | Flash liquidation helper | `Address` | None |
  `PCONFIG` | Pool configurator | `Address` | None |

### Instance Storage Keys (Configuration Parameters)
  Symbol | Purpose | Type | Default |
  --------|---------|------|---------|
  `FLPREM` | Flash loan premium (bps) | `u128` | `30` (0.3%) |
  `FLPREMMAX` | Max flash loan premium (bps) | `u128` | `100` (1%) |
  `FLLIQPR` | Flash liquidation premium | `u128` | `0` |
  `HFLIQTH` | HF liquidation threshold | `u128` | `1e18` (1.0 WAD) |
  `MINSWAP` | Min swap output (bps) | `u128` | `9800` (98%) |
  `PLIQHF` | Partial liquidation HF threshold | `u128` | `0.5e18` |
  `PSTALE` | Price staleness threshold (sec) | `u64` | `3600` (1 hour) |
  `ASTALMP` | Per-asset staleness overrides | `Map<Address, u64>` | None |
  `LPTOLBPS` | Liquidation price tolerance (bps) | `u128` | `300` (3%) |

### Instance Storage Keys (Flags and State)
  Symbol | Purpose | Type | Note |
  --------|---------|------|------|
  `FLACTIVE` | Flash loan active (reentrancy guard) | `bool` | `false` |
  `REENTRY` | Protocol locked (reentrancy guard) | `bool` | `false` |
  `LWLF` | Liquidation whitelist exists? | `bool` | Flag to avoid reading empty list |
  `LBLF` | Liquidation blacklist exists? | `bool` | Flag to avoid reading empty list |
  `SWLF` | Swap handler whitelist exists? | `bool` | Flag to avoid reading empty list |
  `RWLMAP` | Reserve whitelist status map | `Map<Address, bool>` | O(1) check per reserve (M-01) |
  `RBLMAP` | Reserve blacklist status map | `Map<Address, bool>` | O(1) check per reserve (M-01) |

### Persistent Storage Keys (Reserve Data)
  Key Pattern | Purpose | Type |
  -------------|---------|------|
  `(RESERVE_DATA, asset)` | Reserve state (rates, indices, config) | `ReserveData` |
  `(RESERVE_DEBT_CEILING, asset)` | Max total debt for reserve | `u128` |
  `(RESERVE_DEFICIT, asset)` | Bad debt amount (from bad debt socialization) | `u128` |
  `(RESERVE_ID_TO_ADDRESS, id)` | Address lookup by reserve ID | `Address` |

### Persistent Storage Keys (User Data)
  Key Pattern | Purpose | Type |
  -------------|---------|------|
  `(USER_CONFIGURATION, user)` | User's 128-bit collateral/borrow bitmap | `UserConfiguration` |

### Persistent Storage Keys (Lists)
  Key | Purpose | Type |
  -----|---------|------|
  `RLIST` | Array of all reserve addresses | `Vec<Address>` |
  `RCOUNT` | Separately stored reserve count (cached for efficiency) | `u32` |
  `NEXTRID` | Next reserve ID counter (0-64) | `u32` |

### Persistent Storage Keys (Access Control)
  Key Pattern | Purpose | Type |
  -------------|---------|------|
  `(WHITELIST, asset)` | Addresses allowed to interact with reserve | `Vec<Address>` |
  `(RESERVE_BLACKLIST, asset)` | Addresses blocked from reserve | `Vec<Address>` |
  `LIQUIDATION_WHITELIST` | Addresses allowed to liquidate | `Vec<Address>` |
  `LIQUIDATION_BLACKLIST` | Addresses blocked from liquidating | `Vec<Address>` |
  `SWAP_HANDLER_WHITELIST` | Addresses allowed as custom swap handlers | `Vec<Address>` |

### Temporary Storage Keys (Operations)
  Key Pattern | Purpose | TTL | Type |
  -------------|---------|-----|------|
  `LIQCB` | Flash loan liquidation callback data | 5-10 min | `LiquidationCallbackParams` |
  `(LIQUIDATION_AUTH, liquidator, user)` | 2-step liquidation authorization | 10 min | `LiquidationAuthorization` |

---

## Reserve Data Storage

### ReserveData Structure

Stored under key `(RESERVE_DATA, asset_address)` in persistent storage.

```rust
#[contracttype]
#[derive(Clone)]
pub struct ReserveData {
    pub liquidity_index: u128,              // RAY (1e27) precision
    pub variable_borrow_index: u128,        // RAY (1e27) precision
    pub current_liquidity_rate: u128,       // RAY per second
    pub current_variable_borrow_rate: u128, // RAY per second
    pub last_update_timestamp: u64,         // Unix timestamp (seconds)
    pub a_token_address: Address,           // aToken contract
    pub debt_token_address: Address,        // Debt token contract
    pub interest_rate_strategy_address: Address,
    pub id: u32,                            // Reserve ID (0-63)
    pub configuration: ReserveConfiguration, // Bitmap (see below)
}
```

### ReserveData Precision Model
  Field | Precision | Meaning | Example |
  -------|-----------|---------|---------|
  `liquidity_index` | RAY (1e27) | Cumulative interest accrual factor for suppliers | `1.05e27` = 5% accrued |
  `variable_borrow_index` | RAY (1e27) | Cumulative interest accrual factor for borrowers | `1.10e27` = 10% accrued |
  `current_liquidity_rate` | RAY per second | Annual rate divided by seconds per year | `1.5851e21` ≈ 5% APY |
  `current_variable_borrow_rate` | RAY per second | Annual rate divided by seconds per year | `3.1709e21` ≈ 10% APY |

### Interest Index Scaling

User balances are "scaled" to the base unit (at initialization when index = RAY):

```
user_balance_in_aTokens = scaled_balance * liquidity_index / RAY
```

This allows all users to earn interest without individual transaction overhead.

### Rate Calculation

Annual percentage rate (e.g., 5% APY) is converted to per-second rate:

```
rate_per_second = annual_rate_ray * seconds_elapsed / seconds_per_year

For 5% APY over 1 second:
  rate_per_second ≈ 5e25 * 1 / 31536000 ≈ 1.5851e18 RAY
```

---

## Reserve Configuration Bitmap

The `ReserveConfiguration` struct packs 128-bit values into two `u128` fields for efficiency.

### data_low Layout (128 bits total)

```
Bits 0-13:      LTV (14 bits) - Loan-to-Value ratio (max 10000 bps)
Bits 14-27:     Liquidation Threshold (14 bits) - HF below this is liquidatable
Bits 28-41:     Liquidation Bonus (14 bits) - Incentive given to liquidators
Bits 42-49:     Decimals (8 bits) - Token decimals (0-18)
Bit 50:         Active (1 bit) - Reserve is active?
Bit 51:         Frozen (1 bit) - Reserve is frozen (no deposits/borrows)?
Bit 52:         Borrowing Enabled (1 bit) - Borrowing allowed?
Bit 53:         Paused (1 bit) - Reserve is paused (emergency)?
Bits 54-55:     Reserved (2 bits) - Future use
Bit 56:         Flashloan Enabled (1 bit) - Flash loans allowed?
Bits 57-70:     Reserve Factor (14 bits) - % of interest to protocol (bps)
Bits 71-102:    Min Remaining Debt (32 bits) - Minimum debt after repay (H-02)
Bits 103-127:   Available (25 bits) - Future expansion
```

### data_high Layout (128 bits total)

```
Bits 0-63:      Borrow Cap (64 bits) - Max total borrow in whole tokens
Bits 64-127:    Supply Cap (64 bits) - Max total supply in whole tokens
```

### Configuration Getter/Setter Pattern

```rust
impl ReserveConfiguration {
    pub fn get_ltv(&self) -> u16 {
        (self.data_low & 0x3FFF) as u16  // Extract bits 0-13
    }

    pub fn set_ltv(&mut self, ltv: u32) -> Result<(), ConfigurationError> {
        if ltv > 10000 {
            return Err(ConfigurationError::InvalidLTV);
        }
        self.data_low &= !0x3FFF;                    // Clear bits 0-13
        self.data_low |= (ltv as u128) & 0x3FFF;    // Set new value
        Ok(())
    }
}
```

### Cap Storage Convention

Borrow and supply caps are stored as **whole tokens**, not smallest units:

```
Stored: 1_000_000 (1M tokens)
To enforce: 1_000_000 * 10^decimals (smallest units)
Example for USDC (6 decimals): 1_000_000 * 10^6 = 10^12 smallest units
```

### Min Remaining Debt (H-02 Fix)

After a borrow repayment, the remaining debt must exceed this threshold:

```
if remaining_debt > 0 && remaining_debt < min_remaining_debt * 10^decimals {
    panic!("Repayment would leave dust debt")
}
```

Stored in bits 71-102 (32-bit field), allowing values up to 4.3 billion tokens.

---

## User Configuration Bitmap

The `UserConfiguration` struct uses a single `u128` field to track each user's positions across up to 64 reserves.

### Bitmap Layout

```
For each reserve ID (0-63):
  Bit 2*i:        Collateral flag (is reserve used as collateral?)
  Bit 2*i + 1:    Borrowing flag (does user owe debt in this reserve?)

Example:
  Reserve 0: bits 0-1 (collateral, borrowing)
  Reserve 1: bits 2-3 (collateral, borrowing)
  Reserve 2: bits 4-5 (collateral, borrowing)
  ...
  Reserve 63: bits 126-127 (collateral, borrowing)
```

### Access Pattern

```rust
impl UserConfiguration {
    pub fn is_using_as_collateral(&self, reserve_index: u8) -> bool {
        let shift = (reserve_index as u32) * 2;
        (self.data >> shift) & 1 == 1
    }

    pub fn is_borrowing(&self, reserve_index: u8) -> bool {
        let shift = (reserve_index as u32) * 2 + 1;
        (self.data >> shift) & 1 == 1
    }
}
```

### Bounds Checking (L-14 Fix)

All operations validate `reserve_index < 64` to prevent bitmap corruption:

```rust
pub fn set_using_as_collateral(&mut self, reserve_index: u8, using: bool) {
    if reserve_index >= 64 { return; }  // Silent no-op if invalid
    // ... bitmap manipulation
}
```

### Iteration Optimization (F-18 / NEW-04)

To iterate over active positions without touching all 64 bits:

```rust
pub fn has_any_borrowing(&self) -> bool {
    // Odd bits (1,3,5...) = borrowing flags
    const BORROW_MASK: u128 = 0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA;
    (self.data & BORROW_MASK) != 0
}
```

This is O(1) instead of O(64).

---

## aToken Contract Storage

Each aToken contract stores its own state separately from the router.

### ATokenState Structure

```rust
#[contracttype]
#[derive(Clone)]
pub struct ATokenState {
    pub underlying_asset: Address,      // The underlying token (USDC, USDT, etc.)
    pub pool_address: Address,          // Kinetic router contract
    pub liquidity_index: u128,          // RAY - synchronized with reserve
    pub last_update_timestamp: u64,     // Last interest accrual time
    pub total_supply_scaled: i128,      // Sum of all user scaled balances
    pub name: String,                   // e.g., "Kinetic USDC"
    pub symbol: String,                 // e.g., "kUSDC"
    pub decimals: u32,                  // Same as underlying
}
```

### Storage Layout

```
Instance Storage:
  DataKey::State           -> ATokenState

Persistent Storage:
  DataKey::Balance(user)   -> i128 (scaled balance)
  DataKey::Allowance(from, spender)  -> AllowanceData
  DataKey::IncentivesContract  -> Address (optional)
```

### Scaled Balance Model

Each aToken balance is stored as a scaled value:

```
actual_balance = scaled_balance * liquidity_index / RAY
```

When `liquidity_index` increases (through interest accrual), all balances grow proportionally without updates.

### AllowanceData

```rust
#[contracttype]
pub struct AllowanceData {
    pub amount: i128,                   // Allowed amount
    pub expiration_ledger: u32,         // When allowance expires (0 = never)
}
```

---

## Debt Token Contract Storage

Debt tokens are **read-only** from the user perspective (cannot transfer or approve).

### DebtTokenState Structure

```rust
#[contracttype]
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DebtTokenState {
    pub borrowed_asset: Address,        // The underlying token
    pub pool_address: Address,          // Kinetic router contract
    pub total_debt_scaled: i128,        // Sum of all user scaled debts
    pub name: String,                   // e.g., "Kinetic Debt USDC"
    pub symbol: String,                 // e.g., "dUSDC"
    pub decimals: u32,                  // Same as underlying
}
```

### Storage Layout

```
Instance Storage:
  DataKey::State           -> DebtTokenState

Persistent Storage:
  DataKey::Debt(user)      -> u128 (scaled debt balance)
  DataKey::IncentivesContract  -> Address (optional)
```

### Scaling Factor

Like aTokens, debts accrue interest through index growth. The borrow index is maintained in the router's `ReserveData`, not in the debt token contract itself:

```
actual_debt = scaled_debt * reserve.variable_borrow_index / RAY
```

---

## Price Cache Storage

The router maintains a **cached oracle configuration** to avoid repeated oracle contract calls.

### Oracle Config Caching (F-02)

```rust
pub fn get_cached_oracle_config(env: &Env) -> Option<k2_shared::OracleConfig> {
    env.storage().instance().get(&ORACLE_CFG)
}

pub fn set_cached_oracle_config(env: &Env, config: &k2_shared::OracleConfig) {
    env.storage().instance().set(&ORACLE_CFG, config);
}

// Cache is invalidated when oracle address changes
pub fn set_price_oracle(env: &Env, oracle: &Address) {
    env.storage().instance().set(&PRICE_ORACLE, oracle);
    if env.storage().instance().has(&ORACLE_CFG) {
        env.storage().instance().remove(&ORACLE_CFG);
    }
}
```

### OracleConfig Structure

```rust
#[contracttype]
pub struct OracleConfig {
    pub price_staleness_threshold: u64,  // Max age (seconds)
    pub price_precision: u32,             // E.g., 14 decimals
    pub wad_precision: u32,               // Always 18
    pub conversion_factor: u128,          // 10^(18 - price_precision)
    pub ltv_precision: u128,              // 1e18
    pub basis_points: u128,               // 10_000
    pub max_price_change_bps: u32,        // Circuit breaker %
}
```

### Per-Asset Staleness Override (M-07)

Each asset can have a custom staleness threshold:

```
ASSET_STALENESS_MAP: Map<Address, u64>
```

If an override exists, use it; otherwise fall back to global threshold.

---

## Liquidation Authorization Storage

The 2-step liquidation flow uses **temporary storage** to pass authorization between steps.

### LiquidationAuthorization Structure

```rust
#[contracttype]
#[derive(Clone)]
pub struct LiquidationAuthorization {
    pub liquidator: Address,            // Who initiated liquidation
    pub user: Address,                  // Who is being liquidated
    pub debt_asset: Address,            // What debt to repay
    pub collateral_asset: Address,      // What collateral to seize
    pub debt_to_cover: u128,            // Amount to repay
    pub collateral_to_seize: u128,      // Amount to seize
    pub min_swap_out: u128,             // Min output for slippage protection
    pub debt_price: u128,               // Price at prepare time (validated)
    pub collateral_price: u128,         // Price at prepare time (validated)
    pub health_factor_at_prepare: u128, // HF at prepare time (WAD-precision)
    pub expires_at: u64,                // Expiry timestamp
    pub nonce: u64,                     // Replay attack prevention
    pub swap_handler: Option<Address>,  // Optional custom DEX handler
}
```

### Storage and TTL

```rust
pub fn set_liquidation_authorization(
    env: &Env,
    liquidator: &Address,
    user: &Address,
    auth: &LiquidationAuthorization,
) {
    let key = (LIQUIDATION_AUTH, liquidator.clone(), user.clone());
    env.storage().temporary().set(&key, auth);
    // Stored for 10 minutes (~600 ledgers) with early extension at 400
    env.storage().temporary().extend_ttl(&key, 400, 600);
}
```

### Nonce Tracking

```rust
pub fn get_and_increment_liquidation_nonce(env: &Env) -> u64 {
    let current_nonce: u64 = env.storage().instance().get(&LIQUIDATION_AUTH_NONCE).unwrap_or(0);
    let next_nonce = current_nonce.checked_add(1).unwrap_or_else(|| {
        panic_with_error!(env, KineticRouterError::MathOverflow)
    });
    env.storage().instance().set(&LIQUIDATION_AUTH_NONCE, &next_nonce);
    current_nonce
}
```

Each `prepare_liquidation` call increments a protocol-wide nonce. The authorization nonce is embedded and validated during execution.

---

## Whitelist and Blacklist Storage

The protocol supports three independent access control lists.

### 1. Reserve Whitelists

**Purpose**: Restrict which addresses can deposit/borrow a specific reserve asset.

```rust
// Key: (WHITELIST, asset_address)
// Value: Vec<Address>

pub fn get_reserve_whitelist(env: &Env, asset: &Address) -> Vec<Address> {
    // ... fetch from persistent storage
}

pub fn is_address_whitelisted_for_reserve(
    env: &Env,
    asset: &Address,
    address: &Address,
) -> bool {
    // Empty whitelist = open access
    // Non-empty whitelist = only listed addresses allowed
}
```

**Optimization (M-01)**: A consolidated Map in instance storage tracks which reserves have whitelists:

```
RWLMAP: Map<Address, bool>
```

This allows O(1) check without fetching the entire list.

### 2. Reserve Blacklists

**Purpose**: Block specific addresses from interacting with a reserve.

```rust
// Key: (RESERVE_BLACKLIST, asset_address)
// Value: Vec<Address>

pub fn get_reserve_blacklist(env: &Env, asset: &Address) -> Vec<Address>
pub fn is_address_blacklisted_for_reserve(env: &Env, asset: &Address, address: &Address) -> bool
```

**Optimization (M-01)**: Similar Map in instance:

```
RBLMAP: Map<Address, bool>
```

### 3. Liquidation Whitelist

**Purpose**: Restrict liquidation to specific liquidators (e.g., authorized bots).

```rust
// Key: LIQUIDATION_WHITELIST
// Value: Vec<Address>

// Empty whitelist = all can liquidate (default)
// Non-empty whitelist = only listed addresses can liquidate

pub fn is_address_whitelisted_for_liquidation(env: &Env, address: &Address) -> bool
```

### 4. Liquidation Blacklist

**Purpose**: Block specific liquidators from liquidating.

```rust
// Key: LIQUIDATION_BLACKLIST
// Value: Vec<Address>

// Empty blacklist = all can liquidate (default)
// Non-empty blacklist = listed addresses cannot liquidate

pub fn is_address_blacklisted_for_liquidation(env: &Env, address: &Address) -> bool
```

### 5. Swap Handler Whitelist

**Purpose**: Control which DEX adapters can be used (M-01 fix).

```rust
// Key: SWAP_HANDLER_WHITELIST
// Value: Vec<Address>

// Empty whitelist = deny custom handlers (only built-in DEX allowed)
// Non-empty whitelist = only listed handlers allowed

pub fn is_swap_handler_whitelisted(env: &Env, handler: &Address) -> bool
```

---

## User Positions

### aToken Balances

Stored in aToken contract persistent storage:

```
aToken persistent storage:
  DataKey::Balance(user)  -> i128 (scaled balance)

Actual balance = scaled_balance * liquidity_index / RAY
```

Each user's aToken balance represents their claim on the pool's liquidity.

### Debt Token Balances

Stored in debt token contract persistent storage:

```
Debt token persistent storage:
  DataKey::Debt(user)  -> u128 (scaled debt)

Actual debt = scaled_debt * borrow_index / RAY
```

Debt tokens are **read-only** from user perspective. Only the pool can mint/burn.

### Position Discovery

To find all of a user's positions, iterate the `UserConfiguration` bitmap:

```rust
let user_config = get_user_configuration(env, &user);

for reserve_id in 0..MAX_RESERVES {
    if user_config.is_using_as_collateral(reserve_id as u8) {
        // User has collateral in this reserve
    }
    if user_config.is_borrowing(reserve_id as u8) {
        // User has debt in this reserve
    }
}
```

---

## Reserve List

The protocol maintains a linear array of all initialized reserves.

### Storage

```rust
// Key: symbol_short!("RLIST")
// Value: Vec<Address>

pub fn get_reserves_list(env: &Env) -> Vec<Address> {
    env.storage().persistent().get(&RESERVES_LIST).unwrap_or(Vec::new(env))
}

// Key: symbol_short!("RCOUNT") — separately stored, not derived from RESERVES_LIST.len()
// Falls back to RESERVES_LIST.len() for backward compatibility
pub fn get_reserves_count(env: &Env) -> u32 {
    env.storage()
        .persistent()
        .get(&RESERVES_COUNT)
        .unwrap_or_else(|| get_reserves_list(env).len())
}
```

### Reserve ID Mapping

For O(1) lookups, the router also stores a reverse mapping:

```rust
// Key: (RESERVE_ID_TO_ADDRESS, id)
// Value: Address

pub fn get_reserve_address_by_id(env: &Env, id: u32) -> Option<Address> {
    env.storage().persistent().get(&(RESERVE_ID_TO_ADDRESS, id))
}

pub fn set_reserve_address_by_id(env: &Env, id: u32, asset: &Address) {
    env.storage().persistent().set(&(RESERVE_ID_TO_ADDRESS, id), asset);
}
```

### Reserve Initialization

During `init_reserve`:

1. Allocate reserve ID from `NEXT_RESERVE_ID` counter
2. Store address in `(RESERVE_ID_TO_ADDRESS, id)`
3. Create `ReserveData` with initial rates
4. Append to `RESERVES_LIST`
5. Create aToken and debt token contracts

The maximum is 64 reserves (`MAX_RESERVES`).

---

## Interest Indices and Rates

### Index Updates

Interest accrual happens at the **reserve level**. Whenever interest is calculated, the indices are updated:

```rust
pub struct ReserveData {
    pub liquidity_index: u128,          // RAY precision
    pub variable_borrow_index: u128,    // RAY precision
    pub current_liquidity_rate: u128,   // RAY per second
    pub current_variable_borrow_rate: u128,
    pub last_update_timestamp: u64,
}
```

### Accrual Calculation

New index = old index × (1 + rate × time_elapsed)

```rust
// Compound interest:
// new_index = old_index * (1 + rate_per_second * seconds_elapsed)^1
// In practice: new_index = old_index * compound_factor
// Where compound_factor ≈ 1 + (rate_per_second * seconds_elapsed / RAY)

let time_delta = current_timestamp - last_update_timestamp;
let interest_factor = calculate_compound_interest(&env, rate, last_update_timestamp, current_timestamp)?;
let new_index = ray_mul(&env, old_index, interest_factor)?;
```

### Current Rates

The current rates are updated whenever interest is accrued:

```
current_liquidity_rate = strategy.calculate_liquidity_rate(...)
current_variable_borrow_rate = strategy.calculate_variable_borrow_rate(...)
```

These are stored in `ReserveData` and can be queried by users without calculating.

---

## Timestamp Tracking

Each reserve records the **last ledger timestamp** when interest was accrued:

```rust
pub fn update_reserve_state(
    env: &Env,
    asset: &Address,
) -> Result<ReserveData, KineticRouterError> {
    let mut reserve_data = get_reserve_data(env, asset)?;
    let current_timestamp = env.ledger().timestamp();

    if current_timestamp > reserve_data.last_update_timestamp {
        // Interest accrual needed
        let interest_factor = calculate_compound_interest(
            &env,
            reserve_data.current_liquidity_rate,
            reserve_data.last_update_timestamp,
            current_timestamp,
        )?;
        reserve_data.liquidity_index = ray_mul(&env, reserve_data.liquidity_index, interest_factor)?;
        // ... similar for borrow index

        reserve_data.last_update_timestamp = current_timestamp;
    }

    set_reserve_data(env, asset, &reserve_data);
    Ok(reserve_data)
}
```

---

## Scaling Factors

### Why Scaled Balances?

Without scaling, every interest accrual would require updating millions of individual user balances. Instead:

**Scaled Model**:
- Store `user_balance_scaled` (constant per user unless deposit/withdraw)
- Store `reserve_index` (updated per interest accrual)
- Calculate actual balance on-the-fly: `balance = scaled_balance * index / RAY`

### Example

User deposits 1000 USDC when `liquidity_index = 1e27`:

```
scaled_balance = 1000 * 10^6 * RAY / liquidity_index
               = 1000 * 10^6 * 1e27 / 1e27
               = 1000 * 10^6 (unchanged if index starts at RAY)
```

After 1 year with 5% interest, `liquidity_index = 1.05e27`:

```
actual_balance = scaled_balance * liquidity_index / RAY
               = 1000 * 10^6 * 1.05e27 / 1e27
               = 1050 * 10^6 (user earned 50 USDC interest)
```

The user never checked in, the balance just grew!

---

## Efficiency Considerations

### 1. Why Bitmaps?

**UserConfiguration** and **ReserveConfiguration** use bit-packing instead of separate storage entries:
  Approach | Instance Entries | Storage Reads |
  ----------|-----------------|---------------|
  Bitmap (current) | 1 per user | 1 read for all 64 positions |
  Separate (alternative) | 128 per user (64 collateral + 64 borrow) | 128 reads to check all positions |

**Savings**: 127× fewer reads per health factor calculation.

### 2. Why Scaled Balances?

**Scaled Model** (current):
- Storage: 1 aToken balance per user (persistent)
- Updates: Only on deposit/withdraw
- Interest: Calculated on-the-fly from `user_balance * index / RAY`

**Alternative (no scaling)**:
- Storage: 1 aToken balance per user
- Updates: Every interest accrual requires updating all balances
- Cost: O(users) per accrual, prohibitively expensive

### 3. Why Consolidated Whitelists?

**Old Approach** (M-01 fix):
```
Instance: (LIQ_WHITELIST_FLAG, LIQUIDATION_WHITELIST_0, LIQUIDATION_WHITELIST_1, ...)
```
Result: Up to 2×(N reserves) instance entries, hitting 4MB limit.

**New Approach**:
```
Instance: LIQ_WHITELIST_FLAG + one Map<Address, bool>
Persistent: (WHITELIST, asset)  -> Vec<Address>
```
Result: 2 instance entries + N persistent entries (much cheaper).

### 4. TTL Extension at Entry Points (F-04)

Instead of extending TTL on every storage access:

**Before**: Call `extend_ttl()` in 20+ helper functions
**After**: Call `extend_instance_ttl()` once at router entry point

Result: ~20× fewer extension operations per transaction.

### 5. Oracle Config Caching (F-02)

Instead of calling oracle contract to fetch config every operation:

**Before**: `get_oracle_config()`  -> external call (expensive)
**After**: Fetch once, cache in instance, validate on oracle change

Result: Elimination of 10+ oracle contract calls per operation.

---

## Data Structure Diagrams

### Storage Hierarchy

```
Kinetic Router Contract
- Instance Storage (4MB shared limit)
   Admin: PADMIN, EADMIN, PENDING_...
   Configuration: ORACLE, TREASURY, DEXROUTE, ...
   Parameters: FLPREM, HFLIQTH, MINSWAP, ...
   Flags: PAUSED, FLACTIVE, REENTRY
   Consolidated Lists: RWLMAP, RBLMAP (Map<Address, bool>)
   Nonce: LIQUIDATION_AUTH_NONCE
   Cache: ORACLE_CFG (OracleConfig)
  - Persistent Storage (unlimited)
   Reserves: (RESERVE_DATA, asset)  -> ReserveData
   Reserve Deficits: (RESERVE_DEFICIT, asset)  -> u128
   User Config: (USER_CONFIGURATION, user)  -> UserConfiguration
   Lists: RLIST (reserves), RCOUNT (cached count), NEXT_RESERVE_ID
   Mappings: (RESERVE_ID_TO_ADDRESS, id)  -> Address
   Whitelists: (WHITELIST, asset)  -> Vec<Address>
   Blacklists: (RESERVE_BLACKLIST, asset)  -> Vec<Address>
   Global Lists: LIQUIDATION_WHITELIST, LIQUIDATION_BLACKLIST, SWAP_HANDLER_WHITELIST
  - Temporary Storage (5-10 min TTL)
- Liquidation Authorization: (LIQUIDATION_AUTH, liquidator, user)  -> LiquidationAuthorization
- Liquidation Callback: LIQCB  -> LiquidationCallbackParams

aToken Contract
- Instance Storage
   State: DataKey::State  -> ATokenState
   Cache: DataKey::IncentivesContract  -> Address
  - Persistent Storage
- Balances: DataKey::Balance(user)  -> i128 (scaled)
- Allowances: DataKey::Allowance(from, spender)  -> AllowanceData

Debt Token Contract
- Instance Storage
   State: DataKey::State  -> DebtTokenState
   Cache: DataKey::IncentivesContract  -> Address
  - Persistent Storage
- Debts: DataKey::Debt(user)  -> u128 (scaled)
```

### ReserveConfiguration Bitmap

**data_low (128 bits)**:
  Bits | Field | Description |
  ------|-------|-------------|
  13-0 | LTV | Loan-to-value ratio (basis points) |
  27-14 | LiqThr | Liquidation threshold (basis points) |
  41-28 | LiqBon | Liquidation bonus (basis points) |
  49-42 | Decimal | Token decimal places (0-18) |
  50 | Act | Reserve is active |
  51 | Froz | Reserve is frozen |
  52 | Borr | Borrowing enabled |
  53 | Pause | Reserve is paused |
  55-54 | Reserved | (unused) |
  56 | FL | Flash loan enabled |
  70-57 | Factor | Min remaining debt (dust threshold) |
  102-71 | MinDebt | Minimum debt amount |
  127-103 | Reserved | (unused) |

**data_high (128 bits)**:
  Bits | Field | Description |
  ------|-------|-------------|
  63-0 | Borrow Cap | Maximum borrowable amount (u64) |
  127-64 | Supply Cap | Maximum supply amount (u64) |

### UserConfiguration Bitmap

**Format**: 128-bit integer representing 64 reserves (2 bits per reserve)

For each reserve `i` (0 to 63):
- **Bit 2*i**: Collateral flag (user using as collateral)
- **Bit 2*i+1**: Borrowing flag (user borrowing from this reserve)

**Layout**:

```
Bit:  127 126  125 124  ...  3   2    1   0
      [ Reserve 63 ][ Reserve 62 ]...[ Reserve 1 ][ Reserve 0 ]
      [ Br   Co ]  [ Br   Co ]      [ Br  Co ]  [ Br  Co ]
```

**Example**:
- Reserve 0 using as collateral: bit 0 set (value = 1)
- Reserve 0 borrowing: bit 1 set (value = 2)
- Reserve 0 both: bits 0 & 1 set (value = 3)

---

## Access Patterns

### Reading Reserve Data

```
1. Get reserve address (known or from RESERVES_LIST)
2. Call get_reserve_data(env, &asset)
    Fetches (RESERVE_DATA, asset) from persistent storage
    Auto-extends TTL if below threshold
3. If outdated, call update_reserve_state() to accrue interest
4. Read specific fields: liquidity_index, variable_borrow_index, rates, etc.
```

### Updating User Position

```
Deposit 100 USDC:
1. Get user's UserConfiguration bitmap
2. Mark reserve as collateral: user_config.set_using_as_collateral(reserve_id, true)
3. Get user's current scaled balance from aToken
4. Fetch reserve's liquidity_index
5. Calculate: new_scaled_balance = user_scaled_balance + (100 * 10^decimals * RAY / liquidity_index)
6. Write new scaled balance to aToken persistent storage
7. Update reserve data (supply amount, etc.)
```

### Health Factor Calculation

```
1. Get user's UserConfiguration
2. For each reserve marked as collateral:
   a. Get reserve data (cached if possible)
   b. Get user's aToken balance
   c. Get oracle price
   d. Calculate: collateral_value = balance * price * oracle_to_wad / 10^decimals
3. For each reserve marked as borrowing:
   a. Get debt token balance
   b. Get oracle price
   c. Calculate: debt_value = debt * price * oracle_to_wad / 10^decimals
4. Get reserve's liquidation_threshold from config
5. Calculate: HF = (total_collateral * threshold * WAD) / (total_debt * 10000)
```

### Liquidation Flow (2-step)

**Step 1 - Prepare**:
```
1. Validate user is liquidatable (HF < 1.0)
2. Calculate collateral to seize and debt to cover
3. Get current prices for both assets
4. Create LiquidationAuthorization struct
5. Store in temporary storage with 10-minute TTL
6. Increment nonce for replay prevention
```

**Step 2 - Execute**:
```
1. Fetch LiquidationAuthorization from temporary storage (auto-expired if stale)
2. Validate nonce hasn't changed
3. Validate prices haven't changed more than tolerance allows
4. Transfer collateral from user to liquidator
5. Transfer debt repayment from liquidator to protocol
6. Remove LiquidationAuthorization
```

---

## Storage Examples

### Example 1: Reserve Data Storage

```rust
// Store reserve data for USDC
let usdc_reserve = ReserveData {
    liquidity_index: 1_050_000_000_000_000_000_000_000_000, // 1.05 RAY (5% interest accrued)
    variable_borrow_index: 1_100_000_000_000_000_000_000_000_000, // 1.10 RAY
    current_liquidity_rate: 1_585_490_000_000_000_000, // ~5% APY per second
    current_variable_borrow_rate: 3_170_980_000_000_000_000, // ~10% APY per second
    last_update_timestamp: 1707500000,
    a_token_address: usdc_atoken_addr,
    debt_token_address: usdc_debt_token_addr,
    interest_rate_strategy_address: strategy_addr,
    id: 0,
    configuration: ReserveConfiguration { /* ... */ }
};

storage::set_reserve_data(env, &usdc_address, &usdc_reserve);
// Stored at key: (RESERVE_DATA, usdc_address)
// TTL auto-extended to 365 days
```

### Example 2: User Configuration Update

```rust
// User supplies 100 USDC as collateral
let mut user_config = storage::get_user_configuration(env, &user_address);

// Mark USDC reserve (id=0) as collateral
user_config.set_using_as_collateral(0, true);

storage::set_user_configuration(env, &user_address, &user_config);
// Stored at key: (USER_CONFIGURATION, user_address)
// Value: 128-bit bitmap with bit 0 set to 1

// After borrowing USDT (id=1):
user_config.set_borrowing(1, true);
// Now bits 0=collateral_usdc, 1=empty, 2=empty, 3=borrow_usdt
// Bitmap: 0b1011 = value 11 (first 4 bits shown)
```

### Example 3: aToken Scaled Balance

```rust
// User deposits 1000 USDC when liquidity_index = 1e27
let deposit_amount = 1000 * 1_000_000; // 1000 USDC with 6 decimals
let liquidity_index = 1_000_000_000_000_000_000_000_000_000u128; // 1e27 RAY

let scaled_balance = (deposit_amount * RAY) / liquidity_index;
// = (1_000_000_000_000 * 1e27) / 1e27
// = 1_000_000_000_000

storage::set_scaled_balance(env, &user_address, &scaled_balance);
// Stored at key: DataKey::Balance(user_address)

// One year later, liquidity_index = 1.05e27 (5% interest)
let liquidity_index_later = 1_050_000_000_000_000_000_000_000_000u128;
let actual_balance = (scaled_balance * liquidity_index_later) / RAY;
// = (1_000_000_000_000 * 1.05e27) / 1e27
// = 1_050_000_000_000 (user now has 1050 USDC)
```

### Example 4: Liquidation Authorization

```rust
// Liquidator calls prepare_liquidation
let auth = LiquidationAuthorization {
    liquidator: liquidator_address.clone(),
    user: borrower_address.clone(),
    debt_asset: usdc_address.clone(),
    collateral_asset: eth_address.clone(),
    debt_to_cover: 10_000_000_000, // 10,000 USDC (6 decimals)
    collateral_to_seize: 5_000_000_000_000_000_000, // 5 ETH (18 decimals)
    min_swap_out: 9_800_000_000, // Min 9,800 USDC from swap
    debt_price: 1_000_000_000_000_000, // $1.00 per USDC
    collateral_price: 45_000_000_000_000_000, // $45,000 per ETH
    health_factor_at_prepare: 900_000_000_000_000_000, // 0.9 HF
    expires_at: current_timestamp + 600,
    nonce: 42,
    swap_handler: Some(soroswap_handler.clone()),
};

storage::set_liquidation_authorization(
    env,
    &liquidator_address,
    &borrower_address,
    &auth,
);
// Stored at key: (LIQUIDATION_AUTH, liquidator_address, borrower_address)
// TTL: 10 minutes with early extension at 400 ledgers
```

### Example 5: Whitelist Check (M-01 Optimization)

```rust
// Check if address can interact with USDC reserve
let has_whitelist: bool = env.storage().instance().get(&RESERVE_WL_MAP)
    .ok_or_else(|| Map::new(env))
    .get(usdc_address.clone())
    .unwrap_or(false);

if !has_whitelist {
    // No whitelist configured = open access
    return Ok(());
}

// Whitelist exists, fetch it
let whitelist = storage::get_reserve_whitelist(env, &usdc_address);
let is_allowed = whitelist.iter().any(|addr| addr == &caller);

if !is_allowed {
    return Err(KineticRouterError::Unauthorized);
}
```

---

## Summary Table
  Storage Aspect | Location | Purpose | TTL | Limit |
  ---|---|---|---|---|
  **Admin addresses** | Instance | Access control | 365 days auto-renew | Within 4MB |
  **Reserve data** | Persistent | Rates, indices, config | 365 days auto-renew | Unlimited |
  **User config** | Persistent | Position bitmap | 365 days auto-renew | Unlimited |
  **aToken balances** | Persistent (aToken) | Scaled supply | 365 days auto-renew | Unlimited |
  **Debt balances** | Persistent (DebtToken) | Scaled borrow | 365 days auto-renew | Unlimited |
  **Whitelists** | Persistent | Access control | 365 days auto-renew | Unlimited |
  **Liquidation auth** | Temporary | 2-step flow | 10 minutes | Auto-expiry |
  **Liquidation callback** | Temporary | Flash loan state | 5-10 minutes | Auto-expiry |

---

## References

- **Soroban Storage**: https://soroban.stellar.org/docs/learn/storing-data
- **TTL Management**: Ledger timestamp-based expiry with automatic extension
- **Scaling Factors**: WAD (1e18) and RAY (1e27) precision model
- **Bitmap Packing**: 2-bit per reserve for 64 reserves in 128-bit field

See also:
- **03-CORE-CONCEPTS.md** - Reserve structure, interest models, health factor
- **05-FLOWS.md** - How storage is accessed during supply, borrow, liquidation
