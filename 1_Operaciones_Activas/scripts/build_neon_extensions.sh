#!/usr/bin/env bash
# C5-REAL EXERGY CERTIFIED
# Motor de Compilación Determinista para Extensiones C SIMD/NEON

set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "============================================================"
echo "  [C5-REAL] ENSAMBLAJE DE SILICIO (ARM NEON / APPLE M1)"
echo "============================================================"

# Optimizaciones extremas para arquitectura ARM64 (Loop Unrolling, Fast Math)
CFLAGS="-O3 -mcpu=apple-m1 -ffast-math -dynamiclib"

compile_extension() {
    local src_file=$1
    local out_file=$2
    if [ -f "$src_file" ]; then
        echo "[*] Compilando $out_file..."
        clang $CFLAGS -o "$out_file" "$src_file"
    fi
}

# 1. Primitivas SIMD Generales
compile_extension "64_cortex_primitives_simd.c" "libcortex_primitives_simd.dylib"

# 2. Operaciones Matemáticas (ULTRATHINK)
compile_extension "61_q_rsqrt_neon.c" "libq_rsqrt_neon.dylib"
compile_extension "61_q_rsqrt_neon_fma.c" "libq_rsqrt_neon_fma.dylib"
compile_extension "65_popcount_ultra_exergy.c" "libpopcount_neon.dylib"
compile_extension "67_xorshift_ultra_exergy.c" "libxorshift_neon.dylib"
compile_extension "68_bitonic_sort_ultra_exergy.c" "libbitonic_neon.dylib"
compile_extension "69_gemm_ultra_exergy.c" "libgemm_ultra_exergy.dylib"

echo "============================================================"
echo "  [OK] TODAS LAS MUTACIONES DE HARDWARE HAN SIDO ENSAMBLADAS"
echo "============================================================"
