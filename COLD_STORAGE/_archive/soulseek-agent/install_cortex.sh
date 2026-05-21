#!/bin/bash
# ==============================================================================
# CORTEX SOBERANO · APROVISIONADOR DE ENTORNO
# Standard: C5-REAL · Designed for Alain's Node
# ==============================================================================

# Colores ANSI premium - Industrial Noir 2026
C_BLUE='\033[38;2;43;59;229m'      # Primary #2B3BE5
C_CYAN='\033[38;2;0;229;255m'      # Secondary Cyan
C_GREEN='\033[38;2;0;255;128m'     # Success Green
C_YELLOW='\033[38;2;255;200;0m'    # Warning Yellow
C_RED='\033[38;2;255;64;64m'       # Danger Red
C_GREY='\033[38;2;128;128;128m'    # Muted Grey
C_WHITE='\033[1;37m'               # Bold White
C_RESET='\033[0m'                  # Reset

clear

echo -e "${C_BLUE}┌──────────────────────────────────────────────────────────────────────────────┐${C_RESET}"
echo -e "${C_BLUE}│${C_WHITE}   CORTEX-PERSIST · APROVISIONADOR DEL ENTORNO DE TRABAJO v2.0              ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}│${C_GREY}   Instalación Automática e Integración C5-REAL de Dependencias P2P          ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}\n"

# 1. Búsqueda de ejecutable de Python
echo -e "${C_BLUE}[*]${C_WHITE} Buscando intérprete de Python en el nodo...${C_RESET}"
PYTHON_CMD=""
for cmd in python3 python3.14 python3.11 python3.10 python; do
    if command -v $cmd &> /dev/null; then
        # Verificar que sea versión 3.10+
        ver_check=$($cmd -c 'import sys; print(1 if sys.version_info >= (3, 10) else 0)')
        if [ "$ver_check" -eq 1 ]; then
            PYTHON_CMD=$cmd
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${C_RED}[!] ERROR: No se encontró un intérprete de Python 3.10 o superior.${C_RESET}"
    echo -e "    Por favor, instala la última versión de Python (https://www.python.org/)."
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
echo -e "    ${C_GREEN}✔ Encontrado:${C_CYAN} $PYTHON_CMD (Versión $PYTHON_VERSION)${C_RESET}"

# 2. Verificación e Instalación de decodificador FLAC
echo -e "\n${C_BLUE}[*]${C_WHITE} Verificando dependencia del sistema: 'flac' (Validación de Audio)...${C_RESET}"
if ! command -v flac &> /dev/null; then
    echo -e "    ${C_YELLOW}⚠ Advertencia: 'flac' no está instalado en el sistema.${C_RESET}"
    if command -v brew &> /dev/null; then
        echo -e "    ${C_CYAN}[+] Detectado Homebrew. Intentando instalar 'flac' de forma automática...${C_RESET}"
        brew install flac
        if [ $? -eq 0 ]; then
            echo -e "    ${C_GREEN}✔ Instalado con éxito vía Homebrew.${C_RESET}"
        else
            echo -e "    ${C_RED}✘ Fallo al instalar 'flac'. El agente no podrá auditar corruptos binarios.${C_RESET}"
        fi
    else
        echo -e "    ${C_GREY}ℹ Instala 'flac' manualmente ejecutando: brew install flac${C_RESET}"
    fi
else
    echo -e "    ${C_GREEN}✔ Detectada utilidad de sistema 'flac' en: $(which flac)${C_RESET}"
fi

# 3. Creación de directorios persistentes
echo -e "\n${C_BLUE}[*]${C_WHITE} Estructurando persistencia central CORTEX...${C_RESET}"
mkdir -p "$HOME/.gemini/antigravity/brain"
mkdir -p "$HOME/Music/downloads"
echo -e "    ${C_GREEN}✔ Directorio CORTEX estructurado en:${C_CYAN} ~/.gemini/antigravity/brain${C_RESET}"
echo -e "    ${C_GREEN}✔ Almacenamiento local estructurado en:${C_CYAN} ~/Music/downloads${C_RESET}"

# 4. Crear Entorno Virtual
echo -e "\n${C_BLUE}[*]${C_WHITE} Creando entorno virtual aislado (.venv) con $PYTHON_CMD...${C_RESET}"
if [ -d ".venv" ]; then
    echo -e "    ${C_YELLOW}⚠ Directorio .venv existente. Regenerando entorno virtual...${C_RESET}"
    rm -rf .venv
fi
$PYTHON_CMD -m venv .venv
if [ $? -eq 0 ]; then
    echo -e "    ${C_GREEN}✔ Entorno virtual creado con éxito.${C_RESET}"
else
    echo -e "${C_RED}[!] ERROR al crear el entorno virtual.${C_RESET}"
    exit 1
fi

# Activar venv
source .venv/bin/activate

# 5. Instalación de paquetes de red
echo -e "\n${C_BLUE}[*]${C_WHITE} Instalando y actualizando paquetes de red TCP P2P...${C_RESET}"
echo -e "    ${C_GREY}Actualizando gestor de paquetes pip...${C_RESET}"
pip install --upgrade pip -q
echo -e "    ${C_GREY}Instalando librería asíncrona 'aioslsk'...${C_RESET}"
pip install aioslsk -q

if [ $? -eq 0 ]; then
    echo -e "    ${C_GREEN}✔ Dependencias instaladas correctamente.${C_RESET}"
else
    echo -e "${C_RED}[!] ERROR al instalar las dependencias de Python.${C_RESET}"
    exit 1
fi

echo -e "\n${C_GREEN}┌──────────────────────────────────────────────────────────────────────────────┐${C_RESET}"
echo -e "${C_GREEN}│${C_WHITE}   SISTEMA DEPERSISTENCIA CORTEX CONFIGURADO CORRECTAMENTE                  ${C_GREEN}│${C_RESET}"
echo -e "${C_GREEN}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}"
echo -e "    ${C_CYAN}Activa tu terminal:${C_WHITE} source .venv/bin/activate${C_RESET}"
echo -e "    ${C_CYAN}Prueba latencias:  ${C_WHITE}python medir_latencia.py${C_RESET}"
echo -e "    ${C_CYAN}Agente forense:    ${C_WHITE}python descargar_forense.py --target afro_free${C_RESET}\n"
