//! Pinning and local persistent replay checks on isolated files/processes.
#![cfg(unix)]
#[path = "support/solver_trust_support.rs"]
mod support;
use babylon60_compiler::semantic_solver::{
    BinaryAuthError, ReceiptError, SolveError, SolverLimits, Z3Adapter, MAX_SOLVER_BINARY_BYTES,
};
use babylon60_compiler::solver_replay::{ReplayError, ReplayJournal, MAX_JOURNAL_BYTES};
use kernel::semantic_entropy::{solver_binary_digest, SemanticEntropyVerdict, SolverOutcome};
use std::fs::{File, OpenOptions};
use std::io::Write;
use std::os::unix::fs::{symlink, PermissionsExt};
use std::process::{Command, Stdio};
use std::sync::{Arc, Barrier};
use std::time::{Duration, Instant};
use support::{real_pin, z3_path, TempDir, NAMESPACE};

fn native(root: &TempDir, journal: ReplayJournal) -> Z3Adapter {
    Z3Adapter::with_temp_root(
        z3_path(),
        real_pin(),
        SolverLimits::default(),
        journal,
        &root.0,
    )
    .unwrap()
}
fn fake(root: &TempDir, journal: ReplayJournal, body: &str) -> (Z3Adapter, std::path::PathBuf) {
    let path = root.program("fixture-solver", body);
    let pin = solver_binary_digest(&std::fs::read(&path).unwrap());
    (
        Z3Adapter::with_temp_root(&path, pin, SolverLimits::default(), journal, &root.0).unwrap(),
        path,
    )
}
const SAT: &str = "print('sat')\nprint('(:reason-unknown \"\")')";

#[test]
fn approved_real_binary_runs_and_query_is_reserved_and_consumed_once() {
    let root = TempDir::new();
    let journal = root.journal();
    let a = native(&root, journal.clone());
    let q = a.query(1, 1, 1, "(assert true)").unwrap();
    let receipt = a.solve(&q).unwrap();
    assert_eq!(receipt.outcome(), SolverOutcome::Sat);
    assert!(matches!(
        a.solve(&q),
        Err(SolveError::Replay(ReplayError::Replay))
    ));
    assert!(matches!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::VerifiedGenuine { .. })
    ));
    assert_eq!(
        receipt.evaluate(&q),
        Err(ReceiptError::Replay(ReplayError::Replay))
    );
    let reopened = ReplayJournal::open(journal.path(), NAMESPACE).unwrap();
    let b = native(&root, reopened);
    let same = b.query(1, 1, 1, "(assert true)").unwrap();
    assert_eq!(q.digest(), same.digest());
    assert!(matches!(
        b.solve(&same),
        Err(SolveError::Replay(ReplayError::Replay))
    ));
    let changed = b.query(1, 1, 1, "(assert (= 1 1))").unwrap();
    assert!(matches!(
        b.solve(&changed),
        Err(SolveError::Replay(ReplayError::Replay))
    ));
}

#[test]
fn wrong_query_does_not_consume_the_correct_receipt() {
    let root = TempDir::new();
    let a = native(&root, root.journal());
    let q = a.query(2, 1, 1, "(assert true)").unwrap();
    let wrong = a.query(3, 1, 1, "(assert true)").unwrap();
    let receipt = a.solve(&q).unwrap();
    assert_eq!(receipt.evaluate(&wrong), Err(ReceiptError::QueryMismatch));
    assert!(matches!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::VerifiedGenuine { .. })
    ));
}

#[test]
fn binary_substitution_is_rejected_before_any_process_effect() {
    let root = TempDir::new();
    let marker = root.0.join("ran");
    let (a, path) = fake(&root, root.journal(), SAT);
    let q = a.query(4, 1, 1, "(assert true)").unwrap();
    let previous = std::fs::read(&path).unwrap();
    std::fs::write(
        &path,
        format!(
            "#!/usr/bin/python3\nfrom pathlib import Path\nPath({:?}).write_text('ran')\n{SAT}\n",
            marker.to_str().unwrap()
        ),
    )
    .unwrap();
    assert_ne!(
        solver_binary_digest(&previous),
        solver_binary_digest(&std::fs::read(&path).unwrap())
    );
    assert!(matches!(
        a.solve(&q),
        Err(SolveError::Authentication(BinaryAuthError::HashMismatch))
    ));
    assert!(!marker.exists());
}

#[test]
fn execution_uses_exact_verified_snapshot_even_when_source_is_overwritten() {
    let root = TempDir::new();
    let original = root.0.join("fixture-solver");
    let witness = root.0.join("executed-bytes");
    let location = root.0.join("executed-path");
    let body = format!("from pathlib import Path\np=Path(__file__)\nPath({:?}).write_bytes(p.read_bytes())\nPath({:?}).write_text(str(p))\nPath({:?}).write_text('substituted after startup')\n{SAT}", witness.to_str().unwrap(), location.to_str().unwrap(), original.to_str().unwrap());
    let (a, path) = fake(&root, root.journal(), &body);
    let approved = std::fs::read(&path).unwrap();
    let q = a.query(5, 1, 1, "(assert true)").unwrap();
    let receipt = a.solve(&q).unwrap();
    assert_eq!(receipt.outcome(), SolverOutcome::Sat);
    assert!(matches!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::VerifiedGenuine { .. })
    ));
    assert_eq!(std::fs::read(&witness).unwrap(), approved);
    let executed = std::fs::read_to_string(location).unwrap();
    assert_ne!(std::path::Path::new(&executed), path);
    assert!(std::path::Path::new(&executed).starts_with(&root.0));
    assert_eq!(
        std::fs::read_to_string(&path).unwrap(),
        "substituted after startup"
    );
    let q2 = a.query(6, 1, 1, "(assert true)").unwrap();
    assert!(matches!(
        a.solve(&q2),
        Err(SolveError::Authentication(BinaryAuthError::HashMismatch))
    ));
}

#[test]
fn pin_journal_and_duration_are_independent_query_binding_fields() {
    let root = TempDir::new();
    let journal = root.journal();
    let a = native(&root, journal.clone());
    let expected = a.query(7, 1, 1, "(assert true)").unwrap();
    let b = Z3Adapter::with_temp_root(
        z3_path(),
        [0; 32],
        SolverLimits::default(),
        journal.clone(),
        &root.0,
    )
    .unwrap();
    let c = Z3Adapter::with_temp_root(
        z3_path(),
        real_pin(),
        SolverLimits {
            wall_timeout: Duration::new(2, 1),
            ..SolverLimits::default()
        },
        journal,
        &root.0,
    )
    .unwrap();
    let another = TempDir::new();
    let d = Z3Adapter::with_temp_root(
        z3_path(),
        real_pin(),
        SolverLimits::default(),
        another.journal(),
        &root.0,
    )
    .unwrap();
    for altered in [&b, &c, &d] {
        let q = altered.query(7, 1, 1, "(assert true)").unwrap();
        assert_ne!(expected.digest(), q.digest());
        assert!(matches!(a.solve(&q), Err(SolveError::QueryMismatch)));
    }
}

#[test]
fn source_symlink_fifo_directory_and_oversize_never_execute() {
    let root = TempDir::new();
    let path = root.program("approved", SAT);
    let pin = solver_binary_digest(&std::fs::read(&path).unwrap());
    let link = root.0.join("link");
    symlink(&path, &link).unwrap();
    let fifo = root.0.join("fifo");
    assert!(Command::new("mkfifo")
        .arg(&fifo)
        .status()
        .unwrap()
        .success());
    let big = root.0.join("too-big");
    File::create(&big)
        .unwrap()
        .set_len(MAX_SOLVER_BINARY_BYTES as u64 + 1)
        .unwrap();
    let journal = root.journal();
    for (id, source, expected) in [
        (10, link, BinaryAuthError::Io),
        (11, fifo, BinaryAuthError::NotRegular),
        (12, root.0.clone(), BinaryAuthError::NotRegular),
        (13, big, BinaryAuthError::TooLarge),
    ] {
        let a = Z3Adapter::new(source, pin, SolverLimits::default(), journal.clone()).unwrap();
        let q = a.query(id, 1, 1, "(assert true)").unwrap();
        let started = Instant::now();
        assert!(matches!(a.solve(&q), Err(SolveError::Authentication(error)) if error == expected));
        assert!(started.elapsed() < Duration::from_secs(2));
    }
}

#[test]
fn unknown_unsat_and_process_error_receipts_are_consumed_too() {
    for (id, body, limits) in [
        (20, "(assert false)", SolverLimits::default()),
        (
            21,
            "(declare-const x Int) (assert (> x 0))",
            SolverLimits {
                resource_limit: 1,
                ..SolverLimits::default()
            },
        ),
    ] {
        let root = TempDir::new();
        let journal = root.journal();
        let a = Z3Adapter::new(z3_path(), real_pin(), limits, journal).unwrap();
        let q = a.query(id, 1, 1, body).unwrap();
        let receipt = a.solve(&q).unwrap();
        assert!(!matches!(
            receipt.evaluate(&q),
            Ok(SemanticEntropyVerdict::VerifiedGenuine { .. }
                | SemanticEntropyVerdict::VerifiedPolysemy { .. })
        ));
        assert_eq!(
            receipt.evaluate(&q),
            Err(ReceiptError::Replay(ReplayError::Replay))
        );
    }
    let root = TempDir::new();
    let (a, _) = fake(&root, root.journal(), "import sys\nsys.exit(7)");
    let q = a.query(22, 1, 1, "(assert true)").unwrap();
    let receipt = a.solve(&q).unwrap();
    assert!(matches!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::SolverFailure { .. })
    ));
    assert_eq!(
        receipt.evaluate(&q),
        Err(ReceiptError::Replay(ReplayError::Replay))
    );
}

#[test]
fn receipt_admission_is_atomic_between_threads() {
    let root = TempDir::new();
    let (a, _) = fake(&root, root.journal(), SAT);
    let q = Arc::new(a.query(30, 1, 1, "(assert true)").unwrap());
    let receipt = Arc::new(a.solve(&q).unwrap());
    let barrier = Arc::new(Barrier::new(8));
    let workers: Vec<_> = (0..8)
        .map(|_| {
            let (q, receipt, barrier) = (q.clone(), receipt.clone(), barrier.clone());
            std::thread::spawn(move || {
                barrier.wait();
                receipt.evaluate(&q)
            })
        })
        .collect();
    let results: Vec<_> = workers.into_iter().map(|w| w.join().unwrap()).collect();
    assert_eq!(results.iter().filter(|r| r.is_ok()).count(), 1);
    assert_eq!(
        results
            .iter()
            .filter(|r| **r == Err(ReceiptError::Replay(ReplayError::Replay)))
            .count(),
        7
    );
}

#[test]
fn bounded_warmed_stress_runs_at_most_once_per_id_with_independent_marker() {
    let root = TempDir::new();
    let marker = root.0.join("executions");
    let script = format!(
        "with open({:?}, 'a') as f: f.write('executed\\n')\n{SAT}",
        marker.to_str().unwrap()
    );
    let (a, _) = fake(&root, root.journal(), &script);
    let a = Arc::new(a);
    for id in 100..102 {
        let q = a.query(id, 1, 1, "(assert true)").unwrap();
        a.solve(&q).unwrap().evaluate(&q).unwrap();
    }
    for id in 200..204 {
        let q = Arc::new(a.query(id, 1, 1, "(assert true)").unwrap());
        let barrier = Arc::new(Barrier::new(8));
        let workers: Vec<_> = (0..8)
            .map(|_| {
                let (a, q, barrier) = (a.clone(), q.clone(), barrier.clone());
                std::thread::spawn(move || {
                    barrier.wait();
                    match a.solve(&q) {
                        Ok(receipt) => {
                            assert!(receipt.evaluate(&q).is_ok());
                            true
                        }
                        Err(SolveError::Replay(ReplayError::Replay)) => false,
                        error => panic!("unexpected {error:?}"),
                    }
                })
            })
            .collect();
        assert_eq!(
            workers
                .into_iter()
                .map(|w| usize::from(w.join().unwrap()))
                .sum::<usize>(),
            1
        );
    }
    assert_eq!(std::fs::read_to_string(marker).unwrap().lines().count(), 6);
}

#[test]
fn journal_states_survive_reopen_and_reject_changed_digest() {
    let root = TempDir::new();
    let journal = root.journal();
    assert_eq!(
        journal.consume(1, [1; 32]),
        Err(ReplayError::MissingReservation)
    );
    journal.reserve(1, [1; 32]).unwrap();
    assert_eq!(journal.reserve(1, [2; 32]), Err(ReplayError::Replay));
    assert_eq!(journal.consume(1, [2; 32]), Err(ReplayError::QueryMismatch));
    journal.consume(1, [1; 32]).unwrap();
    let reopened = ReplayJournal::open(journal.path(), NAMESPACE).unwrap();
    assert_eq!(reopened.reserve(1, [1; 32]), Err(ReplayError::Replay));
    assert_eq!(reopened.consume(1, [1; 32]), Err(ReplayError::Replay));
    assert_eq!(
        std::fs::metadata(journal.path()).unwrap().len(),
        64 + 2 * 80
    );
}

#[test]
fn absent_corrupt_partial_wrong_namespace_and_full_journals_fail_closed() {
    let missing = TempDir::new();
    assert!(ReplayJournal::open(missing.0.join("absent"), NAMESPACE).is_err());
    assert!(!missing.0.join("absent").exists());
    for mode in 0..5 {
        let root = TempDir::new();
        let journal = root.journal();
        journal.reserve(1, [1; 32]).unwrap();
        match mode {
            0 => {
                OpenOptions::new()
                    .append(true)
                    .open(journal.path())
                    .unwrap()
                    .write_all(b"partial")
                    .unwrap();
            }
            1 => {
                let mut data = std::fs::read(journal.path()).unwrap();
                data[90] ^= 1;
                std::fs::write(journal.path(), data).unwrap();
            }
            2 => {
                OpenOptions::new()
                    .write(true)
                    .open(journal.path())
                    .unwrap()
                    .set_len(63)
                    .unwrap();
            }
            3 => {
                assert!(matches!(
                    ReplayJournal::open(journal.path(), [0; 16]),
                    Err(ReplayError::Corrupt)
                ));
                continue;
            }
            _ => {
                OpenOptions::new()
                    .write(true)
                    .open(journal.path())
                    .unwrap()
                    .set_len(MAX_JOURNAL_BYTES as u64 + 1)
                    .unwrap();
            }
        }
        let expected = if mode == 4 {
            ReplayError::Capacity
        } else {
            ReplayError::Corrupt
        };
        assert!(matches!(ReplayJournal::open(journal.path(),NAMESPACE), Err(e) if e==expected));
        assert_eq!(journal.reserve(2, [2; 32]), Err(expected));
    }
}

#[test]
fn journal_missing_or_unusable_at_consumption_never_returns_verified() {
    let root = TempDir::new();
    let journal = root.journal();
    let (a, _) = fake(&root, journal.clone(), SAT);
    let q = a.query(40, 1, 1, "(assert true)").unwrap();
    let receipt = a.solve(&q).unwrap();
    std::fs::set_permissions(journal.path(), std::fs::Permissions::from_mode(0o400)).unwrap();
    assert!(matches!(receipt.evaluate(&q), Err(ReceiptError::Replay(_))));
    std::fs::set_permissions(journal.path(), std::fs::Permissions::from_mode(0o600)).unwrap();
    std::fs::remove_file(journal.path()).unwrap();
    assert!(matches!(receipt.evaluate(&q), Err(ReceiptError::Replay(_))));
    assert!(!journal.path().exists());
}

#[test]
fn journal_symlink_hardlink_public_parent_and_fifo_parent_reject() {
    let root = TempDir::new();
    let journal = root.journal();
    let link = root.0.join("symlink");
    symlink(journal.path(), &link).unwrap();
    assert!(ReplayJournal::open(link, NAMESPACE).is_err());
    let hard = root.0.join("hard");
    std::fs::hard_link(journal.path(), hard).unwrap();
    assert!(ReplayJournal::open(journal.path(), NAMESPACE).is_err());
    let public = TempDir::new();
    std::fs::set_permissions(&public.0, std::fs::Permissions::from_mode(0o755)).unwrap();
    assert!(ReplayJournal::create(public.0.join("journal"), NAMESPACE).is_err());
    let fifo = root.0.join("parent-fifo");
    assert!(Command::new("mkfifo")
        .arg(&fifo)
        .status()
        .unwrap()
        .success());
    let now = Instant::now();
    assert!(ReplayJournal::create(fifo.join("journal"), NAMESPACE).is_err());
    assert!(now.elapsed() < Duration::from_secs(2));
}

fn worker(path: &std::path::Path, mode: &str, ack: Option<&std::path::Path>) -> Command {
    let mut command = Command::new(std::env::current_exe().unwrap());
    command
        .args(["--exact", "replay_worker", "--ignored", "--nocapture"])
        .env("B60_TEST_REPLAY_PATH", path)
        .env("B60_TEST_REPLAY_MODE", mode)
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    if let Some(ack) = ack {
        command.env("B60_TEST_REPLAY_ACK", ack);
    }
    command
}

#[test]
#[ignore = "subprocess worker, invoked explicitly with a private journal"]
fn replay_worker() {
    let path = std::env::var_os("B60_TEST_REPLAY_PATH").expect("explicit child fixture");
    let journal = ReplayJournal::open(path, NAMESPACE).unwrap();
    let result = journal.reserve(90000, [0xA5; 32]);
    match result {
        Ok(()) => println!("WORKER_RESERVED"),
        Err(ReplayError::Replay) => println!("WORKER_REPLAY"),
        error => panic!("{error:?}"),
    }
    if std::env::var("B60_TEST_REPLAY_MODE").unwrap() == "hold" {
        assert!(result.is_ok());
        let path = std::env::var_os("B60_TEST_REPLAY_ACK").unwrap();
        let mut ack = File::create(path).unwrap();
        ack.write_all(b"reserved-and-synced").unwrap();
        ack.sync_all().unwrap();
        loop {
            std::thread::sleep(Duration::from_millis(50));
        }
    }
}

#[test]
fn concurrent_processes_reserve_exactly_once() {
    let root = TempDir::new();
    let journal = root.journal();
    let children: Vec<_> = (0..8)
        .map(|_| worker(journal.path(), "reserve", None).spawn().unwrap())
        .collect();
    let outputs: Vec<_> = children
        .into_iter()
        .map(|c| c.wait_with_output().unwrap())
        .collect();
    assert!(outputs.iter().all(|o| o.status.success()));
    assert_eq!(
        outputs
            .iter()
            .filter(|o| String::from_utf8_lossy(&o.stdout).contains("WORKER_RESERVED"))
            .count(),
        1
    );
    assert_eq!(
        outputs
            .iter()
            .filter(|o| String::from_utf8_lossy(&o.stdout).contains("WORKER_REPLAY"))
            .count(),
        7
    );
    assert_eq!(
        ReplayJournal::open(journal.path(), NAMESPACE)
            .unwrap()
            .reserve(90000, [0xA5; 32]),
        Err(ReplayError::Replay)
    );
}

#[test]
fn sigkill_after_synced_reservation_keeps_id_spent_on_restart() {
    use std::os::unix::process::ExitStatusExt;
    let root = TempDir::new();
    let journal = root.journal();
    let ack = root.0.join("ack");
    let mut child = worker(journal.path(), "hold", Some(&ack)).spawn().unwrap();
    let deadline = Instant::now() + Duration::from_secs(5);
    while !ack.exists() && Instant::now() < deadline {
        std::thread::sleep(Duration::from_millis(5));
    }
    let observed = ack.exists();
    child.kill().unwrap();
    let status = child.wait().unwrap();
    assert!(observed, "child never acknowledged durable reservation");
    assert_eq!(status.signal(), Some(9));
    assert_eq!(std::fs::read(ack).unwrap(), b"reserved-and-synced");
    let reopened = ReplayJournal::open(journal.path(), NAMESPACE).unwrap();
    assert_eq!(
        reopened.reserve(90000, [0xA5; 32]),
        Err(ReplayError::Replay)
    );
    reopened.reserve(90001, [0xB6; 32]).unwrap();
}
