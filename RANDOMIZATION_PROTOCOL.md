# RANDOMIZATION_PROTOCOL.md — Frozen Randomization & Allocation Protocol

> **STATUS: FROZEN / NORMATIVE**  
> **Repository**: `borjamoskv/teorema-robinson-moskv`  

This document specifies the exact randomization, seed generation, sample pairing, arm ordering, baseline generation, retry handling, and stopping rules for all experimental runs within the Teorema Robinson-Moskv framework.

---

## 1. Frozen Allocation Schema

```yaml
randomization:
  master_seed: 0x5F3759DF
  prng_algorithm: "ChaCha20"
  pairing_policy: "EXACT_PAIRED_SAMPLES"
  arm_ordering: "BALANCED_LATIN_SQUARE"
  retry_policy: "ZERO_RETRIES"
  stopping_rule: "FIXED_SAMPLE_SIZE"
```

---

## 2. Seed Generation & Deterministic Pairing

To ensure exact paired sample comparisons across all treatment arms ($D, C, B, F$):

1. **Master PRNG Initialization**: A cryptographic ChaCha20 PRNG is seeded with `master_seed = 0x5F3759DF`.
2. **Task Seed Derivation**: For each benchmark task index $i \in \{1, \dots, N\}$, the specific evaluation seed $S_i$ is generated as:
   $$S_i = \text{HMAC-SHA256}(\text{master\_seed}, \text{"task\_" } \parallel i)$$
3. **Arm Seed Invariance**: Task item $i$ executed under Arm $D$, Arm $C$, Arm $B$, and Arm $F$ uses the identical task seed $S_i$ to initialize model sampling, environment non-determinism, and generator state.

---

## 3. Arm Ordering & Execution Interleaving

To prevent order-dependent resource contention, thermal throttling, or API rate-limiting biases:

1. **Interleaved Execution**: Tasks are evaluated in batches where treatment arms are executed in randomized order per task item:
   $$\text{Order}(i) = \text{Permute}(\{D, C, B, F\}, S_i)$$
2. **No Post-Hoc Arm Switching**: The assignment of task $i$ to treatment arm $A$ is determined prior to executing task $i$. Switching arms post-execution is strictly forbidden.

---

## 4. Ablation & Null Generation Protocols

### 4.1 Permutation of Arm F
- Arm $F$ evaluates CTM reachability under a permuted action-transition matrix $\mathbf{P} \cdot \delta \cdot \mathbf{P}^T$.
- The permutation matrix $\mathbf{P}$ is generated deterministically using $S_i$ and locked prior to run execution.

### 4.2 Null Baseline Generation for Arm C
- Arm $C$ runs without reachability bounds or action filtering, establishing the empirical unconstrained null distribution $\mathcal{N}_C$.

---

## 5. Retry & Stopping Rules

1. **Zero Retries (`ZERO_RETRIES`)**: Any transient API error, timeout, or rate-limit failure on task $i$ is recorded as an `EVALUATION_TIMEOUT` or `INVALID_OUTPUT` failure for that task across all arms. Retrying failed calls is strictly prohibited.
2. **Fixed Sample Size (`FIXED_SAMPLE_SIZE`)**: Evaluation continues until all $N$ pre-registered task items complete. Early stopping based on intermediate $p$-values (adaptive stopping) is **prohibited**.
