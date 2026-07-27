# 1. Protocol Overview

## Purpose

K2 is a decentralized borrowing and lending protocol deployed on Stellar's Soroban smart-contract platform. It enables users to:

- **Supply** assets to earn interest-bearing positions
- **Borrow** assets against collateral at market-determined rates
- **Liquidate** undercollateralized positions to maintain protocol solvency
- **Execute flash loans** for atomic operations without collateral

The protocol is modeled after Aave V3, adapted for Soroban's execution model and Stellar's ecosystem.

---

## Design Principles

### 1. **Safety First**
- Multi-layered authorization checks
- Health factor enforcement before every position-changing operation
- Emergency pause controls for rapid incident response
- Conservative default parameters

### 2. **Capital Efficiency**
- Scaled balance accounting to minimize rounding errors
- Interest index accumulation for exact interest calculation
- Flash loans to optimize liquidation and arbitrage
- Configurable caps and parameters per asset

### 3. **Transparency**
- All state changes emit typed events
- Oracle prices publicly queryable
- User positions deterministically calculated
- Reserve metrics available on-chain

### 4. **Modularity**
- Separated concerns: routing, tokens, oracles, strategies
- Upgradeable contracts for business logic
- Factory pattern for reserve deployment
- Adapter pattern for DEX integrations

---

## User Archetypes

### **Liquidity Providers**
Users supplying assets to earn interest.

- Supply assets → receive aTokens
- aToken balance grows via interest accrual
- Withdraw anytime (if protocol has liquidity)
- Interest earned automatically compounded

### **Borrowers**
Users borrowing against collateral.

- Supply collateral → borrow other assets
- Interest accrues daily at variable rate
- Repay anytime to reduce debt
- Liquidation risk if health factor falls below 1.0

### **Liquidators**
Users liquidating undercollateralized positions.

- Monitor health factors of risky positions
- Execute liquidation when HF < 1.0
- Receive liquidation bonus (e.g. 5%)
- Protocol fee deducted from bonus

### **Developers**
Building apps on top of K2.

- Use TypeScript client bindings
- Integrate into wallets, dashboards, arbitrage bots
- Subscribe to events for real-time UI updates
- Query view functions for account data

---

## Key Statistics


### **Protocol Parameters** (Configurable)

| Parameter | Default | Range |
|-----------|---------|-------|
| Flash Loan Premium | 30 bps (0.30%) storage fallback; `initialize()` sets max to 100 bps | 0-100 bps |
| Liquidation Close Factor | 50% default (5000 bps); 100% when HF < threshold or small positions | Dynamic |
| Liquidation Threshold | Per-asset | 50-100% |
| LTV | Per-asset | 0-99% |
| Supply Cap | Per-asset | 0-u128::MAX |
| Borrow Cap | Per-asset | 0-u128::MAX |
| Price Max Age | Per-asset | Seconds |

---

---

## Protocol Invariants

The protocol maintains several key invariants that must hold after every operation:

1. **Solvency**
   - `total_aToken_supply ≤ underlying_balance + total_debt`
   - Providers never lose capital

2. **Health**
   - After supply/borrow/repay: `HF ≥ 1.0` or position liquidatable
   - Borrowers always have min safety margin

3. **Monotonicity**
   - Liquidity index never decreases
   - Borrow index never decreases
   - Interest always accrues forward in time

4. **Conservation**
   - Every debt token mint matched by collateral lock
   - Every debt token burn releases collateral proportionally
   - Flash loan premium always collected

5. **Completeness**
   - Every reserve has interest rate strategy
   - Every reserve has oracle price available
   - No missing configuration data

---

## Success Metrics

### **For Users**
- Earn APY on supplied capital
- Borrow at predictable rates
- Liquidations prevent catastrophic loss cascades
- No unexpected fees or parameter changes

### **For Protocol**
- Growing total value locked (TVL)
- Stable utilization rate (optimal ~80%)
- Healthy liquidation participation
- Zero bad debt accumulation

### **For Ecosystem**
- Deepens Stellar's DeFi infrastructure
- Enables new financial primitives
- Attracts developers and users
- Sustains long-term growth

---

## Deployment Models

### **Isolated Pool**
Single instance for a specific ecosystem or use case.

- One Kinetic Router contract
- Multiple reserves (assets)
- Dedicated oracle and treasury
- Isolated risk domain

### **Multi-Pool** (Future)
Multiple pools with cross-pool features.

- Separate risk domains
- Shared oracle for efficiency
- Central treasury
- Pool-to-pool transfers

---

## Next Steps

1. **To understand the protocol**: Read [Core Concepts](03-CORE-CONCEPTS.md)
2. **To deploy K2**: Follow [Deployment Guide](12-DEPLOYMENT.md)
3. **To integrate**: See [Integration Reference](13-INTEGRATION.md)
4. **To audit**: Review [Security Model](09-SECURITY.md)

---

**Last Updated**: February 2026
