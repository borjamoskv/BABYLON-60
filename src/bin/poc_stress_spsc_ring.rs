// ============================================================================
// BABYLON-60 v4.0 Sovereign Hardened
// █ AUTOCOGNITION-Ω | STATE: C5-REAL 
// ============================================================================
//! Proof of Concept & Runtime Stress Test: SPSC Ring Buffer Lock-Free
//! Certifies:
//! 1. Memory alignment (64 B cache line, 0 false sharing)
//! 2. Concurrent SPSC contention (1 Producer, 1 Consumer)
//! 3. Zero torn reads, strict monotonicity, zero data loss under stress.

use std::thread;
use std::time::Instant;

use babylon60::spsc_ring::SpscRingBuffer;

fn main() {
    println!("╔═══════════════════════════════════════════════════════════════════════════╗");
    println!("║       BABYLON-60 :: SPSC RING BUFFER STRESS TEST (C5-REAL)               ║");
    println!("╚═══════════════════════════════════════════════════════════════════════════╝\n");

    println!("[1/2] Verificando alineación e invariantes estructurales...");
    let ring: &'static SpscRingBuffer<u64, 1024> = Box::leak(Box::new(SpscRingBuffer::new()));
    let ptr = ring as *const SpscRingBuffer<u64, 1024> as usize;
    println!("  > Tamaño de estructura:      {} B", std::mem::size_of_val(ring));
    println!("  > Dirección en memoria:      0x{:016X}", ptr);
    println!("  > Offset dentro de caché:    {} B (Debe ser 0)", ptr % 64);
    assert_eq!(ptr % 64, 0, "INV-1 FAIL: Ptr no alineado a 64 bytes");
    println!("  [✓] INV-1 Certificado: Estructura alineada y false sharing mitigado.\n");

    println!("[2/2] Ejecutando test de estrés empírico concurrente (1 Productor, 1 Consumidor)...");
    
    let total_messages = 10_000_000u64;
    println!("  > Mensajes a transferir:     {}", total_messages);

    let t0 = Instant::now();

    let consumer_handle = thread::spawn(move || {
        let mut expected = 0u64;
        let mut errors = 0u64;
        let mut reads = 0u64;
        
        while expected < total_messages {
            if let Some(val) = ring.pop() {
                if val != expected {
                    errors += 1;
                }
                expected += 1;
                reads += 1;
            } else {
                std::hint::spin_loop();
            }
        }
        (reads, errors)
    });

    let producer_handle = thread::spawn(move || {
        let mut sent = 0u64;
        while sent < total_messages {
            match ring.push(sent) {
                Ok(_) => sent += 1,
                Err(_) => std::hint::spin_loop(), // Ring lleno
            }
        }
        sent
    });

    let sent = producer_handle.join().expect("Productor panicked");
    let (reads, errors) = consumer_handle.join().expect("Consumidor panicked");
    let elapsed = t0.elapsed();

    let mops = (total_messages as f64 / elapsed.as_secs_f64()) / 1_000_000.0;
    
    println!("  ── SPSC [1 Productor vs. 1 Consumidor] ──");
    println!("    > Tiempo Total:         {:?}", elapsed);
    println!("    > Mensajes Enviados:    {}", sent);
    println!("    > Mensajes Recibidos:   {}", reads);
    println!("    > Throughput Agregado:  {:.2} Mops/sec", mops);
    println!("    > Errores de Secuencia: {}", errors);

    assert_eq!(sent, total_messages, "Productor falló en enviar todo");
    assert_eq!(reads, total_messages, "Consumidor falló en leer todo");
    assert_eq!(errors, 0, "Se detectaron huecos o corrupciones en la secuencia");
    
    println!("\n  [✓] SPSC Certificado: Cero pérdidas de paquetes y cero bloqueos (Deadlocks) en {} operaciones.", total_messages);
}
