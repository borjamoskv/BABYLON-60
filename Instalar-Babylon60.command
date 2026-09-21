#!/bin/bash
# ==============================================================================
# BABYLON-60: Instalador Proactivo 1-Clic (Self-Healing & Zero-Anergy)
# Especificación: babylon60-architecture v4.3 / C5-REAL
# ==============================================================================

DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

echo "============================================================"
echo "      BABYLON IDE — Secuencia de Ignición 1-Clic"
echo "      Hypervisor: MOSKV-1 | Ring-0 C-ABI Runtime"
echo "============================================================"
echo ""

echo "[1/4] Verificando dependencias del sistema (Rust y uv)..."

if ! command -v cargo >/dev/null 2>&1; then
    echo "[!] Error: 'cargo' (Rust) no detectado en el PATH."
    echo "[+] Instala Rust con: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh"
    exit 1
fi

if ! command -v uv >/dev/null 2>&1; then
    echo "[!] Error: 'uv' (Python package manager) no detectado en el PATH."
    echo "[+] Instala uv con: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi

echo "[2/4] Aprovisionando Ring-0 (Silicio / Rust)..."
cargo build --workspace
if [ $? -ne 0 ]; then
    echo "[!] Error en la compilación del Ring-0. Abortando."
    exit 1
fi

echo "[3/4] Aprovisionando Ring-1 (Exocórtex / Python)..."
uv sync
if [ $? -ne 0 ]; then
    echo "[!] Error en la sincronización de dependencias Python. Abortando."
    exit 1
fi

echo "[4/4] Transfiriendo control a MOSKV-1..."
echo "============================================================"
echo ""

# El kernel C-ABI toma el control
cargo run --bin babylon60_kernel -- unbox || uv run python scripts/c5_setup/unboxing_moskv1.py
