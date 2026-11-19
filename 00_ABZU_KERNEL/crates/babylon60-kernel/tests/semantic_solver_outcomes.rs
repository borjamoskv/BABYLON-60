//! Synthetic API/partition checks; no solver, factual oracle or protected effect runs here.
use babylon60_kernel::semantic_entropy::{
    BitmaskSemanticKernel, SemanticEntropyInputError, SemanticEntropyVerdict, SolverError,
    SolverOutcome, ERR_CONFABULATION, ERR_INCORRECT_BELIEF, TAU_SEM_Q16,
};

const OUTCOMES: [SolverOutcome; 7] = [
    SolverOutcome::Sat,
    SolverOutcome::Unsat,
    SolverOutcome::Unknown,
    SolverOutcome::Error(SolverError::Timeout),
    SolverOutcome::Error(SolverError::Transport),
    SolverOutcome::Error(SolverError::Protocol),
    SolverOutcome::Error(SolverError::Execution),
];

fn matrix_from_labels(labels: &[usize]) -> u64 {
    let mut matrix = 0;
    for (i, left) in labels.iter().enumerate() {
        for (j, right) in labels.iter().enumerate() {
            if left == right {
                matrix |= 1u64 << (8 * i + j);
            }
        }
    }
    matrix
}

// Independent arithmetic oracle: use label frequencies and floating-point Shannon
// contributions in this test executable, without reading the production Q16 LUT.
fn summary_from_labels(labels: &[usize]) -> (u32, u8) {
    let mut counts = [0usize; 8];
    for &label in labels {
        counts[label] += 1;
    }
    let entropy = counts
        .iter()
        .filter(|&&count| count != 0)
        .map(|&count| {
            let p = count as f64 / labels.len() as f64;
            (-p * p.log2() * 65536.0).round() as u32
        })
        .sum();
    (
        entropy,
        counts.iter().filter(|&&count| count != 0).count() as u8,
    )
}

fn check_outcomes(labels: &[usize], summary: (u32, u8)) {
    let matrix = matrix_from_labels(labels);
    let (h_sem_q16, num_classes) = summary;
    for outcome in OUTCOMES {
        let expected = match outcome {
            SolverOutcome::Sat if h_sem_q16 > TAU_SEM_Q16 => {
                SemanticEntropyVerdict::VerifiedPolysemy {
                    h_sem_q16,
                    num_classes,
                }
            }
            SolverOutcome::Sat => SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16,
                num_classes,
            },
            SolverOutcome::Unsat if h_sem_q16 > TAU_SEM_Q16 => {
                SemanticEntropyVerdict::ApoptosisConfabulation {
                    h_sem_q16,
                    code: ERR_CONFABULATION,
                }
            }
            SolverOutcome::Unsat => SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                h_sem_q16,
                code: ERR_INCORRECT_BELIEF,
            },
            SolverOutcome::Unknown => SemanticEntropyVerdict::SolverUnknown,
            SolverOutcome::Error(error) => SemanticEntropyVerdict::SolverFailure { error },
        };
        assert_eq!(
            BitmaskSemanticKernel::evaluate(matrix, labels.len(), outcome),
            expected,
            "labels={labels:?}, outcome={outcome:?}"
        );
    }
}

#[test]
fn conclusive_quadrants_keep_their_payloads() {
    // Golden values exercise all four historical variants with explicit SAT/UNSAT.
    check_outcomes(&[0, 0, 0, 0, 0], (0, 1));
    check_outcomes(&[0, 0, 0, 1, 1], (63633, 2));
    check_outcomes(&[0, 1, 2, 3, 4], (152170, 5));
}

fn visit_partitions(labels: &mut [usize; 8], n: usize, pos: usize, largest: usize) -> usize {
    if pos == n {
        let labels = &labels[..n];
        check_outcomes(labels, summary_from_labels(labels));
        return 1;
    }
    let mut count = 0;
    for label in 0..=largest + 1 {
        labels[pos] = label;
        count += visit_partitions(labels, n, pos + 1, largest.max(label));
    }
    count
}

#[test]
fn all_5295_partitions_cover_all_seven_solver_outcomes() {
    let mut partitions = 0;
    for n in 1..=8 {
        partitions += visit_partitions(&mut [0; 8], n, 1, 0);
    }
    assert_eq!(partitions, 5295);
    assert_eq!(partitions * OUTCOMES.len(), 37065);
}

#[test]
fn invalid_input_has_precedence_over_every_solver_outcome() {
    use SemanticEntropyInputError::*;
    let cases = [
        (0, 0, SampleCountOutOfRange),
        (u64::MAX, 0, SampleCountOutOfRange),
        (0, 9, SampleCountOutOfRange),
        (u64::MAX, 9, SampleCountOutOfRange),
        (0, usize::MAX, SampleCountOutOfRange),
        (u64::MAX, usize::MAX, SampleCountOutOfRange),
        (0x0004_0209, 3, BitsOutsideDomain),
        (0x0104_0201, 3, BitsOutsideDomain),
        (0x8, 3, BitsOutsideDomain), // Also lacks the diagonal.
        (0, 3, NotReflexive),
        (0x0004_0203, 3, NotSymmetric),
        (0x0006_0703, 3, NotTransitive),
    ];
    for (matrix, n, error) in cases {
        for outcome in OUTCOMES {
            assert_eq!(
                BitmaskSemanticKernel::evaluate(matrix, n, outcome),
                SemanticEntropyVerdict::InvalidInput { error },
                "matrix={matrix:#x}, n={n}, outcome={outcome:?}"
            );
        }
    }
}

#[test]
fn zero_entropy_and_eight_sample_maximum_do_not_override_solver_rejection() {
    check_outcomes(&[0], (0, 1));
    check_outcomes(&[0; 8], (0, 1));
    check_outcomes(&[0, 1, 2, 3, 4, 5, 6, 7], (196608, 8));
}

#[test]
fn mixed_calls_are_deterministic_without_retaining_previous_admission() {
    let clique = matrix_from_labels(&[0; 8]);
    let identity = matrix_from_labels(&[0, 1, 2, 3, 4, 5, 6, 7]);
    for _ in 0..256 {
        // A preceding SAT must not admit an inconclusive result, including after errors.
        assert_eq!(
            BitmaskSemanticKernel::evaluate(identity, 8, SolverOutcome::Sat),
            SemanticEntropyVerdict::VerifiedPolysemy {
                h_sem_q16: 196608,
                num_classes: 8
            }
        );
        for outcome in OUTCOMES.into_iter().rev() {
            assert_eq!(
                BitmaskSemanticKernel::evaluate(0, 0, outcome),
                SemanticEntropyVerdict::InvalidInput {
                    error: SemanticEntropyInputError::SampleCountOutOfRange,
                }
            );
        }
        check_outcomes(&[0; 8], (0, 1));
        assert_eq!(
            BitmaskSemanticKernel::evaluate(clique, 8, SolverOutcome::Unknown),
            SemanticEntropyVerdict::SolverUnknown
        );
        check_outcomes(&[0, 1, 2, 3, 4, 5, 6, 7], (196608, 8));
    }
}
