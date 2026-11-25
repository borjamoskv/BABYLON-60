#!/usr/bin/env bash
# ==============================================================================
# BABYLON60 SOVEREIGN NATIVE LAUNCHER
# System: macOS (Darwin ARM64 / Apple Silicon)
# Engine: Tauri v2 + Rust + WebKit
# ==============================================================================

set -euo pipefail

CYAN='\033[1;36m'
GREEN='\033[1;32m'
YELLOW='\033[1;33m'
RED='\033[1;31m'
NC='\033[0m'

APP_BUNDLE="/Users/borjafernandezangulo/10_PROJECTS/babylon60-ide/src-tauri/target/release/bundle/macos/BABYLON60.app"
BINARY_PATH="/Users/borjafernandezangulo/10_PROJECTS/babylon60-ide/src-tauri/target/release/app"

echo -e "${CYAN}[*] Arrancando BABYLON60 Standalone Sovereign Engine...${NC}"

if [ -d "$APP_BUNDLE" ]; then
    echo -e "${GREEN}✅ Abriendo aplicación nativa macOS: BABYLON60.app${NC}"
    open "$APP_BUNDLE"
elif [ -f "$BINARY_PATH" ]; then
    echo -e "${GREEN}✅ Iniciando ejecutable binario nativo: $BINARY_PATH${NC}"
    "$BINARY_PATH" &
else
    echo -e "${YELLOW}[!] El paquete de release aún se está compilando. Ejecutando frontend de desarrollo...${NC}"
    cd /Users/borjafernandezangulo/10_PROJECTS/babylon60-ide
    npx @tauri-apps/cli dev
fi
