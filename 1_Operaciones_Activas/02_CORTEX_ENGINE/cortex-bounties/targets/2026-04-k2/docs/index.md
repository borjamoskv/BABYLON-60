---
layout: home
title: Home
nav_order: 0
---

# K2 Lending Protocol

**Decentralized borrowing and lending, natively on Stellar.**

K2 is a fully on-chain money market protocol built on [Stellar's Soroban](https://soroban.stellar.org/) smart contract platform. It enables users to supply digital assets to earn yield, borrow against their collateral, and participate in liquidations — all with deterministic settlement and no intermediaries.

---

## What K2 Does

| For Suppliers | For Borrowers | For the Ecosystem |
|:--|:--|:--|
| Deposit assets and earn variable interest in real-time | Borrow against collateral at market-driven rates | First institutional-grade lending protocol on Stellar |
| Receive transferable aTokens representing your position | Flexible repayment with no lock-up periods | Composable with Stellar DEXs (Soroswap, Aquarius) |
| Withdraw anytime, subject to utilization | Flash loans for capital-efficient operations | Audited smart contracts with multi-layer security |

---

## Why Stellar / Soroban?

- **5-second finality** — no waiting for block confirmations
- **Sub-cent transaction fees** — accessible to all users, not just whales
- **No MEV / frontrunning** — Stellar's consensus model eliminates transaction reordering
- **Native asset interop** — seamless integration with Stellar's existing asset ecosystem (USDC, SolvBTC, and more)
- **Built-in authorization model** — Soroban's auth tree eliminates entire classes of smart contract vulnerabilities

---

## Protocol at a Glance

| Metric | Detail |
|:--|:--|
| **Architecture** | Modular router pattern (Aave V3-inspired) |
| **Supported Assets** | Any SEP-41 token (USDC, XLM, PYUSD, SolvBTC, ...) |
| **Interest Rates** | Variable, algorithmically determined by utilization |
| **Oracle System** | Multi-source (Reflector, RedStone) with batch pricing and caching |
| **Liquidation** | Permissionless with configurable close factors and bonuses |
| **Security** | Professional audit completed, all critical findings remediated |
| **Network** | Stellar Soroban (Testnet live, Mainnet ready) |

---

## Documentation

Explore the sections below to understand how K2 works:

- [**Protocol Overview**]({% link 01-OVERVIEW.md %}) — Purpose, design principles, and user archetypes
- [**Architecture**]({% link 02-ARCHITECTURE.md %}) — System design, contract topology, and data flow
- [**Core Concepts**]({% link 03-CORE-CONCEPTS.md %}) — Reserves, collateral, health factors, and interest mechanics
- [**System Components**]({% link 04-COMPONENTS.md %}) — Router, tokens, oracle, and supporting contracts
- [**Execution Flows**]({% link 05-FLOWS.md %}) — Supply, borrow, repay, withdraw, and swap operations
- [**Liquidation System**]({% link 06-LIQUIDATION.md %}) — Risk management, liquidation mechanics, and bad debt handling
- [**Interest Model**]({% link 07-INTEREST-MODEL.md %}) — Rate curves, utilization targeting, and yield mechanics
- [**Oracle Architecture**]({% link 08-ORACLE.md %}) — Price feeds, staleness protection, and multi-source aggregation
- [**DEX Integration**]({% link 08-DEX-INTEGRATION.md %}) — Collateral swaps, flash liquidations, and adapter pattern
- [**Security Model**]({% link 09-SECURITY.md %}) — Authorization, audit posture, and defense-in-depth design
- [**Glossary**]({% link 15-GLOSSARY.md %}) — Key terms and definitions
