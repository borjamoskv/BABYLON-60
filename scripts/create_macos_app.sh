#!/usr/bin/env bash
# ==============================================================================
# BABYLON-60: Generador de Aplicación Nativa macOS (Babylon60.app)
# Cero dependencias externas. Genera un bundle .app compatible con Finder y Dock.
# ==============================================================================

set -e

DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$DIR"

APP_NAME="Babylon60.app"
APP_DIR="$DIR/$APP_NAME"
CONTENTS_DIR="$APP_DIR/Contents"
MACOS_DIR="$CONTENTS_DIR/MacOS"
RESOURCES_DIR="$CONTENTS_DIR/Resources"

if [ "$1" = "--check-only" ]; then
    echo "APP_GENERATOR_READY"
    exit 0
fi

echo "============================================================"
echo "  BABYLON IDE — Empaquetado Nativo macOS ($APP_NAME)"
echo "============================================================"

# Crear estructura del bundle
mkdir -p "$MACOS_DIR"
mkdir -p "$RESOURCES_DIR"

# 1. Info.plist
cat <<EOF > "$CONTENTS_DIR/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>Babylon60Launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.babylon60.ide</string>
    <key>CFBundleName</key>
    <string>BABYLON IDE</string>
    <key>CFBundleDisplayName</key>
    <string>BABYLON-60</string>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleShortVersionString</key>
    <string>60.4.0</string>
    <key>CFBundleVersion</key>
    <string>60.4.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>LSMinimumSystemVersion</key>
    <string>12.0</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# 2. Script de Lanzamiento ejecutable (MacOS/Babylon60Launcher)
cat <<'EOF' > "$MACOS_DIR/Babylon60Launcher"
#!/bin/bash
DIR="$(cd "$(dirname "$0")/../../.." && pwd)"
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:$HOME/.cargo/bin:$HOME/.local/bin:$PATH"

if [ -f "$DIR/Instalar-Babylon60.command" ]; then
    exec "$DIR/Instalar-Babylon60.command"
elif [ -f "$DIR/scripts/babylon_launcher.py" ]; then
    exec python3 "$DIR/scripts/babylon_launcher.py"
else
    open "$DIR/ui/index.html"
fi
EOF

chmod +x "$MACOS_DIR/Babylon60Launcher"

# 3. Acceso directo en ~/Applications para indexación en Spotlight
USER_APPS="$HOME/Applications"
mkdir -p "$USER_APPS" 2>/dev/null || true
if [ -d "$USER_APPS" ]; then
    ln -sf "$APP_DIR" "$USER_APPS/$APP_NAME" 2>/dev/null || true
    echo "  [+] App indexada en Spotlight: ~/Applications/$APP_NAME"
fi

# 4. Acceso directo opcional en el Escritorio del usuario si no existe
DESKTOP_DIR="$HOME/Desktop"
if [ -d "$DESKTOP_DIR" ] && [ ! -e "$DESKTOP_DIR/$APP_NAME" ]; then
    ln -sf "$APP_DIR" "$DESKTOP_DIR/$APP_NAME" 2>/dev/null || true
    echo "  [+] Acceso directo creado en el Escritorio: ~/Desktop/$APP_NAME"
fi

echo "  [+] Bundle compilado exitosamente: $APP_DIR"
echo "============================================================"
