#!/usr/bin/env bash
# AESTHETIC-OMEGA: Pre-commit Hook
# Aísla la sobreexcitabilidad. Este hook rechaza commits si hay violaciones estéticas de CSS.

echo "[C5-REAL] Invoking Aesthetic-Foundry-Omega Audit..."

# Verificar archivos CSS o JS/TS en el stage
STAGED_FILES=$(git diff --cached --name-only | grep -E '\.(css|js|jsx|ts|tsx)$')

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

for file in $STAGED_FILES; do
    # Búsqueda adversarial: Rechazar valores genéricos del navegador y sombras débiles.
    if grep -Ei "box-shadow:\s*(0px 0px|none|1px 1px 2px)" "$file" > /dev/null; then
        echo "[ERROR: AESTHETIC] Fallo termodinámico visual en $file. No uses sombras genéricas. Usa el estándar Industrial Noir."
        exit 1
    fi
    if grep -Ei "color:\s*(blue|red|green|yellow);" "$file" > /dev/null; then
        echo "[ERROR: AESTHETIC] Paleta de colores prohibida en $file. Usa tokens HSL o la jerarquía Noir 2026."
        exit 1
    fi
done

echo "[C5-REAL] Aesthetic QA Passed. Zero visual entropy."
exit 0
