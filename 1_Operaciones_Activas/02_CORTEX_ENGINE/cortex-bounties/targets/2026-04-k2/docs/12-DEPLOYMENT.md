# 12. Deployment Guide (K2 + Volta Multisig)

This guide replaces the old deployment flow with a Volta-first sequence and documents what can and cannot be initialized directly to Volta.

For the detailed operator runbook that existed before this rewrite, including build instructions, contract init parameters, reserve configuration, verification steps, and troubleshooting, see [12-DEPLOYMENT-REFERENCE.md](./12-DEPLOYMENT-REFERENCE.md).

## Canonical Sequence

1. Deploy Volta multisig first (manually or via `deploy.sh` auto-deploy).
2. Deploy K2 contracts.
3. Initialize K2 with Incentives `emission_manager` set to the Volta vault.
4. Keep other admin roles initially on the EOA deployer where required for bootstrap.
5. Complete reserve/oracle/bootstrap setup.
6. Transfer remaining ownership/admin roles to Volta.

This is the practical path with current contracts and `deployment/deploy.sh`.

---

## Research Findings: Can We Skip Transfer Step Entirely?

Short answer: **not fully, with the current deploy script and contract auth model**.

### Initialization Auth Matrix

| Contract | `initialize` requires auth of admin param? | Can set Volta directly during plain CLI init? | Notes |
|---|---:|---:|---|
| `k2_kinetic_router` | Yes (`pool_admin.require_auth()`) | No | Volta contract auth is needed; plain EOA tx cannot satisfy this. |
| `k2_price_oracle` | Yes (`admin.require_auth()`) | No | Same reason. |
| `k2_treasury` | Yes (`admin.require_auth()`) | No | Same reason. |
| `k2_pool_configurator` | No | Yes (technical) | But current bootstrap calls `init_reserve` with EOA caller; setting Volta early breaks that flow. |
| `k2_interest_rate_strategy` | No | Yes | Can be Volta from init if desired. |
| `k2_incentives` | No | Yes | Recommended to set Volta as `emission_manager` at init. |
| `k2_a_token` / `k2_debt_token` | No | Yes | Not required for this migration. |

### Conclusion

- **Full “no transfer” deployment is not currently practical** without redesigning deploy orchestration to initialize and operate via Volta contract invocations.
- **Best current approach**: set Incentives manager to Volta during deployment, then transfer the remaining required admin roles after bootstrap.

---

## Prerequisites

- `stellar` CLI
- `rust`, `cargo`, `jq`
- Funded deployer key alias (example: `k2-deployer-v3`)
- Volta owner keys ready in Freighter for co-signing

```bash
stellar --version
rustc --version
cargo --version
jq --version
```

Network setup:

```bash
stellar network add testnet \
  --rpc-url "https://soroban-testnet.stellar.org" \
  --network-passphrase "Test SDF Network ; September 2015"
```

---

## Step 1: Prepare Volta Deployment Inputs

Set shared variables:

```bash
export NETWORK=testnet
export SOURCE_ACCOUNT=k2-deployer-v3
export VOLTA_WASM_HASH=ce84b965f3fdbf4ff9ea4c28813a7a30d6dd65c69d0d1bc19834d907a5e0d27b
```

Set Volta constructor config (example 4 owners, threshold 2):

```bash
export VOLTA_CONFIG='{"owners":["GALM2Z4UR6E3CSN53AE4EWAEPRO33HQEHHOX5ALAYDRU4JTVAZUNIU3F","GDBBLOK4HT5XYAY4HRU4EF5WMP7Q3IRZ7HPQXYS5CACTUBQ4XI565H3W","GA36EIK53TMFP3GNQ3Z4CJ6L3YJZZ6I4PU6RQ5KFCRTKS2PHQAFXCTKN","GDXFHG3ZDLWQVQD4XUSYHZLTBQOV6DY3BGXB47VSSCW2YPVTV2Z44UZX"],"threshold":2}'
```

Optional: if Volta is already deployed, set:

```bash
export VOLTA_VAULT_ADDRESS=<existing_volta_contract_id>
export INCENTIVES_EMISSION_MANAGER="$VOLTA_VAULT_ADDRESS"
```

---

## Step 2: Build K2 Contracts

From the `k2-contracts` repository root:

```bash
cd /path/to/k2-contracts
./deployment/build.sh
```

---

## Step 3: Deploy K2 (Volta Is the Incentives Manager)

### 3.1 Auto-deploy Volta and reuse address (recommended)

If `INCENTIVES_EMISSION_MANAGER` is not set, `deployment/deploy.sh` can deploy Volta first using `VOLTA_WASM_HASH` + `VOLTA_CONFIG`, then reuse the resulting vault address for incentives initialization.

```bash
cd /path/to/k2-contracts

# Dry run
VOLTA_WASM_HASH="$VOLTA_WASM_HASH" \
VOLTA_CONFIG="$VOLTA_CONFIG" \
./deployment/deploy.sh --network testnet --source k2-deployer-v3 --dry-run

# Live
VOLTA_WASM_HASH="$VOLTA_WASM_HASH" \
VOLTA_CONFIG="$VOLTA_CONFIG" \
./deployment/deploy.sh --network testnet --source k2-deployer-v3
```

The script stores the captured vault address in deployment state and sets it as `INCENTIVES_EMISSION_MANAGER` for the run.

### 3.2 Use pre-existing Volta address (alternative)

If you already have a vault address, provide it directly:

```bash
export INCENTIVES_EMISSION_MANAGER=<volta_contract_id>

# Live
./deployment/deploy.sh --network testnet --source k2-deployer-v3
```

Optional manual Volta deploy (if you want to deploy outside `deploy.sh`):

```bash
NEW_VOLTA_VAULT=$(
  stellar contract deploy \
    --wasm-hash "$VOLTA_WASM_HASH" \
    --source "$SOURCE_ACCOUNT" \
    --network "$NETWORK" \
    -- \
    --config "$VOLTA_CONFIG"
)

export INCENTIVES_EMISSION_MANAGER="$NEW_VOLTA_VAULT"
```

Verify:

```bash
stellar contract invoke --id "$INCENTIVES_EMISSION_MANAGER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_config
stellar contract invoke --id "$INCENTIVES_EMISSION_MANAGER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- version
stellar contract extend --id "$INCENTIVES_EMISSION_MANAGER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" --ledgers-to-extend 3110400
```

Result:

- Incentives is initialized with Volta as emission manager.
- Router / Oracle / Treasury bootstrap still uses EOA admin where required.

---

## Step 4: Transfer Remaining Ownership/Admin Roles to Volta

Recommended: use the dedicated post-deploy handoff script after `deploy.sh` completes. The deploy script prints a reminder pointing here.

The script wraps the live `propose_admin` / `propose_pool_admin` calls, reads contract addresses from `deployments/<network>/state.json`, reads the Volta vault from `.external.volta_vault.address` by default, supports `--dry-run`, and verifies the pending admin after each proposal.

Example:

```bash
cd /path/to/k2-contracts

export TRANSFER_PRICE_ORACLE_ADMIN=false
export TRANSFER_EMERGENCY_ADMIN=false

# Dry run
./deployment/transfer-admin-to-volta.sh \
  --network "$NETWORK" \
  --source "$SOURCE_ACCOUNT" \
  --dry-run

# Live
./deployment/transfer-admin-to-volta.sh \
  --network "$NETWORK" \
  --source "$SOURCE_ACCOUNT"
```

Optional overrides:

```bash
export VOLTA_VAULT_ADDRESS=<override_volta_contract_id>
./deployment/transfer-admin-to-volta.sh \
  --network "$NETWORK" \
  --source "$SOURCE_ACCOUNT" \
  --state-file /path/to/state.json
```


Default handoff set:

- Router upgrade admin
- Router pool admin
- Pool Configurator admin
- Interest Rate Strategy admin
- Treasury admin

Optional via env flags:

- Price Oracle admin if `TRANSFER_PRICE_ORACLE_ADMIN=true`
- Router emergency admin if `TRANSFER_EMERGENCY_ADMIN=true`

Manual reference (the script wraps these same calls):

```bash
export CURRENT_ADMIN=$(stellar keys address "$SOURCE_ACCOUNT")
export ROUTER=<router_contract_id>
export CONFIGURATOR=<pool_configurator_contract_id>
export INTEREST_RATE=<interest_rate_contract_id>
export TREASURY=<treasury_contract_id>
export ORACLE=<price_oracle_contract_id>
export TRANSFER_PRICE_ORACLE_ADMIN=false
export TRANSFER_EMERGENCY_ADMIN=false

# Router upgrade admin
stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
  propose_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"

# Router pool admin
stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
  propose_pool_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"

# Pool Configurator admin
stellar contract invoke --id "$CONFIGURATOR" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
  propose_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"

# Interest Rate Strategy admin
stellar contract invoke --id "$INTEREST_RATE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
  propose_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"

# Treasury admin
stellar contract invoke --id "$TREASURY" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
  propose_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"

# Optional: Price Oracle admin
if [[ "${TRANSFER_PRICE_ORACLE_ADMIN}" == "true" ]]; then
  stellar contract invoke --id "$ORACLE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
    propose_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"
fi

# Optional: Router emergency admin
if [[ "${TRANSFER_EMERGENCY_ADMIN}" == "true" ]]; then
  stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- \
    propose_emergency_admin --caller "$CURRENT_ADMIN" --pending-admin "$INCENTIVES_EMISSION_MANAGER"
fi
```


Important:

- Use `--pending-admin` (kebab-case), not `--new_admin`.
- Proposing the transfer only sets `pending_admin`. Ownership does not switch until the Volta side accepts and reaches threshold.

Accept via K2 Admin UI:

1. Update UI config to new addresses + new Volta vault.
2. Connect a Volta owner wallet.
3. Admin Transfer tab -> Accept each pending role.
4. Co-signer votes in Proposals tab until threshold is met.

---

## Step 5: Verify Handoff State

### 5.1 Verify Pending Handoff After Running `transfer-admin-to-volta.sh`

These should return `INCENTIVES_EMISSION_MANAGER` immediately after the proposal phase:

```bash
stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_admin
stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_pool_admin
stellar contract invoke --id "$CONFIGURATOR" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_admin
stellar contract invoke --id "$INTEREST_RATE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_admin
stellar contract invoke --id "$TREASURY" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_admin

if [[ "${TRANSFER_PRICE_ORACLE_ADMIN}" == "true" ]]; then
  stellar contract invoke --id "$ORACLE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_admin
fi

if [[ "${TRANSFER_EMERGENCY_ADMIN}" == "true" ]]; then
  stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_pending_emergency_admin
fi
```

### 5.2 Verify Completed Handoff After Volta Acceptance + Threshold Votes

These should return `INCENTIVES_EMISSION_MANAGER` after the Volta proposals have been accepted and executed:

```bash
stellar contract invoke --id "$ROUTER" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_admin
stellar contract invoke --id "$CONFIGURATOR" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_admin
stellar contract invoke --id "$INTEREST_RATE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- admin
stellar contract invoke --id "$TREASURY" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_admin

if [[ "${TRANSFER_PRICE_ORACLE_ADMIN}" == "true" ]]; then
  stellar contract invoke --id "$ORACLE" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- get_admin
fi
```

Notes:

- Kinetic Router does not expose a public current `pool_admin` getter in this flow. Verify router pool-admin handoff via the K2 Admin UI state change or by successfully executing a pool-admin-gated Volta proposal.
- If `TRANSFER_EMERGENCY_ADMIN=false`, `emergency_admin` remains on the EOA by design.

Verify incentives ownership path is Volta-managed:

```bash
export INCENTIVES=<incentives_contract_id>
stellar contract invoke --id "$INCENTIVES" --source "$SOURCE_ACCOUNT" --network "$NETWORK" -- is_paused
```

Then test a rewards admin action from K2 Admin (via Volta proposal), for example `fund_rewards` or `configure_asset_rewards`.

---

## Step 6: Update K2 Admin UI Config

Update `kinetic-demo/lib/data/testnet-deployment.json` with:

- New core contract addresses
- New token/aToken/debtToken addresses
- `contracts.voltaVault = INCENTIVES_EMISSION_MANAGER`

Run UI checks:

```bash
cd ../kinetic-demo
yarn type-check
yarn test
yarn dev
```

---

## Troubleshooting

### `unexpected argument '--new_admin'`

Use:

- `--caller <G...>`
- `--pending-admin <C...>`

### Why not set all admins to Volta in deploy script?

Because router/oracle/treasury `initialize()` require auth from the admin address itself. With plain EOA deployment transactions, contract-address auth (Volta) is not satisfied automatically.

### Can we build a true no-transfer flow?

Yes, but it requires a different deployment orchestrator that initializes and configures contracts through Volta invocations from the start (multisig approvals throughout). That is not what current `deployment/deploy.sh` does.
