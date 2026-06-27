# Antigravity Skills Tree

This directory is the local source of truth for the Antigravity skills catalog.

## Status Model

- `canonical`: the primary skill directory for a named capability.
- `alias-only`: a compatibility alias that should resolve to a canonical sibling and should not grow its own implementation.
- `local-stub`: a local wrapper that points to a canonical sibling while still carrying an executable script.
- `docs-only`: a documented capability with no bundled local implementation script.
- `script-backed`: a normal skill with a local implementation script and no special alias semantics.

## Machine Entry Points

- `python3 validate_skills_tree.py`
  Validates YAML front matter, local script targets, and the resolution contract.

- `python3 resolve_skill.py <skill-name> --pretty`
  Resolves a skill name into its execution contract: canonical, alias-only, local-stub, docs-only, or script-backed.

- `python3 resolve_skill.py --all`
  Emits the full machine-readable resolution table for all local skills.

- `python3 build_skills_inventory.py`
  Rebuilds the inventory artifacts and the fully resolved catalog from the current tree and the resolution contract.

## Consumer Rule

- Runtime consumers should use `skills_catalog.json` or `resolve_skill.py`, not ad hoc directory scraping.
- `engines/autopoiesis/governor.py` already consumes `skills_catalog.json` and skips `alias-only` directories by default.
- Historical notes, archived plans, and scratch scripts may still mention raw `SKILL.md` scanning; do not treat those as the current contract.

## Generated Artifacts

- `SKILLS_INVENTORY.md`
  Human-readable inventory snapshot.

- `skills_inventory.json`
  Machine-readable inventory snapshot.

- `skills_resolution.json`
  Canonical/alias/docs-only resolution contract used by tooling.

- `skills_catalog.json`
  Fully resolved per-skill catalog for tooling that wants a static export instead of running `resolve_skill.py`.

## Usage Tracking (Evidence-Based Lifecycle)

Every skill invocation MUST be recorded. After 30 days of data, skills with `count=0` are archived; skills with `count>10` are prioritized for refinement. Decisions based on evidence, not intuition.

- `python3 usage_tracker.py record <skill_name>`
  **MANDATORY.** Call this every time a skill's SKILL.md is read for task execution.

- `python3 usage_tracker.py stats`
  Show all usage counts, last-used timestamps, and active status.

- `python3 usage_tracker.py recommend --days 30`
  Generate archive/refine recommendations based on the configured window.

- `python3 usage_tracker.py reset <skill_name>`
  Reset a skill's counter (use after major refactoring).

**Agent Mandate:** When you read a `SKILL.md` file with `IsSkillFile: true`, you MUST also execute `python3 usage_tracker.py record <skill_dir_name>` in the same turn. No exceptions.

**Data Store:** `usage_ledger.json` — centralized, append-only, capped at 100 timestamps per skill.

## Operating Rule

Do not delete duplicate or docs-only directories casually. First update `skills_resolution.json`, then validate the tree, then rebuild the inventory.
