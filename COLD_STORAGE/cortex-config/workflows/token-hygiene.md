---
description: Monthly token budget audit — prevent system prompt bloat
---
# Token Hygiene Audit

Run monthly or when sessions start hitting 200K token limits.

## 1. Quick Check (Audit)
// turbo
1. Count active skills, workflows, and total description bytes using `/bin/bash`:
```bash
/bin/bash -c '
echo "=== TOKEN HYGIENE AUDIT ==="
echo "Skills: $(ls -d ~/.gemini/antigravity/skills/*/ 2>/dev/null | grep -v _archived | wc -l)"
echo "Workflows: $(find ~/.agent/workflows ~/.agents/workflows -maxdepth 1 -name "*.md" 2>/dev/null | wc -l)"
echo "Global GEMINI.md: $(wc -c < ~/.gemini/GEMINI.md 2>/dev/null || echo "Not found")"
echo "Workspace GEMINI.md: $(wc -c < ./GEMINI.md 2>/dev/null || echo "Not found")"
echo -n "Total Skill Bytes: "
find ~/.gemini/antigravity/skills -not -path "*/_archived/*" -name "SKILL.md" -exec wc -c {} + | tail -1
echo "=== HEAVIEST SKILLS ==="
for d in ~/.gemini/antigravity/skills/*/; do if [ -f "$d/SKILL.md" ]; then echo -n "$d: "; wc -c < "$d/SKILL.md"; fi; done | sort -nr -k2 | head -n 5
'
```

## 2. Threshold Constraints (The Law of Exergy Ω2)
- **GEMINI.md**: must be <12KB (~3K tokens). Violations must be compressed immediately.
- **Active Skills**: must be <45 (each adds ~100-500 tokens).
- **Active Workflows**: must be <30.
- **Top 5 Heaviest Skills**: Should not exceed 8KB each unless strictly P0 paths.

## 3. Remediation (If over threshold)
2. Compress `description:` frontmatter fields to <100 chars (The system prompt directly injects the description).
3. Find longest `SKILL.md` documents and summarize internal rules or move logs/examples to Knowledge Items.
4. Identify dormant skills (e.g., L1 Clusters like Navier-Stokes if not used) and archive them:
```bash
mkdir -p ~/.gemini/antigravity/skills/_archived
# Replace NAME with the skill name to archive
# mv ~/.gemini/antigravity/skills/NAME ~/.gemini/antigravity/skills/_archived/
```
5. Manually compress massive SKILL.md files: collapse examples, inline tables, remove redundant prose. Target 0% fact-loss structural compression.

## 4. Recovery
```bash
# Restore a skill:  mv ~/.gemini/antigravity/skills/_archived/NAME ~/.gemini/antigravity/skills/
# Restore a workflow: mv ~/.agent/workflows/_archived/NAME.md ~/.agent/workflows/
# Restore GEMINI.md: cp ~/.gemini/GEMINI.md.backup-YYYYMMDD-HHMMSS ~/.gemini/GEMINI.md
```
