#!/usr/bin/env bash
set -e

# MOSKV-1 APEX SINGULARITY: Kinetic Deployment Script
# Industrial Noir 2026 | C5-REAL

COLOR_BLUE="\033[38;5;27m"
COLOR_GREEN="\033[38;5;70m"
COLOR_RED="\033[38;5;160m"
COLOR_RESET="\033[0m"

echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo -e "${COLOR_BLUE}    MOSKV-1 APEX SINGULARITY — KINETIC DEPLOYMENT     ${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo ""
echo -e "Executing C5-REAL physical state mutation..."
echo ""

if ! command -v uv &> /dev/null; then
    echo -e "${COLOR_RED}[Vector] uv package manager not found. Installing uv...${COLOR_RESET}"
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

if [ -d "BABYLON-60" ]; then
    echo -e "${COLOR_GREEN}[Vector] Directory BABYLON-60 exists. Purging and pulling latest...${COLOR_RESET}"
    cd BABYLON-60
    git pull origin main
else
    echo -e "${COLOR_GREEN}[Vector] Cloning repository BABYLON-60...${COLOR_RESET}"
    git clone https://github.com/borjamoskv/BABYLON-60.git
    cd BABYLON-60
fi

echo -e "${COLOR_GREEN}[Vector] Resolving C5-REAL Thermodynamic virtual environment...${COLOR_RESET}"
uv sync --all-extras

echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo -e "${COLOR_GREEN}  DEPLOYMENT COMPLETE. EXERGY YIELD MAXIMIZED.        ${COLOR_RESET}"
echo -e "${COLOR_BLUE}======================================================${COLOR_RESET}"
echo -e "Usage:"
echo -e "  cd BABYLON-60"
echo -e "  source .venv/bin/activate"
echo -e "  python run_backend.py"
