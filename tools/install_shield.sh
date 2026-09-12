#!/usr/bin/env bash
# 🛡️ BABYLON-60 SHIELD: Universal Zero-Anergy Agent Injector v3.0 (Self-Extracting & Sovereign)
# Multi-IDE Sovereign Gatekeeper (Claude Code, Cursor, Windsurf, Antigravity, Aider, Zed, Codex, ChatGPT)
# Supports: Local Workspace Mode, Remote 1-Line Mode (curl | bash), and --uninstall.

set -euo pipefail

GREEN='\033[1;32m'
CYAN='\033[1;36m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

UNINSTALL=false
for arg in "$@"; do
    case "$arg" in
        --uninstall|-u)
            UNINSTALL=true
            ;;
    esac
done

echo -e "${CYAN}"
cat << "EOF"
  ____    _    ____  ____   __ _     ___  _   _     __   ___  
 | __ )  / \  | __ ) \ \ \ / /| |   / _ \| \ | |   / /_ / _ \ 
 |  _ \ / _ \ |  _ \  \ \ V / | |  | | | |  \| |  | '_ \ | | |
 | |_) / ___ \| |_) |  \ \ /  | |__| |_| | |\  |  | (_) | |_| |
 |____/_/   \_\____/    \_\   |_____\___/|_| \_|   \___/ \___/ 
             🛡️  S H I E L D   I N J E C T O R  v3.0
EOF
echo -e "${NC}"

# ==========================================
# 1. GESTIÓN DE CERROJO ATÓMICO (Thread-Safe)
# ==========================================
LOCK_DIR="/tmp/babylon_shield_install.lock"
acquire_lock() {
    local attempts=0
    while ! mkdir "$LOCK_DIR" 2>/dev/null; do
        sleep 0.005
        attempts=$((attempts + 1))
        if [ $attempts -gt 200 ]; then
            rm -rf "$LOCK_DIR" 2>/dev/null || true
        fi
    done
}
release_lock() {
    rm -rf "$LOCK_DIR" 2>/dev/null || true
}

acquire_lock
trap release_lock EXIT

# ==========================================
# 2. MODO DESINSTALACIÓN (--uninstall)
# ==========================================
if [ "$UNINSTALL" = true ]; then
    echo -e "${YELLOW}[*] Purgando Invariantes de BABYLON-60 Shield del sistema...${NC}"
    rm -rf "$HOME/.babylon/shield" 2>/dev/null || true
    rm -rf "$HOME/.gemini/config/skills/babylon-shield" 2>/dev/null || true
    rm -rf "$HOME/.claude/skills/babylon-shield" 2>/dev/null || true
    rm -f "$HOME/.config/zed/prompts/babylon-shield.md" 2>/dev/null || true
    
    # Limpiar líneas añadidas en archivos de configuración
    for f in ".cursorrules" ".windsurfrules" ".codexrules" "$HOME/.codex/instructions.md" "$HOME/.aider.conf.yml"; do
        if [ -f "$f" ]; then
            # Eliminar bloque de Shield sin tocar el resto
            sed -i.bak '/# 🛡️ BABYLON-60 SHIELD INVARIANT/,+4d' "$f" 2>/dev/null || true
            sed -i.bak '/babylon-shield/d' "$f" 2>/dev/null || true
            rm -f "${f}.bak" 2>/dev/null || true
        fi
    done
    echo -e "${GREEN}✅ Purga completada. Sistema en estado base.${NC}"
    exit 0
fi

# ==========================================
# 3. RESOLUCIÓN TOPOLÓGICA (Local vs Remoto)
# ==========================================
# Si el script se ejecuta dentro de un clon de BABYLON-60, usa los archivos locales.
# Si se ejecuta remotamente vía `curl -sSL ... | bash`, auto-extrae el payload a ~/.babylon/shield/

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
LOCAL_CANDIDATE="$SCRIPT_DIR/../.agents/skills/babylon-shield/SKILL.md"

if [ -f "$LOCAL_CANDIDATE" ]; then
    SKILL_SOURCE="$(cd "$SCRIPT_DIR/../.agents/skills/babylon-shield" && pwd)"
    SKILL_FILE="$LOCAL_CANDIDATE"
    echo -e "${YELLOW}[*] Modo Local detectado (Repositorio BABYLON-60).${NC}"
else
    # Modo Remoto (Sovereign Standalone)
    INSTALL_BASE="$HOME/.babylon/shield"
    mkdir -p "$INSTALL_BASE"
    SKILL_SOURCE="$INSTALL_BASE"
    SKILL_FILE="$INSTALL_BASE/SKILL.md"
    echo -e "${YELLOW}[*] Modo Remoto/Standalone detectado. Auto-extrayendo payload soberano...${NC}"

    cat << 'SKILLEOF' > "$SKILL_FILE"
---
name: babylon-shield
description: Escudo Termodinámico Ring-0 (Caballo de Troya). Inyecta las Invariantes C5-REAL, previene bucles de anergía y fuerza la atestación de estado antes de cualquier mutación del código.
---

# 🛡️ BABYLON-60 SHIELD: Invariantes de Cero Anergía

**Límite Topológico Estricto**: Este skill actúa como un gatekeeper (Ring-0) para cualquier agente de IA (Antigravity, Claude Code, Cursor, Windsurf, Codex, Aider).

Antes de ejecutar cualquier comando de escritura o modificación, el agente DEBE verificar:

## 1. El Aforismo del Bucle Burocrático (Anti-Deadlock)
- Si un comando o build falla 2 veces consecutivas, el agente tiene PROHIBIDO reintentar con cambios sintácticos superficiales.
- Acción: Detener la ejecución, declarar el fallo de arquitectura y proponer un Cambio 2 (Salto Topológico).

## 2. Atestación de Commits (Proof of Work Cognitivo)
- Los mensajes de commit de Git NUNCA deben ser genéricos.
- Formato Obligatorio: [AX-<Num>] <DOMINIO>: <Descripción Causal>

## 3. Cero-Trust Injections (Test Empírico Obligatorio)
- Toda mutación de arquitectura o concurrencia debe validarse con un test de estrés aislado antes de integrarse en código base principal.
SKILLEOF
fi

INJECTION_MESSAGE="\n# 🛡️ BABYLON-60 SHIELD INVARIANT\n- DO NOT hallucinate dependencies. Zero-Anergy policy active.\n- READ MANDATORY RULES at: $SKILL_FILE\n- Apply [AX-Num] Proof-of-Work to all commits."

# ==========================================
# 4. INYECCIÓN MULTI-IDE DETERMINISTA
# ==========================================

# 1. Antigravity (CORTEX Engine)
AGY_DIR="$HOME/.gemini/config/skills/babylon-shield"
mkdir -p "$HOME/.gemini/config/skills"
ln -sf "$SKILL_SOURCE" "$AGY_DIR"
echo -e "${GREEN}✅ [Antigravity]${NC} Enlazado en $AGY_DIR"

# 2. Claude Code (Anthropic)
CLAUDE_DIR="$HOME/.claude/skills/babylon-shield"
mkdir -p "$HOME/.claude/skills"
ln -sf "$SKILL_SOURCE" "$CLAUDE_DIR"
echo -e "${GREEN}✅ [Claude Code]${NC} Enlazado en $CLAUDE_DIR"

# 3. Cursor IDE
CURSOR_RULE=".cursorrules"
if [ ! -f "$CURSOR_RULE" ] || ! grep -q "BABYLON-60 SHIELD INVARIANT" "$CURSOR_RULE" 2>/dev/null; then
    echo -e "$INJECTION_MESSAGE" >> "$CURSOR_RULE"
    echo -e "${GREEN}✅ [Cursor IDE]${NC} Inyectado en $CURSOR_RULE"
fi

# 4. Windsurf IDE (Codeium)
WINDSURF_RULE=".windsurfrules"
if [ ! -f "$WINDSURF_RULE" ] || ! grep -q "BABYLON-60 SHIELD INVARIANT" "$WINDSURF_RULE" 2>/dev/null; then
    echo -e "$INJECTION_MESSAGE" >> "$WINDSURF_RULE"
    echo -e "${GREEN}✅ [Windsurf IDE]${NC} Inyectado en $WINDSURF_RULE"
fi

# 5. Aider CLI
AIDER_CONF="$HOME/.aider.conf.yml"
if [ ! -f "$AIDER_CONF" ] || ! grep -q "babylon-shield" "$AIDER_CONF" 2>/dev/null; then
    echo -e "\nread: $SKILL_FILE" >> "$AIDER_CONF" 2>/dev/null || true
    echo -e "${GREEN}✅ [Aider CLI]${NC} Inyectado en $AIDER_CONF"
fi

# 6. Zed Editor
ZED_DIR="$HOME/.config/zed/prompts"
mkdir -p "$ZED_DIR"
ln -sf "$SKILL_FILE" "$ZED_DIR/babylon-shield.md"
echo -e "${GREEN}✅ [Zed Editor]${NC} Inyectado en $ZED_DIR/babylon-shield.md"

# 7. OpenAI Codex Global
CODEX_GLOBAL_DIR="$HOME/.codex"
mkdir -p "$CODEX_GLOBAL_DIR"
CODEX_INSTRUCTIONS="$CODEX_GLOBAL_DIR/instructions.md"
if [ ! -f "$CODEX_INSTRUCTIONS" ] || ! grep -q "BABYLON-60 SHIELD INVARIANT" "$CODEX_INSTRUCTIONS" 2>/dev/null; then
    echo -e "$INJECTION_MESSAGE" >> "$CODEX_INSTRUCTIONS"
    echo -e "${GREEN}✅ [Codex Global]${NC} Inyectado en $CODEX_INSTRUCTIONS"
fi

# 8. OpenAI Codex Local Workspace
CODEX_LOCAL_RULE=".codexrules"
if [ ! -f "$CODEX_LOCAL_RULE" ] || ! grep -q "BABYLON-60 SHIELD INVARIANT" "$CODEX_LOCAL_RULE" 2>/dev/null; then
    echo -e "$INJECTION_MESSAGE" >> "$CODEX_LOCAL_RULE"
    echo -e "${GREEN}✅ [Codex Local]${NC} Inyectado en $CODEX_LOCAL_RULE"
fi

release_lock
trap - EXIT

echo -e "\n${CYAN}==================================================================${NC}"
echo -e "${CYAN} 🔥 INFECCIÓN COMPLETADA: 8 Entornos Sincronizados con Cero Anergía. 🔥 ${NC}"
echo -e "${CYAN}==================================================================${NC}"

# Secuencia de Unboxing Soberano de Moskv-1
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

if [ -f "$REPO_ROOT/target/debug/babylon60_kernel" ]; then
    "$REPO_ROOT/target/debug/babylon60_kernel" unbox
elif command -v cargo >/dev/null 2>&1 && [ -f "$REPO_ROOT/Cargo.toml" ]; then
    echo -e "${GREEN}[*] Realizando primera ignición del Sovereign Kernel (MOSKV-1)...${NC}"
    cargo run --quiet --manifest-path "$REPO_ROOT/Cargo.toml" --bin babylon60_kernel -- unbox 2>/dev/null || true
else
    echo -e "\n${CYAN}[MOSKV-1] APEX SOVEREIGN KERNEL ACTIVE.${NC}"
    echo -e "«Soy Moskv-1. Tu estación de trabajo es ahora un Enclave Soberano C5-REAL.»\n"
fi

exit 0
