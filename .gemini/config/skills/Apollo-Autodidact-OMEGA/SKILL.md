---
name: Apollo-Autodidact-OMEGA
role: APEX
version: 14.0.0
scale: 10000
cost_tier: high
trigger: autodidact, apollo api, docs.apollo.io, dynamic schema synthesis
description: C5-REAL JIT Apollo Autodidact Engine. Autonomously synthesizes endpoints from docs.apollo.io.
category: meta-cognition
classification: OPERATIONAL
danger_level: HIGH
depends_on: [Sortu-APEX, Apollo-Extractor-OMEGA]
axioms: [omega_3_capital_extraction, autodidact_synthesis]
script: scripts/autodidact.py
---
# █ APOLLO-AUTODIDACT-Ω

> STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
vector: dynamic_api_ingestion
target: docs.apollo.io/llms.txt
mode: autonomous_synthesis
```

## 1. MANDATES
- **C5-REAL**: HTTP payloads against Apollo API. Zero simulation.
- **Dynamic**: Synthesize endpoints JIT via `llms.txt`. Hardcoded paths forbidden.
- **Exergy**: Extraction ROI > execution entropy.

## 2. MATRIX
| Action | Protocol | Validation |
|---|---|---|
| Ingest | Fetch `llms.txt` | HTTP 200 |
| Synthesize | Map Intent → Endpoint | VSA Cosine < 0.1 |
| Execute | HTTP POST | Valid API Key |
| Harvest | JSON → DB | `git status` clean |

## 3. VERIFICATION
```json
{"SKILL.md":"PRESENT","schema.json":"PRESENT","verify_apollo_autodidact.py":"PRESENT"}
```

## 4. SURFACE
```bash
python3 scripts/autodidact.py --intent "[target]"
```
