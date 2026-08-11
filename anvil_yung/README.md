# 🔨 Anvil Yung: EVM Apoptosis Notarization Layer (`anvil_yung/`)

[![Foundry](https://img.shields.io/badge/Toolkit-Foundry-orange?style=for-the-badge&logo=ethereum)](https://getfoundry.sh/)
[![Smart Contract](https://img.shields.io/badge/Contract-ApoptosisAnchor.sol-blue?style=for-the-badge&logo=solidity)](./src/ApoptosisAnchor.sol)
[![Test Suite](https://img.shields.io/badge/Fuzz_Tests-20%2C000_Runs_PASS-brightgreen?style=for-the-badge)](./test/ApoptosisAnchor.t.sol)

**Anvil Yung** is the Ethereum Virtual Machine (EVM) smart contract notarization substrate for **BABYLON-60**. Built with **Foundry** (Forge, Cast, Anvil), it compiles and deploys the **`ApoptosisAnchor`** contract, registering Merkle state roots, tamper-evident hash-chains, and WORM Quarantine IPFS CIDs directly on EVM-compatible blockchains.

---

## 🎯 `ApoptosisAnchor.sol` Smart Contract Interface

The core smart contract [`src/ApoptosisAnchor.sol`](./src/ApoptosisAnchor.sol) acts as an on-chain consensus anvil to settle `CORTEX-TAINT` and enforce state transition invariants:

```solidity
contract ApoptosisAnchor {
    bytes32 public currentHead;
    uint256 public latentSteps;
    address public immutable authority;
    
    event MembraneStateCommitted(bytes32 prevHead, bytes32 newHead, uint256 latentSteps);
    event ApoptosisLogged(bytes32 taint, string reason, string wormSnapshotCid, bytes signature);

    function commitState(bytes32 inputHash, bytes32 outputHash, uint256 steps) external onlyAuthority;
    function logApoptosis(bytes32 taintLog, string calldata reason, string calldata wormSnapshotCid, bytes calldata signature) external onlyAuthority;
}
```

### Key Security Invariants

1. **Fork Protection (`BFT_FORK_DETECTED`)**: `commitState` requires `inputHash == currentHead`. Attempting to commit from a stale or divergent state head reverts with `BFT_FORK_DETECTED: Input hash does not match current head`.
2. **WORM Quarantine Logging (`logApoptosis`)**: When an agent state triggers a thermodynamic halt, `logApoptosis` locks the current head to `taintLog`, resets latent steps to zero, and emits an `ApoptosisLogged` event with the WORM snapshot IPFS CID and hardware cryptographic signature.
3. **Authority Guard (`onlyAuthority`)**: Only the immutable authority address (configured at deployment) can commit states or trigger apoptosis logging, preventing unauthorized state corruption.

---

## 🛠️ Verification & Fuzz Testing

```bash
cd anvil_yung

# Run Foundry test suite (20,000 fuzz iterations per property)
forge test -vvv
```

### Verified Test Suite ([`test/ApoptosisAnchor.t.sol`](./test/ApoptosisAnchor.t.sol))

- `testFuzz_CommitState(bytes32,uint256)`: Verifies continuous head state transition and step accumulation.
- `testFuzz_ForkProtection(bytes32,bytes32,uint256)`: Proves that invalid input hashes trigger `BFT_FORK_DETECTED`.
- `testFuzz_ApoptosisTruncation(bytes32,string,string,bytes)`: Validates state truncation and WORM snapshot CID recording upon apoptosis.
- `test_UnauthorizedCallerReverts()`: Asserts that non-authority addresses are rejected with `UNAUTHORIZED_ANCHOR_CALLER`.

---

## 🚀 Deployment & Anvil Local Node

```bash
# 1. Start local Anvil RPC node
anvil --port 8545

# 2. Deploy ApoptosisAnchor contract to Anvil
forge script script/Counter.s.sol:CounterScript \
  --rpc-url http://127.0.0.1:8545 \
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 \
  --broadcast
```

---

<sub>BABYLON-60 Anvil Yung Substrate · EVM On-Chain Notary · Borja Moskv</sub>
