# Autodidact Learning Module – K2 Lending Close‑Factor Bypass (C4)

## 1️⃣ Overview
The **Close‑Factor Bypass** (C4) vulnerability allows an attacker to open a loan with insufficient collateral by exploiting a race condition between the vault’s pending‑exit accounting and the loan‑opening balance check. The protocol over‑estimates the borrower’s collateral, enabling over‑borrowing and profit extraction.

## 2️⃣ Threat Model
| Actor | Capability | Goal |
|-------|------------|------|
| **Attacker (EOA)** | Can call `requestExit`, `openLoan`, and any public vault function in the same block. | Inflate effective collateral, bypass the close‑factor limit, and extract excess funds. |
| **Protocol** | Tracks deposits via `vaultAccountedBalance` and `inFlightExitingAmount` in epoch‑bucketed storage. | Ensure solvency and enforce the close‑factor invariant.

## 3️⃣ Core Logical Flaw
- The vault records a *pending exit* (`inFlightExitingAmount`) that is only reconciled at the end of the epoch.
- `K2Lending.openLoan` checks the **snapshot** of `vaultAccountedBalance` **before** the pending exit is deducted.
- When `requestExit` and `openLoan` are executed in the same block, the loan passes the collateral check using the stale balance, while the pending exit later reduces the real collateral.

## 4️⃣ Exploit Steps (single‑agent)
```solidity
// 1. Deposit collateral
vault.deposit{value: 10 ether}();

// 2. Queue a tiny exit (e.g., 0.1 ether)
vault.requestExit(0.1 ether);

// 3. Within the same block, open a loan using the stale balance
k2Lending.openLoan({borrowAmount: 5 ether}); // passes close‑factor check

// 4. After the block, the pending exit is reconciled, reducing collateral to 9.9 ether
//    The loan is now under‑collateralized (5 ether borrowed against 4.95 ether effective).
```
Running the above in a single transaction (or using a flash‑loan‑style wrapper) yields profit without liquidation risk.

## 5️⃣ Multi‑Agent Amplification
Deploy **N** parallel agents (e.g., 100) each performing the above steps in the same block. The aggregate profit scales linearly:
```
Profit_per_agent ≈ 0.05 ether → 0.05 ether × N
```
With **N = 100**, profit ≈ 5 ether (~$8 k).

## 6️⃣ Mitigations (Deterministic Guard Insertion)
1. **Synchronize Balance Read** – Call `vault.processPendingExits()` **before** any balance snapshot in `openLoan`.
2. **Atomic Exit‑Borrow** – Implement a wrapper `safeBorrow(uint256 amount)` that performs `requestExit → processPendingExits → openLoan` atomically.
3. **Re‑entrancy Guard** – Apply `nonReentrant` to all public vault entry points.
4. **Event‑Based Assertion** – Emit `VaultSyncViolation(address attacker, uint256 before, uint256 after)` if a balance mismatch is detected.

## 7️⃣ Test Suite (Foundry)
- **`test/CloseFactorBypass.t.sol`** – Deploy mainnet‑fork of the exact contract (`0xE31b…4817`).
- Use `vm.prank` to simulate 100 agents in a single block.
- Assert that the profit before mitigation is `> 0` and after applying guards is `== 0`.

## 8️⃣ References
- **K2 Lending Audit** – Code4rena submission (2026‑04‑K2).
- **StakingVaultOperations.sol** – Lines 120‑149 (pending‑exit logic) and 210‑224 (balance read).
- **EIP‑2535 (Diamond) Proxy** – Interaction via `delegatecall`/`ERC‑7201`.

---
*Prepared as an autodidact learning module to enable rapid self‑education and replication of the vulnerability analysis.*
