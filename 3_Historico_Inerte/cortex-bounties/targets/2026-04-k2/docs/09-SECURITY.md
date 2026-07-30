# 9. Security Model

## Overview

K2's security architecture is built on multiple defense-in-depth layers, combining **Soroban's native capabilities** with **application-level checks** and **economic incentives**.

### Design Philosophy

1. **Fail-Safe**: Operations that cannot be verified fail and revert (not silent failures)
2. **Defense-in-Depth**: Multiple independent checks prevent single-point compromises
3. **Conservative Defaults**: Parameters favor protocol solvency over capital efficiency
4. **Transparency**: All actions generate verifiable events and state changes
5. **Least Privilege**: Each actor gets only permissions needed for their role

### Core Assumptions

- **EOA Authenticity**: The Soroban authorization tree correctly identifies transaction signers
- **Price Integrity**: Oracle systems (Reflector, RedStone) provide manipulation-resistant prices
- **Stellar Assets**: SEP-41 tokens implement standard transfer semantics
- **Reentrancy Protection**: Explicit `ReentrancyGuard` RAII pattern with `PROTOCOL_LOCKED` flag prevents re-entry
- **No Frontrunning**: Block-level finality prevents transaction reordering within blocks

---

## Authorization Patterns

### require_auth() Flow

**Soroban Authorization Tree**: Every Stellar contract transaction builds an authorization tree specifying:
- Which addresses authorized the transaction
- Which contracts/functions they invoked
- What contract calls are authorized

#### How require_auth() Works

```rust
// In any contract function:
pub fn my_operation(env: Env, caller: Address, ...) {
    caller.require_auth();
    // If caller did not authorize this contract to invoke this function,
    // the transaction fails at this point
}
```

**Verification Process**:
1. Transaction initiator signs the TX envelope with signing key
2. Soroban builds authorization tree: `caller -> contract_A::function_X -> contract_B`
3. When `contract_B::function` calls `caller.require_auth()`, Soroban verifies:
   - `caller` appears in the auth tree
   - `caller` authorized invocation of this contract/function
   - The invocation matches the authorized path

**Result**: `require_auth()` always succeeds exactly once per authorized invoker per TX.

#### Cross-Contract Call Example

```
User TX:
  1. User.require_auth()  (User signed the TX)
  2. supply(caller: User, ...)
      -> Router.require_auth(caller)  (User is in auth tree)
  3. Router calls AToken.transfer(...)
      -> AToken does NOT call User.require_auth()
      -> Router.require_auth() was already done
```

### Pool Admin Operations

All administrative state changes require pool admin authorization.

```rust
pub fn set_liquidation_bonus(
    env: Env,
    reserve_id: u32,
    new_bonus: u32,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();  // Verify admin authorized this TX

    // Only proceeds if authorized
    storage::update_reserve_liquidation_bonus(&env, reserve_id, new_bonus);
    Ok(())
}
```

**Protected Functions**:
- `init_reserve()` - Add new reserve
- `update_reserve_configuration()` - Modify reserve parameters
- `set_interest_rate_strategy()` - Change rate calculation
- `set_liquidation_whitelist()` - Restrict liquidators
- `set_reserve_whitelist()` - Restrict users
- `transfer_admin()` - Change pool admin

### Emergency Admin Operations

Pause is available to both emergency admin and pool admin. Unpause is restricted to pool admin only.

```rust
pub fn pause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    // validate_emergency_admin accepts EITHER emergency admin OR pool admin
    storage::validate_emergency_admin(&env, &caller)?;
    caller.require_auth();

    storage::set_paused(&env, true);
    Ok(())
}

pub fn unpause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    storage::validate_admin(&env, &caller)?;  // Only pool admin can unpause
    caller.require_auth();

    storage::set_paused(&env, false);
    Ok(())
}
```

---

## EOA Authorization

### User Operations

Users always authorize their own transactions explicitly.

```
User wants to borrow 100 USDC:

1. User calls: Router.borrow(caller: User, ...)
2. User's signing key signs the TX envelope
3. Soroban auth tree includes: User -> Router::borrow
4. Router calls User.require_auth()  -> PASS (User signed)
5. Borrow proceeds
```

### Authorization Implications

- **User cannot authorize another user's borrow** (can only authorize own TX)
- **User cannot borrow on behalf of another user** (would need their auth)
- **Exception**: `on_behalf_of` parameter allows changing where aTokens/debt are recorded

#### on_behalf_of Pattern

```rust
pub fn supply(
    env: Env,
    caller: Address,        // Must be authorized
    asset: Address,
    amount: u128,
    on_behalf_of: Address,  // Different account gets aToken
) {
    caller.require_auth();  // User authorizes their own supply

    // Transfer happens FROM caller
    underlying.transfer_from(&env, &caller, &atoken, amount)?;

    // But aToken is credited to on_behalf_of
    atoken.mint_scaled(&env, on_behalf_of, amount, liquidity_index)?;
}
```

**Valid Flows**:
- `supply(caller: User, on_behalf_of: User)` - Supply to self 
- `supply(caller: User, on_behalf_of: Treasury)` - Supply to treasury 
- `supply(caller: Treasury, on_behalf_of: User)` - Not allowed (User didn't authorize)

---

## Dual Authorization

### Safe Delegation Pattern

In cases where two parties must collaborate (e.g., liquidation), both must authorize.

#### Liquidation Authorization

```rust
pub fn liquidation_call(
    env: Env,
    liquidator: Address,      // Performs liquidation
    borrower: Address,         // Gets liquidated
    debt_to_cover: u128,
    receive_a_token: bool,
) {
    liquidator.require_auth();  // Liquidator authorizes action
    // Borrower does NOT need to authorize (bad debt recovery)
}
```

**Why Borrower Doesn't Authorize**:
- Borrower may be off-chain
- Protocol must recover collateral automatically
- Liquidator is economically incentivized to execute correctly

#### Swap Collateral Authorization

```rust
pub fn swap_collateral(
    env: Env,
    caller: Address,           // User authorizes
    in_asset: Address,
    out_asset: Address,
    amount_in: u128,
) {
    caller.require_auth();     // User authorizes the swap

    // Swap executes:
    // 1. Burn collateral (in_asset)
    // 2. Call DEX adapter
    // 3. Mint new collateral (out_asset)
    // 4. Verify health factor maintained
}
```

---

## Contract Self-Authorization

### authorize_as_current_contract Pattern

When a contract needs to invoke itself or delegate to another contract, it uses special authorization.

#### Flash Loan Callback

Flash loans use a special callback pattern where the handler contract authorizes itself:

```rust
pub fn request_flash_loan(
    env: Env,
    receiver: Address,         // Contract that will handle the loan
    amounts: Vec<(Address, u128)>,  // (asset, amount)
    data: Bytes,
) {
    // Receiver does NOT need to require_auth()
    // Instead, receiver.authorize_as_current_contract() is implicit

    // 1. Transfer assets to receiver
    for (asset, amount) in amounts {
        transfer_asset(&env, &asset, &router, &receiver, amount)?;
    }

    // 2. Call receiver's flash loan handler
    let result = receiver.flash_loan_handler(&env, &amounts, &data);

    // 3. Receiver must return assets + premium
    // Verified by balance check, not by auth
}
```

**Key Difference**:
- Flash loan handler **does not call `receiver.require_auth()`**
- Instead, authorization happens implicitly via direct invocation
- Handler must repay by deadline (verified by contract invariant)

#### DEX Adapter Invocation

Similarly, swap adapters are invoked directly without explicit auth:

```rust
pub fn swap_collateral(...) {
    // Get configured DEX adapter
    let adapter = storage::get_dex_adapter(&env)?;

    // Invoke directly (adapter authorizes itself)
    let out_amount = adapter.swap_exact_in(
        &env,
        in_asset,
        out_asset,
        amount_in,
        min_out,
    )?;

    // No adapter.require_auth() needed
    // Adapter is a trusted contract, invoked internally
}
```

---

## Protocol Invariants

Core guarantees that must always hold after every operation.

### Solvency Invariant

**Statement**: For each reserve, the supply is always overcollateralized.

```
aToken_supply ≤ underlying_balance + total_debt_in_reserve
```

**In Words**:
- Every aToken minted must be backed by an underlying asset
- Assets come from either:
  1. Supplied capital (sits in aToken contract)
  2. Borrowed capital (lent out, backed by collateral)

**Enforcement**:
- aToken.mint() can only be called by Kinetic Router
- Kinetic Router only mints when it receives the underlying asset
- Debt tokens always paired with collateral lock
- Interest accrual respects index monotonicity

**Why It Matters**:
- Users can always redeem aTokens for underlying
- Protocol never faces insolvency cascade
- Providers' capital is protected

#### Example Violation (Prevented)

```
Scenario: User tries to supply 100 USDC

1. Router receives supply() call
2. BEFORE: aToken_supply = 0, underlying_balance = 0
3. Router tries: atoken.mint_scaled(user, 100, index)
4. User balance would become: 100 / index
5. BUT underlying_balance is still 0
6. This violates solvency

Solution: Router only mints AFTER it receives the underlying:
  1. underlying.transfer_from(caller, atoken, 100) 
  2. NOW: underlying_balance = 100
  3. atoken.mint_scaled(user, 100, index) 
  4. Solvency maintained: atoken_supply ≤ underlying_balance
```

### Health Factor Invariant

**Statement**: After any position-changing operation, either:
1. User's health factor ≥ 1.0, OR
2. User had zero debt before operation, OR
3. User becomes liquidatable (HF < 1.0) with explicit consent

```
FOR ALL users, FOR ALL states:
  IF user.debt_value > 0:
    THEN health_factor ≥ 1.0 ∨ user_is_liquidatable
```

**Enforcement**:
- `borrow()`: Validates HF ≥ 1.0 after borrow
- `withdraw()`: Validates HF ≥ 1.0 after withdrawal
- `supply()`: No HF check (supplies collateral, improves HF)
- `repay()`: No HF check (reduces debt, improves HF)
- `liquidation()`: Validates HF improves or position is recovered

**Why It Matters**:
- Borrowers always have safety margin
- Protocol cannot freeze capital unexpectedly
- Liquidation is economically viable

#### Example Violation (Prevented)

```
Scenario: User borrows too much

Position:
  - Collateral: 100 XLM @ $1 = $100
  - LTV: 75%
  - Liquidation threshold: 80%
  - Max borrow (by LTV): $75

1. User calls: borrow(caller, USDC, 85)
2. Router checks: health_factor = (100 * 0.8) / 85 = 0.94
   (health factor uses liquidation_threshold, not LTV)
3. HF < 1.0  -> REVERT
4. Borrow fails with HealthFactorTooLow

Instead, user can only borrow up to $75 (LTV limit).
```

### Index Monotonicity

**Statement**: Liquidity and borrow indices never decrease.

```
liquidity_index(t) ≤ liquidity_index(t + Δt)
borrow_index(t) ≤ borrow_index(t + Δt)
```

**In Words**:
- Interest always accrues in one direction
- Users' balances only grow
- Time moves forward, interest accumulates

**Enforcement**:
- `update_reserve_state()` runs before every operation
- New index = old index × (1 + rate × time_passed)
- Multiplication by positive factor ensures monotonicity
- Stored as u128 RAY (precision prevents underflow)

**Why It Matters**:
- Users earn predictable interest
- Suppliers never see balance decreases due to system mechanics
- Borrowers owe more principal + interest, never less

#### Example

```
Initial state:
  - liquidity_index = 1.0 RAY
  - aToken balance = 100 USDC

After 1 year (5% APY):
  - liquidity_index = 1.05 RAY
  - aToken balance = 100 * (1.05 RAY) / (1.0 RAY) = 105 USDC 

After 2 years:
  - liquidity_index = 1.1025 RAY (compound interest)
  - aToken balance = 100 * (1.1025 RAY) / (1.0 RAY) = 110.25 USDC 

Index always increases (monotonic)
```

### Conservation of Value

**Statement**: Protocol creation and destruction of value is balanced.

```
ALWAYS:
  aToken_supply + total_debt_locked = assets_in_protocol

On liquidation:
  seized_collateral_value = debt_covered_value + liquidator_bonus + protocol_fee
```

**In Words**:
- Flash loan premiums are collected, not created
- Liquidation bonuses come from seized collateral
- No surprise wealth transfer mechanisms
- All fees are explicit

**Enforcement**:
- Flash loan: debt = borrowed_amount × (1 + premium_bps / 10000)
- Liquidation: bonus = collateral × bonus_bps / 10000
- Protocol fee: fee = liquidation_premium × liquidation_fee_bps / 10000

**Why It Matters**:
- System is zero-sum (fair)
- No hidden inflation/deflation
- Users can audit their own positions

### Completeness Invariant

**Statement**: All required data is present and valid.

```
FOR ALL reserves:
  - Interest rate strategy is set and deployed
  - Price oracle is available
  - LTV and threshold are specified
  - aToken and debt token are initialized
```

**Enforcement**:
- `init_reserve()` validates all fields before storage
- `update_reserve_configuration()` validates bitmap fields
- View functions return errors if data missing
- No fallback to defaults (fail-closed)

**Why It Matters**:
- No missing/incomplete configurations that cause crashes
- All reserves are fully operational
- No surprise behavior from default values

---

## Liquidation Safety

### Health Factor Improvement Guarantee

After liquidation, the borrower's health factor must not decrease (unless position is fully closed).

```rust
// Before liquidation
let hf_before = calculate_health_factor(&env, &borrower, &reserves)?;

// Execute liquidation
let (debt_covered, collateral_seized) = liquidate(&env, ...)?;

// After liquidation
let hf_after = calculate_health_factor(&env, &borrower, &reserves)?;

// Guarantee
if remaining_debt > 0 {
    assert!(hf_after >= hf_before, "HF must improve");
}
```

**Why This Matters**:
- Liquidation cannot worsen a position
- Cannot force users into worsening debt
- Prevents liquidation from harming borrowers

### Deeply Underwater Position Protection

When a position's health factor falls below `PARTIAL_LIQUIDATION_HF_THRESHOLD`, the close factor escalates to 100%, allowing full liquidation of the position.

```rust
let hf = calculate_health_factor(...)?;
let close_factor = if hf < PARTIAL_LIQUIDATION_HF_THRESHOLD {
    10000  // 100% close factor - full liquidation allowed
} else {
    5000   // 50% close factor - partial liquidation only
};
```

**Close Factor Behavior**:
- **HF >= threshold** (e.g., 0.5 < HF < 1.0): Close factor is 50%. Liquidator can cover up to half the debt. This limits extraction and gives the borrower a chance to recover.
- **HF < threshold** (e.g., HF < 0.5): Close factor is 100%. Full liquidation is allowed. The entire debt can be covered and all collateral seized, preventing stuck positions that cannot be resolved.

**Example**: User has $100 collateral, $500 debt (HF = 0.1)
- HF < threshold, so close factor = 100%
- Liquidator can cover the full $500 debt
- All $100 collateral seized
- Position is fully closed (no locked/unresolvable remainder)

---

## Flash Loan Safety

### Premium Collection

Flash loan premiums are always collected before repayment verification.

```
1. Transfer borrowed_amount to receiver
2. Call receiver.flash_loan_handler(...)
3. Receiver must return: borrowed_amount + (borrowed_amount × premium_bps / 10000)
4. Verify returned_balance >= required_amount
5. Premium flows to treasury (fee collection)
```

**Formula**: `premium = amount × premium_bps / 10000`
- Default: 30 bps = 0.30% fee
- Rounding: Always round UP (protocol favor)
- Example: 1000 USDC × 30 bps = 3 USDC (rounded up if necessary)

**Enforcement**:
- Balance check is atomic: either full repayment or revert
- No way to "borrow" without repaying
- Premium is owed immediately (no grace period)

### Premium Rounding

Premiums are calculated using `percent_mul_up` to ensure protocol always benefits.

```rust
fn calculate_flash_loan_premium(amount: u128, bps: u32, env: &Env) -> u128 {
    // Ensures rounding always favors protocol
    percent_mul_up(amount, bps, env)
}

// Example:
amount = 1 USDC
bps = 30 (0.30%)
result = 1 * 30 / 10000 = 0.003 USDC
rounded up = 1 wei (smallest unit)
user pays 1 + 1 = 2 wei for 1-wei loan
```

---

## Access Control

### Reserve Whitelisting

Reserves can restrict supply/borrow to whitelisted addresses.

```rust
pub fn set_reserve_whitelist(
    env: Env,
    asset: Address,
    whitelist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Empty = open access
    // Non-empty = restricted to listed addresses
    storage::set_reserve_whitelist(&env, &asset, &whitelist);
    Ok(())
}

// In supply() flow:
if !is_whitelisted_for_reserve(&env, &asset, &caller) {
    return Err(KineticRouterError::AddressNotWhitelisted);
}
```

**Use Cases**:
- **Permissioned reserves**: Only approved institutions can supply/borrow
- **Isolated testing**: Restrict to testnet addresses during development
- **Institutional assets**: Only KYC'd users can access premium assets

### Liquidation Whitelisting

Liquidations can be restricted to a whitelist of liquidators.

```rust
pub fn set_liquidation_whitelist(
    env: Env,
    whitelist: Vec<Address>,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    storage::set_liquidation_whitelist(&env, &whitelist);
    Ok(())
}

// In liquidation_call() flow:
if !is_liquidator_whitelisted(&env, &liquidator) {
    return Err(KineticRouterError::Unauthorized);
}
```

**Use Cases**:
- **Permissioned liquidation**: Only approved liquidators can execute
- **Gradual decentralization**: Start permissioned, open up over time
- **Emergency lockdown**: Disable liquidation if bug detected

---

## Pause Mechanism

### Emergency Protocol Pause

The protocol can be paused by either the emergency admin or the pool admin.

```rust
pub fn pause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    // Accepts either emergency admin or pool admin
    storage::validate_emergency_admin(&env, &caller)?;
    caller.require_auth();

    storage::set_paused(&env, true);
    Ok(())
}
```

**Effect of Pause**:
- `supply()`  -> Disabled
- `borrow()`  -> Disabled
- `withdraw()`  -> Disabled
- `repay()`  -> Disabled
- `liquidation_call()`  -> Disabled
- `swap_collateral()`  -> Disabled
- `flash_loan()`  -> Disabled

**Unaffected Operations**:
- View functions (queries)
- Interest accrual (continues on-chain)
- Administrative functions (can still configure)

### Pause Guard Implementation

```rust
pub fn supply(...) -> Result<(), KineticRouterError> {
    // First check: is protocol paused?
    if storage::is_paused(&env) {
        return Err(KineticRouterError::AssetPaused);
    }

    // Then proceed with normal logic
    ...
}
```

### Unpause Authorization

**Only pool admin can unpause** (emergency admin cannot).

```rust
pub fn unpause(env: Env, caller: Address) -> Result<(), KineticRouterError> {
    storage::validate_admin(&env, &caller)?;  // Must be pool admin
    caller.require_auth();

    storage::set_paused(&env, false);
    Ok(())
}
```

**Rationale**:
- Both emergency admin and pool admin can react quickly to pause
- Only pool admin (slower, more careful) can unpause
- Prevents a compromised emergency key from undoing a deliberate pause
- Creates check-and-balance system

---

## Admin Separation

### Pool Admin vs Emergency Admin

Two independent admin roles with distinct permissions.

| Operation | Pool Admin | Emergency Admin |
|-----------|-----------|-----------------|
| Initialize reserves | Yes | No |
| Update configuration | Yes (via configurator) | No |
| Set interest rates | Yes | No |
| Set oracle prices (manual) | Yes | No |
| Pause protocol | Yes | Yes |
| Unpause protocol | Yes | No |
| Transfer admin | Yes | No |

### Independence Guarantee

Each admin is stored in separate `instance` storage slots using short symbol keys:

```rust
const POOL_ADMIN: Symbol = symbol_short!("PADMIN");
const EMERGENCY_ADMIN: Symbol = symbol_short!("EADMIN");

pub fn get_pool_admin(env: &Env) -> Result<Address, KineticRouterError> {
    env.storage()
        .instance()
        .get(&POOL_ADMIN)
        .ok_or(KineticRouterError::NotInitialized)
}

pub fn get_emergency_admin(env: &Env) -> Option<Address> {
    env.storage().instance().get(&EMERGENCY_ADMIN)
}
```

**Benefits**:
- Compromise of one admin doesn't compromise other
- Emergency admin can be fast (dedicated to pause)
- Pool admin can be careful (thorough governance)
- Different key management practices possible

---

## Two-Step Admin Transfer

### Transfer Initiation

Pool admin proposes a new admin address.

```rust
pub fn transfer_admin(
    env: Env,
    new_admin: Address,
) -> Result<(), KineticRouterError> {
    let current_admin = storage::get_pool_admin(&env)?;
    current_admin.require_auth();

    // Store proposed admin (not active yet)
    storage::set_pending_admin(&env, &new_admin);

    events::publish_admin_transferred_initiated(&env, new_admin);
    Ok(())
}
```

### Transfer Acceptance

New admin must explicitly accept the role.

```rust
pub fn accept_admin(env: Env) -> Result<(), KineticRouterError> {
    let pending_admin = storage::get_pending_admin(&env)?;
    pending_admin.require_auth();  // New admin must authorize

    // Finalize transfer
    storage::set_pool_admin(&env, &pending_admin);
    storage::clear_pending_admin(&env);

    events::publish_admin_transferred(&env, pending_admin);
    Ok(())
}
```

**Two-Step Protection**:
1. Current admin proposes new admin (can be anyone)
2. New admin must accept (must have access to their key)
3. Prevents admin key from being transferred to wrong address
4. Gives new admin chance to verify they have the right address

**Scenario Prevention**:
```
Attacker tries to redirect admin:
1. Current admin calls: transfer_admin(attacker_address)
2. storage::pending_admin = attacker_address
3. Attacker calls accept_admin()
4. But attacker_address.require_auth() fails if attacker doesn't actually have the key
5. Transfer reverts, admin remains unchanged

OR attacker targets wrong address:
1. Admin calls: transfer_admin(intended_address)
2. But admin specifies wrong address by mistake
3. Proposed admin receives transfer request
4. Proposed admin realizes wrong address
5. Proposed admin does NOT call accept_admin()
6. Transfer expires (no explicit timeout, but remains pending)
```

---

## Parameter Validation

All configuration changes validate parameters before storage.

### Reserve Initialization Validation

```rust
pub fn init_reserve(
    env: Env,
    asset: Address,
    a_token: Address,
    debt_token: Address,
    interest_rate_strategy: Address,
    reserve_factor_bps: u32,
    liquidation_bonus_bps: u32,
    liquidation_threshold_bps: u32,
    ltv_bps: u32,
    decimals: u32,
) -> Result<(), KineticRouterError> {
    // Comprehensive validation

    // LTV <= 100%
    if ltv_bps > 10000 {
        return Err(KineticRouterError::InvalidLTV);
    }

    // Threshold >= LTV
    if liquidation_threshold_bps < ltv_bps {
        return Err(KineticRouterError::InvalidLiquidationThreshold);
    }

    // Bonus cannot exceed 100%
    if liquidation_bonus_bps > 10000 {
        return Err(KineticRouterError::InvalidLiquidationBonus);
    }

    // Decimals must fit in pow() calculation
    if decimals > 38 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // Reserve factor must be <= 100%
    if reserve_factor_bps > 10000 {
        return Err(KineticRouterError::InvalidAmount);
    }

    // All validations passed - safe to store
    storage::set_reserve_configuration(&env, &asset, ...);
    Ok(())
}
```

### Oracle Configuration Validation

```rust
pub fn set_oracle_config(
    env: Env,
    asset: Address,
    price_source: Address,
    price_precision: u32,
) -> Result<(), OracleError> {
    // Price precision must be in range [0, 18]
    if price_precision > 18 {
        return Err(OracleError::InvalidConfig);
    }

    // Verify price_source can be invoked (not guaranteed, but basic check)
    // Could also validate it's in a whitelist of known feeds

    storage::set_oracle_config(&env, &asset, price_source, price_precision);
    Ok(())
}
```

### Why Validation on Update?

Previous vulnerability: `update_reserve_configuration()` stored raw bitmaps without validation.

**Fixed Approach**:
```rust
pub fn update_reserve_configuration(
    env: Env,
    caller: Address,
    reserve_id: u32,
    new_config: ReserveConfiguration,
) -> Result<(), KineticRouterError> {
    // Access restricted to pool configurator, not pool admin directly
    storage::validate_pool_configurator(&env, &caller)?;
    caller.require_auth();

    // Extract and validate all fields
    let ltv = new_config.ltv();
    let threshold = new_config.liquidation_threshold();
    let bonus = new_config.liquidation_bonus();
    let decimals = new_config.decimals();

    // Apply same validation as init_reserve()
    validate_reserve_parameters(ltv, threshold, bonus, decimals, ...)?;

    // Only store after validation passes
    storage::set_reserve_configuration(&env, reserve_id, new_config);
    Ok(())
}
```

---

## Reentrancy Model

### Explicit Reentrancy Guard

K2 uses an explicit `ReentrancyGuard` RAII pattern in `router.rs` with a `PROTOCOL_LOCKED` flag stored in instance storage. This guard is acquired at the start of every state-changing operation and automatically released when the guard goes out of scope.

```rust
const PROTOCOL_LOCKED: Symbol = symbol_short!("REENTRY");

struct ReentrancyGuard<'a> {
    env: &'a Env,
}

impl<'a> Drop for ReentrancyGuard<'a> {
    fn drop(&mut self) {
        storage::set_protocol_locked(self.env, false);
    }
}

fn acquire_reentrancy_guard(env: &Env) -> ReentrancyGuard {
    storage::extend_instance_ttl(env);
    if storage::is_protocol_locked(env) {
        panic_with_error!(env, SecurityError::ReentrancyDetected);
    }
    storage::set_protocol_locked(env, true);
    ReentrancyGuard { env }
}
```

Every router entry point (supply, borrow, withdraw, repay, liquidation, swap, flash loan) acquires this guard as its first action. If the protocol is already locked (e.g., during a flash loan callback), any attempt to re-enter a protected function panics with `SecurityError::ReentrancyDetected`.

### Flash Loan Reentrancy Protection

Flash loans use a callback pattern where the handler contract receives control flow. The reentrancy guard prevents the handler from calling back into protected router operations:

```
TX Execution:
  1. User calls Router.flash_loan(Handler, amounts, data)
  2. Router acquires ReentrancyGuard (PROTOCOL_LOCKED = true)
  3. Router.flash_loan() executes
      -> Transfers amounts to Handler
      -> Calls Handler.flash_loan_handler(amounts, data)
        -> Handler executes arbitrary code
        -> Can call other contracts
        -> If Handler tries to call Router.supply/borrow/etc:
           -> acquire_reentrancy_guard() finds PROTOCOL_LOCKED = true
           -> Panics with ReentrancyDetected
  4. Handler returns
  5. Router verifies balance increased by premium
  6. ReentrancyGuard dropped (PROTOCOL_LOCKED = false)
  7. TX completes
```

**Why Flash Loans Are Safe**:
- Reentrancy guard blocks re-entry during callback execution
- Balance check happens after callback completes
- Guard is automatically released via RAII Drop, even on panic
- Premium is enforced before any return

---

## Cross-Contract Risks

### Swap Adapter Invocation

DEX adapters are external contracts that execute swaps.

```rust
pub fn swap_collateral(
    env: Env,
    caller: Address,
    in_asset: Address,
    out_asset: Address,
    amount_in: u128,
    min_out: u128,
) -> Result<u128, KineticRouterError> {
    caller.require_auth();

    // Burn incoming collateral
    in_token.burn_scaled(...)?;

    // Get DEX adapter
    let adapter = storage::get_dex_adapter(&env)?;

    // Execute swap (trusts adapter implementation)
    let amount_out = adapter.swap_exact_in(
        &env,
        in_asset,
        out_asset,
        amount_in,
        min_out,
    )?;

    // Mint outgoing collateral
    out_token.mint_scaled(...)?;

    // Verify health factor
    validate_user_health_factor(...)?;

    Ok(amount_out)
}
```

**Risks**:
- Adapter could misbehave or be compromised
- Adapter controls exact_in amount passed to swap

**Mitigations**:
- DEX adapter is whitelisted by pool admin
- `min_out` parameter prevents excessive slippage
- Health factor check prevents over-leveraging
- Only whitelisted adapters can be registered

### Oracle Price Invocation

Price oracle is external contract that returns asset prices.

```rust
pub fn get_price(
    env: Env,
    asset: Address,
) -> Result<u128, OracleError> {
    // Oracle could:
    // 1. Return stale prices
    // 2. Return manipulated prices
    // 3. Return zero prices
    // 4. Hang/timeout

    let oracle = storage::get_price_oracle(&env)?;
    let price = oracle.get_price(&env, &asset)?;

    // Validate freshness
    validate_price_staleness(&env, &asset, &price)?;

    // Validate against circuit breaker
    validate_price_bounds(&env, &asset, &price)?;

    Ok(price)
}
```

**Risks**:
- Oracle could be compromised
- Prices could be stale
- Prices could be extreme

**Mitigations**:
- Staleness checks enforce max age
- Circuit breaker limits price changes
- Multiple oracle sources available (Reflector, RedStone)
- Manual price overrides for emergency

### Flash Loan Handler

Flash loan callback is user-provided contract.

```rust
pub fn request_flash_loan(
    env: Env,
    receiver: Address,
    amounts: Vec<(Address, u128)>,
    data: Bytes,
) -> Result<(), KineticRouterError> {
    // Receiver could:
    // 1. Fail to repay
    // 2. Repay but not return assets
    // 3. Request another flash loan (nested)

    // 1. Transfer assets to receiver
    for (asset, amount) in &amounts {
        transfer_asset(&env, asset, &router, &receiver, amount)?;
    }

    // 2. Invoke handler (could fail or hang)
    receiver.flash_loan_handler(&env, &amounts, &data)?;

    // 3. Verify repayment (atomic check)
    for (asset, amount) in &amounts {
        let premium = calculate_flash_loan_premium(amount, bps);
        let required = amount + premium;

        let balance = asset.balance(&receiver);
        if balance < required {
            return Err(KineticRouterError::FlashLoanNotRepaid);
        }
    }

    // 4. Collect premium
    for (asset, amount) in &amounts {
        let premium = calculate_flash_loan_premium(amount, bps);
        transfer_asset(&env, asset, &receiver, &treasury, premium)?;
    }

    Ok(())
}
```

**Risks**:
- Handler could not repay
- Handler could be complex and expensive (CPU cost)
- Handler could transfer assets elsewhere

**Mitigations**:
- Atomic balance check (either full repayment or revert)
- Premium is enforced immediately
- CPU limits prevent infinite loops
- Handler is temporary (only during TX)

---

## Oracle Manipulation

### Circuit Breaker

Oracle prices are validated against a moving window of acceptable values.

```rust
pub fn validate_price_bounds(
    env: Env,
    asset: Address,
    new_price: u128,
) -> Result<(), OracleError> {
    // Get last valid price
    let last_price = storage::get_last_valid_price(&env, &asset)?;

    // Calculate max allowed change
    let max_change_bps = storage::get_circuit_breaker_threshold(&env, &asset)?;
    let max_price = last_price * (10000 + max_change_bps) / 10000;
    let min_price = last_price * 10000 / (10000 + max_change_bps);

    // Validate new price within bounds
    if new_price > max_price || new_price < min_price {
        return Err(OracleError::PriceManipulationDetected);
    }

    // Update last valid price
    storage::set_last_valid_price(&env, &asset, new_price);

    Ok(())
}
```

**Parameters**:
- `max_change_bps`: Maximum allowed price change per update (e.g., 1000 = 10%)
- Prevents prices from jumping 100x suddenly
- Allows gradual legitimate price movements

### Price Staleness Check

Prices must be recent.

```rust
pub fn validate_price_staleness(
    env: Env,
    asset: Address,
    price_info: PriceInfo,  // Contains timestamp
) -> Result<(), OracleError> {
    let now = env.ledger().timestamp();
    let max_age = storage::get_max_price_age(&env, &asset)?;

    if now > price_info.timestamp + max_age {
        return Err(OracleError::PriceTooOld);
    }

    Ok(())
}
```

**Parameters**:
- `max_age`: Maximum seconds price can be old
- Prevents using week-old prices as current
- Enforced per asset (different assets can have different staleness)

**Example Values**:
- Stellar-native assets: 15 minutes (Reflector updates frequently)
- External assets: 1 hour (RedStone updates less frequently)
- Stablecoins: 1 hour (slower expected change)

### Manual Price Override

Admin can manually set price in emergency.

```rust
pub fn set_manual_price(
    env: Env,
    asset: Address,
    price: u128,
    duration_seconds: u64,
) -> Result<(), OracleError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();

    // Prevent indefinite overrides
    if duration_seconds > MAX_OVERRIDE_DURATION {
        return Err(OracleError::OverrideDurationTooLong);
    }

    let expiration = env.ledger().timestamp() + duration_seconds;
    storage::set_manual_price_override(&env, &asset, price, expiration);

    Ok(())
}
```

**Use Cases**:
- Emergency price recovery if oracle fails
- Testing price scenarios
- Gradual price adjustment if oracle breaks

---

## Price Staleness

### Max Age Enforcement

Every reserve can have different max age for its price.

```
Reserve: USDC
  - Max age: 15 minutes (tightly traded, fast price discovery)

Reserve: Less Common Token
  - Max age: 1 hour (slower trading, less frequent updates)

Reserve: Stablecoin
  - Max age: 30 minutes (stable price, but slow oracle updates)
```

### Staleness Check Flow

```
1. Request price for asset X
2. Fetch price from oracle (includes timestamp)
3. Calculate age: current_time - price_timestamp
4. Validate age <= max_age for asset X
   - If too old: REVERT (PriceTooOld)
   - If fresh: USE price

Before any health factor calculation:
   -> All prices must pass staleness check
   -> Cannot use stale prices for HF
   -> Cannot use stale prices for liquidation decisions
```

### Prevention of Stale-Based Attacks

Attacker cannot exploit stale prices:

```
Scenario: USDC price feed breaks for 1 hour

1. Attack vector: Use 1-hour-old price as "current"
   - Would allow massive overborrow if price is stale

2. Protection: Staleness check blocks this
   - Fetching 1-hour-old price fails
   - Operation requiring fresh price REVERTS
   - No overborrow possible

3. Result: When oracle breaks, protocol pauses related operations
   - Liquidation using USDC halts
   - New USDC borrows halt
   - Existing positions become unliquidatable (safer than overborrowing)
```

---

## Slippage Protection

### Minimum Output Enforcement

Swap operations include slippage protection.

```rust
pub fn swap_collateral(
    env: Env,
    caller: Address,
    in_asset: Address,
    out_asset: Address,
    amount_in: u128,
    min_out: u128,  // Slippage protection
) -> Result<u128, KineticRouterError> {
    // Execute swap
    let adapter = storage::get_dex_adapter(&env)?;
    let amount_out = adapter.swap_exact_in(
        &env,
        in_asset,
        out_asset,
        amount_in,
        min_out,
    )?;

    // Verify received amount meets minimum
    if amount_out < min_out {
        return Err(KineticRouterError::InsufficientSwapOut);
    }

    Ok(amount_out)
}
```

**Parameters**:
- `amount_in`: Exact amount to sell
- `min_out`: Minimum amount to receive
- If market moves adversely and output < min_out: REVERT

**User Responsibility**:
- User calculates acceptable min_out based on current market
- User includes buffer for slippage (e.g., 0.5% buffer)
- User sends TX

**Example**:
```
Current market: 1 USDC = 0.00008 BTC
User wants to swap 1000 USDC

Expected output: 1000 * 0.00008 = 0.08 BTC

With 0.5% slippage buffer: min_out = 0.08 * 0.995 = 0.0796 BTC

User calls: swap_collateral(..., min_out: 0.0796 BTC)

If DEX price has moved unfavorably:
  - Output = 0.078 BTC < 0.0796 BTC  -> REVERT
  - Swap rejected, no position change

If price is stable:
  - Output = 0.0799 BTC > 0.0796 BTC  -> SUCCESS
  - Swap executes, position changes
```

---

## Liquidation Economics

### Bonus as Liquidator Incentive

Liquidators are rewarded for removing undercollateralized positions.

```
Seized collateral = collateral_balance × (1 + bonus_bps / 10000)

Example:
  - Position has 100 XLM ($10) collateral
  - Liquidator covers $9 debt
  - Liquidator bonus: 5% (500 bps)
  - Seized collateral: 100 XLM × (1 + 500 / 10000) = 105 XLM
  - But only 100 XLM available
  - Liquidator receives: 100 XLM (worth $10)
  - Cost: $9 debt (repaid by collateral)
  - Profit: $1 per $9 liquidated = 11.1% return
```

### Protocol Fee Deduction

Part of liquidation bonus is claimed as protocol revenue.

```
Total seized = collateral × (1 + bonus_bps / 10000)
Liquidator receives = total_seized - protocol_fee
Protocol fee = total_seized × liquidation_fee_bps / 10000

Example:
  - Seized collateral: 105 XLM (worth $10.50)
  - Liquidation fee: 10% of bonus (0.5 XLM)
  - Liquidator receives: 105 - 0.5 = 104.5 XLM
  - Protocol fee: 0.5 XLM  -> treasury
```

### Prevention of Liquidator Collusion

Multiple economic safeguards prevent liquidators from extracting unfair value:

1. **Health Factor Requirement**: Position must be liquidatable (HF < 1.0)
   - Cannot liquidate healthy positions
   - Liquidation only permitted when protocol is at risk

2. **Auction Mechanism** (if implemented): Liquidations could be bid-on
   - Multiple liquidators can participate
   - Highest bidder wins, paying more for privilege

3. **Close Factor Limits**: Maximum amount liquidatable per TX
   - Cannot fully liquidate healthy positions
   - 50% close factor when HF is between threshold and 1.0
   - 100% close factor when HF falls below threshold (full liquidation allowed)
   - Prevents single liquidator from capturing all bonus on marginally-unhealthy positions

### Bad Debt Prevention

If liquidation insufficient to cover debt:

```
Position:
  - Collateral: 10 XLM ($1)
  - Debt: $100
  - HF: 0.01 (deeply underwater)

Liquidation attempt:
  - Close factor: 100% (HF < 0.5)
  - Debt to cover: $100
  - Max collateral: 10 XLM ($1)
  - Cannot repay full debt

Solution:
  - Collateral seized: 10 XLM ($1)
  - Debt remaining: $99 (bad debt)
  - Debt socialized across remaining suppliers
  - Bad debt is explicit event, not hidden
```

---

## Flash Loan Risks

### No Collateral Requirement

Flash loans permit borrowing without collateral.

```
Risk: Attacker borrows massive amount, uses for price manipulation

Protection:
  1. Borrowed amount must be repaid IN SAME TX
  2. Repayment is atomic (either full or revert)
  3. Cannot leave protocol with borrowed amount
  4. Premium ensures protocol still benefits even if used
  5. CPU limits prevent arbitrarily long execution
```

### Atomic Repayment Guarantee

Repayment is verified atomically after callback.

```
Execution:
  1. Transfer borrowed_amount to receiver
  2. Execute callback (user code)
  3. Verify balance: receiver.balance(asset) >= borrowed_amount + premium
     - If fails: REVERT (entire TX reverted)
     - Borrowed assets must be returned or TX fails
  4. If passes: premium collected, TX succeeds
```

**Implication**:
- Loan either succeeds atomically or fails completely
- No partial repayment
- No way to "borrow" assets from protocol (always repaid)

### Premium as Deterrent

High premiums discourage frivolous flash loan usage.

```
Example premium: 30 bps (0.30%)

Cost analysis:
  - Borrow 1,000,000 USDC for 1 TX
  - Premium: 1,000,000 × 30 / 10000 = 3,000 USDC
  - Cost: 3,000 USDC for atomic operations only
  - Must have > 3,000 USDC profit to be worthwhile
  - Economically viable only for real arbitrage/liquidation
```

### Flash Loan Vulnerability Classes

Despite mitigations, flash loans enable certain attacks:

1. **Price Manipulation**: Borrow large amount, affect DEX price
   - Mitigation: Circuit breaker prevents extreme prices
   - Mitigation: Other assets remain price-stable

2. **Liquidation Front-Running**: Use flash loan to liquidate position first
   - Mitigation: Liquidation whitelist can restrict access
   - Mitigation: Public liquidation opportunity (others can execute)

3. **Sandwich Attacks**: Borrow to influence swap price
   - Mitigation: Slippage protection prevents worse outcomes
   - Mitigation: Min output enforcement by user

---

## Audit History

### Consolidated Audit (Feb 2026)

**Audit Scope**: 8 specialized agents reviewing all aspects

**Summary**: 47 findings identified (5 High, 15 Medium, 19 Low, 8 Info)

### High Severity Findings (Fixed)

| ID | Issue | Status |
|---|-------|--------|
| H-01 | Swap fast-path HF omits oracle_to_wad, uses u128 |  Fixed |
| H-02 | initialize() lacks caller authentication |  Fixed |
| H-03 | update_reserve_configuration() bypasses validation |  Fixed |
| H-04 | No post-liquidation HF improvement check |  Fixed |
| H-05 | Deeply underwater positions become unliquidatable |  Fixed |

### Medium Severity Findings

| ID | Issue | Status |
|---|-------|--------|
| M-01 | Unvalidated swap handler whitelist |  Fixed |
| M-02 | No mutual check between upgrade/pool admin |  Deferred to Phase 2 |
| M-03 | No timelock on admin operations |  Deferred to Phase 2 |
| M-04 | Emergency admin can pause AND unpause |  Fixed |
| M-05 | Oracle price_precision not validated |  Fixed |
| M-06 | No timelock on oracle changes |  Deferred to Phase 2 |
| M-07 | Global staleness threshold, no per-asset |  Accepted (global works) |
| M-08 | Missing reentrancy guards | Fixed (ReentrancyGuard RAII pattern with PROTOCOL_LOCKED) |
| M-09 | swap_collateral has CEI violation | Accepted (reentrancy guard provides protection) |
| M-10 | Fee-on-transfer token risk |  Accepted (Stellar tokens don't have fees) |
| M-11 | Self-liquidation allowed |  Accepted (Aave V3 precedent) |
| M-12 | min_remaining_debt + collateral cap conflict |  Fixed by H-05 |
| M-13 | Two-step liquidation lacks min_remaining_debt |  Fixed |
| M-14 | Symmetric rounding doesn't favor protocol |  Fixed |
| M-15 | claim_all_rewards quadratic complexity |  Fixed |

### Low Severity Findings

Key fixes applied:
- L-10: Flash loan premium rounds UP (percent_mul_up)
- L-14: UserConfiguration bounds-checks reserve_index < 64
- L-13: All raw panic!() replaced with panic_with_error!()

### Deferred Findings

Phase 2 (future improvements, not blocking production):
- M-02: Admin unification (upgrade vs pool admin)
- M-03, M-06: Timelocks on admin operations
- M-07: Per-asset staleness thresholds

### Security Fixes Applied

**Total Commits**: 11 critical/high/medium findings fixed
**File Changes**: 30 files modified
**New Code**: Comprehensive U256 arithmetic, enhanced validation
**Status**:  All contracts compile successfully

---

## Key Takeaways

### For Users
- Your positions are protected by health factor enforcement
- Liquidation improves your HF if it improves at all
- Pauses prevent unexpected losses during emergencies
- Whitelists restrict access only if configured

### For Developers
- use `require_auth()` for user-initiated operations
- Reentrancy is blocked by explicit `ReentrancyGuard` (RAII pattern with `PROTOCOL_LOCKED` flag)
- Validate all external data (prices, amounts)
- U256 arithmetic for large intermediate values

### For Administrators
- Pool admin controls normal operations
- Both emergency admin and pool admin can pause; only pool admin can unpause
- Two-step transfers prevent accidental lockouts
- All parameters validated before storage

### For Auditors
- Protocol invariants are enforced at every step
- Authorization model is robust
- Oracle integration has multiple safeguards
- Cross-contract interactions are carefully managed

---

**Last Updated**: March 2026
**Audit Status**: Phase 1 Complete, Phase 2 Planned
