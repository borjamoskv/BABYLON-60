#!/usr/bin/env bash
# ============================================================
# Purga de historia git — BABYLON-60
# Objetivo: reducir .git de 9,2 GB (packs con binarios) a <100 MB
# ⚠️  EJECUTAR CON EL SWARM/DAEMON PARADO. Reescribe TODA la historia.
#     Después requiere force-push y que cualquier clon se re-clone.
# Uso: bash scripts/purge_git_history.sh
# ============================================================
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
BACKUP="$HOME/BABYLON-60-backup-$(date +%Y%m%d-%H%M).git"

command -v git-filter-repo >/dev/null 2>&1 || pip3 install git-filter-repo

# 1) Backup espejo completo (imprescindible, no lo saltes)
git clone --mirror "$REPO" "$BACKUP"
echo "✅ Backup en $BACKUP"

cd "$REPO"
git worktree prune

# 2) Top 20 blobs más pesados de la historia (informativo, revisa antes de seguir)
echo "--- Blobs más pesados en la historia ---"
git rev-list --objects --all |
  git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' |
  awk '/^blob/ {print $3, $4}' | sort -rn | head -20
read -rp "¿Continuar con la purga? [y/N] " ok; [[ "$ok" == "y" ]] || exit 1

# 3) Purga: todo blob >5 MB + media conocida, de TODA la historia
git filter-repo --force \
  --strip-blobs-bigger-than 5M \
  --path-glob '*.wav' --path-glob '*.mp4' --path-glob '*.mov' \
  --path naroa_archive --path VIDEOS \
  --invert-paths

# 4) Compactar
git reflog expire --expire=now --all
git gc --prune=now --aggressive
echo "--- Tamaño final de .git ---"
du -sh .git

# 5) filter-repo elimina los remotes: restaurar y publicar (manual, coordinado)
git remote add origin git@github.com:borjamoskv/BABYLON-60.git
cat <<'EOF'
Siguiente paso (manual, cuando estés seguro):
  git push --force --all origin
  git push --force --tags origin
Si quieres media versionada en el futuro, usa git-lfs ANTES de re-añadirla:
  git lfs install && git lfs track '*.wav' '*.mp3' '*.mp4'
EOF
