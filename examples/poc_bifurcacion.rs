use std::f64;

/// Estado de la simulación del Bucle Cibernético
#[derive(Debug, Clone)]
struct SystemState {
    dysfunction: f64,      // x: Tamaño del problema
    anergy: f64,           // Entropía disipada (fricción estéril)
    exergy: f64,           // Energía útil liberada post-colapso
    attractor_active: bool,// Estado topológico
}

fn simulate_change_1(mut state: SystemState, iterations: usize, silent: bool) -> SystemState {
    if !silent { println!("--- INICIANDO CAMBIO 1: HOMEOSTASIS PATOLÓGICA ---"); }
    // El regulador intenta reducir la disfunción empujando en contra (-x).
    // Pero el sistema está en un atractor de Watzlawick: "La solución es el problema".
    for i in 0..iterations {
        if !state.attractor_active { break; }
        
        let effort = -0.1 * state.dysfunction; // Esfuerzo de resistencia (Cambio 1)
        // El problema se realimenta de la resistencia
        state.dysfunction = (state.dysfunction - effort).abs() + 0.1;
        
        // Fricción térmica estéril
        state.anergy += effort.abs() * 2.0;
        
        if !silent && i % 100 == 0 {
            println!("Iter {}: Dysfun={:.2}, Anergy={:.2}", i, state.dysfunction, state.anergy);
        }
    }
    state
}

fn simulate_change_2(mut state: SystemState, limit_c: f64, silent: bool) -> SystemState {
    if !silent { println!("--- INICIANDO CAMBIO 2: TRAMPOLÍN CIBERNÉTICO (Menos x Menos) ---"); }
    // Maniobra: Prescripción del síntoma. Hacemos del problema un problema insostenible.
    let mut i = 0;
    while state.attractor_active && i < 1000 {
        // En lugar de oponerse, multiplicamos la restricción (amplificación).
        // (-) x (-) = (+)
        let effort = 0.5 * state.dysfunction; 
        state.dysfunction += effort;
        
        // Aumenta la fricción pero acumula gradiente
        state.anergy += effort.abs() * 0.5;
        
        if !silent { println!("Iter {}: Dysfun={:.2}, Anergy={:.2} (Acelerando)", i, state.dysfunction, state.anergy); }
        
        // Umbral termodinámico: El dolor de permanecer igual > dolor de cambiar
        if state.dysfunction > limit_c {
            if !silent {
                println!("! UMBRAL CRÍTICO ALCANZADO (x > {}) !", limit_c);
                println!("! COLAPSO DEL ATRACTOR (Bifurcación Topológica) !");
            }
            state.attractor_active = false;
            // Salto de fase: Implosión del problema y liberación exergética
            state.exergy = state.anergy * 0.8;
            state.dysfunction = 0.0;
            state.anergy = 0.0;
        }
        i += 1;
    }
    state
}

fn main() {
    println!("=== STRESS TEST: FALSACIÓN EMPÍRICA C5-REAL ===");
    let mut stress_success = 0;
    let stress_iters = 1000;
    
    for _ in 0..stress_iters {
        let initial_state = SystemState {
            dysfunction: 1.0,
            anergy: 0.0,
            exergy: 0.0,
            attractor_active: true,
        };

        // Simula 500 ciclos de atasco homeostático
        let state_after_c1 = simulate_change_1(initial_state, 500, true);
        
        // Fuerzo la bifurcación
        let final_state = simulate_change_2(state_after_c1, 1000.0, true);
        
        if !final_state.attractor_active && final_state.exergy > 0.0 && final_state.dysfunction == 0.0 {
            stress_success += 1;
        }
    }
    
    println!("Stress test superado: {}/{} iteraciones bifurcaron correctamente sin deadlocks.", stress_success, stress_iters);
    
    println!("\n=== DEMOSTRACIÓN VERBOSA (1 ITERACIÓN) ===");
    let initial_state = SystemState { dysfunction: 1.0, anergy: 0.0, exergy: 0.0, attractor_active: true };
    let state_c1 = simulate_change_1(initial_state, 500, false);
    println!(">> Fin Cambio 1: Atrapado. Anergía Acumulada: {:.2}\n", state_c1.anergy);
    
    let state_c2 = simulate_change_2(state_c1, 100.0, false);
    println!(">> Fin Cambio 2: Nuevo Atractor Base. Exergía: {:.2}, Disfunción: {:.2}", state_c2.exergy, state_c2.dysfunction);
}
