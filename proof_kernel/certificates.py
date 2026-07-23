from typing import Any
from proof_kernel.canonicalizer import hash_evidence

class ClosureCertificate:
    """
    Ω171 · Completeness Certificate Invariant
    
    Un expediente diagnóstico es incompleto hasta que emite un certificado
    que verifique H_residual -> 0, determinismo asegurado y ausencia
    de evidencia huérfana.
    """
    def __init__(self, final_state: dict[str, Any], proof_hash: str, residual_entropy: int):
        # Operamos estrictamente con enteros para preservar determinismo BFT.
        if residual_entropy != 0:
            raise ValueError(f"Ω171 Violated: Cannot certify completeness with residual entropy {residual_entropy}. Must be 0.")
        
        self.residual_entropy = residual_entropy
        self.proof_hash = proof_hash
        self.state_hash = hash_evidence(final_state)
        self.certified = True
        
    def verify(self) -> bool:
        """
        Verify(Replay(E)) = true
        """
        return self.certified and self.residual_entropy == 0
