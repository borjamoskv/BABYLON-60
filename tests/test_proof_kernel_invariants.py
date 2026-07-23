import pytest
from proof_kernel.canonicalizer import canonicalize, hash_evidence
from proof_kernel.inference import pure_inference, compute_information_gain
from proof_kernel.replay import replay, verify_replay_determinism
from proof_kernel.certificates import ClosureCertificate

def dummy_rule(state: dict) -> dict:
    state["processed"] = True
    return state

def proof_pipeline(evidence: dict) -> dict:
    return pure_inference(evidence, [dummy_rule])

def test_semantic_preservation():
    """Ω167 · Semantic Preservation Executable Test"""
    evidence = {"event": "crash", "id": 1}
    state_t1 = proof_pipeline(evidence)
    state_t2 = proof_pipeline(evidence)
    assert state_t1 == state_t2, "Ω167 Violated: Semantic output mutated without evidence shift."

def test_canonicalization():
    """Ω168 · Canonical Representation Executable Test"""
    ev1 = {"a": 1, "b": 2}
    ev2 = {"b": 2, "a": 1}
    assert hash_evidence(ev1) == hash_evidence(ev2), "Ω168 Violated: Isomorphic states produced diverging hashes."
    
    # Float prohibition
    with pytest.raises(ValueError):
        hash_evidence({"a": 1.5})

def test_proof_derivation():
    """Ω169 · Proof-Carrying Diagnosis Executable Test"""
    evidence = {"event": "crash", "id": 1}
    result = proof_pipeline(evidence)
    assert result.get("processed") is True, "Ω169 Violated: Proof derivation pipeline failed execution."

def test_minimality():
    """Ω170 · Minimality Executable Test"""
    prior_entropy = 5
    posterior_entropy = 6
    with pytest.raises(ValueError, match="Epistemic Monotonicity"):
        compute_information_gain(prior_entropy, posterior_entropy)
        
    assert compute_information_gain(5, 5) == 0, "No exergy implies pruning under Ω170"

def test_closure_certificate():
    """Ω171 · Completeness Certificate Executable Test"""
    state = {"resolved": True}
    proof_hash = hash_evidence(state)
    
    cert = ClosureCertificate(state, proof_hash, residual_entropy=0)
    assert cert.verify() is True, "Ω171 Violated: Valid certificate rejected."
    
    with pytest.raises(ValueError, match="residual entropy"):
        ClosureCertificate(state, proof_hash, residual_entropy=1)

def test_replay_determinism():
    """Ω172 · Replay Determinism Executable Test"""
    evidence = {"id": "SIGABRT", "frame": "llvm"}
    
    # ∀E, Replay(E) == Replay(Canonicalize(E))
    assert verify_replay_determinism(evidence, proof_pipeline) is True
