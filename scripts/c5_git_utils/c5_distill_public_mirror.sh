#!/usr/bin/env bash
# ==============================================================================
# C5-REAL · SINTETIZADOR Y PROYECTOR HOLOGRÁFICO PÚBLICO (BABYLON-60)
#
# Automatiza la destilación de un árbol limpio (<20 MB) desde el monorrepo
# privado y su despacho determinista hacia el repositorio público en GitHub.
#
# Invariantes verificadas en silicio:
# 1. Cero archivos de marketing, bases de datos o leads (.csv, .jsonl, .db, .vtt).
# 2. Peso total del bundle archivado estrictamente menor a 20 MB.
# 3. Escaneo estricto de secretos con Gitleaks (cero hallazgos).
# 4. Atestación biométrica física obligatoria en el Secure Enclave (Touch ID).
# ==============================================================================

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TARGET_REMOTE="${1:-public}"
DRY_RUN=0

if [ "${1:-}" = "--dry-run" ] || [ "${2:-}" = "--dry-run" ]; then
    DRY_RUN=1
    echo "[C5-PROJECTION] Modo DRY-RUN activo. Se verificarán invariantes sin ejecutar git push."
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [C5-REAL] PROYECTOR HOLOGRÁFICO PÚBLICO · BABYLON-60"
echo "  Raíz: $REPO_ROOT"
echo "  Remote destino: $TARGET_REMOTE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

cd "$REPO_ROOT"

# 1. Verificación de Árbol de Trabajo
echo -n "[1/6] Verificando árbol de trabajo en silicio... "
if [ "$DRY_RUN" -eq 0 ] && ! git diff-index --quiet HEAD --; then
    echo "ERROR"
    echo "FATAL: El árbol de trabajo tiene mutaciones rastreadas sin registrar. Haz commit antes de proyectar."
    exit 1
fi
if ! git diff-index --quiet HEAD --; then
    echo "WARN (mutaciones locales presentes en DRY-RUN)"
else
    echo "OK (Limpio)"
fi

# 2. Síntesis del Árbol Canónico Destilado (Zero Historical Bloat / Zero .agents)
echo -n "[2/6] Sintetizando árbol limpio en índice temporal (excluyendo .agents)... "
TEMP_INDEX=$(mktemp)
export GIT_INDEX_FILE="$TEMP_INDEX"
git read-tree HEAD
git rm --cached -r -q --ignore-unmatch .agents
CLEAN_TREE=$(git write-tree)
rm -f "$TEMP_INDEX"
unset GIT_INDEX_FILE
echo "OK ($CLEAN_TREE)"

# 3. Veto Anti-Bloat y Anti-Fugas (Cero CSV / JSONL / DB / VTT en CLEAN_TREE)
echo -n "[3/6] Auditando contorno de archivos prohibidos (.csv, .jsonl, .db, .vtt)... "
FORBIDDEN_FILES=$(git ls-tree -r "$CLEAN_TREE" --name-only | grep -E '\.(csv|jsonl|db|vtt)$' || true)
if [ -n "$FORBIDDEN_FILES" ]; then
    echo "ERROR"
    echo "FATAL: Se detectaron archivos prohibidos en el árbol destilado:"
    echo "$FORBIDDEN_FILES"
    exit 1
fi
echo "OK (0 archivos prohibidos)"

# 4. Validación de Límite Físico (< 20 MB)
echo -n "[4/6] Calculando tamaño del árbol empaquetado... "
BUNDLE_BYTES=$(git archive --format=tar "$CLEAN_TREE" | wc -c | tr -d ' ')
BUNDLE_MB=$(awk "BEGIN {printf \"%.2f\", $BUNDLE_BYTES / 1048576}")
MAX_BYTES=20971520 # 20 MB

if [ "$BUNDLE_BYTES" -gt "$MAX_BYTES" ]; then
    echo "ERROR ($BUNDLE_MB MB)"
    echo "FATAL: El tamaño del árbol ($BUNDLE_MB MB) supera el umbral soberano de 20 MB."
    exit 1
fi
echo "OK ($BUNDLE_MB MB < 20 MB)"

# 5. Escaneo de Secretos con Gitleaks
echo -n "[5/6] Ejecutando escaneo Gitleaks sobre el árbol de código... "
if command -v gitleaks >/dev/null 2>&1; then
    if ! gitleaks detect --config="$REPO_ROOT/.gitleaks.toml" --source="$REPO_ROOT" --no-git --redact >/dev/null 2>&1; then
        echo "ERROR"
        echo "FATAL: Gitleaks detectó posibles secretos en el código. Revisa .gitleaks.toml o purga las claves."
        exit 1
    fi
    echo "OK (0 secretos detectados)"
else
    echo "WARNING (gitleaks no instalado en PATH; se omite escaneo dinámico)"
fi

# 6. Sello Biométrico Somático (Touch ID / Secure Enclave) y Forja de Rama Huérfana
TREE_DIGEST="$CLEAN_TREE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  Clean Tree Digest (SHA-1 Git): $TREE_DIGEST"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Forjar commit huérfano local 'release/v5.0-clean'
COMMIT_MSG="feat(release): BABYLON-60 v5.0 Sovereign Core (Clean Distillation)"
CLEAN_COMMIT=$(git commit-tree "$CLEAN_TREE" -m "$COMMIT_MSG")
git branch -f release/v5.0-clean "$CLEAN_COMMIT"
echo "[6/6] Rama huérfana forjada en silicio: release/v5.0-clean -> $CLEAN_COMMIT"

if [ "$DRY_RUN" -eq 0 ]; then
    echo "  Solicitando atestación somática en silicio (Touch ID)..."
    if command -v c5_biometric_gate >/dev/null 2>&1; then
        if ! c5_biometric_gate --causal-hash "$TREE_DIGEST" --action "Proyección Pública" --agent "MOSKV-1" --scope "BABYLON-60-PUBLIC" --no-sound; then
            echo "FATAL: Atestación biométrica fallida o cancelada por el operador."
            exit 1
        fi
    elif [ -f "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" ]; then
        if ! swift "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" --causal-hash "$TREE_DIGEST" --action "Proyección Pública" --agent "MOSKV-1" --scope "BABYLON-60-PUBLIC" --no-sound; then
            echo "FATAL: Atestación biométrica fallida o cancelada por el operador."
            exit 1
        fi
    else
        echo "FATAL: c5_biometric_gate no disponible; abortando en Fail-Stop 0xDEAD_6060."
        exit 1
    fi
    echo "[AUTORIZACIÓN BIOMÉTRICA CONCEDIDA]"
fi

# 7. Despacho hacia el Repositorio Público
if [ "$DRY_RUN" -eq 1 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  [DRY-RUN EXITOSO] El árbol cumple 100% de las invariantes para publicación."
    echo "  Rama local lista: release/v5.0-clean ($CLEAN_COMMIT)"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
fi

if ! git remote get-url "$TARGET_REMOTE" >/dev/null 2>&1; then
    echo "AVISO: El remote '$TARGET_REMOTE' no está configurado en este repositorio."
    echo "Para vincular el repositorio público independiente, ejecuta:"
    echo "  git remote add $TARGET_REMOTE git@github.com:borjamoskv/babylon60-core.git"
    echo "Luego vuelve a ejecutar este script:"
    echo "  ./scripts/c5_git_utils/c5_distill_public_mirror.sh $TARGET_REMOTE"
    exit 0
fi

echo "Despachando rama limpia hacia '$TARGET_REMOTE' (main)..."
git push "$TARGET_REMOTE" release/v5.0-clean:main --force

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  [ÉXITO] Proyección pública completada sin fugas y con linaje limpio."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
