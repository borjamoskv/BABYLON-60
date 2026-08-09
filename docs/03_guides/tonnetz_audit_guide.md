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

<sub>BABYLON-60 v4.0 · Human Oversight Guide · Borja Moskv</sub>
