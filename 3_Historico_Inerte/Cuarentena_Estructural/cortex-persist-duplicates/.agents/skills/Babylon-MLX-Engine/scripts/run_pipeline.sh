#!/bin/bash
# BABYLON-60 Pipeline Runner (C5-REAL)
# Uso: bash run_pipeline.sh
set -euo pipefail

PROJ_DIR="/Users/borjafernandezangulo/30_BABYLON-60/babylon60-llm-zero"
cd "$PROJ_DIR"
source .venv/bin/activate
echo "[C5-REAL] Pipeline iniciado: $(date)"
python pipeline.py
echo "[C5-REAL] Pipeline finalizado: $(date)"
