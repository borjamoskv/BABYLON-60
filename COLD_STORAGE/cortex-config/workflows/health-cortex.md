---
description: Health Cortex — Unified System Diagnostic & Recovery Protocol
---

# 🩺 Health Cortex v1 — Sovereign System Integrity

// turbo-all

Diagnóstico, reparación y evaluación rápida de infraestructura MOSKV-1, conexiones MCP y recursos críticos.

---

## Paso 1 — Autodiagnóstico Activo

### 1A. MCP Connection Status (The Cortex Nerves)
```bash
# Test CORTEX CLI is functional
cortex --version

# Test Git connectivity
git status 2>&1 | head -5
```

### 1B. CORTEX DB Integrity
```bash
# Verify DB exists and is queryable
sqlite3 ~/.cortex/cortex.db "SELECT count(*) as total_facts FROM facts" 2>&1
sqlite3 ~/.cortex/cortex.db "PRAGMA integrity_check" 2>&1
```

### 1C. Memory Filesystem Integrity
```bash
/bin/bash -c '
echo "=== MEMORY HEALTH ==="
for f in ghosts.json system.json mistakes.jsonl bridges.jsonl; do
  if [ -f "$HOME/.agent/memory/$f" ]; then
    echo "✅ $f ($(wc -c < "$HOME/.agent/memory/$f")B)"
  else
    echo "❌ $f MISSING"
  fi
done
echo "Projects: $(ls "$HOME/.agent/memory/projects/" | wc -l) files"
echo "Capsules: $(ls "$HOME/.agent/memory/capsules/" | wc -l) files"
echo "Snapshots: $(ls "$HOME/.agent/memory/snapshots/" | wc -l) files"
'
```

### 1D. Rendimiento Termodinámico (Exergy Load)
```bash
# Top memory consumers
top -l 1 -o mem | head -15

# Zombie processes
ps aux | grep -E "defunct|zombie" | grep -v grep

# Port collisions (common dev ports)
lsof -ti :3000 2>/dev/null && echo "⚠️ Port 3000 in use" || echo "✅ Port 3000 free"
```

### 1E. Skills & Workflows Integrity
```bash
/bin/bash -c '
echo "=== SKILLS & WORKFLOWS ==="
echo "Skills: $(ls -d ~/.gemini/antigravity/skills/*/ 2>/dev/null | wc -l)"
echo "Workflows: $(find ~/.agent/workflows -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)"
echo "GEMINI.md: $(wc -c < ~/.gemini/GEMINI.md 2>/dev/null || echo "Not found")"
'
```

---

## ⚡ Recovery Actions

If a port or OS operation is paralyzed:
1. Kill port: `lsof -ti :<PORT> | xargs kill -9 2>/dev/null`
2. Purge Python cache: `find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null`
3. Purge Node cache: `rm -rf node_modules package-lock.json && npm install`

---

## Reporte Final
```text
🩺 HEALTH CORTEX — SYSTEM REPORT
✅ CORTEX CLI: [version]
✅ CORTEX DB: [N] facts, integrity [OK/FAIL]
✅ Memory FS: [N/N] files present
✅ Core Exergy: [OK / OVERLOAD] (Zombies: [N])
✅ Skills: [N] active | Workflows: [N] active
```
