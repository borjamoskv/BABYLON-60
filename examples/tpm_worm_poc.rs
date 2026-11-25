use ed25519_dalek::{Signature, Signer as DalekSigner, SigningKey, Verifier};
use rand::rngs::OsRng;
use sha2::{Digest, Sha256};
use std::sync::atomic::{compiler_fence, Ordering};
use std::time::{Duration, Instant};

/// =========================================================================
/// [AX-?] TOPOLOGY: Hardware Enclave & WORM Ledger PoC
/// =========================================================================
///
/// Invariante de Hardware (Falsacion de TEE)
pub trait HardwareEnclave {
    fn sign(&self, payload: &[u8]) -> Vec<u8>;
    fn verify(&self, payload: &[u8], signature: &[u8]) -> bool;
    fn get_public_key(&self) -> Vec<u8>;
}

/// Mock de TPM 2.0 con simulacion de latencia criptografica
pub struct MockTpm2 {
    signing_key: SigningKey,
    simulated_latency: Duration,
}

impl MockTpm2 {
    pub fn new(latency_ms: u64) -> Self {
        let mut csprng = OsRng;
        let signing_key = SigningKey::generate(&mut csprng);
        Self {
            signing_key,
            simulated_latency: Duration::from_millis(latency_ms),
        }
    }
}

impl HardwareEnclave for MockTpm2 {
    fn sign(&self, payload: &[u8]) -> Vec<u8> {
        if self.simulated_latency.as_nanos() > 0 {
            std::thread::sleep(self.simulated_latency);
        }
        let signature = self.signing_key.sign(payload);
        signature.to_bytes().to_vec()
    }

    fn verify(&self, payload: &[u8], signature_bytes: &[u8]) -> bool {
        if signature_bytes.len() != 64 {
            return false;
        }
        let sig = Signature::from_bytes(signature_bytes.try_into().expect("BFT Fallback"));
        self.signing_key.verify(payload, &sig).is_ok()
    }

    fn get_public_key(&self) -> Vec<u8> {
        self.signing_key.verifying_key().to_bytes().to_vec()
    }
}

/// =========================================================================
/// Registro WORM (Write Once Read Many) Estricto
/// =========================================================================

#[derive(Clone, Debug)]
pub struct WormEntry {
    pub index: u64,
    pub payload: Vec<u8>,
    pub signature: Vec<u8>,
    pub hash: [u8; 32],
}

pub struct WormLedger {
    chain: Vec<WormEntry>,
    enclave_pubkey: Vec<u8>,
}

impl WormLedger {
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

    pub fn append(&mut self, payload: &[u8], signature: &[u8]) -> Result<[u8; 32], &'static str> {
        use ed25519_dalek::{Signature, VerifyingKey};
        let vk = VerifyingKey::from_bytes(self.enclave_pubkey.as_slice().try_into().expect("BFT Fallback"))
            .map_err(|_| "Clave publica del enclave invalida")?;
        
        if signature.len() != 64 {
            return Err("Longitud de firma incorrecta");
        }
        let sig = Signature::from_bytes(signature.try_into().expect("BFT Fallback"));
        vk.verify(payload, &sig).map_err(|_| "Rechazo WORM: Firma del TEE invalida")?;

        let prev_hash = self.chain.last().expect("BFT Fallback").hash;
        let mut hasher = Sha256::new();
        hasher.update(prev_hash);
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

    pub fn audit_integrity(&self) -> bool {
        for i in 1..self.chain.len() {
            let prev = &self.chain[i - 1];
            let curr = &self.chain[i];
            
            let mut hasher = Sha256::new();
            hasher.update(prev.hash);
            hasher.update(&curr.payload);
            hasher.update(&curr.signature);
            let expected_hash: [u8; 32] = hasher.finalize().into();
            
            if curr.hash != expected_hash {
                return false;
            }
        }
        true
    }

    pub fn force_corruption(&mut self, target_index: usize, tampered_payload: &[u8]) {
        if target_index < self.chain.len() {
            self.chain[target_index].payload = tampered_payload.to_vec();
        }
    }
}

/// =========================================================================
/// Falsacion Termodinamica (PoC & Stress Testing Invariant)
/// =========================================================================
///
fn run_stress_test(iterations: usize) {
    println!("> Iniciando Prueba de Estres TEE / WORM...");
    println!("> Iteraciones objetivo: {}", iterations);
    
    let enclave = MockTpm2::new(0);
    let mut ledger = WormLedger::new(enclave.get_public_key());

    let start = Instant::now();
    for i in 1..=iterations {
        let payload = format!("C5-REAL Transaction #{}", i);
        let signature = enclave.sign(payload.as_bytes());
        ledger.append(payload.as_bytes(), &signature).expect("Fallo critico en WORM");
    }
    let elapsed = start.elapsed();
    
    println!("  [+] {} registros sellados en WORM exitosamente.", iterations);
    println!("  [+] Tiempo total: {:?}", elapsed);
    println!("  [+] Latencia media por transaccion: {:.2} ms/op", elapsed.as_secs_f64() * 1000.0 / iterations as f64);
    
    assert!(ledger.audit_integrity(), "[-] FRACTURA EPISTEMICA: Integridad WORM violada durante carga de estres.");
    println!("  [+] Integridad criptografica del WORM: VERIFICADA.");

    println!("\n> Simulando Ataque Bizantino retrospectivo...");
    ledger.force_corruption(500, b"MALICIOUS_PAYLOAD");
    if !ledger.audit_integrity() {
        println!("  [+] Invariante Falsable VERIFICADA: Corrupcion WORM detectada exitosamente.");
    } else {
        panic!("[-] FALLO DE DISENO: WORM acepto silenciosamente mutacion de estado.");
    }
}

fn main() {
    println!("BABYLON-60 Sovereign TEE / WORM Validator PoC (C5-REAL)");
    println!("=======================================================\n");

    let args: Vec<String> = std::env::args().collect();
    let mut iterations = 1000;
    
    let mut i = 1;
    while i < args.len() {
        if args[i] == "--stress-test" && i + 1 < args.len() {
            iterations = args[i + 1].parse().unwrap_or(1000);
        }
        i += 1;
    }

    run_stress_test(iterations);
    
    println!("\n[✔] PoC COMPLETO: Topologia causal del WORM demostrada.");
}
