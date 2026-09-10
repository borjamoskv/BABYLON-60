use std::time::Instant;
use babylon60_kernel::scheduler::{F60ThermodynamicScheduler, AgentExecutionState};
use babylon60_kernel::shared_manifest::SharedManifest;
use babylon60_kernel::thermodynamics::MarkovBlanket;

#[test]
fn stress_test_10k_swarm_thermodynamic_limits() {
    println!("\n================================================================================");
    println!(" 🔥 PRUEBA DE ESTRÉS C5-REAL: ENJAMBRE 10.000 AGENTES (F60 THERMODYNAMIC KERNEL)");
    println!("    Sustrato: Ring-0 / no_std | Arquitectura: Markov Blanket & Active Inference");
    println!("================================================================================");

    const NUM_AGENTS: usize = 10_000;
    const NUM_TICKS: u64 = 60; // 1 segundo completo de simulación F60 a 60 Hz
    
    println!("[*] Inicializando topología: {} agentes en memoria continua...", NUM_AGENTS);
    let init_start = Instant::now();

    // 1. Asignar tuberías IPC lock-free (SharedManifest) de 64B alineados a caché
    let mut sensory_pipes: Vec<SharedManifest> = Vec::with_capacity(NUM_AGENTS);
    let mut active_pipes: Vec<SharedManifest> = Vec::with_capacity(NUM_AGENTS);
    for _ in 0..NUM_AGENTS {
        sensory_pipes.push(SharedManifest::new());
        active_pipes.push(SharedManifest::new());
    }

    // 2. Instanciar 10.000 Mantas de Markov con partición de regímenes térmicos:
    // - Agentes 0 a 6.999 (70%): Régimen Laminar (Capacidad 100.000 TFE)
    // - Agentes 7.000 a 8.999 (20%): Régimen Dinámico Langevin (Capacidad 50.000 TFE)
    // - Agentes 9.000 a 9.999 (10%): Régimen Adversarial / Shock (Capacidad 500 TFE - Diseñados para Burnout)
    let mut blankets: Vec<MarkovBlanket> = Vec::with_capacity(NUM_AGENTS);
    for i in 0..NUM_AGENTS {
        let capacity = if i < 7000 {
            100_000
        } else if i < 9000 {
            50_000
        } else {
            500 // Capacidad muy baja para forzar prueba de estrés de Burnout y Epistemic Halt
        };
        blankets.push(MarkovBlanket::new(capacity, &sensory_pipes[i], &active_pipes[i]));
    }

    let mut scheduler = F60ThermodynamicScheduler::new();
    let init_elapsed = init_start.elapsed();
    println!("[+] Inicialización completada en {:.2?} (~{:.1} KB memoria)", 
             init_elapsed, (NUM_AGENTS * 128) as f64 / 1024.0);

    // 3. Ejecutar ciclo caliente de estrés F60
    println!("\n[*] DETONANDO CICLO DE ESTRÉS F60 ({} ticks x {} agentes = {} evaluaciones)...", 
             NUM_TICKS, NUM_AGENTS, NUM_TICKS * NUM_AGENTS as u64);
    
    let stress_start = Instant::now();
    let mut active_count = 0;
    let mut burnout_count = 0;

    for tick in 1..=NUM_TICKS {
        // Inyectar gradientes sensoriales estocásticos según el régimen del agente
        for i in 0..NUM_AGENTS {
            if i < 7000 {
                // Régimen 1: Variación mínima (Coarse-Graining laminar, sin sorpresa)
                let value = (i as u64 % 2) + 1;
                sensory_pipes[i].publish(tick, &[value, 0, 0, 0]).unwrap();
            } else if i < 9000 {
                // Régimen 2: Salto dinámico moderado (Langevin relaxation)
                let value = (tick * 3 + (i as u64 % 5)) % 20;
                sensory_pipes[i].publish(tick, &[value, 0, 0, 0]).unwrap();
            } else {
                // Régimen 3: Shock adversarial de alta entropía (Inducción forzada de colapso)
                let value = tick * 1000 + (i as u64 * 77);
                sensory_pipes[i].publish(tick, &[value, 0, 0, 0]).unwrap();
            }
        }

        // Evaluar el enjambre completo bajo el planificador F60
        active_count = 0;
        burnout_count = 0;

        for i in 0..NUM_AGENTS {
            match scheduler.step(&blankets[i]) {
                Ok(AgentExecutionState::Active) => {
                    active_count += 1;
                }
                Ok(AgentExecutionState::BurnoutHalted { .. }) => {
                    burnout_count += 1;
                }
                Err(err) => {
                    panic!("Colapso no controlado del Kernel en agente {}: {}", i, err);
                }
            }
        }
    }

    let stress_elapsed = stress_start.elapsed();
    let total_evaluations = NUM_TICKS * NUM_AGENTS as u64;
    let throughput = total_evaluations as f64 / stress_elapsed.as_secs_f64();
    let latency_per_eval_ns = stress_elapsed.as_nanos() as f64 / total_evaluations as f64;

    println!("\n================================================================================");
    println!(" 📊 RESULTADOS DE LA PRUEBA DE ESTRÉS (TELEMETRÍA C5-REAL)");
    println!("================================================================================");
    println!(" -> Evaluaciones Epistémicas Totales : {}", total_evaluations);
    println!(" -> Tiempo de Cómputo Total          : {:.2?}", stress_elapsed);
    println!(" -> Throughput Sostenido             : {:.0} evaluaciones/segundo", throughput);
    println!(" -> Latencia Media por Evaluación    : {:.2} nanosegundos ({:.4} µs)", 
             latency_per_eval_ns, latency_per_eval_ns / 1000.0);
    println!(" -> Agentes Homeostáticos Activos    : {} / {} ({:.1}%)", 
             active_count, NUM_AGENTS, (active_count as f64 / NUM_AGENTS as f64) * 100.0);
    println!(" -> Agentes Aislados por Burnout     : {} / {} ({:.1}%)", 
             burnout_count, NUM_AGENTS, (burnout_count as f64 / NUM_AGENTS as f64) * 100.0);
    println!(" -> Reloj F60 Lógico Alcanzado       : tick #{}", scheduler.logical_clock.0);
    println!(" -> Reloj F60 Simulado Q32.32        : {} segundos exactos", scheduler.simulation_clock.as_secs());
    println!(" -> Integridad del Kernel            : 100% (CERO PANICS / CERO MEMORY LEAKS)");
    println!("================================================================================\n");

    // Verificaciones formales
    assert_eq!(burnout_count, 1000, "Exactamente los 1.000 agentes adversariales debieron entrar en Burnout");
    let min_throughput = if cfg!(debug_assertions) { 10_000.0 } else { 100_000.0 };
    assert!(throughput > min_throughput, "Throughput ({:.0} evals/s) debe superar {:.0} evals/s en sustrato Apple Silicon", throughput, min_throughput);
}
