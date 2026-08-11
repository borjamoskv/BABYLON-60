# 🎵 TONNETZ App (`tonnetz_app/`)

[![EU AI Act](https://img.shields.io/badge/EU_AI_Act-Article_14_Human_Oversight-purple?style=for-the-badge)](../docs/03_guides/tonnetz_audit_guide.md)
[![Neo-Riemannian](https://img.shields.io/badge/Theory-Neo--Riemannian_Toric_Graph-blue?style=for-the-badge)](https://en.wikipedia.org/wiki/Tonnetz)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen?style=for-the-badge)]()

**TONNETZ App** is a standalone, browser-based Neo-Riemannian spatial harmonic visualizer and generative audit interface. It serves as the primary visual debugging interface for **EU AI Act Article 14 (Human Oversight)** compliance within BABYLON-60, mapping high-dimensional model drift and cognitive state transitions into a 2D/3D toric harmonic grid.

---

## 🎼 Theoretical Foundation

The *Tonnetz* (German for "tone network") is a two-dimensional lattice diagram representing tonal space. In BABYLON-60:
1. **Parallel (P)**, **Leading-tone exchange (L)**, and **Relative (R)** Neo-Riemannian transformations model continuous state trajectories.
2. **Generative Seed System**: Enter any alphanumeric seed (e.g., `BILBAO-60`) to generate deterministic harmonic maps.
3. **Drift Detection**: Sudden shifts in harmonic trajectory correspond to semantic hallucination or out-of-bounds agent execution, giving human auditors instantaneous visual intuition.

---

## ⚡ Quick Start

No build steps required. `tonnetz_app` is built with pure zero-dependency vanilla HTML5, CSS3, and JavaScript.

```bash
# Option 1: Open directly in your default browser (macOS)
open tonnetz_app/index.html

# Option 2: Serve via any static web server
python3 -m http.server 8080 --directory tonnetz_app
```

Then visit `http://localhost:8080` in your web browser.

---

## 🛠️ Controls & Parameters

- **Semilla (Seed)**: Input deterministic seed (e.g. `BILBAO-60`) for reproducible trajectory generation.
- **Tonalidad (Key)**: Select root key ($A, C, E, \dots$) and mode (Major / Minor).
- **Forma (Structural Form)**: Choose arrangement templates (`techno: A A B A B C B A C`, `house: A B A C A B`).
- **Harmonic Spatial Grid**: Interactive Canvas visualizing chordal nodes, fifth/third intervals, and trajectory tension.

---

## 📁 File Structure

```
tonnetz_app/
├── index.html          # Application structure & UI controls
├── style.css           # Premium Industrial Noir Dark Theme stylesheet
└── script.js           # Neo-Riemannian math engine & Canvas renderer
```

---

<sub>BABYLON-60 Tonnetz Substrate · Human Oversight (Art. 14) · Borja Moskv</sub>
