"""C6-REAL Orchestrator and Auditor."""
import hashlib
from typing import Dict, Optional
from .invariant import C6Attestation, RecoveryResult, ByzantineResult

def generate_witness_hash(data: Dict[str, str]) -> str:
    m = hashlib.sha3_256()
    for k, v in sorted(data.items()):
        m.update(k.encode('utf-8'))
        m.update(str(v).encode('utf-8'))
    return m.hexdigest()

def generate_attestation(
    experiment_id: str, 
    environment: Dict[str, str], 
    attacks_injected: int, 
    storage_recovery: Optional[RecoveryResult] = None,
    byzantine_result: Optional[ByzantineResult] = None,
    replay_deterministic: bool = True
) -> C6Attestation:
    """Synthesizes the execution results into the final Temporal Identity C6 Attestation."""
    
    # Evaluate Storage
    if storage_recovery:
        safety_pass = storage_recovery.integrity_ok
        durability_pass = (storage_recovery.committed_transactions_lost == 0 and storage_recovery.phantom_transactions_found == 0)
        recovery_pass = storage_recovery.recovery_idempotent and storage_recovery.state_hash_stable
        committed_tx_loss = storage_recovery.committed_transactions_lost
        corruption = not storage_recovery.integrity_ok
    else:
        safety_pass = True
        durability_pass = True
        recovery_pass = True
        committed_tx_loss = 0
        corruption = False

    # Evaluate Byzantine
    if byzantine_result:
        byzantine_pass = (
            byzantine_result.reachable_invalid_state == 0 and
            byzantine_result.attacks_isolated == attacks_injected and
            byzantine_result.history_preserved == attacks_injected
        )
    else:
        byzantine_pass = True
        
    # Witness hash computation based on results
    witness_data = {
        "exp": experiment_id,
        "attacks": str(attacks_injected),
        "safety": str(safety_pass),
        "durability": str(durability_pass),
        "recovery": str(recovery_pass),
        "byzantine": str(byzantine_pass),
        "replay": str(replay_deterministic)
    }
    witness_hash = generate_witness_hash(witness_data)
    
    return C6Attestation(
        experiment_id=experiment_id,
        environment=environment,
        attacks_injected=attacks_injected,
        safety_pass=safety_pass,
        durability_pass=durability_pass,
        recovery_pass=recovery_pass,
        byzantine_pass=byzantine_pass,
        committed_tx_loss=committed_tx_loss,
        corruption_detected=corruption,
        replay_deterministic=replay_deterministic,
        witness_hash=witness_hash
    )
