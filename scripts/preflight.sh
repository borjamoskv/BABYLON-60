#!/usr/bin/env bash
# C5-REAL EXERGY CERTIFIED
set -euo pipefail

echo "=================================================="
echo " C5-REAL PREFLIGHT & HYGIENE VERIFICATION GATE"
echo "=================================================="

# 1. Verificar que no hay archivos de claves privadas no protegidas
echo "[+] 1. Verificando ausencia de secretos en el árbol..."
if grep -rn "BEGIN RSA PRIVATE KEY\|BEGIN OPENSSH PRIVATE KEY" . --exclude-dir=".git" --exclude-dir=".venv" --exclude-dir="__pycache__" --exclude-dir="target" --exclude-dir=".agents" --exclude-dir="node_modules" --exclude-dir="scratch" --exclude="*.log" --exclude=".env*" --exclude="preflight.sh" --exclude="reviewer_agent_test.py" 2>/dev/null; then
    echo "[!] ERROR: Se detectó una clave privada expuesta."
    exit 1
fi

# 1b. Verificar ausencia de .gocache y binarios ejecutables en c_src
if [ -d ".gocache" ] && git ls-files --error-unmatch .gocache >/dev/null 2>&1; then
    echo "[!] ERROR: Se detectó .gocache rastreado en Git."
    exit 1
fi
if git ls-files tests/compliance-suite/c_src/ | grep -E -v "\.(c|h|cpp)$" >/dev/null 2>&1; then
    echo "[!] ERROR: Se detectaron binarios compilados rastreados en c_src."
    exit 1
fi

# 2. Comprobar sintaxis básica de scripts Python
echo "[+] 2. Validando sintaxis de scripts Python..."
python3 -m py_compile scripts/*.py

echo "[+] 3. Verificando compilación de Rust..."
cargo check --workspace

# 4. Verificación de Alineación C-ABI (SharedManifest == 64B)
echo "[+] 4. Verificando alineación exacta de C-ABI FFI (64 bytes)..."
python3 -c "import sys; sys.path.insert(0, 'src/02_engines/cortex_bft'); from ipc.bridge import SharedManifest; import ctypes; assert ctypes.sizeof(SharedManifest) == 64, 'Desalineación C-ABI detectada en SharedManifest'"

# 5. Escaneo por Enjambre Legión-100 sobre todo el monorepositorio
echo "[+] 5. Ejecutando escaneo paralelo por la Legión de 100 Agentes..."
python3 scratch/legion_100_agents_full_monorepo.py

echo "=================================================="
echo " [✓] Preflight superado. Cero anergía detectada."
echo "=================================================="
