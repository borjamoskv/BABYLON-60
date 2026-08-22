use exergy_core::{ExergyError, FeaturePayload, MarkovBlanketVerifier};

#[test]
fn test_markov_blanket_clean_isolation() {
    let verifier = MarkovBlanketVerifier::new(0.0);

    let clean_payload = FeaturePayload::new(
        "AGCTAGCTAGCTAGCTAGCT",
        vec![
            ("locus_1", "GATA_12"),
            ("locus_2", "GATA_14"),
            ("instrument_id", "ABI_3500_SEQ"),
        ],
    );

    let result = verifier.verify_and_isolate(&clean_payload).expect("Isolation should succeed");

    assert!(result.is_isolated);
    assert_eq!(result.information_leakage_bits, 0.0);
    assert_eq!(result.purged_noise_fields.len(), 0);
    assert_eq!(result.retained_features.len(), 3);
}

#[test]
fn test_markov_blanket_purges_contextual_noise() {
    let verifier = MarkovBlanketVerifier::new(15.0); // Allow up to 15 bits of purged leakage


    let noisy_payload = FeaturePayload::new(
        "MINUTIAE_POINTS_FINGERPRINT_RIDGE",
        vec![
            ("quality_score", "0.98"),
            ("suspect_name", "Brandon Mayfield"),
            ("race", "Caucasian"),
            ("media_hype", "Madrid Train Bombing"),
        ],
    );

    let result = verifier.verify_and_isolate(&noisy_payload).expect("Isolation with purging should succeed");

    assert!(result.is_isolated);
    assert!(result.information_leakage_bits > 0.0);
    assert_eq!(result.purged_noise_fields.len(), 3);
    assert_eq!(result.retained_features.len(), 1);
    assert_eq!(result.retained_features[0], "quality_score:0.98");
}

#[test]
fn test_markov_blanket_rejects_excessive_leakage() {
    let verifier = MarkovBlanketVerifier::new(0.0); // Zero tolerance for leakage

    let contaminated_payload = FeaturePayload::new(
        "STR_DNA_MIXTURE_4_CONTRIBUTORS",
        vec![
            ("prior_record", "Felony 1999"),
            ("prosecutor_theory", "Homicide premeditated"),
        ],
    );

    let err = verifier.verify_and_isolate(&contaminated_payload).unwrap_err();

    match err {
        ExergyError::MarkovBlanketViolation { field, leakage_bits, .. } => {
            assert!(field.contains("prior_record"));
            assert!(field.contains("prosecutor_theory"));
            assert!(leakage_bits > 0.0);
        }
        _ => panic!("Expected MarkovBlanketViolation error variant"),
    }
}
