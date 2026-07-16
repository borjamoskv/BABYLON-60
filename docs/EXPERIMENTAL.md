# EXPERIMENTAL — cortex-persist Extensions

> [!CAUTION]
> **All features documented here are experimental, prototypical, or at design stage.** They are not suitable for production use. APIs may change without notice. Coverage is below 40%.

---

## BFT Swarm (L4 Consensus)

**Status: Prototype (~20% coverage)**

Byzantine Fault Tolerant consensus extending the local ledger to a distributed quorum of agents.

### Theoretical Model

- Requires N ≥ 3f+1 nodes where f = tolerated Byzantine faults
- Each node maintains an independent copy of the hash-chain
- Lamport timestamps provide total ordering across nodes
- CRDT merge resolves non-conflicting concurrent writes

### Current State

- `babylon60.bft.ledger_actor` implements the single-writer actor (L2 — stable)
- Distributed quorum layer (`moskv-swarm`) is a **separate package** that is not a dependency of the core `cortex-persist`
- No production benchmarks exist for N>1 node scenarios

### Known Limitations

- Split-brain recovery under network partition is not tested
- Reputational weighting of agents in quorum is not implemented
- No authentication between swarm nodes

---

## Vector Memory (`sqlite-vec`)

**Status: Alpha (~35% coverage)**

Semantic similarity search over ledger entries using embedded vectors.

### Usage (Experimental)

```bash
pip install "cortex-persist[embeddings]"
```

```python
from babylon60.memory.vector import VectorMemory
mem = VectorMemory(db_path="cortex_memory.db")
results = mem.search("agent startup sequence", top_k=5)
```

### Limitations

- Embedding models must be loaded separately (`sentence-transformers` or `mlx-lm`)
- Vector index is rebuilt from scratch on schema migration
- No incremental index update — full reindex required on large ledger mutations

---

## Formal Verification (`proof/lean/`)

**Status: Prototype (~15% coverage)**

Lean 4 mechanical proofs of core ledger invariants.

### Theorems in Progress

- `Babylon.lean` — partial ordering of ledger entries
- Non-equivocation: a single-writer actor cannot produce two conflicting entries for the same Lamport timestamp
- BFT safety bound: no fork below f < N/3 Byzantine nodes

### Current State

Not integrated into CI. Requires `lake build` locally. Theorem coverage does not match implementation — proofs are written against an idealized model, not against `ledger_actor.py` directly.

---

## LoRA Fine-Tuning Daemon

**Status: Design (0% coverage)**

A planned background daemon that fine-tunes a local LLM on ledger history to produce a personalized inference layer.

### Design Intent

- Consume `cortex_memory.db` history as training data
- Fine-tune a base model via LoRA / QLoRA on Apple Silicon (MLX-LM)
- Write fine-tuned adapter weights back to the ledger with causal taint

### Current State

**Not implemented.** No code exists beyond design notes. Do not reference this as a feature.

---

## Hyperdimensional Computing (HDC)

**Status: Design (0% coverage)**

An alternative to vector embeddings using binary hypervectors for near-zero memory similarity search.

### Design Intent

- Encode ledger entries as 10,000-bit hypervectors
- Similarity via Hamming distance — O(1) per comparison
- Bundling and binding operations for compositional memory

### Current State

**Not implemented.** Literature review only.

---

## Blockchain Anchoring (L5)

**Status: Research (0% coverage)**

External tamper-evident anchoring of the ledger's Merkle root to a public blockchain.

### Design Intent

- Accumulate BLAKE3 hashes into a Merkle tree
- Submit root hash to Bitcoin via OP_RETURN or to Solana
- Use OpenTimestamps protocol for decentralized timestamp proofs

### Current State

`L1_sink/` directory contains an experimental OTS sink. Not integrated into the main ledger pipeline. No production use.

---

## Node.js Telemetry Daemon

**Status: Alpha (~25% coverage)**

Local HTTP + WebSocket server collecting Mac-native hardware telemetry (CPU, memory, thermal state).

### Usage

```bash
node server.js
```

Exposes metrics at `ws://localhost:8080`.

### Limitations

- macOS-only (uses `system_profiler` and native APIs)
- No authentication on WebSocket endpoint
- Metrics schema may change between versions

---

## Contributing to Experimental Features

If you are working on any of these modules:

1. Keep experimental code under `experimental/` or clearly namespaced (`babylon60.experimental.*`)
2. Write at minimum a unit test stub before opening a PR
3. Update the maturity matrix in `README.md` when coverage changes
4. Do not import experimental modules from stable `babylon60.*` paths
