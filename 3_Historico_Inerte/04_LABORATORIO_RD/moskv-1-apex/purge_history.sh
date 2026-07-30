#!/usr/bin/env bash
# ============================================================
# purge_history.sh — Purga de datos sensibles del historial git
# Repo: moskv-1-apex (copia buena: ~/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/moskv-1-apex)
# Generado: 2026-07-13 tras auditoría
#
# ORDEN CORRECTO (no lo alteres):
#   1. Repo a PRIVADO en GitHub (Settings → Danger Zone)  ← ANTES de esto
#   2. Rotar pq_seed.key                                   ← ANTES de esto
#   3. Ejecutar este script
#   4. git push --force origin master  (línea final, comentada)
#
# NOTA: aunque hagas force-push, los commits viejos quedan
# cacheados en GitHub hasta su GC. Con el repo ya privado el
# riesgo baja; para purga total pide a GitHub Support que
# ejecute GC del repo. Clones/forks ajenos conservan todo.
# ============================================================
set -euo pipefail
cd "$(cd "$(dirname "$0")" && pwd)"

# --- Precondiciones ---
command -v git-filter-repo >/dev/null 2>&1 || pip3 install git-filter-repo
# (ignora untracked: auditoría, este script y pycache no bloquean)
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "ABORT: hay cambios tracked sin commitear."; exit 1; }

# --- Backup completo antes de reescribir ---
git bundle create ../moskv-1-apex-pre-purge-$(date +%Y%m%d_%H%M%S).bundle --all
echo "Backup bundle creado en el directorio padre."

# --- Purga ---
# BLOQUE A: dossier fiscal / legal (todas las ubicaciones históricas)
# BLOQUE B: secretos (clave PQ, .env de payment_gateway)
# BLOQUE C: bases de datos con estado personal
# BLOQUE D: documentos personales (blog TDAH y el_espacio_entre_nosotros
#   confirmados para purga el 2026-07-13)
# BLOQUE E: media pesado (todo wav/mp4/m4a/mov/mp3 del historial;
#   elimina también remix_project/*.wav de HEAD — regenerables con htdemucs)
# BLOQUE F: bloat (node_modules y target de rust en historial, no en HEAD)
git filter-repo --force --invert-paths \
  --path Dossier_Abogado_BorjaMoskv.zip \
  --path archive/legacy/Dossier_Abogado_BorjaMoskv.zip \
  --path Dossier_Defensa_Fiscal \
  --path archive/legacy/Dossier_Defensa_Fiscal \
  --path docs/INFORME_FISCAL_ABOGADO.md \
  --path core/moskv-1/docs/INFORME_FISCAL_ABOGADO.md \
  \
  --path kernel/crypto/pq_seed.key \
  --path core/moskv-1/kernel/crypto/pq_seed.key \
  --path payment_gateway/.env \
  \
  --path cortex.db \
  --path swarm_os.sqlite \
  --path-glob 'cortex_dag.sqlite*' \
  \
  --path-glob '*el_espacio_entre_nosotros*' \
  --path-glob 'archive/legacy_omega.tar.gz*' \
  --path apps/cortex_blog/entries/2026-06-18-termodinamica-del-tdah.md \
  \
  --path-glob '*.wav' \
  --path-glob '*.mp4' \
  --path-glob '*.m4a' \
  --path-glob '*.mov' \
  --path-glob '*.mp3' \
  \
  --path-regex '(^|/)node_modules/' \
  --path-regex '(^|/)rust_core/target/'

# --- filter-repo elimina los remotes: restaurar origin ---
git remote add origin git@github.com:borjamoskv/moskv-1-apex.git

# --- Resultado ---
git gc --prune=now --aggressive 2>/dev/null || git gc --prune=now
echo "=== Tamaño final ===" && du -sh .git
echo "=== Verificación: debe salir vacío ==="
git log --all --pretty=format: --name-only | sort -u | grep -iE 'dossier|INFORME_FISCAL|pq_seed|\.env$|\.wav$|\.mp4$' || echo "OK: cero restos sensibles"

# --- PASO FINAL (manual, tras confirmar lo de arriba) ---
# filter-repo reescribe TODAS las ramas locales (master, home-final,
# feat/novela, home-final-snapshot, refactor/archive-amputation):
# el dossier desaparece de home-final y de tu disco (queda en el bundle).
# master (ex-b1f8c36) sigue siendo la copia buena consolidada.
# git push --force origin --all
# git push --force origin --tags
