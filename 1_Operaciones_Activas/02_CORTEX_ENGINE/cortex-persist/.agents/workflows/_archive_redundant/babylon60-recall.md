---
description: "BABYLON60 Recall — Deep memory retrieval from the BABYLON60 Ledger."
---

# 🧬 BABYLON60-RECALL — Deep Ledger Retrieval

// turbo-all

## Paso 1 — Semantic Search
```bash
cd ~/babylon60 && .venv/bin/python -m babylon60.cli search "[query]" --limit 20 2>/dev/null
```

## Paso 2 — Type-Specific Search
```bash
cd ~/babylon60 && .venv/bin/python -m babylon60.cli search "type:decision" --limit 10 2>/dev/null
cd ~/babylon60 && .venv/bin/python -m babylon60.cli search "type:error" --limit 10 2>/dev/null
cd ~/babylon60 && .venv/bin/python -m babylon60.cli search "type:meta_learning" --limit 10 2>/dev/null
```

## Paso 3 — Cross-Reference with KIs
Read relevant Knowledge Item artifacts.

> **Skills:** `Cognitive-Crystallizer-Omega`, `Specialized-Vectors-Omega`
