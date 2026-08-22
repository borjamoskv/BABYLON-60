#!/usr/bin/env bash
# ==============================================================================
# QWEN 3.8 SOVEREIGN RUNNER — APPLE SILICON M3 PRO (18 GB RAM)
# Ecosistema C5-REAL / BABYLON-60 — Capa Abductiva de Inferencia Local
# ==============================================================================

set -euo pipefail

# Colores y Formato
BOLD="\033[1m"
GREEN="\033[32m"
CYAN="\033[36m"
YELLOW="\033[33m"
RED="\033[31m"
RESET="\033[0m"

# Invariantes de Hardware
EXPECTED_CHIP="M3 Pro"
EXPECTED_RAM_GB=18
DEFAULT_WIRED_MEM_MB=15360

show_usage() {
    echo -e "${BOLD}Uso:${RESET} $0 [OPCIONES]"
    echo ""
    echo -e "${BOLD}Modos de Operación:${RESET}"
    echo "  -f, --fast     Modo Inferencia Rápida: Qwen 3.8 9B (~50 t/s) - Código diario y autocompletado"
    echo "  -d, --deep     Modo Razonamiento Profundo: Qwen 3.8 27B (Q3/Q4) - Abducción y Arquitectura"
    echo "  -b, --backend  Motor de inferencia: 'ollama' (default) o 'mlx'"
    echo "  -t, --tune     Ajustar sysctl iogpu.wired_mem_limit a ${DEFAULT_WIRED_MEM_MB}MB para M3 Pro"
    echo "  -i, --info     Mostrar telemetría física de memoria y chip Apple Silicon"
    echo "  -h, --help     Mostrar esta ayuda"
    echo ""
    echo -e "${BOLD}Ejemplos:${RESET}"
    echo "  $0 --fast"
    echo "  $0 --deep --backend mlx"
    echo "  $0 --tune"
}

check_hardware() {
    echo -e "${CYAN}[C5-HARDWARE] Verificando sustrato físico Apple Silicon...${RESET}"
    
    if [[ "$(uname)" != "Darwin" ]]; then
        echo -e "${RED}[ERROR] Este script requiere macOS.${RESET}"
        exit 1
    fi

    SYS_CHIP=$(sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Apple Silicon")
    SYS_MEM_BYTES=$(sysctl -n hw.memsize 2>/dev/null || echo "0")
    SYS_MEM_GB=$((SYS_MEM_BYTES / 1024 / 1024 / 1024))

    echo -e "  • Chip detectado: ${BOLD}${SYS_CHIP}${RESET}"
    echo -e "  • Memoria Unificada: ${BOLD}${SYS_MEM_GB} GB${RESET}"

    CURRENT_WIRED=$(sysctl -n iogpu.wired_mem_limit 2>/dev/null || echo "Desconocido")
    echo -e "  • Límite Metal iogpu.wired_mem_limit: ${BOLD}${CURRENT_WIRED}${RESET} bytes"
}

tune_metal_memory() {
    echo -e "${YELLOW}[C5-TUNE] Configurando límite de Memoria Unificada Metal a ${DEFAULT_WIRED_MEM_MB} MB...${RESET}"
    echo -e "${CYAN}Ejecutando: sudo sysctl iogpu.wired_mem_limit=${DEFAULT_WIRED_MEM_MB}${RESET}"
    sudo sysctl iogpu.wired_mem_limit=${DEFAULT_WIRED_MEM_MB}
    echo -e "${GREEN}[OK] Memoria Metal sintonizada para 18 GB RAM (M3 Pro).${RESET}"
}

run_ollama() {
    local model="$1"
    echo -e "${GREEN}[C5-RUNNER] Iniciando inferencia local via Ollama: ${BOLD}${model}${RESET}"
    if ! command -v ollama &>/dev/null; then
        echo -e "${RED}[ERROR] 'ollama' CLI no encontrado en PATH. Instálalo desde https://ollama.com${RESET}"
        exit 1
    fi
    ollama run "${model}"
}

run_mlx() {
    local model_repo="$1"
    echo -e "${GREEN}[C5-RUNNER] Iniciando inferencia local nativa via MLX (mlx-lm): ${BOLD}${model_repo}${RESET}"
    if ! python3 -c "import mlx_lm" &>/dev/null; then
        echo -e "${YELLOW}[AVISO] 'mlx-lm' no está instalado en el entorno de Python. Instalando...${RESET}"
        pip install -q mlx-lm
    fi
    python3 -m mlx_lm.chat --model "${model_repo}"
}

# Parsing de argumentos
MODE=""
BACKEND="ollama"

while [[ $# -gt 0 ]]; do
    case "$1" in
        -f|--fast)
            MODE="fast"
            shift
            ;;
        -d|--deep)
            MODE="deep"
            shift
            ;;
        -b|--backend)
            BACKEND="$2"
            shift 2
            ;;
        -t|--tune)
            tune_metal_memory
            exit 0
            ;;
        -i|--info)
            check_hardware
            exit 0
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            echo -e "${RED}[ERROR] Opción desconocida: $1${RESET}"
            show_usage
            exit 1
            ;;
    esac
done

if [[ -z "${MODE}" ]]; then
    check_hardware
    echo ""
    echo -e "${YELLOW}[!] Selecciona un modo de operación:${RESET}"
    echo "  1) Modo FAST (Qwen 3.8 9B - Diario / 50 t/s)"
    echo "  2) Modo DEEP (Qwen 3.8 27B - Razonamiento Profundo)"
    read -p "Opción [1/2]: " opt
    case "$opt" in
        1) MODE="fast" ;;
        2) MODE="deep" ;;
        *) echo "Cancelado."; exit 0 ;;
    esac
fi

check_hardware

echo ""
if [[ "${MODE}" == "fast" ]]; then
    echo -e "${BOLD}${CYAN}>>> LANZANDO: Modo FAST (Qwen 3.8 9B) <<<${RESET}"
    if [[ "${BACKEND}" == "ollama" ]]; then
        run_ollama "qwen3.8:9b"
    else
        run_mlx "mlx-community/Qwen3.8-9B-Instruct-4bit"
    fi
elif [[ "${MODE}" == "deep" ]]; then
    echo -e "${BOLD}${CYAN}>>> LANZANDO: Modo DEEP (Qwen 3.8 27B) <<<${RESET}"
    echo -e "${YELLOW}[CONSEJO] Si notas tirantes en memoria, ejecuta '$0 --tune' previamente.${RESET}"
    if [[ "${BACKEND}" == "ollama" ]]; then
        run_ollama "qwen3.8:27b-instruct-q4_K_S"
    else
        run_mlx "mlx-community/Qwen3.8-27B-Instruct-4bit"
    fi
fi
