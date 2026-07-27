---
cat_id: steal
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
description: "Steal \u2014 An\xE1lisis competitivo y asimilaci\xF3n de patrones externos."
---



# 🕵️ STEAL — Competitive Extraction

// turbo-all

## Step 1 — Target Identification
What system/project to analyze?

## Step 2 — Structural Extraction
```bash
# Clone shallow
git clone --depth 1 [repo_url] /tmp/analysis_target
# Analyze
find /tmp/analysis_target -name "*.py" -o -name "*.js" | xargs wc -l | sort -rn | head -20
```

## Step 3 — Pattern Catalog
Identify: architecture, design patterns, API surface, quality practices.

## Step 4 — Assimilate
Translate relevant patterns into BABYLON60-native implementations.

## Step 5 — Clean Up
```bash
rm -rf /tmp/analysis_target
```

> **Skills:** `x-copy-omega`, `agent-landscape-omega`
