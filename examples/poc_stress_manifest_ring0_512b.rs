// ============================================================================
// BABYLON-60 :: SHAREDMANIFEST RING-0 (512B) PRUEBA LOCAL ACOTADA
// Comprueba layout, snapshots aceptados y rechazo terminal por la API pública.
// Informa tiempos y rechazos con 1 productor y 8 lectores en este proceso.
// Las muestras no prueban ausencia general de carreras, progreso wait-free,
// tráfico RFO, false sharing ni comportamiento de una integración C-FFI real.
// ============================================================================

use std::hint::black_box;
use std::mem::{align_of, size_of};
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Instant;

use babylon60::manifest::{
    PayloadSlot, ReaderPinLine, SharedManifestRing0, WriterControlLine, POISON_BIT, POISON_SENTINEL,
};

fn make_state_hash(tick: u64) -> [u8; 32] {
    let mut h = [0u8; 32];
    let bytes = tick.to_le_bytes();
    for i in 0..8 {
        h[i] = bytes[i];
        h[i + 8] = !bytes[i];
        h[i + 16] = bytes[i] ^ 0x5A;
        h[i + 24] = bytes[i].wrapping_mul(37);
    }
    h
}

fn verify_state_hash(tick: u64, hash: &[u8; 32]) -> bool {
    let expected = make_state_hash(tick);
    hash == &expected
}

struct ReaderMetrics {
    total_reads: u64,
    rejected_reads: u64,
    monotonicity_violations: u64,
    hash_corruptions: u64,
}

fn main() {
    println!("╔═══════════════════════════════════════════════════════════════════════════╗");
    println!("║     BABYLON-60 :: SHAREDMANIFEST RING-0 512B PRUEBA LOCAL ACOTADA         ║");
    println!("╚═══════════════════════════════════════════════════════════════════════════╝\n");
    println!(
        "  > Plataforma: {} / {}",
        std::env::consts::OS,
        std::env::consts::ARCH
    );

    // ────────────────────────────────────────────────────────────────────────
    // 0. Layout y alineación del objeto en este proceso
    // ────────────────────────────────────────────────────────────────────────
    println!("[0/4] Verificando layout y alineación del objeto...");
    let manifest: &'static SharedManifestRing0 = Box::leak(Box::new(SharedManifestRing0::new()));
    let ptr = manifest as *const SharedManifestRing0 as usize;

    println!(
        "  > Tamaño SharedManifestRing0: {} B (4 × 128 B)",
        size_of::<SharedManifestRing0>()
    );
    println!(
        "  > Alineación requerida:       {} B",
        align_of::<SharedManifestRing0>()
    );
    println!("  > Dirección de memoria:       0x{:016X}", ptr);
    println!(
        "  > Resto de alineación:        {} B (Debe ser 0)",
        ptr % 128
    );
    println!(
        "  > Línea 0 (WriterControl):    {} B (align {})",
        size_of::<WriterControlLine>(),
        align_of::<WriterControlLine>()
    );
    println!(
        "  > Línea 1 (ReaderPin):        {} B (align {})",
        size_of::<ReaderPinLine>(),
        align_of::<ReaderPinLine>()
    );
    println!(
        "  > Línea 2/3 (PayloadSlots):   {} B (align {})",
        size_of::<PayloadSlot>(),
        align_of::<PayloadSlot>()
    );

    assert_eq!(
        size_of::<SharedManifestRing0>(),
        512,
        "FAIL: Tamaño != 512 B"
    );
    assert_eq!(
        align_of::<SharedManifestRing0>(),
        128,
        "FAIL: Alineación != 128 B"
    );
    assert_eq!(ptr % 128, 0, "FAIL: No alineado a 128 bytes");
    assert_eq!(size_of::<WriterControlLine>(), 128);
    assert_eq!(size_of::<ReaderPinLine>(), 128);
    assert_eq!(size_of::<PayloadSlot>(), 128);
    println!("  [✓] Layout observado: 512 B, alineación de 128 B.\n");

    // ────────────────────────────────────────────────────────────────────────
    // 1. Línea Base No Contendida (1,000,000 operaciones)
    // ────────────────────────────────────────────────────────────────────────
    println!("[1/4] Evaluando latencias baseline sin contención (1,000,000 iteraciones)...");
    let iters = 1_000_000u64;

    // Baseline Productor
    let mut slot = PayloadSlot::zeroed();
    let t0 = Instant::now();
    for tick in 1..=iters {
        slot.logical_tick = tick;
        slot.state_hash = make_state_hash(tick);
        slot.metrics[0] = tick.wrapping_mul(10);
        manifest
            .publish_and_audit(&slot, tick)
            .expect("Publicación baseline rechazada");
    }
    let write_elapsed = t0.elapsed();
    let write_ns_op = write_elapsed.as_nanos() as f64 / iters as f64;
    let write_mops = (iters as f64 / write_elapsed.as_secs_f64()) / 1_000_000.0;
    println!(
        "  > Productor Ring-0:   {:?} ({:.2} ns/op, {:.2} Mops/sec)",
        write_elapsed, write_ns_op, write_mops
    );

    // Baseline Consumidor
    let mut read_buf = PayloadSlot::zeroed();
    let t1 = Instant::now();
    for _ in 1..=iters {
        manifest
            .read_snapshot(&mut read_buf)
            .expect("Lectura baseline rechazada");
        black_box(&read_buf);
    }
    let read_elapsed = t1.elapsed();
    let read_ns_op = read_elapsed.as_nanos() as f64 / iters as f64;
    let read_mops = (iters as f64 / read_elapsed.as_secs_f64()) / 1_000_000.0;
    println!(
        "  > Lector Rust:        {:?} ({:.2} ns/op, {:.2} Mops/sec)",
        read_elapsed, read_ns_op, read_mops
    );
    println!("  [✓] Tiempos observados en esta ejecución; sin umbral de latencia.\n");

    // ────────────────────────────────────────────────────────────────────────
    // 2. Contención Concurrente SPMC (1 Productor + 8 Consumidores)
    // ────────────────────────────────────────────────────────────────────────
    let num_readers = 8;
    println!(
        "[2/4] Evaluando contención SPMC saturada (1 Productor vs {} Consumidores concurrentes)...",
        num_readers
    );
    let run_manifest = Arc::new(SharedManifestRing0::new());
    let stop_signal = Arc::new(AtomicBool::new(false));

    let mut reader_handles = Vec::new();
    for reader_id in 0..num_readers {
        let m = Arc::clone(&run_manifest);
        let stop = Arc::clone(&stop_signal);

        reader_handles.push(
            thread::Builder::new()
                .name(format!("reader-{}", reader_id))
                .spawn(move || {
                    let mut metrics = ReaderMetrics {
                        total_reads: 0,
                        rejected_reads: 0,
                        monotonicity_violations: 0,
                        hash_corruptions: 0,
                    };
                    let mut buf = PayloadSlot::zeroed();
                    let mut last_tick = 0u64;

                    while !stop.load(Ordering::Relaxed) {
                        if m.read_snapshot(&mut buf).is_ok() {
                            if buf.logical_tick == 0 {
                                // Slot inicial no inicializado antes del primer publish
                                continue;
                            }
                            metrics.total_reads += 1;
                            if buf.logical_tick < last_tick {
                                metrics.monotonicity_violations += 1;
                            }
                            if !verify_state_hash(buf.logical_tick, &buf.state_hash) {
                                metrics.hash_corruptions += 1;
                            }
                            last_tick = buf.logical_tick;
                        } else {
                            metrics.rejected_reads += 1;
                        }
                    }
                    metrics
                })
                .expect("Failed to spawn reader thread"),
        );
    }

    let prod_manifest = Arc::clone(&run_manifest);
    let prod_iters = 500_000u64;
    let prod_handle = thread::Builder::new()
        .name("producer-ring0".to_string())
        .spawn(move || {
            let mut s = PayloadSlot::zeroed();
            let t_start = Instant::now();
            for tick in 1..=prod_iters {
                s.logical_tick = tick;
                s.state_hash = make_state_hash(tick);
                s.metrics[0] = tick.wrapping_mul(7);
                prod_manifest
                    .publish_and_audit(&s, tick)
                    .expect("Publicación concurrente rechazada");
            }
            let el = t_start.elapsed();
            el
        })
        .expect("Failed to spawn producer thread");

    let prod_duration = prod_handle.join().expect("Producer panicked");
    stop_signal.store(true, Ordering::Release);

    let mut total_reads = 0u64;
    let mut rejected_reads = 0u64;
    let mut total_violations = 0u64;
    let mut total_corruptions = 0u64;

    for h in reader_handles {
        let m = h.join().expect("Reader panicked");
        total_reads += m.total_reads;
        rejected_reads += m.rejected_reads;
        total_violations += m.monotonicity_violations;
        total_corruptions += m.hash_corruptions;
    }

    let prod_mops = (prod_iters as f64 / prod_duration.as_secs_f64()) / 1_000_000.0;
    println!("  > Escrituras completadas:   {}", prod_iters);
    println!(
        "  > Tiempo total productor:   {:?} ({:.2} Mops/sec)",
        prod_duration, prod_mops
    );
    println!("  > Snapshots aceptados:       {}", total_reads);
    println!("  > Lecturas rechazadas:       {}", rejected_reads);
    println!("  > Violaciones monotonicidad: {}", total_violations);
    println!("  > Corrupciones de payload:   {}", total_corruptions);

    assert!(
        total_reads > 0,
        "FAIL: No se observaron snapshots publicados"
    );
    assert_eq!(
        total_violations, 0,
        "FAIL: Violación de monotonicidad detectada"
    );
    assert_eq!(
        total_corruptions, 0,
        "FAIL: Lectura rasgada o corrupción de payload"
    );
    println!(
        "  [✓] Snapshots aceptados sin retrocesos de tick ni hashes incorrectos en esta muestra.\n"
    );

    // ────────────────────────────────────────────────────────────────────────
    // 3. Watchdog con pin lógico retenido en este proceso
    // ────────────────────────────────────────────────────────────────────────
    println!("[3/4] Evaluando watchdog con un pin lógico retenido...");
    let poison_manifest = SharedManifestRing0::new();
    let mut p_slot = PayloadSlot::zeroed();

    // 1. Consumidor FFI fija su pin en tick 100
    poison_manifest.ffi_pin(100);

    // 2. Productor avanza dentro de tolerancia (delta = 50 <= 64)
    p_slot.logical_tick = 150;
    assert!(poison_manifest.publish_and_audit(&p_slot, 150).is_ok());
    println!("  > Productor tick 150 (delta = 50 <= 64): Publicación OK");

    // 3. Productor avanza más allá de MAX_FFI_HOLD_TICKS (delta = 70 > 64)
    p_slot.logical_tick = 170;
    let res = poison_manifest.publish_and_audit(&p_slot, 170);
    assert_eq!(
        res,
        Err(POISON_SENTINEL),
        "FAIL: Productor no disparó apoptosis asimétrica"
    );
    let ctl = poison_manifest
        .check_or_trigger_apoptosis(170)
        .expect_err("FAIL: El watchdog no conserva el rechazo terminal");
    assert_eq!(ctl, POISON_SENTINEL);
    assert_ne!(ctl & POISON_BIT, 0, "FAIL: POISON_BIT no está activo");
    println!("  > Productor tick 170 (delta = 70 > 64): Apoptosis disparada (POISON_SENTINEL = 0x{:016X})", POISON_SENTINEL);

    // 4. Lectura y publicación posteriores deben rechazar el estado terminal
    let mut check_buf = PayloadSlot::zeroed();
    assert_eq!(
        poison_manifest.read_snapshot(&mut check_buf),
        Err(POISON_SENTINEL)
    );
    assert_eq!(
        poison_manifest.publish_and_audit(&p_slot, 180),
        Err(POISON_SENTINEL)
    );
    println!("  [✓] Watchdog, lectura y publicación devolvieron el mismo rechazo terminal.\n");

    println!("╔═══════════════════════════════════════════════════════════════════════════╗");
    println!("║           COMPROBACIONES LOCALES COMPLETADAS EN ESTA EJECUCIÓN            ║");
    println!("╚═══════════════════════════════════════════════════════════════════════════╝");
}
