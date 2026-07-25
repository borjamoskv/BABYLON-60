#!/usr/bin/env bash
set -e

echo "⚡ [C5-REAL] Iniciando Brutalismo Cinético (INV_C5_20)..."

# 1. Dropping Mach VM caches
echo "Purgando Mach VM caches..."
osascript -e 'do shell script "purge"' || echo "Advertencia: Requiere privilegios elevados para purga profunda, mitigado."

# 2. Aggressively wiping redundant local repository caches
echo "Erradicando entropía térmica (__pycache__, target)..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
# Evitar borrar el .venv principal, pero borrar basuras de rust (target) si no es moskv-1-apex
find . -type d -name "target" -path "*/proof_kernel/*" -exec rm -rf {} + 2>/dev/null || true

echo "🟢 Purga Cinética completada."
