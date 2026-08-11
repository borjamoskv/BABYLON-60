---
title: Supervisión Humana mediante Visualización Armónica Tonnetz
status: Causal-Determinist
version: 4.0.0
---

# Supervisión Humana mediante Visualización Armónica de Decisiones (`tonnetz_app/`)

**Guía de Auditor y Supervisor para la Visualización del Espacio de Estado y Disonancia del Agente**

> BABYLON-60 v4.0 Sovereign Hardened · Guía de Cumplimiento EU AI Act Artículo 14

---

## 1. Concept: Why Harmonic Visualization?

Complex autonomous agent networks generate multi-dimensional state transitions that are difficult for human supervisors to audit in real time. Reading raw text logs or JSON arrays during high-frequency execution leads to **auditor fatigue** and missed hallucinations.

`tonnetz_app/` solves this by projecting agent decision space into a **Neo-Riemannian Tonnetz** — a 2D geometric lattice used in music theory to represent pitch relationships and harmonic transformations.

```
       C ─── G ─── D
      ╱ ╲   ╱ ╲   ╱ ╲
     E ─── B ─── F# ─ A
    ╱ ╲   ╱ ╲   ╱ ╲
   G# ── D# ── A# ─ C#
```

In BABYLON-60:
- **Consonant Triads (Major/Minor Chords):** Represent stable, causal state transitions verified by the Merkle DAG Ledger.
- **Dissonant Interval Shifts (Augmented/Diminished Triads):** Visually and acoustically flag context rot, limerence loops, or anomalous state jumps *before* execution commits.

---

## 2. Launching `tonnetz_app/`

`tonnetz_app/` is a lightweight, zero-dependency HTML5/CSS3/JS visualizer located in the monorepo:

```bash
# Open directly in browser
open tonnetz_app/index.html
```

Or serve via local HTTP:

```bash
python3 -m http.server 8080 --directory tonnetz_app
# Navigate to http://localhost:8080
```

---

## 3. Auditor Workflow & Key Visual Signals

### 3.1 Consonant Trajectories (Nominal Execution)
When the agent executes instructions under strict F60 exactness:
- The lattice highlights smooth, adjacent triadic movement (e.g., C Major → A Minor → F Major).
- The exergy indicator remains steady.
- **Auditor action:** No intervention required.

### 3.2 Dissonant Jumps (Context Rot & Hallucination Flag)
If an ungrounded state jump occurs:
- The lattice displays a sharp chromatic collision across non-adjacent vertices (e.g., C Major → F# Minor / Tritone jump).
- The visualizer highlights the node in high-contrast red.
- **Auditor action:** Pause execution or trigger `QUARANTINE_AND_FREEZE` via the IDE interface.

---

## 4. Statutory Compliance (EU AI Act Article 14)

Article 14 requires that human supervisors be enabled to:
1. Fully understand the system's capacities and limitations.
2. Remain aware of the possible tendency to automatically rely on system outputs (automation bias).
3. Correctly interpret system outputs.
4. Intervene or override system decisions at any moment.

`tonnetz_app/` satisfies Article 14 by providing an intuitive, real-time geometric interface that makes anomalous agent behavior instantly visible to non-technical human controllers.

---

## 5. Popperian Falsification & Landauer Thermodynamic Bound

Under the **C5-REAL Epistemological Constitution**, visual harmonic mapping ($T: \mathrm{Kl}(\mathcal{D}) \to \mathbf{Tonnetz}$) is an *observational heuristic*, not a formal proof of correctness.

### 5.1 Functor Infidelity (Non-Injectivity Lemma)
The projection functor $T$ collapses distinct stochastic belief states $q_1 \neq q_2$ into identical triadic nodes on the toric lattice ($T(q_1) = T(q_2)$). Therefore, harmonic consonance alone does **not** guarantee semantic validity.

### 5.2 Landauer Exergy Dissipation Limit
To prevent false-negative safety passes, BABYLON-60 couples the visual grid with exact thermodynamic exergy dissipation tracking in `babylon60-kernel`:

$$\Delta \Xi \ge k_B T \ln(2) \cdot D_{\mathrm{KL}}(p \parallel q)$$

- **Nominal Execution ($D_{\mathrm{KL}} < \epsilon$):** Consonant lattice trajectory, $\Delta \Xi \approx 0$.
- **Hallucinated State ($D_{\mathrm{KL}} \ge \epsilon$):** Exergy surge triggers an immediate `Step::critical_halt` in Rust, independent of UI display state.

Run the empirical falsification verification:
```bash
python3 scripts/verify_tonnetz_falsification.py
```

---

<sub>BABYLON-60 v4.0 · Human Oversight Guide · Borja Moskv</sub>

