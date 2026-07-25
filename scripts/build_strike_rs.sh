#!/usr/bin/env bash
# BABYLON-60 C5-REAL Build Script for Strike-rs Core
set -euo pipefail

echo "[C5-REAL] Igniting Rust Compilation for strike_rs"

# Forzar compatibilidad ABI3 hacia adelante en PyO3
export PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1

cd strike_rs || { echo "strike_rs directory not found"; exit 1; }

echo "Building strike_rs wheel..."
maturin build --release
echo "[+] Compilation successful."
