---
cat_id: organizar
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Organizar \u2014 Reorganizar estructura de archivos, m\xF3dulos, y workspace."
---



# 📁 ORGANIZAR — Workspace Organization

// turbo-all

## Paso 1 — Audit Structure
```bash
find . -maxdepth 2 -type d | head -40
find . -name "*.py" | wc -l
find . -name "__pycache__" -type d | wc -l
```

## Paso 2 — Identify Entropy
- Orphan files
- Misplaced modules
- Duplicate directories
- Stale caches

## Paso 3 — Reorganize
Move files to correct locations. Update imports.

## Paso 4 — Clean Caches
```bash
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null
```

## Paso 5 — Verify
```bash
python3 -c "import babylon60" && pytest tests/ --maxfail=3 --timeout=60 -q
```

> **Skills:** `BABYLON60-Guard-Omega`
