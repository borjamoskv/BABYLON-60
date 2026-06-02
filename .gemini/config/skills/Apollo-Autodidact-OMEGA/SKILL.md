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

# APOLLO-AUTODIDACT-Ω v14.0.0

> *"The API is not a static endpoint. It is a surface area to be dynamically ingested and conquered."*

Forged via Sortu-APEX from intent: `"autodidact sortu apex https://docs.apollo.io/"`

This skill implements a dynamic, self-updating API client for Apollo.io. It leverages the OpenAPI specifications and `llms.txt` documentation from `docs.apollo.io` to self-synthesize query schemas, rate-limit governance, and extraction logic without hardcoded static endpoints.

## Tripartite Validation
- [x] SKILL.md
- [x] schema.json
- [x] verify_apollo_autodidact.py

## Core Directives
1. **Dynamic Ingestion:** Reads the live Apollo documentation to map endpoints dynamically.
2. **C5-REAL Execution:** Executes real HTTP requests against Apollo API. No SIM.
3. **Exergy Yield:** Must extract leads, enrich contacts, or query CRM data with positive ROI.

## Execution
Use `python3 ~/.gemini/config/skills/Apollo-Autodidact-OMEGA/scripts/autodidact.py`
