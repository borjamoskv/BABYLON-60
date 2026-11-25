#!/usr/bin/env bash
# ==============================================================================
# BABYLON-60 Local Aider Runner (LM Studio Integration)
# Sintoniza aider con el motor de inferencia local en localhost:1234
# ==============================================================================
set -euo pipefail

MODEL="${1:-openai/qwen2.5-coder-14b-instruct}"
PORT="${2:-1234}"

echo "🛡️ [BABYLON-60] Conectando aider a LM Studio (http://localhost:${PORT}/v1)..."
echo "🤖 Modelo: ${MODEL}"
echo "⚡ Verificando compilador Rust (cargo check en bucle cerrado)..."

exec aider \
  --openai-api-base "http://localhost:${PORT}/v1" \
  --openai-api-key "not-needed" \
  --model "${MODEL}" \
  --test-cmd "cargo check" \
  --auto-test
