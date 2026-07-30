#!/usr/bin/env bash
set -e

# MOSKV-1 APEX: Deployment Protocol (C5-REAL)
# Este script levanta el enjambre termodinámico localmente.

echo "[Deploy] Inicializando base de datos Epigenética y Quorum Sensing..."
python3 -c "import epigenetic_store; epigenetic_store.init_db()"
python3 -c "import quorum_bus; quorum_bus.init_db()"
echo "[Deploy] SQLite Ledger estabilizado."

echo "[Deploy] Instalando Demonio de Exergía (Cron Autopoiético) en macOS Launchd..."
PLIST_NAME="com.moskv.exergy.plist"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

mkdir -p "$LAUNCH_AGENTS_DIR"
cp "$PLIST_NAME" "$LAUNCH_AGENTS_DIR/"

# Descargar si existe y recargar
launchctl unload "$LAUNCH_AGENTS_DIR/$PLIST_NAME" 2>/dev/null || true
launchctl load "$LAUNCH_AGENTS_DIR/$PLIST_NAME"
echo "[Deploy] Daemon acoplado exitosamente al Kernel de macOS."

echo "[Deploy] Sellando versión de despliegue en Git Sentinel..."
git add deploy.sh
git commit -m "chore(release): Deploy scripts and Swarm Initialization" || true
git tag -f "v1.0.0-APEX"
git push -f origin master --tags || true

echo "=== MOSKV-1 APEX DEPLOYMENT COMPLETE ==="
echo "Estado Operativo: V-OMEGA Activo. Autarquía Local Lograda."
