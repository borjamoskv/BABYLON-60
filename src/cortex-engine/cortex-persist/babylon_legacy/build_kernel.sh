# C5-REAL EXERGY CERTIFIED
#!/bin/bash
set -e

echo "[C5-REAL] Initiating Transducer Build (F# Domain Kernel -> Vite Isomorphic UI)"

cd "$(dirname "$0")"
ROOT_DIR=$(pwd)

echo "[1/3] Restoring .NET tools in domain_kernel..."
cd domain_kernel
dotnet tool restore

echo "[2/3] Transducing F# to TypeScript via Fable..."
dotnet fable Babylon60.Domain.fsproj --outDir ../babylon-web/src/domain --lang TypeScript

echo "[3/3] Building Babylon Web UI (Vite)..."
cd ../babylon-web
npm install
npm run build

echo "[OK] Axiom Ω25 Fulfilled. C5-REAL Transduction Complete."
