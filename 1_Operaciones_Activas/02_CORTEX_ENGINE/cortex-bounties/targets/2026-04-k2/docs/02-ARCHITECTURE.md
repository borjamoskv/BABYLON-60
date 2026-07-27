# 2. Architecture Model

## System Overview

K2's architecture follows a modular, contract-based design where each component has a specific responsibility.

```mermaid
graph TD
    Users["Users, Liquidators, Developers"]

    Router["Kinetic Router<br/>(Main Pool)"]
    PoolCfg["Pool Configurator<br/>(Admin)"]
    FlashHelper["Flash Loan Helper<br/>(Validation)"]

    AToken["aToken<br/>(Supply)"]
    DebtToken["Debt Token<br/>(Borrow)"]
    UserConfig["User Config<br/>(Positions)"]

    UnderlyingAsset["Underlying Asset<br/>(SEP-41 Token)"]

    Oracle["Price Oracle"]
    RateStrategy["Interest Rate<br/>Strategy"]
    Treasury["Treasury<br/>(Fees)"]
    Incentives["Incentives<br/>(Rewards)"]

    Reflector["Reflector Oracle<br/>(Stellar)"]
    RedStone["RedStone Adapter<br/>(External)"]
    RedStoneFeeds["RedStone Feeds<br/>(BTC, ETH, etc.)"]

    DEXAdapters["DEX Adapters"]
    Soroswap["Soroswap<br/>DEX"]
    Aquarius["Aquarius<br/>DEX"]

    Users --> Router
    Users --> PoolCfg
    Router --> FlashHelper

    Router --> AToken
    Router --> DebtToken
    Router --> UserConfig

    AToken --> UnderlyingAsset

    Router --> Oracle
    Router --> RateStrategy
    Router --> Treasury
    Router --> Incentives

    Oracle --> Reflector
    Oracle --> RedStone
    RedStone --> RedStoneFeeds

    Router --> DEXAdapters
    DEXAdapters --> Soroswap
    DEXAdapters --> Aquarius

    style Users fill:#e1f5ff
    style Router fill:#fff3e0
    style PoolCfg fill:#f3e5f5
    style FlashHelper fill:#f3e5f5
    style AToken fill:#e8f5e9
    style DebtToken fill:#e8f5e9
    style Oracle fill:#fce4ec
    style Treasury fill:#fff9c4
```

---

## Contract Responsibilities

### **Kinetic Router** (Core)
**Entry point for all user operations.**

Responsibilities:
- User authentication and authorization
- Supply/withdraw asset operations
- Borrow/repay operations
- Liquidation execution (standard and two-step)
- Flash loan coordination
- Collateral swap execution
- Health factor validation
- Interest rate updates

Dependencies:
- Price Oracle (for valuations)
- Interest Rate Strategy (for rate calculations)
- Treasury (for fee collection)
- Swap Adapters (for liquidation and swaps)
- aToken & Debt Token contracts (for position management)

### **Pool Configurator** (Admin)
**Manages reserve lifecycle and protocol parameters.**

Responsibilities:
- Deploy new aToken and debtToken contracts
- Initialize new reserves
- Configure reserve parameters
- Manage supply/borrow caps
- Update protocol settings
- Reserve activation/deactivation

Dependencies:
- Kinetic Router (updates propagated here)
- aToken & Debt Token implementations

### **Price Oracle** (Core Dependency)
**Provides asset prices with manipulation protection.**

Responsibilities:
- Query asset prices
- Manage asset whitelist
- Validate staleness
- Circuit breaker for extreme movements
- Handle manual overrides
- Support multiple price sources

Data:
- Current prices (14 decimals)
- Timestamps (for staleness checks)
- Circuit breaker state
- Manual override values

### **Interest Rate Strategy** (Core Dependency)
**Calculates interest rates based on market conditions.**

Responsibilities:
- Calculate liquidity rate (supply APY)
- Calculate variable borrow rate
- Use utilization-based curve
- Support per-asset configuration
- Optimize for capital efficiency

Inputs:
- Total supply
- Total debt
- Reserve factor
- Optimal utilization

### **aToken** (Token Contract)
**Interest-bearing token representing supplied assets.**

Responsibilities:
- Track scaled balances
- Apply liquidity index for balance growth
- Support transfers (with whitelist validation)
- Mint on supply
- Burn on withdraw
- Transfer underlying to withdrawers

Features:
- Automatic interest accrual
- Whitelist enforcement
- Only pool can mint/burn

### **Debt Token** (Token Contract)
**Non-transferable token representing borrowed amounts.**

Responsibilities:
- Track scaled balances
- Apply borrow index for interest accrual
- Prevent transfers/approvals
- Mint on borrow
- Burn on repay
- Never held by users (read-only)

Features:
- Automatic interest accrual
- Non-transferable
- Only pool can mint/burn

### **Treasury** (Fund Management)
**Collects and manages protocol fees.**

Responsibilities:
- Receive protocol fees from liquidations
- Receive protocol fees from flash loans
- Withdraw funds (admin-only)
- Track balances per asset

### **Incentives** (Reward System)
**Distributes rewards to suppliers and borrowers.**

Responsibilities:
- Manage reward emissions
- Calculate user rewards
- Distribute reward tokens
- Support per-asset configuration

### **RedStone Adapter** (Oracle Integration)
**Bridges RedStone oracle network to K2.**

Responsibilities:
- Verify cryptographic signatures
- Validate timestamps
- Store external asset prices
- Implement Reflector-compatible interface
- Manage trusted signers

---

## Authorization Model

### **Authorization Tree** (Soroban)
Each transaction establishes authorization context once:

```mermaid
graph TD
    A["User Signs Transaction"]
    B["User's intent authorized for this tx"]
    C["All contract calls inherit this authorization"]
    D["No re-authorization needed for sub-calls"]
    E["Unless different user or fund movement"]

    A --> B
    A --> C
    A --> D
    D --> E

    style A fill:#bbdefb
    style D fill:#fff9c4
```

### **Authorization Patterns**

#### **1. User Operations**
Functions that move user funds require user authorization.

```mermaid
graph TD
    A["router.supply(user, asset, amount, on_behalf_of)"]
    B["require_auth(user)"]
    C{"user ≠ on_behalf_of?"}
    D["require_auth(on_behalf_of)"]
    E["Transfer user's tokens to pool"]
    F["Mint aTokens to on_behalf_of"]

    A --> B
    B --> C
    C -->|Yes| D
    C -->|No| E
    D --> E
    E --> F

    style B fill:#ffcdd2
    style D fill:#ffcdd2
```

#### **2. Admin Operations**
Functions that change protocol state require admin authorization.

```mermaid
graph TD
    A["router.initialize(pool_admin, oracle, treasury, ...)"]
    B["require_auth(pool_admin)"]
    C["Initialize protocol state"]

    A --> B
    B --> C

    style B fill:#ffcdd2
```

#### **3. Cross-Contract Authorization**
When contracts call each other's token operations.

```mermaid
sequenceDiagram
    participant Router
    participant aToken

    Router->>aToken: mint_scaled(user, amount, index)
    Note over aToken: Check caller == authorized_pool
    aToken->>aToken: Authorized (inherited from router)
    aToken-->>Router: Mint complete
```

#### **4. Self-Authorization** (Rare)
When a contract needs to authorize its own token transfers.

```mermaid
sequenceDiagram
    participant SwapAdapter
    participant Token

    SwapAdapter->>SwapAdapter: authorize_as_current_contract([transfer(...)])
    SwapAdapter->>Token: transfer_from(from, to, amount)
    Token-->>SwapAdapter: Transfer complete
```
    -Adapter can now call token.transfer()
```

---

## Data Flow

### **Supply Operation**
```
User
  
  -Approve tokens �� aToken address
  
  -router.supply(user, asset, amount, on_behalf_of)
       
       -require_auth(user)
       -Validate whitelist
       -Update reserve state (accrue interest)
       -Validate supply cap
       
       -Transfer assets: user �� aToken
       
       -aToken.mint_scaled(on_behalf_of, amount, index)
          -Update user's scaled balance
       
       -Update user configuration bitmap
       -Update interest rates
            
            -Store new reserve state
```

### **Borrow Operation**
```
User (has collateral)
  
  -router.borrow(user, asset, amount, rate_mode, on_behalf_of)
       
       -require_auth(user)
       -Update reserve states (both assets)
       -Validate borrow cap
       -Get prices from oracle
       
       -Calculate health factor after borrow
          -Verify HF �� 1.0
       
       -Validate available liquidity
       
       -Debt Token.mint_scaled(on_behalf_of, amount, borrow_index)
       
       -aToken.transfer_underlying(on_behalf_of, amount)
          -Send borrowed assets to user
       
       -Update user configuration
       -Update interest rates
```

---

## Execution Model

### **Single-Transaction Operations**
Operations completing in one Soroban transaction:

- Supply (30-40M CPU)
- Withdraw (30-40M CPU)
- Borrow (40-50M CPU)
- Repay (30-40M CPU)
- Standard Liquidation (35-46M CPU, 2-5 reserves)
- Flash Loan (40-60M CPU)
- Swap Collateral (50-70M CPU)

### **Two-Transaction Operations**
Operations split across transactions for large computations:

**Two-Step Liquidation:**

Transaction 1: Preparation
- Validate liquidator
- Fetch prices
- Calculate health factor
- Calculate liquidation amounts
- Store authorization (10-min expiry, 600 ledgers)

Transaction 2: Execution
- Validate authorization
- Execute flash loan
- Perform collateral swap
- Settle debt
- Transfer profit

---

## State Persistence

### **Contract Storage**
Soroban stores contract state persistently:

```
Contract Instance Storage
-Instance Data (max 4 MB)
  -Simple key-value pairs
  -Admin addresses
  -Configuration parameters
  -Protocol state

-Temporary Data (TTL-managed)
   -User positions (balances)
   -Reserve data
   -Liquidation authorizations (10 min, 600 ledgers)
   -Price cache entries
```

### **TTL Management**
All contract data has a Time-To-Live (TTL):

- **TTL**: Up to 6 months per entry
- **Renewal**: Automatic on each read/write
- **Expiry**: Deleted if not renewed
- **Router Entry Points**: Extend TTL on major operations

---

## Integration Points

### **DEX Adapters**
Soroswap and Aquarius swap adapters enable:
- Collateral swaps (user can change collateral type)
- Flash liquidation swaps (liquidator swaps collateral �� debt asset)
- Two-step liquidation coordination

### **Price Feeds**
Two price feed sources:
- **Reflector**: Default for Stellar-native assets
- **RedStone**: External assets (BTC, ETH, stables)

### **Event Stream**
Off-chain indexers subscribe to events:
- User operations (supply, borrow, repay, withdraw)
- Liquidations
- Protocol state changes
- Administrative actions

---

## Deployment Topology

### **Testnet**
```
Deployment Network: testnet.stellar.org
-Kinetic Router (main contract)
-Pool Configurator (admin)
-Price Oracle (Reflector + RedStone)
-Interest Rate Strategy
-Treasury
-aToken implementation
-Debt Token implementation
-Soroswap Adapter
-Aquarius Adapter
-RedStone Adapter
-Liquidation Engine
-Flash Liquidation Helper
-Incentives
```

### **Mainnet**
```
Same contract set, deployed to mainnet.stellar.org
- Higher gas costs (higher CPU per operation)
- Conservative parameter defaults
- Multi-sig admin controls
- Emergency pause capability
```

---

## Upgrade Path

### **Business Logic Contracts** (Upgradeable)
- Kinetic Router
- Pool Configurator
- Interest Rate Strategy
- Price Oracle
- aToken & Debt Token
- All adapters

Upgrade Process:
1. Compile new WASM
2. Install on-chain (get hash)
3. Upgrade admin + pool admin call `upgrade(new_hash)` (dual-auth)
4. Code updated, storage preserved

### **Immutable Contracts** (Never Change)
- Shared library (math, types)
- Core cryptographic utilities

Reason: Upgrading breaks all dependents

---

## Next Steps

1. Understand each component: [System Components](04-COMPONENTS.md)
2. Learn execution flows: [Execution Flows](05-FLOWS.md)
3. Dive into storage: [Storage Architecture](10-STORAGE.md)

---

**Last Updated**: February 2026
