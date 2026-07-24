import cbor2
from typing import Any, Callable
from proof_kernel.canonicalizer import canonicalize_cbor, hash_evidence

def replay(evidence: dict[str, Any], proof_pipeline: Callable[[dict[str, Any]], dict[str, Any]]) -> dict[str, Any]:
    """
    Reconstruye una prueba derivando un nuevo estado epistémico 
    exclusivamente desde la representación canónica de la evidencia (CBOR).
    """
    canonical_ev_bytes = canonicalize_cbor(evidence)
    canonical_evidence = cbor2.loads(canonical_ev_bytes)
    return proof_pipeline(canonical_evidence)

def verify_replay_determinism(evidence: dict[str, Any], proof_pipeline: Callable[[dict[str, Any]], dict[str, Any]]) -> bool:
    """
    Ω172 · Replay Determinism
    
    Garantiza axiomáticamente que la evaluación cruda produce 
    el mismo estado que la evaluación canónica pura:
    ∀E, Replay(E) == Replay(Canonicalize(E))
    """
    res_direct = proof_pipeline(evidence)
    
    res_canonical = replay(evidence, proof_pipeline)
    
    hash_direct = hash_evidence(res_direct)
    hash_canonical = hash_evidence(res_canonical)
    
    if hash_direct != hash_canonical:
        raise RuntimeError(
            f"Ω172 Violated: Replay determinism failed.\n"
            f"Direct hash: {hash_direct}\n"
            f"Canonical hash: {hash_canonical}"
        )
    return True
