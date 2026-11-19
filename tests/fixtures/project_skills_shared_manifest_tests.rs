#[cfg(test)]
extern crate std;

#[cfg(test)]
mod regression_tests {
    use super::*;
    use std::{sync::Arc, thread, vec::Vec};

    #[test]
    fn layout_and_snapshot() {
        assert_eq!(core::mem::size_of::<SharedManifest>(), 64);
        assert_eq!(core::mem::align_of::<SharedManifest>(), 64);
        let m = SharedManifest::new();
        assert!(m.publish(7, &[7; 4]));
        assert_eq!(m.read(), Ok((7, [7; 4])));
    }

    #[test]
    fn halt_is_terminal_and_idempotent() {
        let m = SharedManifest::new();
        assert!(m.publish(7, &[7; 4]));
        m.epistemic_halt();
        m.epistemic_halt();
        assert!(m.is_halted());
        assert!(!m.publish(8, &[8; 4]));
        assert_eq!(m.read(), Err(ReadError::Halted));
        assert_eq!(m.epoch_id.load(Ordering::SeqCst), 7);
    }

    #[test]
    fn bounded_reader_reports_contention_without_writing() {
        let m = SharedManifest::new();
        m.seq.store(1, Ordering::SeqCst);
        assert_eq!(m.read(), Err(ReadError::Contended));
        assert_eq!(m.seq.load(Ordering::SeqCst), 1);
        assert_eq!(m.status_flag.load(Ordering::SeqCst), RUNNING);
        // A supervisory policy can explicitly halt; the reader does not do so.
        m.epistemic_halt();
        assert_eq!(m.read(), Err(ReadError::Halted));
    }

    #[test]
    fn counter_never_wraps_into_an_old_snapshot() {
        let m = SharedManifest::new();
        m.seq.store(u32::MAX - 1, Ordering::SeqCst);
        assert!(!m.publish(8, &[8; 4]));
        assert!(m.is_halted());
        assert_eq!(m.seq.load(Ordering::SeqCst), u32::MAX - 1);
        assert!(!m.publish(9, &[9; 4]));
    }

    #[test]
    fn concurrent_readers_never_return_mixed_payloads() {
        let m = Arc::new(SharedManifest::new());
        assert!(m.publish(0, &[0; 4]));
        let rounds = if cfg!(miri) { 16 } else { 20_000 };
        let readers = if cfg!(miri) { 2 } else { 4 };
        let mut handles = Vec::new();
        for _ in 0..readers {
            let m = Arc::clone(&m);
            handles.push(thread::spawn(move || {
                for _ in 0..rounds {
                    match m.read() {
                        Ok((epoch, hash)) => assert_eq!(hash, [epoch; 4]),
                        Err(ReadError::Contended) => (),
                        Err(ReadError::Halted) => panic!("unexpected halt"),
                    }
                }
            }));
        }
        for epoch in 1..=rounds {
            assert!(m.publish(epoch, &[epoch; 4]));
        }
        for handle in handles {
            handle.join().unwrap();
        }
        assert_eq!(m.read(), Ok((rounds, [rounds; 4])));
    }

    #[test]
    fn halt_racing_with_publication_cannot_reopen_admission() {
        let rounds = if cfg!(miri) { 2 } else { 128 };
        for _ in 0..rounds {
            let m = Arc::new(SharedManifest::new());
            let writer = Arc::clone(&m);
            let handle = thread::spawn(move || writer.publish(9, &[9; 4]));
            m.epistemic_halt();
            handle.join().unwrap();
            assert!(m.is_halted());
            assert!(!m.publish(10, &[10; 4]));
            assert_eq!(m.read(), Err(ReadError::Halted));
        }
    }
}
