#!/usr/bin/env bash
# C5-REAL EXERGY CERTIFIED
set -euo pipefail

echo "=================================================="
echo " C5-REAL PREFLIGHT & HYGIENE VERIFICATION GATE"
echo "=================================================="

# 1. Verificar que no hay claves privadas o secretos expuestos
echo "[+] 1. Verificando ausencia de secretos en el árbol..."
if grep -rn "PRIVATE KEY" . --exclude-dir=".git" --exclude-dir=".venv" --exclude-dir="target" --exclude="*.log" 2>/dev/null; then
    echo "[!] ERROR: Se detectó una clave privada expuesta."
    exit 1
fi

# 2. Comprobar sintaxis básica de scripts Python
echo "[+] 2. Validando sintaxis de scripts Python..."
python3 -m py_compile scripts/*.py

echo "[+] 3. Verificando compilación de Rust..."
cargo check --workspace

echo "=================================================="
echo " [✓] Preflight superado. Cero anergía detectada."
echo "=================================================="
