---
cat_id: enterrar
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Enterrar \u2014 Archive and deprecate modules, features, or approaches."
---



# ⚰️ ENTERRAR — Archive & Deprecate

## Step 1 — Identify Candidate
What is being deprecated? Why?

## Step 2 — Document
Create deprecation notice with: reason, alternatives, timeline.

## Step 3 — Move to Archive
```bash
mkdir -p _archived/[module]
git mv [module] _archived/[module]/
git commit -m "chore(archive): move [module] to _archived [CORTEX-TAINT:archive]"
```

## Step 4 — Update References
Remove imports, update docs, fix tests.

## Step 5 — Verify
```bash
pytest tests/ --maxfail=3 --timeout=60 --tb=short
```

> **Skills:** `Archaeologist-Omega`
