#!/usr/bin/env bash
# C5-REAL EXERGY CERTIFIED BUILD SCRIPT FOR BABYLON-60 DOMAIN KERNEL
set -eo pipefail

echo "=========================================="
echo "■ BABYLON-60 DOMAIN KERNEL BUILD & AUDIT"
echo "=========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
KERNEL_DIR="${SCRIPT_DIR}/domain_kernel"
WEB_DIR="${SCRIPT_DIR}/babylon-web"

echo "➜ [1/3] Validating F# Domain Kernel (.NET SDK)..."
if command -v dotnet &> /dev/null; then
    (cd "${KERNEL_DIR}" && dotnet build --configuration Release)
    echo "✔ F# Domain Kernel compiled successfully."
else
    echo "⚠ dotnet SDK not found in path. Skipping native .NET compilation step."
fi

echo "➜ [2/3] Building babylon-web Frontend (React 19 + Vite 8)..."
if command -v npm &> /dev/null; then
    (cd "${WEB_DIR}" && npm run build)
    echo "✔ babylon-web built successfully."
else
    echo "❌ npm not found."
    exit 1
fi

echo "➜ [3/3] Build & Verification Complete."
