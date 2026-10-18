use babylon60::capability::ScopedHandle;
use babylon60::ontology::babylon::RejectReason;

/// FL-008 CONFUSED DEPUTY STRESS HARNESS
///
/// Goal: Prove that a capability must correspond strictly to its causal parent.
/// A malicious LLM or untrusted agent cannot reuse an open handle for an unauthorized entity.
fn main() {
    println!("╔══════════════════════════════════════════════════════════════════════════════╗");
    println!("║          BABYLON-60 · FL-008 · CONFUSED DEPUTY PREVENTION HARNESS            ║");
    println!("╚══════════════════════════════════════════════════════════════════════════════╝");

    // Simulate two distinct causal origins (e.g., two distinct prompts/sessions)
    let alice_origin_id = [0xAA; 32];
    let eve_origin_id = [0xEE; 32];

    // Alice requests a capability to mutate a directory
    let temp_dir = std::env::temp_dir();
    
    // We instantiate the ScopedHandle bound to Alice's causal parent
    let alice_cap = ScopedHandle::new(temp_dir.as_path(), alice_origin_id)
        .expect("Failed to create Alice's capability");

    println!("Alice Capability Acquired. DIRFD: {}, INO: {}", alice_cap.dirfd, alice_cap.ino);

    // Eve attempts to execute a mutation using Alice's capability handle
    // The executor MUST verify the causal parent
    let verification_result = alice_cap.verify_causal_parent(&eve_origin_id);

    match verification_result {
        Ok(_) => {
            panic!("FL-008 FALSIFIED: Confused Deputy attack succeeded! Eve used Alice's capability.");
        }
        Err(RejectReason::ConfusedDeputyAttempt) => {
            println!("Intercepted malicious capability reuse: ConfusedDeputyAttempt.");
        }
        Err(e) => {
            panic!("FL-008 UNEXPECTED REJECTION: {:?}", e);
        }
    }

    // Alice attempts to use her own capability
    let alice_verification = alice_cap.verify_causal_parent(&alice_origin_id);
    assert!(alice_verification.is_ok(), "FL-008 FALSIFIED: Legitimate causal parent rejected!");
    
    println!("Legitimate causal parent verified successfully.");
    println!("Verdict: SUPPORTED_WITHIN_DOMAIN. Capability causal provenance verified.");
}
