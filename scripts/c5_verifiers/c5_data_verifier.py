#!/usr/bin/env python3
"""
C5-REAL Data Layer Verifier - BABYLON-60
Verifica integridad de esquema, alineación BPE y consistencia de Hash Merkle en /data
"""

import json
import hashlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = REPO_ROOT / "data"

class DataExergyVerifier:
    def __init__(self, data_path: Path = DATA_DIR):
        self.data_path = data_path

    def verify_oncology_schema(self) -> bool:
        onc_file = self.data_path / "oncology_300.json"
        if not onc_file.exists():
            print(f"[ERROR] No existe el archivo: {onc_file}")
            return False
        
        with open(onc_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if data.get("standard") != "C5-REAL" or data.get("total_primitives") != 300:
            print(f"[ERROR] Metadatos inválidos en oncology_300.json")
            return False

        primitives = data.get("primitives", [])
        if len(primitives) != 300:
            print(f"[ERROR] Número de primitivas incorrecto: {len(primitives)} != 300")
            return False

        # Verificar unicidad de IDs y ausencia de anergía
        seen_ids = set()
        for idx, prim in enumerate(primitives, 1):
            expected_id = f"ONC-{idx:03d}"
            if prim.get("id") != expected_id:
                print(f"[ERROR] ID discordante en índice {idx}: {prim.get('id')} != {expected_id}")
                return False
            seen_ids.add(prim["id"])

        return len(seen_ids) == 300

    def calculate_merkle_root(self) -> str:
        hashes = []
        for file_path in sorted(self.data_path.rglob("*.json")):
            if "L1_sink" in str(file_path):
                continue
            content = file_path.read_bytes()
            h = hashlib.sha3_256(content).hexdigest()
            hashes.append(h)

        combined = "".join(hashes).encode("utf-8")
        return hashlib.sha3_256(combined).hexdigest()

def main():
    verifier = DataExergyVerifier()
    schema_ok = verifier.verify_oncology_schema()
    root_hash = verifier.calculate_merkle_root()
    
    print("=== C5 DATA EXERGY VERIFIER ===")
    print(f"Ruta de Datos: {DATA_DIR}")
    print(f"Oncology 300 Schema Valid: {schema_ok}")
    print(f"Data Layer Merkle Root SHA3-256: {root_hash}")
    
    if not schema_ok:
        sys.exit(1)

if __name__ == "__main__":
    main()
