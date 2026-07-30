# 11. Admin & Governance

## Overview

K2's administrative architecture separates concerns between **Pool Admin** (configuration authority) and **Emergency Admin** (rapid incident response). This two-role model prevents single-point compromise while enabling quick response to protocol threats.

### Design Philosophy

1. **Separation of Duties**: Pool admin and emergency admin are distinct roles with clearly bounded responsibilities
2. **Least Privilege**: Each role has only the permissions required for its function
3. **Two-Step Transfers**: Admin transitions use proposal + acceptance to prevent mis-addressing
4. **Fail-Safe Defaults**: Protocol defaults to paused state during critical transitions
5. **Audit Trail**: All administrative actions emit events for monitoring and transparency

### Key Principles

- **Pool Admin**: Manages protocol configuration, reserve parameters, whitelists, and future contract upgrades
- **Emergency Admin**: Only capability is to pause the protocol during security incidents
- **Unpause Authority**: Only pool admin can unpause, preventing emergency admin from undoing pause
- **Authorization**: All admin operations require caller authentication via Soroban's authorization tree

---

## Admin Roles

### Pool Admin

**Responsibilities**:
- Reserve initialization and configuration
- Parameter updates (LTV, liquidation thresholds, bonuses, caps)
- Interest rate strategy assignment
- Flash loan premium configuration
- Treasury address management
- Whitelist/blacklist management
- Contract lifecycle upgrades (via upgrade admin)
- Unpausing the protocol

**Scope**: All configuration-related operations

**Caller Pattern**:
```rust
let admin = storage::get_pool_admin(&env)?;
admin.require_auth();  // Verify authorization via Soroban auth tree
// Proceed with admin operation
```

**Events Emitted**: All parameter changes, reserve operations, admin transfers

### Emergency Admin

**Responsibilities**:
- Pause the protocol in response to security incidents
- Pause reserve deployment (via pool-configurator)
- Unpause reserve deployment (via pool-configurator)

**Scope**: Pause/unpause protocol operations and reserve deployment

**Caller Pattern**:
```rust
let emergency_admin = storage::get_emergency_admin(&env)
    .ok_or(KineticRouterError::Unauthorized)?;
emergency_admin.require_auth();
storage::set_paused(&env, true);
```

**Security Constraint**: Emergency admin cannot unpause. This prevents a compromised emergency key from deliberately undoing a protective pause set by the pool admin.

**Events Emitted**: ProtocolPausedEvent

### Role Separation Benefits

| Operation | Pool Admin | Emergency Admin | Rationale |
|-----------|-----------|-----------------|-----------|
| Initialize reserves | ✅ | ❌ | Configuration authority |
| Update parameters | ✅ | ❌ | Protocol management |
| Pause protocol | ✅ | ✅ | Both roles can pause (via `validate_emergency_admin`) |
| Unpause protocol | ✅ | ❌ | Prevent false resumption |
| Pause reserve deployment | ✅ | ✅ | Both roles (via pool-configurator) |
| Unpause reserve deployment | ✅ | ✅ | Both roles (via pool-configurator) |
| Change pool admin | ✅ | ❌ | Governance transitions |
| Change emergency admin | ✅ | ❌ | Emergency role management |

---

## Pool Admin

### Responsibilities

Pool admin serves as the protocol's configuration authority, responsible for:

1. **Reserve Lifecycle**: Adding new assets, updating parameters, deactivating reserves
2. **Risk Parameters**: LTV, liquidation thresholds, bonuses, supply/borrow caps
3. **Economic Parameters**: Flash loan premium, treasury address, reserve factor
4. **Access Control**: User and liquidator whitelists/blacklists, swap handler whitelist
5. **Oracle Configuration**: Asset whitelisting, price feed management, manual overrides
6. **Protocol Maintenance**: Pausing/unpausing, managing contract addresses

### Required Signing Authority

All pool admin operations must:

1. Be signed by the current pool admin address
2. Call `.require_auth()` for verification
3. Include the caller in the Soroban authorization tree

**Example**: Setting a reserve parameter

```bash
# Pool admin must sign this transaction
stellar contract invoke \
  --id CONTRACT_ID \
  --source POOL_ADMIN_SECRET_KEY \
  -- set_reserve_factor \
  --asset USDC_ADDRESS \
  --reserve_factor 1000  # 10%
```

The transaction fails if:
- Signer is not the current pool admin
- Admin's key is not authorized for the function call
- Authorization tree doesn't match expected structure

---

## Pool Admin

### Detailed Functions

This section documents each pool admin operation available through the kinetic-router contract.

#### Flash Loan Premium Configuration

**Function**: `set_flash_loan_premium(env: Env, premium_bps: u128)`

**Purpose**: Configure the fee charged for flash loans

**Parameters**:
- `premium_bps`: Basis points (0-10000). 100 = 1% fee.

**Validation**:
- Must not exceed `get_flash_loan_premium_max()`
- Example range: 50-200 bps (0.5%-2%)

**Example**:
```bash
# Set flash loan fee to 0.09% (9 basis points)
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_loan_premium \
  --premium_bps 9
```

**Event**: `FlashLoanPremiumUpdatedEvent` with old and new values

**Effect**: Immediate. New flash loans use the updated fee.

#### Flash Loan Premium Maximum

**Function**: `set_flash_loan_premium_max(env: Env, premium_max_bps: u128)`

**Purpose**: Set ceiling for flash loan premium to prevent excessive fees

**Parameters**:
- `premium_max_bps`: Maximum allowed basis points

The default is 100 bps (1%), set during `initialize()`. Increasing to 500 bps (5%) would raise the ceiling and allow higher premiums to be configured.

**Usage**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_loan_premium_max \
  --premium_max_bps 500
```

#### Health Factor Liquidation Threshold

**Function**: `set_hf_liquidation_threshold(env: Env, threshold: u128)`

**Purpose**: Configure the health factor below which positions become liquidatable

**Parameters**:
- `threshold`: Health factor value in WAD (1e18)
- Default: 1.0 (1e18) = position is liquidatable when HF < 1.0

**Precision**: This value is in WAD (1e18). Example:
- 1.0 = `1_000_000_000_000_000_000`
- 1.05 = `1_050_000_000_000_000_000`

**Setting**: 1.0 is standard (position liquidatable when undercollateralized)

```bash
# Set to 1.05 (positions become liquidatable at 5% cushion above 1.0)
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_hf_liquidation_threshold \
  --threshold 1050000000000000000
```

#### Partial Liquidation Health Factor Threshold

**Function**: `set_partial_liq_hf_threshold(env: Env, threshold: u128)`

**Purpose**: Controls the boundary between partial and full liquidation

**Parameters**:
- `threshold`: Health factor in WAD
- Default: 0.5 (5e17)

**Behavior**:
- HF >= threshold: Liquidator can close up to 50% of debt (partial liquidation)
- HF < threshold: Liquidator can close up to **100%** of debt (full liquidation allowed). This also triggers when individual debt or collateral is below `MIN_CLOSE_FACTOR_THRESHOLD`.

**Example**:
```bash
# Trigger partial liquidation at HF < 0.5
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_partial_liq_hf_threshold \
  --threshold 500000000000000000
```

#### Minimum Swap Output

**Function**: `set_min_swap_output_bps(env: Env, min_output_bps: u128)`

**Purpose**: Set minimum acceptable slippage for flash liquidation swaps (protection against sandwich attacks)

**Parameters**:
- `min_output_bps`: Basis points of input amount acceptable as output
- Default: 9800 (98% slippage protection)
- Range: Enforced between `MIN_SWAP_OUTPUT_FLOOR_BPS` and `BASIS_POINTS_MULTIPLIER`

**Example**:
```bash
# Accept minimum 97% of expected output (3% max slippage)
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_min_swap_output_bps \
  --min_output_bps 9700
```

**Security Note**: Lower values increase slippage vulnerability. Keep >= 9600 (96%) for protection.

#### Treasury Address

**Function**: `set_treasury(env: Env, treasury: Address)`

**Purpose**: Configure the address receiving protocol fees

**Parameters**:
- `treasury`: Stellar account or contract address

**Example**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_treasury \
  --treasury CAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABSC4
```

**Fee Destination**: All protocol fees (from interest, flash loans) accumulate here

Consider using a multisig account for treasury control

#### Connected Service Addresses

**Flash Liquidation Helper**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_liquidation_helper \
  --helper HELPER_CONTRACT_ADDRESS
```

**Pool Configurator**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_pool_configurator \
  --configurator CONFIG_CONTRACT_ADDRESS
```

**Incentives Contract**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_incentives_contract \
  --incentives_contract INCENTIVES_ADDRESS
```

---

## Emergency Admin

### Protocol Pause

**Function**: `pause(env: Env, caller: Address) -> Result<(), KineticRouterError>`

**Purpose**: Immediately halt all user operations during security incidents

**Caller**: Emergency admin or pool admin (validated via `validate_emergency_admin`)

**Authorization**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source EMERGENCY_ADMIN_KEY \
  -- pause
```

### Impact of Pause

When paused = true, the following operations revert with `AssetPaused` error:

- Supply
- Borrow
- Repay
- Withdraw
- Liquidation
- Flash loans
- Collateral swaps

**Unaffected Operations** (read-only):
- Get health factor
- Get reserve data
- Check balances
- View prices

### Check Pause Status

```bash
# View pause status
stellar contract invoke \
  --id ROUTER_ID \
  -- is_paused
```

Returns `true` if protocol is paused, `false` otherwise.

---

## Admin Authorization

### Soroban Authorization Tree

Every K2 transaction builds an authorization tree that specifies which addresses authorized which operations.

#### Verification Process

1. **Transaction Signing**: Caller signs TX envelope with their signing key
2. **Tree Construction**: Soroban builds auth tree containing all invocations
3. **Authorization Check**: When contract calls `caller.require_auth()`:
   - Soroban verifies caller appears in auth tree
   - Verifies caller authorized this contract/function invocation
   - Confirms the call path matches authorized structure

#### Pattern

```rust
// Admin operation
pub fn set_reserve_factor(
    env: Env,
    asset: Address,
    reserve_factor: u32,
) -> Result<(), KineticRouterError> {
    let admin = storage::get_pool_admin(&env)?;
    admin.require_auth();  // Verify admin authorized this call

    // Only proceeds if authorized
    // ...
}
```

#### Example: Cross-Contract Call

```
User Transaction (signed by pool_admin):
| AuthPath: pool_admin -> set_reserve_factor
|  | require_auth(pool_admin)  matches auth tree
|  -Router calls PoolConfigurator
|      | PoolConfigurator calls Router.update_reserve_configuration
|      |  -require_auth(pool_admin)  inherited from auth tree
```

#### Key Points

- `require_auth()` called once per authorized invoker per transaction
- Cross-contract calls inherit authorization from parent contract
- Failing `require_auth()` reverts the entire transaction
- No additional authorization needed for subsequent calls in auth chain

---

## Two-Step Admin Transfer

### Rationale

Two-step admin transfer prevents accidental loss of admin privileges due to typos or misaddressed transfers.

**Scenario**: Pool admin copies wrong address into transfer function
- **One-step model**: Admin immediately lost to wrong address (unrecoverable)
- **Two-step model**: Proposed admin must explicitly accept, preventing mistakes

### Process

#### Step 1: Propose New Admin

Current pool admin proposes a new admin address.

**Function**: `propose_pool_admin(env: Env, caller: Address, pending_admin: Address)`

**Caller**: Current pool admin (must be authorized)

**Effect**:
- Stores proposed admin address
- Clears any previous pending proposal (emits cancellation event)
- Emits `AdminProposedEvent`

**Example**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source CURRENT_ADMIN_KEY \
  -- propose_pool_admin \
  --pending_admin NEW_ADMIN_ADDRESS
```

#### Step 2: Accept Admin Role

Proposed admin confirms acceptance and becomes active admin.

**Function**: `accept_pool_admin(env: Env, caller: Address)`

**Caller**: The proposed admin address (must be authorized)

**Verification**:
- Caller must match the pending admin address exactly
- Caller must sign the transaction

**Effect**:
- Promotes proposed admin to active admin
- Clears pending proposal
- Emits `AdminAcceptedEvent` with previous and new admin

**Example**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source NEW_ADMIN_KEY \
  -- accept_pool_admin
```

### Error Conditions

| Condition | Error | Resolution |
|-----------|-------|-----------|
| No pending admin exists | `NoPendingAdmin` | Call `propose_pool_admin` first |
| Caller != pending admin | `InvalidPendingAdmin` | Use correct address to accept |
| Caller not authorized | `Unauthorized` | Use pending admin's signing key |
| No current admin set | `Unauthorized` | Initialize protocol first |

### Canceling a Proposal

Current pool admin can cancel a pending proposal before it's accepted.

**Function**: `cancel_pool_admin_proposal(env: Env, caller: Address)`

**Effect**:
- Clears pending admin
- Emits `AdminProposalCancelledEvent`

**Example**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source CURRENT_ADMIN_KEY \
  -- cancel_pool_admin_proposal
```

### Getting Pending Admin

Query the address waiting to accept admin role.

**Function**: `get_pending_pool_admin(env: Env) -> Result<Address, KineticRouterError>`

**Returns**: Pending admin address if proposal exists, `NoPendingAdmin` error otherwise

```bash
stellar contract invoke \
  --id ROUTER_ID \
  -- get_pending_pool_admin
```

### Emergency Admin Transfer

Same two-step process for emergency admin role.

**Propose**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- propose_emergency_admin \
  --pending_admin NEW_EMERGENCY_ADMIN
```

**Accept**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source NEW_EMERGENCY_ADMIN_KEY \
  -- accept_emergency_admin
```

**Cancel**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- cancel_emergency_admin_proposal
```

---

## Admin Transition Procedures

### Scheduled Handoff

Use this procedure for planned admin transitions (e.g., moving to multisig, rotating signers).

#### Phase 1: Preparation (Day 1)

1. **Document Current State**
   ```bash
   # Get current admins
   stellar contract invoke --id ROUTER_ID -- get_admin
   stellar contract invoke --id ROUTER_ID -- get_pending_pool_admin
   ```

2. **Verify New Admin Address**
   - Triple-check address spelling
   - Confirm new admin has access to signing key
   - Ensure new admin understands responsibilities

3. **Notify Stakeholders**
   - Alert ecosystem partners
   - Update status pages
   - Schedule monitoring alerts

#### Phase 2: Proposal (Day 2)

1. **Current Admin Proposes**
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source CURRENT_ADMIN_KEY \
     -- propose_pool_admin \
     --pending_admin NEW_ADMIN_ADDRESS
   ```

2. **Verify Proposal**
   ```bash
   # Confirm pending admin is correct
   stellar contract invoke \
     --id ROUTER_ID \
     -- get_pending_pool_admin
   ```

3. **Communicate to New Admin**
   - Send new admin the pending confirmation
   - Provide acceptance instructions

#### Phase 3: Acceptance (Day 3+)

1. **New Admin Accepts**
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source NEW_ADMIN_KEY \
     -- accept_pool_admin
   ```

2. **Verify Transition**
   ```bash
   # Confirm new admin is active
   stellar contract invoke \
     --id ROUTER_ID \
     -- get_admin
   ```

3. **Test Admin Authority**
   - New admin tries a safe operation (e.g., check flash loan premium)
   - Confirm no errors occur

4. **Communicate Success**
   - Notify ecosystem
   - Update documentation
   - Archive old admin key securely

### Emergency Admin Rotation

Same process as pool admin but for emergency admin role.

**Key Difference**: Current pool admin proposes emergency admin changes (not emergency admin self-proposing).

### Rollback Procedure

If proposal was sent to wrong address:

1. **Current admin cancels proposal**
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source CURRENT_ADMIN_KEY \
     -- cancel_pool_admin_proposal
   ```

2. **Wait for confirmation**
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     -- get_pending_pool_admin
   # Should return NoPendingAdmin error
   ```

3. **Retry with correct address**
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source CURRENT_ADMIN_KEY \
     -- propose_pool_admin \
     --pending_admin CORRECT_ADDRESS
   ```

---

## Reserve Management

### Adding Reserves (Initialization)

New assets are added through `init_reserve()` in the **pool-configurator contract**, which validates pool admin authorization and then calls the router's `init_reserve()`. The router's `init_reserve()` requires the caller to be the registered pool configurator contract (via `validate_pool_configurator`), not the pool admin directly.

#### Pre-Deployment Checklist

1. **Asset Information**
   - Token contract address (SEP-41 compliant)
   - Decimals (0-38, validated to prevent u128 overflow in `10^decimals`)
   - Price oracle integration confirmed

2. **Token Contracts**
   - aToken implementation contract deployed
   - Variable debt token implementation deployed

3. **Interest Rate Strategy**
   - Interest rate strategy contract deployed and tested
   - Slope parameters reviewed

4. **Risk Parameters**
   - LTV: 0-10000 bps (e.g. 3000-8000)
   - Liquidation Threshold: > LTV + 50 bps (e.g. 4000-9000)
   - Liquidation Bonus: 0-10000 bps (e.g. 500-1000)
   - Reserve Factor: 0-10000 bps (e.g. 1000-2000)
   - Supply Cap: Max tokens (0 = unlimited)
   - Borrow Cap: Max tokens (0 = unlimited)

#### Deployment Command

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- init_reserve \
  --underlying_asset USDC_ADDRESS \
  --a_token_impl A_TOKEN_CONTRACT \
  --variable_debt_impl DEBT_TOKEN_CONTRACT \
  --interest_rate_strategy RATE_STRATEGY_ADDRESS \
  --treasury TREASURY_ADDRESS \
  --params '{
    "decimals": 9,
    "ltv": 7500,
    "liquidation_threshold": 8000,
    "liquidation_bonus": 500,
    "reserve_factor": 1000,
    "supply_cap": "10000000",
    "borrow_cap": "5000000",
    "borrowing_enabled": true,
    "flashloan_enabled": true
  }'
```

#### Validation Rules

| Parameter | Min | Max | Example |
|-----------|-----|-----|---------|
| ltv | 0 | 10000 | 7500 (75%) |
| liquidation_threshold | ltv+50 | 10000 | 8000 (80%) |
| liquidation_bonus | 0 | 10000 | 500 (5%) |
| reserve_factor | 0 | 10000 | 1000 (10%) |
| decimals | 0 | 38 | 9 (USDC) |
| supply_cap | 0 | 2^64-1 | 1_000_000 |
| borrow_cap | 0 | 2^64-1 | 500_000 |

**Safety Checks**:
- liquidation_threshold > ltv (always)
- liquidation_threshold >= ltv + 50 bps (buffer)
- All percentages <= 10000 bps
- Decimals in range 0-38 (prevents `10^decimals` overflow in u128). The bitmap stores 8 bits (0-255) but validation rejects values > 38.

#### Events Emitted

- `ReserveInitializedEvent`: Main initialization event
- `ReserveConfiguredEvent`: Reserve added to tracking

#### Post-Deployment Verification

```bash
# Get reserve data
stellar contract invoke \
  --id ROUTER_ID \
  -- get_reserve_data \
  --asset USDC_ADDRESS

# Verify parameters match config
```

### Updating Reserve Parameters

#### Configure as Collateral

Modify LTV, liquidation threshold, and bonus for an existing reserve.

**Function**: `configure_reserve_as_collateral()`

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- configure_reserve_as_collateral \
  --asset USDC_ADDRESS \
  --ltv 7500 \
  --liquidation_threshold 8000 \
  --liquidation_bonus 500
```

**Validation**: Same rules as init_reserve

**Effect**: Immediate. Existing positions use new parameters.

**Monitoring**: Watch for liquidations after threshold changes.

#### Enable/Disable Borrowing

**Function**: `enable_borrowing_on_reserve()`

```bash
# Enable borrowing
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- enable_borrowing_on_reserve \
  --asset USDC_ADDRESS \
  --stable_rate_enabled false
```

**Effect**: Users can now borrow the asset (if not otherwise restricted)

#### Reserve Factor

Configure protocol's share of accrued interest.

**Function**: `set_reserve_factor()`

```bash
# Set 10% reserve factor (90% to suppliers, 10% to protocol)
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_factor \
  --asset USDC_ADDRESS \
  --reserve_factor 1000
```

**Range**: 0-10000 bps

**Effect**: Applies to future interest accrual only (retroactive)

---

## Parameter Configuration

### LTV (Loan-to-Value)

Maximum percentage of collateral value borrowers can use as credit.

**Range**: 0-10000 bps (0-100%)

**Example Values**:
- Stablecoins: 7500-8500 (75-85%)
- Major cryptocurrencies: 6000-7500 (60-75%)
- Minor/volatile assets: 3000-5000 (30-50%)

**Example**:
```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- configure_reserve_as_collateral \
  --asset USDC_ADDRESS \
  --ltv 8000 \
  --liquidation_threshold 8500 \
  --liquidation_bonus 500
```

**Health Factor Impact**:
```
HF = (collateral_value * ltv / 10000) / (debt_value)
```

Lower LTV  -> Higher HF  -> More protection  -> Less liquidation risk

### Liquidation Threshold

The collateral value percentage at which positions become liquidatable.

**Range**: Must be > LTV + 50 bps

**Example Values**:
- Stablecoins: 8000-9000 (80-90%)
- Major cryptocurrencies: 7000-8000 (70-80%)
- Minor/volatile assets: 5000-6000 (50-60%)

**Example**:
```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- configure_reserve_as_collateral \
  --asset USDC_ADDRESS \
  --ltv 8000 \
  --liquidation_threshold 8500 \
  --liquidation_bonus 500
```

**Health Factor Calculation**:
```
HF = (collateral_value * liquidation_threshold / 10000) / (debt_value)
```

Position liquidatable when HF < 1.0

### Liquidation Bonus

Discount percentage liquidators receive on collateral purchase.

**Range**: 0-10000 bps (0-100%)

**Example Values**:
- Stablecoins: 500-700 (5-7%)
- Major cryptocurrencies: 700-1000 (7-10%)
- Minor/volatile assets: 1000-2000 (10-20%)

**Economics**:
- Higher bonus  -> More liquidator incentive  -> Faster liquidations
- Lower bonus  -> Better collateral price  -> More funds recovered

**Example**:
```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- configure_reserve_as_collateral \
  --asset USDC_ADDRESS \
  --ltv 8000 \
  --liquidation_threshold 8500 \
  --liquidation_bonus 500
```

### Reserve Factor

Protocol's percentage share of accrued interest.

**Range**: 0-10000 bps (0-100%)

**Example Values**: 1000-2000 (10-20%)

**Example**:
```bash
# Allocate 15% of interest to protocol
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_factor \
  --asset USDC_ADDRESS \
  --reserve_factor 1500
```

**Revenue Model**:
- If reserve factor = 1500 (15%)
  - 85% of interest goes to suppliers
  - 15% of interest accrues to protocol treasury

**Budget Impact**: Higher reserve factor reduces lender APY

---

## Reserve Activation/Deactivation

### Freezing and Unfreezing

Freeze a reserve to halt new deposits and borrows (emergency use).

#### Set Reserve Active Status

**Function**: `set_reserve_active()`

```bash
# Deactivate/freeze reserve
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_active \
  --asset USDC_ADDRESS \
  --active false
```

**When Active = False**:
-  New supplies blocked
-  New borrows blocked
-  Withdrawals allowed
-  Repays allowed
-  Liquidations allowed

**Use Cases**:
- Security incident affecting asset
- Deprecating stablecoin
- Removing illiquid asset

**Recovery**:
```bash
# Re-activate reserve
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_active \
  --asset USDC_ADDRESS \
  --active true
```

---

## Supply Cap Management

### Setting Supply Caps

Limit total supplied amount of an asset.

**Function**: `set_supply_cap()`

```bash
# Limit USDC supply to 10M tokens
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_supply_cap \
  --asset USDC_ADDRESS \
  --supply_cap 10000000  # 10M with 6 decimals
```

**Parameters**:
- `supply_cap`: Max tokens (not WAD). For USDC (6 decimals): 1_000_000 = 1M tokens
- 0 = unlimited

**Validation**:
- Must fit in u64 (18 quintillion tokens max)

**Effect**:
- Deposits that would exceed cap revert
- Current supply + new deposit > cap  -> Rejected

**Monitoring**:
```bash
# View reserve data to check current supply
stellar contract invoke \
  --id ROUTER_ID \
  -- get_reserve_data \
  --asset USDC_ADDRESS
```

### Use Cases

1. **New Asset Onboarding**: Start with conservative cap, increase as liquidity grows
2. **Risk Limiting**: Cap exposure to volatile or illiquid assets
3. **Market Stabilization**: Manage protocol's market impact on asset price
4. **Testing**: Cap at 0 during integration testing

### Monitoring Supply Against Cap

```bash
# Check current supply
RESERVE_DATA=$(stellar contract invoke --id ROUTER_ID -- get_reserve_data --asset USDC_ADDRESS)

# Extract total_scaled_supply and divideIndex
# supply = total_scaled_supply / index

# Alert if supply > 0.9 * cap
```

---

## Borrow Cap Management

### Setting Borrow Caps

Limit total borrowed amount of an asset.

**Function**: `set_borrow_cap()`

```bash
# Limit USDC borrowing to 5M tokens
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_borrow_cap \
  --asset USDC_ADDRESS \
  --borrow_cap 5000000  # 5M with 6 decimals
```

**Parameters**:
- `borrow_cap`: Max tokens (not WAD)
- 0 = unlimited

**Validation**:
- Must fit in u64

**Effect**:
- Borrows that would exceed cap revert
- Current debt + new borrow > cap  -> Rejected

### Example Ratios

| Asset Type | Supply Cap | Borrow Cap | Ratio |
|-----------|-----------|-----------|-------|
| Stablecoins | 50M | 40M | 80% |
| Major crypto | 10M | 7M | 70% |
| Minor assets | 1M | 500K | 50% |

**Rationale**: Borrow cap < supply cap ensures solvent protocol (deposits > borrows)

### Emergency Cap Reduction

If asset becomes risky:

1. **Reduce Borrow Cap** (faster recovery)
   ```bash
   stellar contract invoke \
     --id POOL_CONFIG_ID \
     --source POOL_ADMIN_KEY \
     -- set_borrow_cap \
     --asset RISKY_ASSET \
     --borrow_cap 0  # Halt new borrows
   ```

2. **Reduce Supply Cap** (if needed)
   ```bash
   stellar contract invoke \
     --id POOL_CONFIG_ID \
     --source POOL_ADMIN_KEY \
     -- set_supply_cap \
     --asset RISKY_ASSET \
     --supply_cap 0  # Halt new supplies
   ```

3. **Freeze Reserve** (last resort)
   ```bash
   stellar contract invoke \
     --id POOL_CONFIG_ID \
     --source POOL_ADMIN_KEY \
     -- set_reserve_active \
     --asset RISKY_ASSET \
     --active false
   ```

---

## Liquidation Parameters

### Close Factor

Percentage of borrower's debt that can be liquidated in a single call.

**Default Close Factor**: 50% (5000 bps) — applies when HF >= partial liquidation threshold (default 0.5)

**Full Liquidation**: When HF < partial liquidation threshold, close factor increases to **100%** (full liquidation allowed). This also applies when individual debt or collateral values are below `MIN_CLOSE_FACTOR_THRESHOLD`.

**Example (partial)**:
- Borrower debt: 1000 USDC, HF = 0.8
- Liquidation call: Liquidator can close up to 500 USDC (50%)

**Example (full)**:
- Borrower debt: 1000 USDC, HF = 0.3 (below threshold)
- Liquidation call: Liquidator can close up to 1000 USDC (100%)

**Rationale**:
- Partial liquidation prevents unnecessary seizure of entire position
- Full liquidation enables efficient resolution of deeply underwater positions
- Configurable via `set_partial_liq_hf_threshold`

### Liquidation Bonus (Per Asset)

Discount applied per asset configured in `configure_reserve_as_collateral()`

See [Parameter Configuration - Liquidation Bonus](#liquidation-bonus)

---

## Flash Loan Premium

### Configuration

Pool admin can set the fee charged for flash loans.

**Function**: `set_flash_loan_premium()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_loan_premium \
  --premium_bps 9  # 0.09%
```

**Parameters**:
- `premium_bps`: Basis points (0-10000)
- 100 = 1%

**Example Range**: 5-100 bps (0.05%-1%)

### Maximum Premium

Set ceiling to prevent excessive fees.

**Function**: `set_flash_loan_premium_max()`

```bash
# Cap maximum premium at 500 bps (5%)
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_loan_premium_max \
  --premium_max_bps 500
```

**Validation**: `set_flash_loan_premium()` verifies current premium <= max

### Economic Implications

| Premium | Use Case |
|---------|----------|
| 5 bps | Earn arbitrage bots (low friction) |
| 25 bps | Standard DeFi flash loans |
| 100+ bps | Discourage flash loan usage |

**Revenue**: All premium fees go to protocol treasury, distributed per reserve factor

### Fee Calculation

```
fee = amount * premium_bps / 10000
```

Example: 1000 USDC flash loan at 9 bps
```
fee = 1000 * 9 / 10000 = 0.9 USDC
```

---

## Interest Rate Configuration

### Interest Rate Strategy

Each reserve uses an independent interest rate strategy contract.

**Purpose**: Define how interest rates respond to utilization

### Setting Interest Rate Strategy

**Function**: `set_reserve_interest_rate()`

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_interest_rate \
  --asset USDC_ADDRESS \
  --rate_strategy NEW_STRATEGY_ADDRESS
```

**Effect**: Applies to all future interest accrual

**Parameters**: Determined by strategy contract (e.g., slope, base rate, optimal utilization)

### Monitoring Interest Rates

```bash
# Get current reserve state (includes borrow/supply APY)
stellar contract invoke \
  --id ROUTER_ID \
  -- get_reserve_data \
  --asset USDC_ADDRESS
```

Returns `current_borrow_rate` and `current_supply_rate` in RAY (1e27)

### Updating Strategy Parameters

If strategy contract supports governance, pool admin can update parameters through the strategy contract itself (not router).

Consider creating new strategy contract instance rather than modifying existing one (easier rollback)

---

## Oracle Management

### Asset Whitelisting

Only whitelisted assets can have prices fetched from oracle.

**Function**: `add_oracle_asset()`

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- add_oracle_asset \
  --asset '{"Stellar": "CAAA..."}'
```

**Asset Type**: Either `{"Stellar": address}` or `{"Soroban": address}`

**Effect**: Asset now has oracle tracking enabled

### Asset Removal

Remove asset from oracle whitelist (prices no longer tracked).

**Function**: `remove_oracle_asset()`

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- remove_oracle_asset \
  --asset '{"Stellar": "CAAA..."}'
```

**Consequence**: Any position using this asset as collateral cannot calculate health factor

### Enabling/Disabling Assets

Disable price feed without removing from whitelist.

**Function**: `set_oracle_asset_enabled()`

```bash
# Disable USDC price feed temporarily
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_oracle_asset_enabled \
  --asset '{"Stellar": "USDC_ADDRESS"}' \
  --enabled false

# Re-enable
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_oracle_asset_enabled \
  --asset '{"Stellar": "USDC_ADDRESS"}' \
  --enabled true
```

---

## Oracle Signer Management

K2 uses RedStone signers to validate price feeds.

### Adding Signers

RedStone data is signed by trusted signers. Pool admin can add signers.

**Function**: Through price oracle contract

```bash
stellar contract invoke \
  --id PRICE_ORACLE_ID \
  --source POOL_ADMIN_KEY \
  -- add_signer \
  --signer_address REDSTONE_SIGNER_ADDRESS
```

### Removing Signers

Deactivate untrustworthy signer.

```bash
stellar contract invoke \
  --id PRICE_ORACLE_ID \
  --source POOL_ADMIN_KEY \
  -- remove_signer \
  --signer_address SIGNER_TO_REMOVE
```

### Signer Threshold

Minimum number of valid signatures required per price update.

**Function**: Through price oracle contract

```bash
stellar contract invoke \
  --id PRICE_ORACLE_ID \
  --source POOL_ADMIN_KEY \
  -- set_signer_threshold \
  --threshold 2  # Require 2-of-N signatures
```

**Security**: Higher threshold = more decentralized but slower updates

---

## Price Feed Configuration

### Manual Price Overrides

Emergency tool to override oracle prices during data provider outages.

**Function**: `set_oracle_manual_override()`

```bash
# Set USDC = 1.0 USD until timestamp
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_oracle_manual_override \
  --asset '{"Stellar": "USDC_ADDRESS"}' \
  --price 1000000000000000  # 1.0 (WAD) \
  --expiry_timestamp 1707950400  # Unix timestamp
```

**Parameters**:
- `price`: Override price in WAD (1e18). Pass `None` to remove override
- `expiry_timestamp`: Unix timestamp when override expires. Required when setting price.

**Constraints**:
- Expiry must be future timestamp
- Override duration capped at 7 days
- Price change validated against circuit breaker

**Use Case**: Data provider temporarily unavailable, manually set stable prices for major assets

### Removing Overrides

```bash
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_oracle_manual_override \
  --asset '{"Stellar": "USDC_ADDRESS"}' \
  --price None \
  --expiry_timestamp None
```

### Custom Oracle Configuration

Route specific assets to alternative price feeds.

**Function**: Through price oracle contract

```bash
stellar contract invoke \
  --id PRICE_ORACLE_ID \
  --source POOL_ADMIN_KEY \
  -- set_custom_oracle \
  --asset ASSET_ADDRESS \
  --oracle_contract CUSTOM_ORACLE_ADDRESS \
  --max_age_seconds 3600
```

---

## Treasury Management

### Treasury Address

Stores protocol fees and can be configured by pool admin.

**Setting Treasury**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_treasury \
  --treasury TREASURY_ADDRESS
```

Consider using multisig account or timelock governance contract for treasury

### Fee Accumulation

Sources of protocol fees:

1. **Interest Reserve Factor**: % of accrued interest per reserve factor configuration
2. **Flash Loan Premium**: All flash loan fees
3. **Liquidation Incentives** (future): Potential liquidation success fees

### Fee Withdrawal

Treasury withdrawal mechanisms handled by treasury contract itself (not router).

**Example Pattern**:
```bash
# Treasury contract sends aTokens to treasury wallet
treasury.withdraw_atoken(usdc_atoken, amount)
```

---

## Emergency Controls

### Protocol Pause

Emergency admin can pause all user operations during security incidents.

**Function**: `pause()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source EMERGENCY_ADMIN_KEY \
  -- pause
```

**Immediate Effect**: All user operations blocked

**Operations Blocked**:
- Supply
- Withdraw
- Borrow
- Repay
- Liquidation
- Flash loans
- Collateral swaps

### Unpause Authority

**Only pool admin can unpause** (emergency admin cannot reverse its own pause).

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- unpause
```

**Rationale**: Prevents emergency admin from unpausing after setting pause (security drift)

### Emergency Incident Response

1. **Detect Issue** (monitoring alerting)
   - Abnormal liquidations
   - Price manipulation
   - Contract vulnerability

2. **Emergency Pause** (< 1 minute)
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source EMERGENCY_ADMIN_KEY \
     -- pause
   ```

3. **Investigate & Fix** (hours/days)
   - Root cause analysis
   - Code review
   - Test fixes

4. **Unpause** (after fix validated)
   ```bash
   stellar contract invoke \
     --id ROUTER_ID \
     --source POOL_ADMIN_KEY \
     -- unpause
   ```

---

## Pause/Unpause

### Emergency Pause

**Function**: `pause(env, caller)` (Emergency Admin or Pool Admin)

**Who**: Emergency admin or pool admin (via `validate_emergency_admin`)

**Effect**: Halts all protocol operations except readonly queries

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source EMERGENCY_ADMIN_KEY \
  -- pause
```

**Verification**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  -- is_paused
# Returns: true
```

### Controlled Unpause

**Function**: `unpause(env, caller)` (Pool Admin only)

**Who**: Pool admin only (emergency admin cannot unpause)

**Effect**: Resume all protocol operations

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- unpause
```

**Verification**:
```bash
stellar contract invoke \
  --id ROUTER_ID \
  -- is_paused
# Returns: false
```

### Pause/Unpause Reserve Deployment

Reserve initialization can be paused independently for safer upgrades.

**Functions**: `pause_reserve_deployment(env, caller)` and `unpause_reserve_deployment(env, caller)` (via pool-configurator)

**Caller**: Emergency admin or pool admin (both validated via `validate_emergency_admin`)

```bash
# Prevent new reserves during upgrade
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source EMERGENCY_ADMIN_KEY \
  -- pause_reserve_deployment

# Resume reserve deployment
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- unpause_reserve_deployment
```

This prevents `init_reserve()` from succeeding without affecting existing reserves.

> **Note**: Unlike protocol `unpause()` which requires pool admin only, `unpause_reserve_deployment()` allows either emergency admin or pool admin.

---

## Circuit Breaker Reset

K2's oracle includes a circuit breaker to detect manipulation.

### What It Detects

Prices changing beyond historical volatility bands.

### When to Reset

1. **False Positive Triggering**: Circuit breaker triggered but price is legitimate
   - Major asset delisting (correct price drop)
   - Black swan market event (price moved 20%+)

2. **After Fix**: Once root cause fixed, reset breaker

### Reset Procedure

```bash
stellar contract invoke \
  --id PRICE_ORACLE_ID \
  --source POOL_ADMIN_KEY \
  -- reset_circuit_breaker \
  --asset '{"Stellar": "ASSET_ADDRESS"}'
```

**Effect**: Clears previous price observation, allows next price update

**Warning**: Only reset when confident price is legitimate

---

## Protocol Upgrades

### Upgrade Process

K2 uses standard Soroban contract upgrades.

#### Preparing Upgrade

1. **Compile New WASM**
   ```bash
   cd contracts/kinetic-router
   cargo build --target wasm32-unknown-unknown --release
   ```

2. **Hash New Code**
   ```bash
   HASH=$(shasum -a 256 target/wasm32-unknown-unknown/release/k2_kinetic_router.wasm | awk '{print $1}')
   echo $HASH
   ```

3. **Test on Testnet**
   - Deploy new version
   - Run full test suite
   - Verify backward compatibility

#### Deploying Upgrade

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source UPGRADE_ADMIN_KEY \
  -- upgrade \
  --new_wasm_hash HASH_HEX
```

**Requirements**:
- **Dual authorization**: Both the upgrade admin AND pool admin must sign the transaction
- Valid WASM hash
- Hash must be previously uploaded to ledger
- Automatically calls `sync_access_control_flags()` after upgrade

**Effect**: Contract code replaced, storage preserved. Access control flags are re-synced to prevent whitelist/blacklist bypass after upgrade.

#### Post-Upgrade Verification

```bash
# Verify upgrade succeeded
stellar contract invoke \
  --id ROUTER_ID \
  -- version

# Should return new version number
```

---

## Access Control Updates

### User Whitelists

Restrict deposits to specific addresses per reserve.

**Function**: `set_reserve_whitelist()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_whitelist \
  --asset USDC_ADDRESS \
  --whitelist '[
    "GAAAA...",  # Vault 1
    "GBBBB...",  # Vault 2
    "GCCCC...'   # Vault 3
  ]'
```

**Behavior**:
- Empty list: Open access
- Non-empty list: Only listed addresses can supply/borrow

**Use Case**: Institutional deployment, controlled beta launch

### User Blacklist

Block specific addresses from reserve interaction.

**Function**: `set_reserve_blacklist()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_blacklist \
  --asset USDC_ADDRESS \
  --blacklist '["GBLOCKED1...", "GBLOCKED2..."]'
```

**Use Case**: Sanction compliance, blocked/hacked accounts

### Liquidator Whitelist

Restrict liquidations to approved liquidators.

**Function**: `set_liquidation_whitelist()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_liquidation_whitelist \
  --whitelist '[
    "GLIQUIDATOR1...",
    "GLIQUIDATOR2...",
    "GLIQUIDATOR3...'
  ]'
```

**Use Case**: Controlled liquidation network, MEV prevention

### Liquidator Blacklist

Block specific addresses from liquidation.

**Function**: `set_liquidation_blacklist()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_liquidation_blacklist \
  --blacklist '["GMALICIOUS1...", "GMALICIOUS2..."]'
```

### Swap Handler Whitelist

Approve custom swap handler contracts for collateral swaps.

**Function**: `set_swap_handler_whitelist()`

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_swap_handler_whitelist \
  --whitelist '[
    "CSWAP1...",   # Soroswap
    "CSWAP2...'    # Aquarius
  ]'
```

**Empty List = Deny All Custom Handlers** (only default DEX allowed)

---

## Monitoring & Alerts

### Critical Metrics

Monitor these metrics to detect operational issues:

| Metric | Alert Threshold | Check Frequency |
|--------|-----------------|-----------------|
| Supply Cap Utilization | > 90% | Hourly |
| Borrow Cap Utilization | > 90% | Hourly |
| Protocol Paused | Any true | Realtime |
| Health Factor (weighted avg) | < 1.05 | Every 10 min |
| Interest Rate (borrow APY) | > 100% | Daily |
| Reserve Factor Accrual | > $1M pending | Daily |
| Oracle Price Staleness | > max_age | Every price update |
| Circuit Breaker Triggered | Any trigger | Realtime |

### Setting Up Monitoring

#### Query Reserve Health

```bash
# Script to monitor all reserves
for ASSET in USDC EURC XLM ETH; do
  stellar contract invoke --id ROUTER_ID -- get_reserve_data --asset ${ASSET}_ADDRESS | jq '..'
done
```

#### Track Supply Cap Utilization

```bash
# USDC supply cap = 50M
# Current supply from reserve data
RESERVE=$(stellar contract invoke --id ROUTER_ID -- get_reserve_data --asset USDC_ADDRESS)
UTIL_PCT=$((CURRENT_SUPPLY * 100 / 50000000))
[ $UTIL_PCT -gt 90 ] && alert "USDC supply cap $UTIL_PCT% full"
```

#### Monitor Flash Loan Activity

```bash
# Track fees collected
stellar contract invoke --id ROUTER_ID -- get_treasury
# Should show accumulated fee balance
```

### Alert Conditions

1. **High Utilization** (> 90% of cap)
   - May indicate growing demand
   - Consider increasing cap

2. **Extreme Interest Rates** (> 100% APY)
   - Market under severe stress
   - May need manual price intervention

3. **Protocol Paused**
   - Investigate emergency admin action
   - Get incident report

4. **Circuit Breaker Triggered**
   - Potential manipulation
   - Or legitimate black swan event

---

## Troubleshooting

### Common Admin Issues

#### Problem: "Unauthorized" Error

**Symptom**: Admin operation fails with `Unauthorized` error

**Causes**:
1. Caller is not the current admin
2. Caller's key not authorized in transaction
3. Admin address not initialized

**Resolution**:
```bash
# Verify current admin
stellar contract invoke --id ROUTER_ID -- get_admin

# Ensure using correct admin's signing key
# Ensure admin key is authorized in transaction
```

#### Problem: "AlreadyInitialized" Error

**Symptom**: Cannot initialize protocol, contract already has admin

**Causes**:
1. Protocol already initialized
2. Contract deployed with initialization call

**Resolution**:
```bash
# Verify if initialized
stellar contract invoke --id ROUTER_ID -- is_initialized

# If yes, cannot re-initialize
# Use existing admin for future operations
```

#### Problem: "NoPendingAdmin" Error

**Symptom**: accept_pool_admin() fails with no pending admin

**Causes**:
1. No proposal made yet
2. Proposal was cancelled
3. Different admin role (check if using accept_admin for upgrade admin vs accept_pool_admin)

**Resolution**:
```bash
# Check pending admin
stellar contract invoke --id ROUTER_ID -- get_pending_pool_admin

# If error, must propose first
stellar contract invoke \
  --id ROUTER_ID \
  --source CURRENT_ADMIN_KEY \
  -- propose_pool_admin \
  --pending_admin NEW_ADMIN_ADDRESS
```

#### Problem: "InvalidPendingAdmin" Error

**Symptom**: Cannot accept admin, credentials mismatch

**Causes**:
1. Caller address != pending admin address
2. Using wrong signing key
3. Pending admin was cancelled

**Resolution**:
1. Verify pending admin address matches caller
   ```bash
   stellar contract invoke --id ROUTER_ID -- get_pending_pool_admin
   ```
2. Ensure using correct key to sign transaction
3. If cancelled, restart proposal

#### Problem: "ReserveNotFound" Error

**Symptom**: Cannot update reserve, asset not initialized

**Causes**:
1. Asset never added with init_reserve()
2. Asset address mismatch
3. Typo in asset address

**Resolution**:
```bash
# Check if reserve exists
stellar contract invoke --id ROUTER_ID -- get_reserve_data --asset USDC_ADDRESS

# If not found, must init_reserve first
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- init_reserve \
  --underlying_asset USDC_ADDRESS \
  ...
```

#### Problem: Reserve Parameter Rejection

**Symptom**: configure_reserve_as_collateral fails with InvalidAmount

**Causes**:
1. ltv > 10000 bps
2. liquidation_threshold > 10000 bps
3. liquidation_threshold <= ltv (must be > ltv + 50 bps)
4. liquidation_bonus > 10000 bps

**Resolution**:
```bash
# Example: Correct parameter set
stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- configure_reserve_as_collateral \
  --asset USDC_ADDRESS \
  --ltv 8000 \
  --liquidation_threshold 8500 \  # Must be > 8050
  --liquidation_bonus 500
```

#### Problem: Cap Enforcement Failing

**Symptom**: set_supply_cap or set_borrow_cap rejected

**Causes**:
1. Cap value > u64::MAX (2^64 - 1)
2. Asset not initialized
3. Caller not admin

**Resolution**:
```bash
# Check cap values fit in u64
# u64::MAX = 18,446,744,073,709,551,615

# Valid cap for USDC (6 decimals):
# 1B tokens = 1_000_000_000_000_000 (well under u64::MAX)

stellar contract invoke \
  --id POOL_CONFIG_ID \
  --source POOL_ADMIN_KEY \
  -- set_supply_cap \
  --asset USDC_ADDRESS \
  --supply_cap 1000000000000000  # 1B tokens OK
```

#### Problem: Cannot Pause/Unpause

**Symptom**: pause() or unpause() fails with Unauthorized

**Causes**:
1. Pause: Caller not emergency admin or pool admin
2. Unpause: Caller not pool admin (emergency admin cannot unpause)
3. Caller's key not authorized

**Resolution**:
```bash
# For pause: use emergency admin key
stellar contract invoke \
  --id ROUTER_ID \
  --source EMERGENCY_ADMIN_KEY \
  -- pause

# For unpause: use pool admin key
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- unpause
```

#### Problem: Oracle Asset Cannot Be Added

**Symptom**: add_oracle_asset fails

**Causes**:
1. Asset already whitelisted
2. Oracle not initialized
3. Caller not admin

**Resolution**:
```bash
# Check if already added
stellar contract invoke --id PRICE_ORACLE_ID -- get_asset_config --asset ASSET_ADDRESS

# If exists, no need to add again
# Or remove and re-add if needed
```

---

## Additional Admin Functions

The following admin functions are available on the router but are not covered in the sections above.

### Liquidation Price Tolerance

**Function**: `set_liquidation_price_tolerance(env: Env, tolerance_bps: u128)`

**Caller**: Pool admin

**Purpose**: Maximum allowed price deviation between `prepare_liquidation` and `execute_liquidation` in the 2-step flow. If prices move more than this tolerance, execution reverts.

**Default**: 300 bps (3%). Capped at 5000 bps (50%).

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_liquidation_price_tolerance \
  --tolerance_bps 300
```

### Price Staleness Threshold

**Function**: `set_price_staleness_threshold(env: Env, threshold_seconds: u64)`

**Caller**: Pool admin

**Purpose**: Global oracle price staleness threshold. Prices older than this are rejected.

**Default**: 3600 seconds (1 hour)

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_price_staleness_threshold \
  --threshold_seconds 3600
```

### Per-Asset Staleness Threshold

**Function**: `set_asset_staleness_threshold(env: Env, asset: Address, threshold_seconds: u64)`

**Caller**: Pool admin

**Purpose**: Override the global staleness threshold for a specific asset (M-07). Different assets can have different oracle heartbeats (e.g., BTC every 60s, stablecoins every 24h). Pass 0 to remove the override and fall back to the global threshold.

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_asset_staleness_threshold \
  --asset BTC_ADDRESS \
  --threshold_seconds 120
```

### Flash Liquidation Premium

**Function**: `set_flash_liquidation_premium(env: Env, premium_bps: u128)`

**Caller**: Pool admin

**Purpose**: Extra premium charged on top of regular flash loan fee during flash liquidations. Set to 0 to disable (default).

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_flash_liquidation_premium \
  --premium_bps 50
```

### Cover Deficit

**Function**: `cover_deficit(env: Env, caller: Address, asset: Address, amount: u128) -> Result<u128, KineticRouterError>`

**Caller**: **Permissionless** — anyone can call this to inject tokens and replenish pool deficit

**Purpose**: Replenish bad debt deficit for a reserve (from bad debt socialization via H-05). Returns the actual amount covered, capped at the current deficit.

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source ANY_KEY \
  -- cover_deficit \
  --asset USDC_ADDRESS \
  --amount 1000000000
```

### Reserve Minimum Remaining Debt

**Function**: `set_reserve_min_remaining_debt(env: Env, asset: Address, min_remaining_debt: u32)`

**Caller**: Pool admin

**Purpose**: Set the minimum debt that must remain after a partial repay (H-02 fix). Prevents dust debt positions that are uneconomical to liquidate. Value is in whole tokens (not WAD); stored in bits 71-102 of the reserve configuration bitmap.

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- set_reserve_min_remaining_debt \
  --asset USDC_ADDRESS \
  --min_remaining_debt 10
```

### Flush Oracle Config Cache

**Function**: `flush_oracle_config_cache(env: Env)`

**Caller**: Pool admin

**Purpose**: Clear the cached oracle configuration (F-02 optimization). Must be called when oracle precision or parameters change outside of `set_price_oracle`.

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- flush_oracle_config_cache
```

### Sync Access Control Flags

**Function**: `sync_access_control_flags(env: Env)`

**Caller**: Pool admin

**Purpose**: Re-synchronize per-reserve and global access control flag maps (AC-01). Must be called after contract upgrade to prevent whitelist/blacklist bypass. Automatically called during `upgrade()`, but can also be called manually.

```bash
stellar contract invoke \
  --id ROUTER_ID \
  --source POOL_ADMIN_KEY \
  -- sync_access_control_flags
```

---

## Governance Future

K2 currently uses centralized admin roles for protocol management. This section documents the path toward community governance.

### Phase 1: Current State

- **Pool Admin**: Single trusted address
- **Emergency Admin**: Single trusted address
- **Decisions**: Made by admin, executed directly

### Phase 2: Timelock Governance (Future)

Introduces delay before sensitive operations take effect.

**Proposal**:
1. Admin calls `propose_parameter_change()`
2. Parameter stored with proposed value
3. Community observes for dispute period (e.g., 48 hours)
4. Admin calls `execute_parameter_change()` after delay

**Benefits**:
- Community has time to react
- Mistakes can be cancelled before taking effect
- Transparent governance trail

### Phase 3: DAO Governance (Future)

Transitions admin role to governance contract.

**Model**:
1. Token holders vote on proposals
2. Governance contract executes approved proposals
3. Pool admin = governance contract address
4. No single person can change parameters

**Requirements**:
- Governance token
- Voting contract
- Treasury management
- Proposal workflow

### Migration Path

When transitioning to governance:

1. **Prepare Governance Contracts** (testnet validation)
2. **Deploy to Mainnet** (governance contracts only, don't initialize)
3. **Propose Admin Transfer** to governance contract
4. **Governance Contract Accepts** (via authorized call)
5. **Monitor** governance contract parameters match protocol

```bash
# Example: Transition to governance
stellar contract invoke \
  --id ROUTER_ID \
  --source CURRENT_ADMIN_KEY \
  -- propose_pool_admin \
  --pending_admin GOVERNANCE_CONTRACT_ADDRESS

# Governance contract (via voting) calls:
stellar contract invoke \
  --id ROUTER_ID \
  --source GOVERNANCE_KEY \
  -- accept_pool_admin
```

### Governance Parameter Examples

Once DAO active, proposals might include:

- Increase USDC supply cap from 50M to 100M
- Reduce liquidation bonus for BTC from 10% to 8%
- Add new asset (stETH) to protocol
- Update flash loan premium from 9 bps to 12 bps
- Pause/unpause specific reserves

---

## Summary

K2's admin model provides:

1. **Clear Separation**: Pool admin vs emergency admin with bounded responsibilities
2. **Safety**: Two-step transfers prevent admin misaddressing
3. **Auditability**: All operations emit events
4. **Flexibility**: Comprehensive parameter management
5. **Emergency Capability**: Quick pause/unpause during incidents
6. **Governance Compatible**: Architecture supports governance patterns

### Quick Reference: Admin Operations

| Operation | Function | Caller | Effect |
|-----------|----------|--------|--------|
| Initialize Reserve | init_reserve | Pool Admin (via pool-configurator) | Add new asset |
| Update Parameters | configure_reserve_as_collateral | Pool Admin | Modify LTV/thresholds |
| Set Supply Cap | set_supply_cap | Pool Admin | Limit deposits |
| Set Borrow Cap | set_borrow_cap | Pool Admin | Limit borrowing |
| Configure Premium | set_flash_loan_premium | Pool Admin | Adjust flash loan fee |
| Pause Protocol | pause | Emergency Admin or Pool Admin | Block operations |
| Unpause Protocol | unpause | Pool Admin only | Resume operations |
| Pause Reserve Deploy | pause_reserve_deployment | Emergency Admin or Pool Admin | Block new reserves |
| Unpause Reserve Deploy | unpause_reserve_deployment | Emergency Admin or Pool Admin | Allow new reserves |
| Upgrade Contract | upgrade | Upgrade Admin + Pool Admin | Dual-sig upgrade |
| Propose Admin | propose_pool_admin | Current Pool Admin | Initiate transfer |
| Accept Admin | accept_pool_admin | Proposed Admin | Complete transfer |
| Whitelist Asset | set_oracle_asset_enabled | Pool Admin | Enable/disable prices |
| Whitelist User | set_reserve_whitelist | Pool Admin | Restrict access |
| Whitelist Liquidator | set_liquidation_whitelist | Pool Admin | Restrict liquidators |
| Price Tolerance | set_liquidation_price_tolerance | Pool Admin | 2-step liq price drift |
| Staleness Threshold | set_price_staleness_threshold | Pool Admin | Global oracle staleness |
| Asset Staleness | set_asset_staleness_threshold | Pool Admin | Per-asset staleness |
| Flash Liq Premium | set_flash_liquidation_premium | Pool Admin | Flash liq extra fee |
| Cover Deficit | cover_deficit | Permissionless | Replenish bad debt |
| Min Remaining Debt | set_reserve_min_remaining_debt | Pool Admin | Prevent dust debt |
| Flush Oracle Cache | flush_oracle_config_cache | Pool Admin | Clear oracle cache |
| Sync ACL Flags | sync_access_control_flags | Pool Admin | Re-sync access flags |

---

## Related Documentation

- **Security Model**: [09-SECURITY.md](09-SECURITY.md) - Authorization patterns, invariants
- **Deployment Guide**: [12-DEPLOYMENT.md](12-DEPLOYMENT.md) - Step-by-step setup and initialization
- **Protocol Overview**: [01-OVERVIEW.md](01-OVERVIEW.md) - High-level protocol structure
- **System Components**: [04-COMPONENTS.md](04-COMPONENTS.md) - Contract details

---

**Last Updated**: February 2026
**Version**: 1.0
