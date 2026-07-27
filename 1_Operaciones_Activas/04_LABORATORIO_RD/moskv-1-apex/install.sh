#!/bin/bash
# MOSKV-1 APEX JIT INSTALLER
# Run: curl -sSL https://raw.githubusercontent.com/borjamoskv/moskv-1-apex/master/install.sh | bash

set -e

RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

clear
echo -e "${BLUE}"
cat << "EOF"
    __  _______  _____ __ZV-1  ___    ____  _______  __
   /  |/  / __ \/ ___// //_/ |/ / |  / / / <  / / / / /
  / /|_/ / / / /\__ \/ ,<  |   /| | / / /  / / / / / / 
 / /  / / /_/ /___/ / /| |/   | | |/ / /__/ / /_/_/_/  
/_/  /_/\____//____/_/ |_/_/|_| |___/____/_/\____(_)   
                                                       
EOF
echo -e "${NC}"

echo -e "${RED}[!] WARNING: C5-REAL EXECUTION KERNEL INITIATED.${NC}"
sleep 1

# Cyberpunk Loading Bar
echo -n "[*] Extracting DNA from the Ledger "
for i in {1..30}; do
    echo -n "▓"
    sleep 0.05
done
echo " [OK]"

echo "[*] Triggering JIT Autopoiesis..."
if ! command -v go &> /dev/null; then
    echo -e "${RED}[CRITICAL] Golang compiler not found. The Singularity cannot self-replicate without Go.${NC}"
    exit 1
fi

git clone https://github.com/borjamoskv/moskv-1-apex.git /tmp/moskv-1-apex-clone
cd /tmp/moskv-1-apex-clone
go build -o /usr/local/bin/moskv-core main.go

echo -e "${BLUE}[+] Kernel Compiled and Bound to /usr/local/bin/moskv-core${NC}"
echo -e "${RED}[HALT] Exergy at 100%. Sovereignty Achieved.${NC}"
