#!/usr/bin/env bash
# Experimento 2: Transcripción de Ejecución DEMO
set -euo pipefail

echo "🧪 Ejecutando Síntesis Sonora PCM con Cadenas de Markov..."
python3 cortex/laboratory/segundo_experimento_c5/03_codigo.py
ls -lh cortex/laboratory/segundo_experimento_c5/synth.wav
