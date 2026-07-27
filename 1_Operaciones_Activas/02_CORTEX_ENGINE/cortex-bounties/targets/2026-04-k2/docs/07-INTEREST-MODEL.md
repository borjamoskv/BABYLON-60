# K2 Lending Protocol: Interest Model

## 1. Overview

The K2 lending protocol implements a sophisticated, variable-rate interest model inspired by Aave V3. The model dynamically calculates borrow and supply rates based on reserve utilization, incentivizing market equilibrium through economic principles:

- **Borrow rates** increase as utilization rises, encouraging repayment when liquidity is scarce
- **Supply rates** are derived from borrow rates, rewarding suppliers when borrowing demand is high
- **Per-asset configuration** allows customized rate curves for different assets
- **Compound interest** for borrowers (via index accumulation) and linear interest for suppliers (via index accumulation)

### Design Principles

1. **Utilization-Driven**: Interest rates respond directly to supply/demand dynamics
2. **Slope-Based Curve**: Two-slope piecewise linear function with optimal utilization threshold
3. **Index-Based Accumulation**: Interest accrues via index multiplication (RAY precision), supporting compound calculation
4. **Per-Asset Flexibility**: Different assets can have different rate curves via the interest rate strategy contract
5. **Lazy Evaluation**: Indices are computed on-demand, not every block—reducing computational overhead

---

## 2. Interest Rate Curve

### 2.1 Rate Calculation Formula

The variable borrow rate follows a two-slope piecewise linear model:

```
If utilization_rate ≤ optimal_utilization_rate:
    variable_borrow_rate = base_rate + slope1 × (utilization_rate / optimal_utilization_rate)

If utilization_rate > optimal_utilization_rate:
    variable_borrow_rate = base_rate + slope1
                         + slope2 × ((utilization_rate - optimal_utilization_rate)
                                     / (1 - optimal_utilization_rate))
```

### 2.2 Rationale

The two-slope curve ensures:
- **Below optimal utilization**: Gentle rate increase encourages borrowing up to target efficiency
- **Above optimal utilization**: Steep rate increase (via slope2) sharply discourages over-utilization
- **Smooth transition**: Continuous function at the optimal point (no jump discontinuity)

### 2.3 Example Rate Curve

With typical deployment parameters:
- `base_rate` = 0% per year
- `slope1` = 4% per year
- `slope2` = 60% per year
- `optimal_utilization_rate` = 80%

| Utilization | Variable Borrow Rate |
|---|---|
| 0% | 0.00% |
| 20% | 1.00% |
| 40% | 2.00% |
| 60% | 3.00% |
| 80% | 4.00% (optimal) |
| 90% | 34.00% (steep increase) |
| 100% | 64.00% (max incentive to repay) |

---

## 3. Utilization Rate

### 3.1 Definition

The utilization rate measures the fraction of reserve liquidity that is borrowed:

```
utilization_rate = total_variable_debt / (total_variable_debt + available_liquidity)
```

In protocol terms:

```
utilization_rate = total_variable_debt / (total_variable_debt + (aToken_supply - total_variable_debt))
                 = total_variable_debt / aToken_supply
```

### 3.2 Calculation

The protocol computes utilization in two stages:

**Stage 1: Router computes actual balances** (in `calculate_interest_rates_for_reserve`):

1. **Fetching scaled totals** from aToken and debt token contracts via `scaled_total_supply()`
2. **Scaling with indices** using `ray_mul`:
   - `total_supply = ray_mul(atoken_scaled_supply, liquidity_index)`
   - `total_debt = ray_mul(debt_scaled_supply, borrow_index)`
3. **Computing available liquidity**: `available_liquidity = total_supply - total_debt`
4. **Passing** `available_liquidity` and `total_debt` to the interest rate strategy contract

**Stage 2: Interest rate strategy computes utilization** (in `calculate_interest_rates`):

5. `total_liquidity = available_liquidity + total_variable_debt`
6. `utilization_rate = ray_div(total_variable_debt, total_liquidity)`

> **Note**: The simplified formula `utilization = total_variable_debt / aToken_supply` in Section 3.1 omits the intermediate `ray_mul` index scaling and `ray_div` rounding. The actual values may differ by small rounding amounts due to these RAY-precision operations.

### 3.3 Edge Cases

| Scenario | Utilization |
|---|---|
| **No debt** | 0 (0% utilization) |
| **Empty reserve** | 0 (default; avoids division by zero) |
| **Full capacity** (debt ≥ available) | approaches 1 RAY (100%) |
| **Insolvency** (debt > supply) | Capped at 1 RAY; triggers solvency event |

### 3.4 Precision

Utilization is computed and stored in **RAY precision** (1e27):

```
utilization_ray = 1_000_000_000_000_000_000_000_000_000 = 1.0 (fully utilized)
```

---

## 4. Variable Borrow Rate

### 4.1 Overview

The variable borrow rate is the annual percentage rate (APR in RAY precision) that borrowers pay on their debt position. It:

- Is calculated by the interest rate strategy contract based on utilization
- Updates after each user action (supply, withdraw, borrow, repay)
- Remains constant until the next action (not continuously updating each block)
- Is stored in `ReserveData.current_variable_borrow_rate` (RAY precision)

### 4.2 Rate Calculation Logic (from interest-rate-strategy contract)

**Step 1: Calculate utilization**

```rust
let total_liquidity = available_liquidity + total_variable_debt;
let utilization_rate = if total_liquidity == 0 {
    0
} else {
    ray_div(env, total_variable_debt, total_liquidity)?
};
```

**Step 2: Apply the two-slope curve**

```rust
if utilization_rate > optimal_utilization_rate {
    // Above optimal: steep increase
    let excess_utilization_rate = utilization_rate - optimal_utilization_rate;
    let excess_ratio = ray_div(env, excess_utilization_rate, RAY - optimal_utilization_rate)?;
    let slope2_component = ray_mul(env, slope2, excess_ratio)?;

    variable_borrow_rate = base_rate + slope1 + slope2_component
} else {
    // Below optimal: gentle increase
    let utilization_ratio = ray_div(env, utilization_rate, optimal_utilization_rate)?;
    let slope1_component = ray_mul(env, slope1, utilization_ratio)?;

    variable_borrow_rate = base_rate + slope1_component
}
```

### 4.3 Time-Independent Updates

**Critical property**: The variable borrow rate is NOT automatically updated every second. Instead:

1. It is recalculated **after user actions** (supply, borrow, repay, withdraw)
2. The action changes utilization  -> interest rate strategy recalculates rate
3. New rate is stored until the next action

This prevents infinite state updates and reduces computational cost.

---

## 5. Supply Rate (Liquidity Rate)

### 5.1 Definition

The supply rate (called `liquidity_rate` in code) is the APR that suppliers earn on their aToken balance. It is derived from the borrow rate and reserve factor:

```
liquidity_rate = variable_borrow_rate × utilization_rate × (1 - reserve_factor)
```

### 5.2 Intuition

- When utilization is high (many borrowers), suppliers earn more interest
- When utilization is low (few borrowers), suppliers earn less interest
- The protocol takes a cut via `reserve_factor`, reducing supplier earnings

### 5.3 Calculation

From the interest-rate-strategy contract:

```rust
// Convert reserve_factor from basis points (0-10000) to RAY
let reserve_factor_ray = (reserve_factor * RAY) / BASIS_POINTS;

// Calculate supply rate: borrow_rate × utilization × (1 - reserve_factor)
let borrow_rate_times_utilization = ray_mul(env, variable_borrow_rate, utilization_rate)?;
let liquidity_rate = ray_mul(
    env,
    borrow_rate_times_utilization,
    RAY - reserve_factor_ray  // (1 - reserve_factor) in RAY
)?;
```

### 5.4 Example

**Scenario**: borrow_rate = 10%, utilization = 80%, reserve_factor = 20%

```
liquidity_rate = 10% × 80% × (1 - 20%)
               = 10% × 80% × 80%
               = 6.4%
```

Suppliers earn 6.4% APR; protocol retains 1.6%.

---

## 6. Rate Parameters

The interest rate strategy contract stores four key parameters per asset (or globally):

### 6.1 Parameters

| Parameter | Type | Unit | Example | Purpose |
|---|---|---|---|---|
| `base_variable_borrow_rate` | u128 | RAY | 0 (0%) | Minimum rate (even at 0% utilization) |
| `variable_rate_slope1` | u128 | RAY | 4% × 1e27 | Rate increase per utilization unit (below optimal) |
| `variable_rate_slope2` | u128 | RAY | 60% × 1e27 | Rate increase per utilization unit (above optimal) |
| `optimal_utilization_rate` | u128 | RAY | 80% × 1e27 | Target utilization threshold |

### 6.2 Basis Points Conversion

Parameters are often specified in basis points (bps) and converted to RAY:

```
param_ray = param_bps × RAY / BASIS_POINTS
          = param_bps × 1e27 / 10_000
```

**Example**: 4% annual rate in basis points = 400 bps

```
param_ray = 400 × 1e27 / 10_000 = 4 × 1e24 (RAY representation of 4%)
```

### 6.3 Validation

When updating parameters, the `validate_interest_rate_params` function enforces:

1. `optimal_utilization_rate` must be strictly between 0 and RAY (exclusive on both ends) — prevents degenerate curves where optimal = 0 (single branch) or optimal = RAY (no second slope branch)
2. `variable_rate_slope1` and `variable_rate_slope2` must be non-zero — ensures the rate curve has meaningful shape
3. `variable_rate_slope2 >= variable_rate_slope1` — enforces monotonic curve so rates do not decrease at high utilization
4. `base_variable_borrow_rate + variable_rate_slope1 + variable_rate_slope2 ≤ 20 × RAY` (2000% APR cap) — prevents overflow in downstream calculations
5. Each individual component (`base_variable_borrow_rate`, `variable_rate_slope1`, `variable_rate_slope2`) is capped at `10 × RAY` (1000% APR)

Additionally, `calculate_interest_rates` validates:

6. `reserve_factor ≤ 10000 bps` (cannot exceed 100%)

---

## 7. Per-Asset Configuration

### 7.1 Global vs. Per-Asset Rates

The interest rate strategy contract supports two levels of configuration:

```rust
// Get parameters: check per-asset first, fall back to global
let params = storage::get_asset_interest_rate_params(&env, &asset)
    .unwrap_or_else(|| storage::get_interest_rate_params(&env));
```

### 7.2 Use Cases

**Global parameters** (fallback):
- Applied to all assets that don't have custom parameters
- Set by admin at initialization or update

**Per-asset parameters**:
- Override global parameters for specific assets
- Allow different rate curves (e.g., volatile assets with steeper curves)
- Example:
  - **ETH**: base=0%, slope1=4%, slope2=60%, optimal=80%
  - **USDC**: base=0%, slope1=2%, slope2=40%, optimal=90% (stablecoin, less volatile)

### 7.3 Configuration Methods

**Set global parameters**:
```
update_interest_rate_params(
    caller: Address,
    base_variable_borrow_rate: u128,
    variable_rate_slope1: u128,
    variable_rate_slope2: u128,
    optimal_utilization_rate: u128,
) -> Result<(), KineticRouterError>
```

**Set per-asset parameters**:
```
set_asset_interest_rate_params(
    caller: Address,
    asset: Address,
    base_variable_borrow_rate: u128,
    variable_rate_slope1: u128,
    variable_rate_slope2: u128,
    optimal_utilization_rate: u128,
) -> Result<(), KineticRouterError>
```

---

## 8. Indices and Accrual

### 8.1 Core Concept

Instead of updating balances directly on every action, the protocol uses **indices** to scale balances. This pattern allows O(1) balance lookups and compound interest without explicit interest bookkeeping per user.

### 8.2 Index Pattern

```
actual_balance = scaled_balance × current_index / RAY
```

When an index increases, all holders automatically earn proportional interest.

### 8.3 Index Types

| Index | Field Name | Type | Purpose |
|---|---|---|---|
| **Liquidity Index** | `liquidity_index` | u128 | Scales aToken (supplier) balances |
| **Borrow Index** | `variable_borrow_index` | u128 | Scales debt token balances |

Both are stored in `ReserveData` and start at **1 RAY** (1e27).

---

## 9. Liquidity Index

### 9.1 Definition

The liquidity index accumulates interest earned by suppliers over time. It scales aToken balances to compute actual supplied amounts:

```
supplier_actual_balance = supplier_scaled_balance × liquidity_index / RAY
```

### 9.2 Accumulation Model

**Linear interest** (not compound):

```
cumulated_liquidity_interest = 1 + (liquidity_rate × time / SECONDS_PER_YEAR)
```

Then:

```
new_liquidity_index = old_liquidity_index × cumulated_liquidity_interest
```

### 9.3 Why Linear?

Despite the name "linear interest," the index pattern creates **compounding**:

1. At time T1: `index_A = 1.0 RAY`
2. After 1 year: `index_B = index_A × (1 + r) = 1.0 RAY × 1.05 = 1.05 RAY` (if 5% rate)
3. After another year: `index_C = index_B × (1 + r) = 1.05 RAY × 1.05 = 1.1025 RAY` (compound effect!)

The linear approximation (1 + r*t) is used for efficiency, but repeated multiplication creates the compounding.

### 9.4 Update Timing

The liquidity index is updated:
- During `update_state()`, called lazily when:
  - A user supplies, withdraws, borrows, or repays
  - Another action touches the same reserve
  - View functions query the current rate

---

## 10. Borrow Index

### 10.1 Definition

The borrow index accumulates interest owed by borrowers. It scales debt token balances to compute actual borrowed amounts:

```
borrower_actual_debt = borrower_scaled_debt × borrow_index / RAY
```

### 10.2 Accumulation Model

**Compound interest** (approximated via Taylor series):

```
cumulated_borrow_interest ≈ 1 + (rate × t / year)
                          + (rate^2 × t × (t-1) / (2 × year^2))
                          + (rate^3 × t × (t-1) × (t-2) / (6 × year^3))
```

(Higher-order terms vanish when `t` is small)

Then:

```
new_borrow_index = old_borrow_index × cumulated_borrow_interest
```

### 10.3 Why Compound?

Borrowers should pay interest on previously accrued interest (standard practice). The compound approximation ensures realistic debt growth:

```
Debt(t) = Principal × (1 + rate)^t
```

### 10.4 Update Timing

The borrow index is updated:
- During `update_state()`, same timing as liquidity index
- Stored directly in `ReserveData.variable_borrow_index` by the router — there is no cross-contract `update_index()` call to the debt token
- Debt token reads the current borrow index from the router via `balance_of_with_index` calls, which accept the index as a parameter

---

## 11. Index Update Formula

### 11.1 Mathematical Definition

Let:
- `I_old` = previous index (liquidity or borrow)
- `r` = current interest rate (liquidity or variable borrow rate) in RAY
- `Δt` = time elapsed since last update (in seconds)
- `S` = SECONDS_PER_YEAR = 31,536,000

Then:

```
cumulated_interest = f(r, Δt)   // Linear or compound
I_new = I_old × cumulated_interest / RAY
```

### 11.2 Linear Interest (Suppliers)

```
f(r, Δt) = RAY + (r × Δt / S)
         = 1 + (r_percent × Δt / S)  [in RAY precision]
```

**Implementation** (from `calculate_linear_interest(rate, last_update_timestamp, current_timestamp)`):

> **Note**: Unlike `calculate_compound_interest`, this function does not take an `Env` parameter — it uses only plain `u128` checked arithmetic (no U256 needed).

```rust
let time_difference = current_timestamp - last_update_timestamp;
let interest = (rate * time_difference) / SECONDS_PER_YEAR;
cumulated_interest = RAY + interest;
```

### 11.3 Compound Interest (Borrowers)

```
f(r, Δt) = RAY + first_term + second_term + third_term
```

Where:
- `first_term = r × Δt / S`
- `second_term = (r^2 × Δt × (Δt - 1)) / (2 × S^2)`
- `third_term = (r^3 × Δt × (Δt - 1) × (Δt - 2)) / (6 × S^3)`

**Implementation** (from `calculate_compound_interest`):

```rust
let exp = current_timestamp - last_update_timestamp;

// Base power calculations
let base_power_two = ray_mul(env, rate, rate)? / (S × S);
let base_power_three = ray_mul(env, base_power_two, rate)? / S;

// All three terms use U256 arithmetic to prevent intermediate overflow:
let first_term = {
    // U256: rate * exp / SECONDS_PER_YEAR
    let rate_u256 = U256::from_u128(env, rate);
    let exp_u256 = U256::from_u128(env, exp);
    let spy_u256 = U256::from_u128(env, S);
    rate_u256.mul(&exp_u256).div(&spy_u256).to_u128()?
};
let second_term = {
    // U256: exp * (exp - 1) * base_power_two / 2
    U256::from_u128(env, exp)
        .mul(&U256::from_u128(env, exp - 1))
        .mul(&U256::from_u128(env, base_power_two))
        .div(&U256::from_u128(env, 2)).to_u128()?
};
let third_term = {
    // U256: exp * (exp - 1) * (exp - 2) * base_power_three / 6
    U256::from_u128(env, exp)
        .mul(&U256::from_u128(env, exp - 1))
        .mul(&U256::from_u128(env, exp - 2))
        .mul(&U256::from_u128(env, base_power_three))
        .div(&U256::from_u128(env, 6)).to_u128()?
};

cumulated_interest = RAY + first_term + second_term + third_term;
```

> **Note**: All three Taylor series terms use `U256` intermediate arithmetic. The pseudocode in Section 10.2 shows simplified notation, but the actual implementation promotes every multiplication to `U256` before dividing, preventing overflow for large rates or long time deltas.

### 11.4 Ray Multiplication

After computing `cumulated_interest`, apply to the old index:

```
I_new = ray_mul(env, I_old, cumulated_interest)
```

Where `ray_mul` is:

```rust
pub fn ray_mul(env: &Env, a: u128, b: u128) -> Result<u128, KineticRouterError> {
    let product = U256::from_u128(env, a) × U256::from_u128(env, b);
    let result = (product + HALF_RAY) / RAY;  // Round-to-nearest
    result.to_u128()  // Check for overflow
}
```

---

## 12. Interest Calculation Examples

### Example 1: Simple Liquidity Index Update

**Setup**:
- Initial liquidity index: 1.0 RAY
- Liquidity rate: 5% annual (0.05 × 1e27)
- Time elapsed: 31,536,000 seconds (1 year)
- SECONDS_PER_YEAR: 31,536,000

**Calculation**:

```
cumulated_interest = RAY + (rate × Δt / SECONDS_PER_YEAR)
                   = 1e27 + (0.05e27 × 31,536,000 / 31,536,000)
                   = 1e27 + 0.05e27
                   = 1.05e27

new_liquidity_index = ray_mul(1e27, 1.05e27)
                    = (1e27 × 1.05e27 + HALF_RAY) / 1e27
                    = 1.05e27  
```

**User Impact**:
- Supplier deposits: 1,000 USDC (scaled balance = 1,000 × 1e18)
- After 1 year with 5% rate:
  - Actual balance = 1,000 × 1e18 × 1.05e27 / 1e27 = 1,050 USDC
  - Interest earned: 50 USDC 

### Example 2: Borrow Index with Compounding

**Setup**:
- Initial borrow index: 1.0 RAY
- Borrow rate: 10% annual (0.10 × 1e27)
- Time elapsed: 31,536,000 seconds (1 year)

**Calculation** (3-term Taylor series):

```
first_term = (0.10e27 × 31,536,000) / 31,536,000 = 0.10e27

base_power_two = (0.10e27 × 0.10e27) / (31,536,000^2)
               = 0.01e54 / 995_518_976,000,000
               ≈ 0.01005e27

second_term = (31,536,000 × 31,535,999 × 0.01005e27) / 2
            ≈ 0.005e27  (very small, compound effect)

third_term ≈ negligible (0.00016e27)

cumulated_interest ≈ 1e27 + 0.10e27 + 0.005e27 + 0.00016e27
                  ≈ 1.10516e27

new_borrow_index = ray_mul(1e27, 1.10516e27)
                 ≈ 1.10516e27  
```

**User Impact**:
- Borrower owes: 1,000 USDC (scaled debt = 1,000 × 1e18)
- After 1 year with 10% compound rate:
  - Actual debt = 1,000 × 1e18 × 1.10516e27 / 1e27 ≈ 1,105.16 USDC
  - Interest owed: ≈105.16 USDC (compounding effect) 

### Example 3: Partial Period (6 months)

**Setup**:
- Liquidity index: 1.0 RAY
- Liquidity rate: 6% annual
- Time elapsed: 15,768,000 seconds (0.5 years)

**Calculation**:

```
cumulated_interest = RAY + (0.06e27 × 15,768,000 / 31,536,000)
                   = 1e27 + (0.06e27 × 0.5)
                   = 1e27 + 0.03e27
                   = 1.03e27

Supplier actual balance = scaled × 1.03e27 / 1e27
                        = scaled × 1.03  (3% interest in 6 months)
```

---

## 13. Compounding vs Linear

### 13.1 Why Different Approaches?

| Aspect | Liquidity (Suppliers) | Borrow (Borrowers) |
|---|---|---|
| **Formula** | Linear approximation | Compound Taylor series |
| **Rationale** | Simpler math, acceptable for suppliers | Precise for borrowers' obligations |
| **Index** | `liquidity_index` | `variable_borrow_index` |
| **Calculation** | `1 + r×t / year` | `1 + r×t/year + r²×t(t-1)/(2×year²) + ...` |

### 13.2 Practical Difference

Over 1 year at 10% rate:

```
Linear: 1 + 0.10 = 1.10 (10% total)
Compound (3-term): 1 + 0.10 + 0.005 + ... ≈ 1.10516 (≈10.516% total)

Difference: +0.516 percentage points in favor of borrowers
(This is a design choice to make the protocol attractive to suppliers.)
```

### 13.3 Aave V3 Compatibility

K2 follows Aave V3's pattern:
- Suppliers: linear (simplified)
- Borrowers: compound (accurate)

This is intentional and tested extensively.

---

## 14. Reserve Factor

### 14.1 Definition

The reserve factor is the percentage of interest earned by borrowers that is **retained by the protocol** (not paid to suppliers):

```
protocol_interest = total_borrow_interest × reserve_factor
supplier_interest = total_borrow_interest × (1 - reserve_factor)
```

### 14.2 Range

- **Type**: u16 (stored in reserve configuration bitmap)
- **Range**: 0 to 10,000 basis points (0% to 100%)
- **Example values**: 1,000 to 5,000 bps (10% to 50% of interest)

### 14.3 Impact on Liquidity Rate

```
liquidity_rate = borrow_rate × utilization × (1 - reserve_factor / 10000)
```

**Example**:
- Borrow rate: 10%
- Utilization: 80%
- Reserve factor: 20% (2,000 bps)

```
liquidity_rate = 10% × 80% × (1 - 0.20)
               = 10% × 80% × 0.80
               = 6.4%

Protocol earns: 10% × 80% × 0.20 = 1.6%
```

### 14.4 Accumulation

Protocol interest is collected into a **treasury** (or equivalent), not distributed to aToken holders:

1. Borrowers pay `borrow_rate`
2. Suppliers receive `liquidity_rate` via index increase
3. Difference accumulates in protocol reserves

---

## 15. APY Calculation

### 15.1 APR vs APY

- **APR** (Annual Percentage Rate): Simple interest rate (what we store)
- **APY** (Annual Percentage Yield): Compound annual yield (accounting for compounding)

### 15.2 APY Formula

For a rate `r` (in decimal, e.g., 0.10 for 10%) with compounding every Δt seconds:

```
APY = (1 + r × Δt / SECONDS_PER_YEAR) ^ (SECONDS_PER_YEAR / Δt) - 1
```

### 15.3 Example: Convert Stored Rate to APY

**Given**:
- Stored liquidity rate (APR): 5% (0.05 in decimal)

**APY calculation**:

```
APY ≈ (1 + APR) ^ (frequency) - 1

Daily compounding:
APY = (1 + 0.05/365)^365 - 1 ≈ 5.13%

Continuous:
APY = e^0.05 - 1 ≈ 5.13%
```

### 15.4 Frontend Considerations

For user display, frontends should:

1. **Fetch current rate**: `liquidity_rate` or `variable_borrow_rate` from `ReserveData`
2. **Convert to percentage**: `rate_percentage = rate / 1e27` (RAY to decimal)
3. **Label as APR**: Display as "5.12% APR (variable)"
4. **Estimate APY**: `APY ≈ (1 + rate_decimal/365)^365 - 1` for daily approximation

---

## 16. Rate Updates

### 16.1 When Rates Update

Rates are recalculated **after every user action**:

| Action | Trigger | Effect |
|---|---|---|
| **supply()** | After aToken minting | Utilization decreases  -> rates may drop |
| **withdraw()** | After aToken burning | Utilization increases  -> rates may rise |
| **borrow()** | After debt token minting | Utilization increases  -> rates rise |
| **repay()** | After debt token burning | Utilization decreases  -> rates drop |
| **liquidation_call()** | After collateral/debt transfer | Utilization changes  -> rates update |
| **flash_loan()** | Deferred (L-02) | Rates NOT updated during flash (prevents manipulation) |

### 16.2 Lazy Evaluation

The protocol does **not** update indices on every second. Instead:

1. **Indices are read/calculated on-demand** via `update_state()`
2. **Only updated if necessary** (different timestamp from last update)
3. **Same-block re-entry**: Multiple calls in same block use cached index

**Code**:

```rust
if current_timestamp == reserve_data.last_update_timestamp {
    return Ok(reserve_data);  // No time has passed, skip computation
}

// Otherwise, compute indices and store
let updated_data = update_state(env, asset, &reserve_data)?;
```

### 16.3 Update Sequence

For a **borrow** operation:

```
1. Read reserve data (includes old indices)
2. Call update_state()  -> computes new liquidity and borrow indices
3. Mint debt token to borrower (at new borrow_index)
4. Recalculate interest rates based on new utilization
5. Store updated reserve data with new rates
```

---

## 17. Time Handling

### 17.1 SECONDS_PER_YEAR Constant

```
SECONDS_PER_YEAR = 31_536_000 seconds
                 = 365 days × 24 hours × 3600 seconds
```

This is used as the denominator for rate calculations to convert annual rates to per-second rates.

### 17.2 Timestamp Source

```
current_timestamp = env.ledger().timestamp()
```

This is the Soroban ledger timestamp, typically synchronized with the network's wall-clock time.

### 17.3 Time Delta Calculation

```
time_elapsed = current_timestamp - last_update_timestamp  // In seconds
```

**Protection**: If `current_timestamp < last_update_timestamp`, the operation panics (prevents manipulation via backward timestamps).

### 17.4 Interest Per Second

From a rate `r` (annual, in RAY):

```
interest_per_second = r / SECONDS_PER_YEAR  (in RAY)
interest_for_Δt = interest_per_second × Δt
               = (r × Δt) / SECONDS_PER_YEAR
```

---

## 18. Edge Cases

### 18.1 Zero Utilization

**Scenario**: No borrows, only supplies

```
utilization = 0 / (0 + supply) = 0 RAY

variable_borrow_rate = base_rate + slope1 × (0 / optimal)
                     = base_rate

liquidity_rate = base_rate × 0 × (1 - reserve_factor)
               = 0
```

**Effect**: Suppliers earn 0% when no one borrows (expected).

### 18.2 100% Utilization

**Scenario**: Debt equals total supply

```
utilization = debt / (debt + 0) = RAY (100%)

variable_borrow_rate = base_rate + slope1 + slope2 × ((RAY - optimal) / (RAY - optimal))
                     = base_rate + slope1 + slope2

liquidity_rate = (base_rate + slope1 + slope2) × RAY × (1 - reserve_factor)
```

**Effect**: Maximum rates, strong incentive to repay/supply.

### 18.3 Exactly Optimal Utilization

**Scenario**: Debt = optimal × total_supply

```
utilization = optimal RAY

variable_borrow_rate = base_rate + slope1 × (optimal / optimal)
                     = base_rate + slope1
```

**Effect**: Smooth transition point between two slopes; no discontinuity.

### 18.4 Empty Reserve

**Scenario**: No supply and no debt (initial state)

```
total_liquidity = 0 + 0 = 0

utilization = ray_div(0, 0)  -> short-circuited to 0
variable_borrow_rate = base_rate
liquidity_rate = 0
```

**Effect**: Handled gracefully; rates default to base without error.

### 18.5 Index Overflow

**Scenario**: Index approaches u128::MAX (e.g., after 100+ years at high rates)

```
U256-based ray_mul handles intermediate overflow:

I_new = ray_mul(I_old, cumulated_interest)
       -> U256::from_u128(I_old) × U256::from_u128(cumulated)
       -> (product + HALF_RAY) / RAY
       -> to_u128()  -> checks for overflow
```

**Effect**: Returns `MathOverflow` error if final result doesn't fit u128.

---

## 19. Precision and Constants

### 19.1 RAY Precision

```
RAY = 1_000_000_000_000_000_000_000_000_000
    = 10^27
```

Used for:
- Interest rates (APR in RAY precision)
- Utilization rates
- Index values
- All rate calculations

### 19.2 WAD Precision

```
WAD = 1_000_000_000_000_000_000
    = 10^18
```

Used for:
- Token amounts (token decimals usually 6-18)
- Health factors
- Collateral valuations

### 19.3 Conversion

```
RAY = WAD × RAY_WAD_RATIO
RAY_WAD_RATIO = 10^9 = 1_000_000_000

wad_to_ray(wad_value) = wad_value × RAY_WAD_RATIO
ray_to_wad(ray_value) = (ray_value + HALF_RAY_WAD_RATIO) / RAY_WAD_RATIO
```

### 19.4 Basis Points (bps)

```
BASIS_POINTS = 10_000
```

Basis points are used for parameters like:
- Reserve factor: 2000 bps = 20%
- LTV: 8000 bps = 80%

Conversion to RAY:

```
param_ray = param_bps × RAY / BASIS_POINTS
```

### 19.5 U256 Overflow Protection

All critical multiplications use U256:

```rust
let product = U256::from_u128(env, a) × U256::from_u128(env, b);
let result = (product + rounding_bias) / divisor;
result.to_u128().ok_or(MathOverflow)?
```

This ensures intermediate overflow is caught before truncating to u128.

---

## 20. Integration with Other Components

### 20.1 Kinetic Router

The main router contract:
1. **Calls interest-rate-strategy** to get rates after each user action
2. **Updates reserve state** via `update_state()` to accrue interest
3. **Passes indices** to aToken and debt token contracts for balance calculations

**Key function**: `update_reserve_state(asset)  -> ReserveData`

### 20.2 aToken Contract

The interest-bearing token (supplier position):
1. **Stores scaled balances** (not actual balances)
2. **Uses liquidity_index** to compute actual balances on reads
3. **Accrues interest automatically** via index growth

**Formula**: `supplier_balance = scaled_balance × liquidity_index / RAY`

### 20.3 Debt Token Contract

The debt token (borrower position):
1. **Stores scaled balances** (not actual debt)
2. **Receives borrow_index** as a parameter via `balance_of_with_index` calls from the router
3. **Does not store its own index** — the authoritative borrow index lives in `ReserveData.variable_borrow_index`

**Formula**: `borrower_debt = scaled_debt × borrow_index / RAY`

### 20.4 Interest Rate Strategy Contract

A separate, upgradeable contract that:
1. **Receives** utilization, available liquidity, total debt, reserve factor
2. **Calculates** liquidity_rate and variable_borrow_rate
3. **Returns** `CalculatedRates` struct

**Interface**:
```
calculate_interest_rates(
    asset: Address,
    available_liquidity: u128,
    total_variable_debt: u128,
    reserve_factor: u128,
)  -> Result<CalculatedRates>
```

---

## 21. Summary Table

| Aspect | Value | Type | Scope |
|---|---|---|---|
| **Interest Rate Model** | Two-slope piecewise linear | Formula | Variable borrow only |
| **Optimal Utilization** | 80% (configurable) | u128 RAY | Per-asset |
| **Base Rate** | 0% (configurable) | u128 RAY | Per-asset |
| **Slope 1** | ~4% annual (configurable) | u128 RAY | Per-asset |
| **Slope 2** | ~60% annual (configurable) | u128 RAY | Per-asset |
| **Liquidity Rate** | Derived (borrow × util × (1-rf)) | u128 RAY | Computed |
| **Utilization** | debt / (debt + available) | u128 RAY | Computed |
| **Reserve Factor** | 10-50% (configurable) | u16 bps | Per-asset |
| **Liquidity Index** | Starts at 1 RAY | u128 RAY | Per-reserve |
| **Borrow Index** | Starts at 1 RAY | u128 RAY | Per-reserve |
| **Interest Accrual** | Linear (suppliers) / Compound (borrowers) | Formula | Per-reserve |
| **Update Timing** | After user actions (lazy) | Trigger | Deterministic |
| **Precision** | RAY (1e27) | Standard | All rates |
| **Overflow Protection** | U256 intermediate math | Safeguard | All multiplications |

---

## 22. References and Further Reading

- **Aave V3 Whitepaper**: https://aave.com/en/whitepapers/
- **Interest-Rate-Strategy Contract**: `/contracts/interest-rate-strategy/src/contract.rs`
- **Kinetic Router Calculation Module**: `/contracts/kinetic-router/src/calculation.rs`
- **Shared Math Utilities**: `/contracts/shared/src/utils.rs`
- **Type Definitions**: `/contracts/shared/src/types.rs`
- **Constants**: `/contracts/shared/src/constants.rs`

---

**Document Version**: 1.1
**Last Updated**: 2026-03-20
**Status**: Final (audit remediation IR-01 through IR-07)
