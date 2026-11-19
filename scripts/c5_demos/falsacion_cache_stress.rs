use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

// 1. Estructura Entrópica (Sin aislamiento geométrico. Causa False Sharing)
struct EntropicState {
    counter0: AtomicUsize,
    counter1: AtomicUsize,
    counter2: AtomicUsize,
    counter3: AtomicUsize,
}

// 2. Estructura Topológicamente Aislada (El compilador fuerza alineación de Línea de Caché a 64 Bytes)
#[repr(align(64))]
struct PaddedCounter {
    counter: AtomicUsize,
}

struct TopologicalState {
    counter0: PaddedCounter,
    counter1: PaddedCounter,
    counter2: PaddedCounter,
    counter3: PaddedCounter,
}

fn main() {
    let iterations = 20_000_000;
    println!("[AX-3] TOPOLOGY: Falsación Termodinámica de Caché L1/L2 iniciada...");
    println!("Inyectando estrés concurrente (20M de mutaciones x 4 Hilos en SMP).");

    // -- Bucle de Estrés Entrópico --
    let state_entropic = Arc::new(EntropicState {
        counter0: AtomicUsize::new(0),
        counter1: AtomicUsize::new(0),
        counter2: AtomicUsize::new(0),
        counter3: AtomicUsize::new(0),
    });

    let start = Instant::now();
    let mut handles = vec![];
    for i in 0..4 {
        let state = Arc::clone(&state_entropic);
        handles.push(thread::spawn(move || {
            for _ in 0..iterations {
                match i {
                    0 => { state.counter0.fetch_add(1, Ordering::Relaxed); },
                    1 => { state.counter1.fetch_add(1, Ordering::Relaxed); },
                    2 => { state.counter2.fetch_add(1, Ordering::Relaxed); },
                    3 => { state.counter3.fetch_add(1, Ordering::Relaxed); },
                    _ => (),
                }
            }
        }));
    }
    for h in handles { h.join().expect("BFT Fallback"); }
    let duration_entropic = start.elapsed();
    println!("-> Disipación Entrópica (False Sharing): {:?}", duration_entropic);


    // -- Bucle de Estrés Topológico --
    let state_topo = Arc::new(TopologicalState {
        counter0: PaddedCounter { counter: AtomicUsize::new(0) },
        counter1: PaddedCounter { counter: AtomicUsize::new(0) },
        counter2: PaddedCounter { counter: AtomicUsize::new(0) },
        counter3: PaddedCounter { counter: AtomicUsize::new(0) },
    });

    let start = Instant::now();
    let mut handles = vec![];
    for i in 0..4 {
        let state = Arc::clone(&state_topo);
        handles.push(thread::spawn(move || {
            for _ in 0..iterations {
                match i {
                    0 => { state.counter0.counter.fetch_add(1, Ordering::Relaxed); },
                    1 => { state.counter1.counter.fetch_add(1, Ordering::Relaxed); },
                    2 => { state.counter2.counter.fetch_add(1, Ordering::Relaxed); },
                    3 => { state.counter3.counter.fetch_add(1, Ordering::Relaxed); },
                    _ => (),
                }
            }
        }));
    }
    for h in handles { h.join().expect("BFT Fallback"); }
    let duration_topo = start.elapsed();
    println!("-> Eficiencia Causal (Alineación Topológica 64B): {:?}", duration_topo);
    
    let ratio = duration_entropic.as_secs_f64() / duration_topo.as_secs_f64();
    println!("DICTAMEN EPISTÉMICO: El aislamiento geométrico redujo la fricción de caché un factor de {:.2}x.", ratio);
}
