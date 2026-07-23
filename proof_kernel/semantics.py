from typing import Any, Callable

def execute_with_versioned_semantics(
    proof_pipeline: Callable, 
    evidence: dict[str, Any], 
    semantics_version: str, 
    ruleset_version: str, 
    kernel_version: str
) -> dict[str, Any]:
    """
    Ω174 · Versioned Semantics Invariant
    Una prueba no es "válida" en absoluto, es "válida bajo las versiones x.y.z".
    """
    if not (semantics_version and ruleset_version and kernel_version):
        raise ValueError("Ω174 Violated: Execution lacks versioned semantics context.")
    
    result = proof_pipeline(evidence)
    # The result is wrapped in the exact versioning context that produced it
    return {
        "conclusion": result,
        "context": {
            "semantics": semantics_version,
            "ruleset": ruleset_version,
            "kernel": kernel_version
        }
    }

def verify_kernel_minimality(verifier_rules_count: int, generator_rules_count: int) -> bool:
    """
    Ω173 · Kernel Minimality (Trusted Computing Base) Invariant
    El conjunto de reglas de verificación debe ser estrictamente menor
    al de generación para evitar colapsos de auto-legitimación.
    """
    if verifier_rules_count >= generator_rules_count:
        raise ValueError("Ω173 Violated: Verifier TCB is larger than or equal to the Generator.")
    return True
