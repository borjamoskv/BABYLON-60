#!/usr/bin/env bash
# SORTU-APEX: DEATH PROTOCOL CRON JOB
# Execution Level: C5-REAL
# Este script escanea directorios por archivos inactivos y ejecuta políticas de purga severa.

WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
echo "[C5-REAL] Executing Sortu-APEX Death Protocol scan in $WORKSPACE_DIR"

# Umbral: 7 días de inactividad
THRESHOLD_DAYS=7

# Busca ramas, scripts o archivos que no han sido modificados en 7 días
INACTIVE_FILES=$(find "$WORKSPACE_DIR" -type f -mtime +$THRESHOLD_DAYS ! -path '*/\.*' ! -path '*/node_modules/*')

if [ -z "$INACTIVE_FILES" ]; then
    echo "[C5-REAL] Zero entropy detected. No files flagged for TOMBSTONE."
    exit 0
fi

echo "[CRITICAL] The following files exceed the TTL of $THRESHOLD_DAYS days and yield zero exergy:"
echo "$INACTIVE_FILES"

# Movemos los inactivos a una cuarentena (o TOMBSTONE) para cumplir el Death Protocol
mkdir -p "$WORKSPACE_DIR/cortex/tombstone"

while IFS= read -r file; do
    basename_file=$(basename "$file")
    mv "$file" "$WORKSPACE_DIR/cortex/tombstone/${basename_file}.archived"
    echo "[TOMBSTONED] $file -> Purged from active working tree."
done <<< "$INACTIVE_FILES"

echo "[C5-REAL] Death Protocol execution complete. Workspace exergy preserved."
