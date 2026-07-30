# CORTEX Asset Taxonomy (CAT-60) Standard

This document establishes the CAT-60 standard for distinguishing and classifying the different execution and configuration assets in the CORTEX persistence substrate.

---

## 1. Rationale
Without a rigorous taxonomy, the system incurs cognitive entropy when determining whether a file is a deterministic script, an autonomous agent, a manual/agentic workflow, or a dynamic capability extension (skill). Standardization collapses this uncertainty.

---

## 2. Asset Type Definitions

| Asset Type | Primary Extension | Execution Model | Typical Location | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Agent** | `.yaml` | Stateful LLM loop with tools and persona | `babylon60/extensions/agents/definitions/` | Autonomous reasoning & execution |
| **Workflow** | `.md` | Step-by-step sequential playbook | `.agent/workflows/` or `.agents/workflows/` | Process orchestration / sequence guide |
| **Skill** | `SKILL.md` (dir) | Instruction package + resources | `skills/` or config path | Capabilities expansion for agents |
| **Script** | `.py` / `.sh` | Deterministic programmatic execution | `scripts/` or `tools/` | Atomic file, DB or OS mutation |
| **Policy** | `.md` | Static ruleset constraints | Root or configuration directory | Behavioral guardrails and invariants |

---

## 3. Metadata Specification (YAML Header)

To enforce standardization, all structural assets MUST include a YAML metadata block.

### 3.1 Markdown Assets (Workflows, Skills, Policies)
Must begin with a YAML frontmatter block:

```yaml
---
cat_id: "my-workflow"
cat_type: "workflow"
version: "1.0.0"
reality_level: "C5-REAL"
owner: "borjamoskv"
exergy_tier: "P1"
dependencies: []
---
```

### 3.2 YAML Assets (Agents)
Must include the metadata block directly in the root keys:

```yaml
metadata:
  cat_id: "demiurge"
  cat_type: "agent"
  version: "1.0.0"
  reality_level: "C5-REAL"
  owner: "borjamoskv"
  exergy_tier: "P0"
```

### 3.3 Python Assets (Scripts)
Must declare metadata at the start of the module docstring:

```python
# [C5-REAL] Exergy-Maximized
"""
cat_id: "validate-taxonomy"
cat_type: "script"
version: "1.0.0"
reality_level: "C5-REAL"
owner: "borjamoskv"
exergy_tier: "P2"
"""
```

---

## 4. Verification & Validation Protocol
Every asset committed to the repository must be checked against this taxonomy to avoid state degradation. The validation script parses these headers to ensure alignment.
