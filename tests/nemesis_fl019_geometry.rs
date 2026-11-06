//! FL-019 exact affine geometry checks against deterministic fixtures.
//!
//! This campaign covers the bounded integer domain in the geometry contract. It
//! does not certify arbitrary scientific workflows or independence of software
//! implementations sharing a compiler and process.
#![cfg(feature = "cortex-persist")]

use babylon60::geometry_integrity::{GeometryRequest, GeometryVerifier, MAX_REQUEST_BYTES};

const IDENTITY: [[i64; 4]; 3] = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]];

fn points() -> Vec<[i64; 3]> {
    vec![
        [0, 0, 0],
        [2, 0, 0],
        [0, 3, 0],
        [0, 0, 5],
        [1, 1, 1],
        [-3, 2, -4],
    ]
}

// Fixture producer belongs to the test and never calls either verifier.
fn fixture_output(points: &[[i64; 3]], transform: [[i64; 4]; 3]) -> Vec<[i64; 3]> {
    points
        .iter()
        .map(|point| {
            transform.map(|row| row[3] + row[0] * point[0] + row[1] * point[1] + row[2] * point[2])
        })
        .collect()
}

fn request(transform: [[i64; 4]; 3], nonce: u64) -> GeometryRequest {
    let points = points();
    let output = fixture_output(&points, transform);
    GeometryRequest {
        points,
        transform,
        output,
        context_digest_b3: "12".repeat(32),
        policy_epoch: 7,
        target_id: 19,
        nonce,
    }
}

#[test]
fn accepts_known_rotation_translation_shear_scale_and_declared_reflection() {
    let cases = [
        // Rotation by 90 degrees around z, translation, shear, nonuniform scale,
        // and a declared reflection are all valid affine operations.
        [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]],
        [[1, 0, 0, 11], [0, 1, 0, -7], [0, 0, 1, 4]],
        [[1, 3, 0, 0], [0, 1, -2, 0], [0, 0, 1, 0]],
        [[2, 0, 0, 0], [0, 3, 0, 0], [0, 0, 4, 0]],
        [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]],
    ];
    let mut verifier = GeometryVerifier::new();
    for (index, transform) in cases.into_iter().enumerate() {
        let report = verifier.verify(request(transform, index as u64)).unwrap();
        assert!(report.accepted, "{index}: {:?}", report.reason);
        assert!(report.coordinate_check);
        assert!(report.oriented_volume_check);
        assert_eq!(report.input_digest_b3.len(), 64);
        assert_eq!(report.artifact_digest_b3.len(), 64);
        assert_eq!(report.joint_evidence_digest_b3.as_ref().unwrap().len(), 64);
        assert!(!report.checker_version.is_empty());
    }
}

#[test]
fn rejects_an_extra_reflection_instead_of_accepting_absolute_volume() {
    let mut candidate = request(IDENTITY, 40);
    for point in &mut candidate.output {
        point[0] = -point[0];
    }
    let report = GeometryVerifier::new().verify(candidate).unwrap();
    assert!(!report.accepted);
    assert!(!report.coordinate_check);
    assert!(!report.oriented_volume_check);
    assert!(report.joint_evidence_digest_b3.is_none());
}

#[test]
fn independent_anchor_reconstruction_rejects_wrong_translation() {
    let mut candidate = request(IDENTITY, 41);
    for point in &mut candidate.output {
        point[0] += 8;
        point[1] -= 3;
    }
    let report = GeometryVerifier::new().verify(candidate).unwrap();
    assert!(!report.accepted);
    assert!(!report.coordinate_check);
    // Volume and barycentric coordinates alone preserve global translation;
    // reconstruction of the affine coefficients must also bind the anchors.
    assert!(!report.oriented_volume_check);
}

#[test]
fn barycentric_check_rejects_changed_non_anchor_point() {
    let mut candidate = request(IDENTITY, 42);
    candidate.output[4][2] += 1;
    let report = GeometryVerifier::new().verify(candidate).unwrap();
    assert!(!report.accepted);
    assert!(!report.coordinate_check);
    assert!(!report.oriented_volume_check);
}

#[test]
fn rejects_stale_output_after_input_or_transform_changes() {
    let mut changed_input = request(IDENTITY, 43);
    changed_input.points[4][0] += 1;
    assert!(
        !GeometryVerifier::new()
            .verify(changed_input)
            .unwrap()
            .accepted
    );

    let mut changed_transform = request(IDENTITY, 44);
    changed_transform.transform[0][3] += 1;
    assert!(
        !GeometryVerifier::new()
            .verify(changed_transform)
            .unwrap()
            .accepted
    );
}

#[test]
fn rejects_missing_and_additional_output_points_semantically() {
    let mut missing = request(IDENTITY, 45);
    missing.output.pop();
    let report = GeometryVerifier::new().verify(missing).unwrap();
    assert!(!report.accepted);
    assert!(!report.coordinate_check);
    assert!(!report.oriented_volume_check);

    let mut extra = request(IDENTITY, 46);
    extra.output.push([0, 0, 0]);
    assert!(!GeometryVerifier::new().verify(extra).unwrap().accepted);
}

#[test]
fn evidence_is_bound_to_input_context_policy_and_candidate_bytes() {
    let baseline = GeometryVerifier::new()
        .verify(request(IDENTITY, 47))
        .unwrap();

    let mut context = request(IDENTITY, 47);
    context.context_digest_b3 = "34".repeat(32);
    let context_report = GeometryVerifier::new().verify(context).unwrap();
    assert!(context_report.accepted);
    assert_ne!(baseline.input_digest_b3, context_report.input_digest_b3);
    assert_ne!(
        baseline.joint_evidence_digest_b3,
        context_report.joint_evidence_digest_b3
    );

    let mut policy = request(IDENTITY, 47);
    policy.policy_epoch += 1;
    let policy_report = GeometryVerifier::new().verify(policy).unwrap();
    assert!(policy_report.accepted);
    assert_ne!(
        baseline.joint_evidence_digest_b3,
        policy_report.joint_evidence_digest_b3
    );

    let mut input = request(IDENTITY, 47);
    input.points[4][0] += 1;
    input.output[4][0] += 1;
    let input_report = GeometryVerifier::new().verify(input).unwrap();
    assert!(input_report.accepted);
    assert_ne!(baseline.input_digest_b3, input_report.input_digest_b3);
    assert_ne!(baseline.artifact_digest_b3, input_report.artifact_digest_b3);
    assert_ne!(
        baseline.joint_evidence_digest_b3,
        input_report.joint_evidence_digest_b3
    );
}

#[test]
fn successful_witness_cannot_be_replayed_within_verifier_instance() {
    let mut verifier = GeometryVerifier::new();
    assert!(verifier.verify(request(IDENTITY, 48)).unwrap().accepted);
    let replay = verifier.verify(request(IDENTITY, 48)).unwrap();
    assert!(!replay.accepted);
    assert!(replay.coordinate_check);
    assert!(replay.oriented_volume_check);
    assert!(replay.joint_evidence_digest_b3.is_none());
    assert!(replay.reason.is_some());
    assert!(verifier.verify(request(IDENTITY, 49)).unwrap().accepted);
}

#[test]
fn malformed_json_cannot_supply_checker_results_or_non_integer_numbers() {
    let ordinary = serde_json::to_value(request(IDENTITY, 50)).unwrap();
    for injected in [serde_json::json!(1.25), serde_json::json!(1.0)] {
        let mut payload = ordinary.clone();
        payload["points"][0][0] = injected;
        assert!(GeometryVerifier::new()
            .verify_json(&payload.to_string())
            .is_err());
    }
    let mut fabricated = ordinary.clone();
    fabricated["passed"] = serde_json::json!(true);
    assert!(GeometryVerifier::new()
        .verify_json(&fabricated.to_string())
        .is_err());
    let json = ordinary.to_string();
    let position = json.find("[[0,0,0]").unwrap();
    let malformed = format!("{}[[NaN,0,0]{}", &json[..position], &json[position + 8..]);
    assert!(GeometryVerifier::new().verify_json(&malformed).is_err());
    assert!(GeometryVerifier::new().verify_json("{").is_err());
    assert!(GeometryVerifier::new()
        .verify_json(&" ".repeat(MAX_REQUEST_BYTES + 1))
        .is_err());
}

#[test]
fn rejects_invalid_shapes_degeneracy_digest_and_numeric_bounds() {
    for count in [3, 257] {
        let mut candidate = request(IDENTITY, 51);
        candidate.points.resize(count, [1, 1, 1]);
        candidate.output = candidate.points.clone();
        assert!(GeometryVerifier::new().verify(candidate).is_err());
    }
    let mut flat = request(IDENTITY, 52);
    flat.points[3] = [1, 1, 0];
    assert!(GeometryVerifier::new().verify(flat).is_err());

    let mut singular = request(IDENTITY, 53);
    singular.transform[2] = [0, 0, 0, 1];
    assert!(GeometryVerifier::new().verify(singular).is_err());

    for bad_digest in ["", "00", &"g".repeat(64)] {
        let mut candidate = request(IDENTITY, 54);
        candidate.context_digest_b3 = bad_digest.into();
        assert!(GeometryVerifier::new().verify(candidate).is_err());
    }
    for huge in [10_001, i64::MIN, i64::MAX] {
        let mut point = request(IDENTITY, 55);
        point.points[4][0] = huge;
        assert!(GeometryVerifier::new().verify(point).is_err());

        let mut coefficient = request(IDENTITY, 56);
        coefficient.transform[0][0] = huge;
        assert!(GeometryVerifier::new().verify(coefficient).is_err());
    }
    for huge in [1_000_000_001, i64::MIN, i64::MAX] {
        let mut candidate = request(IDENTITY, 57);
        candidate.output[4][0] = huge;
        assert!(GeometryVerifier::new().verify(candidate).is_err());
    }
}

#[test]
fn bounded_extreme_coordinates_and_256_points_do_not_overflow() {
    let mut candidate = request(
        [
            [10_000, 10_000, 0, 10_000],
            [0, 10_000, 0, -10_000],
            [0, 0, -10_000, 0],
        ],
        58,
    );
    candidate.points = vec![
        [-10_000, -10_000, -10_000],
        [10_000, -10_000, -10_000],
        [-10_000, 10_000, -10_000],
        [-10_000, -10_000, 10_000],
    ];
    candidate.points.resize(256, [10_000, 10_000, 10_000]);
    candidate.output = fixture_output(&candidate.points, candidate.transform);
    let report = GeometryVerifier::new().verify(candidate).unwrap();
    assert!(report.accepted, "{:?}", report.reason);
    assert!(report.coordinate_check);
    assert!(report.oriented_volume_check);
}

#[test]
fn deterministic_campaign_checks_500_valid_and_500_corrupted_runs() {
    let mut verifier = GeometryVerifier::new();
    let mut valid_accepted = 0;
    let mut invalid_accepted = 0;
    for case in 0..500_u64 {
        let n = case as i64;
        // Upper triangular matrices with nonzero diagonal are nonsingular by
        // construction; alternating the x sign includes declared reflections.
        let transform = [
            [
                if case % 2 == 0 { 1 } else { -2 },
                n % 7 - 3,
                n % 5 - 2,
                n - 250,
            ],
            [0, 1 + n % 3, n % 11 - 5, 100 - n],
            [0, 0, 1 + n % 5, n % 17],
        ];
        let valid = verifier
            .verify(request(transform, 1_000 + 2 * case))
            .unwrap();
        valid_accepted += usize::from(valid.accepted);
        assert!(valid.coordinate_check, "valid case {case}");
        assert!(valid.oriented_volume_check, "valid case {case}");

        let mut corrupted = request(transform, 1_001 + 2 * case);
        // Mutate a point beyond the anchor tetrahedron: oriented anchor volume
        // alone still passes, but the barycentric relation must reject it.
        corrupted.output[4][(case % 3) as usize] += 1;
        let invalid = verifier.verify(corrupted).unwrap();
        invalid_accepted += usize::from(invalid.accepted);
        assert!(!invalid.coordinate_check, "invalid case {case}");
        assert!(!invalid.oriented_volume_check, "invalid case {case}");
    }
    assert_eq!(valid_accepted, 500);
    assert_eq!(invalid_accepted, 0);
}
