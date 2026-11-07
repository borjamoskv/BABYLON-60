#!/bin/bash
# scripts/c5_setup/install_host.sh
# Registra moskv_native_host.py en Chrome/Brave en macOS

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
HOST_NAME="com.babylon60.moskv_scavenger"
HOST_PATH="$(cd "$DIR/../c5_cli" && pwd)/moskv_native_host.py"

# Aseguramos que el script Python sea ejecutable
chmod +x "$HOST_PATH"

# IMPORTANTE: Reemplazar "<ID_DE_LA_EXTENSION>" con el ID real que Chrome asigne 
# al cargar la extensión desempaquetada. Para la PoC, permitimos el wildcard o
# usaremos un placeholder. (Nota: Chrome prefiere IDs explícitos por seguridad).
ALLOWED_ORIGIN="chrome-extension://plcholderidreemplazar/"

# JSON de manifiesto de Native Messaging
MANIFEST_CONTENT="{
  \"name\": \"$HOST_NAME\",
  \"description\": \"Motor Causal B60 (Native Messaging Host)\",
  \"path\": \"$HOST_PATH\",
  \"type\": \"stdio\",
  \"allowed_origins\": [
    \"$ALLOWED_ORIGIN\"
  ]
}"

# Rutas de instalación en macOS
CHROME_TARGET_DIR="$HOME/Library/Application Support/Google/Chrome/NativeMessagingHosts"
BRAVE_TARGET_DIR="$HOME/Library/Application Support/BraveSoftware/Brave-Browser/NativeMessagingHosts"

mkdir -p "$CHROME_TARGET_DIR"
mkdir -p "$BRAVE_TARGET_DIR"

echo "$MANIFEST_CONTENT" > "$CHROME_TARGET_DIR/$HOST_NAME.json"
echo "$MANIFEST_CONTENT" > "$BRAVE_TARGET_DIR/$HOST_NAME.json"

echo "✅ Native Messaging Host instalado."
echo "Ruta: $CHROME_TARGET_DIR/$HOST_NAME.json"
echo "Ejecutable anclado: $HOST_PATH"
echo "⚠️  IMPORTANTE: Edita $CHROME_TARGET_DIR/$HOST_NAME.json e inserta el ID real de la extensión."
