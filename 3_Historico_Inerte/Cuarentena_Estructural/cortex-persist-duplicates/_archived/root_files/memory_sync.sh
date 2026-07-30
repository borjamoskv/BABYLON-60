#!/bin/bash
export CORTEX_NO_OMEGA=1
export CORTEX_VIRGO_MODE=TEST
export CORTEX_NO_TAINT_ENFORCE=1
export BABYLON_SYNC_MODE=BATCH
export BABYLON_FORCE_UPDATE=1

cd /Users/borjafernandezangulo/30_BABYLON-60 || exit 1

echo "[C5-REAL] Introduciendo Facts Ontológicos en BABYLON-60..."
.venv/bin/python -m babylon60.cli memory store-batch _facts.json
rm _facts.json

echo "[C5-REAL] Exportando Snapshot Global..."
.venv/bin/python -m babylon60.cli export
