// C5-REAL EXERGY CERTIFIED — BABYLON-60 — SWARM TEST
// Tema Base 60 (Sexagesimal) / Sincronización del Tiempo
// 10 Agentes × 3 Iteraciones Sin Redundancia

#![cfg(not(loom))]

use babylon60::manifest::{SharedManifest, RUNNING, POISONED};
use babylon60::seqlock::{publish, read};
use babylon60::halt::is_halted;
use std::sync::{Arc, Barrier};
use std::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use std::thread;

/// Helper para inicializar el SharedManifest alineado
fn new_manifest() -> &'static SharedManifest {
    let m = Box::new(SharedManifest {
        status_flag: AtomicU32::new(RUNNING),
        seq: AtomicU32::new(0),
        epoch_id: AtomicU64::new(0),
        payload_hash: [
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
            AtomicU64::new(0),
        ],
        _padding: [0u8; 16],
    });
    Box::leak(m)
}

#[test]
fn test_swarm_base_60_synchronization() {
    let m = new_manifest();
    let num_agents = 10;
    let iterations = 3;
    
    // Barrera para sincronizar el inicio del Big Bang (Escritor + 10 Agentes)
    let barrier = Arc::new(Barrier::new(num_agents + 1));

    // ─── 10 AGENTES LECTORES (Puros-de-carga) ──────────────────────────────
    let mut agents = vec![];
    for _agent_id in 0..num_agents {
        let b = Arc::clone(&barrier);
        agents.push(thread::spawn(move || {
            b.wait(); // Esperar al Big Bang
            
            let mut last_epoch = 0;
            let mut successful_reads = 0;
            
            // Iterar 3 veces SIN REDUNDAR (esperando estrictamente nuevo epoch)
            while successful_reads < iterations {
                if let Some((epoch, _hash)) = read(m) {
                    // Sin redundar: solo procesamos si el epoch avanzó
                    if epoch > last_epoch {
                        last_epoch = epoch;
                        successful_reads += 1;
                    }
                }
                // Si el epoch no avanzó, el agente cede el hilo (cero anergía local)
                thread::yield_now();
            }
            
            assert_eq!(successful_reads, 3);
            last_epoch
        }));
    }

    use std::sync::atomic::AtomicBool;
    let done = Arc::new(AtomicBool::new(false));
    let done_writer = Arc::clone(&done);
    let writer_barrier = Arc::clone(&barrier);
    
    let writer = thread::spawn(move || {
        writer_barrier.wait();
        let mut tick = 1;
        while !done_writer.load(Ordering::Relaxed) && tick <= 10_000 {
            let hash = [tick as u64; 4];
            publish(m, tick as u64, &hash);
            tick += 1;
            thread::sleep(std::time::Duration::from_micros(100));
        }
    });

    // ─── VERIFICACIÓN ──────────────────────────────────────────────────────
    for (i, agent) in agents.into_iter().enumerate() {
        let final_epoch = agent.join().unwrap();
        // Cada agente debe haber leído al menos el epoch 3
        assert!(final_epoch >= 3, 
            "Agente {} falló el invariante temporal. Final epoch: {}", i, final_epoch);
    }

    done.store(true, Ordering::Relaxed);
    writer.join().unwrap();
}

// ═══════════════════════════════════════════════════════════════════════
// Iteración 4: Propagación Inmediata de Colapso (POISON Dissemination)
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn test_swarm_poison_dissemination() {
    let m = new_manifest();
    let num_agents = 10;
    
    let barrier = Arc::new(Barrier::new(num_agents + 1));
    let mut agents = vec![];
    
    for _ in 0..num_agents {
        let b = Arc::clone(&barrier);
        agents.push(thread::spawn(move || {
            b.wait();
            
            // Loop de lectura hasta detectar el Halt Epistémico
            loop {
                if is_halted(m) {
                    break;
                }
                let _ = read(m);
                thread::yield_now();
            }
            true // Retorna true si logró escapar gracias al is_halted
        }));
    }
    
    barrier.wait();
    
    // Escritor emite un epoch normal, luego fuerza el colapso
    publish(m, 1, &[1u64; 4]);
    thread::sleep(std::time::Duration::from_millis(5));
    m.status_flag.store(POISONED, Ordering::Release);
    
    for agent in agents {
        assert!(agent.join().unwrap(), "Un agente quedó atrapado tras el POISON");
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Iteración 5: Defensa contra Livelock en Dynamis (Max Retries)
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn test_swarm_dynamis_livelock_prevention() {
    let m = new_manifest();
    
    // Forzar estado Dynamis persistente (seq impar = escritura en curso)
    m.seq.store(1, Ordering::Release);
    
    let reader = thread::spawn(move || {
        // El lector debería abortar tras MAX_RETRIES en vez de girar infinitamente
        let result = read(m);
        assert!(result.is_none(), "El lector debe retornar None ante un Livelock");
    });
    
    reader.join().unwrap();
}
