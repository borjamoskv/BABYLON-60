# Skills Inventory

Last updated: 2026-06-06

## Summary

- Total skill directories audited: `35`
- Skill manifests with parseable YAML front matter: `35`
- Script-backed skills: `10`
- Documentation-only skills: `25`
- Missing local script links in manifests: `0`
- Residual references to `$CORTEX_ROOT/30_CORTEX`, `compiled_skills`, or `worktrees/sigint-monitor-fix`: `0`

## Duplicate Clusters

- None

## Documentation-Only Skills

- `API-Provider-OMEGA`
- `API-Sentinel-OMEGA`
- `Agent-Paper-RedTeam-OMEGA`
- `Alpha-Target-OMEGA`
- `Antigravity-Github-Omega`
- `Autodidact-Research-OMEGA`
- `Autonomous-Audit-OMEGA`
- `Browser-CDP-Automation-OMEGA`
- `C5-DEATH-OMEGA`
- `Cortex-Live-Broadcaster`
- `Cortex-Research-Loop-OMEGA`
- `Crystallize-Knowledge-JIT`
- `Deep-Research-SOTA-Edition-OMEGA`
- `Episodic-Memory-OMEGA`
- `Exergy-Engine-OMEGA`
- `Ouroboros-Strike-OMEGA`
- `UI-Mechanisms-Rule`
- `accidental-data-loss-prevention`
- `agente-sota`
- `borja-moskv-ultrathink`
- `dios`
- `filologa-de-combate`
- `managing-python-dependencies`
- `ouroboros-infinity`
- `skill-repair`

## Script-Backed Skills

- `Aesthetic-Foundry-Omega` → `scripts/aesthetic_foundry_omega.py`
- `Apollo-Autodidact-OMEGA` → `scripts/autodidact.py`
- `Apollo-Extractor-OMEGA` → `scripts/extract.py`
- `Autodidact-21EDO-OMEGA` → `scripts/engine_21edo.py`
- `Autodidact-History-OMEGA` → `scripts/retrieve_history.py`
- `Estado-Del-Arte-OMEGA` → `scripts/sota_forge.py`
- `Mac-Control-OMEGA` → `scripts/mac_control_omega.py`
- `P2P-Comms-OMEGA` → `scripts/send_p2p_email.py`
- `Python-Extractor-OMEGA` → `scripts/sovereign_python_extractor.py`
- `Sortu-APEX` → `scripts/sortu.py`

## Resolution Snapshot

- `canonical`: None
- `alias_only`: None
- `local_stubs`: None

## Next Decisions

1. Canonicalize duplicate clusters and decide whether alias directories should remain human-readable markers or be removed entirely.
2. Decide whether documentation-only skills are valid product surfaces or should be marked archived/non-executable.
3. Regenerate any external registry that consumes this tree so it matches the repaired local manifests.
4. Use `resolve_skill.py` and `validate_skills_tree.py` as the machine entrypoints instead of scraping manifests ad hoc.
