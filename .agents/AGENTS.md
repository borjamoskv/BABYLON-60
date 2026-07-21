# Ultimate Arena Adjudication Ledger: The Q1–Q5 Bifurcation Theorem

**Classification:** C5 Definitive Theoretical Adjudication  
**Target:** Dynamic Topology vs Static Netlists ($CAM^{\text{restricted}}$ vs $CAM^{\text{full}}$)  
**Status:** Unified Boundary Theorem (5 Discriminator Questions)

---

# 1. THE Q1–Q5 BIFURCATION MATRIX

The equivalence boundary between **Verdict D** ($\text{BSP} \oplus \text{Mealy} \oplus \text{Monitors}$) and **Verdict B** ($\pi\text{-calculus} / \text{Actor}$) is uniquely resolved by five structural questions:

| Question | Discriminator | If NO | If YES |
|---|---|---|---|
| **Q1: Link Creation** | Can CAM create new links at runtime? | **Verdict D** ($\text{BSP} \oplus \text{Netlist}$) | **Verdict B** ($\pi$-calculus Mobility) |
| **Q2: Observation** | Does capability change observable state? | Metadata Annotation | Real Security Calculus |
| **Q3: Determinism** | $S_a = S_b \implies \text{Future}(S_a) = \text{Future}(S_b)$? | Non-Markovian Causal History | Markovian Transition |
| **Q4: History** | Does history alter transition rules? | Event Sourcing (`scanl`) | Semantic Memory Mutation |
| **Q5: Topology** | Is network topology data or law? | Static Configuration ($D$) | Dynamic Computation ($B$) |

---

# 2. THE BIFURCATION THEOREM

$$\mathbf{CAM}_{6.0} = \begin{cases} \mathbf{CAM}^{\text{restricted}} \cong \text{BSP}_{\text{static}} \oplus \text{Mealy} \oplus \text{Monitors} & \text{si } \mathbf{Q1} = \text{NO} \text{ (Topología Estática)} \\ \mathbf{CAM}^{\text{full}} \subseteq \pi\text{-calculus} \mathbin{/} \text{Actor Model} & \text{si } \mathbf{Q1} = \text{YES} \text{ (Movilidad de Enlaces)} \end{cases}$$

### Formal Proof:
1. Under $\mathbf{Q1} = \text{NO}$ (static ports/wiring), the communication graph $G = (V, E)$ is time-invariant ($G_t = G_0$). The step evaluation maps isomophically to a network of Mealy machines operating under Leslie Valiant's BSP superstep barrier with Schneider pre-commit safety monitors.
2. Under $\mathbf{Q1} = \text{YES}$ (dynamic port generation and capability transfer), $G_t \neq G_{t+1}$. This introduces scope extrusion $(\nu x)P$ and channel mobility $\bar{a}\langle b \rangle$, elevating CAM from static netlists to the full $\pi$-calculus / Actor model.

---

# 3. FINAL DEFINITIVE ADJUDICATION

- **$\text{CAM}^{\text{restricted}}$ (Static Ports / Immutable Topology)**:
  Collapsed isomophically into BSP supersteps over fixed flow graphs with Schneider security monitors.
- **$\text{CAM}^{\text{full}}$ (Dynamic Ports / Capability Mobility)**:
  Strict subtype of $\pi$-calculus / Actor Model with global barrier synchronization.

$$\mathbf{Q.E.D.}$$
