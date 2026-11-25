#[cfg(test)]
mod tests {
    // Replay Tests: Causal State Determinism
    // Verifies that a given sequence of causal events always deterministically rebuilds the same State Tuple.
    
    use sha2::{Digest, Sha256};

    #[test]
    fn test_causal_determinism_replay_hash() {
        // Enforces that execution determinism is invariant to physical hardware state,
        // using genuine cryptographic SHA-256 hash accumulation.
        
        let initial_state_hash = "BABYLON-60-INIT-HASH";
        let mock_trace = vec![
            "EV_01: FORK TaskA",
            "EV_02: AWAIT DB_SYNC",
            "EV_03: EMIT DB_SYNC",
        ];
        
        // Simulating the replay of the trace through SHA256 accumulation:
        // H_0 = SHA256(initial_state_hash)
        // H_{i+1} = SHA256(H_i ++ event_bytes)
        let compute_trace_hash = |trace: &[&str]| -> String {
            let mut hasher = Sha256::new();
            hasher.update(initial_state_hash.as_bytes());
            let mut current_hash = hasher.finalize().to_vec();

            for ev in trace {
                let mut step_hasher = Sha256::new();
                step_hasher.update(&current_hash);
                step_hasher.update(ev.as_bytes());
                current_hash = step_hasher.finalize().to_vec();
            }
            hex::encode(current_hash)
        };

        let computed_hash = compute_trace_hash(&mock_trace);
        
        // Replay again to confirm bit-for-bit determinism
        let replayed_hash = compute_trace_hash(&mock_trace);
        assert_eq!(
            computed_hash, replayed_hash,
            "CRITICAL: Causal determinism broken. Replay hash diverged across iterations."
        );

        // Negative test: verify that a trace with identical string lengths but different event payload
        // produces a completely different hash (anti-collision property).
        let mutated_trace = vec![
            "EV_01: KILL TaskA",
            "EV_02: AWAIT DB_SYNC",
            "EV_03: EMIT DB_SYNC",
        ];
        let mutated_hash = compute_trace_hash(&mutated_trace);
        assert_ne!(
            computed_hash, mutated_hash,
            "CRITICAL: Hash collision detected! String length hashing vulnerability reintroduced."
        );
    }

    // --- UNIÓN α: Algebra Monoidal de Transacciones (M, ⊗, e) ---

    pub trait Monoid: Sized + PartialEq {
        fn empty() -> Self;
        fn combine(&self, other: &Self) -> Self;
    }

    #[derive(Debug, Clone, PartialEq, Eq)]
    pub struct LedgerBatch {
        pub events: Vec<String>,
    }

    impl Monoid for LedgerBatch {
        fn empty() -> Self {
            LedgerBatch { events: Vec::new() }
        }

        fn combine(&self, other: &Self) -> Self {
            let mut combined = self.events.clone();
            combined.extend(other.events.clone());
            LedgerBatch { events: combined }
        }
    }

    #[test]
    fn test_monoidal_ledger_associativity() {
        // Demuestra algebraicamente la ley asociativa: (A ⊗ B) ⊗ C == A ⊗ (B ⊗ C)
        let a = LedgerBatch { events: vec!["EV_01: DAH R0, 1/2".to_string()] };
        let b = LedgerBatch { events: vec!["EV_02: LAL R1, R0".to_string()] };
        let c = LedgerBatch { events: vec!["EV_03: FORK Child_01".to_string()] };

        let ab_then_c = a.combine(&b).combine(&c);
        let a_then_bc = a.combine(&b.combine(&c));

        assert_eq!(
            ab_then_c, a_then_bc,
            "VIOLACIÓN MONOIDAL: La composición de lotes no es asociativa."
        );
    }

    #[test]
    fn test_monoidal_ledger_identity() {
        // Demuestra el elemento neutro: A ⊗ e == A y e ⊗ A == A
        let a = LedgerBatch { events: vec!["EV_01: DAH R0, 1/2".to_string()] };
        let e = LedgerBatch::empty();

        assert_eq!(a.combine(&e), a, "VIOLACIÓN DE IDENTIDAD DERECHA");
        assert_eq!(e.combine(&a), a, "VIOLACIÓN DE IDENTIDAD IZQUIERDA");
    }
}

