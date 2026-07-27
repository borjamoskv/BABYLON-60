<!-- C5-REAL EXERGY CERTIFIED -->
# Ultrathink Adapters

This directory contains external integrations and adapters for the `ultrathink` system.

## Included Adapters
- **codex-ultrathink**: Adapter for OpenAI Codex models.
- **claude-ultrathink**: Adapter for Anthropic Claude models.
- **antigravity-ultrathink**: Adapter for Google Antigravity SDK with **Nodo 4 JIT Skill Routing**.

## Architecture (Nodo 4 Integration)

The `antigravity-ultrathink` adapter is the first adapter to integrate with the
Secretario (Nodo 4) skill router. Instead of loading all 103+ skills into a
single monolithic context, it:

1. Receives an operator intent (natural language goal)
2. Routes the intent through `secretary_router.py` to select ≤3 optimal skills
3. Injects only the selected skills into the ULTRATHINK P0 prompt
4. Launches a subagent via the Antigravity SDK with the focused prompt

*These packages were formerly standalone in the `10_PROJECTS` workspace but have been consolidated into the BABYLON-60 monorepo for centralized management.*
