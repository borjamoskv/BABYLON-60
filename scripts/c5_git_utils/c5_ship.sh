#!/usr/bin/env bash
# ============================================================================
# BABYLON-60 v5.0 Sovereign Hardened
# █ C5-SHIP v3.0: MÁQUINA DE ESTADOS AUTOMÁTICA + FILTRO ANTI-BLOAT + RADAR
# ============================================================================
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

# 0. Instalar aliases nativos de Git de forma idempotente (git sellar / git ship / git estado)
git config alias.sellar "!bash '$REPO_ROOT/scripts/c5_git_utils/c5_ship.sh'" 2>/dev/null || true
git config alias.ship "!bash '$REPO_ROOT/scripts/c5_git_utils/c5_ship.sh'" 2>/dev/null || true
git config alias.estado "!bash '$REPO_ROOT/scripts/c5_git_utils/c5_ship.sh' --status" 2>/dev/null || true

CURRENT_BRANCH="$(git rev-parse --abbrev-ref HEAD)"
PENDING_LINES="$(git status --porcelain)"
DIRTY_COUNT=0
if [ -n "$PENDING_LINES" ]; then
    DIRTY_COUNT=$(printf "%s\n" "$PENDING_LINES" | wc -l | tr -d ' ')
fi
AHEAD_COUNT="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"

# Modo de solo lectura (--status / estado)
if [ "${1:-}" = "--status" ] || [ "${1:-}" = "estado" ] || [ "${1:-}" = "status" ]; then
    echo "╭──────────────────────────────────────────────────────────────────╮"
    echo "│  RADAR DE ESTADO GIT · BABYLON-60 (C5-SHIP v3.0)                 │"
    echo "├──────────────────────────────────────────────────────────────────┤"
    if [ "$DIRTY_COUNT" -eq 0 ]; then
        echo "│  [1] EN TU MAC (Commit) : ✓ Todo guardado (0 archivos sueltos)   │"
    else
        echo "│  [1] EN TU MAC (Commit) : ● $DIRTY_COUNT archivo(s) pendiente(s) de guardar"
    fi
    if [ "$CURRENT_BRANCH" = "main" ]; then
        echo "│  [2] PISTA ACTIVA (Merge): ✓ En pista maestra (main)              │"
    else
        echo "│  [2] PISTA ACTIVA (Merge): ● En rama '$CURRENT_BRANCH' (pendiente de merge)"
    fi
    if [ "$AHEAD_COUNT" -eq 0 ]; then
        echo "│  [3] GITHUB (Push)      : ✓ 100% sincronizado con origin/main    │"
    else
        echo "│  [3] GITHUB (Push)      : ● $AHEAD_COUNT commit(s) listos para subir a GitHub"
    fi
    echo "├──────────────────────────────────────────────────────────────────┤"
    if [ "$DIRTY_COUNT" -eq 0 ] && [ "$CURRENT_BRANCH" = "main" ] && [ "$AHEAD_COUNT" -eq 0 ]; then
        echo "│  ACCIÓN RECOMENDADA     : Ninguna (Mac == GitHub)                │"
    else
        echo "│  ACCIÓN RECOMENDADA     : Ejecuta 'make sellar' o 'git sellar'   │"
    fi
    echo "╰──────────────────────────────────────────────────────────────────╯"
    exit 0
fi

TEMP_BRANCH=""
MAX_FILE_BYTES=524288

# Guardián Anti-Bloat y Anti-Fuga antes de tocar el índice de Git
enforce_pre_staging_hygiene() {
    local candidate_paths
    candidate_paths="$(git status --porcelain | awk '$1 != "D" && $1 != "R" {print $NF}')"
    for f in $candidate_paths; do
        [ -e "$f" ] || continue
        if echo "$f" | grep -qiE '\.(mid|flp|wav|mp3|mp4|m4a|pem|key|p12|db|sqlite|db-wal|db-shm)$'; then
            echo "[C5-SHIP][VETO] Archivo bloqueado por política Anti-Bloat/Secretos: $f" >&2
            exit 1
        fi
        if [ -f "$f" ]; then
            local fsize
            fsize=$(wc -c < "$f" | tr -d ' ')
            if [ "$fsize" -gt "$MAX_FILE_BYTES" ]; then
                echo "[C5-SHIP][VETO] Archivo supera el límite de 512 KB ($fsize bytes): $f" >&2
                exit 1
            fi
        fi
    done
}

# Función para calcular dinámicamente el mensaje [AX-N] con archivos y líneas reales
compute_next_semantic_commit_msg() {
    local last_ax
    last_ax=$(git log -n 50 --pretty=format:"%s" | grep -o '\[AX-[0-9]*\]' | head -n 1 | tr -d '[]AX-' || echo 0)
    if [ -z "$last_ax" ]; then
        last_ax=0
    fi
    local next_ax=$((last_ax + 1))

    local domain="GOVERNANCE"
    local changed_paths
    changed_paths="$(git diff --cached --name-only)"

    if echo "$changed_paths" | grep -qE "^(crates/|src/)|\.rs$"; then
        domain="KERNEL"
    elif echo "$changed_paths" | grep -qE "02_EDIN_SWARMS|orchestrator|blackboard|royal_rumble"; then
        domain="ORCHESTRATOR"
    elif echo "$changed_paths" | grep -qE "01_KISH_ENGINE|mcp"; then
        domain="MCP"
    elif echo "$changed_paths" | grep -qE "clients|openrouter|kimi"; then
        domain="CLIENTS"
    elif echo "$changed_paths" | grep -qE "proof/|lean"; then
        domain="EPISTEMOLOGY"
    elif echo "$changed_paths" | grep -qE "guards|security"; then
        domain="SECURITY"
    fi

    local file_list
    file_list=$(echo "$changed_paths" | awk -F/ '{print $NF}' | head -n 3 | paste -sd ", " - | sed 's/, $//')
    local total_files
    total_files=$(echo "$changed_paths" | wc -l | tr -d ' ')
    if [ "$total_files" -gt 3 ]; then
        file_list="$file_list (+$((total_files - 3)) más)"
    fi

    local ins del
    ins=$(git diff --cached --numstat | awk '{s+=$1} END {print s+0}')
    del=$(git diff --cached --numstat | awk '{s+=$2} END {print s+0}')

    echo "[AX-$next_ax] $domain: Actualizar $file_list (+${ins}/-${del})"
}

USER_COMMIT_MSG="${1:-}"

echo "[C5-SHIP] 1/5 Inspeccionando estado local (rama: $CURRENT_BRANCH)..."

# 1. Si hay cambios pendientes, auditar higiene, validar suites y hacer commit
if [ -n "$PENDING_LINES" ]; then
    echo "[C5-SHIP] -> Cambios detectados ($DIRTY_COUNT archivo(s)). Verificando filtro Anti-Bloat..."
    enforce_pre_staging_hygiene

    if echo "$PENDING_LINES" | grep -qE "\.py$"; then
        echo "[C5-SHIP]    - Validando suites Python (pytest)..."
        PYTHONPATH=02_EDIN_SWARMS uv run pytest tests/test_agents_archi.py -q
    fi

    if echo "$PENDING_LINES" | grep -qE "\.rs$|Cargo\."; then
        echo "[C5-SHIP]    - Validando suites Rust (cargo check)..."
        cargo check --tests -q
    fi

    if [ "$CURRENT_BRANCH" = "main" ]; then
        TEMP_BRANCH="ship/auto-$(git rev-parse --short HEAD)"
        echo "[C5-SHIP] -> Creando rama efímera '$TEMP_BRANCH' (Active Branch Awareness)..."
        git checkout -b "$TEMP_BRANCH"
        CURRENT_BRANCH="$TEMP_BRANCH"
    fi

    git add -A
    if [ -z "$USER_COMMIT_MSG" ]; then
        COMMIT_MSG="$(compute_next_semantic_commit_msg)"
    else
        COMMIT_MSG="$USER_COMMIT_MSG"
    fi
    git commit -m "$COMMIT_MSG"
    echo "[C5-SHIP] -> Commit certificado: '$COMMIT_MSG'."
else
    echo "[C5-SHIP] -> Árbol local limpio (cero cambios pendientes de commit)."
fi

# 2. Si estamos en rama efímera/secundaria, mergear a main con --no-ff
if [ "$CURRENT_BRANCH" != "main" ]; then
    echo "[C5-SHIP] 2/5 Fusionando explícitamente '$CURRENT_BRANCH' en 'main'..."
    git checkout main
    git merge --no-ff "$CURRENT_BRANCH" -m "Merge branch '$CURRENT_BRANCH' into main"
    if [ -n "$TEMP_BRANCH" ]; then
        git branch -d "$TEMP_BRANCH"
    fi
else
    echo "[C5-SHIP] 2/5 Ya en rama 'main' (sin ramas pendientes de merge)."
fi

# 3. Sincronización preventiva con origin/main (anti-divergencia)
echo "[C5-SHIP] 3/5 Comprobando estado del remoto origin/main..."
git fetch --quiet origin main 2>/dev/null || true
BEHIND_COUNT="$(git rev-list --count HEAD..origin/main 2>/dev/null || echo 0)"
if [ "$BEHIND_COUNT" -gt 0 ]; then
    echo "[C5-SHIP] -> El remoto tiene $BEHIND_COUNT commit(s) más recientes. Rebasando..."
    git rebase origin/main
fi

# 4. Comprobar si hay commits locales pendientes de push
AHEAD_COUNT="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
if [ "$AHEAD_COUNT" -gt 0 ]; then
    CAUSAL_HASH="$(git rev-parse HEAD)"
    echo "[C5-SHIP] 4/5 Detectados $AHEAD_COUNT commit(s) locales listos para subir a GitHub (HEAD=$CAUSAL_HASH)."
    echo "[C5-SHIP] -> Solicitando autorización biométrica Touch ID (Secure Enclave)..."

    mkdir -p "$REPO_ROOT/.babylon60"
    RECEIPT_PATH="$REPO_ROOT/.babylon60/last_ship_receipt.json"

    if command -v c5_biometric_gate >/dev/null 2>&1; then
        c5_biometric_gate --causal-hash "$CAUSAL_HASH" --action "Git Push origin/main" --agent "MOSKV-1" --scope "BABYLON-60" --no-sound | tee "$RECEIPT_PATH"
    elif [ -f "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" ]; then
        swift "$REPO_ROOT/01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift" --causal-hash "$CAUSAL_HASH" --action "Git Push origin/main" --agent "MOSKV-1" --scope "BABYLON-60" --no-sound | tee "$RECEIPT_PATH"
    fi

    echo "[C5-SHIP] -> Recibo biométrico persistido en .babylon60/last_ship_receipt.json"
    echo "[C5-SHIP] 5/5 Subiendo cambios a origin/main (git push origin main)..."
    git push origin main
    echo "[C5-SHIP] ✓ ÉXITO: Mac y GitHub están 100% sincronizados."
else
    echo "[C5-SHIP] 4/5 Nada pendiente de push (origin/main ya está al día)."
    echo "[C5-SHIP] ✓ ÉXITO: Estado sincronizado."
fi
