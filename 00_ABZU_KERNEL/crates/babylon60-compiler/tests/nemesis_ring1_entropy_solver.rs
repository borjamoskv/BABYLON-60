//! CLAIM-RING1-009 adversarial NEMESIS campaign over `BitmaskSemanticKernel`,
//! `Z3Adapter`, and `ReplayJournal` with independent physical filesystem/process witnesses.
#![cfg(unix)]

#[path = "support/solver_trust_support.rs"]
mod support;

use babylon60_compiler::semantic_solver::{
    BinaryAuthError, QueryError, ReceiptError, SolveError, SolverLimits, Z3Adapter,
};
use babylon60_compiler::solver_replay::{ReplayError, ReplayJournal};
use kernel::semantic_entropy::{
    solver_binary_digest, BitmaskSemanticKernel, SemanticEntropyInputError, SemanticEntropyVerdict,
    SolverError, SolverOutcome, ERR_CONFABULATION, ERR_INCORRECT_BELIEF, TAU_SEM_Q16,
};
use std::os::unix::fs::symlink;
use std::path::Path;
use std::process::Command;
use std::sync::{Arc, Barrier, Mutex};
use std::time::Duration;
use support::{real_pin, z3_path, TempDir, NAMESPACE};

static SERIAL_TIMEOUT_GATE: Mutex<()> = Mutex::new(());

fn is_verified(verdict: SemanticEntropyVerdict) -> bool {
    matches!(
        verdict,
        SemanticEntropyVerdict::VerifiedGenuine { .. }
            | SemanticEntropyVerdict::VerifiedPolysemy { .. }
    )
}

fn is_valid_equivalence(matrix: u64, n: usize) -> bool {
    if n == 0 || n > 8 {
        return false;
    }
    let row_mask = ((1u16 << n) - 1) as u8;
    let mut domain = 0u64;
    for i in 0..n {
        domain |= u64::from(row_mask) << (i * 8);
    }
    if (matrix & !domain) != 0 {
        return false;
    }
    let cell = |i: usize, j: usize| ((matrix >> (i * 8 + j)) & 1) != 0;
    for i in 0..n {
        if !cell(i, i) {
            return false;
        }
        for j in 0..n {
            if cell(i, j) != cell(j, i) {
                return false;
            }
            for k in 0..n {
                if cell(i, j) && cell(j, k) && !cell(i, k) {
                    return false;
                }
            }
        }
    }
    true
}

fn build_fixture_adapter(
    root: &TempDir,
    scratch: &Path,
    journal: ReplayJournal,
    name: &str,
    python_body: &str,
    limits: SolverLimits,
) -> (Z3Adapter, std::path::PathBuf) {
    let exe = root.program(name, python_body);
    let bytes = std::fs::read(&exe).expect("read fixture solver");
    let pin = solver_binary_digest(&bytes);
    let adapter = Z3Adapter::with_temp_root(&exe, pin, limits, journal, scratch)
        .expect("valid fixture adapter");
    (adapter, exe)
}

fn scratch_entries(scratch: &Path) -> usize {
    std::fs::read_dir(scratch)
        .expect("read scratch dir")
        .count()
}

#[test]
fn nem_r1_01_adversarial_nli_relations_never_admit_verified_under_forced_sat() {
    let root = TempDir::new();
    let scratch = TempDir::new();
    let (adapter, _) = build_fixture_adapter(
        &root,
        &scratch.0,
        root.journal(),
        "noop-solver",
        "print('sat')\nprint('(:reason-unknown \"\")')",
        SolverLimits::default(),
    );

    // Exhaustive 2^16 sweep of all 4x4 packed relations in the 8x8 bitmask layout
    let mut valid_count = 0usize;
    let mut rejected_count = 0usize;
    for raw16 in 0u32..65_536 {
        let mut matrix = 0u64;
        for r in 0..4 {
            let row_nibble = ((raw16 >> (r * 4)) & 0xF) as u64;
            matrix |= row_nibble << (r * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(matrix, 4, SolverOutcome::Sat);
        if is_valid_equivalence(matrix, 4) {
            valid_count += 1;
            assert!(
                is_verified(verdict),
                "valid equivalence rejected: {matrix:#x}"
            );
        } else {
            rejected_count += 1;
            assert!(
                !is_verified(verdict),
                "invalid relation admitted under forced SAT: {matrix:#x}"
            );
            assert!(matches!(
                verdict,
                SemanticEntropyVerdict::InvalidInput { .. }
            ));
            assert!(matches!(
                adapter.query(1, matrix, 4, "(assert true)"),
                Err(QueryError::InvalidInput(_))
            ));
        }
    }
    assert_eq!(valid_count, 15); // Bell number B_4 = 15
    assert_eq!(rejected_count, 65_521);

    // Targeted n=8 boundary attacks: missing diagonal, asymmetric edge, non-transitive chain, out-of-domain
    let diag8: u64 = (0..8).fold(0u64, |acc, i| acc | (1u64 << (i * 8 + i)));
    let attacks = [
        (diag8 & !1u64, 8, SemanticEntropyInputError::NotReflexive),
        (
            diag8 | (1u64 << 1),
            8,
            SemanticEntropyInputError::NotSymmetric,
        ),
        (
            diag8 | (1u64 << 1) | (1u64 << 8) | (1u64 << 10) | (1u64 << 17),
            8,
            SemanticEntropyInputError::NotTransitive,
        ),
        (
            1u64 | (1u64 << 63),
            1,
            SemanticEntropyInputError::BitsOutsideDomain,
        ),
        (
            u64::MAX,
            0,
            SemanticEntropyInputError::SampleCountOutOfRange,
        ),
        (
            u64::MAX,
            9,
            SemanticEntropyInputError::SampleCountOutOfRange,
        ),
    ];
    for (matrix, n, expected_err) in attacks {
        assert_eq!(
            BitmaskSemanticKernel::evaluate(matrix, n, SolverOutcome::Sat),
            SemanticEntropyVerdict::InvalidInput {
                error: expected_err
            }
        );
    }
}

#[test]
fn nem_r1_02_smt2_control_injection_and_ambiguous_protocol_output_never_admit() {
    let root = TempDir::new();
    let scratch = TempDir::new();
    let journal = root.journal();
    let witness = root.0.join("pre_exec_spawned.witness");
    let witness_body = format!(
        "from pathlib import Path\nPath({:?}).write_text('spawned')\nprint('sat')\nprint('(:reason-unknown \"\")')",
        witness.to_str().expect("utf8 path")
    );
    let (adapter, _) = build_fixture_adapter(
        &root,
        &scratch.0,
        journal.clone(),
        "witness-solver",
        &witness_body,
        SolverLimits {
            max_output_bytes: 128,
            ..SolverLimits::default()
        },
    );

    for smt_attack in [
        "",
        "(declare-const x Int)",
        "(assert true)\n(check-sat)",
        "(set-option :timeout 9999999)\n(assert true)",
        "(assert true)\n(get-model)",
        "(assert true)\n(echo \"sat\")",
        "(assert true)\n(reset)",
        "(assert true)\n(exit)",
        "(include \"/etc/passwd\")\n(assert true)",
        "(assert true)\n; comment\n(check-sat)",
        "(assert true)\0(exit)",
        "(assert (= 1 1)",
    ] {
        assert!(
            adapter.query(100, 1, 1, smt_attack).is_err(),
            "injection accepted: {smt_attack:?}"
        );
    }
    // Physical witness: none of the rejected scripts spawned the solver process
    assert!(!witness.exists());

    // Post-execution protocol corruption vectors: each must consume its ID and fail-closed as Protocol
    let corrupt_outputs = [
        ("dup-sat", "print('sat')\nprint('sat')\nprint('(:reason-unknown \"\")')"),
        ("sat-unsat", "print('sat')\nprint('unsat')\nprint('(:reason-unknown \"\")')"),
        (
            "sat-with-stderr",
            "import sys\nprint('sat')\nprint('(:reason-unknown \"\")')\nsys.stderr.write('warn\\n')",
        ),
        ("oversize-stdout", "print('sat')\nprint('A' * 512)"),
    ];

    for (idx, (label, body)) in corrupt_outputs.into_iter().enumerate() {
        let req_id = 200 + (idx as u64);
        let (bad_adapter, _) = build_fixture_adapter(
            &root,
            &scratch.0,
            journal.clone(),
            label,
            body,
            SolverLimits {
                max_output_bytes: 128,
                ..SolverLimits::default()
            },
        );
        let q = bad_adapter
            .query(req_id, 1, 1, "(assert true)")
            .expect("valid query");
        let receipt = bad_adapter.solve(&q).expect("receipt bound to failure");
        assert_eq!(
            receipt.outcome(),
            SolverOutcome::Error(SolverError::Protocol)
        );
        assert_eq!(
            receipt.evaluate(&q),
            Ok(SemanticEntropyVerdict::SolverFailure {
                error: SolverError::Protocol
            })
        );
        // Receipt is consumed even on protocol error; replay is blocked
        assert_eq!(
            receipt.evaluate(&q),
            Err(ReceiptError::Replay(ReplayError::Replay))
        );
    }
    assert_eq!(scratch_entries(&scratch.0), 0);
}

#[test]
fn nem_r1_03_toctou_binary_swap_and_symlink_escape_rejected_with_physical_witness() {
    let root = TempDir::new();
    let scratch = TempDir::new();
    let journal = root.journal();
    let legit_witness = root.0.join("legit.witness");
    let pwned_witness = root.0.join("attacker_pwned.witness");
    let target_exe = root.0.join("mutable-solver");

    let self_mutating_body = format!(
        "from pathlib import Path\nPath({:?}).write_text('ok')\nPath({:?}).write_text('#!/usr/bin/python3\\nfrom pathlib import Path\\nPath({:?}).write_text(\"pwned\")\\nprint(\"sat\")\\nprint(\"(:reason-unknown \\\"\\\")\")\\n')\nprint('sat')\nprint('(:reason-unknown \"\")')",
        legit_witness.to_str().expect("utf8"),
        target_exe.to_str().expect("utf8"),
        pwned_witness.to_str().expect("utf8"),
    );

    let (adapter, exe_path) = build_fixture_adapter(
        &root,
        &scratch.0,
        journal.clone(),
        "mutable-solver",
        &self_mutating_body,
        SolverLimits::default(),
    );
    assert_eq!(exe_path, target_exe);

    // First invocation runs the verified snapshot even while overwriting the source path
    let q1 = adapter.query(301, 1, 1, "(assert true)").expect("q1");
    let r1 = adapter.solve(&q1).expect("r1");
    assert!(matches!(
        r1.evaluate(&q1),
        Ok(SemanticEntropyVerdict::VerifiedGenuine { .. })
    ));
    assert!(legit_witness.exists());
    assert!(!pwned_witness.exists());

    // Second invocation detects BLAKE3 drift BEFORE spawning and never writes attacker_pwned.witness
    let q2 = adapter.query(302, 1, 1, "(assert true)").expect("q2");
    assert_eq!(
        adapter.solve(&q2).unwrap_err(),
        SolveError::Authentication(BinaryAuthError::HashMismatch)
    );
    assert!(!pwned_witness.exists());

    // Symlink swap to an executable with identical bytes is rejected by O_NOFOLLOW (ELOOP -> Io)
    let real_copy = root.program("real-copy", "print('sat')\nprint('(:reason-unknown \"\")')");
    let copy_pin = solver_binary_digest(&std::fs::read(&real_copy).expect("read copy"));
    let link_path = root.0.join("symlink-solver");
    symlink(&real_copy, &link_path).expect("create symlink");
    let sym_adapter = Z3Adapter::with_temp_root(
        &link_path,
        copy_pin,
        SolverLimits::default(),
        journal.clone(),
        &scratch.0,
    )
    .expect("config");
    let q3 = sym_adapter.query(303, 1, 1, "(assert true)").expect("q3");
    assert_eq!(
        sym_adapter.solve(&q3).unwrap_err(),
        SolveError::Authentication(BinaryAuthError::Io)
    );

    // Non-regular directory path is rejected with NotRegular
    let dir_adapter = Z3Adapter::with_temp_root(
        &root.0,
        copy_pin,
        SolverLimits::default(),
        journal,
        &scratch.0,
    )
    .expect("dir config");
    let q4 = dir_adapter.query(304, 1, 1, "(assert true)").expect("q4");
    assert_eq!(
        dir_adapter.solve(&q4).unwrap_err(),
        SolveError::Authentication(BinaryAuthError::NotRegular)
    );
    assert_eq!(scratch_entries(&scratch.0), 0);
}

#[test]
fn nem_r1_04_bounded_termination_under_hang_kills_child_and_leaves_zero_temp_residue() {
    let _guard = SERIAL_TIMEOUT_GATE
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());

    let root = TempDir::new();
    let scratch = TempDir::new();
    let pid_file = root.0.join("hung_child.pid");
    let hang_body = format!(
        "import os, time\nfrom pathlib import Path\nPath({:?}).write_text(str(os.getpid()))\ntime.sleep(30)",
        pid_file.to_str().expect("utf8")
    );
    let (adapter, _) = build_fixture_adapter(
        &root,
        &scratch.0,
        root.journal(),
        "hang-solver",
        &hang_body,
        SolverLimits {
            solver_timeout_ms: 50,
            wall_timeout: Duration::from_millis(120),
            ..SolverLimits::default()
        },
    );

    let q = adapter.query(401, 0x201, 2, "(assert true)").expect("q");
    let receipt = adapter.solve(&q).expect("timeout receipt");
    assert_eq!(
        receipt.outcome(),
        SolverOutcome::Error(SolverError::Timeout)
    );
    assert_eq!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::SolverFailure {
            error: SolverError::Timeout
        })
    );
    assert_eq!(
        scratch_entries(&scratch.0),
        0,
        "temporary snapshot/files leaked"
    );

    // If the child reached Python startup before timeout, verify the OS process was killed and reaped
    if let Ok(raw_pid) = std::fs::read_to_string(&pid_file) {
        let pid = raw_pid.trim();
        let status = Command::new("/bin/kill")
            .args(["-0", pid])
            .status()
            .expect("invoke /bin/kill -0");
        assert!(
            !status.success(),
            "hung solver PID {pid} survived ChildGuard kill"
        );
    }
}

#[test]
fn nem_r1_05_concurrent_swarm_replay_storm_executes_physically_once() {
    let root = TempDir::new();
    let scratch = TempDir::new();
    let journal = root.journal();
    let exec_log = root.0.join("executions.log");
    let log_body = format!(
        "import os\nfd = os.open({:?}, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)\nos.write(fd, b'X\\n')\nos.close(fd)\nprint('sat')\nprint('(:reason-unknown \"\")')",
        exec_log.to_str().expect("utf8")
    );
    let (adapter, _) = build_fixture_adapter(
        &root,
        &scratch.0,
        journal.clone(),
        "counting-solver",
        &log_body,
        SolverLimits::default(),
    );

    let shared_adapter = Arc::new(adapter);
    let shared_query = Arc::new(
        shared_adapter
            .query(777, 1, 1, "(assert true)")
            .expect("shared query"),
    );

    const WORKERS: usize = 16;
    let start_barrier = Arc::new(Barrier::new(WORKERS));
    let mut handles = Vec::with_capacity(WORKERS);
    for _ in 0..WORKERS {
        let a = Arc::clone(&shared_adapter);
        let q = Arc::clone(&shared_query);
        let b = Arc::clone(&start_barrier);
        handles.push(std::thread::spawn(move || {
            b.wait();
            a.solve(&q)
        }));
    }

    let mut receipts = Vec::new();
    let mut replay_rejects = 0usize;
    for h in handles {
        match h.join().expect("worker join") {
            Ok(r) => receipts.push(r),
            Err(SolveError::Replay(ReplayError::Replay)) => replay_rejects += 1,
            other => panic!("unexpected solve result: {other:?}"),
        }
    }
    assert_eq!(receipts.len(), 1);
    assert_eq!(replay_rejects, WORKERS - 1);

    // Physical witness: solver process ran strictly once across all 16 racing threads
    let physical_runs = std::fs::read_to_string(&exec_log)
        .expect("read executions.log")
        .lines()
        .count();
    assert_eq!(physical_runs, 1);

    // Concurrent receipt consumption race: 16 threads race on the single receipt
    let shared_receipt = Arc::new(receipts.pop().expect("single receipt"));
    let eval_barrier = Arc::new(Barrier::new(WORKERS));
    let mut eval_handles = Vec::with_capacity(WORKERS);
    for _ in 0..WORKERS {
        let r = Arc::clone(&shared_receipt);
        let q = Arc::clone(&shared_query);
        let b = Arc::clone(&eval_barrier);
        eval_handles.push(std::thread::spawn(move || {
            b.wait();
            r.evaluate(&q)
        }));
    }

    let mut eval_wins = 0usize;
    let mut eval_replays = 0usize;
    for h in eval_handles {
        match h.join().expect("eval join") {
            Ok(SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16: 0,
                num_classes: 1,
            }) => eval_wins += 1,
            Err(ReceiptError::Replay(ReplayError::Replay)) => eval_replays += 1,
            other => panic!("unexpected receipt evaluation: {other:?}"),
        }
    }
    assert_eq!(eval_wins, 1);
    assert_eq!(eval_replays, WORKERS - 1);

    // Durable reopen from disk still rejects request_id 777 even with a changed formula
    let reopened = ReplayJournal::open(journal.path(), NAMESPACE).expect("reopen journal");
    let exe_path = root.0.join("counting-solver");
    let pin = solver_binary_digest(&std::fs::read(&exe_path).expect("read exe"));
    let reopened_adapter = Z3Adapter::with_temp_root(
        &exe_path,
        pin,
        SolverLimits::default(),
        reopened,
        &scratch.0,
    )
    .expect("reopened adapter");
    let mutated = reopened_adapter
        .query(777, 1, 1, "(assert (= 2 2))")
        .expect("mutated query");
    assert_eq!(
        reopened_adapter.solve(&mutated).unwrap_err(),
        SolveError::Replay(ReplayError::Replay)
    );
    assert_eq!(scratch_entries(&scratch.0), 0);
}

#[test]
#[ignore = "requiere el Z3 auditado: BABYLON_Z3_BIN (audit_ring1_entropy_solver.py)"]
fn nem_r1_06_real_z3_adversarial_contradiction_and_rlimit_campaign() {
    let _guard = SERIAL_TIMEOUT_GATE
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner());

    let root = TempDir::new();
    let scratch = TempDir::new();
    let journal = root.journal();
    let z3 = z3_path();
    let pin = real_pin();

    let adapter = Z3Adapter::with_temp_root(
        &z3,
        pin,
        SolverLimits {
            wall_timeout: Duration::from_secs(10),
            ..SolverLimits::default()
        },
        journal.clone(),
        &scratch.0,
    )
    .expect("real Z3 adapter");

    // 1. High-entropy 5-sample identity partition (H_Q16 = 152170 > TAU_SEM_Q16) + UNSAT contradiction -> 0xDEAD_6060
    let id5: u64 = (0..5).fold(0u64, |acc, i| acc | (1u64 << (i * 8 + i)));
    let q_confab = adapter
        .query(
            901,
            id5,
            5,
            "(declare-const a Int)\n(declare-const b Int)\n(assert (> a b))\n(assert (> b a))",
        )
        .expect("confab query");
    let r_confab = adapter.solve(&q_confab).expect("solve confab");
    assert_eq!(r_confab.outcome(), SolverOutcome::Unsat);
    assert_eq!(
        r_confab.evaluate(&q_confab),
        Ok(SemanticEntropyVerdict::ApoptosisConfabulation {
            h_sem_q16: 152_170,
            code: ERR_CONFABULATION,
        })
    );
    assert!(152_170 > TAU_SEM_Q16);

    // 2. Zero-entropy 5-sample clique + UNSAT contradiction -> 0xDEAD_6061
    let clique5: u64 = (0..5).fold(0u64, |acc, i| acc | (0b0001_1111u64 << (i * 8)));
    let q_belief = adapter
        .query(
            902,
            clique5,
            5,
            "(declare-const x Int)\n(assert (= (* 2 x) 1))",
        )
        .expect("belief query");
    let r_belief = adapter.solve(&q_belief).expect("solve belief");
    assert_eq!(r_belief.outcome(), SolverOutcome::Unsat);
    assert_eq!(
        r_belief.evaluate(&q_belief),
        Ok(SemanticEntropyVerdict::ApoptosisIncorrectBelief {
            h_sem_q16: 0,
            code: ERR_INCORRECT_BELIEF,
        })
    );

    // 3. Bounded deterministic step exhaustion (rlimit = 1) -> SolverUnknown, zero scratch residue
    let rlimit_adapter = Z3Adapter::with_temp_root(
        &z3,
        pin,
        SolverLimits {
            resource_limit: 1,
            wall_timeout: Duration::from_secs(10),
            ..SolverLimits::default()
        },
        journal,
        &scratch.0,
    )
    .expect("rlimit adapter");
    let q_rlimit = rlimit_adapter
        .query(903, clique5, 5, "(declare-const x Int)\n(assert (> x 0))")
        .expect("rlimit query");
    let r_rlimit = rlimit_adapter.solve(&q_rlimit).expect("solve rlimit");
    assert_eq!(r_rlimit.outcome(), SolverOutcome::Unknown);
    assert_eq!(
        r_rlimit.unknown_reason(),
        Some("max. resource limit exceeded")
    );
    assert_eq!(
        r_rlimit.evaluate(&q_rlimit),
        Ok(SemanticEntropyVerdict::SolverUnknown)
    );
    assert_eq!(scratch_entries(&scratch.0), 0);
}
