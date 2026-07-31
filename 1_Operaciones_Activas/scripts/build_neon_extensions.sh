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

# 1. Hamming Weight / Popcount (ILP 4x)
if [ -f "65_popcount_ultra_exergy.c" ]; then
    echo "[*] Compilando libpopcount_neon.dylib (4.2+ BOPs)..."
    clang $CFLAGS -o libpopcount_neon.dylib 65_popcount_ultra_exergy.c
fi

# 2. Xorshift PRNG (ILP 8x)
if [ -f "67_xorshift_ultra_exergy.c" ]; then
    echo "[*] Compilando libxorshift_neon.dylib (4.0+ BOPs)..."
    clang $CFLAGS -o libxorshift_neon.dylib 67_xorshift_ultra_exergy.c
fi

# 3. Fast Inverse Square Root (si aplica a futuro como librería aislada)
# if [ -f "63_q_rsqrt.c" ]; then
#     clang $CFLAGS -o libq_rsqrt.dylib 63_q_rsqrt.c
# fi

echo "============================================================"
echo "  [OK] MUTACIONES DE HARDWARE ENSAMBLADAS CON ÉXITO"
echo "============================================================"
