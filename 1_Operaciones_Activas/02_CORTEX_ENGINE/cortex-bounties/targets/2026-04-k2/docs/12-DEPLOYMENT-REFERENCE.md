# 12. Deployment Guide

## Overview

The K2 lending protocol deployment process consists of two main phases:

1. **Build Phase** - Compile Rust contracts to WASM, optimize for size, and generate deployment artifacts
2. **Deploy Phase** - Deploy contracts to Soroban networks in dependency order, initialize with parameters, and verify functionality

### Deployment Phases

**Phase 1: Build** (local)
- Compile all 13 contracts using `cargo build` and `stellar contract build`
- Optimize WASM files to meet mainnet size constraints
- Generate hash signatures for verification
- Estimated time: 3-5 minutes

**Phase 2: Testnet** (optional but recommended)
- Deploy to testnet for validation
- Test all contract interactions
- Verify admin functions and configuration
- Estimated time: 15-30 minutes

**Phase 3: Mainnet** (production)
- Deploy to mainnet using same procedures as testnet
- Use multi-sig admin for governance
- Monitor first 48 hours closely
- Estimated time: 30-60 minutes

### Testing Strategy

Each phase includes:
1. **Deployment verification** - Check contract existence and WASM hash matches
2. **Initialization verification** - Confirm initialization parameters were set
3. **Functional testing** - Execute sample transactions (supply, borrow, liquidate)
4. **Integration testing** - Test cross-contract interactions
5. **Configuration validation** - Verify all reserves and parameters are correct

---

## Prerequisites

### Tools Required

```bash
# Stellar CLI (latest)
stellar --version
# Expected: 23.0.0+

# Rust toolchain with Soroban support
rustup target add wasm32-unknown-unknown
rustup component add rust-src

# Installation
cargo install --force --locked stellar-cli
```

### Environment Setup

**macOS/Linux:**
```bash
# Add Stellar tools to PATH
export PATH="$HOME/.stellar/bin:$PATH"

# Create project directories
mkdir -p ~/.stellar/networks
mkdir -p ~/.stellar/keys
```

**Windows (PowerShell):**
```powershell
# Add to profile
$env:Path += ";$env:APPDATA\.stellar\bin"
```

### Dependencies Checklist

```bash
# Verify installation
stellar contract --help
rustc --version
cargo --version
jq --version  # For JSON parsing in scripts
```

### Network Configuration

Add networks before deployment:

```bash
# Testnet (Soroban RPC)
stellar network add testnet \
  --rpc-url "https://soroban-testnet.stellar.org" \
  --network-passphrase "Test SDF Network ; September 2015"

# Mainnet (production)
stellar network add mainnet \
  --rpc-url "https://soroban-mainnet.stellar.org" \
  --network-passphrase "Public Global Stellar Network ; September 2015"

# Verify networks
stellar network list
```

---

## Build Instructions

### stellar contract build

The official Soroban build command compiles a single contract from its directory:

```bash
cd contracts/CONTRACT_NAME
stellar contract build
```

**Output:**
- Location: `target/wasm32v1-none/release/{contract_name}.wasm`
- Unoptimized size: ~300-600 KB
- Can be deployed directly but not recommended for mainnet

### Optimization

All contracts must be optimized before mainnet deployment:

```bash
# Optimize a single WASM file
stellar contract optimize \
  --wasm target/wasm32v1-none/release/kinetic_router.wasm \
  --wasm-out target/wasm32v1-none/release/kinetic_router.optimized.wasm
```

**Size Reduction:**
- Typical reduction: 30-50% (e.g., 500 KB  -> 250 KB)
- Mainnet requirement: < 200 KB (enforced by Soroban)

**Check optimized size:**
```bash
ls -lh target/wasm32v1-none/release/*.optimized.wasm | awk '{print $9, $5}'
```

### stellar contract build (Workspace)

For the entire K2 workspace, Rust's cargo can build all contracts:

```bash
# From project root
cargo build --release --target wasm32-unknown-unknown
```

This outputs all contract WASMs to `target/wasm32v1-none/release/`.

---

## Build Script

Use the provided `./deployment/build.sh` for automated building and optimization:

### Quick Start

```bash
cd /path/to/k2-contracts
./deployment/build.sh
```

This script:
1. Builds all 14 contracts from `contracts/CONTRACT_NAME/` directories
2. Optimizes all unoptimized WASM files via `stellar contract optimize`
3. Reports final sizes and success
4. Validates all contracts compiled successfully

### Build Output

```
Building kinetic-router...
Building a-token...
Building debt-token...
...
Optimizing WASM files...
Optimizing target/wasm32v1-none/release/kinetic_router.wasm...
...
Build complete. Optimized WASMs are in target/wasm32v1-none/release/

Contract sizes:
  target/wasm32v1-none/release/kinetic_router.optimized.wasm: 186K
  target/wasm32v1-none/release/a_token.optimized.wasm: 98K
  target/wasm32v1-none/release/debt_token.optimized.wasm: 98K
  ...
```

### Contracts Built

The script builds 14 contracts in order:
  Contract | Type | Used By |
  ----------|------|---------|
  kinetic-router | Core | All operations |
  a-token | Token | Supply collateral |
  debt-token | Token | Borrow positions |
  price-oracle | Oracle | Price lookups |
  pool-configurator | Admin | Reserve setup |
  liquidation-engine | Helper | Liquidation processing |
  interest-rate-strategy | Config | Rate calculation |
  incentives | Rewards | Reward distribution |
  treasury | Fees | Fee collection |
  flash-liquidation-helper | Helper | Flash loans |
  token | Token | Underlying test assets |
  aquarius-swap-adapter | DEX | Liquidation swaps |
  soroswap-swap-adapter | DEX | Liquidation swaps |
  redstone-feed-wrapper | Oracle | RedStone price feeds (all networks) |

**Build command:**
```bash
./deployment/build.sh
```

**What it does:**
1. Builds all 14 contracts via `stellar contract build` from `contracts/CONTRACT_NAME`
2. Optimizes all WASM files via `stellar contract optimize`
3. Reports final file sizes

**Note on redstone-adapter:**
- Commented out in build.sh (only for testnet; RedStone maintains mainnet adapter)
- K2 deploys redstone-feed-wrapper wrappers for all networks

**Total deployable size:** ~1.2 MB (well under typical limits)

---

## Manual Build

Build individual contracts outside the script:

### Build Single Contract

```bash
cd contracts/kinetic-router
stellar contract build
```

**Output:** `target/wasm32v1-none/release/kinetic_router.wasm` (from project root)

### Build with Logs

```bash
RUST_LOG=debug stellar contract build
```

### Clean Build

```bash
cd /path/to/k2-contracts
cargo clean
./deployment/build.sh
```

### Manual WASM Optimization

After building, optimize individual WASMs:

```bash
stellar contract optimize \
  --wasm target/wasm32v1-none/release/kinetic_router.wasm \
  --wasm-out target/wasm32v1-none/release/kinetic_router.optimized.wasm
```

### Cargo.toml Optimization Profile

The workspace includes optimized release profile:

```toml
[profile.release]
opt-level = "z"        # Optimize for size
overflow-checks = true # Catch integer overflow
debug = 0              # No debug symbols
strip = "symbols"      # Remove symbols
lto = true             # Link-time optimization
```

---

## WASM Optimization

### Why Optimize?

1. **Size requirement** - Soroban has 200 KB limit per contract
2. **Deployment cost** - Smaller WASM = lower fees
3. **Network efficiency** - Faster transmission

### Automatic Optimization

The `./deployment/build.sh` script automatically optimizes all WASMs:

```bash
# Optimization happens automatically in build.sh
for wasm in target/wasm32v1-none/release/*.wasm; do
  if [[ ! "$wasm" =~ \.optimized\.wasm$ ]]; then
    stellar contract optimize --wasm "$wasm" --wasm-out "${wasm%.wasm}.optimized.wasm"
  fi
done
```

### Manual Optimization

For individual contracts:

```bash
stellar contract optimize --wasm input.wasm --wasm-out output.optimized.wasm
```

### Verification

```bash
# Check final sizes
ls -lh target/wasm32v1-none/release/*.optimized.wasm | awk '{print $9 ": " $5}'

# Verify all are under 200 KB limit
ls -lh target/wasm32v1-none/release/*.optimized.wasm | \
  awk '{if ($5 ~ /[M]/ || ($5 ~ /K/ && int(substr($5,1,length($5)-1)) > 200)) print "FAIL: " $9 " is " $5}'
```

### Mainnet Requirement

All contracts **must** be optimized before mainnet:

```bash
# Verify all 14 optimized files exist (testnet) or 13 (mainnet without redstone-adapter)
ls -1 target/wasm32v1-none/release/*.optimized.wasm | wc -l

# Check max size (all should be < 200KB)
ls -lh target/wasm32v1-none/release/*.optimized.wasm
```

---

## Testnet Deployment

### Step-by-Step Testnet Deployment

#### 1. Setup Account

```bash
# Generate deployer account if needed
stellar keys generate k2-deployer --network testnet

# Fund with testnet friendbot (or manually add XLM)
curl "https://friendbot.stellar.org?addr=$(stellar keys address k2-deployer)"

# Verify funding (need ~10 XLM for all deployments)
stellar account info k2-deployer --network testnet
```

#### 2. Environment Variables

```bash
# Set deployer and required tokens
export SOURCE_ACCOUNT="k2-deployer"
export NETWORK="testnet"

# Required: existing USDC address on testnet
export EXISTING_USDC="CCSRDNFQQSZ52XOHZBOTPVZBEK5GG4YLJMJMIEFWKSLLWFK3TPZ4GLT5"

# Optional: custom network/RPC
export SOROBAN_RPC_URL="https://soroban-testnet.stellar.org"
```

#### 3. Build Contracts

```bash
cd /path/to/k2-contracts
./deployment/build.sh

# Verify all optimized WASMs exist
ls -1 target/wasm32v1-none/release/*.optimized.wasm | wc -l
```

#### 4. Deploy via Script

```bash
# Dry run first (no actual deployment)
./deployment/deploy.sh \
  --network testnet \
  --source k2-deployer \
  --dry-run

# Actual deployment
./deployment/deploy.sh \
  --network testnet \
  --source k2-deployer
```

#### 5. Monitor Deployment

```bash
# Watch logs in real time
tail -f logs/deploy_testnet_*.log

# Check deployment state
cat deployments/testnet/state.json | jq '.contracts'
```

### Deployment Output

```
[INFO] Deploying K2 Protocol to testnet
[INFO] Checking network configuration...
[INFO] Loading WASM files from target/wasm32v1-none/release/
[INFO] Deploying k2_price_oracle...
[INFO]   Contract address: C1234567...
[INFO]   WASM hash: ab1234567...
[INFO]   Initializing...
[INFO] Deploying k2_interest_rate_strategy...
...
[INFO] Deployment complete!
[INFO] Summary: 11 contracts deployed in 24 seconds
```

---

## Deploy Script

The comprehensive `./deployment/deploy.sh` handles all deployment logic including building, deploying, initializing, and verifying contracts.

### Usage

```bash
./deployment/deploy.sh [OPTIONS]

Options:
  -n, --network <NETWORK>      Target network (local|testnet|mainnet) [default: testnet]
  -s, --source <ACCOUNT>       Source account for signing [default: k2-deployer]
  -d, --dry-run                Simulate deployment without executing
  --skip-build                 Skip contract build step
  --skip-verify                Skip WASM hash verification
  --skip-pool-seed             Skip Soroswap pool seeding and price sync
  --force-redeploy             Force redeploy all contracts even if already deployed
  --no-ttl-extend              Don't extend contract TTL after deploy
  -v, --verbose                Enable verbose output
  -h, --help                   Show help message
```

### Common Usage Patterns

**Testnet deployment (builds + deploys + initializes):**
```bash
./deployment/deploy.sh --network testnet
```

**Mainnet dry run (no execution):**
```bash
./deployment/deploy.sh --network mainnet --dry-run
```

**Resume failed deployment (skip build):**
```bash
./deployment/deploy.sh --network testnet --skip-build
```

**Verbose debugging:**
```bash
./deployment/deploy.sh --network testnet --verbose 2>&1 | tee deployment.log
```

**Mainnet with specific deployer:**
```bash
./deployment/deploy.sh --network mainnet --source k2-mainnet-deployer
```

### Resume Functionality

The script automatically tracks deployment state in `deployments/{network}/state.json`:
- Already deployed contracts are skipped
- Already initialized contracts are detected on-chain and skipped
- Reserve configuration is tracked and skipped if done

If interrupted, simply re-run the same command to resume from where it left off.

### State Tracking

The script maintains deployment state in `deployments/{network}/state.json`:

```json
{
  "network": "testnet",
  "created_at": "2025-02-10T12:00:00Z",
  "updated_at": "2025-02-10T12:05:00Z",
  "deployer": "GXXX...",
  "contracts": {
    "k2_price_oracle": {
      "address": "CXXX...",
      "alias": "price_oracle",
      "wasm_hash": "ab12...",
      "deployed_at": "2025-02-10T12:00:30Z",
      "tx_hash": "xxx..."
    }
  },
  "wasm_hashes": {
    "kinetic_router.optimized.wasm": "ab12..."
  },
  "deployment_history": [
    {
      "timestamp": "2025-02-10T12:00:00Z",
      "action": "deploy",
      "contract": "k2_price_oracle",
      "address": "CXXX...",
      "status": "success"
    }
  ]
}
```

### Contract Aliases

Deployed contracts are registered with aliases:

```bash
# Query by alias (no address needed)
stellar contract invoke --id kinetic_router --network testnet -- \
  get_pool_admin

# Query by address
stellar contract invoke \
  --id "CXXX..." \
  --network testnet \
  -- get_pool_admin
```

### Skip Already-Deployed Contracts

The script checks `state.json` and skips re-deployment:

```bash
# To force redeploy, remove from state.json:
jq 'del(.contracts.k2_price_oracle)' deployments/testnet/state.json > tmp.json
mv tmp.json deployments/testnet/state.json
```

Or delete entire state for fresh deployment:
```bash
rm deployments/testnet/state.json
./deployment/deploy.sh --network testnet
```

---

## Manual Deployment

Deploy contracts individually when troubleshooting or customizing.

### Deploy Single Contract

```bash
# Deploy kinetic-router
stellar contract deploy \
  --wasm target/wasm32v1-none/release/kinetic_router.optimized.wasm \
  --source k2-deployer \
  --network testnet \
  --alias kinetic_router

# Output:
# Created contract: CXXX...
```

### Get WASM Hash

```bash
# Required for verification
stellar contract install \
  --wasm target/wasm32v1-none/release/kinetic_router.optimized.wasm \
  --source k2-deployer \
  --network testnet

# Returns WASM hash (aaaa1234...)
# This is stored but not deployed yet
```

### Deploy from Hash

```bash
# Deploy already-installed WASM by hash
stellar contract deploy \
  --wasm-hash "aaaa1234..." \
  --source k2-deployer \
  --network testnet \
  --alias kinetic_router
```

### Fund Contract Before Initialization

Contracts need minimum balance before accepting calls:

```bash
# Create contract and get address
CONTRACT_ADDR=$(stellar contract deploy \
  --wasm target/wasm32v1-none/release/kinetic_router.optimized.wasm \
  --source k2-deployer \
  --network testnet \
  --alias kinetic_router 2>&1 | grep "Created contract" | awk '{print $NF}')

echo "Deployed to: $CONTRACT_ADDR"

# Extend TTL (ensure contract doesn't expire)
stellar contract extend \
  --id "$CONTRACT_ADDR" \
  --source k2-deployer \
  --network testnet \
  --ledgers-to-extend 3110400  # 1 year
```

### Manual Account Setup

```bash
# Generate new account (no network call needed yet)
stellar keys generate k2-mainnet-admin --network mainnet

# Get public key (save this!)
stellar keys address k2-mainnet-admin

# Add to hardware wallet / multi-sig setup
# ... then fund via exchange or another account

# Verify funded
stellar account info k2-mainnet-admin --network mainnet
```

---

## Network Configuration

### Available Networks

**Testnet (for testing):**
```bash
stellar network add testnet \
  --rpc-url "https://soroban-testnet.stellar.org" \
  --network-passphrase "Test SDF Network ; September 2015"
```

**Mainnet (production):**
```bash
stellar network add mainnet \
  --rpc-url "https://soroban-mainnet.stellar.org" \
  --network-passphrase "Public Global Stellar Network ; September 2015"
```

**Local (for development):**
```bash
stellar network add local \
  --rpc-url "http://localhost:8000" \
  --network-passphrase "Soroban Standalone Network ; September 2015"
```

### View Configuration

```bash
# List all networks
stellar network list

# Show active network
stellar network show

# Switch network for a command
stellar keys address --network mainnet k2-deployer
```

### RPC Endpoints
  Network | RPC URL | Passphrase |
  ---------|---------|-----------|
  Testnet | `https://soroban-testnet.stellar.org` | `Test SDF Network ; September 2015` |
  Mainnet | `https://soroban-mainnet.stellar.org` | `Public Global Stellar Network ; September 2015` |
  Futurenet | `https://soroban-futurenet.stellar.org` | `Test SDF Future Network ; September 2015` |

---

## Account Setup

### Key Generation

**Generate new deployer account:**
```bash
stellar keys generate k2-deployer --network testnet
```

**Generate mainnet admin account:**
```bash
stellar keys generate k2-mainnet-admin --network mainnet
```

**List all keys:**
```bash
stellar keys ls
```

### Fund Accounts

**Testnet friendbot (automatic):**
```bash
# Friendbot sends 10,000 XLM
curl "https://friendbot.stellar.org?addr=$(stellar keys address k2-deployer)"

# Verify
stellar account info k2-deployer --network testnet
```

**Mainnet (manual exchange transfer):**
```bash
# Get address
ADDRESS=$(stellar keys address k2-mainnet-admin)

# Transfer 10 XLM from your exchange account to $ADDRESS
# Then verify:
stellar account info k2-mainnet-admin --network mainnet
```

### Set Transaction Permissions

For multi-sig mainnet setup:

```bash
# Export public key
PUBKEY=$(stellar keys address k2-deployer)

# Use in multi-sig contract initialization
# (See section: Initialize Kinetic Router)
```

---

## Contract Deployment Order

The `./deployment/deploy.sh` script deploys contracts in this exact order:

**Base 11 contracts (all networks):**
```bash
1. k2_price_oracle               (No dependencies)
2. k2_interest_rate_strategy     (No dependencies)
3. k2_treasury                   (No dependencies)
4. k2_incentives                 (No dependencies)
5. k2_kinetic_router             (Depends on 1-4)
6. k2_pool_configurator          (Depends on 5)
7. k2_flash_liquidation_helper   (Depends on 5)
8. k2_a_token (USDC)             (Depends on 5)
9. k2_a_token (XLM)              (Depends on 5)
10. k2_debt_token (USDC)         (Depends on 5)
11. k2_debt_token (XLM)          (Depends on 5)
```

**Additional on testnet:**
```bash
12. k2_redstone_adapter          (testnet only; RedStone maintains mainnet)
```

**From CONTRACTS array in deploy.sh:**

```bash
CONTRACTS=(
    "k2_price_oracle:price_oracle"
    "k2_interest_rate_strategy:interest_rate"
    "k2_treasury:treasury"
    "k2_incentives:incentives"
    "k2_kinetic_router:kinetic_router"
    "k2_pool_configurator:configurator"
    "k2_flash_liquidation_helper:flash_liquidation"
    "k2_a_token:atoken_usdc"
    "k2_a_token:atoken_xlm"
    "k2_debt_token:debt_usdc"
    "k2_debt_token:debt_xlm"
)

# RedStone adapter only deployed on testnet (RedStone maintains mainnet adapter)
if [[ "$NETWORK" == "testnet" ]]; then
    CONTRACTS+=(
        "k2_redstone_adapter:redstone_adapter"
    )
fi
```

**Why this order?**

- **Phase 1** - Oracle, IRS, Treasury, Incentives (no dependencies, initialize independently)
- **Phase 2** - Router (initializes with Phase 1 contracts)
- **Phase 3** - Configurator, Flash helper (register with router)
- **Phase 4** - Tokens (initialize with router)
- **Phase 5** - Reserve configuration (via Pool Configurator)
- **Phase 6** - Pool seeding and price syncing (testnet only)

---

## Initialize Contracts

After deployment, initialize each contract with parameters.

### Kinetic Router

**Parameters:**
```bash
POOL_ADMIN="G..."            # Admin account (can be multi-sig)
EMERGENCY_ADMIN="G..."       # Can pause/unpause
ORACLE_CONTRACT="C..."       # Price oracle address
TREASURY_CONTRACT="C..."     # Treasury contract
SOROSWAP_ROUTER="C..."       # Soroswap adapter
AQUARIUS_ROUTER="C..."       # Aquarius adapter
```

**Initialize:**
```bash
stellar contract invoke \
  --id kinetic_router \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --pool_admin "$POOL_ADMIN" \
  --emergency_admin "$EMERGENCY_ADMIN" \
  --oracle "$ORACLE_CONTRACT" \
  --treasury "$TREASURY_CONTRACT" \
  --swap_adapters '[
    {"soroswap": "'$SOROSWAP_ROUTER'"},
    {"aquarius": "'$AQUARIUS_ROUTER'"}
  ]'
```

### Price Oracle

**Parameters:**
```bash
ADMIN="G..."              # Oracle admin
BASE_CURRENCY="C..."      # USDC (base for prices)
REFLECTOR_ORACLE="C..."   # Stellar Reflector oracle
```

**Initialize:**
```bash
stellar contract invoke \
  --id price_oracle \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --admin "$ADMIN" \
  --base_currency "$BASE_CURRENCY" \
  --reflector_oracle "$REFLECTOR_ORACLE"
```

### Interest Rate Strategy

**Parameters:**
```bash
ADMIN="G..."                                          # IRS admin
BASE_VARIABLE_BORROW_RATE="20000000000000000000000000"  # 2% (RAY precision, 1e27 = 100%)
VARIABLE_RATE_SLOPE1="40000000000000000000000000"       # 4% (RAY precision)
VARIABLE_RATE_SLOPE2="600000000000000000000000000"      # 60% (RAY precision)
OPTIMAL_UTILIZATION_RATE="800000000000000000000000000"   # 80% (RAY precision)
```

**Initialize:**
```bash
stellar contract invoke \
  --id interest_rate \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --admin "$ADMIN" \
  --base_variable_borrow_rate "$BASE_VARIABLE_BORROW_RATE" \
  --variable_rate_slope1 "$VARIABLE_RATE_SLOPE1" \
  --variable_rate_slope2 "$VARIABLE_RATE_SLOPE2" \
  --optimal_utilization_rate "$OPTIMAL_UTILIZATION_RATE"
```

### Treasury

**Parameters:**
```bash
ADMIN="G..."         # Treasury admin
```

**Initialize:**
```bash
stellar contract invoke \
  --id treasury \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --admin "$ADMIN"
```

### Incentives

**Initialize:**
```bash
stellar contract invoke \
  --id incentives \
  --source k2-deployer \
  --network testnet \
  -- initialize
```

---

## Register Assets

After router initialization, add assets (reserves) to the protocol.

### Add USDC Reserve

**Parameters:**
```bash
ASSET_CODE="USDC"
ASSET_ISSUER="GBUQWP3BOUZX34ULNQG23RQ6F4BVWCIAMRUILY3M3MS5BNQHTQP2P6L"
DECIMALS="9"
INITIAL_PRICE="100000000000000"  # $1.00 USD (price × 10^14)
```

**Register:**
```bash
stellar contract invoke \
  --id kinetic_router \
  --source k2-deployer \
  --network testnet \
  -- add_reserve \
  --asset '{"asset_code": "'$ASSET_CODE'", "issuer": "'$ASSET_ISSUER'"}' \
  --decimals "$DECIMALS" \
  --price "$INITIAL_PRICE"
```

### Add XLM Reserve

**Parameters:**
```bash
ASSET_CODE="native"
DECIMALS="7"
INITIAL_PRICE="25000000000000"  # $0.25 USD (price × 10^14)
```

**Register:**
```bash
stellar contract invoke \
  --id kinetic_router \
  --source k2-deployer \
  --network testnet \
  -- add_reserve \
  --asset '{"asset_code": "native"}' \
  --decimals "$DECIMALS" \
  --price "$INITIAL_PRICE"
```

---

## Configure Reserves

For each reserve, deploy and initialize tokens, then configure parameters.

### Deploy aToken and DebtToken

```bash
# aToken for USDC
stellar contract deploy \
  --wasm target/wasm32v1-none/release/a_token.optimized.wasm \
  --source k2-deployer \
  --network testnet \
  --alias atoken_usdc

# DebtToken for USDC
stellar contract deploy \
  --wasm target/wasm32v1-none/release/debt_token.optimized.wasm \
  --source k2-deployer \
  --network testnet \
  --alias debt_usdc
```

### Initialize aToken

```bash
stellar contract invoke \
  --id atoken_usdc \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --router "$KINETIC_ROUTER_ADDR" \
  --underlying_asset "$USDC_ADDR" \
  --decimals "9"
```

### Initialize DebtToken

```bash
stellar contract invoke \
  --id debt_usdc \
  --source k2-deployer \
  --network testnet \
  -- initialize \
  --router "$KINETIC_ROUTER_ADDR" \
  --underlying_asset "$USDC_ADDR" \
  --decimals "9"
```

### Configure Reserve Parameters

```bash
stellar contract invoke \
  --id kinetic_router \
  --source k2-deployer \
  --network testnet \
  -- configure_reserve \
  --reserve_index "0" \
  --ltv_threshold "7500"           # 75% LTV
  --liquidation_threshold "8000"   # 80%
  --liquidation_bonus "500"        # 5% bonus
  --supply_cap "10000000"          # 10M USDC (human units)
  --borrow_cap "5000000"           # 5M USDC (human units)
  --reserve_factor "1000"          # 10% protocol share
```

---

## Verify Deployment

After deployment, verify all contracts exist and initialized correctly using the deployment summary and state file.

### Check Deployment State File

```bash
# View deployment state
cat deployments/testnet/state.json | jq '.contracts'

# Output includes all deployed contract addresses, WASM hashes, and timestamps
# Example:
# {
#   "price_oracle": {
#     "address": "CXXX...",
#     "wasm_hash": "abc123...",
#     "deployed_at": "2025-02-10T12:00:00Z",
#     "initialized": true,
#     "initialized_at": "2025-02-10T12:00:15Z"
#   },
#   ...
# }
```

### Check Deployment Summary

```bash
# View human-readable summary
cat deployments/testnet/DEPLOYMENT_SUMMARY.md

# Lists all contract addresses and external dependencies
```

### Verify Contract Existence

```bash
# Query deployed contract info
stellar contract info \
  --id kinetic_router \
  --network testnet

# Should output: Address and Source Code Hash (WASM hash)
```

### Verify WASM Hashes

```bash
# Compare deployed hash with local WASM file
# Get deployed hash from state file:
cat deployments/testnet/state.json | jq '.contracts.kinetic_router.wasm_hash'

# Verify local WASM matches (stored in state.json after deploy.sh runs)
```

### Query Initialization State

```bash
# Check if router is initialized
stellar contract invoke \
  --id kinetic_router \
  --network testnet \
  -- get_pool_admin

# Should return admin address (not error)

# Check oracle
stellar contract invoke \
  --id kinetic_router \
  --network testnet \
  -- get_oracle

# Should return oracle contract address
```

### Test Basic Functionality

```bash
# Get reserves (viewable function)
stellar contract invoke \
  --id kinetic_router \
  --network testnet \
  -- get_reserves

# Should return reserve data

# Get asset price from oracle
stellar contract invoke \
  --id price_oracle \
  --network testnet \
  -- get_asset_price \
  --asset '{"Stellar":"<USDC_ADDRESS>"}'

# Should return price in WAD precision (1e18)
```

---

## Integration Testing

Run realistic transaction flows to validate the deployment.

### Test 1: Supply Collateral

```bash
# User supplies USDC as collateral
stellar contract invoke \
  --id kinetic_router \
  --source testuser \
  --network testnet \
  -- supply \
  --asset '{"asset_code": "USDC", "issuer": "GBUQ..."}' \
  --amount "1000000000000"  # 1,000 USDC (9 decimals)

# Verify aToken balance increased
stellar contract invoke \
  --id atoken_usdc \
  --network testnet \
  -- balance_of \
  --id "$TESTUSER"

# Should return 1,000,000,000 aTokens
```

### Test 2: Borrow Asset

```bash
# User borrows against collateral
stellar contract invoke \
  --id kinetic_router \
  --source testuser \
  --network testnet \
  -- borrow \
  --asset '{"asset_code": "native"}' \
  --amount "100000000"  # 100 XLM

# Verify debt token minted
stellar contract invoke \
  --id debt_xlm \
  --network testnet \
  -- balance_of \
  --id "$TESTUSER"

# Should return 100,000,000 debt tokens
```

### Test 3: Repay Loan

```bash
# User repays borrow
stellar contract invoke \
  --id kinetic_router \
  --source testuser \
  --network testnet \
  -- repay \
  --asset '{"asset_code": "native"}' \
  --amount "50000000"  # Repay 50 XLM

# Verify debt reduced
stellar contract invoke \
  --id debt_xlm \
  --network testnet \
  -- balance_of \
  --id "$TESTUSER"

# Should return 50,000,000 remaining
```

### Test 4: Withdraw Collateral

```bash
# User withdraws aToken
stellar contract invoke \
  --id kinetic_router \
  --source testuser \
  --network testnet \
  -- withdraw \
  --asset '{"asset_code": "USDC", "issuer": "GBUQ..."}' \
  --amount "500000000"  # 500 USDC

# Verify aToken balance decreased
stellar contract invoke \
  --id atoken_usdc \
  --network testnet \
  -- balance_of \
  --id "$TESTUSER"

# Should return 500,000,000 aTokens (1B - 500M)
```

### Test 5: Liquidation Flow

```bash
# Liquidator executes liquidation (if user is unhealthy)
stellar contract invoke \
  --id kinetic_router \
  --source liquidator \
  --network testnet \
  -- liquidation_call \
  --user_to_liquidate "$UNHEALTHY_USER" \
  --debt_asset '{"asset_code": "native"}' \
  --debt_to_cover "50000000" \
  --collateral_asset '{"asset_code": "USDC", "issuer": "GBUQ..."}' \
  --receive_a_token false

# Liquidator receives USDC, protocol receives liquidation fees
```

---

## Mainnet Preparation

### Pre-Deployment Checklist

```
[ ] Code audit completed and fixes verified
[ ] All unit tests passing (cargo test --all)
[ ] All integration tests passing on testnet
[ ] Testnet deployment running for 48+ hours without incidents
[ ] All contract WASM files optimized and under 200 KB
[ ] Multi-sig contract deployed and tested
[ ] Mainnet RPC endpoints verified working
[ ] All admin keys securely stored (hardware wallet/multi-sig)
[ ] Emergency admin account separate from pool admin
[ ] Mainnet oracle prices confirmed and updating
[ ] DEX adapters (Soroswap, Aquarius) confirmed available on mainnet
[ ] Network configuration (passphrases, RPC URLs) verified
[ ] Deployment scripts tested against mainnet (dry-run)
[ ] Post-deployment monitoring system ready
[ ] Incident response procedures documented
```

### Multi-Sig Admin Setup

For mainnet, use multi-sig timelock contract for governance:

```bash
# Deploy multi-sig contract
stellar contract deploy \
  --wasm k2_multisig.optimized.wasm \
  --source mainnet-deployer \
  --network mainnet \
  --alias k2_pool_admin_multisig

# Initialize with signers
stellar contract invoke \
  --id k2_pool_admin_multisig \
  --source mainnet-deployer \
  --network mainnet \
  -- initialize \
  --signers '["GXXX1...", "GXXX2...", "GXXX3...", "GXXX4...", "GXXX5..."]' \
  --threshold "3" \
  --timelock_delay "34560"  # 48 hours
```

### Dry Run Deployment

Test mainnet deployment without executing:

```bash
# Dry run (no actual deployment)
./deployment/deploy.sh \
  --network mainnet \
  --source mainnet-deployer \
  --dry-run

# Review output carefully
# Check contract addresses, initialization parameters
```

---

## Mainnet Deployment

### Pre-Deployment Setup

```bash
# 1. Create mainnet deployer account
stellar keys generate k2-mainnet-deployer --network mainnet

# 2. Fund with 20 XLM (enough for all contracts + gas)
# Transfer from exchange to the address above

# 3. Set environment
export NETWORK="mainnet"
export SOURCE_ACCOUNT="k2-mainnet-deployer"
export EXISTING_USDC="<mainnet_usdc_address>"

# 4. Verify network config
stellar network show mainnet
```

### Execute Mainnet Deployment

```bash
# Final safety check
echo "Deploying to MAINNET!"
read -p "Continue? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
  ./deployment/deploy.sh \
    --network mainnet \
    --source k2-mainnet-deployer \
    --verbose 2>&1 | tee mainnet_deployment_$(date +%Y%m%d_%H%M%S).log
fi
```

### Deployment Sequence (Mainnet)

1. **Deploy and initialize oracle** (10-15 min)
2. **Deploy and initialize interest rate strategy** (5 min)
3. **Deploy and initialize treasury** (5 min)
4. **Deploy and initialize incentives** (5 min)
5. **Deploy and initialize kinetic router** (15 min)
6. **Transfer pool admin to multi-sig** (5 min)
7. **Deploy configurator and helpers** (10 min)
8. **Deploy token contracts** (20 min)
9. **Register reserves and configure parameters** (20 min)
10. **Verify all contracts and functionality** (20 min)

**Total estimated time: 90-120 minutes**

---

## Post-Mainnet Monitoring

### First 24 Hours

**Every 30 minutes:**
```bash
# Check contract status
stellar contract info --id kinetic_router --network mainnet

# Monitor important functions (no gas cost for readonly)
stellar contract invoke --id kinetic_router --network mainnet -- \
  get_active_reserves_count

stellar contract invoke --id kinetic_router --network mainnet -- \
  get_total_deposits
```

**Every 2 hours:**
```bash
# Get price oracle status
stellar contract invoke --id price_oracle --network mainnet -- \
  get_last_update_time

# Check if prices are updating (should be recent)
```

### First 48 Hours

**Track key metrics:**

```bash
# Total deposits
stellar contract invoke --id kinetic_router --network mainnet -- \
  get_total_deposits

# Total borrows
stellar contract invoke --id kinetic_router --network mainnet -- \
  get_total_borrows

# Average health factor (sample users)
stellar contract invoke --id kinetic_router --network mainnet -- \
  get_user_account_data \
  --user "$USER_ADDRESS"
```

**Watch for unusual activity:**
- Sudden price movements
- Rapid liquidity drains
- Failed transactions (increase in error rates)
- Unexpected liquidations

### Alerts to Set Up

```bash
# Monitor contract balance (should grow with deposits)
stellar account info <ROUTER_ADDRESS> --network mainnet | grep Balance

# Monitor reserve utilization (should be stable)
# Alert if single reserve exceeds 95% utilization

# Monitor oracle staleness
# Alert if last update > 1 hour

# Monitor health factor distribution
# Alert if significant positions drop below 1.2
```

---

## Rollback Procedures

If critical issues discovered after mainnet deployment:

### Immediate Actions

```bash
# 1. Pause the protocol
stellar contract invoke \
  --id kinetic_router \
  --source mainnet-emergency-admin \
  --network mainnet \
  -- pause_protocol

# Prevents new operations while investigating

# 2. Assess damage
stellar contract invoke \
  --id kinetic_router \
  --network mainnet \
  -- get_total_deposits

# Calculate loss exposure
```

### Rollback if Necessary

**Option 1: Pause and Investigate (Preferred)**

```bash
# Keep protocol paused while investigating
# Users can still withdraw/repay but can't supply/borrow
# Gives time to develop proper fix

# Monitor situation
while true; do
  stellar contract invoke \
    --id kinetic_router \
    --network mainnet \
    -- is_paused
  sleep 60
done
```

**Option 2: Re-Deploy Previous Version**

```bash
# Only if pause is insufficient

# 1. Update to previous working WASM commit
git checkout <PREVIOUS_COMMIT_HASH>

# 2. Rebuild previous version
./deployment/build.sh

# 3. Deploy previous WASM (may require multi-sig)
stellar contract deploy \
  --wasm target/wasm32v1-none/release/kinetic_router.optimized.wasm \
  --source mainnet-deployer \
  --network mainnet \
  --alias kinetic_router_v2

# 4. Migrate state (if possible, depends on upgrade mechanism)
```

### Communication

```bash
# Notify users immediately
# 1. Post on social media
# 2. Email subscribers
# 3. Update status page

# Sample message:
echo "K2 Protocol paused due to [issue].
      We are investigating and will provide updates every 30 minutes.
      All deposits are safe. No user action required at this time."
```

---

## Reserve Addition

Add new assets post-deployment.

### Add New Reserve (Example: BTC)

**Preparation:**

```bash
# 1. Verify BTC price feed available in oracle
stellar contract invoke \
  --id price_oracle \
  --network mainnet \
  -- get_price \
  --asset '{"asset_code": "BTC", "issuer": "..."}'

# 2. Check DEX trading pairs
# Must have BTC/USDC pair on Soroswap and/or Aquarius for liquidations

# 3. Get asset details
ASSET_CODE="BTC"
ASSET_ISSUER="GBUQWP3BOUZX34ULNQG23RQ6F4BVWCIAMRUILY3M3MS5BNQHTQP2P6L"
DECIMALS="7"
LTV="5000"  # 50% (BTC is volatile)
LIQUIDATION_THRESHOLD="6500"  # 65%
LIQUIDATION_BONUS="1000"  # 10%
```

**Deployment:**

```bash
# 1. Register reserve
stellar contract invoke \
  --id kinetic_router \
  --source k2-mainnet-deployer \
  --network mainnet \
  -- add_reserve \
  --asset '{"asset_code": "'$ASSET_CODE'", "issuer": "'$ASSET_ISSUER'"}' \
  --decimals "$DECIMALS" \
  --price "65000000000"  # Current BTC price in USD

# 2. Deploy aToken for BTC
stellar contract deploy \
  --wasm target/wasm32v1-none/release/a_token.optimized.wasm \
  --source k2-mainnet-deployer \
  --network mainnet \
  --alias atoken_btc

# 3. Initialize aToken
stellar contract invoke \
  --id atoken_btc \
  --source k2-mainnet-deployer \
  --network mainnet \
  -- initialize \
  --router "$KINETIC_ROUTER_ADDR" \
  --underlying_asset "$ASSET_ISSUER" \
  --decimals "$DECIMALS"

# 4. Deploy debtToken for BTC
stellar contract deploy \
  --wasm target/wasm32v1-none/release/debt_token.optimized.wasm \
  --source k2-mainnet-deployer \
  --network mainnet \
  --alias debt_btc

# 5. Initialize debtToken
stellar contract invoke \
  --id debt_btc \
  --source k2-mainnet-deployer \
  --network mainnet \
  -- initialize \
  --router "$KINETIC_ROUTER_ADDR" \
  --underlying_asset "$ASSET_ISSUER" \
  --decimals "$DECIMALS"

# 6. Configure reserve parameters
stellar contract invoke \
  --id kinetic_router \
  --source k2-mainnet-deployer \
  --network mainnet \
  -- configure_reserve \
  --reserve_index "2"  # Adjust based on existing reserves
  --ltv_threshold "$LTV" \
  --liquidation_threshold "$LIQUIDATION_THRESHOLD" \
  --liquidation_bonus "$LIQUIDATION_BONUS" \
  --borrow_cap "100000000000"  # 100 BTC cap
  --supply_cap "200000000000"  # 200 BTC cap
  --reserve_factor "2000"  # 20% protocol share
```

**Verification:**

```bash
# Verify reserve registered
stellar contract invoke \
  --id kinetic_router \
  --network mainnet \
  -- get_reserves

# Verify price updating
stellar contract invoke \
  --id price_oracle \
  --network mainnet \
  -- get_price \
  --asset '{"asset_code": "BTC", "issuer": "'$ASSET_ISSUER'"}'

# Test supply (small amount)
stellar contract invoke \
  --id kinetic_router \
  --source testuser \
  --network mainnet \
  -- supply \
  --asset '{"asset_code": "BTC", "issuer": "'$ASSET_ISSUER'"}' \
  --amount "1000000"  # 0.1 BTC
```

---

## Upgrade Procedures

### Contract Upgrade Process

K2 supports contract upgrades via `upgrade_wasm_hash()`.

**Preconditions:**
- Only pool admin can call
- New WASM must be pre-installed
- Requires multi-sig approval (mainnet)

**Steps:**

```bash
# 1. Build new contract version
./deployment/build.sh

# 2. Verify new WASM hash
NEW_HASH=$(stellar contract install \
  --wasm target/wasm32v1-none/release/kinetic_router.optimized.wasm \
  --source k2-mainnet-deployer \
  --network mainnet 2>&1 | grep -i hash | awk '{print $NF}')

echo "New WASM hash: $NEW_HASH"

# 3. Get current WASM hash
CURRENT_HASH=$(stellar contract info \
  --id kinetic_router \
  --network mainnet | grep -i "hash" | awk '{print $NF}')

echo "Current WASM hash: $CURRENT_HASH"

# 4. Create upgrade proposal (multi-sig)
stellar contract invoke \
  --id k2_pool_admin_multisig \
  --source k2-mainnet-deployer \
  --network mainnet \
  -- propose \
  --target kinetic_router \
  --function "upgrade_wasm_hash" \
  --args '["'"$NEW_HASH"'"]'

# 5. Signers approve proposal
stellar contract invoke \
  --id k2_pool_admin_multisig \
  --source signer1 \
  --network mainnet \
  -- approve \
  --proposal_id "0"

stellar contract invoke \
  --id k2_pool_admin_multisig \
  --source signer2 \
  --network mainnet \
  -- approve \
  --proposal_id "0"

# (Repeat for threshold)

# 6. Wait for timelock (48 hours typical)
sleep 172800  # 48 hours in seconds

# 7. Execute upgrade
stellar contract invoke \
  --id k2_pool_admin_multisig \
  --source signer1 \
  --network mainnet \
  -- execute \
  --proposal_id "0"

# 8. Verify upgrade
stellar contract info \
  --id kinetic_router \
  --network mainnet | grep -i hash
# Should now show: $NEW_HASH
```

### Version Management

```bash
# Tag releases in git
git tag -a v1.0.0 -m "K2 Protocol mainnet launch"
git tag -a v1.0.1 -m "Security fixes"
git push origin --tags

# Keep version in Cargo.toml in sync
# [package]
# version = "1.0.0"
```

---

## Troubleshooting

### Common Issues and Solutions

#### Build Failures

**Problem:** `error: failed to compile contracts`

```bash
# Solution 1: Update Rust toolchain
rustup update
rustup target add wasm32-unknown-unknown

# Solution 2: Clean build
cargo clean
./deployment/build.sh

# Solution 3: Check dependencies
cargo tree | grep duplicate
cargo update
```

**Problem:** `stellar contract build: command not found`

```bash
# Solution: Reinstall stellar CLI
cargo install --force --locked stellar-cli

# Verify
stellar version
```

#### Deployment Failures

**Problem:** `Error: account does not have minimum balance`

```bash
# Solution: Fund the account
curl "https://friendbot.stellar.org?addr=$(stellar keys address k2-deployer)"

# Verify balance (need ~10 XLM)
stellar account info k2-deployer --network testnet
```

**Problem:** `Error: contract already deployed`

```bash
# Solution: Skip this contract and continue
# The script automatically detects deployed contracts

# Or force redeploy by removing from state:
jq 'del(.contracts.k2_kinetic_router)' deployments/testnet/state.json > tmp.json
mv tmp.json deployments/testnet/state.json
./deployment/deploy.sh --network testnet --skip-build
```

#### Initialization Failures

**Problem:** `Error: AlreadyInitialized`

```bash
# Solution: The contract was already initialized
# Verify current state:
stellar contract invoke --id kinetic_router --network testnet -- \
  get_pool_admin
# If returns valid address, initialization succeeded
```

**Problem:** `Error: InvalidOracle`

```bash
# Solution: Oracle not deployed yet
# Check deployment order:
stellar contract info --id price_oracle --network testnet
# If "not found", deploy oracle first

./deployment/deploy.sh --network testnet --skip-build
```

#### RPC/Network Issues

**Problem:** `Error: connection refused`

```bash
# Solution: Verify network configuration
stellar network show testnet

# Check RPC endpoint
curl https://soroban-testnet.stellar.org/health

# Or use alternative RPC if available
stellar network add testnet \
  --rpc-url "https://soroban-testnet.stellar.org" \
  --network-passphrase "Test SDF Network ; September 2015"
```

**Problem:** `Error: timeout waiting for transaction`

```bash
# Solution: Wait for confirmation (normal on busy networks)
sleep 10
stellar transaction info <TX_HASH> --network testnet

# Or increase timeout
stellar contract deploy \
  --wasm kinetic_router.optimized.wasm \
  --source k2-deployer \
  --network testnet \
  --timeout 60
```

---

## Files and Locations

### Key Directories

```
k2-contracts/
- contracts/                    # Contract source code
   kinetic-router/          # Core router
   a-token/                 # Supply token
   debt-token/              # Borrow token
   price-oracle/            # Price aggregator
   pool-configurator/       # Admin helper
   ...
  - deployment/                   # Deployment scripts
   build.sh                 # Build all contracts
   deploy.sh                # Deploy to network
   pre_deploy_check.sh      # Pre-deployment validation
   setup_multisig.sh        # Multi-sig setup
   config/                  # Network configurations
  - deployments/                 # Deployment state
   testnet/
     | state.json          # Current deployment state
      DEPLOYMENT_SUMMARY.md
   mainnet/
   state.json
   DEPLOYMENT_SUMMARY.md
  - target/                       # Build output
   wasm32v1-none/release/  # Compiled WASM files
   kinetic_router.wasm
   kinetic_router.optimized.wasm
   ...
  - docs/                        # Documentation
   02-ARCHITECTURE.md      # System architecture
   12-DEPLOYMENT.md        # This file
   ...
  - logs/                        # Deployment logs
- deploy_testnet_20250210_120000.log
```

### Important Files
  File | Purpose |
  ------|---------|
  `Cargo.toml` | Workspace configuration, dependencies |
  `Cargo.lock` | Lock file, exact versions |
  `rust-toolchain.toml` | Rust version pin |
  `deployment/build.sh` | Automated build and optimize |
  `deployment/deploy.sh` | Automated deployment |
  `deployments/{network}/state.json` | Deployment state tracker |

---

## References

- **Architecture Reference:** See [02-ARCHITECTURE.md](./02-ARCHITECTURE.md)
- **Admin Functions:** See [11-ADMIN.md](./11-ADMIN.md) (expected)
- **Security Considerations:** See [09-SECURITY.md](./09-SECURITY.md)
- **Soroban Documentation:** https://developers.stellar.org/learn/smart-contracts
- **Stellar CLI:** https://developers.stellar.org/tools/stellar-cli
