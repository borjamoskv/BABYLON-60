use ark_bls12_381::{Bls12_381, Fr as BlsFr};
use ark_groth16::Groth16;
use ark_serialize::CanonicalSerialize;
use ark_snark::{CircuitSpecificSetupSNARK, SNARK};
use rand::SeedableRng;
use rand_chacha::ChaCha20Rng;
use std::ffi::CString;
use std::time::Instant;
use verifiable_inference_engine::verify_inference_payload;

include!(concat!(env!("OUT_DIR"), "/inference_circuit.rs"));

fn main() {
    println!("╔═══════════════════════════════════════════════════════════════════════╗");
    println!("║   C5-REAL / BABYLON-60: ZK VERIFIABLE INFERENCE EMPIRICAL STRESS TEST ║");
    println!("╚═══════════════════════════════════════════════════════════════════════╝\n");

    println!("[1/4] Inicializando Setup Causal Determinista (ChaCha20 seed: 0xC5...)...");
    let mut setup_rng = ChaCha20Rng::seed_from_u64(0xC5C5C5C5C5C5C5C5u64);
    let empty_circuit = InferenceConstraint::<BlsFr> {
        weight: None,
        nonce: None,
        expected_hash: None,
    };
    let (pk, _vk) = Groth16::<Bls12_381>::setup(empty_circuit, &mut setup_rng)
        .expect("Error al inicializar Trusted Setup para el Prover");
    println!("      ✓ Proving Key & Verifying Key generadas determinísticamente.\n");

    println!("[2/4] Sintetizando pruebas de referencia (Valid / Falsification)...");
    let weight = BlsFr::from(1337u64);
    let nonce_val = 42u64;
    let nonce_fr = BlsFr::from(nonce_val);
    let expected_hash_fr = weight * nonce_fr;

    let mut prov_rng = ChaCha20Rng::seed_from_u64(0x42424242u64);
    let valid_circuit = InferenceConstraint::<BlsFr> {
        weight: Some(weight),
        nonce: Some(nonce_fr),
        expected_hash: Some(expected_hash_fr),
    };

    let proof = Groth16::<Bls12_381>::prove(&pk, valid_circuit, &mut prov_rng)
        .expect("Error al computar prueba Groth16");

    let mut proof_bytes = Vec::new();
    proof.serialize_compressed(&mut proof_bytes).unwrap();
    let proof_hex = hex::encode(&proof_bytes);

    let mut hash_bytes = Vec::new();
    expected_hash_fr.serialize_compressed(&mut hash_bytes).unwrap();
    let hash_hex = hex::encode(&hash_bytes);

    // Valores adulterados para testing de falsación
    let mut fake_hash_bytes = Vec::new();
    (expected_hash_fr + BlsFr::from(1u64)).serialize_compressed(&mut fake_hash_bytes).unwrap();
    let fake_hash_hex = hex::encode(&fake_hash_bytes);
    let corrupt_proof_hex = format!("{}deadbeef", &proof_hex[..proof_hex.len() - 8]);
    let garbage_str = "not_a_valid_hex_string_xyz";

    let c_hash_valid = CString::new(hash_hex.clone()).unwrap();
    let c_proof_valid = CString::new(proof_hex.clone()).unwrap();
    let c_hash_fake = CString::new(fake_hash_hex).unwrap();
    let c_proof_corrupt = CString::new(corrupt_proof_hex).unwrap();
    let c_garbage = CString::new(garbage_str).unwrap();

    println!("      ✓ Test vectors compilados. Tamaño de prueba Groth16: {} bytes.", proof_bytes.len());
    println!("      ✓ Payload Hash: 0x{}...", &hash_hex[..16]);
    println!("      ✓ Nonce: {}\n", nonce_val);

    println!("[3/4] Ejecutando Stress Test Termodinámico (500 iteraciones FFI C-ABI)...");
    const ITERATIONS: usize = 500;
    let mut latencies_valid: Vec<u128> = Vec::with_capacity(ITERATIONS);

    let start_total = Instant::now();

    for i in 0..ITERATIONS {
        // A. Test Válido (Soundness Positiva)
        let t0 = Instant::now();
        let res_valid = verify_inference_payload(c_hash_valid.as_ptr(), nonce_val, c_proof_valid.as_ptr());
        let dt = t0.elapsed().as_micros();
        latencies_valid.push(dt);
        assert!(res_valid, "Iteración {}: La prueba legítima fue rechazada!", i);

        // B. Test Falsación 1: Nonce adulterado
        let res_bad_nonce = verify_inference_payload(c_hash_valid.as_ptr(), nonce_val + 1, c_proof_valid.as_ptr());
        assert!(!res_bad_nonce, "Iteración {}: Ataque de Nonce falsificado fue aceptado!", i);

        // C. Test Falsación 2: Payload Hash adulterado
        let res_bad_hash = verify_inference_payload(c_hash_fake.as_ptr(), nonce_val, c_proof_valid.as_ptr());
        assert!(!res_bad_hash, "Iteración {}: Ataque de Payload Hash modificado fue aceptado!", i);

        // D. Test Falsación 3: Prueba corrupta / truncada
        let res_corrupt = verify_inference_payload(c_hash_valid.as_ptr(), nonce_val, c_proof_corrupt.as_ptr());
        assert!(!res_corrupt, "Iteración {}: Prueba corrupta no causó fail-stop inmediato!", i);

        // E. Test Falsación 4: Basura no-hexadecimal
        let res_garbage = verify_inference_payload(c_hash_valid.as_ptr(), nonce_val, c_garbage.as_ptr());
        assert!(!res_garbage, "Iteración {}: String malformado no causó fail-stop seguro!", i);

        // F. Test Falsación 5: Punteros Nulos (Memory Safety)
        let res_null = verify_inference_payload(std::ptr::null(), nonce_val, c_proof_valid.as_ptr());
        assert!(!res_null, "Iteración {}: Null pointer no fue mitigado limpiamente!", i);
    }

    let total_elapsed = start_total.elapsed();
    latencies_valid.sort_unstable();

    let avg_us = latencies_valid.iter().sum::<u128>() as f64 / latencies_valid.len() as f64;
    let min_us = latencies_valid[0];
    let max_us = *latencies_valid.last().unwrap();
    let p50_us = latencies_valid[latencies_valid.len() / 2];
    let p95_us = latencies_valid[(latencies_valid.len() as f64 * 0.95) as usize];
    let p99_us = latencies_valid[(latencies_valid.len() as f64 * 0.99) as usize];

    let total_checks = ITERATIONS * 6; // 6 verificaciones por iteración = 3,000 llamadas C-ABI
    let throughput = total_checks as f64 / total_elapsed.as_secs_f64();

    println!("\n[4/4] ─── MÉTRICAS TERMODINÁMICAS Y RESULTADOS ───");
    println!("  Total llamadas FFI ejecutadas : {}", total_checks);
    println!("  Tiempo total transcurrido     : {:.3} s", total_elapsed.as_secs_f64());
    println!("  Throughput de verificación    : {:.2} ops/s", throughput);
    println!("  Latencia Media (Groth16)      : {:.2} µs ({:.2} ms)", avg_us, avg_us / 1000.0);
    println!("  Latencia Mínima               : {} µs", min_us);
    println!("  Latencia P50 (Mediana)        : {} µs", p50_us);
    println!("  Latencia P95                  : {} µs", p95_us);
    println!("  Latencia P99                  : {} µs", p99_us);
    println!("  Latencia Máxima (Jitter)      : {} µs", max_us);
    println!("  Fail-Stop & Null Safety       : 100% Mitigado (0 panics, 0 aborts)");
    println!("  Ratio de Falsación Soundness  : 100% Éxito (0 falsos positivos)");
    println!("═══════════════════════════════════════════════════════════════════════");
    println!("ESTADO EXÉRGICO: CERTIFICADO POR ESTRÉS EMPÍRICO (Zero-Trust Invariant)");
}
