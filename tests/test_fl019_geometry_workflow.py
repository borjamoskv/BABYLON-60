"""FL-019 exercises the real native checkers and persistent governance DAG.

Set BABYLON60_TEST_GEOMETRY_LIBRARY to the library built with --features python.
No checker or persistence implementation is replaced in these tests.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import sqlite3

import pytest

from babylon60.memory.geometry_workflow import GeometryWorkflow, GeometryWorkflowError
from babylon60.memory.governance import MemoryGovernanceEngine, compute_salted_commitment, sign_memory_commitment


POINTS = [[0, 0, 0], [2, 0, 0], [0, 3, 0], [0, 0, 4], [1, 2, 3], [-1, 1, -2]]
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]]
TRANSFORMS = [
    IDENTITY,
    [[1, 0, 0, 7], [0, 1, 0, -3], [0, 0, 1, 2]],
    [[0, -1, 0, 0], [1, 0, 0, 0], [0, 0, 1, 0]],
    [[2, 1, 0, 3], [0, 3, 1, -2], [0, 0, 2, 1]],
    [[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0]],
]


@pytest.fixture(scope="session")
def geometry_library() -> Path:
    value = os.environ.get("BABYLON60_TEST_GEOMETRY_LIBRARY")
    if value is None:
        pytest.skip("build --features python and set BABYLON60_TEST_GEOMETRY_LIBRARY; CI runs this suite explicitly")
    path = Path(value).absolute()
    assert path.is_file(), path
    return path


def engine_at(path: Path) -> MemoryGovernanceEngine:
    engine = MemoryGovernanceEngine(path)
    engine.register_principal_key("geometry-test", "checker-host", b"fl019-disposable-test-key-0001")
    return engine


def workflow_at(engine: MemoryGovernanceEngine, library: Path) -> GeometryWorkflow:
    return GeometryWorkflow(engine, tenant_id="geometry-test", principal="checker-host", native_library=library)


@pytest.fixture
def case(tmp_path: Path, geometry_library: Path) -> tuple[MemoryGovernanceEngine, GeometryWorkflow, Path]:
    engine = engine_at(tmp_path / "geometry.db")
    return engine, workflow_at(engine, geometry_library), geometry_library


def fixture_output(matrix, points=POINTS):
    # Fixture producer is Python; neither Rust verifier calls this implementation.
    return [[sum(row[k] * point[k] for k in range(3)) + row[3] for row in matrix] for point in points]


def register(workflow, matrix=IDENTITY, output=None, *, method="matrix", points=POINTS):
    source = workflow.register_input(points)
    specification = workflow.register_transform(source, matrix)
    execution = workflow.register_execution(specification, method=method)
    result = workflow.register_output(execution, fixture_output(matrix, points) if output is None else output)
    return source, specification, execution, result


@pytest.mark.parametrize("matrix", TRANSFORMS)
@pytest.mark.parametrize("method", ["matrix", "decomposed"])
def test_legitimate_transforms_and_alternative_procedures(case, matrix, method):
    engine, workflow, _ = case
    *_, output = register(workflow, matrix, method=method)
    acceptance = workflow.accept(output, nonce=42)
    assert acceptance.status == "SEMANTICALLY_VERIFIED"
    assert acceptance.report["coordinate_check"] is True
    assert acceptance.report["oriented_volume_check"] is True
    assert workflow.get_acceptance(acceptance.record_id).status == "SEMANTICALLY_VERIFIED"
    assert engine.ledger.verify_integrity()


@pytest.mark.parametrize("damage", ["mirror", "coordinate", "permutation", "stale"])
def test_plausible_but_wrong_results_never_become_verified(case, damage):
    _, workflow, _ = case
    output = copy.deepcopy(POINTS)
    if damage == "mirror":
        output = [[-x, y, z] for x, y, z in output]
    elif damage == "coordinate":
        output[-1][0] += 1
    elif damage == "permutation":
        output[1], output[2] = output[2], output[1]
    else:
        output = fixture_output(TRANSFORMS[1])
    *_, candidate = register(workflow, output=output)
    result = workflow.accept(candidate, nonce=1)
    assert result.status != "SEMANTICALLY_VERIFIED"
    assert result.report["accepted"] is False
    assert result.report["coordinate_check"] is False
    assert result.report["oriented_volume_check"] is False


@pytest.mark.parametrize("stage_index", range(4))
def test_tampered_stage_bytes_fail_closed(case, stage_index):
    engine, workflow, _ = case
    records = register(workflow)
    with sqlite3.connect(engine.db_path) as conn:
        conn.execute("UPDATE cortex_memory_blobs SET plaintext = '{}' WHERE record_id = ?", (records[stage_index],))
    with pytest.raises((GeometryWorkflowError, ValueError)):
        workflow.accept(records[-1], nonce=1)


@pytest.mark.parametrize("damage", ["omit", "transplant"])
def test_signed_payload_cannot_hide_changed_dag_edges(case, damage):
    engine, workflow, _ = case
    first = register(workflow)
    second = register(workflow, TRANSFORMS[1])
    with sqlite3.connect(engine.db_path) as conn:
        if damage == "omit":
            conn.execute("DELETE FROM cortex_memory_edges WHERE child_id = ?", (first[-1],))
        else:
            conn.execute(
                "UPDATE cortex_memory_edges SET parent_id = ? WHERE child_id = ? AND parent_id = ?",
                (second[2], first[-1], first[2]),
            )
    with pytest.raises(GeometryWorkflowError):
        workflow.accept(first[-1], nonce=1)


def test_stage_order_cannot_be_skipped(case):
    _, workflow, _ = case
    source = workflow.register_input(POINTS)
    specification = workflow.register_transform(source, IDENTITY)
    with pytest.raises(GeometryWorkflowError):
        workflow.register_output(specification, POINTS)


def test_validity_and_replay_survive_reopening(case):
    engine, workflow, library = case
    *_, candidate = register(workflow)
    first = workflow.accept(candidate, nonce=9)
    with pytest.raises(GeometryWorkflowError):
        workflow.accept(candidate, nonce=9)
    reopened = workflow_at(engine_at(engine.db_path), library)
    assert reopened.get_acceptance(first.record_id).status == "SEMANTICALLY_VERIFIED"
    with pytest.raises(GeometryWorkflowError):
        reopened.accept(candidate, nonce=9)


@pytest.mark.parametrize("upstream_index", range(4))
def test_revoked_upstream_invalidates_prior_acceptance(case, upstream_index):
    engine, workflow, library = case
    records = register(workflow)
    first = workflow.accept(records[-1], nonce=3)
    engine.revoke_record(
        record_id=records[upstream_index],
        tenant_id="geometry-test",
        principal="checker-host",
        reason="FL-019 mutation",
    )
    reopened = workflow_at(engine_at(engine.db_path), library)
    with pytest.raises(GeometryWorkflowError):
        reopened.get_acceptance(first.record_id)
    with pytest.raises(GeometryWorkflowError):
        reopened.accept(records[-1], nonce=4)


def test_revoked_checker_policy_cannot_be_recreated_on_reopen(case):
    engine, workflow, library = case
    *_, candidate = register(workflow)
    result = workflow.accept(candidate, nonce=2)
    engine.revoke_record(
        record_id=workflow.policy_record_id,
        tenant_id="geometry-test",
        principal="checker-host",
        reason="checker withdrawn",
    )
    with pytest.raises(GeometryWorkflowError):
        workflow.get_acceptance(result.record_id)
    with pytest.raises(GeometryWorkflowError):
        workflow_at(engine_at(engine.db_path), library)


@pytest.mark.parametrize("nonce", [-1, 2**64, True, 1.5])
def test_nonce_must_be_an_exact_u64(case, nonce):
    _, workflow, _ = case
    *_, candidate = register(workflow)
    with pytest.raises(GeometryWorkflowError):
        workflow.accept(candidate, nonce=nonce)


@pytest.mark.parametrize("point", [[True, 0, 0], [1.0, 0, 0], [10001, 0, 0]])
def test_input_outside_exact_domain_is_rejected(case, point):
    _, workflow, _ = case
    points = copy.deepcopy(POINTS)
    points[-1] = point
    with pytest.raises((GeometryWorkflowError, ValueError)):
        register(workflow, points=points)


def test_native_checker_is_required(tmp_path):
    with pytest.raises(GeometryWorkflowError):
        workflow_at(engine_at(tmp_path / "missing.db"), tmp_path / "missing-library.so")


def test_even_a_signed_fabricated_report_is_rechecked(case):
    engine, workflow, _ = case
    wrong = fixture_output(TRANSFORMS[1])
    *_, candidate = register(workflow, output=wrong)
    rejected = workflow.accept(candidate, nonce=31)
    assert rejected.status == "EXECUTED"
    view = engine.get_record(rejected.record_id, tenant_id="geometry-test")
    payload = json.loads(view.content)
    payload["data"]["status"] = "SEMANTICALLY_VERIFIED"
    payload["data"]["report"].update(accepted=True, coordinate_check=True, oriented_volume_check=True)
    forged = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    # Model a signer inventing a positive report, retaining all real input/lineage.
    # Native verification still runs; no checker is replaced or supplied by the caller.
    with sqlite3.connect(engine.db_path) as conn:
        salt = conn.execute(
            "SELECT salt_hex FROM cortex_memory_blobs WHERE record_id = ?",
            (view.record_id,),
        ).fetchone()[0]
        commitment = compute_salted_commitment(salt, forged, view.modality, view.kind)
        signature = sign_memory_commitment(
            b"fl019-disposable-test-key-0001",
            view.principal,
            view.tenant_id,
            commitment,
            view.policy_epoch,
        )
        conn.execute("UPDATE cortex_memory_blobs SET plaintext = ? WHERE record_id = ?", (forged, view.record_id))
        conn.execute(
            "UPDATE cortex_memory_records SET commitment = ?, signature = ? WHERE record_id = ?",
            (commitment, signature, view.record_id),
        )
    # Confirm that this attack gets past the existing signature check first.
    assert engine.get_record(view.record_id, tenant_id="geometry-test").content == forged
    with pytest.raises(GeometryWorkflowError, match="revalidation"):
        workflow.get_acceptance(view.record_id)


def test_revocation_at_acceptance_commit_does_not_return_verified(case, monkeypatch):
    engine, workflow, _ = case
    source, *_, output = register(workflow)
    add_record = engine.add_record
    scheduled = []

    def revoke_before_acceptance(**kwargs):
        if json.loads(kwargs["content"])["stage"] == "ACCEPTANCE":
            engine.revoke_record(
                record_id=source,
                tenant_id="geometry-test",
                principal="checker-host",
                reason="commit interleaving",
            )
            scheduled.append(True)
        return add_record(**kwargs)

    # This hook schedules a real revocation, then delegates to the actual insert.
    monkeypatch.setattr(engine, "add_record", revoke_before_acceptance)
    with pytest.raises(GeometryWorkflowError):
        workflow.accept(output, nonce=2)
    assert scheduled == [True]
    assert all(
        json.loads(record.content)["stage"] != "ACCEPTANCE"
        for record in engine.query_active_memories(tenant_id="geometry-test")
    )


def test_failed_native_verification_consumes_attempt_across_reopen(case):
    engine, workflow, library = case
    coplanar = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [1, 1, 0]]
    *_, candidate = register(workflow, points=coplanar)
    with pytest.raises(GeometryWorkflowError, match="Native geometry verification failed"):
        workflow.accept(candidate, nonce=19)
    reopened = workflow_at(engine_at(engine.db_path), library)
    with pytest.raises(GeometryWorkflowError, match="Replay"):
        reopened.accept(candidate, nonce=19)


@pytest.mark.parametrize("field,value", [("valid_from_tick", 2**60), ("valid_to_tick", 1)])
def test_active_flag_cannot_override_invalid_temporal_metadata(case, field, value):
    engine, workflow, _ = case
    source, *_, output = register(workflow)
    with sqlite3.connect(engine.db_path) as conn:
        # Identifiers come exclusively from this fixed parameter list.
        conn.execute(f"UPDATE cortex_memory_records SET {field} = ? WHERE record_id = ?", (value, source))
    with pytest.raises(GeometryWorkflowError):
        workflow.accept(output, nonce=8)
