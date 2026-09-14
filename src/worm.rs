use crate::receipt::Signer;
use sha2::{Digest, Sha256};
use core::sync::atomic::{compiler_fence, Ordering};
extern crate alloc;
use alloc::vec::Vec;
use alloc::vec;

#[derive(Clone, Debug)]
/// Entrada individual inmutable de la cadena WORM.
pub struct WormEntry {
    /// Índice monótono de la entrada.
    pub index: u64,
    /// Carga útil (Halt payload o SCITT receipt).
    pub payload: Vec<u8>,
    /// Firma asimétrica (EdDSA / Ed25519) del enclave.
    pub signature: Vec<u8>,
    /// Hash encadenado de la entrada.
    pub hash: [u8; 32],
}

/// Registro WORM (Write Once Read Many) respaldado por Hash-Chaining.
pub struct WormLedger {
    chain: Vec<WormEntry>,
    /// Clave pública del hardware enclave, utilizada para certificar la estructura (SCITT).
    #[allow(dead_code)]
    pub enclave_pubkey: Vec<u8>,
}

impl WormLedger {
    /// Crea un nuevo WORM Ledger con su bloque génesis.
    pub fn new(enclave_pubkey: Vec<u8>) -> Self {
        let genesis = WormEntry {
            index: 0,
            payload: b"BABYLON-60: GENESIS".to_vec(),
            signature: vec![],
            hash: [0u8; 32],
        };
        Self {
            chain: vec![genesis],
            enclave_pubkey,
        }
    }

    /// Añade un nuevo recibo al WORM. Falla si la firma es inválida según el Signer (TEE).
    pub fn append<S: Signer>(&mut self, payload: &[u8], signature: &[u8], signer: &S) -> Result<[u8; 32], &'static str> {
        // Validar la firma utilizando el hardware signer (Enclave)
        if !signer.verify(payload, signature) {
            return Err("Rechazo WORM: Firma del TEE invalida");
        }

        // Hash-Chaining: H(prev_hash || payload || signature)
        let prev_hash = self.chain.last().unwrap().hash;
        let mut hasher = Sha256::new();
        hasher.update(&prev_hash);
        hasher.update(payload);
        hasher.update(signature);
        let new_hash: [u8; 32] = hasher.finalize().into();

        let entry = WormEntry {
            index: self.chain.len() as u64,
            payload: payload.to_vec(),
            signature: signature.to_vec(),
            hash: new_hash,
        };
        
        self.chain.push(entry);
        compiler_fence(Ordering::SeqCst);
        
        Ok(new_hash)
    }

    /// Audita toda la cadena criptográfica
    pub fn audit_integrity(&self) -> bool {
        for i in 1..self.chain.len() {
            let prev = &self.chain[i - 1];
            let curr = &self.chain[i];
            
            let mut hasher = Sha256::new();
            hasher.update(&prev.hash);
            hasher.update(&curr.payload);
            hasher.update(&curr.signature);
            let expected_hash: [u8; 32] = hasher.finalize().into();
            
            if curr.hash != expected_hash {
                return false;
            }
        }
        true
    }
}
