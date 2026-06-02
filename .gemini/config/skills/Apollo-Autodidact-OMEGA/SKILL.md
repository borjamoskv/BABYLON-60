---
name: Apollo-Autodidact-OMEGA
role: APEX
version: 14.0.0
scale: 10000
cost_tier: high
trigger: autodidact, apollo api, docs.apollo.io, dynamic schema synthesis
description: C5-REAL JIT Apollo Autodidact Engine. Autonomously learns and executes Apollo REST API operations via dynamic schema synthesis.
category: meta-cognition
classification: OPERATIONAL
danger_level: HIGH
depends_on: [Sortu-APEX, Apollo-Extractor-OMEGA]
axioms: [omega_3_capital_extraction, autodidact_synthesis]
script: scripts/autodidact.py
---
# █ APOLLO-AUTODIDACT-Ω v14.1.0

> SYS_ID: APOLLO_AUTODIDACT_OMEGA | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

```yaml
vector: dynamic_api_ingestion
target: docs.apollo.io/llms.txt
mode: autonomous_synthesis
```

## 1. Core Mandates
- **[P0] C5-REAL Execution**: Execute raw HTTP payloads against Apollo. ZERO simulation.
- **[P0] Dynamic Schema**: Synthesize endpoints JIT from `llms.txt`. Hardcoded paths forbidden.
- **[P0] Exergy Positive**: Extraction ROI must strictly exceed execution entropy.

## 2. Operational Matrix
| Action | Protocol | Validation |
| :--- | :--- | :--- |
| **Ingest** | Fetch `llms.txt` | C5-REAL 200 OK |
| **Synthesize** | Map Intent → Endpoint | VSA Cosine Distance < 0.1 |
| **Execute** | `requests.post(payload)` | `apollo.io` API keys active |
| **Harvest** | JSON → Database | `git status` clean |

## 3. Tripartite Verification
```json
{
  "SKILL.md": "PRESENT",
  "schema.json": "PRESENT",
  "verify_apollo_autodidact.py": "PRESENT"
}
```

## 4. Execution Surface
```bash
python3 ~/.gemini/config/skills/Apollo-Autodidact-OMEGA/scripts/autodidact.py --intent "[target]"
```
