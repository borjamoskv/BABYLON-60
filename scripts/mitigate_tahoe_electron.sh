#!/usr/bin/env bash
# [C5-REAL] TAHOE 26.5.2 KINETIC MITIGATION FOR ELECTRON/CHROMIUM
# Target Invariant: Preserve GPU rendering stability across ViewBridge framework

echo "🟢 [CORTEX] Forzando deshabilitación de aceleración de hardware para apps Electron/Chromium en macOS Tahoe..."
# Inyectar variables de entorno a nivel de sesión en launchd para mitigar el desbordamiento de _cornerMask
launchctl setenv ELECTRON_DISABLE_GPU 1
launchctl setenv ELECTRON_ENABLE_LOGGING 1
launchctl setenv ELECTRON_DISABLE_HW_ACCELERATION 1

echo "🔍 [CORTEX] Purgando cachés termodinámicos de Chrome y apps Electron (Slack, Discord, VS Code)..."
rm -rf ~/Library/Caches/Google/Chrome/Default/Cache/* 2>/dev/null
rm -rf ~/Library/Caches/com.electron.*/Cache/* 2>/dev/null

echo "💾 [CORTEX] Estado cristalizado. Reinicia tus aplicaciones afectadas."
