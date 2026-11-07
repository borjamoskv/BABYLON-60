// Bounded integer entropy of a supplied equivalence relation, compatible with no_std.
// Ring-0 is a project category; this module does not prove factual truth or execute effects.

pub const ERR_CONFABULATION: u32 = 0xDEAD_6060;
pub const ERR_INCORRECT_BELIEF: u32 = 0xDEAD_6061;
pub const STATUS_VERIFIED: u32 = 0x0000_0001;

/// Configured Q16 threshold: 55706 / 65536 is approximately 0.85 bits.
pub const TAU_SEM_Q16: u32 = 55706;

/// Rounded Q16 contributions for -(c/n) * log2(c/n), for 1 <= c <= n <= 8.
/// This approximates real-valued entropy; integer arithmetic does not imply zero energy use.
const ENTROPY_LUT_Q16: [[u32; 9]; 9] = [
    /* n=0 */ [0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n=1 */ [0, 0, 0, 0, 0, 0, 0, 0, 0],
    /* n=2 */ [0, 32768, 0, 0, 0, 0, 0, 0, 0],
    /* n=3 */ [0, 34624, 25557, 0, 0, 0, 0, 0, 0],
    /* n=4 */ [0, 32768, 32768, 20400, 0, 0, 0, 0, 0],
    /* n=5 */ [0, 30434, 34654, 28979, 16878, 0, 0, 0, 0],
    /* n=6 */ [0, 28235, 34624, 32768, 25557, 14365, 0, 0, 0],
    /* n=7 */ [0, 26283, 33842, 34333, 30235, 22724, 12493, 0, 0],
    /* n=8 */ [0, 24576, 32768, 34776, 32768, 27774, 20400, 11047, 0],
];

/// Caller-reported solver failures. This module does not invoke or authenticate a solver.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SolverError {
    Timeout,
    Transport,
    Protocol,
    Execution,
}

/// Explicit outcome of a caller-supplied constraint check.
/// SAT concerns the supplied constraints; it does not establish external factual truth.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SolverOutcome {
    Sat,
    Unsat,
    Unknown,
    Error(SolverError),
}

/// Standard BLAKE3 of the exact executable bytes; callers provide the trusted pin.
/// This does not establish vendor identity or authenticate dynamic dependencies.
pub fn solver_binary_digest(bytes: &[u8]) -> [u8; 32] {
    *blake3::hash(bytes).as_bytes()
}

/// Framed local replay-record checksum, not a signature or rollback protection.
pub fn solver_replay_record_digest(bytes: &[u8]) -> [u8; 32] {
    let mut hash = blake3::Hasher::new();
    hash.update(b"B60-Z3-REPLAY-RECORD-v1\0");
    hash.update(&(bytes.len() as u64).to_le_bytes());
    hash.update(bytes);
    *hash.finalize().as_bytes()
}

/// Local query identity, not solver authentication or a proof of satisfiability.
/// Integers are little-endian u64; both variable byte fields are length-prefixed.
pub fn solver_query_digest(
    request_id: u64,
    adj_matrix: u64,
    n: u8,
    policy: &[u8],
    smt2: &[u8],
) -> [u8; 32] {
    let mut hash = blake3::Hasher::new();
    hash.update(b"B60-SEMANTIC-SOLVER-QUERY-v1\0");
    for value in [request_id, adj_matrix, u64::from(n)] {
        hash.update(&value.to_le_bytes());
    }
    for bytes in [policy, smt2] {
        hash.update(&(bytes.len() as u64).to_le_bytes());
        hash.update(bytes);
    }
    *hash.finalize().as_bytes()
}

/// Invalid input is distinct from a valid zero-entropy partition or a solver outcome.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticEntropyInputError {
    SampleCountOutOfRange,
    BitsOutsideDomain,
    NotReflexive,
    NotSymmetric,
    NotTransitive,
}

/// Historical variant names classify entropy and a supplied outcome, not factual truth.
/// Returning a variant does not itself abort execution or commit persistent state.
#[derive(Debug, Clone, Copy, PartialEq, Eq)]
pub enum SemanticEntropyVerdict {
    InvalidInput { error: SemanticEntropyInputError },
    SolverUnknown,
    SolverFailure { error: SolverError },
    VerifiedGenuine { h_sem_q16: u32, num_classes: u8 },
    VerifiedPolysemy { h_sem_q16: u32, num_classes: u8 },
    ApoptosisConfabulation { h_sem_q16: u32, code: u32 },
    ApoptosisIncorrectBelief { h_sem_q16: u32, code: u32 },
}

/// Integer Q16 entropy for at most eight samples with a validated equivalence relation.
pub struct BitmaskSemanticKernel;

impl BitmaskSemanticKernel {
    /// The cell (i,j) occupies bit 8*i+j. Only the declared n-by-n submatrix may be set.
    /// Requires 1 <= n <= 8 and reflexivity, symmetry and transitivity; returns an
    /// explicit error otherwise. No equivalence closure is inferred from arbitrary NLI data.
    /// A successful result is (rounded entropy in Q16, number of nonempty classes).
    #[inline(always)]
    pub fn compute_quotient_entropy(
        adj_matrix: u64,
        n: usize,
    ) -> Result<(u32, u8), SemanticEntropyInputError> {
        if n == 0 || n > 8 {
            return Err(SemanticEntropyInputError::SampleCountOutOfRange);
        }

        // The wider shift supports n=8 without shifting a u8 by its full width.
        let row_mask = ((1u16 << n) - 1) as u8;
        let mut domain_bits = 0u64;
        let mut rows = [0u8; 8];
        for (i, row) in rows.iter_mut().enumerate().take(n) {
            domain_bits |= u64::from(row_mask) << (i * 8);
            *row = (adj_matrix >> (i * 8)) as u8;
        }
        if adj_matrix & !domain_bits != 0 {
            return Err(SemanticEntropyInputError::BitsOutsideDomain);
        }
        for (i, row) in rows.iter().enumerate().take(n) {
            if row & (1u8 << i) == 0 {
                return Err(SemanticEntropyInputError::NotReflexive);
            }
        }
        for i in 0..n {
            for j in 0..n {
                if ((rows[i] >> j) & 1) != ((rows[j] >> i) & 1) {
                    return Err(SemanticEntropyInputError::NotSymmetric);
                }
            }
        }
        for i in 0..n {
            for j in 0..n {
                // In a reflexive symmetric relation, related rows are equal exactly
                // when each connected class is complete (the transitivity condition).
                if rows[i] & (1u8 << j) != 0 && rows[i] != rows[j] {
                    return Err(SemanticEntropyInputError::NotTransitive);
                }
            }
        }

        let mut visited = 0u8;
        let mut num_classes = 0u8;
        let mut total_h_q16 = 0u32;
        for i in 0..n {
            let mask_i = 1u8 << i;
            if (visited & mask_i) != 0 {
                continue;
            }
            let class_members = rows[i];
            let size = class_members.count_ones() as usize;
            visited |= class_members;
            num_classes += 1;
            total_h_q16 += ENTROPY_LUT_Q16[n][size];
        }
        Ok((total_h_q16, num_classes))
    }

    /// Validate the partition first, then classify it using the caller-supplied outcome.
    /// UNKNOWN and errors never produce a `Verified*` variant. No solver is invoked,
    /// and the supplied outcome does not authenticate an external fact or cause an effect.
    ///
    /// A boolean discards UNKNOWN/errors and is intentionally not accepted.
    /// ```compile_fail
    /// use babylon60_kernel::semantic_entropy::BitmaskSemanticKernel;
    /// let _ = BitmaskSemanticKernel::evaluate(1, 1, true);
    /// ```
    #[inline(always)]
    pub fn evaluate(adj_matrix: u64, n: usize, outcome: SolverOutcome) -> SemanticEntropyVerdict {
        let (h_sem_q16, k) = match Self::compute_quotient_entropy(adj_matrix, n) {
            Ok(result) => result,
            Err(error) => return SemanticEntropyVerdict::InvalidInput { error },
        };

        match outcome {
            SolverOutcome::Unknown => SemanticEntropyVerdict::SolverUnknown,
            SolverOutcome::Error(error) => SemanticEntropyVerdict::SolverFailure { error },
            SolverOutcome::Sat if h_sem_q16 > TAU_SEM_Q16 => {
                SemanticEntropyVerdict::VerifiedPolysemy {
                    h_sem_q16,
                    num_classes: k,
                }
            }
            SolverOutcome::Sat => SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16,
                num_classes: k,
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
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_genuine_knowledge_quadrant1() {
        // Clique completo 5x5 (todas las muestras equivalentes)
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (0b0001_1111u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, SolverOutcome::Sat);
        assert_eq!(
            verdict,
            SemanticEntropyVerdict::VerifiedGenuine {
                h_sem_q16: 0,
                num_classes: 1
            }
        );
    }

    #[test]
    fn test_confabulation_quadrant2() {
        // Identidad 5x5 (cinco clases distintas, K=5), con UNSAT suministrado.
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (1u64 << i) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, SolverOutcome::Unsat);
        match verdict {
            SemanticEntropyVerdict::ApoptosisConfabulation { h_sem_q16, code } => {
                assert!(h_sem_q16 > TAU_SEM_Q16);
                assert_eq!(code, ERR_CONFABULATION);
            }
            _ => panic!("Se esperaba la variante ApoptosisConfabulation"),
        }
    }

    #[test]
    fn test_incorrect_belief_quadrant3() {
        // Clique completo 5x5 (H_sem = 0), con UNSAT suministrado.
        let mut adj = 0u64;
        for i in 0..5 {
            adj |= (0b0001_1111u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, SolverOutcome::Unsat);
        assert_eq!(
            verdict,
            SemanticEntropyVerdict::ApoptosisIncorrectBelief {
                h_sem_q16: 0,
                code: ERR_INCORRECT_BELIEF
            }
        );
    }

    #[test]
    fn test_polysemy_quadrant4() {
        // Partición en 2 clases (3 en C1, 2 en C2), con SAT suministrado.
        let mut adj = 0u64;
        for i in 0..3 {
            adj |= (0b0000_0111u64) << (i * 8);
        }
        for i in 3..5 {
            adj |= (0b0001_1000u64) << (i * 8);
        }
        let verdict = BitmaskSemanticKernel::evaluate(adj, 5, SolverOutcome::Sat);
        match verdict {
            SemanticEntropyVerdict::VerifiedPolysemy {
                h_sem_q16,
                num_classes,
            } => {
                assert_eq!(num_classes, 2);
                assert_eq!(h_sem_q16, 63633); // 0.9709 bits en Q16
            }
            _ => panic!("Se esperaba la variante VerifiedPolysemy"),
        }
    }
}
