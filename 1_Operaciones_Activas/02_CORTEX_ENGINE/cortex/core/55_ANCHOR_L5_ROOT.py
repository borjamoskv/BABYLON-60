# C5-REAL EXERGY CERTIFIED
"""
55_ANCHOR_L5_ROOT.py (C5-REAL Certified)
----------------------------------------
Transductor para anclar el estado raíz consolidado del Ledger L1
(SQLite WAL) en Bitcoin mediante OpenTimestamps.
Cierra el ciclo termodinámico BFT de L1 a L5.
"""
import asyncio
import sqlite3
import sys
import hashlib
from pathlib import Path

import importlib
L5Anchor = importlib.import_module("l5_opentimestamps").BlockchainAnchor

async def anchor_ledger_root():
    db_path = Path("stress_ledger.db")
    storage_dir = Path("l5_anchors")

    if not db_path.exists():
        print("[💥 ERR] El ledger L1 no existe. Debes ejecutar el asalto de estrés primero.")
        sys.exit(1)

    print("\n[🔗 L5] Extrayendo raíz de Merkle (aproximada) del Ledger L1...")

    # Calcular el hash acumulativo del master_ledger para representar su estado global
    hasher = hashlib.sha3_256()
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT entry_hash FROM master_ledger ORDER BY created_at ASC")
        rows = cursor.fetchall()

    if not rows:
        print("[💥 ERR] El ledger L1 está vacío.")
        sys.exit(1)

    for row in rows:
        hasher.update(row[0].encode('utf-8'))

    root_hash = hasher.hexdigest()
    print(f"[🔗 L5] Root Hash consolidado: {root_hash}")

    anchor = L5Anchor(storage_dir)
    ots_file = await anchor.anchor_hash(root_hash)

    if ots_file:
        print("\n[🛡️ L5 SECURE] Ciclo Termodinámico Cerrado. Estado L1 anclado criptográficamente en OTS.")
        sys.exit(0)
    else:
        print("\n[💥 REFUTED] Fricción en L5. No se pudo generar el sello.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(anchor_ledger_root())
