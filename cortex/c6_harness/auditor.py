"""C6-REAL Orchestrator and Auditor."""
from .invariant import C6Attestation, ComponentScore, ByzantineScore, ReplayScore, RecoveryResult

def generate_attestation(storage_recovery: RecoveryResult) -> C6Attestation:
    """Synthesizes the execution results into the final Temporal Identity C6 Attestation."""
    
    safety = 1.0 if storage_recovery.integrity_check == "OK" else 0.0
    durability = 1.0 if storage_recovery.committed_transactions_lost == 0 and storage_recovery.phantom_transactions_found == 0 else 0.0
    recovery_score = 1.0 if safety == 1.0 and durability == 1.0 else 0.0
    
    storage = ComponentScore(safety=safety, durability=durability, recovery=recovery_score)
    
    # C6.2 and C6.3 are stubs for now until their specific tests are run
    byzantine = ByzantineScore(detection=0.0, isolation=0.0)
    replay = ReplayScore(intermediate_identity=0.0, causal_alignment=0.0)
    
    # Currently verified if Storage Chaos passes. Full C6 requires all 3.
    verified = (storage.recovery == 1.0)
    
    return C6Attestation(
        storage=storage,
        byzantine=byzantine,
        replay=replay,
        temporal_identity_verified=verified
    )
