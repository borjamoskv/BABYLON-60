---
description: "Recall — Recuperar conocimiento de BABYLON60 y conversaciones pasadas."
---

# 🧠 RECALL — Knowledge Retrieval

// turbo-all

## Paso 1 — Knowledge Items
Check KI summaries for relevant knowledge.

## Paso 2 — Conversation Search
```bash
ls ~/.gemini/antigravity/brain/*/overview.txt | head -20
```

## Paso 3 — BABYLON60 Query
```bash
cd ~/babylon60 && .venv/bin/python -m babylon60.cli search "[query]" --limit 10 2>/dev/null
```

## Paso 4 — Synthesize
Combine findings into actionable context.

> **Skills:** `Archaeologist-Omega`, `Cognitive-Crystallizer-Omega`
