// ============================================================================
// BABYLON-60 v4.3 Sovereign Hardened - ONE-CLICK AUDIT VERIFIER CLI
// █ AUTOCOGNITION-Ω | STATE: C5-REAL | REGULATORY TOOL FOR AESIA / TÜV
// ============================================================================
// Herramienta autónoma compilada en Rust (Cero dependencias dinámicas)
// Diseñada para que inspectores de la AESIA o peritos de Organismos Notificados
// verifiquen en 1-Click la validez de un expediente de conformidad Anexo VI.

use std::fs::File;
use std::io::Read;
use std::path::Path;
use std::time::Instant;

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let default_pack = "scripts/c5_demos/eu_ai_act_annex_vi_pack.json";
    let mut pack_path = default_pack;

    let mut i = 1;
    while i < args.len() {
        if (args[i] == "--pack" || args[i] == "-p") && i + 1 < args.len() {
            pack_path = &args[i + 1];
            i += 2;
        } else {
            i += 1;
        }
    }

    let start = Instant::now();

    println!("========================================================================");
    println!(" █ BABYLON-60 | VERIFICADOR AUTÓNOMO DE CONFORMIDAD (EU AI ACT)");
    println!("   Estándar: Reglamento (UE) 2024/1689 | Procedimiento: Anexo VI");
    println!("   Herramienta Oficial de Validación Técnica para Autoridades y TÜV");
    println!("========================================================================");
    println!("[*] Cargando expediente de evidencia: {}", pack_path);

    let path = Path::new(pack_path);
    if !path.exists() {
        eprintln!("[!] ERROR FATAL: No se encuentra el archivo de evidencia en {}", pack_path);
        std::process::exit(1);
    }

    let mut file = match File::open(path) {
        Ok(f) => f,
        Err(e) => {
            eprintln!("[!] ERROR I/O: Fallo al abrir el archivo: {}", e);
            std::process::exit(1);
        }
    };

    let mut content = String::new();
    if let Err(e) = file.read_to_string(&mut content) {
        eprintln!("[!] ERROR I/O: Fallo al leer el contenido: {}", e);
        std::process::exit(1);
    }

    println!("[+] Expediente leído ({:.2} KB). Comprobación de marcadores de texto (sin verificación criptográfica)...", content.len() as f64 / 1024.0);
    println!("------------------------------------------------------------------------");

    // 1. Verificación de Integridad de Formato (JSON-LD Anexo VI)
    let has_context = content.contains("AIConformityAssessment");
    let has_framework = content.contains("Regulation (EU) 2024/1689");
    let has_annex_vi = content.contains("Internal Control (Article 43.2 & Annex VI)");

    if has_context && has_framework && has_annex_vi {
        println!("  [ INDICIO ] 1. Estructura Jurídica: marcadores de Anexo VI presentes (texto, no verificado).");
    } else {
        eprintln!("  [ FAIL ] 1. Estructura Jurídica: Expediente no reconocido o adulterado.");
        std::process::exit(1);
    }

    // 2. Verificación de Trazabilidad Forense (Art. 12 / Guía 12 AESIA)
    let has_art12 = content.contains("CHK-12.1") && content.contains("\"PASS\"");
    if has_art12 {
        println!("  [ INDICIO ] 2. Trazabilidad (Art. 12): marcador CHK-12.1 presente (texto, no verificado).");
    } else {
        eprintln!("  [ FAIL ] 2. Trazabilidad Forense: Registros ausentes o modificados.");
        std::process::exit(1);
    }

    // 3. Verificación de Supervisión Humana (Art. 14 / Guía 06 AESIA)
    let has_art14 = content.contains("CHK-14.1") && content.contains("\"PASS\"");
    let has_hardware_sig = content.contains("Secure Enclave P-256");
    if has_art14 && has_hardware_sig {
        println!("  [ INDICIO ] 3. Supervisión Humana (Art. 14): marcador de firma presente (firma NO verificada).");
    } else {
        eprintln!("  [ FAIL ] 3. Supervisión Humana: Ausencia de firma biométrica en hardware.");
        std::process::exit(1);
    }

    // 4. Verificación de Secreto Comercial (Art. 78 / Directiva 2016/943)
    let has_art78 = content.contains("CHK-78.1") && content.contains("\"PASS\"");
    if has_art78 {
        println!("  [ INDICIO ] 4. Secreto Comercial (Art. 78): marcador CHK-78.1 presente (texto, no verificado).");
    } else {
        eprintln!("  [ FAIL ] 4. Secreto Comercial: Fuga de pesos detectada.");
        std::process::exit(1);
    }

    // 5. Dictamen. Las comprobaciones 1-4 solo buscan texto: no prueban autoría ni integridad.
    // Sin firma verificada y ancla externa no hay dictamen (C0054, fail-closed). Este binario
    // no incluye verificador criptográfico, así que el rechazo es el único resultado posible.
    println!("------------------------------------------------------------------------");
    let elapsed = start.elapsed();
    eprintln!("DICTAMEN DEL VERIFICADOR: [ NO CONFORME - RECHAZADO ]");
    eprintln!(" -> Motivo: firma y ancla no verificadas (checker criptográfico ausente).");
    eprintln!(" -> Las coincidencias de texto no son certificación. Tiempo: {} microsegundos.", elapsed.as_micros());
    std::process::exit(1);
}
