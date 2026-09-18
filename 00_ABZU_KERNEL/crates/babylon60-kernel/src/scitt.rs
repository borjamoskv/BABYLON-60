use ed25519_dalek::{Signature, Signer, SigningKey, VerifyingKey};

/// COSE_Sign1 Headers y Payload fijos (simplificados para no_std).
/// Estructura conceptual CBOR COSE_Sign1: [protected, unprotected, payload, signature]
/// En esta implementación C5-REAL, retornamos la firma cruda Ed25519 (64 bytes)
/// sobre el Hash SHA-256 o estado del epoch envenenado.
pub struct ScittReceipt {
    pub epoch_halted: u64,
    pub signature: [u8; 64],
}

impl ScittReceipt {
    /// Genera un recibo criptográfico de parada epistémica firmado.
    /// Para cumplir con el determinismo `#![no_std]`, inyectamos un SigningKey explícito.
    pub fn new(epoch_id: u64, secret_key_bytes: &[u8; 32]) -> Self {
        // En producción las claves provienen de un HSM o C-ABI inyectado.
        let signing_key = SigningKey::from_bytes(secret_key_bytes);
        
        // El payload a firmar es el epoch serializado (representación simbólica del estado)
        let payload = epoch_id.to_le_bytes();
        
        // Ed25519 es determinista, por lo que no necesita rand::Rng
        let signature: Signature = signing_key.sign(&payload);
        
        Self {
            epoch_halted: epoch_id,
            signature: signature.to_bytes(),
        }
    }

    /// Verifica que el recibo proviene de la clave pública del Kernel Soberano.
    pub fn verify(&self, public_key_bytes: &[u8; 32]) -> bool {
        use ed25519_dalek::Verifier;
        if let Ok(verifying_key) = VerifyingKey::from_bytes(public_key_bytes) {
            let payload = self.epoch_halted.to_le_bytes();
            let sig = Signature::from_bytes(&self.signature);
            return verifying_key.verify(&payload, &sig).is_ok();
        }
        false
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_scitt_receipt_generation_and_verification() {
        // [AX-4] Criptografía determinista: Par de claves de prueba.
        let secret_bytes = [0u8; 32]; // Cero-Entropía (Solo para tests)
        let signing_key = SigningKey::from_bytes(&secret_bytes);
        let pub_key = signing_key.verifying_key().to_bytes();

        let epoch_id = 9942; // Referencia RFC 9942
        
        // Generamos el recibo
        let receipt = ScittReceipt::new(epoch_id, &secret_bytes);
        
        assert_eq!(receipt.epoch_halted, 9942);
        
        // Verificamos la firma
        assert!(receipt.verify(&pub_key), "La firma del recibo SCITT debe ser válida matemáticamente.");
    }
}
