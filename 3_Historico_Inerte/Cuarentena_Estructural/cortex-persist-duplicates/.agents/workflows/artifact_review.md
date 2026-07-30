---
cat_id: artifact_review
cat_type: workflow
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
---
# 🔄 Artifact Review & Multi-Model Approval Workflow

This document defines the strict gate verification procedure for evaluating artifacts and code changes generated across the multi-repo workspace structure.

---

## 1. 📋 Pre-mutation Review Checklist

Before any code modification is merged or committed:

### 1.1 Architectural Planning (Gemini 3 Pro)
- [ ] Has an `implementation_plan.md` been generated?
- [ ] Are all affected files and symbols mapped to clickable links using the format: `[basename](file:///absolute/path/to/file#Lline)`?
- [ ] Have all open questions been identified and answered by the operator or the belief engine?

### 1.2 Code Implementation (Claude 4.6 / Claude 3.5 Sonnet)
- [ ] **No server comments in client files:** Ensure Astro/TSX files do not contain Python-style `# C5-REAL` comments. Use `//` or `/* */` (Rule R11).
- [ ] **No bare prints or sleep states:** Ensure no `print()` or síncrono `time.sleep()` is present in async paths.
- [ ] **Decimals over floats:** Verify that financial calculations or scoring methods use `Decimal` instead of `float`.
- [ ] **SQLite WAL integrity:** Verify that any SQLite concurrent access uses WAL mode and a `busy_timeout` of `5000ms`.

### 1.3 Testing Verification (Gemini 3.5 Flash)
- [ ] Has a test suite verifying the change been written?
- [ ] Did the tests execute successfully with exit code 0 (`pytest` or `vitest`)?

---

## 2. 🚦 Parallel Pipeline Orchestration

To run a multi-agent parallel synthesis:
1. **Spawn Planning Agent:** Read codebase AST, output plan.
2. **Review Gate:** Plan must be reviewed by the validator (or user review policy).
3. **Spawn Execution Agent & Test Writer Agent:**
   - Execution Agent constructs code changes in memory or workspace files.
   - Test Writer Agent designs testing coverage in parallel.
4. **Integration Gate:** Run tests. If tests fail, rollback and trigger self-healing loop (apopotosis / ouroboros).
5. **Sentinel Gate:** Git Sentinel commits mutational state: `git commit -m "[bridge] <msg>"`.
