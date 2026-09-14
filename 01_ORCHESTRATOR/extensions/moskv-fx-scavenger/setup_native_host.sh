#!/bin/bash
# Script de Registro Causal (Native Messaging Host)
# Autoriza a la extensión a hablar con el Kernel Python

set -e

HOST_NAME="com.babylon60.moskv_scavenger"
REPO_ROOT="$(cd "../.." && pwd)"
KERNEL_SCRIPT="$REPO_ROOT/scripts/c5_cli/moskv_native_host.py"

echo "========================================================="
echo "   BABYLON-60 NATIVE MESSAGING HOST REGISTRATION"
echo "========================================================="
echo ""
echo "Ruta del Kernel resuelta: $KERNEL_SCRIPT"

if [ ! -f "$KERNEL_SCRIPT" ]; then
    echo "[!] ERROR FATAL: No se encuentra native_messaging_host.py en $KERNEL_SCRIPT"
    exit 1
fi

read -p "Introduce el ID de tu extensión (chrome://extensions): " EXTENSION_ID

if [ -z "$EXTENSION_ID" ]; then
    echo "[!] ERROR: El Extension ID es obligatorio para la Invariante de Seguridad."
    exit 1
fi

echo ""
echo "¿Qué navegador estás utilizando?"
echo "1) Google Chrome"
echo "2) Arc"
echo "3) Brave"
read -p "Selecciona (1-3): " BROWSER_CHOICE

case $BROWSER_CHOICE in
    1)
        TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
        ;;
    2)
        TARGET_DIR="$HOME/Library/Application Support/Arc/User Data/NativeMessagingHosts"
        ;;
    3)
        TARGET_DIR="$HOME/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"
        ;;
    *)
        echo "[!] Opción inválida. Abortando colapso."
        exit 1
        ;;
esac

mkdir -p "$TARGET_DIR"
MANIFEST_PATH="$TARGET_DIR/$HOST_NAME.json"

cat <<EOF > "$MANIFEST_PATH"
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

echo ""
echo "[✓] ÉXITO: Manifiesto IPC forjado y anclado."
echo "Ruta del manifiesto: $MANIFEST_PATH"
echo "========================================================="
echo "El túnel Causal entre el navegador y el Kernel está listo."
