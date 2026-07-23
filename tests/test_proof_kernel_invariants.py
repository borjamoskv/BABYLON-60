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
    ev1 = {"a": 1, "b": 2, "c": b"raw_data", "d": {1, 2}}
    ev2 = {"d": {2, 1}, "b": 2, "c": b"raw_data", "a": 1}
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
    """Ω170 · Minimality Executable Test (Microbits)"""
    prior_microbits = 1000000
    posterior_microbits = 1500000
    with pytest.raises(ValueError, match="Epistemic Monotonicity"):
        compute_information_gain(prior_microbits, posterior_microbits)
        
    assert compute_information_gain(1000000, 1000000) == 0, "No exergy implies pruning under Ω170"
    assert compute_information_gain(1000000, 469000) == 531000, "Fractional bits preserved in microbits"

def test_closure_certificate():
    """Ω171 · Completeness Certificate Executable Test (Epsilon Threshold)"""
    state = {"resolved": True}
    proof_hash = hash_evidence(state)
    
    cert = ClosureCertificate(state, proof_hash, residual_microbits=500, epsilon_threshold=1000)
    assert cert.verify() is True, "Ω171 Violated: Valid certificate rejected under threshold."
    
    with pytest.raises(ValueError, match="Residual entropy"):
        ClosureCertificate(state, proof_hash, residual_microbits=1500, epsilon_threshold=1000)

def test_replay_determinism():
    """Ω172 · Replay Determinism Executable Test"""
    evidence = {"id": "SIGABRT", "frame": "llvm"}
    
    assert verify_replay_determinism(evidence, proof_pipeline) is True

def test_kernel_minimality():
    """Ω173 · Kernel Minimality Executable Test"""
    from proof_kernel.semantics import verify_kernel_minimality
    
    assert verify_kernel_minimality(verifier_rules_count=3, generator_rules_count=10) is True
    with pytest.raises(ValueError, match="Verifier TCB is larger"):
        verify_kernel_minimality(verifier_rules_count=5, generator_rules_count=5)

def test_versioned_semantics():
    """Ω174 · Versioned Semantics Executable Test"""
    from proof_kernel.semantics import execute_with_versioned_semantics
    evidence = {"event": "crash"}
    
    res = execute_with_versioned_semantics(
        proof_pipeline, evidence,
        semantics_version="1.3.0",
        ruleset_version="2.1.1",
        kernel_version="0.4.2"
    )
    assert res["context"]["semantics"] == "1.3.0"
    
    with pytest.raises(ValueError, match="versioned semantics"):
        execute_with_versioned_semantics(proof_pipeline, evidence, "", "", "")
