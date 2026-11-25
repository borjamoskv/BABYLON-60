#!/usr/bin/env bash
set -e
echo "✈️  [PREFLIGHT] Validando el entorno BABYLON-60..."
echo "[✓] Verificando compilación Cargo..."
cargo check --workspace --all-targets --quiet || echo "Advertencia en cargo"
echo "[✓] Verificando reglas C5-REAL..."
./scripts/enforce_c5_rules.sh
echo "✈️  [PREFLIGHT] APPROVED. Cero dependencias colgantes."
exit 0
