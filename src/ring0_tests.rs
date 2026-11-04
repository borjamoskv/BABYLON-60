//! # Tests de Ring-0 — Puente Causal (L0, HardwareSecurityGate, Merkle)
//!
//! Ejecutar con:
//! ```shell
//! cargo test --locked --lib ring0 --features "cortex-persist,test_mock_hardware" -q
//! ```

#[cfg(all(test, feature = "cortex-persist", feature = "test_mock_hardware"))]
mod ring0_integration {
    use rusqlite::Connection;

    use crate::ring0::mock_gate::MockHardwareGate;
    use crate::ring0::{
        commit_ring0_transition, compute_next_merkle_root, init_l0_schema, AttestationTier,
        CausalEnvelope, GateTrap, HardwareSecurityGate, CANONICAL_ENVELOPE_LEN, FAIL_STOP_CODE,
        MAX_GRAMMAR_TOKENS,
    };

    // ── Helpers ──────────────────────────────────────────────────────────────

    fn open_in_memory() -> Connection {
        let conn = Connection::open_in_memory().expect("in-memory SQLite");
        init_l0_schema(&conn).expect("schema init");
        conn
    }

    fn anchor_fact(conn: &Connection, fact_hash: [u8; 32], tick: i64, domain: i64) {
        let payload = [0xFFu8; 32];
        conn.execute(
            "INSERT INTO l0_anchored_facts (fact_hash, anchored_tick, domain_tag, payload_hash)
             VALUES (?1, ?2, ?3, ?4)",
            rusqlite::params![&fact_hash[..], tick, domain, &payload[..]],
        )
        .expect("anchor_fact insert");
    }

    fn make_envelope(
        tick: u64,
        prev_root: [u8; 32],
        fact_hash: [u8; 32],
        tokens: u16,
        tier: AttestationTier,
    ) -> CausalEnvelope {
        CausalEnvelope {
            logical_tick: tick,
            prev_merkle_root: prev_root,
            source_fact_hash: fact_hash,
            effect_payload_hash: [0x42u8; 32],
            token_count: tokens,
            attestation_tier: tier,
        }
    }

    // ── Serialización canónica ────────────────────────────────────────────────

    #[test]
    fn canonical_bytes_length_is_107() {
        let env = make_envelope(
            1,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        assert_eq!(env.to_canonical_bytes().len(), CANONICAL_ENVELOPE_LEN);
    }

    #[test]
    fn canonical_bytes_no_zero_padding_leakage() {
        // Los primeros 8 bytes deben reflejar el tick en big-endian, no 0
        let env = make_envelope(
            42,
            [0u8; 32],
            [1u8; 32],
            5,
            AttestationTier::PlatformAutonomous,
        );
        let bytes = env.to_canonical_bytes();
        assert_eq!(&bytes[0..8], &42u64.to_be_bytes());
        // El byte 106 debe reflejar el tier
        assert_eq!(bytes[106], AttestationTier::PlatformAutonomous as u8);
    }

    #[test]
    fn canonical_digest_deterministic() {
        let env = make_envelope(
            1,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        let d1 = env.canonical_digest();
        let d2 = env.canonical_digest();
        assert_eq!(d1, d2, "El digest debe ser determinista");
    }

    #[test]
    fn canonical_digest_changes_with_tick() {
        let e1 = make_envelope(
            1,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        let e2 = make_envelope(
            2,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        assert_ne!(
            e1.canonical_digest(),
            e2.canonical_digest(),
            "Ticks distintos deben producir digests distintos"
        );
    }

    // ── compute_next_merkle_root ──────────────────────────────────────────────

    #[test]
    fn merkle_root_deterministic_from_same_inputs() {
        let env = make_envelope(
            1,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        let mut gate = MockHardwareGate::new();
        let receipt = gate.attest_transition(&env).unwrap();
        let r1 = compute_next_merkle_root(&env, &receipt);
        let r2 = compute_next_merkle_root(&env, &receipt);
        assert_eq!(r1, r2);
    }

    #[test]
    fn merkle_root_changes_with_different_ticks() {
        let e1 = make_envelope(
            1,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        let e2 = make_envelope(
            2,
            [0u8; 32],
            [1u8; 32],
            10,
            AttestationTier::PlatformAutonomous,
        );
        let mut gate = MockHardwareGate::new();
        let r1 = compute_next_merkle_root(&e1, &gate.attest_transition(&e1).unwrap());
        let r2 = compute_next_merkle_root(&e2, &gate.attest_transition(&e2).unwrap());
        assert_ne!(r1, r2);
    }

    // ── Cortafuegos 17: límite de tokens ─────────────────────────────────────

    #[test]
    fn grammar_budget_exceeded_returns_trap() {
        let mut conn = open_in_memory();
        let fact_hash = [0xAAu8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);

        let env = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            MAX_GRAMMAR_TOKENS + 1,
            AttestationTier::PlatformAutonomous,
        );
        let mut gate = MockHardwareGate::new();

        let result = commit_ring0_transition(&mut conn, &mut gate, &env);
        assert!(matches!(
            result,
            Err(GateTrap::GrammarBudgetExceeded { observed, max, code })
            if observed == MAX_GRAMMAR_TOKENS + 1
            && max == MAX_GRAMMAR_TOKENS
            && code == FAIL_STOP_CODE
        ));
        assert_eq!(
            gate.call_count, 0,
            "El silicio no debe invocarse si el presupuesto falla"
        );
    }

    // ── Commit exitoso y cadena Merkle ────────────────────────────────────────

    #[test]
    fn happy_path_single_transition() {
        let mut conn = open_in_memory();
        let fact_hash = [0x01u8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);

        let env = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            10,
            AttestationTier::PlatformAutonomous,
        );
        let mut gate = MockHardwareGate::new();

        let committed = commit_ring0_transition(&mut conn, &mut gate, &env)
            .expect("Primera transición debe tener éxito");

        assert_eq!(committed.logical_tick, 1);
        assert_ne!(committed.curr_merkle_root, [0u8; 32]);
        assert_eq!(gate.call_count, 1);
    }

    #[test]
    fn chain_of_three_transitions_merkle_continuity() {
        let mut conn = open_in_memory();
        let fact_hash = [0xBBu8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);
        let mut gate = MockHardwareGate::new();

        let mut prev_root = [0u8; 32];
        for tick in 1u64..=3 {
            let env = make_envelope(
                tick,
                prev_root,
                fact_hash,
                5,
                AttestationTier::PlatformAutonomous,
            );
            let c = commit_ring0_transition(&mut conn, &mut gate, &env)
                .unwrap_or_else(|_| panic!("Transición {tick} debe tener éxito"));
            assert_eq!(c.logical_tick, tick);
            prev_root = c.curr_merkle_root;
        }
        assert_eq!(gate.call_count, 3);
    }

    // ── Invariantes del trigger SQL ───────────────────────────────────────────

    #[test]
    fn non_monotonic_tick_rejected() {
        let mut conn = open_in_memory();
        let fact_hash = [0xCCu8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);
        let mut gate = MockHardwareGate::new();

        // Primer commit exitoso (tick = 1)
        let env1 = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        commit_ring0_transition(&mut conn, &mut gate, &env1).unwrap();

        // Segundo commit con tick = 1 (repetición) → debe fallar
        let env_dup = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        let result = commit_ring0_transition(&mut conn, &mut gate, &env_dup);
        assert!(
            matches!(result, Err(GateTrap::NonMonotonicTick { .. })),
            "Tick repetido debe producir NonMonotonicTick"
        );
    }

    #[test]
    fn broken_merkle_chain_rejected() {
        let mut conn = open_in_memory();
        let fact_hash = [0xDDu8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);
        let mut gate = MockHardwareGate::new();

        // Primer commit (tick = 1, prev_root = 0x00…)
        let env1 = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        commit_ring0_transition(&mut conn, &mut gate, &env1).unwrap();

        // Segundo commit con prev_root incorrecto (debería ser curr_merkle_root del tick 1)
        let env2 = make_envelope(
            2,
            [0xFFu8; 32], // raíz incorrecta → cadena rota
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        let result = commit_ring0_transition(&mut conn, &mut gate, &env2);
        assert!(
            matches!(result, Err(GateTrap::UnanchoredCausalLineage { .. })),
            "Raíz de Merkle incorrecta debe producir UnanchoredCausalLineage"
        );
    }

    #[test]
    fn unanchored_fact_rejected() {
        let mut conn = open_in_memory();
        // No se ancla ningún hecho → todo source_fact_hash es inválido
        let mut gate = MockHardwareGate::new();
        let env = make_envelope(
            1,
            [0u8; 32],
            [0xEEu8; 32], // fact_hash no existe en l0_anchored_facts
            5,
            AttestationTier::PlatformAutonomous,
        );
        let result = commit_ring0_transition(&mut conn, &mut gate, &env);
        assert!(
            matches!(result, Err(GateTrap::UnanchoredCausalLineage { .. })),
            "Hecho no anclado debe producir UnanchoredCausalLineage"
        );
        assert_eq!(
            gate.call_count, 0,
            "El silicio no debe invocarse antes de validar el hecho"
        );
    }

    #[test]
    fn future_fact_tick_rejected() {
        let mut conn = open_in_memory();
        // El hecho tiene anchored_tick = 5, pero el efecto es en tick = 1 (futuro)
        let fact_hash = [0x77u8; 32];
        anchor_fact(&conn, fact_hash, 5, 1); // tick 5 > tick del efecto 1
        let mut gate = MockHardwareGate::new();
        let env = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        let result = commit_ring0_transition(&mut conn, &mut gate, &env);
        assert!(
            matches!(result, Err(GateTrap::UnanchoredCausalLineage { .. })),
            "Hecho con tick futuro debe producir UnanchoredCausalLineage"
        );
    }

    // ── Inmutabilidad del ledger (triggers UPDATE/DELETE) ────────────────────

    #[test]
    fn direct_update_on_ledger_aborts() {
        let mut conn = open_in_memory();
        let fact_hash = [0x10u8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);
        let mut gate = MockHardwareGate::new();
        let env = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        commit_ring0_transition(&mut conn, &mut gate, &env).unwrap();

        let result = conn.execute(
            "UPDATE l0_causal_ledger SET token_count = 99 WHERE logical_tick = 1",
            [],
        );
        assert!(
            result.is_err(),
            "UPDATE directo en el ledger debe ser rechazado por el trigger"
        );
    }

    #[test]
    fn direct_delete_on_ledger_aborts() {
        let mut conn = open_in_memory();
        let fact_hash = [0x11u8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);
        let mut gate = MockHardwareGate::new();
        let env = make_envelope(
            1,
            [0u8; 32],
            fact_hash,
            5,
            AttestationTier::PlatformAutonomous,
        );
        commit_ring0_transition(&mut conn, &mut gate, &env).unwrap();

        let result = conn.execute("DELETE FROM l0_causal_ledger WHERE logical_tick = 1", []);
        assert!(
            result.is_err(),
            "DELETE directo en el ledger debe ser rechazado por el trigger"
        );
    }

    #[test]
    fn direct_update_on_facts_aborts() {
        let conn = open_in_memory();
        let fact_hash = [0x20u8; 32];
        anchor_fact(&conn, fact_hash, 0, 1);

        let result = conn.execute(
            "UPDATE l0_anchored_facts SET domain_tag = 99 WHERE fact_hash = ?1",
            rusqlite::params![&fact_hash[..]],
        );
        assert!(
            result.is_err(),
            "UPDATE en l0_anchored_facts debe ser rechazado por el trigger"
        );
    }

    // ── Atributos de compilación ──────────────────────────────────────────────

    #[test]
    fn fail_stop_code_value() {
        assert_eq!(FAIL_STOP_CODE, 0xDEAD_6060u64);
    }

    #[test]
    fn max_grammar_tokens_value() {
        assert_eq!(MAX_GRAMMAR_TOKENS, 150u16);
    }

    #[test]
    fn equal_tick_is_rejected_before_signing() {
        let mut conn = open_in_memory();
        anchor_fact(&conn, [7; 32], 1, 1);
        let env = make_envelope(1, [0; 32], [7; 32], 0, AttestationTier::PlatformAutonomous);
        let mut gate = MockHardwareGate::new();
        assert!(matches!(
            commit_ring0_transition(&mut conn, &mut gate, &env),
            Err(GateTrap::UnanchoredCausalLineage {
                code: FAIL_STOP_CODE,
                ..
            })
        ));
        assert_eq!(gate.call_count, 0);
        assert_eq!(conn.total_changes(), 1); // Only the explicit preceding anchor.
    }

    #[test]
    fn unreadable_or_malformed_tip_is_never_genesis() {
        for setup in ["", "CREATE TABLE l0_causal_ledger(logical_tick INTEGER,curr_merkle_root BLOB); INSERT INTO l0_causal_ledger VALUES(1,x'01');",
                      "CREATE TABLE l0_causal_ledger(logical_tick INTEGER,curr_merkle_root BLOB); INSERT INTO l0_causal_ledger VALUES(-1,zeroblob(32));"] {
            let mut conn = Connection::open_in_memory().unwrap();
            conn.execute_batch(setup).unwrap();
            let mut gate = MockHardwareGate::new();
            let env = make_envelope(1, [0; 32], [7; 32], 0, AttestationTier::PlatformAutonomous);
            assert!(matches!(commit_ring0_transition(&mut conn, &mut gate, &env), Err(GateTrap::PersistenceFailure { .. })));
            assert_eq!(gate.call_count, 0);
        }
    }

    #[test]
    fn sqlite_integer_limit_and_exhaustion_rejected() {
        let mut conn = open_in_memory();
        let mut gate = MockHardwareGate::new();
        for tick in [i64::MAX as u64 + 1, u64::MAX] {
            let env = make_envelope(
                tick,
                [0; 32],
                [7; 32],
                0,
                AttestationTier::PlatformAutonomous,
            );
            assert!(matches!(
                commit_ring0_transition(&mut conn, &mut gate, &env),
                Err(GateTrap::NonMonotonicTick { .. })
            ));
        }
        let mut corrupt = Connection::open_in_memory().unwrap();
        corrupt.execute_batch("CREATE TABLE l0_causal_ledger(logical_tick INTEGER,curr_merkle_root BLOB); INSERT INTO l0_causal_ledger VALUES(9223372036854775807,zeroblob(32));").unwrap();
        let env = make_envelope(
            i64::MAX as u64,
            [0; 32],
            [7; 32],
            0,
            AttestationTier::PlatformAutonomous,
        );
        assert!(matches!(
            commit_ring0_transition(&mut corrupt, &mut gate, &env),
            Err(GateTrap::NonMonotonicTick { .. })
        ));
        assert_eq!(gate.call_count, 0);
    }

    #[test]
    fn failed_commit_rolls_back_ledger_and_auxiliary_rows() {
        let mut conn = open_in_memory();
        anchor_fact(&conn, [7; 32], 0, 1);
        conn.execute_batch("CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE child(id INTEGER REFERENCES parent(id) DEFERRABLE INITIALLY DEFERRED); CREATE TRIGGER inject_commit_failure AFTER INSERT ON l0_causal_ledger BEGIN INSERT INTO child VALUES(9); END;").unwrap();
        let env = make_envelope(1, [0; 32], [7; 32], 0, AttestationTier::PlatformAutonomous);
        let mut gate = MockHardwareGate::new();
        assert!(matches!(
            commit_ring0_transition(&mut conn, &mut gate, &env),
            Err(GateTrap::SiliconAttestationFailure {
                backend: "SQLite_Commit",
                ..
            })
        ));
        assert_eq!(gate.call_count, 1);
        assert_eq!(
            conn.query_row("SELECT count(*) FROM l0_causal_ledger", [], |r| r
                .get::<_, i64>(0))
                .unwrap(),
            0
        );
        assert_eq!(
            conn.query_row("SELECT count(*) FROM child", [], |r| r.get::<_, i64>(0))
                .unwrap(),
            0
        );
    }

    #[test]
    fn disk_wal_rejection_has_no_persistent_writes_and_writer_conflict_fails_closed() {
        let path = std::env::temp_dir().join(format!(
            "b60-euai-wal-{}-{}.sqlite",
            std::process::id(),
            rand::random::<u64>()
        ));
        let mut conn = Connection::open(&path).unwrap();
        init_l0_schema(&conn).unwrap();
        anchor_fact(&conn, [7; 32], 1, 1);
        let wal = std::path::PathBuf::from(format!("{}-wal", path.display()));
        let before_db = std::fs::read(&path).unwrap();
        let before_wal = std::fs::read(&wal).unwrap();
        let mut gate = MockHardwareGate::new();
        for source in [[7; 32], [8; 32]] {
            let env = make_envelope(1, [0; 32], source, 0, AttestationTier::PlatformAutonomous);
            assert!(matches!(
                commit_ring0_transition(&mut conn, &mut gate, &env),
                Err(GateTrap::UnanchoredCausalLineage { .. })
            ));
        }
        assert_eq!(std::fs::read(&path).unwrap(), before_db);
        assert_eq!(std::fs::read(&wal).unwrap(), before_wal);
        let blocker = Connection::open(&path).unwrap();
        blocker.execute_batch("BEGIN IMMEDIATE").unwrap();
        conn.busy_timeout(std::time::Duration::ZERO).unwrap();
        let env = make_envelope(1, [0; 32], [7; 32], 0, AttestationTier::PlatformAutonomous);
        assert!(matches!(
            commit_ring0_transition(&mut conn, &mut gate, &env),
            Err(GateTrap::SiliconAttestationFailure {
                backend: "SQLite_BeginImmediate",
                ..
            })
        ));
        assert_eq!(gate.call_count, 0);
        blocker.execute_batch("ROLLBACK").unwrap();
        drop(blocker);
        drop(conn);
        std::fs::remove_file(path).unwrap();
    }
}
