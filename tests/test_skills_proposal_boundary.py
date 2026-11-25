"""Skill proposals cannot certify execution or supply their own postcondition evidence."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from babylon60.mcp.skills_snapshot import GATEWAY_EXPECTED_AUDIENCE, ImmutableSkillsSnapshot


@pytest.fixture
def snapshot() -> ImmutableSkillsSnapshot:
    root = Path(__file__).absolute().parents[1]
    return ImmutableSkillsSnapshot.load(root / "docs/skills.json", root / ".agents/skills")


def proposal(snapshot: ImmutableSkillsSnapshot, target: Path, skill_id: str = "wizard") -> dict[str, object]:
    # `wizard` is a workspace-backed STATE_MUTATION skill: it passes the FL-P08 v3.2 artifact gate,
    # so these tests keep exercising the proposal boundary rather than ARTIFACT_UNBOUND.
    skill = snapshot.resolve(skill_id)
    assert skill is not None
    return {
        "skill_id": skill.name,
        "version": skill.version,
        "tool_identity_hash": skill.tool_identity_hash,
        "arguments": {"target_path": str(target), "expected_pre_hash": "a" * 64},
        "precondition_snapshot": {"allowed_roots": [str(target.parent)], "observed_pre_hash": "a" * 64},
        "credential": {"audience": GATEWAY_EXPECTED_AUDIENCE, "project_id": "fixture", "nonce": "once"},
    }


def test_proposal_fixture_is_artifact_bound_state_mutation(snapshot):
    skill = snapshot.resolve("wizard")
    assert skill is not None
    assert skill.effect_profile["class"] == "STATE_MUTATION"
    assert skill.artifact_provenance == "workspace_disk"


def test_synthetic_state_mutation_denied_artifact_unbound(snapshot, tmp_path):
    skill = snapshot.resolve("cortex-skill-genesis")
    assert skill is not None
    assert skill.effect_profile["class"] == "STATE_MUTATION"
    assert skill.artifact_provenance == "catalog_synthetic"
    target = tmp_path / "state"
    target.write_bytes(b"before")
    result = snapshot.propose_skill_effect(proposal(snapshot, target, "cortex-skill-genesis"))
    assert result["status"] == "DENIED"
    assert result["failure_class"] == "ARTIFACT_UNBOUND"
    assert target.read_bytes() == b"before"


def test_lock_entries_declare_provenance(snapshot):
    lock = snapshot.to_lockfile()
    assert lock["schema_version"] == "3.2.0"
    assert lock["lock_scope"] == "repo"
    provenances = {entry["artifact_provenance"] for entry in lock["skills"].values()}
    assert provenances <= {"workspace_disk", "catalog_synthetic"}


def test_provenance_tamper_rejected(snapshot):
    lock = deepcopy(snapshot.to_lockfile())
    lock["skills"]["cortex-skill-genesis"]["artifact_provenance"] = "workspace_disk"
    with pytest.raises(ValueError, match="SKILLS_LOCK_MISMATCH"):
        snapshot.verify_against_lockfile(lock)


def test_proposal_does_not_certify_execution(snapshot, tmp_path):
    target = tmp_path / "state"
    target.write_bytes(b"before")
    result = snapshot.propose_skill_effect(proposal(snapshot, target))
    assert result["status"] == "AUTHORIZED"
    assert result["effects_executed"] == 0
    assert result["evidence"]["postconditions_checked"] == []
    assert "verified_by" not in result["evidence"]
    assert target.read_bytes() == b"before"


@pytest.mark.parametrize(
    "evidence",
    [
        None,
        {},
        {"observed_post_hash": "b" * 64},
        {"observed_post_hash": "b" * 64, "actual_file_sha256": "b" * 64, "http_status": 200},
    ],
)
def test_client_cannot_forge_postconditions(snapshot, tmp_path, evidence):
    target = tmp_path / "state"
    target.write_bytes(b"before")
    args = proposal(snapshot, target)
    args["simulated_execution_result"] = evidence
    for _ in range(110):  # 10 warmups, 100 repeated adversarial requests.
        result = snapshot.propose_skill_effect(args)
        assert result["status"] == "DENIED"
        assert result["failure_class"] == "UNTRUSTED_EXECUTION_EVIDENCE"
        assert "action_capability" not in result
    assert target.read_bytes() == b"before"
    del args["simulated_execution_result"]
    assert snapshot.propose_skill_effect(args)["status"] == "AUTHORIZED"


@pytest.mark.parametrize(
    "field,value",
    [
        ("tool_identity_hash", None),
        ("tool_identity_hash", 5),
        ("tool_identity_hash", ""),
        ("version", None),
        ("version", ""),
    ],
)
def test_proposal_requires_exact_identity(snapshot, tmp_path, field, value):
    args = proposal(snapshot, tmp_path / "state")
    if value is None:
        del args[field]
    else:
        args[field] = value
    result = snapshot.propose_skill_effect(args)
    assert result["status"] == "DENIED"
    assert result["failure_class"] == "TOOL_IDENTITY_MISMATCH"


@pytest.mark.parametrize("field", ["effect_profile", "guard_invariants", "skill_id"])
def test_lock_pins_policy_as_well_as_artifact(snapshot, field):
    lock = deepcopy(snapshot.to_lockfile())
    entry = lock["skills"]["cortex-skill-genesis"]
    if field == "effect_profile":
        entry[field]["requires_action_lease"] = False
    elif field == "guard_invariants":
        entry[field]["postconditions"] = []
    else:
        entry[field] = "shadow"
    with pytest.raises(ValueError, match="SKILLS_LOCK_MISMATCH"):
        snapshot.verify_against_lockfile(lock)


def test_python_snapshot_matches_checked_in_lock(snapshot):
    root = Path(__file__).absolute().parents[1]
    lock = json.loads((root / "skills-lock.json").read_text())
    snapshot.verify_against_lockfile(lock)


def test_load_rejects_missing_or_tampered_pin(snapshot, tmp_path):
    root = Path(__file__).absolute().parents[1]
    lock_path = tmp_path / "skills-lock.json"
    with pytest.raises(FileNotFoundError):
        ImmutableSkillsSnapshot.load(root / "docs/skills.json", root / ".agents/skills", lockfile_path=lock_path)
    lock = snapshot.to_lockfile()
    lock["skills"]["thermo-audit"]["guard_invariants"]["postconditions"] = []
    lock_path.write_text(json.dumps(lock))
    with pytest.raises(ValueError, match="SKILLS_LOCK_MISMATCH"):
        ImmutableSkillsSnapshot.load(root / "docs/skills.json", root / ".agents/skills", lockfile_path=lock_path)
