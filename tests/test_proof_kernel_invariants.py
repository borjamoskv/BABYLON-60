import pytest
from proof_kernel.inference import compute_information_gain, dag_inference
from proof_kernel.canonicalizer import hash_evidence
from proof_kernel.certificates import ClosureCertificate
from proof_kernel.crdt import CRDTMap
from proof_kernel.ast_rule import ASTRule
from proof_kernel.semantics import verify_kernel_minimality

def test_canonicalization():
    """Ω168 · Canonical Representation Executable Test"""
    ev1 = {"a": 1, "b": 2, "c": b"raw_data", "d": {1, 2}}
    ev2 = {"d": {2, 1}, "b": 2, "c": b"raw_data", "a": 1}
    assert hash_evidence(ev1) == hash_evidence(ev2), "Ω168 Violated: Isomorphic states produced diverging hashes."
    
    with pytest.raises(ValueError):
        hash_evidence({"a": 1.5})

def test_crdt_merge():
    """CRDT Map Deterministic Merge Test"""
    map1 = CRDTMap()
    map1.set("keyA", "val1", 10)
    map1.set("keyB", "valB", 5)
    
    map2 = CRDTMap()
    map2.set("keyA", "val2", 20) # higher lamport
    map2.set("keyB", "valB_new", 2) # lower lamport
    
    merged = map1.merge(map2)
    assert merged.get("keyA") == "val2"
    assert merged.get("keyB") == "valB"

def test_ast_rule():
    """Ω165 / Ω166 AST Rule Binding Test"""
    def dummy_rule(state: CRDTMap) -> CRDTMap:
        state.set("mutated", True, 100)
        return state
        
    rule = ASTRule(dummy_rule)
    assert rule.get_hash() is not None
    
    initial = CRDTMap()
    result = rule.execute(initial)
    assert result.get("mutated") is True

def test_ast_purity_auditor():
    """Ω166 · Pure Inference Impurity Escape Test"""
    def impure_import(state: CRDTMap) -> CRDTMap:
        import time
        state.set("time", time.time(), 1)
        return state
        
    with pytest.raises(ValueError, match="Imports are prohibited"):
        ASTRule(impure_import)
        
    def impure_eval(state: CRDTMap) -> CRDTMap:
        eval("1 + 1")
        return state
        
    with pytest.raises(ValueError, match="Call to impure function 'eval'"):
        ASTRule(impure_eval)

def test_proof_derivation():
    """Ω169 · Proof-Carrying Diagnosis Executable Test (DAG Mode)"""
    def r1(s: CRDTMap) -> CRDTMap:
        s.set("A", 1, 1)
        return s
    
    def r2(s: CRDTMap) -> CRDTMap:
        s.set("B", 2, 2)
        return s
        
    rules = {"node1": ASTRule(r1), "node2": ASTRule(r2)}
    dag = {"node1": ["node2"]}
    initial = CRDTMap()
    
    result, entropy = dag_inference(initial, dag, rules)
    
    result, entropy = dag_inference(initial, dag, rules)
    
    assert result.get("A") == 1
    assert result.get("B") == 2
    assert entropy >= 0

def test_epistemic_monotonicity():
    """Ω155 · Epistemic Monotonicity Executable Test"""
    # A prior cannot have less entropy than a posterior
    assert compute_information_gain(prior_microbits=1000, posterior_microbits=500) == 500
    with pytest.raises(ValueError, match="entropy increased"):
        compute_information_gain(prior_microbits=500, posterior_microbits=1000)

def test_closure_certificate():
    """Ω171 · Completeness Certificate Executable Test (Triple Bind)"""
    state = {"resolved": True}
    e_hash = "evidence_root"
    r_hash = "ruleset_root"
    
    cert = ClosureCertificate(e_hash, r_hash, state, residual_microbits=500, epsilon_threshold=1000)
    assert cert.verify() is True, "Ω171 Violated: Valid certificate rejected under threshold."
    assert hasattr(cert, 'cert_hash')
    
    with pytest.raises(ValueError, match="Residual entropy"):
        ClosureCertificate(e_hash, r_hash, state, residual_microbits=1500, epsilon_threshold=1000)

def test_certificate_tampering():
    """Ω171 · Tamper-Evident Verification Test"""
    state = {"resolved": True}
    cert = ClosureCertificate("e_hash", "r_hash", state, residual_microbits=500, epsilon_threshold=1000)
    assert cert.verify() is True
    
    # Simulate memory tampering (Agent dynamically changes microbits to 0)
    cert.residual_microbits = 0
    with pytest.raises(ValueError, match="Certificate Tampering Detected"):
        cert.verify()

def test_kernel_minimality():
    """Ω173 · Kernel Minimality AST-based Test"""
    # Verifier must be strictly simpler than Generator
    assert verify_kernel_minimality(verifier_ast_nodes=50, generator_ast_nodes=100) is True
    
    with pytest.raises(ValueError, match="TCB is too large"):
        verify_kernel_minimality(verifier_ast_nodes=150, generator_ast_nodes=100)
        
    with pytest.raises(ValueError, match="TCB is too large"):
        verify_kernel_minimality(verifier_ast_nodes=100, generator_ast_nodes=100)
