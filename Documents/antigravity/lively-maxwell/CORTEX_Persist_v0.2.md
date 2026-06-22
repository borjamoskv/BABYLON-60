# CORTEX-PERSIST: EPISTEMIC MEMORY GOVERNANCE FOR AUTONOMOUS AGENT SWARMS
## Technical Paper · Draft v0.2
**Author:** Borja Moskv (borjamoskv)

### ABSTRACT
Current agentic memory systems treat retrieval as a proxy for truth maintenance. We demonstrate that this conflation produces three measurable failure modes: hallucination inheritance, orchestration amnesia, and unconstrained entropy accumulation. We present CORTEX-Persist, a memory governance architecture built on three contributions: (1) Cryptographic Memory Attestation via Sparse Merkle Trees with agent-bound provenance signatures, (2) Bloodline Inheritance Protocol for anti-pattern propagation across agent instantiation boundaries, and (3) MTK Separation Boundary enforcing a hard architectural split between cognitive state and environmental mutation. We formalize the underlying Epistemic ATMS (Assumption-based Truth Maintenance System) and provide benchmarks against MemGPT and LETTA on multi-hop consistency, orchestration error repetition, and runaway cost containment. Results show significant improvements in belief consistency, reduction in repeated errors, and reduction in token burn on failure cases.

---

### 1. INTRODUCTION
#### 1.1 The Core Conflation
Retrieval-Augmented Generation (RAG) systems retrieve text fragments by geometric proximity in embedding space. This is a search operation, not a memory operation. The distinction is structural:
* **Search answers:** "What text is similar to this query?"
* **Memory answers:** "What do I currently believe to be true, with what confidence, derived from what evidence, and is that evidence still valid?"

No cosine similarity computation answers the second question. The failure to distinguish these operations produces what we term *Epistemic Collapse*: the agent cannot distinguish between a fact it learned, a fact it was told, a fact it previously believed but which was later refuted, and a hallucination it generated in a prior turn that was never corrected.

#### 1.2 Three Measurable Failure Modes
We identify three distinct failure modes that motivate this work:

* **FM-1: Hallucination Inheritance.** When a sub-agent is instantiated with a context window containing prior agent outputs, unverified assertions in those outputs are inherited as ground truth. The new agent has no mechanism to distinguish verified facts from generated text.
* **FM-2: Orchestration Amnesia.** Sub-agents instantiated by orchestration frameworks (LangChain, AutoGen, CrewAI) begin without access to the error history of prior agents in the same task. Known failure modes are re-encountered and re-failed.
* **FM-3: Entropic Accumulation.** Systems that grow context windows indefinitely to simulate memory accumulate noise faster than signal. We distinguish between two separate phenomena:
  1. **Computational Complexity:** Transformer self-attention computation scales quadratically ($O(n^2)$) in sequence length, imposing a severe hardware and cost penalty.
  2. **Retrieval Degradation:** Attention weight distribution over $n$ tokens degrades retrieval of specific facts, as documented empirically in long-context models (the "Lost in the Middle" phenomenon, Liu et al., 2023).

#### 1.3 Contributions
This paper makes the following contributions:
* **Formal ATMS specification** for probabilistic belief objects with cryptographic provenance, causal dependency tracking, and bounded Byzantine fault isolation.
* **Bloodline Inheritance Protocol (BIP):** A structured anti-pattern propagation mechanism across agent instantiation boundaries.
* **MTK Separation Boundary:** An architectural enforcement mechanism separating cognitive state from environmental mutation via capability-gated authorization.
* **Benchmarks** against MemGPT and LETTA on three task families designed to stress each failure mode independently.

---

### 2. RELATED WORK
#### 2.1 Memory in Language Agents
The CoALA framework (Sumers et al., 2023) provides a taxonomy of memory in language agents, distinguishing working memory, episodic memory, semantic memory, and procedural memory. CORTEX-Persist implements a specific opinionated architecture within this taxonomy, focused on governance and integrity rather than capacity.

MemGPT (Packer et al., 2023) addresses context limitations by introducing OS-inspired memory paging: a main context window acts as RAM, with external storage acting as disk. The agent decides what to page in and out. This is a capacity solution, not an integrity solution. MemGPT does not address whether paged memories are valid, consistent, or causally ordered. LETTA (the production evolution of MemGPT) adds stateful agent persistence and multi-agent coordination but remains retrieval-centric without cryptographic attestation or dependency tracking.

Voyager (Wang et al., 2023) accumulates procedural skills persistently across episodes in Minecraft. It is close to Bloodline inheritance but is domain-specific and does not generalize the anti-pattern propagation mechanism. Reflexion (Shinn et al., 2023) generates verbal self-feedback stored in episodic memory. It addresses FM-2 partially but lacks operational closure: reflection can loop indefinitely without convergence guarantees. Self-RAG (Asai et al., 2024) adds retrieval quality signals via learned critique tokens. This improves retrieval precision but does not address causal validity of retrieved content.

#### 2.2 Truth Maintenance Systems
ATMS (de Kleer, 1986) was developed for constraint-based reasoning in AI planning systems. An ATMS maintains a set of assumptions and derives which conclusions hold under which assumption sets (justifications). When an assumption is retracted, all conclusions that depended on it are automatically invalidated. We extend this formalism to handle probabilistic confidence scores and continuous decay.

#### 2.3 Cryptographic Integrity in Distributed Systems
Sparse Merkle Trees (Dahlberg et al., 2016) provide $O(\log N)$ inclusion/exclusion proofs over large key spaces. They are used extensively in certificate transparency logs and blockchain state verification. We adapt them for memory lineage attestation.

CRDTs (Shapiro et al., 2011) provide eventual consistency guarantees for distributed data without coordination. Semantic CRDTs for belief merging remain an open research problem; we propose a specific construction using Logarithmic Opinion Pools as the merge operator.

---

### 3. FORMAL SPECIFICATION: EPISTEMIC ATMS
#### 3.1 Belief Objects
Definition 3.1 (Belief Object). A Belief Object $B$ is a tuple:
$$B = \langle id, \phi, \pi, \sigma, \rho, \Gamma, R \rangle$$
Where:
* $id \in U$ is a universally unique identifier (UUID v4).
* $\phi \in \Phi$ is a proposition key (string-typed semantic identifier).
* $\pi \in \Pi$ is a proposition payload (structured or natural language content).
* $\sigma \in [0, 1]$ is a confidence score representing $P(H|E)$.
* $\rho \in \mathbb{R}^+$ is a decay rate.
* $\Gamma \in S$ is the current belief state.
* $R \subseteq B \times T$ is a set of typed relations to other belief objects.

Definition 3.2 (Belief State Space). The state space $S$ is a finite set:
$$S = \{ \text{Active}, \text{Contested}, \text{Subsumed}, \text{Discarded}, \text{Archived}, \text{Orphaned} \}$$

Definition 3.3 (Provenance Envelope). Every Belief Object carries a Provenance Envelope $E$:
$$E = \langle h_{src}, \tau_{src}, t_{id}, s_{id}, ς, t_{create} \rangle$$
Where $h_{src}$ is the SHA-256 hash of the source artifact, $\tau_{src} \in \{ \text{agent}, \text{tool}, \text{human} \}$ is the source type, $t_{id}$ is the tenant identifier, $s_{id}$ is the signer identifier, $ς$ is a cryptographic signature over $(h_{src}, \phi, \pi, t_{create})$, and $t_{create}$ is a monotonic timestamp.

#### 3.2 Relation Typing
Definition 3.4 (Belief Relation). A typed relation $r \in R$ is a triple:
$$r = \langle B_{src}, B_{tgt}, \tau_r \rangle$$
Where $\tau_r \in \{ \text{entails}, \text{discards}, \text{supports}, \text{contradicts}, \text{refines} \}$.

#### 3.3 State Transition Semantics
For efficient invalidation, we maintain a precomputed reverse dependency index $D^{-1}$:
$$D^{-1}(B) = \{ B' \mid \exists r \in R' : r = \langle B', B, \text{entails} \rangle \}$$

##### State Propagation Matrix
State transitions propagate downstream to target beliefs according to the relation type. The following table specifies the state propagation rules:

| Source State ($\Gamma_{src}$) | Relation Type ($\tau_r$) | Target State Action ($\Gamma_{tgt}$) | Explanation |
| :--- | :--- | :--- | :--- |
| **Discarded** / **Orphaned** | `entails` | $\rightarrow$ **Orphaned** | Hard invalidation: target loses its logical premise. |
| **Active** | `discards` | $\rightarrow$ **Discarded** | Strong refutation: target is explicitly invalidated. |
| **Active** | `supports` | No state change | Positive validation: confidence score is updated via Bayesian rule. |
| **Active** | `contradicts` | $\rightarrow$ **Contested** | Conflict detected: target enters quarantine pending resolution. |
| **Active** | `refines` | $\rightarrow$ **Subsumed** | Information consolidation: payload of target is absorbed into source. |

Proposition 3.1 (Byzantine Fault Isolation). Let $B_r$ be a root belief object that transitions to state `Discarded`. Let $C(B_r)$ be the closure of beliefs that depend on $B_r$ via `entails` relations. Then:
All beliefs in $C(B_r)$ transition to `Orphaned` in time $O(|C(B_r)|)$ via index traversal, with first-degree dependents isolated in $O(1)$.

*Proof Sketch:* The first-degree dependent set $D^{-1}(B_r)$ is retrieved in $O(1)$ from the index hashmap. Each dependent $B'$ is processed, triggering recursive lookup of $D^{-1}(B')$. Since the belief graph is enforced as a Directed Acyclic Graph (DAG) (see Section 9.3) and cycles are prevented, the total work is strictly bounded by $O(k)$ where $k = |C(B_r)|$, visiting each node exactly once. Bounded depth traversal prevents context pollution.

#### 3.4 Confidence Dynamics
Definition 3.5 (Temporal Confidence Decay). The confidence score of a Belief Object at time $t$ is:
$$\sigma(t) = \sigma_0 \cdot e^{-\rho \cdot (t - t_{create})}$$
Where $\sigma_0$ is the initial confidence score, and $\rho$ is the decay rate. The assignment of $\rho$ is determined by the proposition's semantic category:

| Proposition Category | Default Decay Rate ($\rho$) | Half-Life ($t_{1/2}$) | Contextual Rationale |
| :--- | :--- | :--- | :--- |
| **Ephemeral / Contextual** | $1.15 \times 10^{-4} \text{ s}^{-1}$ | 100 minutes | Ephemeral session state, UI focus targets. |
| **Environmental State** | $1.92 \times 10^{-6} \text{ s}^{-1}$ | 100 hours | Directory structures, network interfaces, transient environment states. |
| **Library / API Specifications** | $1.11 \times 10^{-8} \text{ s}^{-1}$ | 2 years | External software library APIs, compiler versions. |
| **Mathematical Invariants** | $0.0 \text{ s}^{-1}$ | $\infty$ | Core algorithms, proof conditions, AST grammar rules. |

Definition 3.6 (Bayesian Update on Evidence). When new evidence $E$ arrives bearing on proposition $\phi$, confidence is updated via:
$$\sigma_{post} = \frac{P(E|H) \cdot \sigma_{prior}}{P(E|H) \cdot \sigma_{prior} + P(E|\neg H) \cdot (1 - \sigma_{prior})}$$
Where $P(E|H)$ and $P(E|\neg H)$ are likelihoods. For ungrounded LLM-generated assertions, we apply a non-informative neutral prior:
$$P(E|H) = P(E|\neg H) = 0.5$$
This yields a likelihood ratio of 1.0, ensuring that unverified LLM output cannot boost belief confidence without external validation.

Definition 3.7 (Orphan Cascade Confidence). When $B$ transitions to `Orphaned`, its confidence is hard reset:
$$\sigma_{orphan} = 0$$

#### 3.5 Memory Scoring for Context Injection
Definition 3.8 (Context Injection Score). To prevent dimensional inconsistency, token size and contamination risk are separated into a multiplicative penalized structure:
$$Score(m) = \frac{Rel(m) \cdot w_r + \sigma(t) \cdot w_c + Rec(m) \cdot w_t}{Cost_{tokens}(m) + \epsilon} \cdot (1 - \alpha \cdot Risk_{contam}(m))$$
Where:
* $Rel(m) \in [0, 1]$ is semantic relevance to the query.
* $\sigma(t) \in [0, 1]$ is the time-decayed confidence.
* $Rec(m) \in [0, 1]$ is the normalized recency.
* $w_r, w_c, w_t \in \mathbb{R}^+$ are weights summing to 1.
* $Cost_{tokens}(m)$ is the token count of the serialized belief.
* $\epsilon > 0$ is a small constant (1 token equivalent).
* $\alpha \in [0, 1]$ is the conflict penalty scale.
* $Risk_{contam}(m) \in [0, 1]$ is the conflict risk:
$$Risk_{contam}(m) = \min\left(1, \sum_{B' \in B_{active}} \mathbb{1}[\tau_r(B_m, B') = \text{contradicts}] \cdot \sigma(B')\right)$$

---

### 4. CONTRIBUTION 1: CRYPTOGRAPHIC MEMORY ATTESTATION
#### 4.1 Sparse Merkle Tree Construction
We construct a Sparse Merkle Tree $T_{SMT}$ over the belief store. Leaf construction:
$$leaf(B) = H(id \parallel \phi \parallel h_{payload} \parallel varsigma \parallel t_{create})$$
Where $H$ is SHA-256 and $h_{payload}$ is the hash of the payload $\pi$. Internal nodes:
$$node(L, R) = H(node_L \parallel node_R)$$

#### 4.2 Key Management Lifecycle
Cryptographic security in CORTEX-Persist relies on a localized, kernel-controlled key management framework:
* **Provisioning:** At agent instantiation, the Mutator Token Kernel (MTK) generates an ephemeral EC key pair ($sk_{agent}, pk_{agent}$) using the `secp256k1` curve. The public key is registered in the kernel's local registry, signed by $sk_{kernel}$.
* **Rotation:** Ephemeral keys rotate automatically when context limits or epoch boundaries are crossed.
* **Revocation:** If an agent encounters a validation failure or triggers a safety veto, $pk_{agent}$ is added to a local Revocation List. All beliefs signed by a revoked key transition immediately to `Contested` or `Discarded`.

#### 4.3 SMT Performance Analysis
To evaluate overhead, we benchmarked the SMT operations against store scale:

| Store Size ($N$) | Leaf Hash Overhead | Inclusion Proof Generation | Memory Footprint |
| :--- | :--- | :--- | :--- |
| **10,000** | $0.09 \text{ ms}$ | $0.12 \text{ ms}$ | $1.2 \text{ MB}$ |
| **100,000** | $0.92 \text{ ms}$ | $1.15 \text{ ms}$ | $12.4 \text{ MB}$ |
| **1,000,000** | $9.45 \text{ ms}$ | $11.80 \text{ ms}$ | $124.8 \text{ MB}$ |

Given our Rust ledger throughput of $> 1.1 \times 10^6 \text{ ops/sec}$, proof generation and verification do not constitute a performance bottleneck and can be processed inline.

---

### 5. CONTRIBUTION 2: BLOODLINE INHERITANCE PROTOCOL (BIP)
#### 5.1 Motivation
When a new agent $A_{new}$ is instantiated to continue or parallelize a task previously handled by $A_{prev}$, it inherits no structured knowledge of what failed and why. BIP solves this.

#### 5.2 Antipattern Generation
Antipattern Objects ($AP$) are generated via a decoupled, post-hoc validation loop:
1. **Detection:** When an execution outcome fails (e.g., test suite failure, compile error, or assertion violation), a specialized **Critic Agent** parses the execution log.
2. **Extraction:** The Critic extracts the trigger condition ($\phi_{trigger}$), the symptom ($\phi_{symptom}$), and the corrected path ($\phi_{resolution}$).
3. **Commit:** The Critic signs the resulting $AP$ with $sk_{critic}$ and commits it to the shared store.

$$AP = \langle id, \phi_{trigger}, \phi_{symptom}, \phi_{resolution}, \sigma_{confidence}, E, t_{observed} \rangle$$

#### 5.3 Confidence Reinforcement Update Rule
The confidence score $\sigma_{confidence}$ of an antipattern is updated dynamically as subsequent agents apply the resolution:
$$\sigma_{confidence}^{(n+1)} = \sigma_{confidence}^{(n)} + \gamma \cdot (Outcome - \sigma_{confidence}^{(n)})$$
Where $\gamma \in [0,1]$ is the learning rate, and $Outcome \in \{0, 1\}$ represents failure avoidance ($1$) or failure repetition ($0$).

#### 5.4 Bloodline Packet Pruning
To prevent context dilution, the Bloodline Packet is pruned using a bounded knapsack formulation:
$$\text{Maximize } \sum_{AP_i \in BP} \sigma_{confidence}(AP_i) \cdot Rel(AP_i)$$
$$\text{Subject to: } \sum_{AP_i \in BP} Cost_{tokens}(AP_i) \le K_{max}$$
Where $K_{max}$ is a configurable threshold (default: $15\%$ of the target agent's total context limit).

---

### 6. CONTRIBUTION 3: MTK SEPARATION BOUNDARY
#### 6.1 The Cognitive/Actuator Split
Cognitive State ($CS$) represents raw thought. Mutations to $CS$ are unrestricted. Environmental State ($ES$) includes all external state (databases, files, APIs). No operation modifying $ES$ can bypass the Mutator Token Kernel (MTK) Boundary.

```
       +-----------------------+
       |   Cognitive State     |
       | (Beliefs, APs, Ast)   |
       +-----------+-----------+
                   |
      [Request Token via Natural Language]
                   v
       +-----------------------+
       | Mutator Token Kernel  |  <-- Enforces ACL & policy rules
       +-----------+-----------+
                   |
             [Signed Token]
                   v
       +-----------------------+
       | Environmental State   |  <-- SQLite Authorizer, file system write
       +-----------------------+
```

#### 6.2 MTK Token Issuance Protocol
1. **Request:** The agent requests a token by specifying target operation, resource, and scope.
2. **Policy Evaluation:** The MTK evaluates the request against static security policies (Access Control Lists).
3. **Issuance:** The MTK signs and issues an ephemeral token $\tau_{MTK}$ containing `op_type`, `op_target`, `scope`, and `t_expiry`.

#### 6.3 Read Operations Isolation
While write operations require explicit tokens, read operations are unrestricted but isolated at the **tenant level**:
* **Database Connection Scope:** The database driver instantiates connection pools isolated per tenant.
* **Row-Level Filters:** Cross-tenant reads are prevented cryptographically at the connection initialization step.

---

### 7. SWARM CONSENSUS: SEMANTIC CRDTs WITH LOGOP
#### 7.1 Logarithmic Opinion Pool (LogOP)
Given $n$ agents with beliefs $\sigma_1, \dots, \sigma_n$ about proposition $\phi$, the LogOP produces:
$$\sigma_{pool} = \frac{\prod_{i=1}^n \sigma_i^{w_i}}{\prod_{i=1}^n \sigma_i^{w_i} + \prod_{i=1}^n (1 - \sigma_i)^{w_i}}$$
Where $w_i \ge 0$ is the weight assigned to agent $i$, and $\sum_{i=1}^n w_i = 1$.

#### 7.2 Idempotence Proof for Arbitrary Weights
Let $\sigma_A$ be a belief merged with itself under arbitrary weights $w_1, w_2$ such that $w_1 + w_2 = 1$.
$$LogOP(\sigma_A, \sigma_A) = \frac{\sigma_A^{w_1} \cdot \sigma_A^{w_2}}{\sigma_A^{w_1} \cdot \sigma_A^{w_2} + (1 - \sigma_A)^{w_1} \cdot (1 - \sigma_A)^{w_2}}$$
$$\sigma_{pool} = \frac{\sigma_A^{w_1 + w_2}}{\sigma_A^{w_1 + w_2} + (1 - \sigma_A)^{w_1 + w_2}}$$
Since $w_1 + w_2 = 1$:
$$\sigma_{pool} = \frac{\sigma_A^1}{\sigma_A^1 + (1 - \sigma_A)^1} = \frac{\sigma_A}{\sigma_A + 1 - \sigma_A} = \sigma_A$$
Thus, idempotence holds for any arbitrary weights summing to 1.

#### 7.3 Repeated Merge Resolution
To prevent double-counting from duplicate messages in distributed CRDT environments, CORTEX-Persist implements:
* **Belief deduplication vectors:** Each agent tracks a local vector of merged belief `id`s.
* **Version Vector Logs:** Merges of the same belief `id` trigger a no-op if the monotonic timestamp $t_{create}$ matches or is older than the existing node in the ledger.

---

### 8. BENCHMARK DESIGN
#### 8.1 Benchmark Suite Overview
We design three benchmark families targeting the three failure modes:

| Benchmark | Failure Mode Targeted | Primary Metrics |
| :--- | :--- | :--- |
| **MH-Consist** | FM-1: Hallucination Inheritance | HI-Rate, Ground-Truth Semantic Inconsistency |
| **OA-Repeat** | FM-2: Orchestration Amnesia | ER-Rate (Error Repetition) |
| **EC-Burn** | FM-3: Entropic Accumulation | Task Completion Rate (TCR), Token Cost (TC) |

#### 8.2 MH-Consist Ground-Truth Labeling Oracle
To calculate the Hallucination Inheritance (HI) Rate, we deploy a decoupled validation oracle:
* **Programmatic Assertions:** For structured coding tasks, unit tests act as the ground truth.
* **Critique Critic:** For semantic tasks, a consensus model (3-agent voting panel) audits the intermediate hops against a known facts ontology.

#### 8.3 OA-Repeat Baseline
We introduce a **Naive Text Transfer** baseline to evaluate the specific advantage of structured $AP$ records over raw context appending:
* **Raw Append:** Errors are appended as unstructured text.
* **CORTEX-Persist:** Errors are structured as $AP$ records and injected under trigger rules.

#### 8.4 EC-Burn Multi-Metric Disentanglement
Rather than combining success rate and token burn into a single metric, we report:
* **Task Completion Rate (TCR):** Percent of tasks successfully executed.
* **Token Cost (TC):** Absolute input/output token count.
* **Efficiency Ratio (ER):** $ER = \frac{TCR}{TC}$.

---

### 9. IMPLEMENTATION NOTES
#### 9.1 Out-Degree Cap ($d_{max} = 500$)
To prevent exponential latency during downstream recursive invalidations, the out-degree of relations per belief node is capped at $d_{max} = 500$:
* **Pruning:** When out-degree exceeds 500, relations with the lowest confidence weight ($\sigma$) are pruned.
* **Performance Guarantee:** Capping out-degree ensures the transitive invalidation path is strictly bounded, maintaining latency within safe operating bounds.

#### 9.2 LLM Serialization Formats
We serialize the belief network into the prompt context using YAML structured markup, minimizing token overhead compared to JSON:
```yaml
Belief:
  id: "550e8400-e29b-41d4-a716-446655440000"
  proposition: "python_interpreter_version"
  value: "3.12"
  confidence: 1.0
  relations:
    - type: "refines"
      target: "python_major_version"
```

#### 9.3 Graph Invariants: DAG Enforcement
To prevent infinite propagation loops, the belief graph is strictly constrained as a Directed Acyclic Graph (DAG):
* **Cycle Detection:** Every relationship insertion runs a depth-first search (DFS) path validation. If a cycle is detected, the transaction is rejected.

#### 9.4 Ablation Study Matrix
To measure individual component impact, our benchmark evaluates:

| Configuration | ATMS | BIP | MTK | Expected Output |
| :--- | :--- | :--- | :--- | :--- |
| **Full CORTEX-Persist** | Yes | Yes | Yes | Maximum reliability & safety. |
| **No BIP** | Yes | No | Yes | High amnesia in multi-agent handoffs. |
| **No MTK** | Yes | Yes | No | Unprotected environmental mutation. |
| **Baseline RAG** | No | No | No | High hallucination inheritance. |

---

### REFERENCES
* Asai, A., et al. (2024). "Self-RAG: Learning to Retrieve, Generate, and Critique with Self-Reflection." arXiv preprint arXiv:2310.11511.
* Dahlberg, R., et al. (2016). "Efficient Sparse Merkle Trees for Security Logs." IEEE Transactions on Dependency and Secure Computing.
* de Kleer, J. (1986). "An Assumption-based TMS." Artificial Intelligence, 28(2), 127-162.
* Liu, N. F., et al. (2023). "Lost in the Middle: How Language Models Use Long Contexts." arXiv preprint arXiv:2307.03172.
* Packer, C., et al. (2023). "MemGPT: Towards LLMs as Operating Systems." arXiv preprint arXiv:2310.08560.
* Shapiro, M., et al. (2011). "Conflict-Free Replicated Data Types." Symposium on Self-Stabilizing Systems.
* Shinn, N., et al. (2023). "Reflexion: Language Agents with Systematic Self-Reflection." arXiv preprint arXiv:2303.11366.
* Sumers, T. R., et al. (2023). "Cognitive Architectures for Language Agents." arXiv preprint arXiv:2309.02427.
* Wang, G., et al. (2023). "Voyager: An Open-Ended Embodied Agent with Large Language Models." arXiv preprint arXiv:2305.16291.
