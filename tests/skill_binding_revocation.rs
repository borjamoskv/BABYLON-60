use babylon60::capability::{
    sha256_digest, GuardProposalInput, GuardSkillLockBinding, McpCapabilityBroker,
};
use babylon60::ontology::babylon::{EffectKind, EffectState, RejectReason};
use std::fs;
use std::path::{Path, PathBuf};

struct Fixture(PathBuf);

impl Fixture {
    fn new() -> Self {
        let path =
            std::env::temp_dir().join(format!("skill-revocation-{:016x}", rand::random::<u64>()));
        fs::create_dir(&path).unwrap();
        Self(path)
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn skill_binding() -> GuardSkillLockBinding {
    GuardSkillLockBinding {
        skill_id: "edit-fixture".into(),
        version: "1.0.0".into(),
        artifact_sha256: [1; 32],
        tool_identity_hash: [2; 32],
        effect_kind: EffectKind::FsMutate,
        network_egress: false,
        validated: true,
    }
}

fn proposal(binding: &GuardSkillLockBinding, file: &Path, nonce: &str) -> GuardProposalInput {
    let pre_hash = sha256_digest(b"before");
    GuardProposalInput {
        skill_id: binding.skill_id.clone(),
        version: binding.version.clone(),
        tool_identity_hash: binding.tool_identity_hash,
        artifact_sha256: binding.artifact_sha256,
        audience: "test-gateway".into(),
        expected_audience: "test-gateway".into(),
        project_id: "test-project".into(),
        trace_id: "test-trace".into(),
        nonce: nonce.into(),
        passthrough_token: None,
        resource_uri: file.to_str().unwrap().into(),
        allowed_roots: vec![file.parent().unwrap().to_str().unwrap().into()],
        args_digest: sha256_digest(b"write after"),
        precondition_snapshot_hash: [3; 32],
        expected_pre_hash: Some(pre_hash),
        observed_pre_hash: Some(pre_hash),
        network_destination: None,
        current_epoch: 1,
        expires_at_epoch: 60,
        human_approved: false,
    }
}

fn dispatch(
    broker: &mut McpCapabilityBroker,
    id: &[u8; 32],
    input: &GuardProposalInput,
    file: &Path,
) -> Result<EffectState, RejectReason> {
    broker
        .execute_and_verify_skill_effect(
            id,
            &input.audience,
            &input.project_id,
            &input.resource_uri,
            &input.args_digest,
            2,
            || {
                fs::write(file, b"after").unwrap();
                Ok(sha256_digest(b"after"))
            },
            || Ok(sha256_digest(&fs::read(file).unwrap())),
        )
        .map(|(_, state)| state)
}

#[test]
fn invalidating_a_skill_revokes_its_pending_grant() {
    let dir = Fixture::new();
    let file = dir.0.join("resource");
    fs::write(&file, b"before").unwrap();
    let mut broker = McpCapabilityBroker::new();
    let mut binding = skill_binding();
    broker.register_skill_lock_binding(binding.clone());
    let input = proposal(&binding, &file, "first");
    let grant = broker.propose_skill_effect(input.clone()).unwrap();

    binding.validated = false;
    broker.register_skill_lock_binding(binding);

    let result = dispatch(&mut broker, &grant.capability_id, &input, &file);
    assert_eq!(
        fs::read(&file).unwrap(),
        b"before",
        "revoked grant wrote to the file"
    );
    assert_eq!(result, Err(RejectReason::StaleCapability));
}

#[test]
fn restoring_a_binding_does_not_revive_the_old_grant() {
    let dir = Fixture::new();
    let file = dir.0.join("resource");
    fs::write(&file, b"before").unwrap();
    let mut broker = McpCapabilityBroker::new();
    let binding = skill_binding();
    broker.register_skill_lock_binding(binding.clone());
    let input = proposal(&binding, &file, "first");
    let grant = broker.propose_skill_effect(input.clone()).unwrap();

    let mut replacement = binding.clone();
    replacement.artifact_sha256 = [4; 32];
    broker.register_skill_lock_binding(replacement);
    broker.register_skill_lock_binding(binding.clone());

    let result = dispatch(&mut broker, &grant.capability_id, &input, &file);
    assert_eq!(
        fs::read(&file).unwrap(),
        b"before",
        "restored binding revived the grant"
    );
    assert_eq!(result, Err(RejectReason::StaleCapability));

    let fresh = proposal(&binding, &file, "second");
    let fresh_grant = broker.propose_skill_effect(fresh.clone()).unwrap();
    broker.register_skill_lock_binding(binding.clone());
    let mut unrelated = binding;
    unrelated.skill_id = "other-skill".into();
    broker.register_skill_lock_binding(unrelated.clone());
    unrelated.validated = false;
    broker.register_skill_lock_binding(unrelated);

    assert_eq!(
        dispatch(&mut broker, &fresh_grant.capability_id, &fresh, &file),
        Ok(EffectState::Verified)
    );
    assert_eq!(fs::read(&file).unwrap(), b"after");
    assert_eq!(
        dispatch(&mut broker, &fresh_grant.capability_id, &fresh, &file),
        Err(RejectReason::StaleCapability)
    );
}
