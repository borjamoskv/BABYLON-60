# 🔨 Anvil Yung: EVM Notarization Layer (`anvil_yung/`)

[![Foundry](https://img.shields.io/badge/Toolkit-Foundry-orange?style=for-the-badge&logo=ethereum)](https://getfoundry.sh/)
[![Smart Contracts](https://img.shields.io/badge/EVM-Solidity_0.8.20-blue?style=for-the-badge&logo=solidity)](https://soliditylang.org/)
[![Causal Anchor](https://img.shields.io/badge/Anchor-On--Chain_WORM-brightgreen?style=for-the-badge)]()

**Anvil Yung** is the Ethereum Virtual Machine (EVM) smart contract notarization layer for **BABYLON-60**. Built with **Foundry** (Forge, Cast, Anvil), it compiles and deploys Solidity contracts that register Merkle state roots, tamper-evident hash-chains, and WORM Quarantine certificates directly on EVM-compatible blockchains.

---

## 🎯 Architecture & Components

- **Forge**: Compiles, unit tests, and fuzzes BABYLON-60 EVM notarization smart contracts.
- **Anvil**: Local ephemeral Ethereum node simulating zero-latency state root commits during integration testing.
- **Cast**: CLI tool interfacing with deployed on-chain notarization contracts.

---

## 🚀 Quick Start

### Build Contracts

```bash
cd anvil_yung
forge build
```

### Run Fuzz & Unit Tests

```bash
forge test -vvv
```

### Launch Local Anvil Node

```bash
anvil --port 8545
```

### Deploy Notary Contract to Chain

```bash
forge script script/Counter.s.sol:CounterScript \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast
```

---

## 📁 Directory Structure

```
anvil_yung/
├── src/                # Solidity smart contract source code
├── test/               # Forge unit & fuzz test suites
├── script/             # Deployment & interaction scripts
├── lib/                # Submodules (forge-std)
└── foundry.toml        # Foundry compilation & EVM network configuration
```

---

<sub>BABYLON-60 Anvil Yung Substrate · EVM On-Chain Notary · Borja Moskv</sub>
