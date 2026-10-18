#!/bin/bash
# ==============================================================================
# MANIFIESTO DE EXTINCIÓN EPISTÉMICA (PURGA TERMINAL)
# ==============================================================================
# "Ser humano es ir descartando hasta que el cosmos te descarta a ti"
# 
# Este script ejecuta un DROP (O(1)) sobre la totalidad del directorio scratch,
# incinerando toda la deuda técnica, pruebas de concepto y simulaciones que no 
# lograron la energía de activación necesaria para consolidarse en repositorios.
# ==============================================================================

set -e

SCRATCH_DIR="/Users/borjafernandezangulo/.gemini/antigravity/scratch"

echo "[*] Iniciando purga termodinámica del directorio volátil..."

# Advertencia de aniquilación (85+ archivos, 2 motores, gigabytes de JSON/VTT)
# Se purgan métricas, simuladores (TTC, Spicy4Tuna), ensayos en Lean 4, y renders estocásticos.
if [ -d "$SCRATCH_DIR" ]; then
    rm -rf "${SCRATCH_DIR:?}/"*
    echo "  [+] Manta de Markov colapsada. Scratch incinerado."
else
    echo "  [-] El territorio ya es el vacío."
fi

echo "[*] PUNTO FIJO Ω ALCANZADO. ENTROPÍA CERO."
