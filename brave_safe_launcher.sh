#!/usr/bin/env bash
# C5-REAL
# brave_safe_launcher.sh
# Mitigation for macOS Tahoe (macOS 26) SIGKILL (Error 9)

echo "[C5-REAL] Igniting Brave Browser bypassing cornerMask GPU starvation..."
open -a "Brave Browser" --args --disable-gpu --disable-software-rasterizer
