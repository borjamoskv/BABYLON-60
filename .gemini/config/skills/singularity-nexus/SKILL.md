---
name: singularity-nexus
role: APEX
version: 3.0.0
scale: '1'
cost_tier: low
description: The Sovereign Singularity Nexus Engine. Orchestrates cross-project unification,
  git health checks, ghost synchronization, code patterns bridging, and cross-domain
  DB mutations.
script: verify_singularity-nexus.py
triggers: [nexus, pulse, ghosts, bridge, sync]
---

# Singularity-Nexus Skill
Sovereign cross-project synchronization and unification hub. Implements `cortex nexus` command tree.

## Actions:
- `pulse`: Health status of all projects in `$CORTEX_ROOT/10_PROJECTS`.
- `ghosts`: Sync project activity to ghosts.json.
- `bridge`: Bridge patterns from one project to another using explicit physical symlinks (Nexus Bridging Ω6).
- `sync`: Automates ghosts syncing + pulse auditing.
- `lea-purge`: Orchestrates the Purge Cluster (`Thermodynamic-Context-Compression-OMEGA` -> `LEA-OMEGA`) to prevent context competition and token burn.
- `crystallize-loop`: Executes Alliance A (`Divergence-Anchor` -> `Thermodynamic-Context-Compression` -> `Architect` -> `Session-Crystallizer`) mapping raw divergence into executable JSON.
- `autopoiesis-loop`: Executes Alliance B (`Genesis-L5` -> `Sortu-APEX` -> `OUROBOROS-∞`) for autonomous substrate evolution.
- `web-swarm`: Executes Alliance C (Parallel unbundled Web C5-REAL optimization via `Browser-CDP` + memory/LCP/a11y) with explicit Worktree Isolation (Σ8) via branch/share mode.
- `capital-compute-loop`: Executes Alliance D (`Zero-Employee-Orchestrator` -> `Architect` -> `Vesicular-Runtime` -> `Genesis-L5`) mapping pure capital intent to fully outsourced, credential-isolated infrastructure deployment with explicit Worktree Isolation (Σ8).
- `macrofago-purge`: Invokes the Macrófago Ontológico (Π2) to force apoptosis on Framework Bloat exceeding 25K LOC.
- `adversarial-truth-loop`: Executes Alliance E (`Honest-Check` -> `Grill-Me` -> `Agent-Paper-RedTeam` -> `Frontier-RevEng`) enforcing absolute epistemic rigor by attacking assumptions, extracting the true blueprint, and validating against SOTA.
- `cognitive-exergy-loop`: Executes Alliance F (`Divergence-Anchor` -> `Autocognition` -> `Session-Crystallizer`) analyzing the token exergy of captured divergence and permanently crystallizing high-yield paths.
