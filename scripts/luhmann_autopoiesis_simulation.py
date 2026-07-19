import json
import hashlib
import random
import math
import sys
from pathlib import Path
from typing import Any, Dict

# Add project root to sys.path to allow absolute imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Try importing the AmendmentLedger from the apex_trials module
AmendmentLedgerClass = None
try:
    from apex_trials.ledger import AmendmentLedger

    AmendmentLedgerClass = AmendmentLedger
except ImportError:
    pass


class LuhmannAutopoiesisSimulation:
    """
    C5-REAL Simulation of a Closed Autopoietic System (Spanish Bureaucracy / RETA)
    interacting with a noisy Environment (Spanish Citizenry) via Structural Coupling.
    """

    def __init__(self, seed: int = 42, steps: int = 500) -> None:
        random.seed(seed)
        self.steps = steps
        self.system_state: Dict[str, Any] = {
            "dossiers_db": {},  # Internal database of registered dossiers
            "internal_queue": [],  # Internal communications (autopoietic loops)
            "loops_run": 0,
        }
        self.env_state: Dict[str, Any] = {
            "citizens": [
                {"id": f"citizen_{i}", "frustration": 0.0, "has_cert": random.random() > 0.3} for i in range(100)
            ],
            "total_attempts": 0,
            "dissipated_atp": 0.0,
        }
        self.successful_couplings = 0
        self.failed_couplings = 0

    def run(self) -> Dict[str, Any]:
        for step in range(self.steps):
            # 1. Environment dispatches a citizen request (Attempt of Structural Coupling)
            citizen = random.choice(self.env_state["citizens"])
            self.env_state["total_attempts"] += 1
            self.env_state["dissipated_atp"] += 1.5  # ATP cost per transaction attempt

            # Structural Coupling check (Digital Certificate signature validation)
            if citizen["has_cert"] and random.random() > 0.4:  # 60% chance signature applet works
                # Successful coupling: transaction is successfully parsed into the system's binary code (1)
                self.successful_couplings += 1
                dossier_id = f"DOSSIER_{self.successful_couplings:04d}"
                self.system_state["dossiers_db"][dossier_id] = {
                    "owner": citizen["id"],
                    "status": "INITIATED",
                    "step_count": 1,
                }
                # System injects internal communication to process the dossier (Autopoietic trigger)
                self.system_state["internal_queue"].append({"dossier_id": dossier_id, "action": "SUBSANACION_CHECK"})
            else:
                # Failed coupling: system remains closed, returns 0 (invalid signature)
                self.failed_couplings += 1
                citizen["frustration"] += 10.0  # Frustration scales on rejection
                self.env_state["dissipated_atp"] += 5.0  # Extra ATP spent cursing the Java Applet

            # 2. System executes its closed autopoietic loop (Internal communications)
            next_queue = []
            for item in self.system_state["internal_queue"]:
                self.system_state["loops_run"] += 1
                d_id = item["dossier_id"]
                action = item["action"]
                dossier = self.system_state["dossiers_db"][d_id]
                dossier["step_count"] += 1

                if action == "SUBSANACION_CHECK":
                    dossier["status"] = "PENDING_TAXES"
                    next_queue.append({"dossier_id": d_id, "action": "TAX_VALIDATION"})
                elif action == "TAX_VALIDATION":
                    dossier["status"] = "PENDING_DECISION"
                    next_queue.append({"dossier_id": d_id, "action": "RESOLVE"})
                elif action == "RESOLVE":
                    dossier["status"] = "RESOLVED"
            self.system_state["internal_queue"] = next_queue

        # Calculate metrics
        total_frustration = sum(c["frustration"] for c in self.env_state["citizens"])
        avg_frustration = total_frustration / len(self.env_state["citizens"])

        # Calculate system entropy (Shannon entropy of status distribution)
        status_counts: Dict[str, int] = {}
        for d in self.system_state["dossiers_db"].values():
            status = d["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        total_dossiers = len(self.system_state["dossiers_db"])
        system_entropy = 0.0
        if total_dossiers > 0:
            for count in status_counts.values():
                p = count / total_dossiers
                if p > 0:
                    system_entropy -= p * math.log(p)
        system_entropy = round(system_entropy, 5)

        results = {
            "steps_simulated": self.steps,
            "successful_couplings": self.successful_couplings,
            "failed_couplings": self.failed_couplings,
            "total_attempts": self.env_state["total_attempts"],
            "autopoietic_loops_executed": self.system_state["loops_run"],
            "environment_frustration_mean": round(avg_frustration, 5),
            "environment_dissipated_atp": round(self.env_state["dissipated_atp"], 5),
            "system_registered_dossiers": total_dossiers,
            "system_entropy": system_entropy,
            "coupling_success_rate": round(
                self.successful_couplings / self.env_state["total_attempts"]
                if self.env_state["total_attempts"] > 0
                else 0,
                5,
            ),
        }

        # Compute SHA3-256 of final metrics
        payload = json.dumps(results, sort_keys=True)
        results_hash = hashlib.sha3_256(payload.encode()).hexdigest()

        ledger_seq = None
        ledger_event_id = None
        ledger_entry_hash = None
        ledger_prev_hash = None

        # Persist results to master_ledger.db if available
        if AmendmentLedgerClass is not None:
            try:
                db_path = project_root / "master_ledger.db"
                ledger = AmendmentLedgerClass(db_path)
                entry = ledger.append(
                    payload=results, causal_taint="borjamoskv:luhmann_autopoiesis", agent_id="borjamoskv"
                )
                ledger_seq = entry.seq
                ledger_event_id = entry.id
                ledger_entry_hash = entry.entry_hash
                ledger_prev_hash = entry.prev_hash
            except (RuntimeError, ValueError, OSError) as e:
                # Log but proceed
                print(f"[-] Ledger write failed: {e}")
                import traceback

                traceback.print_exc()
        else:
            print("[-] AmendmentLedger not imported")

        output = {
            "metadata": {
                "author": "borjamoskv",
                "timestamp": "2026-07-17T19:25:00Z",
                "cortex_taint": f"borjamoskv:luhmann_autopoiesis:{results_hash[:16]}",
            },
            "results": results,
            "results_hash": results_hash,
            "ledger_metadata": {
                "seq": ledger_seq,
                "event_id": ledger_event_id,
                "entry_hash": ledger_entry_hash,
                "prev_hash": ledger_prev_hash,
            },
        }
        return output


if __name__ == "__main__":
    sim = LuhmannAutopoiesisSimulation()
    report = sim.run()
    print(json.dumps(report, indent=2))
