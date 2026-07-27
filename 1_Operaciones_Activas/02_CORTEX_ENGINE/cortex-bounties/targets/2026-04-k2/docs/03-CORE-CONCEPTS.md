# 3. Core Concepts

## Reserves

A **reserve** is a single asset that can be supplied and borrowed. Each reserve maintains:

- **Liquidity Index**: Cumulative interest earned by suppliers (starts at 1 RAY)
- **Borrow Index**: Cumulative interest owed by borrowers (starts at 1 RAY)
- **Interest Rates**: Current supply rate (APY) and borrow rate (APY)
- **Configuration**: LTV, liquidation threshold, bonus, and feature flags
- **Token Contracts**: aToken (supply) and Debt Token (borrow)
- **Strategy**: Interest rate calculation strategy

### **Reserve State**
```rust
pub struct ReserveData {
    pub liquidity_index: u128,              // RAY precision (1e27)
    pub variable_borrow_index: u128,        // RAY precision
    pub current_liquidity_rate: u128,       // APY in RAY/year
    pub current_variable_borrow_rate: u128, // APY in RAY/year
    pub last_update_timestamp: u64,         // Seconds
    pub a_token_address: Address,           // aToken contract
    pub debt_token_address: Address,        // Debt token contract
    pub interest_rate_strategy_address: Address,
    pub id: u32,                            // Reserve index (0-63)
    pub configuration: ReserveConfiguration, // Bitmap
}
```

---

## Collateral Assets

Assets supplied to the protocol that back borrowing positions. Properties:

### **Loan-to-Value (LTV)**
Maximum percentage of collateral value that can be borrowed.

- **Basis Points**: 0-10000 (10000 = 100%)
- **Example**: 7500 = 75% LTV → $75 borrowing power per $100 collateral
- **Usage**: `borrowing_power = collateral_value × LTV / 10000`

### **Liquidation Threshold**
The LTV at which a position becomes eligible for liquidation. Always ≥ LTV.

- **Example**: LTV = 75%, Threshold = 80%
- **Buffer**: 5% safety margin before liquidation
- **Usage**: Calculates weighted liquidation threshold in health factor

### **Liquidation Bonus**
Premium paid to liquidators for taking on liquidation risk. Paid from seized collateral.

- **Basis Points**: e.g. 500 (5%)
- **Calculation**: `collateral_with_bonus = collateral_base × (10000 + bonus) / 10000`
- **Cap**: Cannot exceed 100% (no infinite arbitrage)
- **Example**: Seize $100 collateral with 5% bonus → liquidator gets $105 worth

---

## aToken

**Interest-bearing token representing supplied assets.**

### **Key Properties**
- **Redeemability**: 1 aToken = 1 unit of underlying asset (plus accrued interest)
- **Transferability**: Can be transferred, with whitelist validation
- **Interest Accrual**: Automatic via liquidity index
- **Ownership**: Belongs to supplier

### **Balance Mechanics**
```
Scaled Balance = Amount / Liquidity Index

Actual Balance = Scaled Balance × Current Liquidity Index

Example:
- User supplies 100 USDC, liquidity index = 1.0
- Scaled balance = 100 / 1.0 = 100
- After 1 year, liquidity index = 1.05 (5% APY)
- Actual balance = 100 × 1.05 = 105 USDC
```

### **Interest Calculation**
Interest accrues continuously via index updates:

```
New Liquidity Index = Old Index × (1 + APY × Time)
User's Balance = Scaled Balance × New Index
```

---

## Debt Token

**Non-transferable token representing borrowed amounts.**

### **Key Properties**
- **Non-Transferable**: Cannot be transferred, approved, or burned by holder
- **Pool-Only Mint/Burn**: Only Kinetic Router can create or destroy
- **Interest Accrual**: Automatic via borrow index
- **Read-Only**: Users only read their balance

### **Balance Mechanics**
Same as aToken, but with borrow index:

```
Scaled Debt = Borrowed Amount / Borrow Index

Actual Debt = Scaled Debt × Current Borrow Index

Example:
- User borrows 100 USDC, borrow index = 1.0
- Scaled debt = 100 / 1.0 = 100
- After 1 year, borrow index = 1.08 (8% APY)
- Actual debt = 100 × 1.08 = 108 USDC (must repay)
```

---

## Liquidity Index

**Tracks cumulative interest earned by suppliers.**

### **Purpose**
Enables efficient interest calculation without per-user tracking.

### **Update Formula**
```
New Index = Old Index × (1 + Interest Rate × Time Delta)

Example:
- Start: index = 1.0 RAY
- 1 year passes, rate = 5%
- New: index = 1.0 × 1.05 = 1.05 RAY
```

### **User Earnings**
```
Interest Earned = Scaled Balance × (New Index - Old Index)
                = Scaled Balance × Index Change

Example:
- User's scaled balance: 100
- Index before: 1.0
- Index after: 1.05
- Interest earned: 100 × (1.05 - 1.0) = 5 units
```

### **Monotonicity**
- **Guarantee**: Index never decreases
- **Property**: Suppliers always earn non-negative interest
- **Enforcement**: Interest rates ≥ 0

---

## Borrow Index

**Tracks cumulative interest owed by borrowers.**

Similar to liquidity index, but for borrowed amounts.

```
New Borrow Index = Old Index × (1 + Borrow Rate × Time Delta)

Borrower's Debt = Scaled Debt × Current Borrow Index
```

---

## Borrowing Power

**Maximum value a user can borrow based on collateral.**

### **Calculation**
```
Borrowing Power = Σ (Collateral Value × LTV)
                  for each collateral asset

Available to Borrow = Borrowing Power - Current Debt
```

### **Example**
```
User has:
- $1,000 USDC (LTV 75%) → $750 borrowing power
- $2,000 ETH (LTV 80%) → $1,600 borrowing power
- Total borrowing power: $2,350

Current debt: $1,000

Available to borrow: $2,350 - $1,000 = $1,350
```

---

## Health Factor

**Measures position safety. Core metric for liquidation risk.**

### **Formula**
```
Health Factor = (Total Collateral × Weighted Liquidation Threshold) / Total Debt

Where:
- Total Collateral = Σ (collateral_balance × price) for all collateral
- Weighted Liquidation Threshold = Σ (collateral_value × threshold) / total_collateral
- Total Debt = Σ (debt_balance × price) for all borrowed assets
```

### **Interpretation**
- **HF = 1.0 (exactly)**: Position at liquidation threshold
- **HF > 1.0**: Position is healthy (safe)
- **HF < 1.0**: Position is liquidatable (at risk)
- **HF = ∞**: No debt (not borrowing)

### **Example**
```
User has:
- $1,000 USDC collateral (80% liquidation threshold)
- $500 ETH collateral (85% liquidation threshold)

Borrowing:
- $800 USDT debt

Calculation:
- Total collateral: $1,500
- Weighted threshold: ($1,000 × 0.80 + $500 × 0.85) / $1,500
                    = ($800 + $425) / $1,500
                    = 0.817 (81.7%)
- HF = ($1,500 × 0.817) / $800
     = 1,225.5 / $800
     = 1.53 ✓ Healthy (>1.0)
```

---

## Liquidation Threshold

**Loan-to-Value at which a position becomes liquidatable.**

- **Always ≥ LTV**: Creates safety buffer
- **Example Gap**: 5-10 percentage points
- **Purpose**: Gives borrowers time to add collateral before liquidation
- **Example**: LTV 75%, Threshold 80%

---

## Liquidation Close Factor

**Maximum percentage of debt liquidated in single transaction.**

The close factor is **dynamic**, not fixed:

- **Normal case**: 50% (5000 basis points) — when HF ≥ `partial_liquidation_hf_threshold`
- **100% (full liquidation)** when any of these conditions apply:
  - Health factor < `partial_liquidation_hf_threshold` (default 0.5 WAD)
  - Individual debt position < `MIN_CLOSE_FACTOR_THRESHOLD` ($2,000 WAD)
  - Individual collateral position < `MIN_CLOSE_FACTOR_THRESHOLD` ($2,000 WAD)
- **Purpose**: Partial liquidation preserves borrower positions; full liquidation restores solvency faster for deeply underwater or small positions
- **Reference**: `liquidation.rs:19-26`, `constants.rs:34-37`

---

## Flash Loan Premium

**Fee charged on flash loans.**

- **Basis Points**: Default 30 (0.30%)
- **Formula**: `premium = debt_amount × premium_bps / 10000`
- **Collection**: Premium added to flash loan debt
- **Revenue**: Goes to protocol treasury

### **Example**
```
Flash loan request: 1,000 USDC at 30 bps
Premium = 1,000 × 30 / 10000 = 3 USDC
Repayment required: 1,000 + 3 = 1,003 USDC
```

---

## Oracle Price Data

Prices come from Stellar's Reflector oracle or RedStone network.

### **Price Format**
- **Precision**: Configurable via `OracleConfig.price_precision: u32` (valid range: 0–18). Default is 14, but this is not a fixed value.
- **Example** (at 14 decimals): $1.00 = 100_000_000_000_000
- **Range**: 0 to u128::MAX

### **Staleness Check**
- **Requirement**: Price timestamp must be recent
- **Max Age**: Configurable per asset (e.g. 3600s = 1 hour)
- **Enforcement**: Queries fail if price too old

### **Circuit Breaker**
- **Trigger**: Price moves >20% from last recorded
- **Effect**: Oracle paused until admin reset
- **Purpose**: Protect against manipulation or data corruption

---

## Interest Rate Mode

Currently K2 supports only **variable rate** borrowing.

- **Mode**: 1 = variable
- **Characteristics**: Rate changes with market conditions
- **APY**: Updated on every reserve interaction
- **Future**: Stable rate mode may be added

---

## Reserve Configuration (Bitmap)

Reserve parameters are packed into two 128-bit integers for efficient storage:

```
data_low (128 bits):
  Bits 0-13:   LTV (14 bits)
  Bits 14-27:  Liquidation Threshold (14 bits)
  Bits 28-41:  Liquidation Bonus (14 bits)
  Bits 42-49:  Decimals (8 bits)
  Bit 50:      Is Active (1 bit)
  Bit 51:      Is Frozen (1 bit)
  Bit 52:      Borrowing Enabled (1 bit)
  Bit 53:      Is Paused (1 bit)
  Bits 54-55:  Reserved (2 bits)
  Bit 56:      Flash Loan Enabled (1 bit)
  Bits 57-70:  Reserve Factor (14 bits)
  Bits 71-127: Reserved (57 bits)

data_high (128 bits):
  Bits 0-63:   Borrow Cap (64 bits, in tokens)
  Bits 64-127: Supply Cap (64 bits, in tokens)
```

### **Setter/Getter Pattern**
Configuration accessed via methods, not directly:

```rust
pub fn ltv(config: ReserveConfiguration) -> u128 { ... }
pub fn set_ltv(config: &mut ReserveConfiguration, value: u128) { ... }
```

---

## User Configuration (Bitmap)

User's collateral and borrowing status for each reserve:

```
Per User, 128-bit bitmap (supports up to 64 reserves):
  For each reserve i (0-63):
    - Bit 2i:     Using as collateral? (1 = yes)
    - Bit 2i+1:   Borrowing? (1 = yes)

NOTE: While the bitmap structurally supports 64 reserves, the protocol
enforces MAX_USER_RESERVES = 15 per user (storage.rs:9). Supply and
borrow operations revert with MaxUserReservesExceeded if a user
attempts to interact with more than 15 distinct reserves. This tighter
limit bounds the health-factor computation loop and prevents reserve
fragmentation attacks.

Example with 4 reserves:
  Reserve 0: using_collateral=1, borrowing=0
  Reserve 1: using_collateral=1, borrowing=1
  Reserve 2: using_collateral=0, borrowing=1
  Reserve 3: using_collateral=0, borrowing=0

  Bitmap: ...0011_0011 (reading right to left)
                  ↑ Reserve 3
                  ↓
                 Reserve 0
```

---

## Collateral vs Borrowing

### **Using as Collateral**
- Must have positive aToken balance
- Can enable/disable collateral status
- Contributes to borrowing power
- Required for liquidation checks

### **Borrowing**
- Must have positive debt token balance
- Tracked separately (automatic via debt token)
- No explicit enable/disable
- Interest accrues daily

---

## Dust Debt

**Minimal debt amounts left after operations.**

### **Why It Exists**
After liquidation, borrower may have tiny debt remainder (rounding error):

```
Total debt: $10,000
Close factor: 50%
Max liquidatable: $5,000

But after liquidation:
- $4,999.99 liquidated (rounding)
- $5,000.01 remains

This $5,000.01 is "dust"
```

### **Handling**
- **Accepted**: Small dust balances allowed
- **Minimization**: Liquidation logic tries to avoid dust
- **Collection**: Dust can be socialized to remaining lenders if needed
- **Future**: May implement dust collection mechanism

---

## Solvency

**Protocol's ability to pay withdrawals and maintain solvency.**

### **Core Invariant**
```
Total aToken Supply ≤ Underlying Balance + Total Debt

Meaning:
- Suppliers never lose their principal
- Bad debt, if any, is socialized to remaining suppliers
```

### **Enforcement**
- Every operation validates invariant before completing
- Liquidations ensure collateral sufficient to cover debt
- Protocol fee taken from liquidation bonus (not from solvency)

---

## Next Steps

1. Learn how these concepts execute: [Execution Flows](05-FLOWS.md)
2. Study liquidation specifics: [Liquidation System](06-LIQUIDATION.md)
3. Understand pricing: [Oracle Architecture](08-ORACLE.md)

---

**Last Updated**: February 2026
**Status**: Stable
