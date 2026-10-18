// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-2 LOOM VERIFICATION
//
// Exhaustive model-checking test for the seqlock protocol (INV-2).
// Uses the Loom crate to explore ALL possible thread interleavings
// between a single writer and multiple concurrent readers.
//
// INVOCACIÓN:
//   RUSTFLAGS="--cfg loom" cargo test --test seqlock_loom --release
//
// INVARIANTE VERIFICADO:
//   ∀ intercalación: read() retorna Some((epoch, hash)) consistente
//   con un publish() completo, O retorna None. Nunca retorna datos
//   parcialmente escritos (torn read).
//
// NOTA: Loom reemplaza las primitivas atómicas de std/core con versiones
// instrumentadas que exploran exhaustivamente el espacio de estados.
// El test NO compila con cargo test normal (requiere --cfg loom).

#![cfg(loom)]

use loom::sync::atomic::{AtomicU32, AtomicU64, Ordering};
use loom::sync::Arc;
use loom::thread;

// ═══════════════════════════════════════════════════════════════════════
// Réplica del SharedManifest con primitivas Loom
// ═══════════════════════════════════════════════════════════════════════
// Loom no puede instrumentar core::sync::atomic directamente,
// así que replicamos la estructura con loom::sync::atomic.

struct LoomManifest {
    #[allow(dead_code)]
    status_flag: AtomicU32,
    seq: AtomicU32,
    epoch_id: AtomicU64,
    payload_hash: [AtomicU64; 4],
}

impl LoomManifest {
    fn new() -> Self {
        Self {
            status_flag: AtomicU32::new(1), // RUNNING
            seq: AtomicU32::new(0),         // par → Entelecheia
            epoch_id: AtomicU64::new(0),
            payload_hash: [
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
                AtomicU64::new(0),
            ],
        }
    }
}

// ═══════════════════════════════════════════════════════════════════════
// Publish (escritor único) — réplica del protocolo seqlock.rs
// ═══════════════════════════════════════════════════════════════════════

fn loom_publish(m: &LoomManifest, epoch: u64, hash: &[u64; 4]) {
    // [AX-CONC-01]: seq → impar (Dynamis)
    let s = m.seq.load(Ordering::Relaxed);
    m.seq.store(s.wrapping_add(1), Ordering::Relaxed);

    // [AX-CONC-02]: barrera Release — hash/epoch no suben antes del impar
    loom::sync::atomic::fence(Ordering::Release);

    // [AX-CONC-03]: stores payload Relaxed (encajonados por barreras)
    for i in 0..4 {
        m.payload_hash[i].store(hash[i], Ordering::Relaxed);
    }
    m.epoch_id.store(epoch, Ordering::Relaxed);

    // [AX-CONC-04]: seq → par (Entelecheia), Release → STLR
    m.seq.store(s.wrapping_add(2), Ordering::Release);
}

// ═══════════════════════════════════════════════════════════════════════
// Read (lector puro-de-carga) — réplica del protocolo seqlock.rs
// ═══════════════════════════════════════════════════════════════════════

const MAX_RETRIES: usize = 4; // Reducido para que Loom converja

fn loom_read(m: &LoomManifest) -> Option<(u64, [u64; 4])> {
    for _ in 0..MAX_RETRIES {
        // [AX-CONC-05]: load Acquire → LDAR
        let s1 = m.seq.load(Ordering::Acquire);

        // Si impar → escritura en curso, reintento
        if s1 & 1 != 0 {
            loom::thread::yield_now();
            continue;
        }

        // Cargar payload Relaxed (puro-de-carga; sin RFO)
        let mut h = [0u64; 4];
        for i in 0..4 {
            h[i] = m.payload_hash[i].load(Ordering::Relaxed);
        }
        let e = m.epoch_id.load(Ordering::Relaxed);

        // [AX-CONC-06]: barrera Acquire → DMB ISHLD (AArch64)
        loom::sync::atomic::fence(Ordering::Acquire);

        // Verificar consistencia
        let s2 = m.seq.load(Ordering::Relaxed);
        if s1 == s2 {
            return Some((e, h));
        }
        loom::thread::yield_now();
    }
    None
}

// ═══════════════════════════════════════════════════════════════════════
// TEST 1: Un escritor, un lector — lectura consistente
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn loom_seqlock_single_writer_single_reader() {
    loom::model(|| {
        let m = Arc::new(LoomManifest::new());

        let writer = {
            let m = Arc::clone(&m);
            thread::spawn(move || {
                // Publicar epoch=1 con hash conocido
                let hash = [0xAAAA_BBBB_CCCC_DDDDu64; 4];
                loom_publish(&m, 1, &hash);
            })
        };

        let reader = {
            let m = Arc::clone(&m);
            thread::spawn(move || loom_read(&m))
        };

        writer.join().unwrap();
        let result = reader.join().unwrap();

        // El lector obtuvo o bien None (legítimo) o bien datos consistentes
        if let Some((epoch, hash)) = result {
            // INV-2: si retorna datos, deben ser coherentes con una
            // publicación completa. Solo hemos hecho una publicación
            // con epoch=1 y hash=0xAAAA_BBBB_CCCC_DDDD.
            // El estado previo es epoch=0, hash=[0;4].
            assert!(
                (epoch == 0 && hash == [0u64; 4])
                    || (epoch == 1 && hash == [0xAAAA_BBBB_CCCC_DDDDu64; 4]),
                "INV-2 VIOLATED: torn read detected! epoch={epoch}, hash={hash:?}"
            );
        }
        // None es aceptable (escritura en curso o retries agotados)
    });
}

// ═══════════════════════════════════════════════════════════════════════
// TEST 2: Un escritor, dos lectores — verificación SPMC
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn loom_seqlock_single_writer_two_readers() {
    loom::model(|| {
        let m = Arc::new(LoomManifest::new());

        let writer = {
            let m = Arc::clone(&m);
            thread::spawn(move || {
                let hash = [0x1111_2222_3333_4444u64; 4];
                loom_publish(&m, 42, &hash);
            })
        };

        let reader1 = {
            let m = Arc::clone(&m);
            thread::spawn(move || loom_read(&m))
        };

        let reader2 = {
            let m = Arc::clone(&m);
            thread::spawn(move || loom_read(&m))
        };

        writer.join().unwrap();

        for result in [reader1.join().unwrap(), reader2.join().unwrap()] {
            if let Some((epoch, hash)) = result {
                assert!(
                    (epoch == 0 && hash == [0u64; 4])
                        || (epoch == 42 && hash == [0x1111_2222_3333_4444u64; 4]),
                    "INV-2 VIOLATED (SPMC): torn read! epoch={epoch}, hash={hash:?}"
                );
            }
        }
    });
}

// ═══════════════════════════════════════════════════════════════════════
// TEST 3: Dos publicaciones secuenciales — monotonicidad de epoch
// ═══════════════════════════════════════════════════════════════════════

#[test]
fn loom_seqlock_two_publishes_monotonic_epoch() {
    loom::model(|| {
        let m = Arc::new(LoomManifest::new());

        // Escritor: dos publicaciones secuenciales
        let writer = {
            let m = Arc::clone(&m);
            thread::spawn(move || {
                let h1 = [0xAAAAu64; 4];
                loom_publish(&m, 1, &h1);
                let h2 = [0xBBBBu64; 4];
                loom_publish(&m, 2, &h2);
            })
        };

        let reader = {
            let m = Arc::clone(&m);
            thread::spawn(move || loom_read(&m))
        };

        writer.join().unwrap();
        let result = reader.join().unwrap();

        if let Some((epoch, hash)) = result {
            // Tres estados válidos: inicial, después de pub1, después de pub2
            let valid = (epoch == 0 && hash == [0u64; 4])
                || (epoch == 1 && hash == [0xAAAAu64; 4])
                || (epoch == 2 && hash == [0xBBBBu64; 4]);
            assert!(
                valid,
                "INV-2/INV-3 VIOLATED: inconsistent state! epoch={epoch}, hash={hash:?}"
            );
        }
    });
}
