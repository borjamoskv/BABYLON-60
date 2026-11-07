//! FL-019: exact verification of bounded integer affine transformations in 3D.
//!
//! Two independently implemented checks must pass. This verifies the declared
//! affine calculation, not the scientific meaning of its inputs or outputs.
//! Replay state belongs to this verifier instance and is not crash persistent.

use crate::larsa::{
    CompositeRejectReason, CompositeSafetyDecision, CompositeSafetyGate, EvaluatorAttestation,
    WitnessReplayLedger,
};
use serde::{Deserialize, Serialize};
use std::fmt;

/// Version of the checker, canonical digest format, and bounded domain.
pub const CHECKER_VERSION: &str = "FL-019-AFFINE-I3-v1";
/// Maximum UTF-8 request size accepted by the JSON boundary.
pub const MAX_REQUEST_BYTES: usize = 65_536;
const MAX_POINTS: usize = 256;
const INPUT_BOUND: i64 = 10_000;
const OUTPUT_BOUND: i64 = 1_000_000_000;

/// Proposed affine result. Evaluator outcomes cannot be supplied by the caller.
#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryRequest {
    /// Source points; the first four must be affinely independent.
    pub points: Vec<[i64; 3]>,
    /// Three rows of an affine matrix, including the translation column.
    pub transform: [[i64; 4]; 3],
    /// Candidate transformed points in the same order.
    pub output: Vec<[i64; 3]>,
    /// BLAKE3 identity of the caller's declared workflow context, as 64 hex digits.
    pub context_digest_b3: String,
    /// Logical policy revision, without wall-clock dependence.
    pub policy_epoch: u64,
    /// Target to which this verification belongs.
    pub target_id: u64,
    /// Caller-chosen logical nonce bound into all joint evidence.
    pub nonce: u64,
}

/// Internally generated verification result, scoped to this exact request.
#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct GeometryReport {
    /// Whether the composite gate admitted both checks and consumed the witness.
    pub accepted: bool,
    /// Result of direct coordinate verification.
    pub coordinate_check: bool,
    /// Result of independent anchor, barycentric, and oriented-volume checks.
    pub oriented_volume_check: bool,
    /// Canonical BLAKE3 identity of inputs, transform, context, and logical scope.
    pub input_digest_b3: String,
    /// Canonical BLAKE3 identity of the candidate output.
    pub artifact_digest_b3: String,
    /// Composite evidence digest, present only after admission.
    pub joint_evidence_digest_b3: Option<String>,
    /// Checker and canonical-format version.
    pub checker_version: String,
    /// Stable rejection reason; absent on acceptance.
    pub reason: Option<String>,
}

/// Malformed requests are errors; semantically wrong results are rejected reports.
#[derive(Debug)]
pub enum GeometryError {
    /// JSON exceeds the bounded input surface.
    RequestTooLarge,
    /// JSON could not be decoded into the strict request schema.
    MalformedJson(String),
    /// A count, coordinate, or context encoding is outside the declared domain.
    InvalidBounds(&'static str),
    /// The four input anchors do not define a tetrahedron.
    DegenerateInput,
    /// The declared affine linear map is singular.
    SingularTransform,
    /// Checked exact arithmetic exceeded its representation.
    ArithmeticOverflow,
}

impl fmt::Display for GeometryError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::RequestTooLarge => f.write_str("geometry request exceeds 65536 bytes"),
            Self::MalformedJson(reason) => write!(f, "invalid geometry JSON: {reason}"),
            Self::InvalidBounds(reason) => write!(f, "geometry domain violation: {reason}"),
            Self::DegenerateInput => f.write_str("first four input points are coplanar"),
            Self::SingularTransform => f.write_str("declared affine transform is singular"),
            Self::ArithmeticOverflow => f.write_str("exact geometry arithmetic overflow"),
        }
    }
}

impl std::error::Error for GeometryError {}

/// Stateful verifier; a fresh instance does not inherit prior replay evidence.
pub struct GeometryVerifier {
    replay_ledger: WitnessReplayLedger,
}

impl Default for GeometryVerifier {
    fn default() -> Self {
        Self::new()
    }
}

impl GeometryVerifier {
    /// Create an isolated verifier with an empty in-memory replay ledger.
    pub fn new() -> Self {
        Self {
            replay_ledger: WitnessReplayLedger::new(),
        }
    }

    /// Decode and verify a bounded, strict JSON request.
    pub fn verify_json(&mut self, request_json: &str) -> Result<GeometryReport, GeometryError> {
        if request_json.len() > MAX_REQUEST_BYTES {
            return Err(GeometryError::RequestTooLarge);
        }
        let request = serde_json::from_str(request_json)
            .map_err(|error| GeometryError::MalformedJson(error.to_string()))?;
        self.verify(request)
    }

    /// Evaluate both independent checks and bind their evidence with the gate.
    pub fn verify(&mut self, request: GeometryRequest) -> Result<GeometryReport, GeometryError> {
        let context = validate_request(&request)?;
        // Evaluate separately: a failed first check must never skip the second.
        let coordinate_check = check_coordinates(&request);
        let oriented_volume_check = check_oriented_geometry(&request)?;
        let input_hash = input_digest(&request, &context);
        let artifact_hash = artifact_digest(&request.output);
        let policy_hash = policy_digest(&request, &context);
        let attestations: Vec<_> = [coordinate_check, oriented_volume_check]
            .into_iter()
            .enumerate()
            .map(|(check_id, passed)| {
                EvaluatorAttestation::new_canonical(
                    check_id as u8,
                    passed,
                    input_hash,
                    artifact_hash,
                    policy_hash,
                    request.policy_epoch,
                    request.target_id,
                    request.nonce,
                )
            })
            .collect();
        // There is no caller-controlled heuristic vote: both bits are mandatory.
        let gate = CompositeSafetyGate::new(
            0b11,
            1,
            input_hash,
            artifact_hash,
            policy_hash,
            request.policy_epoch,
            request.target_id,
            request.nonce,
        );
        let (accepted, joint, reason) =
            match gate.evaluate_admission(&attestations, 1, &mut self.replay_ledger) {
                CompositeSafetyDecision::Accepted {
                    joint_evidence_digest,
                    ..
                } => (true, Some(hex_digest(&joint_evidence_digest)), None),
                CompositeSafetyDecision::Rejected(reason) => {
                    let reason = match reason {
                        CompositeRejectReason::CriticalCheckFailed { check_id: 0 } => {
                            "coordinate_check_failed"
                        }
                        CompositeRejectReason::CriticalCheckFailed { check_id: 1 } => {
                            "oriented_volume_check_failed"
                        }
                        CompositeRejectReason::ReplayDetected => "replay_detected",
                        _ => "composite_gate_rejected",
                    };
                    (false, None, Some(reason.to_owned()))
                }
            };
        Ok(GeometryReport {
            accepted,
            coordinate_check,
            oriented_volume_check,
            input_digest_b3: hex_digest(&input_hash),
            artifact_digest_b3: hex_digest(&artifact_hash),
            joint_evidence_digest_b3: joint,
            checker_version: CHECKER_VERSION.to_owned(),
            reason,
        })
    }
}

fn validate_request(request: &GeometryRequest) -> Result<[u8; 32], GeometryError> {
    if !(4..=MAX_POINTS).contains(&request.points.len()) || request.output.len() > MAX_POINTS {
        return Err(GeometryError::InvalidBounds(
            "expected 4..256 input points and at most 256 outputs",
        ));
    }
    if request
        .points
        .iter()
        .flatten()
        .any(|v| !(-INPUT_BOUND..=INPUT_BOUND).contains(v))
        || request
            .transform
            .iter()
            .flatten()
            .any(|v| !(-INPUT_BOUND..=INPUT_BOUND).contains(v))
    {
        return Err(GeometryError::InvalidBounds(
            "input and coefficient magnitude exceeds 10000",
        ));
    }
    if request
        .output
        .iter()
        .flatten()
        .any(|v| !(-OUTPUT_BOUND..=OUTPUT_BOUND).contains(v))
    {
        return Err(GeometryError::InvalidBounds(
            "output magnitude exceeds 1000000000",
        ));
    }
    let context = decode_context(&request.context_digest_b3)?;
    if determinant4(&anchors(&request.points))? == 0 {
        return Err(GeometryError::DegenerateInput);
    }
    let linear = request
        .transform
        .map(|row| [i128::from(row[0]), i128::from(row[1]), i128::from(row[2])]);
    if determinant3(&linear)? == 0 {
        return Err(GeometryError::SingularTransform);
    }
    Ok(context)
}

fn decode_context(value: &str) -> Result<[u8; 32], GeometryError> {
    if value.len() != 64 || !value.bytes().all(|b| b.is_ascii_hexdigit()) {
        return Err(GeometryError::InvalidBounds(
            "context digest must contain 64 hexadecimal digits",
        ));
    }
    let mut result = [0u8; 32];
    for (slot, pair) in result.iter_mut().zip(value.as_bytes().chunks_exact(2)) {
        let digit = |b: u8| {
            if b <= b'9' {
                b - b'0'
            } else {
                b.to_ascii_lowercase() - b'a' + 10
            }
        };
        *slot = digit(pair[0]) * 16 + digit(pair[1]);
    }
    Ok(result)
}

// Checker 1: direct affine coordinate equations. Validated operands bound each
// accumulator by 300010000, strictly inside i128 (and the output domain).
fn check_coordinates(request: &GeometryRequest) -> bool {
    request.points.len() == request.output.len()
        && request
            .points
            .iter()
            .zip(&request.output)
            .all(|(point, output)| {
                request.transform.iter().zip(output).all(|(row, observed)| {
                    let expected = i128::from(row[3])
                        + row[..3]
                            .iter()
                            .zip(point)
                            .map(|(a, x)| i128::from(*a) * i128::from(*x))
                            .sum::<i128>();
                    expected == i128::from(*observed)
                })
            })
}

// Checker 2: Cramer's rule on homogeneous anchors, independently of checker 1.
// Anchor equations recover every declared affine coefficient. Barycentric
// determinants then verify every additional output, and signed volume checks
// the declared orientation (including legitimate reflections). Every arithmetic
// operation below is checked; bounded requests keep intermediates within i128.
fn check_oriented_geometry(request: &GeometryRequest) -> Result<bool, GeometryError> {
    if request.points.len() != request.output.len() {
        return Ok(false);
    }
    let source = anchors(&request.points);
    let result = anchors(&request.output);
    let source_volume = determinant4(&source)?;
    let linear = request
        .transform
        .map(|row| [i128::from(row[0]), i128::from(row[1]), i128::from(row[2])]);
    let expected_volume = determinant3(&linear)?
        .checked_mul(source_volume)
        .ok_or(GeometryError::ArithmeticOverflow)?;
    let mut valid = determinant4(&result)? == expected_volume;
    for (axis, coefficients) in request.transform.iter().enumerate() {
        for (column, coefficient) in coefficients.iter().enumerate() {
            let mut replaced = source;
            for row in 0..4 {
                replaced[row][column] = result[row][axis];
            }
            let expected = i128::from(*coefficient)
                .checked_mul(source_volume)
                .ok_or(GeometryError::ArithmeticOverflow)?;
            valid &= determinant4(&replaced)? == expected;
        }
    }
    for (point, output) in request.points.iter().zip(&request.output) {
        let mut weights = [0i128; 4];
        for anchor in 0..4 {
            let mut replaced = source;
            replaced[anchor] = homogeneous(point);
            weights[anchor] = determinant4(&replaced)?;
        }
        for axis in 0..3 {
            let mut observed = 0i128;
            for anchor in 0..4 {
                let term = weights[anchor]
                    .checked_mul(result[anchor][axis])
                    .ok_or(GeometryError::ArithmeticOverflow)?;
                observed = observed
                    .checked_add(term)
                    .ok_or(GeometryError::ArithmeticOverflow)?;
            }
            let expected = source_volume
                .checked_mul(i128::from(output[axis]))
                .ok_or(GeometryError::ArithmeticOverflow)?;
            valid &= observed == expected;
        }
    }
    Ok(valid)
}

fn homogeneous(point: &[i64; 3]) -> [i128; 4] {
    [
        i128::from(point[0]),
        i128::from(point[1]),
        i128::from(point[2]),
        1,
    ]
}

fn anchors(points: &[[i64; 3]]) -> [[i128; 4]; 4] {
    [
        homogeneous(&points[0]),
        homogeneous(&points[1]),
        homogeneous(&points[2]),
        homogeneous(&points[3]),
    ]
}

fn determinant3(matrix: &[[i128; 3]; 3]) -> Result<i128, GeometryError> {
    let mut total = 0i128;
    for (permutation, positive) in [
        ([0, 1, 2], true),
        ([1, 2, 0], true),
        ([2, 0, 1], true),
        ([2, 1, 0], false),
        ([1, 0, 2], false),
        ([0, 2, 1], false),
    ] {
        let product = matrix[0][permutation[0]]
            .checked_mul(matrix[1][permutation[1]])
            .and_then(|v| v.checked_mul(matrix[2][permutation[2]]))
            .ok_or(GeometryError::ArithmeticOverflow)?;
        total = if positive {
            total.checked_add(product)
        } else {
            total.checked_sub(product)
        }
        .ok_or(GeometryError::ArithmeticOverflow)?;
    }
    Ok(total)
}

fn determinant4(matrix: &[[i128; 4]; 4]) -> Result<i128, GeometryError> {
    let mut total = 0i128;
    for column in 0..4 {
        let mut minor = [[0i128; 3]; 3];
        for row in 1..4 {
            let mut target = 0;
            for (source, value) in matrix[row].iter().enumerate() {
                if source != column {
                    minor[row - 1][target] = *value;
                    target += 1;
                }
            }
        }
        let term = matrix[0][column]
            .checked_mul(determinant3(&minor)?)
            .ok_or(GeometryError::ArithmeticOverflow)?;
        total = if column % 2 == 0 {
            total.checked_add(term)
        } else {
            total.checked_sub(term)
        }
        .ok_or(GeometryError::ArithmeticOverflow)?;
    }
    Ok(total)
}

fn hasher(domain: &[u8]) -> blake3::Hasher {
    let mut hasher = blake3::Hasher::new();
    hasher.update(domain);
    hasher.update(CHECKER_VERSION.as_bytes());
    hasher.update(&[0]);
    hasher
}

fn hash_points(hasher: &mut blake3::Hasher, points: &[[i64; 3]]) {
    hasher.update(&(points.len() as u64).to_le_bytes());
    for point in points {
        for coordinate in point {
            hasher.update(&coordinate.to_le_bytes());
        }
    }
}

fn input_digest(request: &GeometryRequest, context: &[u8; 32]) -> [u8; 32] {
    let mut hasher = hasher(b"B60:FL-019:INPUT:v1\0");
    hasher.update(context);
    hash_points(&mut hasher, &request.points);
    for coefficient in request.transform.iter().flatten() {
        hasher.update(&coefficient.to_le_bytes());
    }
    for scope in [request.policy_epoch, request.target_id, request.nonce] {
        hasher.update(&scope.to_le_bytes());
    }
    *hasher.finalize().as_bytes()
}

fn artifact_digest(output: &[[i64; 3]]) -> [u8; 32] {
    let mut hasher = hasher(b"B60:FL-019:ARTIFACT:v1\0");
    hash_points(&mut hasher, output);
    *hasher.finalize().as_bytes()
}

fn policy_digest(request: &GeometryRequest, context: &[u8; 32]) -> [u8; 32] {
    let mut hasher = hasher(b"B60:FL-019:POLICY:v1\0");
    hasher.update(context);
    hasher.update(&request.policy_epoch.to_le_bytes());
    *hasher.finalize().as_bytes()
}

fn hex_digest(digest: &[u8; 32]) -> String {
    blake3::Hash::from_bytes(*digest).to_hex().to_string()
}
