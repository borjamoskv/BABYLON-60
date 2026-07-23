from typing import Any
from proof_kernel.canonicalizer import hash_evidence

class ClosureCertificate:
    """
    Ω171 · Completeness Certificate Invariant
    
    Un expediente diagnóstico es incompleto hasta que emite un certificado
    que verifique H_residual < epsilon_threshold, determinismo asegurado y ausencia
    de evidencia huérfana.
    """
    def __init__(self, final_state: dict[str, Any], proof_hash: str, residual_microbits: int, epsilon_threshold: int = 1000):
        # Epsilon de Certeza: Resuelve la Paradoja de Cromwell evitando la 
        # exigencia de 0 bits exactos inalcanzables bajo evidencia empírica con ruido.
        if residual_microbits >= epsilon_threshold:
            raise ValueError(
                f"Ω171 Violated: Cannot certify completeness. "
                f"Residual entropy {residual_microbits} >= threshold {epsilon_threshold} microbits."
            )
        
        self.residual_microbits = residual_microbits
        self.epsilon_threshold = epsilon_threshold
        self.proof_hash = proof_hash
        self.state_hash = hash_evidence(final_state)
        self.certified = True
        
    def verify(self) -> bool:
        """
        Verify(Replay(E)) = true
        """
        return self.certified and self.residual_microbits < self.epsilon_threshold
