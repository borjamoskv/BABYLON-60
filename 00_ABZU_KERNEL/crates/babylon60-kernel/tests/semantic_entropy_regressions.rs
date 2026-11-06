//! Regression checks of bounded arithmetic and input rejection, not factual truth.
use babylon60_kernel::semantic_entropy::{
    BitmaskSemanticKernel, SemanticEntropyInputError, SemanticEntropyVerdict, SolverOutcome,
};

fn is_admitted(verdict: SemanticEntropyVerdict) -> bool {
    matches!(
        verdict,
        SemanticEntropyVerdict::VerifiedGenuine { .. }
            | SemanticEntropyVerdict::VerifiedPolysemy { .. }
    )
}

#[test]
fn eight_sample_clique_has_one_class() {
    assert_eq!(
        BitmaskSemanticKernel::evaluate(u64::MAX, 8, SolverOutcome::Sat),
        SemanticEntropyVerdict::VerifiedGenuine {
            h_sem_q16: 0,
            num_classes: 1
        }
    );
}

#[test]
fn out_of_range_sample_counts_are_not_admitted() {
    for n in [0, 9, usize::MAX] {
        assert!(
            !is_admitted(BitmaskSemanticKernel::evaluate(0, n, SolverOutcome::Sat)),
            "n={n}"
        );
    }
}

#[test]
fn a_non_reflexive_relation_is_not_admitted() {
    assert!(!is_admitted(BitmaskSemanticKernel::evaluate(
        0,
        3,
        SolverOutcome::Sat
    )));
}

#[test]
fn an_asymmetric_reflexive_relation_is_not_admitted() {
    // Rows 011,010,100 include all diagonal cells, but 0~1 and not 1~0.
    assert!(!is_admitted(BitmaskSemanticKernel::evaluate(
        0x0004_0203,
        3,
        SolverOutcome::Sat
    )));
}

#[test]
fn a_symmetric_nontransitive_relation_is_not_admitted() {
    // Rows 011,111,110 would previously count overlapping sizes 2+2 for n=3.
    assert!(!is_admitted(BitmaskSemanticKernel::evaluate(
        0x0006_0703,
        3,
        SolverOutcome::Sat
    )));
}

#[test]
fn a_column_outside_the_declared_domain_is_not_admitted() {
    // Identity n=3 with extra cell (0,3).
    assert!(!is_admitted(BitmaskSemanticKernel::evaluate(
        0x0004_0209,
        3,
        SolverOutcome::Sat
    )));
}

#[test]
fn a_row_outside_the_declared_domain_is_not_admitted() {
    // Identity n=3 with extra cell (3,0).
    assert!(!is_admitted(BitmaskSemanticKernel::evaluate(
        0x0104_0201,
        3,
        SolverOutcome::Sat
    )));
}

fn assert_invalid(matrix: u64, n: usize, error: SemanticEntropyInputError) {
    assert_eq!(
        BitmaskSemanticKernel::compute_quotient_entropy(matrix, n),
        Err(error)
    );
    for outcome in [SolverOutcome::Unsat, SolverOutcome::Sat] {
        assert_eq!(
            BitmaskSemanticKernel::evaluate(matrix, n, outcome),
            SemanticEntropyVerdict::InvalidInput { error }
        );
    }
}

#[test]
fn invalid_inputs_have_typed_errors_under_either_conclusive_outcome() {
    for n in [0, 9, usize::MAX] {
        assert_invalid(0, n, SemanticEntropyInputError::SampleCountOutOfRange);
    }
    for matrix in [0x0004_0209, 0x0104_0201] {
        assert_invalid(matrix, 3, SemanticEntropyInputError::BitsOutsideDomain);
    }
    assert_invalid(0, 3, SemanticEntropyInputError::NotReflexive);
    assert_invalid(0x0004_0203, 3, SemanticEntropyInputError::NotSymmetric);
    assert_invalid(0x0006_0703, 3, SemanticEntropyInputError::NotTransitive);
}

fn matrix_from_labels(labels: &[usize]) -> u64 {
    let mut matrix = 0;
    for (i, left) in labels.iter().enumerate() {
        for (j, right) in labels.iter().enumerate() {
            if left == right {
                matrix |= 1u64 << (i * 8 + j);
            }
        }
    }
    matrix
}

// Independent reference: derive class sizes from labels and compute each rounded
// Shannon contribution in floating point in this test executable, not via the LUT.
fn reference_from_labels(labels: &[usize]) -> (u32, u8) {
    let mut counts = [0usize; 8];
    for &label in labels {
        counts[label] += 1;
    }
    let n = labels.len() as f64;
    let mut entropy = 0u32;
    let mut classes = 0u8;
    for count in counts.into_iter().filter(|count| *count != 0) {
        let probability = count as f64 / n;
        entropy += (-probability * probability.log2() * 65536.0).round() as u32;
        classes += 1;
    }
    (entropy, classes)
}

#[test]
fn exact_endpoint_and_existing_nominal_values_are_preserved() {
    for (labels, expected) in [
        (&[0][..], (0, 1)),
        (&[0, 0, 0, 0, 0, 0, 0, 0][..], (0, 1)),
        (&[0, 1, 2, 3, 4, 5, 6, 7][..], (196608, 8)),
        (&[0, 0, 1, 1][..], (65536, 2)),
        (&[0, 0, 0, 1, 1][..], (63633, 2)),
    ] {
        assert_eq!(
            BitmaskSemanticKernel::compute_quotient_entropy(
                matrix_from_labels(labels),
                labels.len()
            ),
            Ok(expected)
        );
    }
}

fn check_partition(labels: &[usize]) {
    let expected = reference_from_labels(labels);
    let n = labels.len();
    assert!(expected.0 <= 196608);
    assert_eq!(
        BitmaskSemanticKernel::compute_quotient_entropy(matrix_from_labels(labels), n),
        Ok(expected),
        "partition: {labels:?}"
    );
    for shift in 0..n {
        let permuted: Vec<_> = (0..n).map(|i| labels[(i + shift) % n]).collect();
        assert_eq!(
            BitmaskSemanticKernel::compute_quotient_entropy(matrix_from_labels(&permuted), n),
            Ok(expected),
            "rotation {shift} of {labels:?}"
        );
    }
    let reversed: Vec<_> = labels.iter().rev().copied().collect();
    let relabelled: Vec<_> = labels.iter().map(|label| 7 - label).collect();
    for permuted in [reversed, relabelled] {
        assert_eq!(
            BitmaskSemanticKernel::compute_quotient_entropy(matrix_from_labels(&permuted), n),
            Ok(expected)
        );
    }
}

fn visit_partitions(labels: &mut [usize; 8], n: usize, position: usize, largest: usize) -> usize {
    if position == n {
        check_partition(&labels[..n]);
        return 1;
    }
    let mut count = 0;
    for label in 0..=largest + 1 {
        labels[position] = label;
        count += visit_partitions(labels, n, position + 1, largest.max(label));
    }
    count
}

#[test]
fn all_5295_partitions_match_independent_arithmetic_and_permutations() {
    let mut total = 0;
    for n in 1..=8 {
        total += visit_partitions(&mut [0; 8], n, 1, 0);
    }
    assert_eq!(total, 5295);
}

fn is_equivalence_by_definition(matrix: u64, n: usize) -> bool {
    let related = |i: usize, j: usize| matrix & (1u64 << (8 * i + j)) != 0;
    for i in 0..n {
        if !related(i, i) {
            return false;
        }
        for j in 0..n {
            if related(i, j) != related(j, i) {
                return false;
            }
            for k in 0..n {
                if related(i, j) && related(j, k) && !related(i, k) {
                    return false;
                }
            }
        }
    }
    true
}

#[test]
fn all_n4_relations_match_an_independent_equivalence_predicate() {
    let mut valid = 0;
    for compact in 0..65536u64 {
        let mut matrix = 0;
        for i in 0..4 {
            for j in 0..4 {
                if compact & (1u64 << (i * 4 + j)) != 0 {
                    matrix |= 1u64 << (i * 8 + j);
                }
            }
        }
        let expected = is_equivalence_by_definition(matrix, 4);
        let actual = BitmaskSemanticKernel::compute_quotient_entropy(matrix, 4).is_ok();
        assert_eq!(actual, expected, "compact relation {compact:04x}");
        if actual {
            valid += 1;
        }
    }
    assert_eq!(valid, 15);
}
