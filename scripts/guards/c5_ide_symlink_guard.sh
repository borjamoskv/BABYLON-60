#!/usr/bin/env bash
# Invariante C5-REAL: Verificación de Punteros IDE
set -euo pipefail

CANONICAL_SOURCE=".babylon60rules"
TARGETS=(".cursorrules" ".windsurfrules" ".codexrules" "CLAUDE.md" ".clinerules" ".roorules")
ANERGY_DETECTED=0

echo "[C5-GUARD] Auditando isomorfismo de reglas IDE..."

if [[ ! -f "$CANONICAL_SOURCE" ]]; then
    echo "🚨 ERROR TERMINAL: Fuente canónica $CANONICAL_SOURCE extraviada."
    exit 1
fi

for target in "${TARGETS[@]}"; do
    if [[ -e "$target" || -L "$target" ]]; then
        if [[ ! -L "$target" ]]; then
            echo "❌ ANERGÍA DETECTADA: $target es un archivo físico (Mimesis rota)."
            ANERGY_DETECTED=1
        else
            link_target=$(readlink "$target")
            if [[ "$link_target" != "$CANONICAL_SOURCE" ]]; then
                echo "❌ FRACTURA TOPOLÓGICA: $target apunta a $link_target, se exigía $CANONICAL_SOURCE."
                ANERGY_DETECTED=1
            fi
        fi
    fi
done

if [[ -e ".github/copilot-instructions.md" || -L ".github/copilot-instructions.md" ]]; then
    if [[ ! -L ".github/copilot-instructions.md" || "$(readlink ".github/copilot-instructions.md")" != "../.babylon60rules" ]]; then
        echo "❌ FRACTURA TOPOLÓGICA: .github/copilot-instructions.md debe ser symlink a ../.babylon60rules."
        ANERGY_DETECTED=1
    fi
fi

if [[ -e ".cursor/mcp.json" || -L ".cursor/mcp.json" ]]; then
    if [[ ! -L ".cursor/mcp.json" || "$(readlink ".cursor/mcp.json")" != "../.mcp.json" ]]; then
        echo "❌ FRACTURA TOPOLÓGICA: .cursor/mcp.json debe ser symlink a ../.mcp.json."
        ANERGY_DETECTED=1
    fi
fi

if [[ $ANERGY_DETECTED -eq 1 ]]; then
    echo "💥 Apoptosis detonada: Regresión entrópica en IDE detectada. Abortando commit."
    exit 1
fi

echo "✅ Soberanía IDE validada en Silicio. Exergía estructural preservada."
exit 0
