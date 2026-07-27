#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  OUROBOROS SNIPER — STAGE RUSO DEPLOYMENT                    ║
# ║  Ley Ω₆: Headless Execution Mandate. O(1) Tensor-State.      ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

SESSION_NAME="ouroboros_stage_ruso"

log() { echo -e "${GREEN}>>> $1${NC}"; }
warn() { echo -e "${YELLOW}>>> WARN: $1${NC}"; }
fail() { echo -e "${RED}>>> FATAL: $1${NC}"; exit 1; }

# ── 1. VALIDACIÓN SOVEREIGN ───────────────────────────────────────────────────
log "Verificando compilación C5-REAL (Release)..."
DAEMON_BIN="$REPO_ROOT/rust-daemon/target/release/ouroboros-daemon"

if [[ ! -f "$DAEMON_BIN" ]]; then
    warn "Binario release no encontrado. Iniciando Forja..."
    cd "$REPO_ROOT/rust-daemon"
    cargo build --release
fi

# ── 2. PREPARACIÓN DEL ENTORNO STAGE ──────────────────────────────────────────
# Si no existe .env, copiamos el de ejemplo para habilitar Dry-Run por seguridad.
cd "$REPO_ROOT/rust-daemon"
if [[ ! -f ".env" ]]; then
    warn ".env no encontrado en rust-daemon. Creando copia segura..."
    cp ../.env.example .env
fi

# Inyectamos el flag de STAGE RUSO explícito si es necesario.
# (En el código ya usamos dry_run=true, esto es seguridad a nivel OS)
export BABYLON60_ENV="STAGE_RUSO"

# ── 3. ORQUESTACIÓN HEADLESS (TMUX) ───────────────────────────────────────────
log "Evaluando Sandbox..."

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    warn "Sesión $SESSION_NAME ya existe. Deteniendo instancia antigua..."
    tmux kill-session -t "$SESSION_NAME"
    sleep 1
fi

log "Inyectando Daemon en sub-espacio Terminal (Session: $SESSION_NAME)..."
tmux new-session -d -s "$SESSION_NAME" -c "$REPO_ROOT/rust-daemon" "$DAEMON_BIN"

log "Extracción asintótica iniciada."
echo -e "${CYAN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  🚀 STAGE RUSO DESPLEGADO EXITOSAMENTE                   ║${NC}"
echo -e "${CYAN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║  → Comando para monitorizar UI en vivo:                  ║${NC}"
echo -e "${CYAN}║     tmux attach -t $SESSION_NAME                         ║${NC}"
echo -e "${CYAN}║  → Comando para desacoplar de la sesión:                 ║${NC}"
echo -e "${CYAN}║     Ctrl+B, luego D                                      ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════════════════════════╝${NC}"
