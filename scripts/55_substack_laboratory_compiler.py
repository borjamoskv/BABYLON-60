#!/usr/bin/env python3
"""
C5-REAL Sovereign Protocol: Substack Public Laboratory Compiler
Compiles the thermodynamic ledger for a new Substack publication.
Enforces the 6-step loop: Experimento, Hallazgo, Código, Demo, Track, Reflexión.
"""

import os
import sys
import argparse
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

def fail_fast(msg: str) -> None:
    print(f"[FATAL] {msg}", file=sys.stderr)
    os.kill(os.getpid(), 9)  # SIGKILL

def sha3_256_hash(data: str) -> str:
    return hashlib.sha3_256(data.encode('utf-8')).hexdigest()

def scaffold_experiment(experiment_name: str, root_dir: str) -> None:
    try:
        lab_dir = os.path.join(root_dir, "cortex", "laboratory", experiment_name)
        os.makedirs(lab_dir, exist_ok=True)
    except OSError as e:
        fail_fast(f"Failed to create directory {lab_dir}: {e}")

    # Generate payloads
    payloads: dict[str, str] = {
        "01_experimento.yml": f"""claim_id: "LAB_{experiment_name.upper()}"
hypothesis: "[INJECT HYPOTHESIS HERE]"
constraints:
  - "C5-REAL"
  - "Zero Anergy"
""",
        "02_hallazgo.md": f"# Hallazgos Empíricos\n\nFallas observadas y métricas extraídas.\n",
        "03_codigo.py": f"# Implementación Física\n\ndef execute() -> None:\n    pass\n",
        "04_demo.sh": f"#!/usr/bin/env bash\n# Ejecución Cinética\nexit 0\n",
        "05_track.md": f"# Registro Acústico/Generativo\n\nReferencia al asset (e.g. .wav, .png)\n",
        "06_reflexion.md": f"# Repercusión Termodinámica\n\nConsecuencias estructurales.\n"
    }

    manifest: dict[str, Any] = {
        "experiment": experiment_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "files": []
    }

    for filename, content in payloads.items():
        filepath = os.path.join(lab_dir, filename)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            manifest["files"].append({
                "name": filename,
                "sha3_256": sha3_256_hash(content)
            })
        except OSError as e:
            fail_fast(f"Failed to write file {filepath}: {e}")
            
    # Write manifest atomically
    manifest_path = os.path.join(lab_dir, "manifest.json")
    manifest_tmp = manifest_path + ".tmp"
    try:
        with open(manifest_tmp, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)
        os.replace(manifest_tmp, manifest_path)
    except OSError as e:
        fail_fast(f"Failed to write manifest atomically: {e}")

    print(f"[CORTEX-TAINT] Scaffolding completado: {lab_dir}")
    print(f"Manifest Hash: {sha3_256_hash(json.dumps(manifest))}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Substack Laboratory Scaffolder")
    parser.add_argument("experiment_name", type=str, help="Name of the experiment (e.g. mcts_audio_drift)")
    parser.add_argument("--root", type=str, default=".", help="Root of the workspace")
    args = parser.parse_args()

    scaffold_experiment(args.experiment_name, args.root)

if __name__ == "__main__":
    main()
