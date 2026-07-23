from typing import Any
from proof_kernel.canonicalizer import hash_evidence

class ClosureCertificate:
    """
    Ω171 · Completeness Certificate Invariant
    
    Un expediente diagnóstico es incompleto hasta que emite un certificado
    que verifique H_residual < epsilon_threshold, determinismo asegurado y ausencia
    de evidencia huérfana. Incorpora Triple Enlace Criptográfico para evitar Grafting.
    """
    def __init__(self, evidence_hash: str, ruleset_hash: str, final_state: dict[str, Any], residual_microbits: int, epsilon_threshold: int = 1000):
        # Epsilon de Certeza
        if residual_microbits >= epsilon_threshold:
            raise ValueError(
                f"Ω171 Violated: Cannot certify completeness. "
                f"Residual entropy {residual_microbits} >= threshold {epsilon_threshold} microbits."
            )
        
        self.residual_microbits = residual_microbits
        self.epsilon_threshold = epsilon_threshold
        
        # Triple Cryptographic Bind
        self.evidence_hash = evidence_hash
        self.ruleset_hash = ruleset_hash
        self.state_hash = hash_evidence(final_state)
        
        # Combine hashes (naive concatenation hashed)
        combined = {"E": self.evidence_hash, "R": self.ruleset_hash, "S": self.state_hash, "M": self.residual_microbits}
        self.cert_hash = hash_evidence(combined)
        self.certified = True
        
    def verify(self) -> bool:
        """
        Ω171 / Tamper-Evident Verification.
        Recalculates the internal cryptographic hash to prove memory immutability.
        """
        combined = {"E": self.evidence_hash, "R": self.ruleset_hash, "S": self.state_hash, "M": self.residual_microbits}
        current_hash = hash_evidence(combined)
        
        if current_hash != self.cert_hash:
            raise ValueError(f"Ω171 Violated: Certificate Tampering Detected. Hash mismatch: {current_hash} != {self.cert_hash}")
            
        return self.certified and self.residual_microbits < self.epsilon_threshold
