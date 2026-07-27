#!/bin/bash
# BABYLON-60 Quick Eval (C5-REAL)
# Uso: bash quick_eval.sh
set -euo pipefail

PROJ_DIR="/Users/borjafernandezangulo/30_BABYLON-60/babylon60-llm-zero"
cd "$PROJ_DIR"
source .venv/bin/activate
echo "[C5-REAL] Evaluación rápida iniciada: $(date)"
python evaluate.py
echo "[C5-REAL] Evaluación completada: $(date)"
