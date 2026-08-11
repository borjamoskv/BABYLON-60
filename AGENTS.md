# C5-REAL Governance & Agentic Rules

Importing root workspace AGENTS.md governance.
See [Workspace AGENTS.md](file:///Users/borjafernandezangulo/10_PROJECTS/.agents/AGENTS.md)

---

## 🌿 Git Branching & Remote Push Governance

- **Active Branch Awareness**: When providing `git push` recommendations, agents MUST account for the user's active working branch. If commits exist on a feature/working branch (e.g. `iter1/*`), provide the complete merge sequence to update `main` before pushing to `origin/main`:
  ```bash
  git checkout main
  git merge <working-branch>
  git push origin main
  git checkout <working-branch>
  ```
- **Stale Lock Recovery**: If git operations fail due to `.git/*.lock` files, purge stale locks safely (`rm -f .git/HEAD.lock .git/index.lock .git/objects/maintenance.lock`) before repeating the command.

