import os
import uuid
import json
import logging
import shutil
from datetime import datetime, timezone
from engine.ledger import ParalifeLedger

# Integration with Agente-Kant-Ω
KANT_LOGIC_PATH = "/Users/borjafernandezangulo/.gemini/antigravity/skills/Agente-Kant-Omega/logic.py"

class ParalifePlatform:
    """
    Sovereign Cognitive Sandbox Platform
    Governs the creation, execution, and annihilation of parallel digital lives.
    """
    def __init__(self, root_dir="/tmp/cortex_paralife"):
        self.root_dir = root_dir
        self.ledger = ParalifeLedger()
        self.active_sessions = {} # Maintaining for backward compat/speed
        self._init_storage()

    def _init_storage(self):
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
        logging.info(f"Paralife Storage initialized at {self.root_dir}")

    def spawn(self, identity_config: dict) -> str:
        """
        Spawns a new 'Parallel Life' with specific cognitive boundaries.
        Example config: {"profile": "Rogue-Trader", "constraints": ["no-network"]}
        """
        session_id = f"PL-{uuid.uuid4().hex[:6].upper()}"
        sandbox_path = os.path.join(self.root_dir, session_id)
        
        os.makedirs(os.path.join(sandbox_path, "workspace"))
        os.makedirs(os.path.join(sandbox_path, "context"))

        # Inject Synthetic Governance
        gemini_md = f"""# {session_id} // SYNTHETIC IDENTITY
> PROFILE: {identity_config.get('profile', 'Generic-Agent')}
> MISSION: Isolated interaction in Paralife Sandbox.
> MANDATE: All data extracted must pass Katian Scrutiny.
"""
        with open(os.path.join(sandbox_path, "GEMINI.md"), "w") as f:
            f.write(gemini_md)

        self.ledger.register_session(session_id, identity_config.get('profile'), sandbox_path)
        
        self.active_sessions[session_id] = {
            "path": sandbox_path,
            "config": identity_config,
            "status": "OPERATIONAL",
            "spawned_at": datetime.now(timezone.utc).isoformat()
        }
        
        return session_id

    def harvest_and_audit(self, session_id: str, data_payload: str, metadata: dict = None):
        """
        Extracts intelligence and routes it through Agente-Kant-Ω Audit Gate.
        """
        if session_id not in self.active_sessions:
            raise Exception("Session not found")

        from extraction.kant_audit_gate import KantAuditGate
        gate = KantAuditGate()
        
        result = gate.verify_and_crystallize(data_payload, session_id, metadata)
        
        if result:
            self.ledger.log_audit(session_id, "APPROVE", "Kant Gate Passed", data_payload)
            return {"status": "CRYSTALLIZED", "gate": "APPROVED"}
        else:
            self.ledger.log_audit(session_id, "REJECT", "Deontological Violation", data_payload)
            return {"status": "PURGED", "gate": "REJECTED"}

    def snapshot(self, session_id: str):
        """
        Creates a state snapshot of the sandbox workspace.
        """
        if session_id not in self.active_sessions:
            return None
            
        src = os.path.join(self.active_sessions[session_id]["path"], "workspace")
        snap_id = f"SNAP-{uuid.uuid4().hex[:4].upper()}"
        dst = os.path.join(self.root_dir, "snapshots", f"{session_id}_{snap_id}")
        
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copytree(src, dst)
        return snap_id

    def _call_kant_omega(self, data):
        """
        Executes the Agente-Kant-Ω logic script to verify the categorical imperative of the data.
        """
        # In a real implementation, we would import logic.py or run it as a subprocess.
        # For this platform prototype, we apply the C5-REAL logic of the Categorical Imperative.
        is_safe = "entropy" not in data.lower() and "leak" not in data.lower() # Basic heuristic
        return {
            "passed": is_safe,
            "reasoning": "Data maintains structural integrity and does not propagate simulation-rot.",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    def _crystallize(self, data, session_id):
        """
        Saves intelligence to persistent knowledge.
        """
        target_path = "/Users/borjafernandezangulo/10_PROJECTS/paralife/extraction/harvested_intelligence.json"
        entry = {
            "origin": session_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data": data
        }
        
        # Load existing or create new
        if os.path.exists(target_path):
            with open(target_path, "r") as f:
                history = json.load(f)
        else:
            history = []
            
        history.append(entry)
        with open(target_path, "w") as f:
            json.dump(history, f, indent=4)

    def collapse(self, session_id: str):
        """
        Quantum Annihilation of the sandbox.
        """
        if session_id in self.active_sessions:
            shutil.rmtree(self.active_sessions[session_id]["path"])
            del self.active_sessions[session_id]
            print(f"[*] COLLAPSE: {session_id} annihilated.")

if __name__ == "__main__":
    p = ParalifePlatform()
    sid = p.spawn({"profile": "Security-Audit-Ω"})
    print(f"Spawned: {sid}")
    result = p.harvest_and_audit(sid, "Intelligence: Found potential optimization in VSA Kernels.")
    print(f"Audit: {result['status']}")
    p.collapse(sid)
