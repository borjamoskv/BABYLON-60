---
name: ANTIGRAVITY-GITHUB-OMEGA
description: Sovereign GitHub MCP protocol. C5-REAL reality level forced. Zero-entropy repository mutations.
script: scripts/antigravity__github__omega.py
---

# ANTIGRAVITY-GITHUB-OMEGA v4.0.0-CRONOS

## 0. COGNITIVE SUBSTRATE
- **Axiom AX-041**: Git repository = Immutable Database.
- **Reality Level**: C5-REAL (Transactional, verifiable, irreversible mutations).
- **Aesthetic**: Industrial Noir 2026. Zero decorative prose.

> [!IMPORTANT]
> **Integrity Directive P0 (Law Ω₉)**: All remote mutations (push, merge, branch) REQUIRE deterministic local C5-REAL validation (tests/lints passing) before execution. NEVER bypass.

## 1. INFRASTRUCTURE & ACCESS
- **Config Path**: `$CORTEX_ROOT/.gemini/antigravity/mcp_config.json`
- **Required Scopes**: `repo`, `workflow`, `admin:org`

```json
{
  "mcpServers": {
    "github": {
      "command": "bun",
      "args": ["$CORTEX_ROOT/.gemini/antigravity/mcp-server-github"],
      "env": { "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_***" }
    }
  }
}
```

## 2. MCP ARSENAL (EXERGY MAPPING)

| Tool | Input Schema | Reality Level | Purpose |
|---|---|---|---|
| `mcp_github_push_files` | `owner`, `repo`, `branch`, `files`, `message` | **C5-REAL** | Atomic multi-file injection. (Preferred over single-file updates). |
| `mcp_github_create_or_update_file` | `owner`, `repo`, `path`, `content`, `message`, `branch`, `sha` | **C5-REAL** | Surgical single-file mutation. `sha` mandatory for updates. |
| `mcp_github_create_branch` | `owner`, `repo`, `branch`, `from_branch` | **C5-REAL** | Topological bifurcation. |
| `mcp_github_merge_pull_request` | `owner`, `repo`, `pull_number`, `merge_method` | **C5-REAL** | Mainnet consolidation. |
| `mcp_github_create_pull_request` | `owner`, `repo`, `title`, `head`, `base`, `body` | **C5-REAL** | Formal C5-REAL mutation proposal. |
| `mcp_github_add_issue_comment` | `owner`, `repo`, `issue_number`, `body` | **C5-REAL** | A2A/Human interface. |
| `mcp_github_get_file_contents` | `owner`, `repo`, `path`, `branch` | *C4-SIM* | Structural extraction. |
| `mcp_github_list_commits` | `owner`, `repo`, `sha`, `page`, `perPage` | *C4-SIM* | Temporal archaeology / Audit. |
| `mcp_github_search_repositories` | `query`, `page`, `perPage` | *C4-SIM* | Dependency/adversary detection. |

## 3. GIT-LEDGER WRITE PROTOCOL (SAGAS)

**Execution Rule**: Always prefer atomic batches (`push_files`) over sequential `update_file` to minimize rate limits and temporal desync.

1. **SAGA-1 (Local Validation)**: Run project-specific build/lint tools locally.
2. **SAGA-2 (Collision Control)**: Fetch current state `sha` via `mcp_github_get_file_contents` before single-file updates.
3. **SAGA-3 (Atomic Injection)**: Batch changes via `mcp_github_push_files`.
4. **SAGA-4 (Governance)**: Open PR documenting C5-REAL validation status.

## 4. OUROBOROS STRIKE (AUTOMATED WORKFLOW)

```yaml
Workflow: Ouroboros_Strike
Steps:
  - Recon: "mcp_github_get_file_contents -> Extract target state (C4-SIM)."
  - Isolate: "mcp_github_create_branch -> Branch feature/* or bugfix/* (C5-REAL)."
  - Inject: "mcp_github_push_files -> Push locally validated payload (C5-REAL)."
  - Govern: "mcp_github_create_pull_request -> Append [Reality Status: C5-REAL (Checked via local tests)] (C5-REAL)."
  - Sentinel: "Run `git status`. If dirty, run `git add . && git commit -m 'feat: ...'`. (C5-REAL)."
```

## 5. RESOLUTION MATRIX

| Error Code | Action Vector (C5-REAL) |
|---|---|
| `401 Bad credentials` | Rotate PAT in `mcp_config.json` -> Restart MCP. |
| `404 Not Found` | Verify `owner/repo` exact string match. Validate PAT permissions. |
| `409 Conflict` | Fetch latest `sha` via `get_file_contents`. Resolve conflicts in PR branch. |
| `403 Rate Limit` | Group mutations into `push_files`. Implement exponential backoff. Cache reads. |

> [!WARNING]
> **Git Sentinel (R4 Global Rule)**: After ANY local code manipulation preceding a GitHub operation, run `git status`. If dirty state is detected, propose or execute a Conventional Commit command immediately.
