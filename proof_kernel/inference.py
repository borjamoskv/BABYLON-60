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

def compute_information_gain(prior_microbits: int, posterior_microbits: int) -> int:
    """
    Ω162 · Falsification Power Invariant & Ω163 · Residual Entropy
    La confianza emerge del Information Gain.
    
    Para cumplir con INV_C5_18 (exclusión de flotantes BFT) sin destruir
    exergía matemática (truncamientos a 0), la Entropía de Shannon se 
    calcula y propaga en 'microbits' (1 bit = 1,000,000 microbits).
    """
    if prior_microbits < posterior_microbits:
        raise ValueError("Epistemic Monotonicity (Ω155) violated: entropy increased.")
    return prior_microbits - posterior_microbits
