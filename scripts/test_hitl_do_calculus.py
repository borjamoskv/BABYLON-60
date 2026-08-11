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
import time

# MOCK para el entorno roto
from types import ModuleType
paths_mock = ModuleType("babylon60.core.paths")
paths_mock.AGENT_DIR = Path(".agent")
paths_mock.CORTEX_DIR = Path(".cortex")
paths_mock.MEMORY_DIR = Path(".agent/memory")
paths_mock.SYNC_STATE_FILE = Path(".agent/memory/sync_state.json")
sys.modules["babylon60.core.paths"] = paths_mock

from babylon60.extensions.daemon.sync_engine import CortexSyncManager
from babylon60.extensions.sync.common import MEMORY_DIR, SYNC_STATE_FILE, topological_file_hash, file_hash
from babylon60.extensions.swarm.verification_gate import VerificationGate, RiskLevel, InterventionChannel

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

async def test_do_calculus_surgery():
    print("\n--- INICIANDO TEST DE CIRUGÍA DO-CALCULUS (HITL) ---")
    
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    ghosts_file = MEMORY_DIR / "ghosts.json"
    ghosts_file.write_text('{"test_project": {"mood": "bifurcating"}}', encoding="utf-8")
    
    real_merkle = file_hash(ghosts_file)
    corrupted_state = {
        "ghosts_merkle": real_merkle, 
        "ghosts_wl": "fake_wl_hash_bifurcated"
    }
    
    SYNC_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    SYNC_STATE_FILE.write_text(json.dumps(corrupted_state))
    
    print("\n[+] 1. EMITIENDO AUTORIZACIÓN HUMANA (HARD_SURGERY)...")
    gate = VerificationGate(str(MEMORY_DIR / "hitl.db"))
    gate.register_sign_off(
        execution_id="EXEC-TEST-SURGERY",
        action_name="Bifurcate Causal Graph",
        risk_level=RiskLevel.CRITICAL,
        decision="APPROVED",
        intervention_channel=InterventionChannel.HARD_SURGERY
    )
    
    engine = DummyEngine()
    manager = CortexSyncManager(engine)
    
    print("\n[+] 2. Disparando el Sync Engine (MerklePulse)...")
    try:
        await manager._merkle_pulse_sync()
        print("\n[SUCCESS] El sistema asimiló la bifurcación causal correctamente sin crashear.")
    except RuntimeError as e:
        print(f"\n[!] ERROR: El sistema hizo FAIL-STOP ignorando la autorización:\n{e}")

if __name__ == "__main__":
    asyncio.run(test_do_calculus_surgery())
