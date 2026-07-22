"""C6-REAL Attestation & Invariants."""
from dataclasses import dataclass
from typing import Dict, Any
import json

@dataclass
class RecoveryResult:
    integrity_ok: bool
    committed_transactions_lost: int
    phantom_transactions_found: int
    recovery_idempotent: bool
    state_hash_stable: bool

@dataclass
class C6Attestation:
    experiment_id: str
    environment: Dict[str, str]
    attacks_injected: int
    
    # Booleans replace scores
    safety_pass: bool
    durability_pass: bool
    recovery_pass: bool
    
    # Specifics
    committed_tx_loss: int
    corruption_detected: bool
    replay_deterministic: bool
    
    witness_hash: str

    def to_yaml_str(self) -> str:
        data = {
            "C6_Attestation": {
                "experiment": {
                    "id": self.experiment_id
                },
                "environment": self.environment,
                "attacks": {
                    "injected": self.attacks_injected
                },
                "results": {
                    "durability": "PASS" if self.durability_pass else "FAIL",
                    "recovery": "PASS" if self.recovery_pass else "FAIL",
                    "safety": "PASS" if self.safety_pass else "FAIL",
                    "committed_tx_loss": self.committed_tx_loss,
                    "corruption": self.corruption_detected,
                    "replay": "deterministic" if self.replay_deterministic else "divergent"
                },
                "witness_hash": self.witness_hash
            }
        }
        return json.dumps(data, indent=2)
