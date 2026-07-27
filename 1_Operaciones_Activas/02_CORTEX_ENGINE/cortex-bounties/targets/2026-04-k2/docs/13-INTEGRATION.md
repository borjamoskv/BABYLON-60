# 13. Integration Reference

Complete guide for developers integrating K2 into applications. Covers client bindings, contract interaction patterns, code examples, and best practices.

---

## 1. Overview

### Integration Approaches

K2 supports three integration paths:

#### **TypeScript/JavaScript Client SDK** (Recommended)
- Type-safe contract bindings
- Automatic parameter serialization
- Built-in error handling
- NPM package: `k2-contracts-client`

#### **Direct CLI Invocation**
- Manual contract calls via `stellar contract invoke`
- Useful for testing and scripting
- Full control over parameters
- No SDK dependency

#### **Soroban RPC Direct**
- Raw HTTP calls to Soroban RPC endpoint
- Manual parameter encoding
- For languages/platforms without SDK support

### Client Options

The K2 SDK provides pre-generated clients for all contracts:

```typescript
import {
  KineticRouter,      // Main protocol contract
  AToken,             // Interest-bearing token
  DebtToken,          // Borrow position token
  PriceOracle,        // Price feed oracle
  PoolConfigurator,   // Admin configuration
  InterestRateStrategy, // Rate calculation
  Treasury,           // Protocol reserves
  Incentives,         // Reward distribution
  LiquidationEngine,  // Internal helper (liquidation invoked via KineticRouter)
  FlashLiquidationHelper, // Flash liquidation prep
  Token,              // SEP-41 token standard
} from 'k2-contracts-client';
```

### Authentication Models

#### **User-Initiated**
User signs transaction authorizing their action:
```
User (signer)  -> approve amount  -> call function  -> authorization inherited
```

#### **Pool-Initiated**
Router validates authority via require_auth:
```
Router  -> verify caller signed tx  -> execute on behalf
```

---

## 2. TypeScript Client Bindings

### Package Installation

Install from npm:

```bash
npm install k2-contracts-client
```

Or with yarn:

```bash
yarn add k2-contracts-client
```

### Package Structure

```
k2-contracts-client/
- src/
   kinetic-router/      # Main protocol router
   a-token/             # aToken (supply token)
   debt-token/          # Debt token (borrow position)
   price-oracle/        # Oracle contract
   pool-configurator/   # Admin operations
   interest-rate-strategy/
   treasury/            # Protocol treasury
   incentives/          # Reward system
   liquidation-engine/  # Internal liquidation helper
   flash-liquidation-helper/
   token/               # Token standard
- dist/                    # Compiled JavaScript
```

### Available Types

Each client exports TypeScript interfaces for type safety:

```typescript
// Query results
export interface UserAccountData {
  health_factor: u128;
  total_collateral_base: u128;
  total_debt_base: u128;
  available_borrows_base: u128;
  current_liquidation_threshold: u128;
  ltv: u128;
}

// Reserve configuration
export interface ReserveData {
  liquidity_index: u128;
  variable_borrow_index: u128;
  current_liquidity_rate: u128;
  current_variable_borrow_rate: u128;
  last_update_timestamp: u64;
  a_token_address: Address;
  debt_token_address: Address;
  interest_rate_strategy_address: Address;
  id: u32;
  configuration: ReserveConfiguration;
}

// Events
export interface SupplyEvent {
  reserve: string;
  user: string;
  on_behalf_of: string;
  amount: u128;
  referral_code: u32;
}
```

---

## 3. Generating Bindings

### From WASM Specification

The SDK is pre-generated from contract WASM files. To regenerate:

```bash
# Install stellar-cli if not present
cargo install stellar-cli

# Generate TypeScript bindings from contract WASM
stellar contract bindings typescript \
  --wasm /path/to/contract.wasm \
  --output-dir src/kinetic-router \
  --package-name k2-contracts-client
```

### Contract WASM Locations

Each contract compiles to:

```bash
contracts/kinetic-router/target/wasm32-unknown-unknown/release/kinetic_router.wasm
contracts/a-token/target/wasm32-unknown-unknown/release/a_token.wasm
contracts/debt-token/target/wasm32-unknown-unknown/release/debt_token.wasm
# ... etc for all contracts
```

### Build All Contracts

```bash
# Build all contracts in release mode
cd k2-contracts
cargo build --release --target wasm32-unknown-unknown

# This creates WASM files for binding generation
```

---

## 4. Using TypeScript Clients

### Basic Client Setup

```typescript
import { KineticRouter } from 'k2-contracts-client';
import { Keypair } from '@stellar/stellar-sdk';

// Create client with contract ID and RPC endpoint
const client = new KineticRouter.Client({
  contractId: 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',

  // Optional: provide signer for transactions
  publicKey: keypair.publicKey(),
});

// For state-changing operations, provide signer
const signerClient = new KineticRouter.Client({
  contractId: 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
  publicKey: keypair.publicKey(),
  secretKey: keypair.secret(), // Required for signing
});
```

### Connection Configuration

```typescript
// Testnet
const testnetConfig = {
  contractId: 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
};

// Mainnet (when available)
const mainnetConfig = {
  contractId: 'CABC...', // Mainnet contract ID TBD
  networkPassphrase: 'Public Global Stellar Network ; September 2015',
  rpcUrl: 'https://soroban-mainnet.stellar.org',
};

// Local Soroban
const localConfig = {
  contractId: 'CABC...',
  networkPassphrase: 'Standalone Network ; February 2017',
  rpcUrl: 'http://localhost:8000/soroban/rpc',
};
```

### Error Handling

```typescript
import { KineticRouter } from 'k2-contracts-client';

try {
  const tx = await client.supply({
    caller: userAddress,
    asset: usdcAddress,
    amount: new BigNumber(1000).times(1e6), // 1000 USDC with 6 decimals
    on_behalf_of: userAddress,
    referral_code: 0,
  });

  const result = await tx.signAndSend();
  console.log('Success:', result);
} catch (error) {
  if (error.code === 7) {
    console.error('InsufficientCollateral');
  } else if (error.code === 8) {
    console.error('HealthFactorTooLow');
  } else {
    console.error('Unknown error:', error.message);
  }
}
```

---

## 5. Available Contract Clients

### KineticRouter

Main protocol entry point for all user operations:

```typescript
import { KineticRouter } from 'k2-contracts-client';

// Core user operations
client.supply()           // Deposit assets
client.withdraw()         // Redeem aTokens
client.borrow()           // Borrow against collateral
client.repay()            // Repay debt
client.liquidation_call() // Standard liquidation
client.prepare_liquidation() // Two-step liquidation prep
client.execute_liquidation() // Two-step liquidation exec
client.flash_loan()       // Flash loan
client.swap_collateral()  // Swap collateral positions

// View functions (read-only)
client.get_user_account_data()  // Query user position
client.get_reserve_data()       // Query reserve state
client.get_current_liquidity_index() // Query supply index
client.get_current_var_borrow_idx() // Query borrow index

// Admin operations
client.initialize()       // Initialize pool
client.update_reserve_configuration()  // Update reserve bitmap (LTV, threshold, pause, freeze, etc.)
client.set_reserve_supply_cap() // Set supply cap
client.set_reserve_borrow_cap() // Set borrow cap
```

### AToken

Interest-bearing token for supplied assets:

```typescript
import { AToken } from 'k2-contracts-client';

const aTokenClient = new AToken.Client({
  contractId: aTokenAddress,
  // ... other config
});

// Token operations
aTokenClient.transfer()    // Transfer aToken
aTokenClient.approve()     // Approve spending
aTokenClient.balance_of()  // Query balance
aTokenClient.total_supply() // Query total supply
```

### DebtToken

Non-transferable token representing debt:

```typescript
import { DebtToken } from 'k2-contracts-client';

const debtClient = new DebtToken.Client({
  contractId: debtTokenAddress,
  // ... other config
});

// Read-only operations (debt token is non-transferable)
debtClient.balance_of()    // Query debt balance
debtClient.total_supply()  // Query total debt
```

### PriceOracle

Price feed oracle for asset valuations:

```typescript
import { PriceOracle } from 'k2-contracts-client';

const oracleClient = new PriceOracle.Client({
  contractId: oracleAddress,
  // ... other config
});

// Query prices
oracleClient.price_by_address() // Get price for Stellar asset
oracleClient.price()            // Get price with precision conversion
oracleClient.get_price_source()  // Query price source config

// Admin operations (requires authority)
oracleClient.set_price_source()  // Configure price source
oracleClient.set_price()         // Manual price override
```

### Other Contracts

Similar pattern for all contracts:

```typescript
import {
  PoolConfigurator,
  InterestRateStrategy,
  Treasury,
  Incentives,
  LiquidationEngine,  // Internal; liquidation via KineticRouter
  FlashLiquidationHelper,
  Token, // Standard SEP-41 token
} from 'k2-contracts-client';

const poolConfig = new PoolConfigurator.Client({ /* ... */ });
const strategy = new InterestRateStrategy.Client({ /* ... */ });
const treasury = new Treasury.Client({ /* ... */ });
const incentives = new Incentives.Client({ /* ... */ });
const liquidation = new LiquidationEngine.Client({ /* ... */ }); // Internal helper — not for direct liquidation calls
const flashHelper = new FlashLiquidationHelper.Client({ /* ... */ });
const token = new Token.Client({ /* ... */ });
```

---

## 6. Initialization

### Create Client Instances

Single-line client creation:

```typescript
import { KineticRouter, AToken } from 'k2-contracts-client';

const router = new KineticRouter.Client({
  contractId: 'CAR253KW...',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
  publicKey: keypair.publicKey(),
});

const aToken = new AToken.Client({
  contractId: 'CABC....',
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
});
```

### Configuration Management

Centralize contract IDs and configuration:

```typescript
// contracts.ts
export const K2_CONTRACTS = {
  testnet: {
    router: 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK',
    usdc: 'CA...',
    eth: 'CA...',
    btc: 'CA...',
    oracle: 'CA...',
    treasury: 'CA...',
  },
  mainnet: {
    router: 'CA...', // TBD
    usdc: 'CA...',
    // ...
  },
};

export const NETWORK_CONFIG = {
  testnet: {
    passphrase: 'Test SDF Network ; September 2015',
    rpcUrl: 'https://soroban-testnet.stellar.org',
  },
  mainnet: {
    passphrase: 'Public Global Stellar Network ; September 2015',
    rpcUrl: 'https://soroban-mainnet.stellar.org',
  },
};

// Create helper
export function createClient(network: 'testnet' | 'mainnet', keypair?: Keypair) {
  const config = NETWORK_CONFIG[network];
  const contracts = K2_CONTRACTS[network];

  return {
    router: new KineticRouter.Client({
      contractId: contracts.router,
      networkPassphrase: config.passphrase,
      rpcUrl: config.rpcUrl,
      publicKey: keypair?.publicKey(),
    }),
    // ... other clients
  };
}
```

### Environment-Based Selection

```typescript
const network = process.env.NETWORK || 'testnet';
const clients = createClient(network as 'testnet' | 'mainnet', keypair);
```

---

## 7. Calling Contract Functions

### Synchronous Queries (View Functions)

Read-only operations that don't change state:

```typescript
// Query user position
const accountData = await client.get_user_account_data({
  user: userAddress,
});

console.log('Health Factor:', accountData.health_factor);
console.log('Collateral:', accountData.total_collateral_base);
console.log('Debt:', accountData.total_debt_base);

// Query reserve state
const reserveData = await client.get_reserve_data({
  asset: usdcAddress,
});

console.log('Liquidity Index:', reserveData.liquidity_index);
console.log('Borrow Index:', reserveData.variable_borrow_index);
```

### Asynchronous Invocations (State-Changing Functions)

Operations that modify contract state:

```typescript
// Construct transaction
const supplyTx = await client.supply({
  caller: userAddress,
  asset: usdcAddress,
  amount: new BigNumber('1000000000'), // 1000 USDC with 6 decimals
  on_behalf_of: userAddress,
  referral_code: 0,
});

// The transaction is prepared but not yet sent
console.log('Transaction envelope:', supplyTx.toEnvelope());

// Sign and submit
const result = await supplyTx.signAndSend();
console.log('Hash:', result.hash);
console.log('Status:', result.status); // 'success' or 'failure'
```

### Parameter Handling

All amounts must use proper precision:

```typescript
import BigNumber from 'bignumber.js';

// Amount in smallest units (e.g., micro-units for USDC with 6 decimals)
const amountUSdc = new BigNumber('1000').times(1e6); // 1000 USDC

// Prices from oracle are in basis points * 1e14 (Oracle precision)
const priceUsdToWad = (priceInUsd: BigNumber): BigNumber => {
  return priceInUsd.times(1e14); // Convert to oracle precision
};

// Health factor, collateral, and debt are in WAD (1e18)
const wadValue = new BigNumber('100').times(1e18); // 100 WAD
```

### Error Handling in Calls

```typescript
try {
  const result = await client.supply({
    caller: userAddress,
    asset: usdcAddress,
    amount: amountUsdc,
    on_behalf_of: userAddress,
    referral_code: 0,
  });

  const sendResult = await result.signAndSend();

  if (sendResult.status === 'failure') {
    // Check error code
    const errorCode = sendResult.error?.code;
    if (errorCode === 19) {
      throw new Error('Supply cap exceeded');
    }
  }
} catch (error) {
  console.error('Transaction failed:', error);
  // Handle specific error codes
  if (error.message.includes('InsufficientBalance')) {
    // User lacks funds
  } else if (error.message.includes('HealthFactorTooLow')) {
    // Would violate health factor
  }
}
```

---

## 8. Type Safety

### TypeScript Interfaces

All contract operations and data structures have full TypeScript definitions:

```typescript
// Strongly typed parameters
function supplyAsset(
  amount: u128,
  asset: Address,
  user: Address
): Promise<AssembledTransaction> {
  return client.supply({
    caller: user,      // string (Address)
    asset: asset,      // string (Address)
    amount: amount,    // u128 (BigNumber or numeric)
    on_behalf_of: user, // string (Address)
    referral_code: 0,  // u32
  });
}

// Strongly typed results
const data: UserAccountData = await client.get_user_account_data({
  user: userAddress,
});

// TypeScript ensures:
data.health_factor;           //  Exists, type u128
data.nonexistent_field;       //  Compilation error
```

### Working with Numeric Types

K2 uses specialized numeric types:

```typescript
// u128: 128-bit unsigned integer (prices, amounts, indices)
import { u128 } from 'k2-contracts-client';
let amount: u128 = 1000000000;

// u64: 64-bit unsigned (timestamps)
let timestamp: u64 = Math.floor(Date.now() / 1000);

// u32: 32-bit unsigned (reserve ID, basis points)
let reserveId: u32 = 0;
let basisPoints: u32 = 5000; // 50%

// Addresses are strings
let address: string = 'GA...';

// Results are wrapped
interface Result<T> {
  tag: 'Ok' | 'Err';
  values: [T] | [{ code: number; message: string }];
}
```

### Autocomplete Support

IDEs with TypeScript support provide:

```typescript
client.
  // Autocomplete lists all available methods:
  // - supply
  // - withdraw
  // - borrow
  // - repay
  // - liquidation_call
  // - prepare_liquidation
  // - execute_liquidation
  // - flash_loan
  // - swap_collateral
  // - get_user_account_data
  // - get_reserve_data
  // - ... (all contract methods)
```

---

## 9. Result Handling

### Success Results

```typescript
const supplyTx = await client.supply({
  caller: userAddress,
  asset: usdcAddress,
  amount: new BigNumber('1000000000'),
  on_behalf_of: userAddress,
  referral_code: 0,
});

const result = await supplyTx.signAndSend();

if (result.status === 'success') {
  console.log('Supplied successfully!');
  console.log('Transaction hash:', result.hash);
  console.log('Ledger sequence:', result.ledger);
}
```

### Error Code Mapping

Reference all error codes:

```typescript
// KineticRouter errors
const KINETIC_ERRORS = {
  1: 'InvalidAmount',
  2: 'AssetNotActive',
  3: 'AssetFrozen',
  4: 'AssetPaused',
  5: 'BorrowingNotEnabled',
  7: 'InsufficientCollateral',
  8: 'HealthFactorTooLow',
  10: 'PriceOracleNotFound',
  11: 'InvalidLiquidation',
  12: 'LiquidationAmountTooHigh',
  13: 'NoDebtOfRequestedType',
  14: 'InvalidFlashLoanParams',
  15: 'FlashLoanNotAuthorized',
  19: 'SupplyCapExceeded',
  20: 'BorrowCapExceeded',
  24: 'ReserveNotFound',
  26: 'Unauthorized',
  37: 'MathOverflow',
  38: 'Expired',
};

// Price Oracle errors
const ORACLE_ERRORS = {
  1: 'AssetPriceNotFound',
  2: 'PriceSourceNotSet',
  4: 'PriceTooOld',
  7: 'AssetNotWhitelisted',
};
```

### Parsing Error Messages

```typescript
try {
  await supplyTx.signAndSend();
} catch (error) {
  // Extract error code
  const errorMatch = error.message.match(/Error #(\d+)/);
  if (errorMatch) {
    const code = parseInt(errorMatch[1]);
    const message = KINETIC_ERRORS[code] || 'Unknown error';
    console.error(`Error: ${message} (code #${code})`);
  } else {
    console.error('Network or parsing error:', error.message);
  }
}
```

### Common Result Patterns

```typescript
// Pattern 1: Check status before using result
const tx = await client.supply({/* ... */});
const result = await tx.signAndSend();

if (result.status === 'success') {
  // Use result.ledger, result.hash
} else {
  // Check result.error for details
}

// Pattern 2: Throw on error
async function supplyWithErrorHandling(
  amount: BigNumber,
  asset: Address
): Promise<string> {
  const tx = await client.supply({/* ... */});
  const result = await tx.signAndSend();

  if (result.status !== 'success') {
    throw new Error(`Supply failed: ${result.error?.message}`);
  }

  return result.hash;
}

// Pattern 3: Retry with backoff
async function supplyWithRetry(
  amount: BigNumber,
  maxRetries: number = 3
): Promise<string> {
  for (let i = 0; i < maxRetries; i++) {
    try {
      return await supplyWithErrorHandling(amount, asset);
    } catch (error) {
      if (i < maxRetries - 1) {
        await delay(Math.pow(2, i) * 1000); // Exponential backoff
      } else {
        throw error;
      }
    }
  }
  throw new Error('Max retries exceeded');
}
```

---

## 10. Direct CLI Integration

### Stellar CLI for Manual Testing

Install Stellar CLI:

```bash
cargo install stellar-cli
```

### Invoke Without Signer

Query view functions (read-only):

```bash
stellar contract invoke \
  --id CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK \
  --rpc-url https://soroban-testnet.stellar.org \
  --network testnet \
  -- \
  get_user_account_data \
  --user GA7QSTOFYBKSIRT5POAOYHHQJG74WJ5L3CFSOHWGHNHV5FASNQWWIUCM
```

### Invoke With Signer

State-changing operations require authorization:

```bash
stellar contract invoke \
  --id CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK \
  --rpc-url https://soroban-testnet.stellar.org \
  --network testnet \
  --secret-key SA... \
  -- \
  supply \
  --caller GA... \
  --asset CA... \
  --amount 1000000000 \
  --on_behalf_of GA... \
  --referral_code 0
```

### Simulating Transactions

Preview transaction cost without sending:

```bash
stellar contract invoke \
  --id CAR253KW... \
  --rpc-url https://soroban-testnet.stellar.org \
  --network testnet \
  -- \
  get_reserve_data \
  --asset CA... \
  --simulate
```

### Parsing CLI Output

CLI returns JSON result:

```bash
# Output includes:
# - "result": Actual value
# - "cost": CPU and memory cost
# - "restore": Ledger restore operations needed

stellar contract invoke ... | jq '.result'
```

---

## 11. View Functions (Read-Only Queries)

### User Account Data

Query complete user position:

```typescript
const data = await client.get_user_account_data({
  user: userAddress,
});

// Returns:
// - health_factor: HF in WAD (1e18), >1.0 = healthy
// - total_collateral_base: Supplied value in base currency (WAD)
// - total_debt_base: Owed value in base currency (WAD)
// - available_borrows_base: Remaining borrowing capacity (WAD)
// - current_liquidation_threshold: Weighted threshold (basis points)
// - ltv: Weighted LTV (basis points)

console.log(`Health Factor: ${data.health_factor / 1e18}`);
console.log(`Liquidation Risk: ${data.health_factor < 1e18 ? 'HIGH' : 'OK'}`);
```

### Reserve Data

Query reserve state and configuration:

```typescript
const reserve = await client.get_reserve_data({
  asset: usdcAddress,
});

// Returns:
// - liquidity_index: Supply index (RAY, 1e27)
// - variable_borrow_index: Borrow index (RAY)
// - current_liquidity_rate: Supply APY (RAY/year)
// - current_variable_borrow_rate: Borrow APY (RAY/year)
// - last_update_timestamp: Last interest accrual
// - a_token_address: aToken contract for this reserve
// - debt_token_address: Debt token contract
// - interest_rate_strategy_address: Rate model contract
// - id: Reserve index (0-63)
// - configuration: Bitmap with LTV, thresholds, flags

const supplyApy = reserve.current_liquidity_rate / 1e27; // Convert RAY to decimal
const borrowApy = reserve.current_variable_borrow_rate / 1e27;

console.log(`Supply APY: ${(supplyApy * 100).toFixed(2)}%`);
console.log(`Borrow APY: ${(borrowApy * 100).toFixed(2)}%`);
```

### Current Indices

Query latest cumulative indices:

```typescript
const liquidityIndex = await client.get_current_liquidity_index({
  asset: usdcAddress,
});

const borrowIndex = await client.get_current_var_borrow_idx({
  asset: usdcAddress,
});

// Use indices to convert scaled balances to actual amounts:
// actual_supply = scaled_supply_balance * liquidity_index
// actual_debt = scaled_debt_balance * borrow_index
```

### Reserve Configuration

Query bitpacked configuration:

```typescript
const reserveData = await client.get_reserve_data({
  asset: usdcAddress,
});
const config = reserveData.configuration;

// Configuration is bitpacked, use helper functions to extract:
// - ltv: Loan-to-value ratio (basis points)
// - liquidation_threshold: Liquidation threshold (basis points)
// - liquidation_bonus: Liquidation bonus (basis points)
// - decimals: Token decimals
// - active: Is reserve active
// - frozen: Is reserve frozen
// - borrowing_enabled: Can borrow this asset
// - flash_loan_enabled: Can flash loan this asset
```

---

## 12. Invoke Functions (State-Changing)

### Authorization Model

All state-changing calls require the user to sign:

```typescript
// TypeScript SDK handles signing transparently
const tx = await client.supply({
  caller: userAddress,        // User who signs tx
  asset: usdcAddress,         // Asset being supplied
  amount: amountInSmallestUnits,
  on_behalf_of: userAddress,  // Position created for this user
  referral_code: 0,           // Optional referral tracking
});

const result = await tx.signAndSend();
```

### Transaction Lifecycle

```
1. Call contract method (client.supply())
    Returns AssembledTransaction

2. Optional: Modify transaction
    Add custom fee, memo, etc.

3. Sign transaction
    User's signature added to envelope

4. Send to RPC
    Soroban validates and executes

5. Wait for ledger close
    Transaction confirmed or rejected
```

### Tracking Pending Operations

```typescript
const transactions = new Map<string, TransactionStatus>();

async function supplyWithTracking(
  amount: BigNumber,
  asset: Address
): Promise<string> {
  const tx = await client.supply({/* ... */});
  const hash = tx.hash;

  transactions.set(hash, { status: 'pending', createdAt: Date.now() });

  const result = await tx.signAndSend();
  transactions.set(hash, {
    status: result.status === 'success' ? 'confirmed' : 'failed',
    ledger: result.ledger,
    error: result.error?.message,
  });

  return hash;
}

// Query pending
function getPendingTransactions(): string[] {
  return Array.from(transactions.entries())
    .filter(([_, status]) => status.status === 'pending')
    .map(([hash]) => hash);
}
```

---

## 13. Authentication

### User Signing

User must sign transaction via wallet:

```typescript
import { Keypair } from '@stellar/stellar-sdk';

// User provides keypair (from wallet, local storage, etc.)
const userKeypair = Keypair.fromSecret('SA...');

// Client needs public key for address
const userAddress = userKeypair.publicKey();

// Client uses keypair to sign transactions
const client = new KineticRouter.Client({
  contractId: routerAddress,
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
  publicKey: userKeypair.publicKey(),
});

// Transaction is signed automatically
const tx = await client.supply({
  caller: userAddress,
  // ...
});
```

### Wallet Integration (Recommended for Frontends)

Never ask users for private keys. Use wallet extensions:

```typescript
import { signTransaction } from '@stellar/freighter-api';

// Get user's public key from wallet
const publicKey = await window.stellar.getPublicKey();

// Create transaction
const tx = await client.supply({
  caller: publicKey,
  // ...
});

// Ask wallet to sign
const signedTx = await signTransaction(
  tx.toEnvelope(),
  'Test SDF Network ; September 2015'
);

// Submit signed transaction
const result = await client.rpc.submitTransaction(signedTx);
```

### Authorization Tree

Soroban validates authorization once per transaction:

```
Transaction Signature
  [DOWN]
Verify caller signed
  [DOWN]
Authorize all called contracts with (caller, function_name)
  [DOWN]
Contracts can now require_auth(caller) without re-signing
```

---

## 14. Supply/Deposit Flow

**Goal**: Deposit USDC and receive aUSDC (interest-bearing token)

### Step 1: Approve Token Transfer

User must authorize router to spend tokens:

```typescript
const usdcToken = new Token.Client({
  contractId: usdcAddress,
  networkPassphrase,
  rpcUrl,
  publicKey: userKeypair.publicKey(),
});

// Approve supply amount to router
const approveTx = await usdcToken.approve({
  from: userAddress,
  spender: routerAddress,
  amount: supplyAmount,
  expiration_ledger: ledgerSeq + 10000,
});

const approveResult = await approveTx.signAndSend();
console.log('Approval confirmed:', approveResult.hash);
```

### Step 2: Supply Assets

Call router's supply function:

```typescript
const router = new KineticRouter.Client({
  contractId: routerAddress,
  networkPassphrase,
  rpcUrl,
  publicKey: userKeypair.publicKey(),
});

const supplyTx = await router.supply({
  caller: userAddress,
  asset: usdcAddress,
  amount: new BigNumber('1000000000'), // 1000 USDC (6 decimals)
  on_behalf_of: userAddress,           // Position for user
  referral_code: 0,
});

const supplyResult = await supplyTx.signAndSend();
console.log('Supply confirmed:', supplyResult.hash);
```

### Step 3: Verify Position

Query aToken balance:

```typescript
const aTokenAddress = (await router.get_reserve_data({
  asset: usdcAddress,
})).a_token_address;

const aToken = new AToken.Client({
  contractId: aTokenAddress,
  networkPassphrase,
  rpcUrl,
});

const aTokenBalance = await aToken.balance_of({
  id: userAddress,
});

console.log('Supplied amount (aUSDC):', aTokenBalance.toString());
```

### Complete Example

```typescript
import { Token, KineticRouter, AToken } from 'k2-contracts-client';
import BigNumber from 'bignumber.js';

async function depositAsset(
  amount: number,
  assetAddress: string,
  userAddress: string,
  keypair: Keypair
): Promise<string> {
  const networkPassphrase = 'Test SDF Network ; September 2015';
  const rpcUrl = 'https://soroban-testnet.stellar.org';
  const routerAddress = 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK';

  // Step 1: Approve
  console.log(`Approving ${amount} tokens...`);
  const tokenClient = new Token.Client({
    contractId: assetAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: keypair.publicKey(),
  });

  const amountSmallest = new BigNumber(amount).times(1e6);
  const approveTx = await tokenClient.approve({
    from: userAddress,
    spender: routerAddress,
    amount: amountSmallest,
    expiration_ledger: Math.floor(Date.now() / 1000) + 600,
  });

  await approveTx.signAndSend();
  console.log(' Approval confirmed');

  // Step 2: Supply
  console.log(`Supplying ${amount} tokens...`);
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: keypair.publicKey(),
  });

  const supplyTx = await router.supply({
    caller: userAddress,
    asset: assetAddress,
    amount: amountSmallest,
    on_behalf_of: userAddress,
    referral_code: 0,
  });

  const supplyResult = await supplyTx.signAndSend();
  console.log(' Supply confirmed:', supplyResult.hash);

  // Step 3: Verify
  const reserveData = await router.get_reserve_data({
    asset: assetAddress,
  });

  const aToken = new AToken.Client({
    contractId: reserveData.a_token_address,
    networkPassphrase,
    rpcUrl,
  });

  const aTokenBal = await aToken.balance_of({
    id: userAddress,
  });

  console.log(` Position verified: ${new BigNumber(aTokenBal.toString()).div(1e6).toFixed(6)} aTokens`);

  return supplyResult.hash;
}
```

---

## 15. Borrow Flow

**Goal**: Borrow USDC against ETH collateral

### Prerequisites

- User must have supplied collateral (e.g., ETH)
- Collateral must have borrowing enabled
- Health factor must remain > 1.0

### Step 1: Check Borrowing Capacity

Query account data to verify available capacity:

```typescript
const accountData = await router.get_user_account_data({
  user: userAddress,
});

// Available borrow = total collateral * weighted LTV - debt
const availableBorrow = accountData.available_borrows_base;

// Check health factor
if (accountData.health_factor < new BigNumber('1').times(1e18)) {
  throw new Error('Not enough collateral');
}

console.log(`Available to borrow: ${availableBorrow.toString()} base currency`);
console.log(`Health factor: ${accountData.health_factor.div(1e18)}`);
```

### Step 2: Call Borrow Function

```typescript
const borrowTx = await router.borrow({
  caller: userAddress,
  asset: usdcAddress,
  amount: new BigNumber('100000000'), // 100 USDC
  interest_rate_mode: 2,              // Variable rate
  referral_code: 0,
  on_behalf_of: userAddress,
});

const borrowResult = await borrowTx.signAndSend();
console.log('Borrow confirmed:', borrowResult.hash);
```

### Step 3: Verify Debt Position

```typescript
const reserveData = await router.get_reserve_data({
  asset: usdcAddress,
});

const debtToken = new DebtToken.Client({
  contractId: reserveData.debt_token_address,
  networkPassphrase,
  rpcUrl,
});

const debtBalance = await debtToken.balance_of({
  id: userAddress,
});

console.log('Debt balance:', debtBalance.toString());

// Query updated account data
const updatedData = await router.get_user_account_data({
  user: userAddress,
});

console.log(`New HF: ${updatedData.health_factor.div(1e18)}`);
```

### Complete Example

```typescript
async function borrowAgainstCollateral(
  borrowAmount: number,
  borrowAsset: string,
  collateralAsset: string,
  userAddress: string,
  keypair: Keypair
): Promise<string> {
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: keypair.publicKey(),
  });

  // Check capacity
  const before = await router.get_user_account_data({ user: userAddress });
  console.log(`Before - HF: ${before.health_factor.div(1e18)}, Available: ${before.available_borrows_base.toString()}`);

  // Borrow
  const amount = new BigNumber(borrowAmount).times(1e6); // 6 decimals
  const borrowTx = await router.borrow({
    caller: userAddress,
    asset: borrowAsset,
    amount,
    interest_rate_mode: 2,
    referral_code: 0,
    on_behalf_of: userAddress,
  });

  const result = await borrowTx.signAndSend();
  console.log(' Borrow confirmed:', result.hash);

  // Verify
  const after = await router.get_user_account_data({ user: userAddress });
  console.log(`After - HF: ${after.health_factor.div(1e18)}, Debt: ${after.total_debt_base.toString()}`);

  return result.hash;
}
```

---

## 16. Repay Flow

**Goal**: Repay borrowed USDC debt

### Step 1: Approve Repayment Amount

```typescript
const tokenClient = new Token.Client({
  contractId: usdcAddress,
  networkPassphrase,
  rpcUrl,
  publicKey: keypair.publicKey(),
});

const repayAmount = new BigNumber('100000000'); // 100 USDC

const approveTx = await tokenClient.approve({
  from: userAddress,
  spender: routerAddress,
  amount: repayAmount,
  expiration_ledger: ledgerSeq + 10000,
});

await approveTx.signAndSend();
console.log('Repay approval confirmed');
```

### Step 2: Call Repay Function

```typescript
const repayTx = await router.repay({
  caller: userAddress,
  asset: usdcAddress,
  amount: repayAmount,        // Actual amount to repay (includes accrued interest)
  rate_mode: 2,               // Match original borrow rate mode
  on_behalf_of: userAddress,  // Debt position to reduce
});

const repayResult = await repayTx.signAndSend();
console.log('Repay confirmed:', repayResult.hash);
```

### Step 3: Verify Debt Reduction

```typescript
const accountDataAfter = await router.get_user_account_data({
  user: userAddress,
});

console.log(`Remaining debt: ${accountDataAfter.total_debt_base.toString()}`);
console.log(`Updated HF: ${accountDataAfter.health_factor.div(1e18)}`);
```

### Complete Example

```typescript
async function repayDebt(
  repayAmount: number,
  borrowAsset: string,
  userAddress: string,
  keypair: Keypair
): Promise<string> {
  const tokenClient = new Token.Client({
    contractId: borrowAsset,
    networkPassphrase,
    rpcUrl,
    publicKey: keypair.publicKey(),
  });

  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: keypair.publicKey(),
  });

  // Query current debt
  const before = await router.get_user_account_data({ user: userAddress });
  console.log(`Debt before: ${before.total_debt_base.toString()}`);

  // Approve repayment
  const amount = new BigNumber(repayAmount).times(1e6);
  const approveTx = await tokenClient.approve({
    from: userAddress,
    spender: routerAddress,
    amount,
    expiration_ledger: ledgerSeq + 10000,
  });
  await approveTx.signAndSend();

  // Repay
  const repayTx = await router.repay({
    caller: userAddress,
    asset: borrowAsset,
    amount,
    rate_mode: 2,
    on_behalf_of: userAddress,
  });

  const result = await repayTx.signAndSend();
  console.log(' Repay confirmed:', result.hash);

  // Verify
  const after = await router.get_user_account_data({ user: userAddress });
  console.log(`Debt after: ${after.total_debt_base.toString()}`);
  console.log(`New HF: ${after.health_factor.div(1e18)}`);

  return result.hash;
}
```

---

## 17. Withdraw Flow

**Goal**: Redeem aTokens for underlying asset + accrued interest

### Step 1: Verify Available Liquidity

```typescript
const reserveData = await router.get_reserve_data({
  asset: usdcAddress,
});

const aToken = new AToken.Client({
  contractId: reserveData.a_token_address,
  networkPassphrase,
  rpcUrl,
});

const aTokenBalance = await aToken.balance_of({
  id: userAddress,
});

// Actual balance = scaled balance * current index
const actualBalance = new BigNumber(aTokenBalance.toString())
  .times(reserveData.liquidity_index)
  .div(1e27);

console.log(`Can withdraw: ${actualBalance.div(1e6).toFixed(6)} USDC`);
```

### Step 2: Call Withdraw Function

```typescript
const withdrawTx = await router.withdraw({
  caller: userAddress,
  asset: usdcAddress,
  amount: new BigNumber('100000000'), // Withdraw 100 USDC
  to: userAddress,                    // Receive tokens here
});

const withdrawResult = await withdrawTx.signAndSend();
console.log('Withdraw confirmed:', withdrawResult.hash);
```

### Step 3: Verify Withdrawn Funds

```typescript
const tokenBalance = await new Token.Client({
  contractId: usdcAddress,
  networkPassphrase,
  rpcUrl,
}).balance_of({
  id: userAddress,
});

console.log('Received:', tokenBalance.toString());
```

### Important: Health Factor Check

Withdraw reduces collateral, so health factor may drop:

```typescript
const before = await router.get_user_account_data({ user: userAddress });
console.log(`HF before: ${before.health_factor.div(1e18)}`);

await withdrawTx.signAndSend();

const after = await router.get_user_account_data({ user: userAddress });
if (after.health_factor < new BigNumber('1').times(1e18)) {
  throw new Error('Withdraw would make position unhealthy');
}
console.log(`HF after: ${after.health_factor.div(1e18)}`);
```

---

## 18. Liquidation Flow

### Standard Liquidation (Single-Step)

**Goal**: Liquidate unhealthy position by selling collateral, repaying debt

#### Step 1: Find Liquidation Target

```typescript
// Monitor user health factors
async function findLiquidationTarget(
  users: string[]
): Promise<{ user: string; hf: BigNumber } | null> {
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
  });

  for (const user of users) {
    const data = await router.get_user_account_data({ user });
    if (data.health_factor < new BigNumber('1').times(1e18)) {
      return { user, hf: data.health_factor };
    }
  }

  return null;
}

const target = await findLiquidationTarget(activeUsers);
if (!target) {
  console.log('No liquidation targets');
  process.exit(0);
}

console.log(`Found target: ${target.user} (HF: ${target.hf.div(1e18)})`);
```

#### Step 2: Calculate Liquidation Amount

```typescript
// Close factor = 50% (fixed in protocol)
const closeFactor = new BigNumber('0.5');

// Get user position
const accountData = await router.get_user_account_data({
  user: targetUser,
});

// Amount to repay = min(debt_to_cover, user_debt * close_factor)
const maxRepay = accountData.total_debt_base.times(closeFactor);

// Get asset prices
const debtPrice = await oracle.price_by_address({
  asset: debtAsset,
});

const collateralPrice = await oracle.price_by_address({
  asset: collateralAsset,
});

// Amount of collateral to seize = (repay * debt_price / collateral_price) * (1 + bonus)
const liquidationBonus = new BigNumber('0.05'); // 5%
const collateralToSeize = maxRepay
  .times(debtPrice)
  .div(collateralPrice)
  .times(1 + liquidationBonus);

console.log(`Repay: ${maxRepay.toString()}, Seize: ${collateralToSeize.toString()}`);
```

#### Step 3: Approve and Liquidate

```typescript
// Approve debt token amount to repay
const debtToken = new Token.Client({
  contractId: debtAsset,
  networkPassphrase,
  rpcUrl,
  publicKey: liquidatorKeypair.publicKey(),
});

const approveTx = await debtToken.approve({
  from: liquidatorAddress,
  spender: routerAddress,
  amount: maxRepay,
  expiration_ledger: ledgerSeq + 10000,
});

await approveTx.signAndSend();

// Execute liquidation
const liquidateTx = await router.liquidation_call({
  caller: liquidatorAddress,
  collateral: collateralAsset,
  debt_asset: debtAsset,
  user: targetUser,
  debt_to_cover: maxRepay,
  receive_a_token: false,
});

const result = await liquidateTx.signAndSend();
console.log('Liquidation confirmed:', result.hash);
```

### Two-Step Flash Liquidation

**For large positions** that exceed CPU limit in single step:

#### Phase 1: Prepare Liquidation

```typescript
const prepareTx = await router.prepare_liquidation({
  caller: liquidatorAddress,
  collateral: collateralAsset,
  collateral_price: collateralPriceWad,
  debt_asset: debtAsset,
  debt_price: debtPriceWad,
  user: targetUser,
  user_debt: userDebtBalance,
  close_factor: 5000, // 50%
  nonce: 0,
});

const prepareResult = await prepareTx.signAndSend();
const authorization = prepareResult.result; // LiquidationAuthorization struct
console.log('Prepare phase confirmed');
```

#### Phase 2: Execute Liquidation

```typescript
const executeTx = await router.execute_liquidation({
  caller: liquidatorAddress,
  debt_asset: debtAsset,
  authorization: authorization, // From step 1
  swap_handler: swapHandlerAddress, // DEX adapter
});

const executeResult = await executeTx.signAndSend();
console.log('Execute phase confirmed:', executeResult.hash);
```

### Complete Liquidation Bot Example

```typescript
async function liquidatePosition(
  targetUser: string,
  liquidatorKeypair: Keypair,
  flashLiquidation: boolean = false
): Promise<string> {
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: liquidatorKeypair.publicKey(),
  });

  const oracle = new PriceOracle.Client({
    contractId: oracleAddress,
    networkPassphrase,
    rpcUrl,
  });

  // 1. Check health factor
  const data = await router.get_user_account_data({ user: targetUser });
  if (data.health_factor >= new BigNumber('1').times(1e18)) {
    throw new Error('Position is not liquidatable');
  }

  // 2. Find collateral and debt to liquidate
  // (In production, iterate through all reserves)
  const collateralAsset = 'CA...'; // ETH
  const debtAsset = 'CA...';        // USDC

  // 3. Calculate amounts
  const collateralData = await router.get_reserve_data({ asset: collateralAsset });
  const debtData = await router.get_reserve_data({ asset: debtAsset });

  const debtBalance = await new DebtToken.Client({
    contractId: debtData.debt_token_address,
    networkPassphrase,
    rpcUrl,
  }).balance_of({ id: targetUser });

  const closeFactor = new BigNumber('0.5');
  const debtToCover = new BigNumber(debtBalance.toString())
    .times(closeFactor)
    .integerValue();

  // Get prices
  const collateralPrice = await oracle.price_by_address({
    asset: collateralAsset,
  });
  const debtPrice = await oracle.price_by_address({
    asset: debtAsset,
  });

  console.log(`Liquidating ${targetUser}`);
  console.log(`Debt to cover: ${debtToCover.div(1e6)} USDC`);

  if (flashLiquidation) {
    // Two-step approach
    const prepareTx = await router.prepare_liquidation({
      caller: liquidatorKeypair.publicKey(),
      collateral: collateralAsset,
      collateral_price: collateralPrice,
      debt_asset: debtAsset,
      debt_price: debtPrice,
      user: targetUser,
      user_debt: debtBalance,
      close_factor: 5000,
      nonce: 0,
    });

    const prepareResult = await prepareTx.signAndSend();
    console.log(' Prepare confirmed');

    const executeTx = await router.execute_liquidation({
      caller: liquidatorKeypair.publicKey(),
      debt_asset: debtAsset,
      authorization: prepareResult.result,
      swap_handler: swapHandlerAddress,
    });

    const executeResult = await executeTx.signAndSend();
    return executeResult.hash;
  } else {
    // Single-step approach
    const approveTx = await new Token.Client({
      contractId: debtAsset,
      networkPassphrase,
      rpcUrl,
      publicKey: liquidatorKeypair.publicKey(),
    }).approve({
      from: liquidatorKeypair.publicKey(),
      spender: routerAddress,
      amount: debtToCover,
      expiration_ledger: ledgerSeq + 10000,
    });

    await approveTx.signAndSend();

    const liquidateTx = await router.liquidation_call({
      caller: liquidatorKeypair.publicKey(),
      collateral: collateralAsset,
      debt_asset: debtAsset,
      user: targetUser,
      debt_to_cover: debtToCover,
      receive_a_token: false,
    });

    const result = await liquidateTx.signAndSend();
    return result.hash;
  }
}
```

---

## 19. Flash Loan Flow

**Goal**: Execute atomic operation with borrowed capital (e.g., arbitrage)

### Step 1: Prepare Flash Loan Contract

Flash loan receiver must implement callback:

```typescript
// This is a Soroban contract that will be called during flash loan
#[contractimpl]
pub fn flash_loan_receiver(
  loan_amount: u128,
  fee: u128,
  initiator: Address,
  receiver: Address,
  params: &Bytes,
) -> Result<(), OperationError> {
  // 1. Execute arbitrage/operation
  // 2. Repay loan + fee to router
  Ok(())
}
```

### Step 2: Call Flash Loan from Router

```typescript
const flashTx = await router.flash_loan({
  receiver: receiverContractAddress,
  asset: usdcAddress,
  amount: new BigNumber('1000000000'), // 1000 USDC
  params: Buffer.from('custom_params'),
  initiator: userAddress,
});

const result = await flashTx.signAndSend();
console.log('Flash loan executed:', result.hash);
```

### Step 3: Calculate Fee

```typescript
// Fee = amount * fee_bps / 10000
const flashConfig = await router.get_flash_loan_config({});

const feeAmount = new BigNumber('1000000000')
  .times(flashConfig.fee_bps)
  .div(10000)
  .integerValue();

console.log(`Loan fee: ${feeAmount.div(1e6)} USDC`);
```

### Complete Example

```typescript
// Frontend initiates flash loan
async function executeFlashLoan(
  loanAmount: BigNumber,
  userKeypair: Keypair
): Promise<string> {
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: userKeypair.publicKey(),
  });

  // Prepare operation data
  const operationData = {
    swap_from: usdcAddress,
    swap_to: ethAddress,
    swap_amount: loanAmount,
  };

  const flashTx = await router.flash_loan({
    receiver: flashLoanReceiverAddress,
    asset: usdcAddress,
    amount: loanAmount,
    params: Buffer.from(JSON.stringify(operationData)),
    initiator: userKeypair.publicKey(),
  });

  const result = await flashTx.signAndSend();
  console.log(' Flash loan executed:', result.hash);

  return result.hash;
}
```

---

## 20. Swap Collateral Flow

**Goal**: Swap one collateral type for another atomically

### Step 1: Validate Swap

```typescript
// Query user's collateral positions
const userAssets = [ethAddress, btcAddress]; // User holds both

// Query reserve data for both
const ethReserve = await router.get_reserve_data({ asset: ethAddress });
const btcReserve = await router.get_reserve_data({ asset: btcAddress });

// Get user's aToken balances
const ethATokenClient = new AToken.Client({
  contractId: ethReserve.a_token_address,
  networkPassphrase,
  rpcUrl,
});

const ethATokenBalance = await ethATokenClient.balance_of({
  id: userAddress,
});

console.log(`ETH collateral: ${ethATokenBalance}`);
```

### Step 2: Approve Swap Handler

```typescript
// Router needs approval to use aToken
const approveTx = await ethATokenClient.approve({
  from: userAddress,
  spender: swapHandlerAddress,
  amount: ethATokenBalance,
  expiration_ledger: ledgerSeq + 10000,
});

await approveTx.signAndSend();
console.log('Approval confirmed');
```

### Step 3: Execute Swap

```typescript
const swapTx = await router.swap_collateral({
  caller: userAddress,
  asset_to_swap_from: ethAddress,
  asset_to_swap_to: btcAddress,
  amount_to_swap: ethATokenBalance,
  min_amount_to_receive: minimumBtc,
  swap_handler: swapHandlerAddress,
});

const result = await swapTx.signAndSend();
console.log('Swap confirmed:', result.hash);
```

### Complete Example

```typescript
async function swapCollateral(
  fromAsset: string,
  toAsset: string,
  amount: BigNumber,
  userKeypair: Keypair
): Promise<string> {
  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase,
    rpcUrl,
    publicKey: userKeypair.publicKey(),
  });

  // Get prices for slippage calculation
  const oracle = new PriceOracle.Client({
    contractId: oracleAddress,
    networkPassphrase,
    rpcUrl,
  });

  const fromPrice = await oracle.price_by_address({ asset: fromAsset });
  const toPrice = await oracle.price_by_address({ asset: toAsset });

  // Calculate minimum output (95% of fair value)
  const minOutput = amount
    .times(fromPrice)
    .div(toPrice)
    .times(0.95)
    .integerValue();

  // Execute swap
  const swapTx = await router.swap_collateral({
    caller: userKeypair.publicKey(),
    asset_to_swap_from: fromAsset,
    asset_to_swap_to: toAsset,
    amount_to_swap: amount,
    min_amount_to_receive: minOutput,
    swap_handler: swapHandlerAddress,
  });

  const result = await swapTx.signAndSend();
  console.log(' Swap confirmed:', result.hash);

  return result.hash;
}
```

---

## 21. Error Handling

### Error Code Reference

#### KineticRouter Errors
  Code | Error | Meaning |
  ------|-------|---------|
  1 | InvalidAmount | Amount is zero or invalid |
  2 | AssetNotActive | Asset not initialized |
  3 | AssetFrozen | Asset frozen by admin |
  4 | AssetPaused | Asset paused by admin |
  5 | BorrowingNotEnabled | Cannot borrow this asset |
  7 | InsufficientCollateral | Not enough collateral to borrow |
  8 | HealthFactorTooLow | HF < 1.0 after operation |
  10 | PriceOracleNotFound | No price for asset |
  11 | InvalidLiquidation | Position not eligible for liquidation |
  12 | LiquidationAmountTooHigh | Liquidation exceeds close factor |
  13 | NoDebtOfRequestedType | User has no debt of this asset |
  14 | InvalidFlashLoanParams | Flash loan parameters invalid |
  19 | SupplyCapExceeded | Would exceed asset supply cap |
  20 | BorrowCapExceeded | Would exceed asset borrow cap |
  24 | ReserveNotFound | Asset not found in reserves |
  26 | Unauthorized | Caller not authorized |
  37 | MathOverflow | Calculation overflow (u128) |
  38 | Expired | Stale price or expired authorization |

#### Oracle Errors
  Code | Error | Meaning |
  ------|-------|---------|
  1 | AssetPriceNotFound | No price available |
  4 | PriceTooOld | Price staleness exceeded |
  7 | AssetNotWhitelisted | Asset not whitelisted |
  8 | AssetDisabled | Oracle disabled for asset |

### Error Recovery Patterns

```typescript
async function operationWithErrorRecovery(
  operation: () => Promise<any>,
  maxRetries: number = 3
): Promise<any> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      console.error(`Attempt ${attempt} failed:`, error.message);

      // Analyze error
      if (error.message.includes('HealthFactorTooLow')) {
        throw error; // Permanent, user must adjust position
      } else if (error.message.includes('PriceTooOld')) {
        console.log('Waiting for fresh price...');
        await delay(5000);
        // Retry
      } else if (error.message.includes('MathOverflow')) {
        throw error; // Permanent, amount too large
      }

      if (attempt === maxRetries) {
        throw error;
      }
    }
  }
}
```

---

## 22. Event Subscription

### Event Types

All major operations emit typed events:

```typescript
export interface SupplyEvent {
  reserve: string;
  user: string;
  on_behalf_of: string;
  amount: u128;
  referral_code: u32;
}

export interface BorrowEvent {
  reserve: string;
  user: string;
  on_behalf_of: string;
  amount: u128;
  borrow_rate: u128;
  borrow_rate_mode: u32;
  referral_code: u32;
}

export interface WithdrawEvent {
  reserve: string;
  user: string;
  to: string;
  amount: u128;
}

export interface RepayEvent {
  reserve: string;
  user: string;
  repayer: string;
  amount: u128;
}

export interface LiquidationCallEvent {
  collateral: string;
  principal: string;
  user: string;
  debt_to_cover: u128;
  liquidated_collateral_amount: u128;
  liquidator: string;
  receive_a_token: boolean;
}
```

### Listening to Events

Subscribe to RPC event stream:

```typescript
import { SorobanRpc } from '@stellar/stellar-sdk';

const rpc = new SorobanRpc.Server('https://soroban-testnet.stellar.org', {
  allowHttp: false,
});

// Listen for supply events
const eventStream = rpc.subscribeEvents(
  'subscribe',
  {
    type: 'contract',
    contract_ids: [routerContractId],
  },
  (event) => {
    if (event.type === 'contract') {
      const eventData = event.contract_data;

      // Parse based on event name
      if (eventData.topic[0] === 'SupplyEvent') {
        const supply = JSON.parse(eventData.data);
        console.log(`User ${supply.user} supplied ${supply.amount}`);
      } else if (eventData.topic[0] === 'BorrowEvent') {
        const borrow = JSON.parse(eventData.data);
        console.log(`User ${borrow.user} borrowed ${borrow.amount}`);
      }
    }
  }
);

// Clean up
eventStream.close();
```

---

## 23. Precision Handling

### Conversion Factors

K2 uses three main precision standards:

```typescript
const WAD = new BigNumber('1e18');   // User-facing values
const RAY = new BigNumber('1e27');   // Interest rates
const BASIS_POINTS = new BigNumber('10000'); // Percentages

// Example conversions
const userAmount = new BigNumber('100'); // 100 USDC
const wad = userAmount.times(1e6).times(1e18); // Convert to WAD with 6-decimal token

const interestRate = new BigNumber('0.05'); // 5%
const rayRate = interestRate.times(1e27); // Convert to RAY

const ltv = new BigNumber('75'); // 75%
const ltv_bps = ltv.times(100); // 7500 basis points
```

### Precision Workflow

```typescript
// 1. Get oracle price (oracle precision: 1e14)
const oraclePrice = await oracle.price_by_address({ asset });
console.log('Oracle price:', oraclePrice); // e.g., 1500e14 for $1500

// 2. Convert to WAD for calculations
const priceWad = new BigNumber(oraclePrice.toString()).div(1e14).times(1e18);

// 3. Calculate collateral value
const collateralAmount = new BigNumber('100').times(1e6); // 100 of 6-decimal token
const collateralValue = collateralAmount.times(priceWad).div(1e18);

// 4. Convert back for storage
const priceOracleFormat = priceWad.div(1e18).times(1e14);
```

### Common Mistakes to Avoid

```typescript
//  WRONG: Forgetting decimals
const amount = 1000; // Interpreted as 1000 smallest units!
const result = amount * price; // Underflows

//  CORRECT: Explicit decimals
const amount = new BigNumber('1000').times(1e6); // 1000 with 6 decimals
const result = amount.times(price).div(1e18); // Proper scaling

//  WRONG: Mixing RAY and WAD
const rate = 1e27; // RAY
const value = 100e18; // WAD
const result = rate * value; // u256 needed, but using u128!

//  CORRECT: Use BigNumber for large calculations
const rate = new BigNumber('1e27');
const value = new BigNumber('100e18');
const result = rate.times(value).integerValue(); // Explicit u256 calculation
```

---

## 24. Gas Estimation

### Soroban Transaction Limits

Soroban has resource limits per transaction:
- CPU budget: 100M instructions
- Memory: 40MB
- Ledger operations: 40 reads, 25 writes

Complex operations may need to be split across multiple transactions.
  return simResult.cpu;
}

// Check before submitting
const tx = await router.supply({ /* ... */ });
const cpuCost = await estimateCost(tx);

if (cpuCost > 100_000_000) {
  throw new Error('Transaction exceeds CPU limit');
}

await tx.signAndSend();
```

---

## 25. Batching Operations

### Sequential Execution

Operations that depend on each other:

```typescript
async function batchOperations(userAddress: string): Promise<string[]> {
  const hashes: string[] = [];

  // Step 1: Approve and supply
  console.log('Step 1: Supply...');
  const supplyTx = await router.supply({
    caller: userAddress,
    asset: usdcAddress,
    amount: new BigNumber('1000000000'),
    on_behalf_of: userAddress,
    referral_code: 0,
  });
  const supplyResult = await supplyTx.signAndSend();
  hashes.push(supplyResult.hash);

  // Step 2: Borrow (requires step 1 complete)
  console.log('Step 2: Borrow...');
  const borrowTx = await router.borrow({
    caller: userAddress,
    asset: ethAddress,
    amount: new BigNumber('100000000'),
    interest_rate_mode: 2,
    referral_code: 0,
    on_behalf_of: userAddress,
  });
  const borrowResult = await borrowTx.signAndSend();
  hashes.push(borrowResult.hash);

  return hashes;
}
```

### Parallel View Queries

Concurrent reads (no state changes):

```typescript
async function getMultipleReserves(assets: string[]): Promise<ReserveData[]> {
  // All queries can run in parallel
  const promises = assets.map(asset =>
    router.get_reserve_data({ asset })
  );

  return Promise.all(promises);
}

const reserves = await getMultipleReserves([usdcAddress, ethAddress, btcAddress]);
```

### Transactional Batch

Multiple operations in single transaction (if under CPU limit):

```typescript
// Some operations can be batched in one tx
const multiOp = async () => {
  const result1 = await router.update_reserve_configuration({
    caller: adminAddress,
    asset: usdcAddress,
    configuration: newConfig, // Updated bitmap with pause bit set
  });

  // Both operations in single envelope
  return result1.signAndSend();
};
```

---

## 26. Frontend Integration

### React Component Example

```typescript
import React, { useState, useEffect } from 'react';
import { KineticRouter, AToken } from 'k2-contracts-client';
import BigNumber from 'bignumber.js';

interface SupplyComponentProps {
  userAddress: string;
  assetAddress: string;
  routerAddress: string;
}

export const SupplyComponent: React.FC<SupplyComponentProps> = ({
  userAddress,
  assetAddress,
  routerAddress,
}) => {
  const [balance, setBalance] = useState<BigNumber | null>(null);
  const [aTokenBalance, setATokenBalance] = useState<BigNumber | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const router = new KineticRouter.Client({
    contractId: routerAddress,
    networkPassphrase: 'Test SDF Network ; September 2015',
    rpcUrl: 'https://soroban-testnet.stellar.org',
  });

  // Load balances on mount
  useEffect(() => {
    loadBalances();
  }, [userAddress]);

  async function loadBalances() {
    try {
      // Load underlying token balance
      const reserveData = await router.get_reserve_data({ asset: assetAddress });
      const aToken = new AToken.Client({
        contractId: reserveData.a_token_address,
        networkPassphrase: 'Test SDF Network ; September 2015',
        rpcUrl: 'https://soroban-testnet.stellar.org',
      });

      const aTokenBal = await aToken.balance_of({ id: userAddress });
      setATokenBalance(new BigNumber(aTokenBal.toString()).div(1e6));
    } catch (err) {
      setError(err.message);
    }
  }

  async function handleSupply(amount: string) {
    setLoading(true);
    setError(null);

    try {
      const supplyAmount = new BigNumber(amount).times(1e6);

      const tx = await router.supply({
        caller: userAddress,
        asset: assetAddress,
        amount: supplyAmount,
        on_behalf_of: userAddress,
        referral_code: 0,
      });

      const result = await tx.signAndSend();

      if (result.status === 'success') {
        await loadBalances();
      } else {
        setError(`Transaction failed: ${result.error?.message}`);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div>
      <h2>Supply</h2>
      <p>aToken Balance: {aTokenBalance?.toFixed(6) || 'Loading...'}</p>

      <input
        type="number"
        placeholder="Amount to supply"
        disabled={loading}
      />

      <button
        onClick={() => handleSupply('100')}
        disabled={loading}
      >
        {loading ? 'Processing...' : 'Supply'}
      </button>

      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
};
```

### Vue 3 Component Example

```typescript
<script setup lang="ts">
import { ref, onMounted } from 'vue';
import { KineticRouter } from 'k2-contracts-client';
import BigNumber from 'bignumber.js';

const props = defineProps<{
  userAddress: string;
  routerAddress: string;
}>();

const balance = ref<BigNumber | null>(null);
const loading = ref(false);
const error = ref<string | null>(null);

const router = new KineticRouter.Client({
  contractId: props.routerAddress,
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
});

onMounted(async () => {
  await loadBalance();
});

async function loadBalance() {
  try {
    const data = await router.get_user_account_data({
      user: props.userAddress,
    });
    balance.value = new BigNumber(data.total_collateral_base.toString()).div(1e18);
  } catch (err) {
    error.value = err.message;
  }
}

async function supply(amount: string) {
  loading.value = true;
  error.value = null;

  try {
    // Implementation...
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="supply-component">
    <h2>Total Collateral: {{ balance?.toFixed(2) }} Base Currency</h2>
    <button @click="supply('100')" :disabled="loading">
      {{ loading ? 'Processing...' : 'Supply 100' }}
    </button>
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>
```

---

## 27. Backend Integration

### Node.js Liquidation Bot

```typescript
import { Keypair } from '@stellar/stellar-sdk';
import { KineticRouter } from 'k2-contracts-client';
import BigNumber from 'bignumber.js';

class LiquidationBot {
  private liquidatorKeypair: Keypair;
  private router: KineticRouter.Client;

  constructor(secretKey: string) {
    this.liquidatorKeypair = Keypair.fromSecret(secretKey);
    this.router = new KineticRouter.Client({
      contractId: ROUTER_ADDRESS,
      networkPassphrase: 'Test SDF Network ; September 2015',
      rpcUrl: 'https://soroban-testnet.stellar.org',
      publicKey: this.liquidatorKeypair.publicKey(),
    });
  }

  async findLiquidationTargets(
    users: string[]
  ): Promise<{ user: string; hf: BigNumber }[]> {
    const targets: { user: string; hf: BigNumber }[] = [];

    for (const user of users) {
      const data = await this.router.get_user_account_data({ user });
      if (data.health_factor < new BigNumber('1').times(1e18)) {
        targets.push({
          user,
          hf: new BigNumber(data.health_factor.toString()),
        });
      }
    }

    return targets.sort((a, b) => a.hf.minus(b.hf).toNumber());
  }

  async liquidateUser(user: string): Promise<string> {
    console.log(`Liquidating ${user}...`);

    // Implementation...

    return 'txHash';
  }

  async run(interval: number = 30000) {
    while (true) {
      try {
        const targets = await this.findLiquidationTargets(ACTIVE_USERS);
        for (const target of targets) {
          try {
            await this.liquidateUser(target.user);
          } catch (err) {
            console.error(`Failed to liquidate ${target.user}:`, err);
          }
        }
      } catch (err) {
        console.error('Error in liquidation loop:', err);
      }

      await new Promise(resolve => setTimeout(resolve, interval));
    }
  }
}

// Run bot
const bot = new LiquidationBot(process.env.LIQUIDATOR_SECRET_KEY);
bot.run();
```

### Indexing Contract Events

```typescript
import { SorobanRpc } from '@stellar/stellar-sdk';
import { Database } from 'sqlite3';

class EventIndexer {
  private rpc: SorobanRpc.Server;
  private db: Database;

  constructor(rpcUrl: string) {
    this.rpc = new SorobanRpc.Server(rpcUrl);
    this.db = new Database('events.db');
    this.setupTables();
  }

  private setupTables() {
    this.db.run(`
      CREATE TABLE IF NOT EXISTS events (
        id TEXT PRIMARY KEY,
        event_type TEXT,
        user TEXT,
        asset TEXT,
        amount TEXT,
        timestamp INTEGER,
        ledger INTEGER,
        hash TEXT
      )
    `);
  }

  async indexEvents() {
    const latestLedger = await this.rpc.getLatestLedger();

    // Subscribe and process events
    const subscription = this.rpc.subscribeEvents(
      'subscribe',
      {
        type: 'contract',
        contract_ids: [ROUTER_ADDRESS],
      },
      (event) => {
        this.processEvent(event);
      }
    );
  }

  private processEvent(event: SorobanRpc.Event) {
    if (event.type !== 'contract') return;

    const data = event.contract_data;
    const eventType = data.topic[0];

    // Parse and store event
    this.db.run(
      `INSERT INTO events VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
      [
        `${data.ledger}_${data.index}`,
        eventType,
        data.user || null,
        data.asset || null,
        data.amount?.toString() || null,
        Math.floor(Date.now() / 1000),
        event.ledger,
        event.txHash,
      ],
      (err) => {
        if (err) console.error('Failed to store event:', err);
      }
    );
  }
}

const indexer = new EventIndexer('https://soroban-testnet.stellar.org');
indexer.indexEvents();
```

---

## 28. Testing

### Unit Tests with Jest

```typescript
import { KineticRouter } from 'k2-contracts-client';
import BigNumber from 'bignumber.js';

describe('Supply Function', () => {
  let router: KineticRouter.Client;

  beforeEach(() => {
    router = new KineticRouter.Client({
      contractId: 'CTEST...',
      networkPassphrase: 'Standalone Network ; February 2017',
      rpcUrl: 'http://localhost:8000/soroban/rpc',
    });
  });

  it('should supply assets successfully', async () => {
    const amount = new BigNumber('1000000000'); // 1000 USDC

    const tx = await router.supply({
      caller: 'GA...',
      asset: 'CA...',
      amount,
      on_behalf_of: 'GA...',
      referral_code: 0,
    });

    expect(tx).toBeDefined();
  });

  it('should fail with invalid amount', async () => {
    const amount = new BigNumber('0');

    expect(() =>
      router.supply({
        caller: 'GA...',
        asset: 'CA...',
        amount,
        on_behalf_of: 'GA...',
        referral_code: 0,
      })
    ).toThrow();
  });
});
```

### Integration Tests

```typescript
import { test } from '@playwright/test';

test('Supply and withdraw flow', async ({ page }) => {
  await page.goto('http://localhost:3000');

  // Connect wallet
  await page.click('button:has-text("Connect")');
  await page.fill('[placeholder="Amount"]', '100');

  // Supply
  await page.click('button:has-text("Supply")');
  await page.waitForSelector(':has-text("Supply confirmed")');

  // Withdraw
  await page.click('button:has-text("Withdraw")');
  await page.fill('[placeholder="Amount"]', '50');
  await page.click('button:has-text("Confirm")');
  await page.waitForSelector(':has-text("Withdraw confirmed")');
});
```

---

## 29. Rate Limiting

### RPC Endpoint Considerations

Soroban testnet has rate limits:

```typescript
class RateLimitedClient {
  private requestQueue: (() => Promise<any>)[] = [];
  private processing = false;
  private lastRequestTime = 0;
  private minDelayMs = 100; // Minimum delay between requests

  async call<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          const now = Date.now();
          const delayNeeded = Math.max(0, this.minDelayMs - (now - this.lastRequestTime));

          if (delayNeeded > 0) {
            await new Promise(r => setTimeout(r, delayNeeded));
          }

          this.lastRequestTime = Date.now();
          const result = await fn();
          resolve(result);
        } catch (err) {
          reject(err);
        }
      });

      this.processQueue();
    });
  }

  private async processQueue() {
    if (this.processing || this.requestQueue.length === 0) return;
    this.processing = true;

    while (this.requestQueue.length > 0) {
      const fn = this.requestQueue.shift();
      await fn();
    }

    this.processing = false;
  }
}

// Usage
const client = new RateLimitedClient();
const data = await client.call(() =>
  router.get_user_account_data({ user: userAddress })
);
```

---

## 30. Deployment Addresses

### Testnet

```typescript
export const TESTNET_ADDRESSES = {
  // Core
  router: 'CAR253KW4HINTBLXGGBNAMH4LZWMWBCOPP6VONJK6YKCOBDPAXAGN4EK',
  priceOracle: 'CA...',

  // Tokens
  usdc: 'CA...',
  eth: 'CA...',
  btc: 'CA...',

  // Infrastructure
  treasury: 'CA...',
  incentives: 'CA...',
  flashLiquidationHelper: 'CA...',

  // Swap handlers
  soroswapAdapter: 'CA...',
  aquariusAdapter: 'CA...',
};

export const TESTNET_CONFIG = {
  networkPassphrase: 'Test SDF Network ; September 2015',
  rpcUrl: 'https://soroban-testnet.stellar.org',
  horizonUrl: 'https://horizon-testnet.stellar.org',
};
```

### Mainnet (When Available)

```typescript
export const MAINNET_ADDRESSES = {
  router: 'CA...', // TBD
  priceOracle: 'CA...', // TBD
  // ... other addresses
};

export const MAINNET_CONFIG = {
  networkPassphrase: 'Public Global Stellar Network ; September 2015',
  rpcUrl: 'https://soroban-mainnet.stellar.org',
  horizonUrl: 'https://horizon.stellar.org',
};
```

### Local Development

```bash
# Deploy contracts locally
soroban contract deploy --network standalone \
  --source-account SA...

# Get contract IDs from deploy output
export ROUTER_ADDRESS="C..."
export ORACLE_ADDRESS="C..."

# Use in tests
const localConfig = {
  contractId: process.env.ROUTER_ADDRESS,
  networkPassphrase: 'Standalone Network ; February 2017',
  rpcUrl: 'http://localhost:8000/soroban/rpc',
};
```

---

## Summary

K2 integration is straightforward with the TypeScript SDK:

1. **Install** the npm package
2. **Create client** with contract address and RPC URL
3. **Call functions** with type-safe parameters
4. **Handle results** and errors appropriately
5. **Query state** with view functions
6. **Subscribe to events** for real-time updates

For complex flows (liquidations, flash loans, swaps), refer to the step-by-step examples above.

For production deployments, use:
- Wallet integration (never ask for private keys)
- Error recovery with retries
- Rate limiting for RPC calls
- Proper precision handling
- CPU cost monitoring

---

**Last Updated**: February 2026
