// C5-REAL EXERGY CERTIFIED — BABYLON-60 — INV-2 LOOM VERIFICATION
//
// Model checking for the seqlock protocol (INV-2), within configured Loom bounds.
// The atomic replica below follows shared_manifest_core.rs; this is not execution
// of the production atomics or a measurement of physical hardware.
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

#[cfg(loom)]
use loom::sync::atomic::{AtomicU32, AtomicU64, Ordering};
#[cfg(loom)]
use loom::sync::Arc;
#[cfg(loom)]
use loom::thread;

// ═══════════════════════════════════════════════════════════════════════
// Réplica del SharedManifest con primitivas Loom
// ═══════════════════════════════════════════════════════════════════════
// Loom no puede instrumentar core::sync::atomic directamente,
// así que replicamos la estructura con loom::sync::atomic.

#[cfg(loom)]
struct LoomManifest {
    status_flag: AtomicU32,
    seq: AtomicU32,
    epoch_id: AtomicU64,
    payload_hash: [AtomicU64; 4],
}

#[cfg(loom)]
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
// Publish — réplica CAS del protocolo canónico shared_manifest_core.rs.
// Este modelo acota reintentos; no certifica mediciones del hardware.
// ═══════════════════════════════════════════════════════════════════════

#[cfg(loom)]
fn loom_publish(m: &LoomManifest, epoch: u64, hash: &[u64; 4]) -> bool {
    if m.status_flag.load(Ordering::Acquire) == 0xDEAD_6060 {
        return false;
    }
    let s = m.seq.load(Ordering::Acquire);
    if s & 1 != 0
        || m.seq
            .compare_exchange(s, s.wrapping_add(1), Ordering::Acquire, Ordering::Relaxed)
            .is_err()
    {
        return false;
    }

    // [AX-CONC-02]: barrera Release — hash/epoch no suben antes del impar
    loom::sync::atomic::fence(Ordering::Release);

    if m.status_flag.load(Ordering::Acquire) == 0xDEAD_6060 {
        m.seq.store(s.wrapping_add(2), Ordering::Release);
        return false;
    }

    // [AX-CONC-03]: stores payload Relaxed (encajonados por barreras)
    m.epoch_id.store(epoch, Ordering::Relaxed);
    for i in 0..4 {
        m.payload_hash[i].store(hash[i], Ordering::Relaxed);
    }

    // [AX-CONC-04]: seq → par (Entelecheia), Release → STLR
    m.seq.store(s.wrapping_add(2), Ordering::Release);
    true
}

#[cfg(loom)]
fn loom_freeze(m: &LoomManifest) -> Option<u64> {
    m.status_flag.store(0xDEAD_6060, Ordering::SeqCst);
    for _ in 0..MAX_RETRIES {
        let s = m.seq.load(Ordering::Acquire);
        if s & 1 == 0
            && m.seq
                .compare_exchange(s, s.wrapping_add(1), Ordering::AcqRel, Ordering::Relaxed)
                .is_ok()
        {
            return Some(m.epoch_id.load(Ordering::Acquire));
        }
        thread::yield_now();
    }
    None
}

// ═══════════════════════════════════════════════════════════════════════
// Read (lector puro-de-carga) — réplica de shared_manifest_core.rs
// ═══════════════════════════════════════════════════════════════════════

#[cfg(loom)]
const MAX_RETRIES: usize = 4; // Reducido para que Loom converja

#[cfg(loom)]
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
        let e = m.epoch_id.load(Ordering::Relaxed);
        let mut h = [0u64; 4];
        for i in 0..4 {
            h[i] = m.payload_hash[i].load(Ordering::Relaxed);
        }

        // [AX-CONC-06]: barrera Acquire → DMB ISHLD (AArch64)
        loom::sync::atomic::fence(Ordering::Acquire);

        // Verificar consistencia
        let s2 = m.seq.load(Ordering::Acquire);
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

#[cfg(loom)]
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

#[cfg(loom)]
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

#[cfg(loom)]
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

#[cfg(loom)]
#[test]
fn loom_seqlock_concurrent_writers_preserve_payload() {
    loom::model(|| {
        let m = Arc::new(LoomManifest::new());
        let first = Arc::clone(&m);
        let writer = thread::spawn(move || loom_publish(&first, 1, &[1; 4]));
        loom_publish(&m, 2, &[2; 4]);
        writer.join().unwrap();
        let (epoch, hash) = loom_read(&m).expect("both writers finished");
        assert_eq!(hash, [epoch; 4]);
    });
}

#[cfg(loom)]
#[test]
fn loom_seqlock_freeze_cannot_steal_writer_ownership() {
    loom::model(|| {
        let m = Arc::new(LoomManifest::new());
        let first = Arc::clone(&m);
        let writer = thread::spawn(move || loom_publish(&first, 1, &[1; 4]));
        let frozen = loom_freeze(&m);
        writer.join().unwrap();
        let epoch = frozen
            .or_else(|| loom_freeze(&m))
            .expect("writer has finished");
        assert_eq!(m.epoch_id.load(Ordering::Acquire), epoch);
        for word in &m.payload_hash {
            assert_eq!(word.load(Ordering::Relaxed), epoch);
        }
        assert!(!loom_publish(&m, 2, &[2; 4]));
        assert_eq!(m.epoch_id.load(Ordering::Acquire), epoch);
    });
}

#[test]
fn production_shared_manifest_core_preserves_loom_verified_orderings() {
    let source = include_str!("../src/shared_manifest_core.rs");
    let normalized: String = source
        .lines()
        .map(|line| line.split("//").next().unwrap_or(""))
        .collect::<Vec<_>>()
        .join("")
        .chars()
        .filter(|ch| !ch.is_whitespace())
        .collect();

    let expected_publish = concat!(
        "pubfnpublish(&self,epoch:u64,hash:&[u64;4])->Result<(),&'staticstr>{",
        "ifself.status_flag.load(Ordering::Acquire)==POISONED{returnErr(\"POISONED_STATE\");}",
        "letseq=self.seq.load(Ordering::Acquire);",
        "ifseq&1!=0||self.seq.compare_exchange(seq,seq.wrapping_add(1),Ordering::Acquire,Ordering::Relaxed,).is_err(){returnErr(\"WRITER_BUSY\");}",
        "fence(Ordering::Release);",
        "ifself.status_flag.load(Ordering::Acquire)==POISONED{self.seq.store(seq.wrapping_add(2),Ordering::Release);returnErr(\"POISONED_STATE\");}",
        "self.epoch_id.store(epoch,Ordering::Relaxed);",
        "for(slot,value)inself.payload_hash.iter().zip(hash){slot.store(*value,Ordering::Relaxed);}",
        "self.seq.store(seq.wrapping_add(2),Ordering::Release);Ok(())}"
    );
    assert!(
        normalized.contains(expected_publish),
        "SharedManifest::publish drifted from Loom-verified memory ordering contract"
    );

    let expected_read_snapshot = concat!(
        "pubfnread_snapshot(&self)->Option<(u64,[u64;4])>{",
        "for_in0..MAX_RETRIES{",
        "letfirst=self.seq.load(Ordering::Acquire);",
        "iffirst&1!=0{core::hint::spin_loop();continue;}",
        "letepoch=self.epoch_id.load(Ordering::Relaxed);",
        "lethash=core::array::from_fn(|i|self.payload_hash[i].load(Ordering::Relaxed));",
        "fence(Ordering::Acquire);",
        "iffirst==self.seq.load(Ordering::Acquire){returnSome((epoch,hash));}",
        "core::hint::spin_loop();}None}"
    );
    assert!(
        normalized.contains(expected_read_snapshot),
        "SharedManifest::read_snapshot drifted from Loom-verified memory ordering contract"
    );

    let expected_freeze = concat!(
        "pubfnfreeze(&self)->Result<u64,&'staticstr>{",
        "self.status_flag.store(POISONED,Ordering::SeqCst);",
        "for_in0..MAX_RETRIES{",
        "letseq=self.seq.load(Ordering::Acquire);",
        "ifseq&1==0&&self.seq.compare_exchange(seq,seq.wrapping_add(1),Ordering::AcqRel,Ordering::Relaxed,).is_ok(){",
        "returnOk(self.epoch_id.load(Ordering::Acquire));}",
        "core::hint::spin_loop();}Err(\"TERMINAL_SNAPSHOT_UNAVAILABLE\")}"
    );
    assert!(
        normalized.contains(expected_freeze),
        "SharedManifest::freeze drifted from Loom-verified memory ordering contract"
    );
}
