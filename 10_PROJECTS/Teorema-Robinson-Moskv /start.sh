#!/bin/bash
# ==============================================================================
# CORTEX ECOSYSTEM MASTER EXERGY INVENTORY - START RUNNER
# ==============================================================================
# Author: Borja Moskv (SYS_ID: borjamoskv)
# Reality Level: C5-REAL
# Aesthetic: Industrial Noir 2026
# ==============================================================================

# ANSI Color Codes (Industrial Noir / YInMn Blue theme)
COLOR_YINMN="\033[38;2;43;59;229m"
COLOR_VOID="\033[38;2;10;10;10m"
COLOR_GOLD="\033[38;5;220m"
COLOR_AMBER="\033[38;5;208m"
COLOR_RESET="\033[0m"
COLOR_BOLD="\033[1m"

# Print Header
echo -e "${COLOR_YINMN}◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈${COLOR_RESET}"
echo -e "${COLOR_BOLD}   CORTEX MASTER EXERGY DASHBOARD RUNNER${COLOR_RESET}"
echo -e "   ---------------------------------------------"
echo -e "   AUTHOR:         ${COLOR_BOLD}Borja Moskv${COLOR_RESET}"
echo -e "   SYS_ID:         ${COLOR_YINMN}borjamoskv${COLOR_RESET}"
echo -e "   REALITY LEVEL:  ${COLOR_YINMN}C5-REAL${COLOR_RESET}"
echo -e "${COLOR_YINMN}◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈◈${COLOR_RESET}"
echo ""

PORT=8000
MODE="auto"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --python|-p) MODE="python"; shift ;;
        --node|-n) MODE="node"; shift ;;
        --port) PORT="$2"; shift 2 ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
done

run_node() {
    echo -e "${COLOR_BOLD}[-] Launching Server via Node.js (npx serve)...${COLOR_RESET}"
    echo -e "${COLOR_YINMN}Target Port: $PORT${COLOR_RESET}"
    echo -e "Access URL:  http://localhost:$PORT"
    echo ""
    npx -y serve . -l "$PORT"
}

run_python() {
    echo -e "${COLOR_BOLD}[-] Launching Server via Python 3 (http.server)...${COLOR_RESET}"
    echo -e "${COLOR_YINMN}Target Port: $PORT${COLOR_RESET}"
    echo -e "Access URL:  http://localhost:$PORT"
    echo ""
    python3 -m http.server "$PORT"
}

if [ "$MODE" = "node" ]; then
    run_node
elif [ "$MODE" = "python" ]; then
    run_python
else
    # Auto-detect mode
    echo -e "Checking server runtimes..."
    if command -v node >/dev/null 2>&1 && command -v npx >/dev/null 2>&1; then
        echo -e "  -> Node.js / npx detected."
        run_node
    elif command -v python3 >/dev/null 2>&1; then
        echo -e "  -> Python 3 detected."
        run_python
    else
        echo -e "${COLOR_AMBER}[!] Error: Neither Node.js (npx) nor Python 3 found in PATH.${COLOR_RESET}"
        echo -e "Please install either to run the dashboard."
        exit 1
    fi
fi
