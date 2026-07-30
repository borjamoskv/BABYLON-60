#!/bin/bash
# [C5-REAL] Serve MOSKV-1 LoRA model via MLX for Arena evaluation
# Author: borjamoskv
# License: Apache-2.0
#
# Usage:
#   ./benchmarks/serve_mlx.sh [MODEL_PATH] [PORT]
#
# Defaults:
#   MODEL_PATH = ~/.babylon60/models/moskv-1-merged
#   PORT = 8000

set -euo pipefail

MODEL_PATH="${1:-$HOME/.babylon60/models/moskv-1-merged}"
PORT="${2:-8000}"

if [ ! -d "$MODEL_PATH" ]; then
    echo "[ARENA] ERROR: Model directory not found: $MODEL_PATH"
    echo "[ARENA] Expected a merged MLX model directory."
    echo "[ARENA] To merge LoRA adapters:"
    echo "  python -m mlx_lm.fuse --model <base_model> --adapter-path <lora_adapter> --save-path $MODEL_PATH"
    exit 1
fi

echo "[ARENA] Serving model: $MODEL_PATH"
echo "[ARENA] Port: $PORT"
echo "[ARENA] Endpoint: http://localhost:$PORT/v1"
echo "[ARENA] Press Ctrl+C to stop"
echo ""

python -m mlx_lm.server \
    --model "$MODEL_PATH" \
    --port "$PORT" \
    --host 0.0.0.0
