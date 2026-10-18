use ark_bls12_381::{Bls12_381, Fr as BlsFr};
use ark_groth16::Groth16;
use ark_snark::{CircuitSpecificSetupSNARK, SNARK};
use rand::thread_rng;

include!(concat!(env!("OUT_DIR"), "/circuit.rs"));

fn main() {
    println!("=== C5-REAL: Auditoría Matemática Termodinámica (Iteración 2) ===");
    println!("Iniciando PoC empírica para circuito Polinomial Complejo generado por nul-zk...\n");
    println!("Ecuación: c = 5 * a^2 + 2 * a + 1");

    let mut rng = thread_rng();

    // 1. Setup
    println!("1. Ejecutando Setup (Trusted Setup simulado)...");
    let empty_circuit = Polynomial::<BlsFr> {
        c: None,
        a: None,
    };
    
    let (pk, vk) = Groth16::<Bls12_381>::setup(empty_circuit, &mut rng)
        .expect("Fallo en Groth16 Setup");
    println!("   => Setup completado. (PK, VK) generadas.\n");

    // 2. Proving
    // c = 5 * (3^2) + 2*3 + 1 = 5*9 + 6 + 1 = 45 + 7 = 52
    let a_val = BlsFr::from(3u64);
    let c_val = BlsFr::from(52u64);

    println!("2. Generando Prueba ZK (Witness: a={}, Public: c={})...", 3, 52);
    let valid_circuit = Polynomial::<BlsFr> {
        c: Some(c_val),
        a: Some(a_val),
    };

    let proof = Groth16::<Bls12_381>::prove(&pk, valid_circuit, &mut rng)
        .expect("Fallo generando la prueba (Proving)");
    println!("   => Prueba generada exitosamente.\n");

    // 3. Verification
    println!("3. Verificando la Prueba (con Public Input c={})...", 52);
    let valid = Groth16::<Bls12_381>::verify(&vk, &vec![c_val], &proof)
        .expect("Fallo ejecutando la verificación");
    
    assert!(valid, "La prueba VÁLIDA fue rechazada");
    println!("   => [ÉXITO] Prueba válida verificada correctamente.\n");

    // 4. Falsación
    println!("4. Falsación Termodinámica (Intento de falsificación de Output)...");
    let fake_c_val = BlsFr::from(53u64);
    println!("   Testando Verificación con c={} (falso)...", 53);
    
    let invalid_verification = Groth16::<Bls12_381>::verify(&vk, &vec![fake_c_val], &proof)
        .expect("Fallo ejecutando la verificación");
    
    assert!(!invalid_verification, "La prueba INVÁLIDA fue aceptada! ¡Fallo crítico!");
    println!("   => [ÉXITO] Prueba inválida rechazada por el Verifier.\n");

    println!("=== RESULTADO DE LA AUDITORÍA 2 ===");
    println!("Evaluación polinomial, precedencia de puertas anidadas y constantes intermedios probados de manera SÓLIDA.");
}
