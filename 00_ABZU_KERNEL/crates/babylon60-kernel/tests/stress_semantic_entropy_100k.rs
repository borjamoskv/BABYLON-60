use babylon60_kernel::semantic_entropy::{
    BitmaskSemanticKernel, SemanticEntropyVerdict, SolverOutcome, ERR_CONFABULATION,
    ERR_INCORRECT_BELIEF, TAU_SEM_Q16,
};
use std::sync::atomic::{AtomicUsize, Ordering};
use std::thread;
use std::time::Instant;

fn matrix_from_labels(labels: &[usize]) -> u64 {
    let mut matrix = 0u64;
    for (i, left) in labels.iter().enumerate() {
        for (j, right) in labels.iter().enumerate() {
            if left == right {
                matrix |= 1u64 << (i * 8 + j);
            }
        }
    }
    matrix
}

fn exact_shannon_bits(labels: &[usize]) -> f64 {
    let mut counts = [0usize; 8];
    for &label in labels {
        counts[label] += 1;
    }
    let n = labels.len() as f64;
    let mut h = 0.0f64;
    for c in counts.into_iter().filter(|&c| c > 0) {
        let p = (c as f64) / n;
        h -= p * p.log2();
    }
    h
}

fn enumerate_rgf_partitions(
    n: usize,
    idx: usize,
    max_used: usize,
    cur: &mut [usize],
    visit: &mut impl FnMut(&[usize]),
) {
    if idx == n {
        visit(&cur[..n]);
        return;
    }
    for label in 0..=max_used {
        cur[idx] = label;
        enumerate_rgf_partitions(n, idx + 1, max_used, cur, visit);
    }
    cur[idx] = max_used + 1;
    enumerate_rgf_partitions(n, idx + 1, max_used + 1, cur, visit);
}

#[test]
fn numerical_stability_and_refinement_monotonicity_across_all_5295_bell_partitions() {
    let mut total_partitions = 0usize;
    let mut max_abs_bits_err = 0.0f64;
    let mut min_threshold_margin_bits = f64::INFINITY;
    let mut refinement_checks = 0usize;
    let mut buf = [0usize; 8];

    for n in 1..=8 {
        buf[0] = 0;
        enumerate_rgf_partitions(n, 1, 0, &mut buf, &mut |labels| {
            total_partitions += 1;
            let matrix = matrix_from_labels(labels);
            let (h_q16, num_classes) = BitmaskSemanticKernel::compute_quotient_entropy(matrix, n)
                .expect("valid RGF partition must succeed");
            let h_q16_bits = (h_q16 as f64) / 65536.0;
            let h_exact = exact_shannon_bits(labels);
            let abs_err = (h_q16_bits - h_exact).abs();
            if abs_err > max_abs_bits_err {
                max_abs_bits_err = abs_err;
            }

            // Verify zero threshold-flip discrepancy at 0.85 bits (TAU_SEM_Q16 = 55706)
            let q16_above = h_q16 > TAU_SEM_Q16;
            let exact_above = h_exact > 0.85;
            assert_eq!(
                q16_above, exact_above,
                "Threshold flip at n={n}, labels={labels:?}: h_q16={h_q16} vs h_exact={h_exact}"
            );
            let margin = (h_exact - 0.85).abs();
            if margin < min_threshold_margin_bits {
                min_threshold_margin_bits = margin;
            }

            // Strict refinement monotonicity: merging any two distinct classes strictly lowers H_Q16
            let k = num_classes as usize;
            if k >= 2 {
                for c_a in 0..k {
                    for c_b in (c_a + 1)..k {
                        let mut coarse = [0usize; 8];
                        for (idx, &lbl) in labels.iter().enumerate() {
                            coarse[idx] = if lbl == c_b {
                                c_a
                            } else if lbl > c_b {
                                lbl - 1
                            } else {
                                lbl
                            };
                        }
                        let coarse_mat = matrix_from_labels(&coarse[..n]);
                        let (h_coarse_q16, coarse_k) =
                            BitmaskSemanticKernel::compute_quotient_entropy(coarse_mat, n)
                                .expect("coarsened partition must remain valid");
                        assert_eq!(coarse_k, num_classes - 1);
                        assert!(
                            h_q16 > h_coarse_q16,
                            "Monotonicity violated: fine={h_q16} <= coarse={h_coarse_q16} for {labels:?}"
                        );
                        refinement_checks += 1;
                    }
                }
            }
        });
    }

    assert_eq!(total_partitions, 5_295);
    assert!(
        max_abs_bits_err <= 4.0 / 65536.0,
        "Q16 quantization error exceeded 4 ULP bound: {max_abs_bits_err}"
    );
    assert!(
        min_threshold_margin_bits > max_abs_bits_err,
        "Threshold safety margin ({min_threshold_margin_bits}) smaller than max Q16 error ({max_abs_bits_err})"
    );
    assert!(refinement_checks > 20_000);
}

#[test]
fn stress_test_100k_semantic_entropy_ring0() {
    println!("\n================================================================================");
    println!(" PRUEBA SINTÉTICA: 100.000 EVALUACIONES SOBRE CUATRO CASOS REPETIDOS");
    println!("    Aritmética Q16 y resultados SAT/UNSAT suministrados por el test");
    println!("    Concurrencia: Multithreading Paralelo (4 Hilos de Ejecución Directa)");
    println!("================================================================================");

    const TOTAL_OPERATIONS: usize = 100_000;
    const NUM_THREADS: usize = 4;
    const OPS_PER_THREAD: usize = TOTAL_OPERATIONS / NUM_THREADS;

    // Contadores de variantes: no miden verdad factual ni contención de hardware.
    static CONFAB_APOPTOSIS_COUNT: AtomicUsize = AtomicUsize::new(0);
    static BELIEF_APOPTOSIS_COUNT: AtomicUsize = AtomicUsize::new(0);
    static GENUINE_VERIFIED_COUNT: AtomicUsize = AtomicUsize::new(0);
    static POLYSEMY_VERIFIED_COUNT: AtomicUsize = AtomicUsize::new(0);

    // Matrices de adyacencia pre-calculadas (N=5)
    // Q1: Clique completo (K=1, H_sem=0)
    let mut adj_genuine: u64 = 0;
    for i in 0..5 {
        adj_genuine |= (0b0001_1111u64) << (i * 8);
    }

    // Q2: Identidad (K=5, H_sem máxima)
    let mut adj_confab: u64 = 0;
    for i in 0..5 {
        adj_confab |= (1u64 << i) << (i * 8);
    }

    // Q3: Dispersión baja (K=1, H_sem=0), con UNSAT suministrado.
    let adj_incorrect_belief = adj_genuine;

    // Q4: Dos clases: {0,1,2} y {3,4}, con SAT suministrado.
    let mut adj_poly: u64 = 0;
    for i in 0..3 {
        adj_poly |= (0b0000_0111u64) << (i * 8);
    }
    for i in 3..5 {
        adj_poly |= (0b0001_1000u64) << (i * 8);
    }

    let global_start = Instant::now();

    thread::scope(|s| {
        for t_id in 0..NUM_THREADS {
            s.spawn(move || {
                let mut local_confab = 0usize;
                let mut local_belief = 0usize;
                let mut local_genuine = 0usize;
                let mut local_poly = 0usize;

                for i in 0..OPS_PER_THREAD {
                    let quadrant = (t_id + i) % 4;
                    match quadrant {
                        0 => {
                            // Cuadrante 1: dispersión baja y SAT.
                            let verdict =
                                BitmaskSemanticKernel::evaluate(adj_genuine, 5, SolverOutcome::Sat);
                            if let SemanticEntropyVerdict::VerifiedGenuine {
                                h_sem_q16,
                                num_classes,
                            } = verdict
                            {
                                assert_eq!(h_sem_q16, 0);
                                assert_eq!(num_classes, 1);
                                local_genuine += 1;
                            }
                        }
                        1 => {
                            // Cuadrante 2: dispersión alta y UNSAT.
                            let verdict = BitmaskSemanticKernel::evaluate(
                                adj_confab,
                                5,
                                SolverOutcome::Unsat,
                            );
                            if let SemanticEntropyVerdict::ApoptosisConfabulation {
                                h_sem_q16,
                                code,
                            } = verdict
                            {
                                assert_eq!(h_sem_q16, 152_170);
                                assert_eq!(code, ERR_CONFABULATION);
                                local_confab += 1;
                            }
                        }
                        2 => {
                            // Cuadrante 3: dispersión baja y UNSAT.
                            let verdict = BitmaskSemanticKernel::evaluate(
                                adj_incorrect_belief,
                                5,
                                SolverOutcome::Unsat,
                            );
                            if let SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                                h_sem_q16,
                                code,
                            } = verdict
                            {
                                assert_eq!(h_sem_q16, 0);
                                assert_eq!(code, ERR_INCORRECT_BELIEF);
                                local_belief += 1;
                            }
                        }
                        _ => {
                            // Cuadrante 4: dispersión alta y SAT.
                            let verdict =
                                BitmaskSemanticKernel::evaluate(adj_poly, 5, SolverOutcome::Sat);
                            if let SemanticEntropyVerdict::VerifiedPolysemy {
                                h_sem_q16,
                                num_classes,
                            } = verdict
                            {
                                assert_eq!(num_classes, 2);
                                assert_eq!(h_sem_q16, 63633);
                                local_poly += 1;
                            }
                        }
                    }
                }

                CONFAB_APOPTOSIS_COUNT.fetch_add(local_confab, Ordering::Relaxed);
                BELIEF_APOPTOSIS_COUNT.fetch_add(local_belief, Ordering::Relaxed);
                GENUINE_VERIFIED_COUNT.fetch_add(local_genuine, Ordering::Relaxed);
                POLYSEMY_VERIFIED_COUNT.fetch_add(local_poly, Ordering::Relaxed);
            });
        }
    });

    let total_elapsed = global_start.elapsed();
    let total_nanos = total_elapsed.as_nanos();
    let nanos_per_op = (total_nanos as f64) / (TOTAL_OPERATIONS as f64);
    let ops_per_sec = (TOTAL_OPERATIONS as f64) / total_elapsed.as_secs_f64();

    let confab_total = CONFAB_APOPTOSIS_COUNT.load(Ordering::SeqCst);
    let belief_total = BELIEF_APOPTOSIS_COUNT.load(Ordering::SeqCst);
    let genuine_total = GENUINE_VERIFIED_COUNT.load(Ordering::SeqCst);
    let poly_total = POLYSEMY_VERIFIED_COUNT.load(Ordering::SeqCst);

    println!("\n--- [TIEMPO DE LA EJECUCIÓN SINTÉTICA] ---");
    println!(
        "  ⏱️  Tiempo Total de Prueba    : {:.3} ms",
        total_elapsed.as_secs_f64() * 1000.0
    );
    println!(
        "  Tiempo total / operaciones  : {:.2} ns/op (amortizado entre hilos)",
        nanos_per_op
    );
    println!("  Este cociente no mide la latencia individual ni su máximo.");
    println!(
        "  🚀 Rendimiento Multihilo     : {:.2} millones de ops / segundo",
        ops_per_sec / 1_000_000.0
    );
    println!("  🧵 Hilos Paralelos           : {}", NUM_THREADS);

    println!("\n--- [CONTEO DE VARIANTES ESPERADAS EN DATOS SINTÉTICOS] ---");
    println!(
        "  • Q1 VerifiedGenuine             : {} / 25000 ({:.1}%)",
        genuine_total,
        genuine_total as f64 / 250.0
    );
    println!(
        "  • Q2 ApoptosisConfabulation       : {} / 25000 ({:.1}%)",
        confab_total,
        confab_total as f64 / 250.0
    );
    println!(
        "  • Q3 ApoptosisIncorrectBelief     : {} / 25000 ({:.1}%)",
        belief_total,
        belief_total as f64 / 250.0
    );
    println!(
        "  • Q4 VerifiedPolysemy             : {} / 25000 ({:.1}%)",
        poly_total,
        poly_total as f64 / 250.0
    );
    println!("  Los nombres históricos no validan hechos ni ejecutan efectos.");

    assert_eq!(genuine_total, 25_000, "Inconsistencia en Cuadrante 1");
    assert_eq!(
        confab_total, 25_000,
        "Inconsistencia en Cuadrante 2 (Apoptosis 0x6060)"
    );
    assert_eq!(
        belief_total, 25_000,
        "Inconsistencia en Cuadrante 3 (Apoptosis 0x6061)"
    );
    assert_eq!(poly_total, 25_000, "Inconsistencia en Cuadrante 4");

    println!("\nConteos esperados obtenidos en los cuatro casos repetidos.");
    println!("================================================================================\n");
}
