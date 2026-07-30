---
description: "Consolidar Estado — Snapshot del estado actual del proyecto para persistencia."
---

# 📸 CONSOLIDAR-ESTADO — State Snapshot

// turbo-all

## Paso 1 — Git State
```bash
git status --short
git log --oneline -5
git branch -a --sort=-committerdate | head -5
```

## Paso 2 — Quality Metrics
```bash
ruff check . 2>&1 | wc -l
pytest tests/ --maxfail=3 --timeout=60 -q 2>&1 | tail -5
```

## Paso 3 — Context Snapshot
Document: open tasks, blockers, next actions, key decisions.

## Paso 4 — Persist
Save to BABYLON60 Ledger and/or Knowledge Item.

> **Skills:** `Cognitive-Crystallizer-Omega`
