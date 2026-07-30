#!/usr/bin/env bash
# ╔══════════════════════════════════════════════════════════════╗
# ║  OUROBOROS SNIPER — BOOTSTRAP SOBERANO                      ║
# ║  Ley Ω₆: Auto-Allow Enforced. Ejecución headless.           ║
# ╚══════════════════════════════════════════════════════════════╝
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}>>> $1${NC}"; }
warn() { echo -e "${YELLOW}>>> WARN: $1${NC}"; }
fail() { echo -e "${RED}>>> FATAL: $1${NC}"; exit 1; }

# ── 1. VERIFICAR DEPENDENCIAS ─────────────────────────────────────────────────
log "Verificando dependencias del clúster..."

command -v forge  &>/dev/null || fail "Foundry no instalado. Ejecuta: curl -L https://foundry.paradigm.xyz | bash"
command -v cargo  &>/dev/null || fail "Rust no instalado. Ejecuta: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
command -v cast   &>/dev/null || fail "Cast (Foundry) no encontrado."

log "Dependencias OK."

# ── 2. COMPILAR CONTRATOS SOLIDITY (Yul optimizer) ───────────────────────────
log "Compilando OuroborosExecutor.sol (optimizador Yul activo)..."
cd "$REPO_ROOT"
forge build --sizes

log "Contrato compilado. Tamaño verificado."

# ── 3. EJECUTAR FUZZING SUITE ─────────────────────────────────────────────────
log "Ejecutando suite de Fuzzing (Honeypot Detection)..."
forge test --match-path "test/HoneypotFuzz.t.sol" -v

log "Fuzzing completado. No se detectaron vulnerabilidades."

# ── 4. COMPILAR DAEMON RUST (Release — Silent Binary) ────────────────────────
log "Compilando Rust Daemon en modo release (lto=fat, strip=true)..."
cd "$REPO_ROOT/rust-daemon"
cargo build --release

BINARY_SIZE=$(du -sh "target/release/ouroboros-daemon" | cut -f1)
log "Daemon compilado. Tamaño del binario: $BINARY_SIZE"

# ── 5. DESPLEGAR EN TESTNET SEPOLIA ──────────────────────────────────────────
log "Desplegando en Sepolia Testnet..."
cd "$REPO_ROOT"

if [ -z "${SOVEREIGN_PRIVATE_KEY:-}" ]; then
    fail "SOVEREIGN_PRIVATE_KEY no definida. Copia .env.example a .env y rellena los valores."
fi

forge script script/Deploy.s.sol:DeployOuroboros \
    --rpc-url "https://sepolia.infura.io/v3/${INFURA_KEY}" \
    --broadcast \
    --verify \
    -vvvv

log "Despliegue completado. Copia la dirección del Executor en .env → EXECUTOR_CONTRACT."

# ── 6. INSTRUCCIONES FINALES ──────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  OUROBOROS SOVEREIGN STACK — LISTO PARA EJECUCIÓN       ║${NC}"
echo -e "${GREEN}╠══════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  → Actualiza .env con la dirección del Executor          ║${NC}"
echo -e "${GREEN}║  → Ejecuta la autenticación Telegram (primera vez):     ║${NC}"
echo -e "${GREEN}║     cd rust-daemon && cargo run                          ║${NC}"
echo -e "${GREEN}║  → Para producción bare-metal (Linux/AWS):               ║${NC}"
echo -e "${GREEN}║     scp target/release/ouroboros-daemon user@server:~/   ║${NC}"
echo -e "${GREEN}║     ssh server './ouroboros-daemon'                      ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
