#!/usr/bin/env bash
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ CORTEX FULL ENVIRONMENT SETUP | STATE: C5-REAL
# ============================================================================

set -e

echo "[CORTEX-SETUP] Instalando entorno agéntico completo CORTEX..."

# 1. Crear directorios de configuración de CORTEX
HOME_DIR="${HOME}"
CORTEX_SKILLS_DIR="${HOME_DIR}/.gemini/config/skills"
CORTEX_AGENTS_DIR="${HOME_DIR}/.gemini/config"

mkdir -p "${CORTEX_SKILLS_DIR}"

echo "[1/4] Directorios configurados en: ${CORTEX_SKILLS_DIR}"

# 2. Sincronizar catálogo de Skills desde el repositorio
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REPO_ROOT="$( dirname "${SCRIPT_DIR}" )"

if [ -d "${REPO_ROOT}/.agents" ]; then
    echo "[2/4] Copiando gobernanza y reglas de workspace..."
    cp -r "${REPO_ROOT}/.agents" "${HOME_DIR}/.agents" 2>/dev/null || true
fi

# 3. Verificar binarios requeridos (jj, python3, git)
echo "[3/4] Comprobando binarios del sistema..."
command -v git >/dev/null 2>&1 || echo "⚠️ Git no instalado"
command -v jj >/dev/null 2>&1 || echo "⚠️ Jujutsu (jj) no instalado (Ejecutar: brew install jujutsu)"
command -v python3 >/dev/null 2>&1 || echo "⚠️ Python 3 no instalado"

# 4. Inyección de variables de entorno recomendadas
echo "[4/4] Verificando variables de entorno..."
if [ -z "$KIMI_API_KEY" ]; then
    echo "⚠️ Recuerda exportar KIMI_API_KEY en tu .zshrc / .bashrc:"
    echo "   export KIMI_API_KEY='tu_clave_moonshot'"
fi

echo "✅ [CORTEX-SETUP] ¡Entorno preparado! La estación ya dispone de la infraestructura CORTEX."
