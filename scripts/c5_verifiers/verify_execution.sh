#!/bin/bash
# verify_execution.sh
# Validador transaccional post-ejecución

set -e

echo "=== Verificador de Ejecución Transaccional ==="

# Las rutas de git son relativas a la raíz del repositorio: trabajar siempre desde ella.
cd "$(git rev-parse --show-toplevel)"

# 1. Verificar si hay cambios sin commit, incluidos archivos no versionados (C0005).
#    Contrato: solo los patrones de los ficheros .gitignore del repositorio excluyen archivos.
#    .git/info/exclude y core.excludesFile NO ocultan nada aquí.
PENDING=$(git status --porcelain --untracked-files=no)
UNTRACKED=$(git ls-files --others --exclude-per-directory=.gitignore)
# Marcas que hacen que git ignore cambios en archivos versionados (skip-worktree, assume-unchanged).
HIDDEN_FLAGS=$(git ls-files -v | grep -E '^[Sa-z] ' || true)
if [ -n "$PENDING" ] || [ -n "$UNTRACKED" ] || [ -n "$HIDDEN_FLAGS" ]; then
    echo "⚠️ CAMBIOS SIN COMMIT DETECTADOS."
    [ -n "$PENDING" ] && echo "$PENDING"
    [ -n "$UNTRACKED" ] && echo "$UNTRACKED" | sed 's/^/?? /'
    [ -n "$HIDDEN_FLAGS" ] && echo "$HIDDEN_FLAGS" | sed 's/^/[cambios ocultos por skip-worktree o assume-unchanged] /'
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
if command -v sha256sum >/dev/null 2>&1; then
    hash_file() { sha256sum "$1"; }
else
    hash_file() { shasum -a 256 "$1"; }
fi
# Rutas separadas por NUL: nombres con espacios no se parten. --root cubre el commit inicial.
while IFS= read -r -d '' file; do
    if [ -f "$file" ]; then
        hash_file "$file"
    else
        echo "[Archivo eliminado/movido]: $file"
    fi
done < <(git diff-tree --root --no-commit-id --name-only -r -z HEAD)

echo "=============================================="
echo "Ejecución auditada correctamente."
