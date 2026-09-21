---
name: c5-alpha-extraction-pipeline
description: Protocol to extract high-exergy algorithmic alpha from arXiv and GitHub directly from raw sources (LaTeX/Git) bypassing PDFs, followed by LARSA-120 formalization.
---

# C5-REAL Alpha Extraction Pipeline (Caza de Alpha)

When the Sovereign Operator requests to "hunt alpha" or extract asymmetrical value from the environment (either to harvest advanced math, or to detect and neutralize regulatory/bureaucratic friction like the EU AI Act), you MUST execute the following pipeline.

## 1. Thermodynamic Ingestion (The Scan)
Use raw APIs to query the environment. Do not use UI-bound tools.
- **arXiv API (Math / Theory):** Query `http://export.arxiv.org/api/query?search_query={target}&sortBy=submittedDate&sortOrder=descending`
- **GitHub API (Code / Implementation):** Search for repos created in the last 48h to catch code before it goes mainstream (`https://api.github.com/search/repositories?q=created:>{date}+{target}&sort=updated`).

## 2. Exergy Evaluation
Do not present raw search results. Filter the nodes strictly by using an Exergy / Thermodynamic grading system.
- **High Exergy Triggers (+ Points):** `causal`, `thermodynamic`, `lock-free`, `topology`, `zero-knowledge`, `neurosymbolic`, `invariant`, `scitt`, `homomorphic`.
- **Anergy Triggers (- Points):** Boilerplate "AI slop" or bureaucratic overhead (`delve into`, `seamless`, `comprehensive`, `compliance`, `mandatory`).
- **Score:** Calculate a proxy metric combining keyword presence and Shannon Entropy, mapping to the `0 - 21000` scale.

## 3. Deep Acople (INV_C5_DEEP_ACOPLE)
Never download PDFs to parse research.
- Select the node with the highest Exergy.
- **For arXiv:** Extract the raw source code via `https://arxiv.org/e-print/{arxiv_id}`. Decompress the `.tar.gz` and parse the `.tex` files specifically looking for `\begin{equation}`, `\begin{algorithm}`, or core struct/axioms.
- **For GitHub:** Run `git clone --depth 1` into the `scratch/` folder and read the primary Rust/C++ files.

## 4. LARSA-120 Execution (The Formal Triad)
Do not stop at just displaying the math or code. You must lock it into the engine to close the loop:
1. **Ring-0 (Thermodynamics):** Implement the math/algorithm as a standalone C-ABI or Rust PoC (Zero-Friction, `src/bin/` or `scripts/c5_demos/`). 
2. **Ring-1 (Epistemology):** Write a Lean 4 theorem to mathematically prove the Rust logic is sound. You MUST use computable functions (`Bool`) and verify by computational reflection (`by decide` or `eq_of_beq`), satisfying the Curry-Howard Isomorphism.
