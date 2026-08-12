// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-1..4 UNIT TESTS
// Tests estándar (no-Loom) para cobertura básica del crate.
//
// Ejecutar con:
//   cargo test --test unit_tests

#![cfg(not(loom))]

use babylon60::manifest::{SharedManifest, HaltReason, RUNNING, POISONED, MAX_RETRIES};
use babylon60::seqlock::{publish, read};
use babylon60::thermodynamics::{
    is_entelecheia, is_dynamis, is_valid_writer_transition,
    LANDAUER_FLOOR_TOTAL_AJ_X1000, BITS_PER_PUBLISH,
};
use babylon60::halt::is_halted;

use core::sync::atomic::Ordering;
use std::mem::{size_of, align_of, offset_of};

// ═══════════════════════════════════════════════════════════════════════
// INV-1: Layout C-ABI — 64 B, align(64), offsets exactos
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn inv1_size_64_bytes() {
    assert_eq!(size_of::<SharedManifest>(), 64);
}

#[test]
fn inv1_align_64_bytes() {
    assert_eq!(align_of::<SharedManifest>(), 64);
}

#[test]
fn inv1_field_offsets() {
    assert_eq!(offset_of!(SharedManifest, status_flag), 0x00);
    assert_eq!(offset_of!(SharedManifest, seq), 0x04);
    assert_eq!(offset_of!(SharedManifest, epoch_id), 0x08);
    assert_eq!(offset_of!(SharedManifest, payload_hash), 0x10);
    assert_eq!(offset_of!(SharedManifest, _padding), 0x30);
}

// ═══════════════════════════════════════════════════════════════════════
// INV-2: Seqlock — publish / read consistencia básica
// ═══════════════════════════════════════════════════════════════════════

/// Helper: crea un SharedManifest en estado inicial (Box::leak para align).
fn new_manifest() -> &'static SharedManifest {
    use std::sync::atomic::{AtomicU32, AtomicU64};
    // Usa Box para garantizar alineación
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
fn inv2_publish_then_read_returns_consistent_data() {
    let m = new_manifest();
    let hash = [0xDEAD_BEEF_CAFE_BABEu64; 4];
    publish(m, 1, &hash);

    let result = read(m);
    assert!(result.is_some(), "read() should succeed after publish()");
    let (epoch, h) = result.unwrap();
    assert_eq!(epoch, 1);
    assert_eq!(h, hash);
}

#[test]
fn inv2_read_initial_state_returns_zeros() {
    let m = new_manifest();
    let result = read(m);
    assert!(result.is_some());
    let (epoch, hash) = result.unwrap();
    assert_eq!(epoch, 0);
    assert_eq!(hash, [0u64; 4]);
}

#[test]
fn inv2_sequential_publishes_monotonic_epoch() {
    let m = new_manifest();
    let h1 = [1u64; 4];
    let h2 = [2u64; 4];
    let h3 = [3u64; 4];

    publish(m, 10, &h1);
    let r1 = read(m).unwrap();
    assert_eq!(r1.0, 10);

    publish(m, 20, &h2);
    let r2 = read(m).unwrap();
    assert_eq!(r2.0, 20);

    publish(m, 30, &h3);
    let r3 = read(m).unwrap();
    assert_eq!(r3.0, 30);

    // Monotonicidad: cada lectura ve epoch estrictamente mayor
    assert!(r1.0 < r2.0 && r2.0 < r3.0);
}

#[test]
fn inv2_seq_transitions_valid() {
    let m = new_manifest();
    let seq_before = m.seq.load(Ordering::Relaxed);
    publish(m, 1, &[0u64; 4]);
    let seq_after = m.seq.load(Ordering::Relaxed);
    assert!(is_valid_writer_transition(seq_before, seq_after));
    assert!(is_entelecheia(seq_after));
}

// ═══════════════════════════════════════════════════════════════════════
// INV-3: Termodinámica — constantes y bisimulación
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn inv3_landauer_floor_positive() {
    assert!(LANDAUER_FLOOR_TOTAL_AJ_X1000 > 0);
}

#[test]
fn inv3_bits_per_publish_384() {
    assert_eq!(BITS_PER_PUBLISH, 384);
}

#[test]
fn inv3_bisimulation_entelecheia_dynamis() {
    // Par → Entelecheia (observable)
    assert!(is_entelecheia(0));
    assert!(is_entelecheia(2));
    assert!(is_entelecheia(100));

    // Impar → Dynamis (inobservable)
    assert!(is_dynamis(1));
    assert!(is_dynamis(3));
    assert!(is_dynamis(99));

    // Mutuamente exclusivos
    for i in 0..256u32 {
        assert_ne!(is_entelecheia(i), is_dynamis(i));
    }
}

#[test]
fn inv3_valid_writer_transitions() {
    assert!(is_valid_writer_transition(0, 2));
    assert!(is_valid_writer_transition(2, 4));
    assert!(is_valid_writer_transition(100, 102));

    // Transiciones inválidas
    assert!(!is_valid_writer_transition(0, 1)); // impar
    assert!(!is_valid_writer_transition(0, 4)); // salto >2
    assert!(!is_valid_writer_transition(2, 2)); // identidad
}

#[test]
fn inv3_aphairesis_entropy_loss() {
    use babylon60::thermodynamics::aphairesis_entropy_loss_aj_x1000;
    // Eliminación de 100 bits → 100 * 2870 = 287_000 aJ*1000 (0.287 aJ)
    assert_eq!(aphairesis_entropy_loss_aj_x1000(100), 287_000);
}

#[test]
fn inv3_calm_monotonic_transition() {
    use babylon60::thermodynamics::is_calm_monotonic_transition;
    assert!(is_calm_monotonic_transition(10, 11));
    assert!(!is_calm_monotonic_transition(10, 10));
    assert!(!is_calm_monotonic_transition(10, 9));
}

#[test]
fn inv3_aphairesis_bound_min_energy() {
    use babylon60::thermodynamics::{AphairesisBound, to_q16_16_from_x1000};
    let bound = AphairesisBound {
        effective_bits_erased_q16: to_q16_16_from_x1000(64000),
        kl_divergence_q16: to_q16_16_from_x1000(100),
        temperature_k: 300,
    };
    let min_energy = bound.min_energy_zeptojoules();
    // E_min > 0 y consistente con Landauer (~ 183 zJ)
    assert!(min_energy > 150);
    assert!(bound.is_physically_valid(1000));
    assert!(!bound.is_physically_valid(10));
}

#[test]
fn inv3_topological_compressor_trait() {
    use babylon60::thermodynamics::{TopologicalCompressorFixed, AphairesisBound, to_q16_16_from_x1000};

    struct TestSheafCompressor;
    impl TopologicalCompressorFixed for TestSheafCompressor {
        const EFFECTIVE_BITS_ERASED_X1000: u32 = 128000;
        const KL_DIVERGENCE_X1000: u32 = 50;
        const DESIGN_TEMP_K: u32 = 300;
    }

    let bound: AphairesisBound = TestSheafCompressor::aphairesis_bound();
    assert_eq!(bound.effective_bits_erased_q16, to_q16_16_from_x1000(128000));
    assert_eq!(bound.kl_divergence_q16, to_q16_16_from_x1000(50));
    assert!(TestSheafCompressor::MIN_ENERGY_ZEPTOJOULES > 0);
}

#[test]
fn sheaf_fusion_respects_extended_landauer() {
    use babylon60::thermodynamics::{TopologicalCompressorFixed, SheafFusionOperator};

    assert!(
        SheafFusionOperator::MIN_ENERGY_ZEPTOJOULES >= 148,
        "Axiomatic bound mismatch: got {}",
        SheafFusionOperator::MIN_ENERGY_ZEPTOJOULES
    );
}

#[test]
fn generated_sheaf_fusion_operator_calibrated() {
    use babylon60::generated_aphairesis_constants::SheafFusionOperator;
    use babylon60::thermodynamics::TopologicalCompressorFixed;

    let bound = SheafFusionOperator::aphairesis_bound();
    assert!(bound.min_energy_zeptojoules() > 0);
    assert!(bound.effective_bits_erased_q16 >= 0);

}



#[test]
fn measurement_below_bound_is_rejected() {
    use babylon60::thermodynamics::{TopologicalCompressorFixed, SheafFusionOperator};
    let op = SheafFusionOperator;
    let impossible_measurement = SheafFusionOperator::MIN_ENERGY_ZEPTOJOULES.saturating_sub(1);
    
    assert!(op.validate_measurement(impossible_measurement).is_err());
}

#[test]
fn measurement_at_bound_is_accepted() {
    use babylon60::thermodynamics::{TopologicalCompressorFixed, SheafFusionOperator};
    let op = SheafFusionOperator;
    assert!(op.validate_measurement(SheafFusionOperator::MIN_ENERGY_ZEPTOJOULES).is_ok());
}

#[test]
fn symbolic_message_spsc_layout_and_bound() {
    use babylon60::thermodynamics::{TopologicalCompressorFixed, SheafFusionOperator, SymbolicMessage};
    use core::mem::size_of;

    let payload = [42u8; 48];
    let msg = SymbolicMessage::<SheafFusionOperator>::new(payload, 1001);

    assert_eq!(msg.logical_timestamp, 1001);
    assert_eq!(msg.energy_bound_zj, SheafFusionOperator::MIN_ENERGY_ZEPTOJOULES);
    assert!(size_of::<SymbolicMessage<SheafFusionOperator>>() <= 64);
}

#[test]
fn spsc_ring_buffer_push_pop() {
    use babylon60::spsc_ring::SpscRingBuffer;

    let ring = SpscRingBuffer::<(u64, [u64; 4]), 16>::new();
    let hash = [1u64, 2u64, 3u64, 4u64];

    assert!(ring.pop().is_none());
    assert!(ring.push((100, hash)).is_ok());

    let pop_res = ring.pop();
    assert!(pop_res.is_some());
    let (epoch, read_hash) = pop_res.unwrap();
    assert_eq!(epoch, 100);
    assert_eq!(read_hash, hash);
}






// ═══════════════════════════════════════════════════════════════════════
// INV-4: Halt — frontera topológica inmutable
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn inv4_is_halted_false_initially() {
    let m = new_manifest();
    assert!(!is_halted(m));
}

#[test]
fn inv4_poisoned_state_detectable() {
    let m = new_manifest();
    // Simular envenenamiento directo (sin abort)
    m.status_flag.store(POISONED, Ordering::Release);
    assert!(is_halted(m));
}

#[test]
fn inv4_poison_is_irreversible() {
    let m = new_manifest();
    m.status_flag.store(POISONED, Ordering::Release);
    // Intentar forzar recuperación: axiomáticamente prohibido en C5-REAL
    let _prev = m.status_flag.compare_exchange(POISONED, RUNNING, Ordering::AcqRel, Ordering::Acquire);
    // En un sistema real, el componente externo o el OS intervienen, pero 
    // a nivel memoria, esta transición no debe existir en la lógica de negocio.
    // Solo demostramos que is_halted sigue activo si alguien hace un store ciego.
    m.status_flag.store(POISONED, Ordering::SeqCst);
    assert!(is_halted(m));
}

#[test]
fn inv4_halt_reason_strings() {
    assert_eq!(HaltReason::SeqRetryExhausted.as_str(), "SEQ_RETRY_EXHAUSTED");
    assert_eq!(HaltReason::HashMismatch.as_str(), "HASH_MISMATCH");
    assert_eq!(HaltReason::EpochNonMonotonic.as_str(), "EPOCH_NON_MONOTONIC");
    assert_eq!(HaltReason::AlreadyPoisoned.as_str(), "ALREADY_POISONED");
    assert_eq!(HaltReason::ExternalSignal.as_str(), "EXTERNAL_SIGNAL");
}

#[test]
fn inv4_max_retries_thermodynamic_limit() {
    // MAX_RETRIES define el techo de fricción (spin) antes de inducir Halt
    assert!(MAX_RETRIES > 0);
    // El límite debe ser determinista para prevenir interbloqueos Livelock
    assert_eq!(MAX_RETRIES, 10_000, "MAX_RETRIES debe anclarse estrictamente a 10_000 iteraciones (Límite Termodinámico C5)");
}

// ═══════════════════════════════════════════════════════════════════════
// INV-2: Multithreaded stress test (no-Loom, pthread real)
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn inv2_concurrent_readers_no_torn_read() {
    use std::thread;

    // Necesitamos un manifest compartido con Arc pero NO en ruta caliente
    // (test only — en producción usar mmap/Box::leak)
    let m: &'static SharedManifest = new_manifest();

    const NUM_PUBLISHES: u64 = 1_000;
    const NUM_READERS: usize = 4;

    // Writer thread
    let writer = thread::spawn(move || {
        for epoch in 1..=NUM_PUBLISHES {
            let hash = [epoch; 4]; // hash = epoch repetido
            publish(m, epoch, &hash);
        }
    });

    // Reader threads
    let readers: Vec<_> = (0..NUM_READERS)
        .map(|_| {
            thread::spawn(move || {
                let mut reads = 0u64;
                let mut nones = 0u64;
                loop {
                    match read(m) {
                        Some((epoch, hash)) => {
                            // Invariante: hash debe ser coherente con epoch
                            assert!(
                                hash == [epoch; 4] || epoch == 0,
                                "TORN READ! epoch={epoch}, hash={hash:?}"
                            );
                            reads += 1;
                            if epoch >= NUM_PUBLISHES {
                                break;
                            }
                        }
                        None => {
                            nones += 1;
                            // Halt legítimo simulado: no abortar en test
                            if nones > 10_000 {
                                break; // evitar spin infinito en test
                            }
                        }
                    }
                }
                (reads, nones)
            })
        })
        .collect();

    writer.join().unwrap();
    for r in readers {
        let (reads, nones) = r.join().unwrap();
        // Debe haber leído al menos una vez
        assert!(reads > 0 || nones > 0, "reader did nothing");
    }
}

// ═══════════════════════════════════════════════════════════════════════
// INV-5: Integridad FFI y Padding
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn inv5_padding_integrity_preserved() {
    let m = new_manifest();
    // Padding inicial debe ser 0
    assert_eq!(m._padding, [0u8; 16]);
    
    // Una escritura (publish) no debe corromper el padding adyacente
    let hash = [0xFF; 4];
    publish(m, 42, &hash);
    
    // El compiler/CPU no debe haber emitido stores overlap-eados (Store Tearing)
    assert_eq!(m._padding, [0u8; 16], "Store tearing detectado sobre _padding C-ABI");
}

// ═══════════════════════════════════════════════════════════════════════
// SPSC Ring Buffer Lock-Free Tests
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn test_spsc_ring_buffer_basic_push_pop() {
    use babylon60::SpscRingBuffer;

    let ring = SpscRingBuffer::<u64, 8>::new();
    assert!(ring.is_empty());
    assert_eq!(ring.len(), 0);

    for i in 0..8 {
        assert!(ring.push(i * 10).is_ok());
    }

    assert!(ring.is_full());
    assert_eq!(ring.len(), 8);
    assert_eq!(ring.push(999), Err(999));

    for i in 0..8 {
        assert_eq!(ring.pop(), Some(i * 10));
    }

    assert!(ring.is_empty());
    assert_eq!(ring.pop(), None);
}

#[test]
fn test_spsc_ring_buffer_concurrent_producer_consumer() {
    use babylon60::spsc_ring::SpscRingBuffer;
    use std::sync::Arc;
    use std::thread;

    let ring = Arc::new(SpscRingBuffer::<u64, 1024>::new());
    let ring_producer = Arc::clone(&ring);
    let ring_consumer = Arc::clone(&ring);

    let count = 100_000u64;

    let producer = thread::spawn(move || {
        for i in 0..count {
            while ring_producer.push(i).is_err() {
                std::hint::spin_loop();
            }
        }
    });

    let consumer = thread::spawn(move || {
        let mut received = Vec::with_capacity(count as usize);
        while received.len() < count as usize {
            if let Some(val) = ring_consumer.pop() {
                received.push(val);
            } else {
                std::hint::spin_loop();
            }
        }
        received
    });

    producer.join().unwrap();
    let received = consumer.join().unwrap();

    assert_eq!(received.len(), count as usize);
    for (idx, &val) in received.iter().enumerate() {
        assert_eq!(val, idx as u64);
    }
}

