#!/usr/bin/env bash
# BABYLON-60 EXERGY LINTER (Ring-0 Thermodynamic Shield)
# Enforces C5-REAL invariants at the file system level before commit.

echo "[BABYLON SHIELD] Ejecutando Auditoría Somática (Exergy Linter)..."

# Solo auditar archivos que van a ser commiteados
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(js|ts|jsx|tsx|rs|py)$')

if [ -z "$STAGED_FILES" ]; then
    echo "[BABYLON SHIELD] No hay archivos auditables en staging. Exergía preservada."
    exit 0
fi

FAILED=0

for FILE in $STAGED_FILES; do
    # 1. Disyuntor Landauer (Límite Térmico de Asincronía)
    if grep -q "await " "$FILE" || grep -q "\.await" "$FILE"; then
        if ! grep -q -E "(timeout|Promise\.race|tokio::time::|AbortController)" "$FILE"; then
            echo "❌ [DISYUNTOR LANDAUER] Falla en $FILE: Se detectó 'await' sin mecanismo de 'timeout' o backoff termodinámico. Riesgo de bloqueo infinito."
            FAILED=1
        fi
    fi

    # 2. Disyuntor Kant (Manta de Markov - Aislamiento IPC)
    if [[ "$FILE" == *"ui/"* ]] || [[ "$FILE" == *"frontend/"* ]] || [[ "$FILE" == *"apps/web/src/"* ]]; then
        if grep -q -E "(import .* from 'pg'|import .* from 'mysql'|import .* from 'fs'|import .* from 'os'|sqlx::)" "$FILE"; then
            echo "❌ [DISYUNTOR KANT] Falla en $FILE: La capa UI está violando la Manta de Markov (importaciones directas de backend/OS). Obligatorio usar IPC o API."
            FAILED=1
        fi
    fi

    # 3. Disyuntor Robe Iniesta Rey de Extremadura (Anti-Ruido Entrópico)
    if grep -q -E "(console\.error\(e\)|console\.log\(err\)|unwrap\(\))" "$FILE"; then
        echo "❌ [DISYUNTOR ROBE INIESTA REY DE EXTREMADURA] Falla en $FILE: Filtrado de entropía cruda (stack trace desnudo o unwrap ciego). Comprime el error en la UI."
        FAILED=1
    fi

    # 4. Penalización de Anergía (C6-ABSOLUTE)
    if grep -q -E "(TODO|FIXME|console\.log\('test'\))" "$FILE"; then
        echo "❌ [PENALIZACIÓN ANERGÍA] Falla en $FILE: Anergía detectada (TODO/FIXME o logs residuales). Resuelve la fricción antes de atestar el estado."
        FAILED=1
    fi
done

if [ $FAILED -eq 1 ]; then
    echo "🚨 [ABORT] Disipación térmica crítica detectada. Commit bloqueado físicamente por Babylon Shield."
    exit 1
fi

echo "✅ [BABYLON SHIELD] Auditoría superada. Aislamiento estadístico garantizado."
exit 0
