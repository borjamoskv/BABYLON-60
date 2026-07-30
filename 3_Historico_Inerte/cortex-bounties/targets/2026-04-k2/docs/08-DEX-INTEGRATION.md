# 8. DEX Integration Architecture

## Overview

K2 integrates with decentralized exchanges (DEX) via adapter contracts to enable:

- Collateral swaps (exchange one asset for another)
- Flash liquidation (swap seized collateral to debt asset)
- Two-step liquidation coordination
- Slippage protection and deadline enforcement

Multiple DEX adapters can be configured simultaneously, with the router selecting the appropriate adapter for each swap.

---

## Integration Model

The adapter pattern decouples K2 from specific DEX implementations:

```
K2 Kinetic Router
    |
    +--- Soroswap Adapter ---> Soroswap DEX
    |
    +--- Aquarius Adapter ---> Aquarius DEX
    |
    +--- [Custom Adapter] ---> [Other DEX]
```

Each adapter implements a standard interface:

```rust
pub trait SwapHandler {
    fn execute_swap(
        from_token: Address,
        to_token: Address,
        amount_in: u128,
        min_amount_out: u128,
        recipient: Address,
    ) -> Result<u128, Error>;

    fn get_quote(
        from_asset: Address,
        to_asset: Address,
        amount_in: u128,
    ) -> Result<u128, Error>;
}
```

> **Note**: The adapter computes its own deadline internally (e.g., Soroswap adapter uses `env.ledger().timestamp() + timeout`). Callers do not pass a deadline.

---

## Adapter Architecture

### **Soroswap Adapter**

Integrates with Soroswap (Uniswap V2-style AMM).

**Purpose**: Enable swaps on Soroswap's liquidity pools.

**Configuration**:
- Router contract address (main swap router)
- Factory contract address (optional, `Option<Address>` — for direct pair lookups)

**Swap Flow**:
1. Router calls `execute_swap()` with asset pair and amount
2. Adapter queries factory for pair contract
3. Adapter authorizes itself: `authorize_as_current_contract()`
4. Adapter calls pair contract: `swap()`
5. Pair transfers `amount_out` back to adapter
6. Adapter transfers received tokens to router

**Authorization**:
- Only Kinetic Router can invoke
- Adapter authorizes token transfers to itself

**Quote Mechanism**:
- Router pair contract provides `get_amounts_out()`
- Calculates exact output for given input
- Used for slippage protection

### **Aquarius Adapter**

Integrates with Aquarius DEX.

**Purpose**: Alternative liquidity source with potentially better rates.

**Configuration**:
- Router contract address (Aquarius router only — no factory parameter)
- Pool mappings registered manually via `register_pool(caller, token_a, token_b, pool_address)`

**Swap Flow**: Similar to Soroswap with Aquarius-specific interface. Pool lookup uses the manually registered mappings rather than a factory contract.

---

## Swap Execution

### **Direct Pair Swap**

```
Asset A --[Pair: A/B]--> Asset B
```

Example: USDC to USDT
- Soroswap has USDC/USDT pair
- Direct swap with single liquidity pool
- K2 currently supports direct pair swaps only

**Note**: Multi-hop routing through intermediate assets is not supported in the current implementation. All swaps must be between asset pairs with direct liquidity pools.

### **Slippage Protection**

Every swap enforces minimum output:

```
minimum_amount_out = quoted_amount * (1 - slippage_tolerance)

Example: 1000 USDC to USDT
- Quote: 1005 USDT
- Slippage tolerance: 0.5% (50 bps)
- Minimum: 1005 * 0.995 = 1000 USDT
- If pair returns < 1000 USDT, transaction reverts
```

### **Deadline Enforcement**

Swaps must complete before deadline:

```
deadline = current_timestamp + timeout (e.g., 5 minutes)

If block time > deadline, transaction reverts.
Prevents stale transactions from executing at bad rates.
```

---

## Collateral Swap Flow

User exchanges one collateral asset for another without withdrawing.

```
1. Router: burn_scaled(user, from_aToken, amount)
   - Remove collateral from user
   - Transfer underlying to router

2. Router: adapter.execute_swap(from, to, amount, min_out)
   - Execute swap on DEX
   - Receive `to_asset` tokens

3. Router: mint_scaled(user, to_aToken, amount_received)
   - Add new collateral to user
   - Update user configuration

4. Router: validate_health_factor()
   - Verify HF >= 1.0 after swap
   - If borrowed, must stay safe
```

**Invariant**: User's health factor improves or remains safe after swap.

---

## Flash Liquidation Flow

Two-step liquidation uses DEX to swap seized collateral.

### **Phase 1: Prepare Liquidation**
- Validate health factor
- Calculate liquidation amounts
- Store authorization

### **Phase 2: Execute Liquidation**
```
1. Flash loan: Borrow debt_to_cover

2. Seize collateral: Burn user's collateral aToken

3. Swap collateral -> debt: adapter.execute_swap(...)
   - Input: collateral_to_seize (underlying)
   - Output: at least debt_to_cover (to repay flash loan + premium)

4. Repay flash loan: debt_to_cover + premium

5. Transfer profit: received - debt_to_cover - premium to liquidator
```

**Slippage Protection**: min_amount_out prevents liquidator loss from bad execution.

---

## Price Impact and Liquidity

### **Thin Markets**
Assets with low liquidity pools:
- Larger swaps cause significant slippage
- Price impact: percentage loss from quoted price
- May make liquidation unprofitable if spread too high

### **Concentrated Liquidity**
AMM liquidity pools have price curves:
- Small swaps: minimal slippage
- Large swaps: exponential slippage increase

### **Mitigation**
- Multi-hop routing through liquid pairs
- Time-weighted average prices (TWAP)
- Off-chain price aggregation (multiple DEX quotes)

---

## Swap Handler Selection

When a swap is needed, the router resolves the handler using a simple priority:

1. **Specified swap handler**: If the caller passes an explicit `swap_handler` address, use it (must be whitelisted)
2. **DEX factory pair**: If a `dex_factory` is configured, look up the direct pair contract for the asset pair
3. **DEX router fallback**: Fall back to the configured `dex_router` address

There is no multi-adapter quote comparison. The first handler found in priority order is used.

---

## Custom Adapter Integration

To add a new DEX:

1. **Implement Swap Handler Interface**
```rust
pub fn execute_swap(
    env: Env,
    from_token: Address,
    to_token: Address,
    amount_in: u128,
    min_amount_out: u128,
    recipient: Address,
) -> Result<u128, Error> {
    // Query DEX for output amount
    let amount_out = query_dex_quote(from_asset, to_asset, amount_in)?;

    // Validate minimum output
    if amount_out < min_amount_out {
        return Err(SlippageExceeded);
    }

    // Execute swap
    execute_swap_on_dex(from_asset, to_asset, amount_in)?;

    // Transfer output to caller
    // Return amount received
    Ok(amount_out)
}
```

2. **Register with Router**
- Deploy adapter contract
- Store adapter address in router configuration
- Update routing rules

3. **Testing**
- Unit tests for swap execution
- Integration tests with K2 router
- Slippage and deadline validation

---

## Error Handling

### **Swap Failures**

| Error | Cause | Recovery |
|-------|-------|----------|
| AssetPairNotFound | DEX has no liquidity for pair | Use alternative adapter or multi-hop |
| InsufficientLiquidity | Pool too small for amount | Reduce swap size or split across txs |
| SlippageExceeded | Market moved unfavorably | Increase slippage tolerance or retry |
| DeadlineExceeded | Swap took too long | Check network congestion |

### **Authorization Failures**

| Error | Cause | Recovery |
|-------|-------|----------|
| Unauthorized | Only router can invoke | Ensure calling from K2 router |
| InsufficientAllowance | Token approval missing | Approve tokens before swap |

---

## Security Considerations

### **Price Manipulation**
Adapters cannot guarantee best execution. Liquidators may:
- Validate quotes off-chain
- Use multiple price sources (oracle + DEX)
- Compare multiple DEX quotes

### **Flash Loan Risk**
Adapters receive borrowed assets temporarily:
- Must transfer swap output to caller
- Cannot keep funds
- Checked via balance assertions

### **Reentrancy**
Soroban's sequential execution prevents reentrancy:
- DEX callback receives control flow
- Cannot re-enter K2 mid-swap
- Safe cross-contract calls

---

## Performance Characteristics

### **Swap Cost** (CPU Instructions)

| Operation | Cost |
|-----------|------|
| Query quote | 10-20M |
| Execute swap (Soroswap) | 20-30M |
| Execute swap (Aquarius) | 20-30M |
| Total swap latency | 30-50M |

Multi-hop swaps cost more (1-2x per additional hop).

### **Optimization**

- Cache quotes when possible
- Batch multiple swaps if allowed
- Use simpler direct pairs over multi-hop
- Monitor DEX liquidity changes

---

## Deployment

### **Soroswap Configuration**
```bash
stellar contract invoke \
  --id <SOROSWAP_ADAPTER> \
  -- initialize \
  --admin <ADMIN> \
  --router <SOROSWAP_ROUTER> \
  --factory <SOROSWAP_FACTORY>   # optional (Option<Address>)
```

### **Aquarius Configuration**
```bash
stellar contract invoke \
  --id <AQUARIUS_ADAPTER> \
  -- initialize \
  --admin <ADMIN> \
  --aquarius_router <AQUARIUS_ROUTER>

# Register pool mappings manually (no factory):
stellar contract invoke \
  --id <AQUARIUS_ADAPTER> \
  -- register_pool \
  --caller <ADMIN> \
  --token_a <TOKEN_A> \
  --token_b <TOKEN_B> \
  --pool_address <POOL_ADDRESS>
```

### **Router Setup**
```bash
stellar contract invoke \
  --id <KINETIC_ROUTER> \
  -- set_dex_router \
  --router <SOROSWAP_ADAPTER>
```

---

## Testing

### **Unit Tests**

```rust
#[test]
fn test_swap_execution() {
    let env = Env::default();
    env.mock_all_auths();

    let adapter = deploy_adapter(&env);
    let amount_out = adapter.execute_swap(
        &usdc,
        &usdt,
        &1_000_000_000, // 1000 USDC (9 decimals)
        &990_000_000,   // min 990 USDT (slippage 1%)
        &recipient,     // where output tokens are sent
    );

    assert!(amount_out >= 990_000_000);
}
```

### **Integration Tests**

Test full liquidation flow with swap:

```rust
#[test]
fn test_liquidation_with_swap() {
    let protocol = deploy_test_protocol(&env);

    // Setup positions
    protocol.supply_and_borrow();

    // Trigger liquidation
    protocol.execute_flash_liquidation();

    // Verify liquidator received profit
    let liquidator_balance = protocol.get_balance(&liquidator);
    assert!(liquidator_balance > 0);
}
```

---

## Monitoring

Key metrics for DEX adapters:

- **Swap success rate**: Percentage of successful executions
- **Slippage realized**: Average difference from quoted price
- **Liquidity trends**: Changes in pool depth
- **Failure reasons**: Revert codes and frequencies

---

## Future Enhancements

- TWAP-based prices instead of spot quotes
- Multi-hop routing optimization
- Order-book DEX integration
- Aggregator pattern (best of multiple DEX)
- MEV protection mechanisms

---

**Last Updated**: March 2026
