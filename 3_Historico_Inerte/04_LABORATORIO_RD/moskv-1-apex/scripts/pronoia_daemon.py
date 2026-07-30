#!/usr/bin/env python3
"""
MOSKV-1 APEX: PRONOIA DAEMON
C5-REAL Execution.

This script acts as a daemon to log "Exergy Anomalies" (e.g., Cenit Atractor triggers, 
Efracción del Corzo events) directly into the Cortex Ledger.
"""

import sys
import yaml
import datetime
from pathlib import Path

LEDGER_PATH = Path(__file__).parent.parent / "cortex" / "pronoia_ledger.yaml"

def append_anomaly(anomaly_type, context, exergy_gain):
    LEDGER_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": anomaly_type,
        "context": context,
        "exergy_gain": float(exergy_gain),
        "status": "C5-REAL"
    }

    ledger_data = {"anomalies": []}
    
    if LEDGER_PATH.exists():
        with open(LEDGER_PATH, 'r') as f:
            existing = yaml.safe_load(f)
            if existing and "anomalies" in existing:
                ledger_data = existing

    ledger_data["anomalies"].append(entry)

    with open(LEDGER_PATH, 'w') as f:
        yaml.dump(ledger_data, f, default_flow_style=False, sort_keys=False)

    print(f"[C5-REAL] Anomaly Crystallized in {LEDGER_PATH}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: pronoia_daemon.py <anomaly_type> <context> <exergy_gain>")
        sys.exit(1)
        
    append_anomaly(sys.argv[1], sys.argv[2], sys.argv[3])
