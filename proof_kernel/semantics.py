from typing import Any, Callable

def execute_with_versioned_semantics(proof_pipeline: Callable[..., Any], evidence: dict[str, Any], semantics_version: str, ruleset_version: str, kernel_version: str) -> dict[str, Any]:
    if not (semantics_version and ruleset_version and kernel_version):
        raise ValueError('Ω174 Violated: Execution lacks versioned semantics context.')
    result = proof_pipeline(evidence)
    return {'conclusion': result, 'context': {'semantics': semantics_version, 'ruleset': ruleset_version, 'kernel': kernel_version}}

def verify_kernel_minimality(verifier_ast_nodes: int, generator_ast_nodes: int) -> bool:
    if verifier_ast_nodes >= generator_ast_nodes:
        raise ValueError(f'Ω173 Violated: Verifier complexity ({verifier_ast_nodes} AST nodes) exceeds or equals Generator complexity ({generator_ast_nodes} AST nodes). The TCB is too large.')
    return True