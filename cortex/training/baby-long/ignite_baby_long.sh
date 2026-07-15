#!/bin/zsh
# C5-REAL: IGNICIÓN DE MOTOR BABY-LONG
# MLX-LM LoRA Training Pipeline (Regla Ε2)

DATA_DIR="./data"
ADAPTER_PATH="./adapters/baby-long"
BASE_MODEL="mlx-community/Mistral-7B-Instruct-v0.3-4bit"

echo "[*] Iniciando destilación de entropía en BABY-LONG..."
mlx_lm.lora --train \
    --model $BASE_MODEL \
    --data $DATA_DIR \
    --iters 50 \
    --batch-size 2 \
    --num-layers 16 \
    --adapter-path $ADAPTER_PATH

echo "[*] Entrenamiento completado. Compilando pesos..."
mlx_lm.fuse \
    --model $BASE_MODEL \
    --adapter-path $ADAPTER_PATH \
    --save-path ./models/baby-long-fused

echo "[*] BABY-LONG FORJADO."
