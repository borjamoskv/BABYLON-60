# C5-REAL EXERGY CERTIFIED
#!/bin/bash
# verify_execution.sh
# Validador transaccional post-ejecución

set -e

echo "=== Verificador de Ejecución Transaccional ==="

# 1. Verificar si hay cambios sin commit
if ! git diff --quiet || ! git diff --cached --quiet; then
    echo "⚠️ CAMBIOS SIN COMMIT DETECTADOS."
    echo "El modelo ha alterado el disco, pero no ha cristalizado la acción (Git Sentinel falló)."
    echo "Fuerza un commit antes de proceder."
    exit 1
fi

# 2. Obtener último commit hash
LAST_HASH=$(git log -1 --pretty=format:"%H")
echo "✅ Repositorio Limpio."
echo "✅ Último Hash: $LAST_HASH"

# 3. Listar archivos alterados en el último commit y sus SHA256 (Deterministic Proof)
echo "✅ Archivos mutados en el último commit y sus pruebas criptográficas (SHA256):"
FILES=$(git diff-tree --no-commit-id --name-only -r HEAD)
for file in $FILES; do
    if [ -f "$file" ]; then
        sha256sum "$file"
    else
        echo "[Archivo eliminado/movido]: $file"
    fi
done

echo "=============================================="
echo "Ejecución auditada correctamente."
