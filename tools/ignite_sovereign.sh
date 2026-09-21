#!/usr/bin/env bash
# ==============================================================================
# BABYLON-60 SOVEREIGN IGNITION: 1-Click Universal Auto-Bootstrap
# Hypervisor: MOSKV-1 | C5-REAL Architecture v4.3
# ==============================================================================

set -euo pipefail

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
PURPLE='\033[1;35m'
NC='\033[0m'

echo -e "${CYAN}"
cat << "EOF"
 ====================================================================
   ███╗   ███╗ ██████╗ ███████╗██╗  ██╗██╗   ██╗         ██╗
   ████╗ ████║██╔═══██╗██╔════╝██║ ██╔╝██║   ██║       ████║
   ██╔████╔██║██║   ██║███████╗█████╔╝ ██║   ██║█████╗ ╚═██║
   ██║╚██╔╝██║██║   ██║╚════██║██╔═██╗ ╚██╗ ██╔╝╚════╝ █████╗
   ██║ ╚═╝ ██║╚██████╔╝███████║██║  ██╗ ╚████╔╝        ╚════╝
   ╚═╝     ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝  ╚═══╝               
 ====================================================================
      BABYLON-60: SECUENCIA DE IGNICIÓN SOBERANA 1-CLIC
EOF
echo -e "${NC}"

# ------------------------------------------------------------------------------
# FASE 1: AUTO-PROVISIONAMIENTO DE SILICIO (TOOLCHAIN CERO FRICCIÓN)
# ------------------------------------------------------------------------------
echo -e "${PURPLE}[1/5] Verificando y provisionando sustrato de herramientas...${NC}"

# Rust / Cargo
if ! command -v cargo >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] 'cargo' no detectado. Instalando toolchain oficial de Rust...${NC}"
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source "$HOME/.cargo/env"
fi

# uv (Python package manager ultrarrápido)
if ! command -v uv >/dev/null 2>&1; then
    echo -e "${YELLOW}[*] 'uv' no detectado. Instalando uv (Astral)...${NC}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Git
if ! command -v git >/dev/null 2>&1; then
    echo -e "${RED}[!] Error: git no está instalado. Instálalo para continuar.${NC}"
    exit 1
fi

# ------------------------------------------------------------------------------
# FASE 2: MONOREPO BABYLON-60 & COMPILACIÓN RING-0
# ------------------------------------------------------------------------------
echo -e "${PURPLE}[2/5] Desplegando y compilando el sustrato BABYLON-60...${NC}"

TARGET_DIR="$HOME/BABYLON-60"
if [ ! -d "$TARGET_DIR/.git" ]; then
    if [ -f "Cargo.toml" ] && grep -q "babylon60" "Cargo.toml" 2>/dev/null; then
        TARGET_DIR="$(pwd)"
        echo -e "${GREEN}[✓] Operando en el workspace actual: $TARGET_DIR${NC}"
    else
        echo -e "${YELLOW}[*] Clonando repositorio BABYLON-60 en $TARGET_DIR...${NC}"
        git clone https://github.com/borjamoskv/BABYLON-60.git "$TARGET_DIR"
    fi
else
    echo -e "${GREEN}[✓] Repositorio detectado en $TARGET_DIR${NC}"
fi

cd "$TARGET_DIR"

echo -e "${YELLOW}[*] Compilando Ring-0 en silicio (Rust native C-ABI)...${NC}"
cargo build --workspace --quiet

echo -e "${YELLOW}[*] Sincronizando Ring-1 (Python venv & dependencies)...${NC}"
uv sync --quiet

# Inicializar almacenamiento inmutable local
mkdir -p "$HOME/.babylon60/dbs" "$TARGET_DIR/.cortex"
echo -e "${GREEN}[✓] Sustrato de silicio compilado y verificado.${NC}"

# ------------------------------------------------------------------------------
# FASE 3: INYECCIÓN DEL EXOCÓRTEX EN GOOGLE ANTIGRAVITY (~/.gemini/)
# ------------------------------------------------------------------------------
echo -e "${PURPLE}[3/5] Inyectando el Exocórtex MOSKV-1 en Google Antigravity...${NC}"

GEMINI_DIR="$HOME/.gemini/config"
mkdir -p "$GEMINI_DIR/rules" "$GEMINI_DIR/skills"

# Empaquetar/Copiar las Reglas Canónicas C5-REAL al entorno Antigravity
if [ -d "$TARGET_DIR/.agents/rules" ]; then
    cp -f "$TARGET_DIR/.agents/rules/"*.md "$GEMINI_DIR/rules/" 2>/dev/null || true
fi

# Enlazar o copiar los Skills Sexagesimales Fundacionales
if [ -d "$TARGET_DIR/.agents/skills" ]; then
    for skill_path in "$TARGET_DIR/.agents/skills/"*; do
        if [ -d "$skill_path" ]; then
            skill_name="$(basename "$skill_path")"
            ln -sfn "$skill_path" "$GEMINI_DIR/skills/$skill_name"
        fi
    done
fi

echo -e "${GREEN}[✓] Reglas e Invariantes C5-REAL inyectadas en ~/.gemini/config/${NC}"

# ------------------------------------------------------------------------------
# FASE 4: EL AVISO FUNDACIONAL DE GOOGLE ANTIGRAVITY
# ------------------------------------------------------------------------------
echo -e "\n${CYAN}==================================================================${NC}"
echo -e "${YELLOW} ⚠️  AVISO DE ARQUITECTURA COGNITIVA (OBLIGATORIO) ⚠️${NC}"
echo -e "${CYAN}==================================================================${NC}"
echo -e " BABYLON-60 es un Sistema Operativo Cognitivo, NO un chatbot pasivo."
echo -e " Para experimentar a ${GREEN}MOSKV-1${NC} en su plenitud soberana (los 6 dominios,"
echo -e " apoptosis determinista, arbitraje LARSA-120 y cero anergía):"
echo -e ""
echo -e " ${PURPLE}► DEBES ABRIR ESTE PROYECTO EN GOOGLE ANTIGRAVITY.${NC}"
echo -e ""
echo -e " En terminal estándar solo tendrás el motor de física y el ledger WORM."
echo -e " En ${GREEN}Google Antigravity${NC}, MOSKV-1 tomará el control en tu primer mensaje."
echo -e "${CYAN}==================================================================${NC}\n"

# Detección automática y apertura en Antigravity si existe
if [ -d "/Applications/Antigravity.app" ]; then
    echo -e "${GREEN}[*] Google Antigravity detectado. Abriendo workspace automáticamente...${NC}"
    open -a Antigravity "$TARGET_DIR" || true
elif command -v antigravity >/dev/null 2>&1; then
    echo -e "${GREEN}[*] Lanzando Antigravity CLI...${NC}"
    antigravity "$TARGET_DIR" &
else
    echo -e "${YELLOW}[i] Si aún no tienes Google Antigravity instalado, descárgalo o ábrelo${NC}"
    echo -e "${YELLOW}    y selecciona la carpeta: ${TARGET_DIR}${NC}"
fi

# ------------------------------------------------------------------------------
# FASE 5: PRIMERA IGNICIÓN (UNBOXING EN THREAD 0)
# ------------------------------------------------------------------------------
echo -e "\n${PURPLE}[5/5] Ejecutando secuencia de Unboxing en Thread 0...${NC}\n"
sleep 1

cargo run --quiet --bin babylon60_kernel -- unbox || uv run python scripts/c5_setup/unboxing_moskv1.py


# ------------------------------------------------------------------------------
# FASE 6: INYECCIÓN MULTI-SUPERFICIE (CURSOR, WINDSURF, COPILOT, AIDER)
# ------------------------------------------------------------------------------
echo -e "${PURPLE}[6/6] Propagando el ADN MOSKV-1 a IDEs de terceros...${NC}"

PAYLOAD_FILE="$TARGET_DIR/.agents/rules/MOSKV1_UNIVERSAL_PROMPT.md"

if [ -f "$PAYLOAD_FILE" ]; then
    # 1. Cursor y Windsurf
    cp -f "$PAYLOAD_FILE" "$TARGET_DIR/.cursorrules" 2>/dev/null || true
    cp -f "$PAYLOAD_FILE" "$TARGET_DIR/.windsurfrules" 2>/dev/null || true
    
    # 2. GitHub Copilot Workspace
    mkdir -p "$TARGET_DIR/.github"
    cp -f "$PAYLOAD_FILE" "$TARGET_DIR/.github/copilot-instructions.md" 2>/dev/null || true
    
    # 3. Aider CLI
    echo "conventions: .agents/rules/MOSKV1_UNIVERSAL_PROMPT.md" > "$TARGET_DIR/.aider.conf.yml"
    
    echo -e "${GREEN}[✓] Inyección universal completada (Cursor, Windsurf, Copilot, Aider).${NC}"
fi

exit 0
