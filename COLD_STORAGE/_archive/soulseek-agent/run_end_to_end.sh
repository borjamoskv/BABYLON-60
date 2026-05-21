#!/bin/bash
# ==============================================================================
# CORTEX SOBERANO · ORQUESTADOR MAESTRO END-TO-END v2.0
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
echo -e "${C_BLUE}│${C_WHITE}   CORTEX-PERSIST · ORQUESTADOR MAESTRO END-TO-END v2.0                    ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}│${C_GREY}   Despliegue Completo Automático e Integración C5-REAL de Mac-Optimizer  ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}\n"

# 1. Ejecutar optimización de macOS Kernel (requiere privilegios sudo)
echo -e "${C_BLUE}[*]${C_WHITE} PASO 1/3: Optimizando el Kernel y descriptores TCP (requiere sudo)...${C_RESET}"
if [ "$EUID" -ne 0 ]; then
    echo -e "    ${C_YELLOW}ℹ Invocando privilegios temporales con sudo para ejecutar optimize_mac.sh...${C_RESET}"
    sudo ./optimize_mac.sh
    if [ $? -ne 0 ]; then
        echo -e "${C_RED}[!] ERROR al optimizar el kernel. Fricción termodinámica no resuelta.${C_RESET}"
        exit 1
    fi
else
    ./optimize_mac.sh
fi

# 2. Ejecutar aprovisionamiento del ecosistema e instalación de CORTEX
echo -e "\n${C_BLUE}[*]${C_WHITE} PASO 2/3: Aprovisionando el entorno CORTEX y dependencias P2P...${C_RESET}"
# Asegurar permisos de ejecución
chmod +x ./install_cortex.sh
./install_cortex.sh
if [ $? -ne 0 ]; then
    echo -e "${C_RED}[!] ERROR al instalar el ecosistema CORTEX.${C_RESET}"
    exit 1
fi

# Activar entorno virtual para los pasos interactivos
source .venv/bin/activate

# 3. Pruebas interactivas opcionales
echo -e "\n${C_BLUE}[*]${C_WHITE} PASO 3/3: Verificación interactiva del estado de red...${C_RESET}"
echo -e -n "    ¿Deseas ejecutar un diagnóstico rápido de latencia TCP RTT (y/n)? ${C_WHITE}"
read -r check_lat
echo -e "${C_RESET}"

if [[ "$check_lat" =~ ^[Yy]$ ]]; then
    echo -e "${C_BLUE}[*]${C_WHITE} Ejecutando test de latencia TCP contra hosts P2P...${C_RESET}"
    python medir_latencia.py
fi

echo -e "\n${C_GREEN}┌──────────────────────────────────────────────────────────────────────────────┐${C_RESET}"
echo -e "${C_GREEN}│${C_WHITE}   DESPLIEGUE COMPLETO EXITOSO · NODO DE ALAIN PREPARADO Y OPERATIVO        ${C_GREEN}│${C_RESET}"
echo -e "${C_GREEN}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}"
echo -e "    ${C_CYAN}Para iniciar la adquisición forense de activos musicales:${C_RESET}"
echo -e "    ${C_WHITE}source .venv/bin/activate${C_RESET}"
echo -e "    ${C_WHITE}python descargar_forense.py --target afro_free${C_RESET}\n"
