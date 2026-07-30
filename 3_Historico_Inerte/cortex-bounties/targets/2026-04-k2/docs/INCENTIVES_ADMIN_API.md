# K2 Incentives — Admin API Reference

---

## Key Concepts

- **Rewards are configured per token contract**, not per underlying asset. Supply rewards target the **aToken** address; borrow rewards target the **debtToken** address.
- **`reward_type`**: `0` = supply, `1` = borrow.
- **`emission_per_second`**: Rate in the reward token's smallest unit. For example, USDC with 7 decimals at 10 USDC/day = `10 × 10⁷ / 86400 ≈ 1157`.
- **`distribution_end`**: Unix timestamp. Set to `0` for no end date.
- The contract must be **funded** with reward tokens before users can claim.
- All admin functions require authorization from the **emission manager** address (set at initialization).

---

## Setup & Configuration

### `configure_asset_rewards`

Register a new reward token for an asset, or update an existing one. This is the primary setup call.

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `asset` | Address | aToken (for supply rewards) or debtToken (for borrow rewards) |
| `reward_token` | Address | The token distributed as reward (e.g., USDC, protocol token) |
| `reward_type` | u32 | `0` = supply, `1` = borrow |
| `emission_per_second` | u128 | Emission rate in smallest units per second |
| `distribution_end` | u64 | Unix timestamp when emissions stop (`0` = no end) |

```bash
stellar contract invoke --id $INCENTIVES -- configure_asset_rewards \
  --caller $EMISSION_MANAGER \
  --asset $A_TOKEN_ADDRESS \
  --reward_token $REWARD_TOKEN \
  --reward_type 0 \
  --emission_per_second 1157 \
  --distribution_end 1744444800
```

### `fund_rewards`

Transfer reward tokens from the emission manager into the contract. **Must be called before users can claim.**

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `reward_token` | Address | The reward token to deposit |
| `amount` | u128 | Amount in smallest units |

```bash
stellar contract invoke --id $INCENTIVES -- fund_rewards \
  --caller $EMISSION_MANAGER \
  --reward_token $REWARD_TOKEN \
  --amount 100000000000
```

---

## Ongoing Management

### `set_emission_per_second`

Change the emission rate for an existing reward configuration. Automatically snapshots the current reward index before updating.

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `asset` | Address | aToken or debtToken |
| `reward_token` | Address | The reward token |
| `reward_type` | u32 | `0` = supply, `1` = borrow |
| `new_emission_per_second` | u128 | New rate in smallest units per second |

```bash
stellar contract invoke --id $INCENTIVES -- set_emission_per_second \
  --caller $EMISSION_MANAGER \
  --asset $A_TOKEN_ADDRESS \
  --reward_token $REWARD_TOKEN \
  --reward_type 0 \
  --new_emission_per_second 2314
```

### `set_distribution_end`

Extend or shorten the reward distribution period.

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `asset` | Address | aToken or debtToken |
| `reward_token` | Address | The reward token |
| `reward_type` | u32 | `0` = supply, `1` = borrow |
| `new_distribution_end` | u64 | New end timestamp (`0` = no end) |

```bash
stellar contract invoke --id $INCENTIVES -- set_distribution_end \
  --caller $EMISSION_MANAGER \
  --asset $A_TOKEN_ADDRESS \
  --reward_token $REWARD_TOKEN \
  --reward_type 0 \
  --new_distribution_end 1747036800
```

---

## Deactivation & Cleanup

### `remove_asset_reward`

Soft-delete: sets `is_active = false`. Emissions stop, but users can still claim already-accrued rewards.

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `asset` | Address | aToken or debtToken |
| `reward_token` | Address | The reward token |
| `reward_type` | u32 | `0` = supply, `1` = borrow |

### `delete_reward_token`

Hard-delete: permanently removes the reward token from an asset's registered list. **Both supply and borrow configs must be inactive first.**

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |
| `asset` | Address | aToken or debtToken |
| `reward_token` | Address | The reward token to unregister |

---

## Emergency Controls

### `pause` / `unpause`

When paused, users **cannot claim** rewards. Reward accrual via `handle_action` continues normally — only claims are blocked.

| Parameter | Type | Description |
|-----------|------|-------------|
| `caller` | Address | Must be emission manager |

---

## View Functions

These are read-only and do not require authorization. Use them to build the admin dashboard.

| Function | Returns | Description |
|----------|---------|-------------|
| `get_assets()` | `Vec<Address>` | All assets (aTokens/debtTokens) with configured rewards |
| `get_reward_tokens(asset)` | `Vec<Address>` | Reward tokens registered for a given asset |
| `get_asset_reward_config(asset, reward_token, reward_type)` | `AssetRewardConfig` | Config: `emission_per_second`, `distribution_end`, `is_active` |
| `get_asset_reward_index(asset, reward_token, reward_type)` | `AssetRewardIndex` | Current global index and last update timestamp |
| `get_user_accrued_rewards(asset, reward_token, user, reward_type)` | `u128` | Pending claimable rewards for a user |
| `get_user_reward_data(asset, reward_token, user, reward_type)` | `UserRewardData` | Full user state: `accrued`, `index_snapshot`, `balance_snapshot` |
| `get_reward_token_balance(reward_token)` | `u128` | Contract's remaining balance for a reward token |
| `is_paused()` | `bool` | Whether claims are currently blocked |

---

## Admin UI Recommendations

### Setup Flow

1. **Configure** rewards for each asset via `configure_asset_rewards` (once per aToken for supply, once per debtToken for borrow).
2. **Fund** the contract via `fund_rewards` with enough tokens to cover the planned emission period.
3. **Verify** with `get_assets()` and `get_asset_reward_config()`.

### Dashboard Indicators

- **Funding health**: Compare `get_reward_token_balance(reward_token)` against projected liability (`emission_per_second × remaining_seconds × number_of_assets`). Alert when balance is insufficient.
- **Active configs**: List all `(asset, reward_token, reward_type)` tuples where `is_active = true`.
- **Time remaining**: `distribution_end - now` for each config.

### Emission Rate Calculator

The UI should provide a helper to convert human-readable rates to `emission_per_second`:

```
emission_per_second = (tokens_per_day × 10^decimals) / 86400
```

| Reward Token | Decimals | 10/day | 100/day | 1000/day |
|-------------|----------|--------|---------|----------|
| USDC (testnet) | 7 | 1,157 | 11,574 | 115,740 |
| XLM | 7 | 1,157 | 11,574 | 115,740 |
| Token (18 dec) | 18 | 115,740,740,740,740 | 1,157,407,407,407,407 | 11,574,074,074,074,074 |

---

## Typical Lifecycle

1. **`configure_asset_rewards`** — Register reward token for an asset
2. **`fund_rewards`** — Deposit reward tokens into the contract
3. Users earn and claim rewards
4. **Adjust as needed:**
   - `set_emission_per_second` — Change the rate
   - `set_distribution_end` — Extend or shorten the period
   - `fund_rewards` — Top up the balance
5. **Emergency:** `pause` / `unpause` — Block or restore claims
6. **Wind down:**
   - `remove_asset_reward` — Deactivate (soft-delete)
   - `delete_reward_token` — Permanently unregister (requires both supply & borrow inactive)

---