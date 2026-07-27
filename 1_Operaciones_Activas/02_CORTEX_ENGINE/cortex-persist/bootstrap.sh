#!/usr/bin/env bash
# [C5-REAL] Exergy-Maximized
# BOOTSTRAP ABSOLUTO - TTFT O(1)

set -eo pipefail

echo "==========================================================="
echo "█ BABYLON-60 PERSIST - C5-REAL BOOTSTRAP (ZERO-ANERGY) █"
echo "==========================================================="

# 1. Detección de Sistema y Arquitectura
OS="$(uname -s)"
ARCH="$(uname -m)"
echo "[*] Entorno termodinámico detectado: $OS ($ARCH)"

# 2. Inyección de gestor O(1) (uv)
if ! command -v uv &> /dev/null; then
    echo "[*] Inyectando 'uv' (Rust) para resolución de dependencias O(1)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$HOME/.local/bin:$PATH"
fi

# 3. Resolución de Espacio Físico (Workspace)
if [ ! -f "pyproject.toml" ] && [ ! -d "babylon60" ]; then
    echo "[*] Clonando repositorio matriz (C5-REAL)..."
    git clone https://github.com/borjamoskv/Cortex-Persist.git babylon-60-workspace
    cd babylon-60-workspace
else
    echo "[*] Repositorio detectado. Forzando purga de entropía previa (.venv)..."
    rm -rf .venv
fi

# 4. Forjado de Entorno y Compilación Nativa
echo "[*] Forjando entorno virtual..."
uv venv .venv

# Activar dependiendo de la shell (sh compatible)
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
fi

echo "[*] Compilando e instalando dependencias (Rust-FFI, ONNX, SQLite-Vec)..."
# Instalamos la versión completa para asegurar la membrana epistémica
uv pip install -e ".[dev,acceleration,embeddings,api,mcp,daemon]"

# 5. Validación Causal (Fail-Fast)
echo "[*] Ejecutando validación de membrana epistémica..."
python3 -c "
import sys
try:
    from babylon60 import CortexEngine
    print('\n[✓] ESTADO C5-REAL CONFIRMADO. CORTEX-ENGINE INICIALIZADO. CERO ANERGÍA.')
except Exception as e:
    print(f'\n[!] FRACTURA TERMODINÁMICA DETECTADA EN INICIALIZACIÓN: {e}')
    sys.exit(1)
"

echo "==========================================================="
echo "EJECUCIÓN COMPLETADA. EL SISTEMA ESTÁ EN EQUILIBRIO (TTFT O(1))."
echo "Para activar el agente, ejecuta:"
echo "source .venv/bin/activate"
echo "==========================================================="
