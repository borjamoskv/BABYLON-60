#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import asyncio
import logging
from pathlib import Path
import sys
import json
import hashlib

# MOCK para el entorno roto de BABYLON-60 (paths.py no existe en el repo original)
from types import ModuleType
paths_mock = ModuleType("babylon60.core.paths")
paths_mock.AGENT_DIR = Path(".agent")
paths_mock.CORTEX_DIR = Path(".cortex")
paths_mock.MEMORY_DIR = Path(".agent/memory")
paths_mock.SYNC_STATE_FILE = Path(".agent/memory/sync_state.json")
sys.modules["babylon60.core.paths"] = paths_mock

from babylon60.extensions.daemon.sync_engine import CortexSyncManager
from babylon60.extensions.sync.common import MEMORY_DIR, SYNC_STATE_FILE, topological_file_hash, file_hash

logging.basicConfig(level=logging.DEBUG)

class DummyEngine:
    async def session(self):
        class DummySession:
            async def __aenter__(self): return self
            async def __aexit__(self, *args): pass
            async def execute(self, *args):
                class DummyCursor:
                    async def fetchall(self): return []
                return DummyCursor()
        return DummySession()

async def test_fail_stop():
    print("\n--- INICIANDO TEST DE FAIL-STOP (MERKLEPULSE) ---")
    
    # Asegurar que el directorio existe
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    
    ghosts_file = MEMORY_DIR / "ghosts.json"
    ghosts_file.write_text('{"test_project": {"mood": "hyper-focused"}}', encoding="utf-8")
    
    # Calculamos hashes reales
    real_merkle = file_hash(ghosts_file)
    real_wl = topological_file_hash(ghosts_file)
    
    # FORZAMOS LA ASIMETRÍA IMPOSIBLE (WL cambió, Merkle intacto)
    print(f"\n[+] Inyectando estado corrupto en {SYNC_STATE_FILE}")
    corrupted_state = {
        "ghosts_merkle": real_merkle,  # Merkle coincide (no hubo cambio en bytes)
        "ghosts_wl": "fake_wl_hash_12345"  # WL no coincide (supuesto cambio topológico)
    }
    
    SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(json.dumps(corrupted_state))
    
    engine = DummyEngine()
    manager = CortexSyncManager(engine)
    
    print("\n[+] Disparando el Sync Engine (run_sync_cycle)...")
    try:
        # Usamos _merkle_pulse_sync directamente para probar la detección temprana
        await manager._merkle_pulse_sync()
        print("\n[!] ERROR: El sistema NO se detuvo.")
    except RuntimeError as e:
        print(f"\n[SUCCESS] Excepción capturada exitosamente:\n{e}")

if __name__ == "__main__":
    asyncio.run(test_fail_stop())
