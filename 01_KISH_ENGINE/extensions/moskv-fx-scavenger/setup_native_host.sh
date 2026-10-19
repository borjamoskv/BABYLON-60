#!/bin/bash
# ============================================================================
# BABYLON-60: Native Messaging Host Registration
# Deterministic CLI & Interactive setup for Chrome / Arc / Brave
# ============================================================================

set -e

HOST_NAME="com.babylon60.moskv_scavenger"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
KERNEL_SCRIPT="$REPO_ROOT/scripts/c5_cli/moskv_native_host.py"

EXTENSION_ID=""
BROWSER=""
DRY_RUN=false

usage() {
    echo "Uso: $0 [opciones]"
    echo "Opciones:"
    echo "  -e, --extension-id <ID>   ID de la extensión de Chrome (32 caracteres)"
    echo "  -b, --browser <nombre>    Navegador: chrome, arc, brave (default: chrome)"
    echo "  -d, --dry-run             Muestra el manifiesto sin escribir en disco"
    echo "  -h, --help                Muestra esta ayuda"
    exit 0
}

# Parse CLI arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -e|--extension-id)
            EXTENSION_ID="$2"
            shift 2
            ;;
        -b|--browser)
            BROWSER=$(echo "$2" | tr '[:upper:]' '[:lower:]')
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo "[!] Argumento desconocido: $1"
            usage
            ;;
    esac
done

echo "========================================================="
echo "   BABYLON-60 NATIVE MESSAGING HOST REGISTRATION"
echo "========================================================="
echo "Directorio base: $REPO_ROOT"
echo "Ruta del Kernel resuelta: $KERNEL_SCRIPT"

if [ ! -f "$KERNEL_SCRIPT" ]; then
    echo "[!] ERROR FATAL: No se encuentra moskv_native_host.py en $KERNEL_SCRIPT"
    exit 1
fi

chmod +x "$KERNEL_SCRIPT"

# Prompt interactivo si falta el ID y estamos en TTY
if [ -z "$EXTENSION_ID" ]; then
    if [ -t 0 ]; then
        read -p "Introduce el ID de tu extensión (chrome://extensions): " EXTENSION_ID
    else
        echo "[!] ERROR: Se requiere --extension-id en modo no interactivo."
        exit 1
    fi
fi

if [ -z "$EXTENSION_ID" ]; then
    echo "[!] ERROR: El Extension ID es obligatorio."
    exit 1
fi

# Resolución de navegador
if [ -z "$BROWSER" ]; then
    if [ -t 0 ]; then
        echo ""
        echo "¿Qué navegador estás utilizando?"
        echo "1) Google Chrome"
        echo "2) Arc"
        echo "3) Brave"
        read -p "Selecciona (1-3) [1]: " BROWSER_CHOICE
        case ${BROWSER_CHOICE:-1} in
            1) BROWSER="chrome" ;;
            2) BROWSER="arc" ;;
            3) BROWSER="brave" ;;
            *) BROWSER="chrome" ;;
        esac
    else
        BROWSER="chrome"
    fi
fi

case "$BROWSER" in
    chrome|google-chrome)
        TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        ;;
    arc)
        TARGET_DIR="$HOME/Library/Application Support/Arc/User Data/NativeMessagingHosts"
        ;;
    brave|brave-browser)
        TARGET_DIR="$HOME/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"
        ;;
    *)
        echo "[!] Navegador no reconocido: $BROWSER. Opciones válidas: chrome, arc, brave."
        exit 1
        ;;
esac

MANIFEST_PATH="$TARGET_DIR/$HOST_NAME.json"

MANIFEST_CONTENT=$(cat <<EOF
{
  "name": "$HOST_NAME",
  "description": "BABYLON-60 Scavenger Native Host (Ring-0)",
  "path": "$KERNEL_SCRIPT",
  "type": "stdio",
  "allowed_origins": [
    "chrome-extension://$EXTENSION_ID/"
  ]
}
EOF
)

if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "[DRY-RUN] Manifiesto resultante para $MANIFEST_PATH:"
    echo "$MANIFEST_CONTENT"
    exit 0
fi

mkdir -p "$TARGET_DIR"
echo "$MANIFEST_CONTENT" > "$MANIFEST_PATH"

echo ""
echo "[✓] ÉXITO: Manifiesto IPC forjado y anclado."
echo "Destino: $MANIFEST_PATH"
echo "Navegador: $BROWSER"
echo "Origen permitido: chrome-extension://$EXTENSION_ID/"
echo "========================================================="
echo "El túnel Causal entre el navegador y el Kernel está listo."
