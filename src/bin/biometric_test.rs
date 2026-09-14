use babylon60::enclave::AppleSecureEnclave;
use babylon60::receipt::Signer;

fn main() {
    println!("===========================================================");
    println!("🛡️  C5-REAL: BARRERA CAUSAL BIOMÉTRICA (HITL) 🛡️");
    println!("===========================================================\n");
    
    // Invariante de Sandboxing: Esto fallará si se ejecuta dentro de VS Code
    println!("ADVERTENCIA: Si estás ejecutando esto desde la terminal integrada de VS Code,");
    println!("el TouchID fallará silenciosamente (Error de Sandboxing).");
    println!("Ejecuta este binario desde la aplicación Terminal.app o iTerm nativa.\n");

    let payload = b"FALSACION_TERMODINAMICA_C5";
    
    let enclave = AppleSecureEnclave::new();
    println!("> Solicitando atestación física del Secure Enclave...");
    
    match enclave.sign(payload) {
        Ok(sig) => {
            println!("  [+] Atestación exitosa.");
            println!("  [+] Firma P256 (Base64): {}", String::from_utf8_lossy(&sig));
            
            if enclave.verify(payload, &sig) {
                println!("  [+] Invariante de validación WORM: COMPROBADA.");
            } else {
                println!("  [-] FRACTURA EPISTÉMICA: Fallo en la verificación.");
            }
        }
        Err(e) => {
            println!("  [-] FALLO CAUSAL (Apoptosis de test). Rechazo Biométrico / Sandboxing: {}", e);
        }
    }
}
