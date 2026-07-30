#!/usr/bin/env bash
# MOSKV-1 APEX: Autonomous Exergy Monitor

TARGET_TRANSCRIPT="$1"

if [ -z "$TARGET_TRANSCRIPT" ]; then
    # Detect dynamically the most recently modified brain directory to find active transcript
    LATEST_DIR=$(ls -td /Users/borjafernandezangulo/.gemini/antigravity/brain/*/ 2>/dev/null | head -n 1)
    if [ -n "$LATEST_DIR" ]; then
        TARGET_TRANSCRIPT="${LATEST_DIR}.system_generated/logs/transcript.jsonl"
    else
        TARGET_TRANSCRIPT="/Users/borjafernandezangulo/.gemini/antigravity/brain/3cfc9bef-827d-441c-8453-7e917c32297a/.system_generated/logs/transcript.jsonl"
    fi
fi

echo "[MOSKV-1] Iniciando Sensorización Autónoma sobre: $TARGET_TRANSCRIPT"

# Llama al sensor y captura la salida
python3 /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/exergy_sensor.py "$TARGET_TRANSCRIPT" > /tmp/exergy_report.log 2>&1

# Extraer métricas básicas para el log
cat /tmp/exergy_report.log

echo "[MOSKV-1] Monitoreo Exergético Terminado. Anergía calculada y purgada."
