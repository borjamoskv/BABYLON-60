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

def verify_kernel_minimality(verifier_ast_nodes: int, generator_ast_nodes: int) -> bool:
    """
    Ω173 · Kernel Minimality Invariant
    El núcleo de verificación (TCB) debe ser estrictamente más simple 
    (en complejidad de AST / Kolmogorov) que el motor generador.
    """
    if verifier_ast_nodes >= generator_ast_nodes:
        raise ValueError(
            f"Ω173 Violated: Verifier complexity ({verifier_ast_nodes} AST nodes) "
            f"exceeds or equals Generator complexity ({generator_ast_nodes} AST nodes). "
            "The TCB is too large."
        )
    return True
