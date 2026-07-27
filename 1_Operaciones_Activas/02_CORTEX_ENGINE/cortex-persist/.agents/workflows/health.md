---
cat_id: health
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Health \u2014 Estado de salud r\xE1pido del ecosistema completo."
---



# 💚 HEALTH — Ecosystem Health

// turbo-all

```bash
# Git
git status --short | wc -l
# Tests
pytest tests/ --maxfail=1 --timeout=60 -q 2>&1 | tail -3
# Lint
ruff check . 2>&1 | wc -l
# Skills
for d in ~/.gemini/antigravity/skills/*/; do [ -f "$d/SKILL.md" ] || echo "MISSING: $(basename $d)"; done
# Workflows
ls .agent/workflows/*.md 2>/dev/null | wc -l
```

Report: 🟢 Healthy | 🟡 Degraded | 🔴 Critical

> **Skills:** `sovereign-sre-omega`, `BABYLON60-Guard-Omega`
