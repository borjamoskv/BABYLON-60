import copy
from typing import Any, Callable

def pure_inference(evidence_state: dict[str, Any], rules: list[Callable[[dict[str, Any]], dict[str, Any]]]) -> dict[str, Any]:
    """
    Ω166 · Pure Inference (Referential Transparency)
    Ejecuta el pipeline de derivación como una función matemática pura.
    
    Args:
        evidence_state: Estado de evidencia canónico
        rules: Lista de reglas de transición (funciones puras)
        
    Returns:
        Un nuevo estado inferencial mutado por las reglas.
    """
    # Se garantiza inmutabilidad del input
    state = copy.deepcopy(evidence_state)
    for rule in rules:
        state = rule(state)
    return state

def compute_information_gain(prior_entropy: int, posterior_entropy: int) -> int:
    """
    Ω162 · Falsification Power Invariant
    La confianza emerge del Information Gain, no de adjetivos estocásticos.
    (Operamos con bits enteros para evitar flotantes no deterministas, Ω18/INV_C5_18).
    """
    if prior_entropy < posterior_entropy:
        raise ValueError("Epistemic Monotonicity (Ω155) violated: entropy increased.")
    return prior_entropy - posterior_entropy
