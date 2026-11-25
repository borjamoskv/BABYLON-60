"""Procedural learning uses durable, varied evidence rather than model confidence."""

from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

import pytest

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger
from babylon60.memory.learning import SkillLearning


def learning(tmp_path: Path) -> SkillLearning:
    return SkillLearning(CortexPersistLedger(tmp_path / "cortex.db"))


def candidate(service: SkillLearning, *, lesson_id: str = "verify", context: str = "code") -> dict[str, object]:
    return service.propose_lesson(
        lesson_id=lesson_id,
        skill_id="verification",
        context=context,
        procedure="Check completed evidence for the current state before reporting success.",
        cortex_taint="test",
    )


def attempt(
    service: SkillLearning,
    number: int,
    *,
    success: bool = True,
    held_out: bool = False,
    variant_id: str | None = None,
    session_id: str | None = None,
    lesson_id: str = "verify",
) -> dict[str, object]:
    return service.record_attempt(
        lesson_id=lesson_id,
        attempt_id=f"attempt-{number}",
        variant_id=variant_id or f"variant-{number}",
        session_id=session_id or f"session-{number}",
        success=success,
        held_out=held_out,
        evidence={"validator": "pytest", "reference": f"run-{number}", "passed": success},
        cortex_taint="test",
    )


def prepare_valid(service: SkillLearning) -> None:
    candidate(service)
    attempt(service, 1)
    attempt(service, 2)
    attempt(service, 3, held_out=True)


def test_candidates_are_exactly_filtered_and_survive_restarts(tmp_path: Path) -> None:
    service = learning(tmp_path)
    assert candidate(service)["status"] == "candidate"
    candidate(service, lesson_id="deploy", context="deployment")

    restarted = learning(tmp_path)
    assert [x["lesson_id"] for x in restarted.retrieve_lessons(skill_id="verification", context="code")] == ["verify"]
    assert restarted.retrieve_lessons(context="CODE") == []
    assert restarted.retrieve_lessons(active_only=True) == []
    assert restarted.get_lesson("verify")["procedure"] == service.get_lesson("verify")["procedure"]


def test_promote_requires_varied_practice_and_a_separate_held_out_session(tmp_path: Path) -> None:
    service = learning(tmp_path)
    candidate(service)
    attempt(service, 1)
    attempt(service, 2, variant_id="variant-1")
    attempt(service, 3, held_out=True)
    with pytest.raises(ValueError, match="validation"):
        service.promote_lesson(lesson_id="verify", cortex_taint="test")
    attempt(service, 4, session_id="session-1")
    # A second practice variant in the original session is insufficient.
    assert service.get_lesson("verify")["validation_ready"] is False
    attempt(service, 5)
    assert service.promote_lesson(lesson_id="verify", cortex_taint="test")["status"] == "active"
    assert learning(tmp_path).retrieve_lessons(active_only=True)[0]["lesson_id"] == "verify"


def test_held_out_requires_distinct_session_and_variant(tmp_path: Path) -> None:
    service = learning(tmp_path)
    candidate(service)
    attempt(service, 1)
    attempt(service, 2)
    attempt(service, 3, held_out=True, session_id="session-2")
    assert service.get_lesson("verify")["validation_ready"] is False
    with pytest.raises(ValueError, match="variant"):
        attempt(service, 4, held_out=True, variant_id="variant-1")
    attempt(service, 5, held_out=True)
    assert service.get_lesson("verify")["validation_ready"] is True


def test_failed_outcome_revokes_activation_and_resets_validation_window(tmp_path: Path) -> None:
    service = learning(tmp_path)
    prepare_valid(service)
    service.promote_lesson(lesson_id="verify", cortex_taint="test")
    attempt(service, 4, success=False)
    assert learning(tmp_path).retrieve_lessons(active_only=True) == []
    assert learning(tmp_path).get_lesson("verify")["status"] == "candidate"
    attempt(service, 5)
    attempt(service, 6, held_out=True)
    with pytest.raises(ValueError, match="validation"):
        service.promote_lesson(lesson_id="verify", cortex_taint="test")
    attempt(service, 7)
    assert service.get_lesson("verify")["status"] == "candidate"
    assert service.promote_lesson(lesson_id="verify", cortex_taint="test")["status"] == "active"


def test_duplicate_candidate_attempt_and_activation_are_idempotent(tmp_path: Path) -> None:
    service = learning(tmp_path)
    first = candidate(service)
    assert candidate(service) == first
    one = attempt(service, 1)
    assert attempt(service, 1) == one
    attempt(service, 2)
    attempt(service, 3, held_out=True)
    promoted = service.promote_lesson(lesson_id="verify", cortex_taint="test")
    assert service.promote_lesson(lesson_id="verify", cortex_taint="test") == promoted
    with pytest.raises(ValueError, match="attempt"):
        attempt(service, 1, success=False)
    with pytest.raises(ValueError, match="lesson"):
        service.propose_lesson(
            lesson_id="verify", skill_id="verification", context="code", procedure="Different rule", cortex_taint="test"
        )


@pytest.mark.parametrize(
    "evidence",
    [
        {},
        {"confidence": 1.0},
        {"validator": "pytest", "reference": "log", "passed": False},
        {"validator": "", "reference": "log", "passed": True},
        {"validator": "pytest", "reference": "log", "passed": 1},
    ],
)
def test_evidence_must_have_validator_reference_and_matching_boolean(
    tmp_path: Path, evidence: dict[str, object]
) -> None:
    service = learning(tmp_path)
    candidate(service)
    with pytest.raises(ValueError, match="evidence"):
        service.record_attempt(
            lesson_id="verify",
            attempt_id="bad",
            variant_id="one",
            session_id="one",
            success=True,
            evidence=evidence,
            cortex_taint="test",
        )
    assert service.get_lesson("verify")["attempt_count"] == 0


def test_inputs_are_bounded_and_missing_lessons_fail(tmp_path: Path) -> None:
    service = learning(tmp_path)
    with pytest.raises(KeyError):
        service.get_lesson("missing")
    with pytest.raises(ValueError):
        service.propose_lesson(
            lesson_id="x", skill_id="verification", context="code", procedure="x" * 8193, cortex_taint="test"
        )
    with pytest.raises(ValueError):
        service.propose_lesson(lesson_id="x", skill_id="verification", context="code", procedure="Do", cortex_taint="")


def test_unpromoted_valid_lesson_is_not_active_and_success_keeps_activation(tmp_path: Path) -> None:
    service = learning(tmp_path)
    prepare_valid(service)
    assert service.get_lesson("verify")["validation_ready"] is True
    assert service.retrieve_lessons(active_only=True) == []
    service.promote_lesson(lesson_id="verify", cortex_taint="test")
    attempt(service, 4)
    assert service.get_lesson("verify")["status"] == "active"


def test_reactivation_after_failure_is_a_new_durable_decision(tmp_path: Path) -> None:
    service = learning(tmp_path)
    prepare_valid(service)
    service.promote_lesson(lesson_id="verify", cortex_taint="first")
    attempt(service, 4, success=False)
    attempt(service, 5)
    attempt(service, 6)
    attempt(service, 7, held_out=True)
    assert service.promote_lesson(lesson_id="verify", cortex_taint="second")["status"] == "active"
    assert learning(tmp_path).get_lesson("verify")["status"] == "active"


def test_concurrent_conflicting_attempts_commit_only_one_outcome(tmp_path: Path) -> None:
    service = learning(tmp_path)
    candidate(service)
    # Warm the event-sourced read and write path in the isolated database.
    attempt(service, 0)
    service.get_lesson("verify")

    def record(number: int) -> bool:
        try:
            attempt(service, 1, success=bool(number % 2))
        except ValueError as error:
            assert "attempt_id" in str(error)
            return False
        return True

    with ThreadPoolExecutor(max_workers=8) as pool:
        outcomes = list(pool.map(record, range(32)))
    assert sum(outcomes) == 16
    assert service.get_lesson("verify")["attempt_count"] == 2
    assert service.ledger.verify_integrity()
