#!/usr/bin/env bash
# ==============================================================================
# BABYLON-60 · SCRIPT DE APROVISIONAMIENTO DETERMINISTA DE APPLIANCE
# Hardware Target: Apple Silicon (Darwin ARM64 / Mac Mini M4 Pro / Mac Studio)
# C5-REAL Sovereign Appliance Engine · Zero-Touch Provisioning
# ==============================================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}╔══════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║      BABYLON-60 · APROVISIONAMIENTO DE APPLIANCE SOBERANO        ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════════╝${NC}"

# 1. Verificación de Arquitectura en Silicio (Fail-Closed)
ARCH=$(uname -m)
OS=$(uname -s)

if [[ "$OS" != "Darwin" ]] || [[ "$ARCH" != "arm64" ]]; then
    echo -e "${RED}[ERROR FAIL-CLOSED]: Este appliance exige Apple Silicon nativo (Darwin ARM64). Detectado: $OS $ARCH${NC}"
    exit 1
fi
echo -e "${GREEN}[+] Silicio validado: Darwin ARM64 (Apple Silicon).${NC}"

# 2. Privilegios de Administrador
if [[ $EUID -ne 0 ]]; then
   echo -e "${YELLOW}[!] Se requieren permisos de superusuario para configurar el demonio y los ajustes de energía.${NC}"
   exec sudo bash "$0" "$@"
fi

# 3. Configuración de Energía de Servidor Desatendido
echo -e "${BLUE}[*] Configurando parámetros de energía y tolerancia a fallos...${NC}"
pmset -a sleep 0
pmset -a displaysleep 10
pmset -a womp 1                # Wake on LAN
pmset -a autorestart 1         # Reinicio automático tras fallo de corriente
systemsetup -setrestartfreeze on > /dev/null 2>&1 || true

# 4. Configuración de Red Local (mDNS Hostname)
echo -e "${BLUE}[*] Fijando nombre mDNS canónico: babylon.local...${NC}"
scutil --set HostName "babylon.local"
scutil --set LocalHostName "babylon"
scutil --set ComputerName "BABYLON-60 Appliance"

# 5. Estructura de Directorios Confinada
echo -e "${BLUE}[*] Creando jerarquía de directorios en /opt/babylon...${NC}"
mkdir -p /opt/babylon/bin
mkdir -p /opt/babylon/models
mkdir -p /opt/babylon/logs
mkdir -p /opt/babylon/data
chmod 755 /opt/babylon
chmod 755 /opt/babylon/models

# 6. Compilación e Instalación del Motor Bare-Metal
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}[*] Verificando compilación de eridu-infer...${NC}"
if [[ -f "$REPO_DIR/target/release/eridu-infer" ]]; then
    cp "$REPO_DIR/target/release/eridu-infer" /opt/babylon/bin/eridu-infer
elif command -v cargo &> /dev/null; then
    echo -e "${YELLOW}[*] Compilando eridu-infer en modo release...${NC}"
    (cd "$REPO_DIR" && cargo build --release)
    cp "$REPO_DIR/target/release/eridu-infer" /opt/babylon/bin/eridu-infer
else
    echo -e "${RED}[ERROR]: Binario no encontrado y cargo no está instalado.${NC}"
    exit 1
fi

chmod +x /opt/babylon/bin/eridu-infer
ln -sf /opt/babylon/bin/eridu-infer /usr/local/bin/eridu-infer || true
echo -e "${GREEN}[+] Motor instalado en /opt/babylon/bin/eridu-infer.${NC}"

# 7. Despliegue del Demonio launchd en macOS
echo -e "${BLUE}[*] Registrando demonio permanente launchd...${NC}"
PLIST_PATH="/Library/LaunchDaemons/com.babylon60.eridu-infer.plist"

cat << 'EOF' > "$PLIST_PATH"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.babylon60.eridu-infer</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/babylon/bin/eridu-infer</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/opt/babylon/logs/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/opt/babylon/logs/stderr.log</string>
    <key>WorkingDirectory</key>
    <string>/opt/babylon</string>
</dict>
</plist>
EOF

chmod 644 "$PLIST_PATH"
chown root:wheel "$PLIST_PATH"

# Recarga segura del demonio
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load "$PLIST_PATH"
echo -e "${GREEN}[+] Demonio activado permanentemente en launchd.${NC}"

# 8. Sonda de Verificación (Probe en 5s)
echo -e "${BLUE}[*] Esperando arranque del motor...${NC}"
sleep 2

STATUS_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:1234/v1/models || echo "000")

if [[ "$STATUS_CODE" == "200" ]]; then
    echo -e "${GREEN}╔══════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   APPLIANCE APROVISIONADO Y OPERATIVO CON ÉXITO                  ║${NC}"
    echo -e "${GREEN}║   • Host Local: http://babylon.local:1234                        ║${NC}"
    echo -e "${GREEN}║   • OpenAI API: http://babylon.local:1234/v1/chat/completions    ║${NC}"
    echo -e "${GREEN}║   • Socket IPC: /tmp/eridu-infer.sock                            ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════════════════════════════╝${NC}"
else
    echo -e "${YELLOW}[!] El demonio está cargado. Verifique los logs en /opt/babylon/logs/stdout.log.${NC}"
fi
