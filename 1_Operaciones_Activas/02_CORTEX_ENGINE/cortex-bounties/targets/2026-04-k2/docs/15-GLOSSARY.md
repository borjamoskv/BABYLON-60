# K2 Lending Protocol - Glossary

Comprehensive terminology reference for K2 lending protocol developers and users.

---

## 1. Core Concepts

### Reserve
A pool of liquidity for a single asset (e.g., USDC reserve). Each reserve tracks:
- Available liquidity (underlying tokens in pool)
- Total variable debt (amount borrowed)
- Interest index (accumulated interest rate)
- Configuration (LTV, liquidation threshold, caps)

### Collateral
Assets supplied to the pool to secure borrowing. Collateral can be liquidated if health factor falls below 1. Each asset has an LTV (loan-to-value) ratio determining max borrowing power.

### Debt / Borrowed Amount
Amount of an asset borrowed from the pool. Borrower must maintain sufficient collateral. Debt accrues interest (variable rate) over time.

### aToken (Collateral Token)
ERC20-like token representing collateral position. When user supplies 100 USDC, they receive ~100 aUSDC. aToken balance earns interest (increases automatically). Transferable (with health factor validation via router's validate_and_finalize_transfer).

**Key Properties:**
- Scales with supply index (tracks accrued interest)
- Transferable with health factor check
- Burned when collateral withdrawn
- Minted proportional to underlying supplied

### Debt Token (dToken)
Non-transferable token representing debt position. When user borrows 50 USDT, they receive 50 dUSDT. Debt token tracks variable interest accrual.

**Key Properties:**
- Tracks scaled balance (normalized by index)
- Accrues variable interest rate
- Burned when debt repaid
- Cannot be transferred

### Supply (Lending)
Action of depositing asset into pool as collateral. Suppliers earn variable APY on supplied amount. Supply is the source of liquidity for borrowers.

### Borrow
Action of taking loan from pool. Borrower pays variable interest on borrowed amount. Must maintain health factor ≥ 1.

### Repay (Repayment)
Action of returning borrowed amount to pool. Repayment includes principal + accrued interest. Can repay partially or fully.

### Withdraw
Action of removing supplied collateral from pool. Withdrawal requires:
- Sufficient unlocked liquidity
- Health factor ≥ 1 after withdrawal
- Sufficient aToken balance

---

## 2. Financial Terms

### LTV (Loan-to-Value)
Maximum percentage of collateral that can be borrowed. Example: 80% LTV means borrowing $80 for every $100 of collateral supplied. Prevents over-leverage.

**Formula:** `max_borrow = collateral_value * LTV / 100`

### Liquidation Threshold
Health factor threshold at which liquidation becomes possible. Example: 85% threshold means liquidation begins when health < 1.0. Always ≥ LTV.

**Liquidation triggers when:**
```
health_factor = (collateral * liquidation_threshold * WAD) / (10000 * debt) < 1.0
```

### Liquidation Bonus
Discount liquidators receive for seizing collateral. Example: 5% bonus means liquidator pays 95% of fair collateral value, keeping 5% as profit.

**Liquidation benefit:**
```
collateral_received = debt_covered * (100 + bonus) / 100
```

### Health Factor (HF)
Ratio of collateral value to debt value, accounting for risk thresholds. Measures position safety.

**Formula:**
```
HF = (collateral_value * liquidation_threshold_bps * WAD) / (debt_value * 10000)
```

**Safety Levels:**
- HF > 1.5: Safe
- 1.0 < HF < 1.5: Caution (watch closely)
- HF < 1.0: Liquidatable

### APY (Annual Percentage Yield)
Effective annual return including compounding. K2 uses variable APY based on utilization rate.

**Relationship to APR:**
```
APY = (1 + APR/n)^n - 1
where n = compounding periods per year
```

### APR (Annual Percentage Rate)
Simple annual interest rate without compounding. Often expressed as RAY (27 decimals) in contracts.

### Utilization Rate
Percentage of reserve liquidity currently borrowed. Affects interest rates.

**Formula:**
```
utilization = total_debt / (total_debt + available_liquidity)
```

**Interest rate increases with utilization:**
- Low utilization (0-80%): Low rates (encourage borrowing)
- High utilization (80-100%): High rates (encourage repayment)

### Interest Rate Strategy
Contract that calculates variable borrow rate based on reserve utilization. Different assets can have different strategies.

**Two-slope model:**
- Below optimal (80%): gentle slope
- Above optimal (80%): steep slope

### Reserve Factor
Percentage of accrued interest reserved for protocol (not paid to suppliers). Remaining goes to suppliers. Example: 10% reserve factor means 90% to suppliers, 10% to treasury.

### Close Factor
Maximum percentage of debt that can be liquidated in one transaction. Default: 50%. Prevents single liquidation from closing entire position.

**Dynamic escalation rules:**
- **50%** (default): Normal liquidation — up to half the debt per call
- **100%** (full close): When HF < `partial_liquidation_hf_threshold` OR remaining position < `MIN_CLOSE_FACTOR_THRESHOLD` — allows full debt closure to avoid dust positions

**Constraint:**
```
debt_to_cover <= total_debt * close_factor / 100
```

---

## 3. Execution Terms

### Initialize
Setup operation called once per asset to create reserve. Creates aToken and debt token, sets configuration. Only pool admin can initialize.

### Refresh Reserve State
Updates reserve's interest indices, rates, and interest-accrued balances. Called automatically before user operations but can be called manually.

### Pause / Unpause
Pause disables all operations on asset (supply, borrow, etc.). Used in emergencies. Emergency admin can pause; pool admin must unpause.

### Flash Loan
Uncollateralized loan that must be repaid within same transaction (atomic operation). Fee: 30 basis points (0.30%) default (storage fallback). Note: the FLASHLOAN_PREMIUM_TOTAL constant (9) in constants.rs is not used as the storage default. Use case: arbitrage, liquidation, swaps.

**Flash Loan Flow:**
1. Borrow amount + fee
2. Execute callback (arbitrary logic)
3. Verify repayment complete
4. Return or revert

### Liquidation / Liquidation Call
Forcing repayment of unhealthy position's debt in exchange for collateral at discount. Only works if position health < 1.

**Liquidation Flow:**
1. Verify position is unhealthy
2. Liquidator provides debt tokens
3. Liquidator receives collateral + bonus
4. Position becomes more healthy

### Bad Debt Socialization
When position is unhealthy and collateral can't cover debt, remaining debt is "socialized" (spread across other suppliers of that asset via interest index reduction).

### Flash Liquidation
Combined flash loan + liquidation to seize unhealthy positions and liquidate in single atomic transaction.

---

## 4. Technical Terms

### Index (Liquidity Index / Borrow Index)
Normalized interest accrual factor. Grows over time with interest rates. Balances stored as "scaled" amounts, multiplied by index to get actual balance.

**Use:**
- Track interest without updating all individual balances
- Compress O(users) updates into O(1) index update

**Formula:**
```
scaled_balance * index = actual_balance
```

### Scaled Balance
Internal storage of position normalized by index. Actual balance = scaled_balance × index / RAY.

**Benefit:** Single index update accrues interest for all users

### Bitmap Configuration
Efficient bit-packed storage of user reserve status. Each reserve has 2 bits (collateral, borrowed).

**User Configuration:**
- Bit 0-1: Reserve 0 status
- Bit 2-3: Reserve 1 status
- ...
- Supports max 64 reserves

### WAD (18 Decimals)
Standard token precision in Soroban: 10^18. Used for prices, rates, amounts.

**1 WAD = 1,000,000,000,000,000,000**

Common values:
- 1 WAD = 100%
- 0.5 WAD = 50%
- 0.01 WAD = 1%

### RAY (27 Decimals)
High precision for interest calculations: 10^27. Used for index values, rates.

**1 RAY = 1,000,000,000,000,000,000,000,000,000**

Relationship to WAD: `1 RAY = 1e9 WAD`

### Oracle (Price Oracle)
Contract providing price data for assets. Examples: Redstone oracle, manual override. Required for liquidations and HF calculations.

### Price Precision
Decimal places of price data from oracle. Default: 14 decimals. Formula: `oracle_to_wad = 10^(18 - oracle_precision)`

### Oracle-to-WAD Factor
Conversion multiplier from oracle precision to WAD precision. Depends on oracle's price_precision.

**Example:**
- Oracle precision: 14 decimals
- WAD precision: 18 decimals
- oracle_to_wad = 10^(18-14) = 10,000

**Must be applied:** `wad_value = oracle_value * oracle_to_wad`

### Basis Points
Unit of interest rates and percentages. 1 basis point = 0.01% = 1/10,000.

**Conversions:**
- 100 basis points = 1%
- 10,000 basis points = 100%

### Interest Accrual
Process of adding earned interest to balance. In K2, accrual is implicit (via index growth) until withdrawal/repay.

### Rounding Direction
Direction for price/interest calculations:
- **Round Down** (ray_div_down): For withdrawal amounts, collateral value (conservative)
- **Round Up** (ray_div_up): For fees, interest charges (fair to protocol)

---

## 5. System Components

### Kinetic Router
Main lending pool contract. Handles all user operations: supply, borrow, repay, withdraw, liquidate.

### Pool Configurator
Admin contract for reserve setup and parameter updates. Manages:
- Reserve initialization
- LTV, threshold, bonus updates
- Supply/borrow cap management
- Asset pause/freeze

### Interest Rate Strategy
Contract calculating borrow rate based on utilization. Can have different strategies per reserve.

### Price Oracle
Provides asset prices in WAD (18 decimals). Validates price staleness and precision. Supports manual overrides.

### Redstone Adapter
Integration with Redstone oracle network. Converts Redstone feeds to K2 oracle interface.

### aToken Contract
Token contract representing collateral (supply position). Minted when supplying, burned when withdrawing.

### Debt Token Contract
Token contract representing debt (borrow position). Minted when borrowing, burned when repaying.

### Treasury
Address receiving protocol fees (reserve factor %). Managed by governance.

### Flash Loan Adapter
Helper contract for executing flash loan callbacks. Whitelisted for flash loan operations.

### AMM / DEX Router
Address of liquidity pools (Soroswap, SoroAMM). Used for collateral swaps during liquidations.

### Adapter Registry
Maps asset pairs to swap adapter contracts for DEX operations.

---

## 6. Security Terms

### Require Auth
Soroban SDK function verifying transaction is signed by specified address. Returns error if auth fails.

```rust
address.require_auth();  // Transaction must be signed by address
```

### Whitelist
Set of approved addresses allowed to perform action. Example: flash loan whitelisted contracts can execute flash loans.

### Blacklist
Set of forbidden addresses. Example: aToken and debt token blacklisted from being transfer recipients.

### Pause
Boolean flag disabling operations on asset. Enforced at operation start:
```
if is_paused(asset) {
    return Err(AssetPaused)
}
```

### Emergency Admin
Special role that can only pause assets (not unpause). Used for emergency circuit breaker. Cannot execute normal admin functions.

### Pool Admin
Role managing reserve configuration. Can unpause assets, update parameters, initialize reserves.

### Authorization Flow
1. User calls contract function
2. Function calls `address.require_auth()`
3. Soroban verifies transaction signed by address
4. If not signed: Error #26 (Unauthorized)

### TTL (Time To Live)
Ledger entry validity period. Extended by contract to prevent entries from expiring mid-transaction.

---

## 7. Precision Values Table

| Constant | Value | Use Case |
|----------|-------|----------|
| WAD | 1e18 | Token amounts, prices, rates (primary) |
| RAY | 1e27 | Interest indices, high precision |
| PRICE_PRECISION | 14 | Oracle price decimal places |
| WAD_PRECISION | 18 | Standard token precision |
| BASIS_POINTS | 10,000 | Basis point denominator |
| RAY_WAD_RATIO | 1e9 | Conversion factor (RAY / WAD) |
| HALF_WAD | 5e17 | For rounding (WAD / 2) |
| HALF_RAY | 5e26 | For rounding (RAY / 2) |
| FLASHLOAN_PREMIUM | 30 | Storage default fee in basis points (0.30%) |
| FLASHLOAN_PREMIUM_TO_PROTOCOL | 0 | Protocol share of fee |
| DEFAULT_CLOSE_FACTOR | 5,000 | Max debt to liquidate (50%) |
| MAX_CLOSE_FACTOR | 10,000 | Absolute max (100%) |
| DEFAULT_LIQUIDATION_THRESHOLD | 85 | Minimum health for no liquidation (%) |
| HEALTH_FACTOR_LIQUIDATION_THRESHOLD | 1e18 | WAD representation of 1.0 |
| MAX_RESERVES | 64 | Maximum assets in pool |
| MAX_ASSETS_PER_TX | 32 | Limit per transaction |
| SECONDS_PER_YEAR | 31,536,000 | Annual interest calculation |
| DEFAULT_PRICE_STALENESS | 3,600 | Max oracle price age (seconds) |
| MAX_PRICE_STALENESS | 86,400 | Absolute max staleness (1 day) |
| DEFAULT_MAX_PRICE_CHANGE | 2,000 | Circuit breaker (20% max change) |

---

## 8. Conversion Formulas

### Oracle Price to WAD

**Given:** Oracle price with precision P

**Convert to WAD:**
```
oracle_to_wad_factor = 10^(18 - P)
wad_price = oracle_price * oracle_to_wad_factor
```

**Example:** Oracle price = 1,000,000,000,000,000 (at 14 decimals)
```
factor = 10^(18-14) = 10,000
wad_price = 1,000,000,000,000,000 * 10,000 = 1e19
```

### Basis Points to WAD Percentage

**Given:** Basis point value (e.g., 500 for 5%)

**Convert to WAD:**
```
wad_percentage = basis_points * 1e18 / 10,000
```

**Example:** 500 basis points (5%)
```
wad_percentage = 500 * 1e18 / 10,000 = 50,000,000,000,000,000 (0.05 WAD)
```

### WAD to Percentage String

**Given:** WAD value

**Convert:**
```
percentage = wad_value * 100 / 1e18
```

**Example:** 5e17 WAD
```
percentage = 5e17 * 100 / 1e18 = 50 (%)
```

### Health Factor Calculation

**Given:**
- Collateral value in WAD
- Liquidation threshold (basis points)
- Debt value in WAD

**Formula:**
```
HF = (collateral_wad * threshold_bps * 1e18) / (debt_wad * 100 * 10,000)
   = (collateral_wad * threshold_bps) / (debt_wad * 1,000,000)
```

**Example:**
```
collateral = 1,000 * 1e18 WAD ($1,000)
threshold = 8,500 basis points (85%)
debt = 800 * 1e18 WAD ($800)

HF = (1000 * 1e18 * 8500) / (800 * 1e18 * 10000)
   = 8,500,000 / 8,000,000
   = 1.0625 (Safe, > 1.0)
```

### Interest Index Growth

**Given:**
- Previous index (in RAY)
- Annual rate (in RAY)
- Time elapsed (seconds)

**Formula:**
```
new_index = prev_index * (1 + annual_rate * time / SECONDS_PER_YEAR)
          = prev_index + (prev_index * annual_rate * time / SECONDS_PER_YEAR)
```

### Scaled Balance to Actual Balance

**Given:**
- Scaled balance (internal storage)
- Current index (in RAY)

**Formula:**
```
actual_balance = scaled_balance * index / RAY
```

**Example:** Accruing interest
```
scaled_balance = 1000 * 1e27 (internal)
index_before = 1.0 * 1e27
index_after = 1.05 * 1e27 (5% interest accrued)

balance_before = 1000 * 1e27 * 1.0 * 1e27 / 1e27 = 1000
balance_after = 1000 * 1e27 * 1.05 * 1e27 / 1e27 = 1050 (gained 50)
```

### U256 Multiplication Protection

**Problem:** Multiplying large u128 values can overflow

**Solution:** Use U256 intermediate
```rust
let result: u128 = U256::from(a)
    .checked_mul(U256::from(b))
    .and_then(|v| v.checked_mul(U256::from(c)))
    .and_then(|v| u128::try_from(v).ok())
    .ok_or(MathOverflow)?;
```

---

## 9. Abbreviations

| Abbreviation | Meaning |
|--------------|---------|
| HF | Health Factor |
| LTV | Loan-to-Value |
| APY | Annual Percentage Yield |
| APR | Annual Percentage Rate |
| WAD | Wei Amount Decimal (1e18) |
| RAY | 1e27 (high precision) |
| bps | Basis points (1/10000) |
| aToken | Interest-bearing token (collateral) |
| dToken | Debt token (borrowed) |
| DEX | Decentralized Exchange |
| AMM | Automated Market Maker |
| ETH | Ethereum (example asset) |
| BTC | Bitcoin (example asset) |
| USDC | USD Coin (stablecoin example) |
| USDT | Tether (stablecoin example) |
| TTL | Time To Live (ledger entry validity) |
| CEI | Checks-Effects-Interactions (security pattern) |
| XLM | Stellar Lumens (native asset) |

---

## 10. Error Codes

Complete error reference (see 14-DEVELOPER.md § 13 for detailed descriptions).

### High Severity Errors

| Code | Error | Meaning |
|------|-------|---------|
| 7 | InsufficientCollateral | Cannot borrow without collateral |
| 8 | HealthFactorTooLow | Position would become unhealthy |
| 11 | InvalidLiquidation | Position not eligible for liquidation |
| 12 | LiquidationAmountTooHigh | Exceeds close factor limit |
| 37 | MathOverflow | Math operation overflowed (u128) |

### Configuration Errors

| Code | Error | Meaning |
|------|-------|---------|
| 19 | SupplyCapExceeded | Supply would exceed reserve limit |
| 20 | BorrowCapExceeded | Borrow would exceed reserve limit |
| 21 | DebtCeilingExceeded | Isolation mode debt exceeded |

### Authorization Errors

| Code | Error | Meaning |
|------|-------|---------|
| 26 | Unauthorized | Caller lacks required permission |
| 27 | AlreadyInitialized | Contract already initialized |
| 28 | NotInitialized | Contract not initialized |

### Oracle Errors (separate enum)

| Code | Error | Meaning |
|------|-------|---------|
| 1 | AssetPriceNotFound | No price for asset |
| 4 | PriceTooOld | Price exceeds staleness limit |
| 7 | AssetNotWhitelisted | Asset not in oracle |

---

## 11. Function Naming

K2 follows Rust naming conventions:

### Snake Case Functions
- `supply_collateral` (not supplyCollateral)
- `calculate_health_factor` (not calcHealthFactor)
- `get_user_account_data` (not getUserAccountData)

### Helper Functions
Prefix indicates operation type:
- `get_*`: Query/view function
- `set_*`: Write function (requires auth)
- `calculate_*`: Computation function
- `validate_*`: Validation function (returns error)
- `execute_*`: Execution function (state change)
- `initialize_*`: Setup function (one-time)

### Boolean Getters
Prefix with `is_` or `has_`:
- `is_paused(asset)`  -> bool
- `is_active_collateral(user, reserve)`  -> bool
- `has_debt(user, asset)`  -> bool

---

## 12. Storage Keys

K2 uses Symbol constants (via `symbol_short!()` macro) for storage keys in Soroban instance storage:

### Admin & Config Keys

```
INIT         — Initialization flag
PADMIN       — Pool admin address
PPADMIN      — Pending pool admin
EADMIN       — Emergency admin address
PEADMIN      — Pending emergency admin
ORACLE       — Price oracle address
TREASURY     — Treasury address
PCONFIG      — Pool configurator address
ORACFG       — Cached oracle config
```

### Protocol State Keys

```
PAUSED       — Global pause flag
FLPREM       — Flash loan premium
FLPREMMAX    — Flash loan premium max
FLLIQPR      — Flash liquidation premium
HFLIQTH      — Health factor liquidation threshold
MINSWAP      — Min swap output (bps)
PLIQHF       — Partial liquidation HF threshold
FLACTIVE     — Flash loan active flag
REENTRY      — Protocol reentrancy lock
LPTOLBPS     — Liquidation price tolerance (bps)
```

### DEX & Incentives Keys

```
DEXROUTE     — DEX router address
DEXFACT      — DEX factory address
INCENT       — Incentives contract address
FLIQHELP     — Flash liquidation helper address
```

### Reserve Keys

```
RLIST        — Reserves list
RCOUNT       — Reserves count
NEXTRID      — Next reserve ID
RDATA        — Reserve data (per asset)
RID2ADDR     — Reserve ID to address mapping
RDEBTCEIL    — Reserve debt ceiling
RDEFICIT     — Reserve deficit
```

### User Keys

```
UCONFIG      — User configuration bitmap
```

### Whitelist/Blacklist Keys

```
WLIST        — General whitelist
RWLMAP       — Per-reserve whitelist map
RBLMAP       — Per-reserve blacklist map
LWLF         — Liquidation whitelist flag
LBLF         — Liquidation blacklist flag
SWLF         — Swap whitelist flag
LIQBLACK     — Liquidation blacklist
RBLACK       — Reserve blacklist
```

### Authorization Keys

```
LIQAUTH      — Liquidation authorization (two-step)
```

---

## 13. Time Constants

| Constant | Value | Use Case |
|----------|-------|----------|
| SECONDS_PER_YEAR | 31,536,000 | Annual interest calculation |
| BLOCKS_PER_YEAR | 2,102,400 | Block-based calculation (Stellar) |
| DEFAULT_PRICE_STALENESS_THRESHOLD | 3,600 | Max oracle age (1 hour) |
| MAX_PRICE_STALENESS_THRESHOLD | 86,400 | Absolute max age (24 hours) |
| MIN_PRICE_STALENESS_THRESHOLD | 60 | Minimum age allowed (1 minute) |
| ORACLE_OVERRIDE_MAX_DURATION | 604,800 | Manual override max age (7 days) |

---

## 14. Limits and Constraints

### System Limits

| Limit | Value | Reason |
|-------|-------|--------|
| Max Reserves | 64 | Bitmap encoding constraint |
| Max Assets per Transaction | 32 | Budget constraint |
| Max Reward Tokens | 16 | Gas optimization |
| Max Signers | 32 | Multi-sig limit |
| Max Feed IDs | 32 | Oracle data limit |
| Max Conversion Bytes | 256 | Data size limit |

### Price Constraints

| Constraint | Value | Reason |
|-----------|-------|--------|
| Price Precision Min | 0 decimals | Minimum allowed |
| Price Precision Max | 18 decimals | Maximum allowed |
| Max Price Change | 2,000 bps (20%) | Circuit breaker |
| Min Swap Output Floor | 9,000 bps (90%) | Slippage limit |

### Liquidation Constraints

| Constraint | Value | Reason |
|-----------|-------|--------|
| Default Close Factor | 50% | Gradual liquidation |
| Max Close Factor | 100% | Absolute max |
| HF Tolerance | 1 bp (0.01%) | Rounding tolerance |
| Min First Deposit | 1,000 (smallest token units, e.g., 0.001 USDC for 6-decimal token) | Share inflation protection |

### Interest Rate Constraints

| Constraint | Value | Reason |
|-----------|-------|--------|
| Optimal Utilization | 80% | Kink point |
| Max Utilization | 100% | Full reserve borrowed |
| Max Excess Stable/Total | 100% | Stability limit |

---

## 15. Default Parameters

### Reserve Configuration Defaults

```
LTV:                    8,000 bps (80%)
Liquidation Threshold:  8,500 bps (85%)
Liquidation Bonus:      500 bps (5%)
Reserve Factor:         1,000 bps (10%)
Supply Cap:             Unlimited
Borrow Cap:             Unlimited
Borrowing Enabled:      True
Flash Loan Enabled:     True
```

### Interest Rate Defaults

```
Optimal Utilization Rate: 8e26 RAY (80%)
Base Variable Borrow:     2e23 RAY (0.02% or 2% annually)
Variable Rate Slope 1:    1e24 RAY (varies with utilization 0-80%)
Variable Rate Slope 2:    1e25 RAY (steep slope 80-100%)
```

### Oracle Defaults

```
Price Staleness Threshold: 3,600 seconds (1 hour)
Price Precision:          14 decimals
WAD Precision:            18 decimals
Max Price Change (Circuit Breaker): 2,000 bps (20%)
```

### Flash Loan Defaults

```
Premium Total: 30 bps (0.30%) storage fallback
Premium to Protocol: 0 bps (0%, all to LPs)
Premium to LPs: 30 bps (0.30%)
Note: FLASHLOAN_PREMIUM_TOTAL = 9 in constants.rs is a legacy constant; actual default comes from storage.rs fallback (30).
```

---

## Quick Reference: Common Conversions

### Price with 14 Decimal Oracle  -> WAD

```
wad_price = oracle_price_14_decimals * 10,000
```

### Basis Points  -> WAD

```
wad_value = basis_points * 1e14
```

### Percentage  -> Basis Points

```
basis_points = percentage * 100
```

### Health Factor Calculation

```
HF = (collateral_usd * liquidation_threshold_bps * WAD) / (debt_usd * 10000)
```

### Interest Accrual Over N Seconds

```
accrued_rate = annual_rate_ray * (n / 31536000)
new_index = old_index * (1 + accrued_rate / 1e27)
```

---

## Summary

This glossary provides complete terminology reference for K2 protocol. Key takeaways:

1. **Precision is critical**: Always apply oracle_to_wad factor
2. **Health factor drives safety**: Must stay ≥ 1.0
3. **Liquidation enables solvency**: Forces repayment of unhealthy positions
4. **Interest accrues via indices**: Single update affects all users
5. **Bitmap compresses configuration**: 64 reserves fit in 128 bits

For implementation details, refer to 14-DEVELOPER.md and main protocol documentation.
