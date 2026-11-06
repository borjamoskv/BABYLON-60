//! Real Z3 integration plus explicitly isolated negative process fixtures.
use babylon60_compiler::semantic_solver::{EntropyQuery, SolverLimits, Z3Adapter};
use kernel::semantic_entropy::{SemanticEntropyVerdict, SolverError, SolverOutcome};
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};
use std::time::{Duration, Instant};

#[path = "support/solver_trust_support.rs"]
mod support;
use support::{secure_new, secure_temp, z3_path, TestAdapter};

// These fixtures exercise short process deadlines, including a 30ms timeout.
// Queue test cases before starting that measured budget rather than making
// unrelated Z3/Python processes compete for the same host resources. Functional
// cases also allow bounded startup headroom on a shared host; they do not measure
// the production wall deadline. Production limits, the explicit 30ms timeout
// regression and the independent replay-concurrency tests are unchanged.
static PROCESS_BUDGET: Mutex<()> = Mutex::new(());

fn process_budget() -> MutexGuard<'static, ()> {
    PROCESS_BUDGET
        .lock()
        .unwrap_or_else(|poisoned| poisoned.into_inner())
}

fn functional_limits() -> SolverLimits {
    SolverLimits {
        wall_timeout: Duration::from_secs(10),
        ..SolverLimits::default()
    }
}

fn adapter() -> TestAdapter {
    secure_new(z3_path(), functional_limits()).unwrap()
}

fn query(adapter: &Z3Adapter, id: u64, body: &str) -> EntropyQuery {
    adapter.query(id, 1, 1, body).unwrap()
}

#[test]
fn real_sat_and_unsat_reach_all_four_entropy_variants() {
    let _budget = process_budget();
    let adapter = adapter();
    for (id, matrix, n, body, outcome) in [
        (1, 1, 1, "(assert true)", SolverOutcome::Sat),
        (2, 1, 1, "(assert false)", SolverOutcome::Unsat),
        (3, 0x201, 2, "(assert true)", SolverOutcome::Sat),
        (4, 0x201, 2, "(assert false)", SolverOutcome::Unsat),
    ] {
        let q = adapter.query(id, matrix, n, body).unwrap();
        let receipt = adapter.solve(&q).unwrap();
        assert_eq!(receipt.outcome(), outcome, "{:?}", receipt.stderr());
        assert_eq!(receipt.request_id(), id);
        assert_eq!(receipt.query_digest(), q.digest());
        let expected = match (id, outcome) {
            (1, _) => SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16: 0,
                num_classes: 1,
            },
            (2, _) => SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                h_sem_q16: 0,
                code: 0xDEAD_6061,
            },
            (3, _) => SemanticEntropyVerdict::VerifiedPolysemy {
                h_sem_q16: 65536,
                num_classes: 2,
            },
            _ => SemanticEntropyVerdict::ApoptosisConfabulation {
                h_sem_q16: 65536,
                code: 0xDEAD_6060,
            },
        };
        assert_eq!(receipt.evaluate(&q), Ok(expected));
    }
}

#[test]
fn real_unknown_retains_resource_reason_and_cannot_be_admitted() {
    let _budget = process_budget();
    let limits = SolverLimits {
        resource_limit: 1,
        ..functional_limits()
    };
    let adapter = secure_new(z3_path(), limits).unwrap();
    for id in 10..13 {
        let q = query(&adapter, id, "(declare-const x Int)\n(assert (> x 0))");
        let receipt = adapter.solve(&q).unwrap();
        assert_eq!(receipt.outcome(), SolverOutcome::Unknown);
        assert_eq!(
            receipt.unknown_reason(),
            Some("max. resource limit exceeded")
        );
        assert_eq!(
            receipt.evaluate(&q),
            Ok(SemanticEntropyVerdict::SolverUnknown)
        );
    }
}

#[test]
fn receipt_rejects_other_request_body_partition_and_policy() {
    let _budget = process_budget();
    let adapter = adapter();
    let q = query(&adapter, 20, "(assert true)");
    let receipt = adapter.solve(&q).unwrap();
    assert_eq!(receipt.outcome(), SolverOutcome::Sat);
    let other_policy = secure_new(
        z3_path(),
        SolverLimits {
            resource_limit: 2000000,
            ..functional_limits()
        },
    )
    .unwrap();
    let fractional_policy = secure_new(
        z3_path(),
        SolverLimits {
            wall_timeout: Duration::new(10, 1),
            ..functional_limits()
        },
    )
    .unwrap();
    let others = [
        query(&adapter, 21, "(assert true)"),
        query(&adapter, 20, "(assert (= 1 1))"), // Same SAT, different exact formula.
        query(&adapter, 20, "(assert true)\n; different exact bytes"),
        adapter.query(20, 0x201, 2, "(assert true)").unwrap(),
        adapter.query(20, 0x303, 2, "(assert true)").unwrap(),
        query(&other_policy, 20, "(assert true)"),
        query(&fractional_policy, 20, "(assert true)"),
    ];
    for other in others {
        assert_ne!(q.digest(), other.digest());
        assert!(receipt.evaluate(&other).is_err());
    }
}

#[test]
fn separate_processes_do_not_retain_previous_assertions() {
    let _budget = process_budget();
    let adapter = adapter();
    for id in 30..34 {
        let body = if id % 2 == 0 {
            "(assert false)"
        } else {
            "(assert true)"
        };
        let q = query(&adapter, id, body);
        assert_eq!(
            adapter.solve(&q).unwrap().outcome(),
            if id % 2 == 0 {
                SolverOutcome::Unsat
            } else {
                SolverOutcome::Sat
            }
        );
    }
}

#[test]
fn input_validation_and_control_command_injection_are_rejected_before_execution() {
    let _budget = process_budget();
    let adapter = adapter();
    for body in [
        "(check-sat)",
        "(assert true) (check-sat)",
        "(echo \"sat\")",
        "(reset)",
        "(exit)",
        "(include \"external.smt2\")",
        "(set-option :regular-output-channel \"other\")",
        "(get-model)",
        "(assert true)) (echo \"sat\") (",
        "(assert true",
        "assert true",
        "(assert true)\n; comment\n(check-sat)",
        "(assert true)\r; comment\r(check-sat)",
        "(assert true) trailing_atom",
        "(assert true)\0(check-sat)",
        "(declare-const |back\\slash| Int) (assert true)",
        "(assert (= \"unterminated 1))",
    ] {
        assert!(
            adapter.query(40, 1, 1, body).is_err(),
            "accepted control script: {body}"
        );
    }
    for (matrix, n) in [
        (0, 0),
        (0, 9),
        (0, 1),
        (0x0006_0703, 3),
        (u64::MAX, usize::MAX),
    ] {
        assert!(adapter.query(40, matrix, n, "(assert true)").is_err());
    }
}

#[test]
fn real_parser_handles_comments_quoted_symbols_and_strings() {
    let _budget = process_budget();
    let adapter = adapter();
    for (index, body) in [
        "; (check-sat) ignored comment\n(assert true) ; ) ignored\n",
        "(declare-const |check-sat| Int) (assert (= |check-sat| 1))",
        "(declare-const |semi;(x)| Int) (assert (= |semi;(x)| 1))",
        r#"(assert (= "(echo ""sat"")" "(echo ""sat"")"))"#,
    ]
    .into_iter()
    .enumerate()
    {
        let q = query(&adapter, 50 + index as u64, body);
        assert_eq!(
            adapter.solve(&q).unwrap().outcome(),
            SolverOutcome::Sat,
            "{body}"
        );
    }
}

#[test]
fn real_solver_parse_error_never_accepts_later_sat_output() {
    let _budget = process_budget();
    let adapter = adapter();
    let q = query(&adapter, 60, "(assert undeclared_symbol)");
    let receipt = adapter.solve(&q).unwrap();
    assert!(matches!(receipt.outcome(), SolverOutcome::Error(_)));
    assert!(matches!(
        receipt.evaluate(&q),
        Ok(SemanticEntropyVerdict::SolverFailure { .. })
    ));
}

#[cfg(unix)]
mod negative_processes {
    use super::*;
    use std::os::unix::fs::{DirBuilderExt, PermissionsExt};

    struct Fixture(PathBuf);
    impl Fixture {
        fn new() -> Self {
            static NEXT: AtomicU64 = AtomicU64::new(1);
            let root = std::env::temp_dir().join(format!(
                "b60-adapter-tests-{}-{}",
                std::process::id(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            std::fs::DirBuilder::new()
                .mode(0o700)
                .create(&root)
                .unwrap();
            Self(root)
        }
        fn program(&self, name: &str, body: &str) -> PathBuf {
            let file = self.0.join(name);
            std::fs::write(&file, format!("#!/usr/bin/python3\n{body}\n")).unwrap();
            std::fs::set_permissions(&file, std::fs::Permissions::from_mode(0o700)).unwrap();
            file
        }
        fn temp_root(&self) -> PathBuf {
            let dir = self.0.join("solver-temp");
            std::fs::create_dir(&dir).unwrap();
            dir
        }
    }
    impl Drop for Fixture {
        fn drop(&mut self) {
            let _ = std::fs::remove_dir_all(&self.0);
        }
    }

    #[test]
    fn malformed_or_ambiguous_output_is_protocol_failure_even_with_sat() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        for (i, output) in [
            "sat\nunsat\n",
            "sat\n(error \"bad\")\n",
            "sat\n",
            "success\nsat\n(:reason-unknown \"\")\n",
            "unknown\n(:reason-unknown \"unfinished)\n",
            "sat\n(:reason-unknown \"\")\nsat\n",
        ]
        .iter()
        .enumerate()
        {
            let binary = fixture.program(
                &format!("protocol-{i}"),
                &format!("import sys\nsys.stdout.write({output:?})"),
            );
            let adapter = secure_new(binary, functional_limits()).unwrap();
            let q = query(&adapter, 100 + i as u64, "(assert true)");
            let receipt = adapter.solve(&q).unwrap();
            assert_eq!(
                receipt.outcome(),
                SolverOutcome::Error(SolverError::Protocol),
                "{output}"
            );
            assert_eq!(
                receipt.evaluate(&q),
                Ok(SemanticEntropyVerdict::SolverFailure {
                    error: SolverError::Protocol
                })
            );
        }
    }

    #[test]
    fn nonzero_exit_and_stderr_cannot_admit_sat() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        for (name, body, error) in [
            ("exit-failed", "import sys\nprint('sat')\nprint('(:reason-unknown \"\")')\nsys.exit(7)", SolverError::Execution),
            ("stderr", "import sys\nprint('sat')\nprint('(:reason-unknown \"\")')\nprint('failure', file=sys.stderr)", SolverError::Protocol),
        ] {
            let adapter = secure_new(fixture.program(name, body), functional_limits()).unwrap();
            let q = query(&adapter, 110, "(assert true)");
            let receipt = adapter.solve(&q).unwrap();
            assert_eq!(receipt.outcome(), SolverOutcome::Error(error));
            assert_eq!(receipt.evaluate(&q), Ok(SemanticEntropyVerdict::SolverFailure { error }));
        }
    }

    #[test]
    fn missing_executable_is_authentication_io_error() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        let adapter = secure_new(fixture.0.join("absent-z3"), SolverLimits::default()).unwrap();
        let q = query(&adapter, 120, "(assert true)");
        assert!(matches!(
            adapter.solve(&q),
            Err(
                babylon60_compiler::semantic_solver::SolveError::Authentication(
                    babylon60_compiler::semantic_solver::BinaryAuthError::Io
                )
            )
        ));
    }

    #[test]
    fn temporary_io_failure_preserves_transport_error() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        let file = fixture.0.join("not-a-directory");
        std::fs::write(&file, b"occupied").unwrap();
        let adapter = secure_temp(z3_path(), SolverLimits::default(), file).unwrap();
        let q = query(&adapter, 130, "(assert true)");
        let receipt = adapter.solve(&q).unwrap();
        assert_eq!(
            receipt.outcome(),
            SolverOutcome::Error(SolverError::Transport)
        );
        assert_eq!(
            receipt.evaluate(&q),
            Ok(SemanticEntropyVerdict::SolverFailure {
                error: SolverError::Transport
            })
        );
    }

    #[test]
    fn wall_timeout_kills_unresponsive_process_without_blocking_on_input_and_cleans_files() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        let temp_root = fixture.temp_root();
        let binary = fixture.program("sleeper", "import time\ntime.sleep(5)");
        let limits = SolverLimits {
            wall_timeout: Duration::from_millis(30),
            ..SolverLimits::default()
        };
        let adapter = secure_temp(binary, limits, temp_root.clone()).unwrap();
        let body = format!("; {}\n(assert true)", "x".repeat(60000));
        let q = query(&adapter, 140, &body);
        let start = Instant::now();
        let receipt = adapter.solve(&q).unwrap();
        assert_eq!(
            receipt.outcome(),
            SolverOutcome::Error(SolverError::Timeout)
        );
        assert!(
            start.elapsed() < Duration::from_secs(2),
            "bounded isolated regression, not a latency benchmark"
        );
        assert_eq!(std::fs::read_dir(temp_root).unwrap().count(), 0);
    }

    #[test]
    fn output_overflow_is_rejected_and_cleans_temporary_files() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        let temp_root = fixture.temp_root();
        let binary = fixture.program(
            "large-output",
            "import sys\nsys.stdout.write('sat\\n' + 'x' * 65536)",
        );
        let limits = SolverLimits {
            max_output_bytes: 128,
            ..functional_limits()
        };
        let adapter = secure_temp(binary, limits, temp_root.clone()).unwrap();
        let q = query(&adapter, 150, "(assert true)");
        let receipt = adapter.solve(&q).unwrap();
        assert_eq!(
            receipt.outcome(),
            SolverOutcome::Error(SolverError::Protocol)
        );
        assert!(receipt.stdout().len() <= 129);
        assert_eq!(std::fs::read_dir(temp_root).unwrap().count(), 0);
    }

    #[test]
    fn different_adapter_cannot_execute_foreign_policy_or_executable_query() {
        let _budget = process_budget();
        let fixture = Fixture::new();
        let a = adapter();
        let q = query(&a, 160, "(assert true)");
        let b = secure_new(
            fixture.program("fake-sat", "print('sat')\nprint('(:reason-unknown \"\")')"),
            SolverLimits::default(),
        )
        .unwrap();
        assert!(matches!(
            b.solve(&q),
            Err(babylon60_compiler::semantic_solver::SolveError::QueryMismatch)
        ));
    }

    #[test]
    fn invalid_configuration_and_oversize_input_are_rejected() {
        let _budget = process_budget();
        assert!(secure_new(Path::new("z3"), SolverLimits::default()).is_err());
        for limits in [
            SolverLimits {
                solver_timeout_ms: 0,
                ..SolverLimits::default()
            },
            SolverLimits {
                resource_limit: 0,
                ..SolverLimits::default()
            },
            SolverLimits {
                wall_timeout: Duration::ZERO,
                ..SolverLimits::default()
            },
            SolverLimits {
                max_input_bytes: 0,
                ..SolverLimits::default()
            },
            SolverLimits {
                max_output_bytes: 0,
                ..SolverLimits::default()
            },
        ] {
            assert!(secure_new(z3_path(), limits).is_err());
        }
        let adapter = secure_new(
            z3_path(),
            SolverLimits {
                max_input_bytes: 256,
                ..SolverLimits::default()
            },
        )
        .unwrap();
        assert!(adapter
            .query(170, 1, 1, &format!("; {}\n(assert true)", "x".repeat(256)))
            .is_err());
    }
}
