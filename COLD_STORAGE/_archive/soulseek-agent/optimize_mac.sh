#!/bin/bash
# ==============================================================================
# CORTEX SOBERANO · MACOS KERNEL OPTIMIZER
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
echo -e "${C_BLUE}│${C_WHITE}   CORTEX-PERSIST · OPTIMIZADOR DEL KERNEL MACOS v2.0                       ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}│${C_GREY}   Configuración BSD de Alto Rendimiento para Concurrencia de Sockets P2P   ${C_BLUE}│${C_RESET}"
echo -e "${C_BLUE}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}\n"

# Verificar privilegios de root
if [ "$EUID" -ne 0 ]; then
  echo -e "${C_RED}[!] ERROR: Este script requiere privilegios sudo para modificar el kernel.${C_RESET}"
  echo -e "    Por favor, ejecútalo como: ${C_WHITE}sudo ./optimize_mac.sh${C_RESET}"
  exit 1
fi

# Apply system control variables in hot state
echo -e "${C_BLUE}[*]${C_WHITE} Aplicando parámetros de kernel sysctl en caliente...${C_RESET}"

sysctl -w kern.maxfiles=122880 >/dev/null
echo -e "    ${C_GREEN}✔ Límite total de descriptores: kern.maxfiles = 122880${C_RESET}"

sysctl -w kern.maxfilesperproc=10240 >/dev/null
echo -e "    ${C_GREEN}✔ Límite por proceso: kern.maxfilesperproc = 10240${C_RESET}"

sysctl -w net.inet.tcp.sendspace=65536 >/dev/null
echo -e "    ${C_GREEN}✔ Búfer de salida TCP: net.inet.tcp.sendspace = 65536${C_RESET}"

sysctl -w net.inet.tcp.recvspace=65536 >/dev/null
echo -e "    ${C_GREEN}✔ Búfer de entrada TCP: net.inet.tcp.recvspace = 65536${C_RESET}"

sysctl -w kern.ipc.somaxconn=2048 >/dev/null
echo -e "    ${C_GREEN}✔ Cola de conexiones sockets: kern.ipc.somaxconn = 2048${C_RESET}"

# Generar persistencia de sysctl con backup de seguridad
SYSCTL_CONF="/etc/sysctl.conf"
echo -e "\n${C_BLUE}[*]${C_WHITE} Configurando persistencia del sistema en ${C_CYAN}$SYSCTL_CONF${C_WHITE}...${C_RESET}"

if [ -f "$SYSCTL_CONF" ]; then
    BACKUP_PATH="${SYSCTL_CONF}.bak.$(date +%F_%H%M%S)"
    echo -e "    ${C_YELLOW}⚠ Archivo existente. Creando copia de seguridad en: $BACKUP_PATH${C_RESET}"
    cp "$SYSCTL_CONF" "$BACKUP_PATH"
fi

cat << EOF > $SYSCTL_CONF
kern.maxfiles=122880
kern.maxfilesperproc=10240
net.inet.tcp.sendspace=65536
net.inet.tcp.recvspace=65536
kern.ipc.somaxconn=2048
EOF

if [ $? -eq 0 ]; then
    echo -e "    ${C_GREEN}✔ Archivo de persistencia de kernel configurado con éxito.${C_RESET}"
else
    echo -e "    ${C_RED}✘ Fallo al escribir persistencia en $SYSCTL_CONF.${C_RESET}"
fi

# Configuración del ulimit en el perfil de terminal
echo -e "\n${C_BLUE}[*]${C_WHITE} Configurando persistencia de sesión 'ulimit' en shells del usuario...${C_RESET}"

# Encontrar el directorio home del usuario no-root que invocó sudo
REAL_USER_HOME=$(eval echo "~$SUDO_USER")

# Comprobar .zshrc
if [ -f "${REAL_USER_HOME}/.zshrc" ]; then
    if ! grep -q "ulimit -n 4096" "${REAL_USER_HOME}/.zshrc"; then
        echo -e "    ${C_CYAN}[+] Agregando 'ulimit -n 4096' automáticamente a ~/.zshrc...${C_RESET}"
        echo -e "\n# CORTEX SOBERANO P2P OPTIMIZATION\nulimit -n 4096" >> "${REAL_USER_HOME}/.zshrc"
        echo -e "    ${C_GREEN}✔ Modificado ~/.zshrc con éxito.${C_RESET}"
    else
        echo -e "    ${C_GREEN}✔ ~/.zshrc ya configurado con 'ulimit -n 4096'.${C_RESET}"
    fi
fi

# Comprobar .bash_profile
if [ -f "${REAL_USER_HOME}/.bash_profile" ]; then
    if ! grep -q "ulimit -n 4096" "${REAL_USER_HOME}/.bash_profile"; then
        echo -e "    ${C_CYAN}[+] Agregando 'ulimit -n 4096' automáticamente a ~/.bash_profile...${C_RESET}"
        echo -e "\n# CORTEX SOBERANO P2P OPTIMIZATION\nulimit -n 4096" >> "${REAL_USER_HOME}/.bash_profile"
        echo -e "    ${C_GREEN}✔ Modificado ~/.bash_profile con éxito.${C_RESET}"
    fi
fi

echo -e "\n${C_GREEN}┌──────────────────────────────────────────────────────────────────────────────┐${C_RESET}"
echo -e "${C_GREEN}│${C_WHITE}   OPTIMIZACIÓN DE KERNEL MACOS APLICADA Y PERSISTIDA CORRECTAMENTE         ${C_GREEN}│${C_RESET}"
echo -e "${C_GREEN}└──────────────────────────────────────────────────────────────────────────────┘${C_RESET}\n"
