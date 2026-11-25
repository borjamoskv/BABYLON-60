"""Synthetic pilot tests: no provider network or generated candidate is executed."""

import asyncio
from pathlib import Path
import os
import random
import sys
from typing import cast

import pytest
from blake3 import blake3

from babylon60.cognitive_pilot import bank, execution, store
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator


@pytest.fixture
def config() -> dict[str, object]:
    return {
        "backend": "local_mlx",
        "model": "TEST-NOT-EXECUTED",
        "endpoint": "http://127.0.0.1:8080/v1/chat/completions",
        "max_tokens": 256,
        "max_calls": 2,
        "timeout": 10,
        "temperature": 0,
        "memory_bytes": 128,
    }


@pytest.fixture
def prepared(tmp_path: Path, config: dict[str, object]) -> Path:
    directory = tmp_path / "cognitive-fixture"
    store.prepare(directory, config, repetitions=1)
    return directory


def final() -> dict[str, object]:
    source = "def solve(p):\n    return 0"
    return {
        "action": "final",
        "source": source,
        "candidates": [{"source": source, "mechanism": "fixture"}],
        "selected": 0,
        "memory": "TEST FIXTURE",
    }


def run_for(directory: Path, stage: str = "quality") -> tuple[dict[str, object], dict[str, object]]:
    plan = store.load(directory)
    run = next(r for r in cast(list[dict[str, object]], plan["runs"]) if r["stage"] == stage)
    return plan, run


@pytest.mark.parametrize(
    "name,p,expected",
    [
        ("idempotency", {"events": [["a", 3], ["a", 9], ["b", -2]]}, 1),
        ("backoff", {"count": 4, "base": 2, "cap": 5}, [2, 4, 5, 5]),
        ("cache", {"now": 5, "entries": [["equal", 5], ["live", 6]]}, ["live"]),
        ("checkpoint", {"seen": ["a"], "events": ["a", "b", "b", "c"]}, ["b", "c"]),
        ("dependencies", {"nodes": ["a", "b", "c"], "edges": [["c", "a"]]}, ["b", "c", "a"]),
        ("dependencies", {"nodes": ["a", "b"], "edges": [["a", "b"], ["b", "a"]]}, None),
        ("contract", {"required": ["a"], "rows": [{"a": 0}, {"a": False}, {"a": None}, {}]}, [0, 1]),
        ("intervals", {"ranges": [[3, 4], [1, 3], [-1, 0]]}, [[-1, 0], [1, 4]]),
        ("allocation", {"weights": [0, 2, 2], "values": [3, 4, 9], "capacity": 2}, 12),
        ("window", {"values": [-4, -2, -3], "width": 2}, [-2, -2]),
        ("window", {"values": [], "width": 2}, []),
        ("offline_merge", {"records": [["k", 1, "a"], ["k", 2, "z"], ["k", 2, "b"]]}, [["k", 2, "b"]]),
        ("packing", {"weights": [4, 4, 2], "limit": 6}, 2),
        ("packing", {"weights": [], "limit": 6}, 0),
        (
            "routing",
            {
                "nodes": ["a", "b", "c"],
                "edges": [["a", "c", 5], ["a", "b", 0], ["b", "c", 2]],
                "source": "a",
                "target": "c",
            },
            2,
        ),
        ("routing", {"nodes": ["a", "b"], "edges": [], "source": "a", "target": "b"}, None),
    ],
)
def test_oracle_boundaries(name: str, p: dict[str, object], expected: object) -> None:
    assert bank.oracle(name, p) == expected


def test_frozen_schedule_and_hidden_bank(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan = store.load(prepared)
    assert len(cast(list[object], plan["runs"])) == 120
    original = bank.inputs

    def changed(name: str, rng: object, index: int) -> dict[str, object]:
        value = original(name, cast(random.Random, rng), index)
        if name == "backoff" and index == 3:
            value["cap"] = 999
        return value

    monkeypatch.setattr(bank, "inputs", changed)
    with pytest.raises(store.PilotError, match="Task bank changed"):
        store.load(prepared)


def test_receipt_digest_uses_blake3() -> None:
    assert store.digest({"fixture": True}) == blake3(store.canonical({"fixture": True})).hexdigest()


def test_nonfinite_and_oversized_numbers_are_validation_errors() -> None:
    for value in (float("nan"), float("inf"), 10**1000):
        with pytest.raises(store.PilotError):
            store.number(value, 0, 100, "fixture")


def test_fresh_receipt_is_fsynced(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = os.fsync
    seen: list[int] = []

    def sync(fd: int) -> None:
        seen.append(fd)
        original(fd)

    monkeypatch.setattr(os, "fsync", sync)
    store.write(tmp_path / "receipt.json", {"fixture": True})
    assert len(seen) >= 2  # Both receipt bytes and directory entry.


def test_read_opens_nonblocking_before_regular_file_check(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "receipt.json"
    store.write(path, {})
    original = os.open
    flags_seen: list[int] = []

    def open_file(path: str | os.PathLike[str], flags: int, mode: int = 0o777, *, dir_fd: int | None = None) -> int:
        flags_seen.append(flags)
        return original(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(os, "open", open_file)
    assert store.read(path) == {}
    assert any(flags & os.O_NONBLOCK for flags in flags_seen)


def test_store_rejects_symlink_parent(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (tmp_path / "linked").symlink_to(outside, target_is_directory=True)
    with pytest.raises((store.PilotError, OSError)):
        store.write(tmp_path / "linked" / "receipt.json", {})
    assert not (outside / "receipt.json").exists()


def test_json_rejects_duplicate_nonfinite_and_deep_values(tmp_path: Path) -> None:
    path = tmp_path / "input.json"
    for text in ('{"x":1,"x":2}', '{"x":NaN}', '{"x":' + "[" * 2000 + "0" + "]" * 2000 + "}"):
        path.write_text(text)
        with pytest.raises(store.PilotError):
            store.read(path)


def test_evaluate_nonfinite_output_is_failed_candidate(monkeypatch: pytest.MonkeyPatch) -> None:
    async def synthetic(*args: object, **kwargs: object) -> dict[str, object]:
        return {"is_valid": True, "tool_output": {"result": [float("nan")]}}

    monkeypatch.setattr(McpSandboxValidator, "execute_and_detonate_mcp", synthetic)
    grade = asyncio.run(execution.evaluate("def solve(p):\n    return 0", [{"input": {}, "expected": 0}]))
    assert grade["quality"] == 0


def test_evaluate_rejects_empty_cases_before_dispatch(monkeypatch: pytest.MonkeyPatch) -> None:
    async def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("No sandbox dispatch expected")

    monkeypatch.setattr(McpSandboxValidator, "execute_and_detonate_mcp", forbidden)
    with pytest.raises(store.PilotError):
        asyncio.run(execution.evaluate("def solve(p):\n    return 0", []))


def test_run_validates_membership_before_provider(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("No provider call expected")

    monkeypatch.setattr(execution.Provider, "call", forbidden)
    plan, run = run_for(prepared)
    run = {**run, "id": "../../escaped"}
    with pytest.raises(store.PilotError, match="scheduled"):
        asyncio.run(execution.run_one(prepared, plan, run))


def test_run_success_is_bound_and_cannot_rerun(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def provider(*args: object, **kwargs: object) -> dict[str, object]:
        return final()

    async def evaluate(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
        return {"quality": 100.0, "passed": len(tests), "total": len(tests), "source_digest": store.digest(source)}

    monkeypatch.setattr(execution.Provider, "call", provider)
    monkeypatch.setattr(execution, "evaluate", evaluate)
    plan, run = run_for(prepared)
    result = asyncio.run(execution.run_one(prepared, plan, run))
    assert result["status"] == "complete"
    stored = store.read(prepared / "runs" / f"{run['id']}.json")
    assert stored == result
    with pytest.raises(store.PilotError, match="recorded"):
        asyncio.run(execution.run_one(prepared, plan, run))


def test_early_evaluation_failure_keeps_failed_receipt(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    async def provider(*args: object, **kwargs: object) -> dict[str, object]:
        return final()

    async def bad_output(*args: object, **kwargs: object) -> dict[str, object]:
        raise ValueError("nonfinite candidate output")

    monkeypatch.setattr(execution.Provider, "call", provider)
    monkeypatch.setattr(execution, "evaluate", bad_output)
    plan, run = run_for(prepared)
    result = asyncio.run(execution.run_one(prepared, plan, run))
    assert result["status"] == "failed"
    assert store.read(prepared / "runs" / f"{run['id']}.json") == result


@pytest.fixture
def synthetic_runtime(monkeypatch: pytest.MonkeyPatch) -> None:
    async def provider(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        self.calls += 1
        self.tokens += 64
        return final()

    async def evaluator(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
        return {"quality": 100.0, "passed": len(tests), "total": len(tests), "source_digest": store.digest(source)}

    monkeypatch.setattr(execution.Provider, "call", provider)
    monkeypatch.setattr(execution, "evaluate", evaluator)


@pytest.mark.parametrize("item", bank.FAMILIES, ids=lambda item: item.name)
@pytest.mark.parametrize("stage", bank.STAGES)
def test_hidden_inputs_are_distinct_and_not_public(item: bank.Family, stage: str) -> None:
    public = {store.canonical(case["input"]) for case in bank.cases(item.name, stage, 42)}
    hidden = [store.canonical(case["input"]) for case in bank.cases(item.name, stage, 42, hidden=True)]
    assert len(set(hidden)) == len(hidden) == 27
    assert not public.intersection(hidden)


@pytest.mark.parametrize(
    "grade",
    [
        {"quality": 100.0, "passed": 0, "total": 27},
        {"quality": 100.0, "passed": -1, "total": 27},
        {"quality": 100.0, "passed": 27, "total": 3},
        {"quality": 100.0, "passed": True, "total": 27},
        {"quality": 100.0},
    ],
)
def test_review_rejects_inconsistent_grades(
    prepared: Path,
    synthetic_runtime: None,
    grade: dict[str, object],
) -> None:
    from babylon60.cognitive_pilot.review import checked_record

    plan, run = run_for(prepared)
    record = asyncio.run(execution.run_one(prepared, plan, run))
    record["grades"] = [{**grade, "source_digest": store.digest(final()["source"])}]
    record.pop("record_digest")
    record["record_digest"] = store.digest(record)
    store.write(prepared / "runs" / f"{run['id']}.json", record, replace=True)
    with pytest.raises(store.PilotError):
        checked_record(prepared, plan, run)


def test_blind_reviews_and_complete_report_flow(prepared: Path, synthetic_runtime: None) -> None:
    from babylon60.cognitive_pilot import review, scoring

    plan = store.load(prepared)

    async def all_runs() -> None:
        for run in cast(list[dict[str, object]], plan["runs"]):
            assert (await execution.run_one(prepared, plan, run))["status"] == "complete"

    asyncio.run(all_runs())
    assert review.blind(prepared, plan)["packets"] == 24
    assert review.blind(prepared, plan)["packets"] == 24  # Idempotent packet registration.
    first_review: Path | None = None
    for folder in (prepared / "blind").iterdir():
        packet = store.read(folder / "packet.json")
        for judge in range(1, 4):
            path = folder / f"review{judge}.json"
            store.write(
                path,
                {
                    "packet_digest": store.digest(packet),
                    "reviewer_id": f"judge-{judge}",
                    "independent": True,
                    "families": ["fixture"],
                    "originality": 1,
                    "critical_violation": False,
                    "evidence": "Synthetic review fixture only",
                },
            )
            first_review = first_review or path
    report = scoring.report(prepared, plan, bootstrap=100)
    assert report["completed_runs"] == report["recorded_runs"] == report["planned_runs"] == 120
    assert report["pending"] == []
    for domain in cast(dict[str, dict[str, object]], report["domains"]).values():
        assert domain["score"] is not None
        assert domain["bootstrap_complete_samples"] == 100
    assert first_review is not None
    duplicate = store.read(first_review)
    duplicate["reviewer_id"] = " JUDGE-2 "
    store.write(first_review, duplicate, replace=True)
    with pytest.raises(store.PilotError, match="distinct"):
        scoring.report(prepared, plan, bootstrap=100)


def test_failed_activation_is_censored(prepared: Path) -> None:
    from babylon60.cognitive_pilot import scoring

    plan = store.load(prepared)
    for run in cast(list[dict[str, object]], plan["runs"]):
        if run["stage"] != "activation":
            continue
        record: dict[str, object] = {
            "run": run,
            "plan_digest": plan["plan_digest"],
            "status": "failed",
            "activation_seconds": "untrusted",
            "calls": 0,
            "tokens": 0,
            "elapsed": 1.0,
        }
        record["record_digest"] = store.digest(record)
        store.write(prepared / "runs" / f"{run['id']}.json", record)
    report = scoring.report(prepared, plan, bootstrap=100)
    for domain in cast(dict[str, dict[str, object]], report["domains"]).values():
        assert cast(dict[str, object], domain["effects"])["activation"] is None


def test_claim_blocks_repeated_attempt_before_provider(prepared: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    plan, run = run_for(prepared)
    store.write(prepared / "claims" / f"{run['id']}.json", {})

    async def forbidden(*args: object, **kwargs: object) -> dict[str, object]:
        raise AssertionError("No second provider dispatch expected")

    monkeypatch.setattr(execution.Provider, "call", forbidden)
    with pytest.raises(store.PilotError, match="attempt already recorded"):
        asyncio.run(execution.run_one(prepared, plan, run))


def test_store_replace_and_collision_are_atomic(tmp_path: Path) -> None:
    path = tmp_path / "receipt.json"
    store.write(path, {"first": True})
    with pytest.raises(FileExistsError):
        store.write(path, {"second": True})
    assert store.read(path) == {"first": True}
    store.write(path, {"second": True}, replace=True)
    assert store.read(path) == {"second": True}
    assert not list(tmp_path.glob(".receipt-*"))


def test_fifo_is_rejected_without_a_writer(tmp_path: Path) -> None:
    import subprocess

    path = tmp_path / "fifo"
    os.mkfifo(path)
    script = (
        "from pathlib import Path; from babylon60.cognitive_pilot.store import read, PilotError\n"
        f"try: read(Path({str(path)!r}))\n"
        "except PilotError: pass\n"
        "else: raise AssertionError('FIFO accepted')"
    )
    subprocess.run([sys.executable, "-c", script], check=True, timeout=5, capture_output=True)


def test_activation_recheck_failure_cannot_leave_complete_status(
    prepared: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0
    evaluations = 0

    async def provider(*args: object, **kwargs: object) -> dict[str, object]:
        nonlocal calls
        calls += 1
        return {"action": "test", "source": final()["source"]} if calls == 1 else final()

    async def evaluator(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
        nonlocal evaluations
        evaluations += 1
        if evaluations == 3:
            raise ValueError("Synthetic activation recheck failure")
        return {"quality": 100.0, "passed": len(tests), "total": len(tests), "source_digest": store.digest(source)}

    monkeypatch.setattr(execution.Provider, "call", provider)
    monkeypatch.setattr(execution, "evaluate", evaluator)
    plan, run = run_for(prepared, "activation")
    result = asyncio.run(execution.run_one(prepared, plan, run))
    assert result["status"] == "failed"
    assert store.read(prepared / "runs" / f"{run['id']}.json") == result


@pytest.mark.skipif(sys.platform != "darwin", reason="Real OS-confinement backend requires macOS")
def test_real_sandbox_run_persists_grade_and_os_evidence(
    prepared: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Only the provider is synthetic; scaffold, process and OS boundary are real."""
    from babylon60.cognitive_pilot.review import checked_record

    source = "def solve(p):\n    return [min(p['cap'], p['base'] * 2**i) for i in range(p['count'])]"

    async def controlled_provider(*args: object, **kwargs: object) -> dict[str, object]:
        return {
            "action": "final",
            "source": source,
            "candidates": [{"source": source, "mechanism": "bounded arithmetic"}],
            "selected": 0,
            "memory": "",
        }

    monkeypatch.setattr(execution.Provider, "call", controlled_provider)
    plan = store.load(prepared)
    run = next(
        item
        for item in cast(list[dict[str, object]], plan["runs"])
        if item["family"] == "backoff" and item["stage"] == "quality"
    )
    record = asyncio.run(execution.run_one(prepared, plan, run))
    assert record["status"] == "complete", record
    grade = cast(list[dict[str, object]], record["grades"])[0]
    assert grade["quality"] == 100
    assert grade["passed"] == grade["total"] == 27
    assert grade["isolation_backend"] == "macos-seatbelt"
    evidence = store.mapping(grade["isolation_evidence"])
    assert evidence and all(value is True for value in evidence.values())
    assert checked_record(prepared, plan, run) == record


@pytest.mark.skipif(sys.platform != "darwin", reason="Real OS-confinement backend requires macOS")
def test_real_sandbox_candidate_cannot_read_external_canary(tmp_path: Path) -> None:
    canary = tmp_path / "outside-secret"
    canary.write_text("private-cognitive-test-canary")
    source = f"def solve(p):\n    from pathlib import Path\n    return Path({str(canary)!r}).read_text()"
    grade = asyncio.run(execution.evaluate(source, [{"input": {}, "expected": canary.read_text()}]))
    assert grade["quality"] == 0
    assert grade["error"] == "TOOL_ERROR", grade
    assert canary.read_text() == "private-cognitive-test-canary"
    assert "private-cognitive-test-canary" not in str(grade)


@pytest.mark.skipif(sys.platform != "darwin", reason="Real OS-confinement backend requires macOS")
def test_real_sandbox_candidate_loop_is_bounded() -> None:
    source = "def solve(p):\n    while True:\n        pass"
    grade = asyncio.run(execution.evaluate(source, [{"input": {}, "expected": 0}], timeout=2))
    assert grade["quality"] == 0
    assert grade["error"] == "TIMEOUT", grade


@pytest.mark.parametrize("failure", [RuntimeError("synthetic runtime failure"), OSError("synthetic IO failure")])
def test_infrastructure_failure_keeps_blocked_receipt(
    prepared: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure: Exception,
) -> None:
    async def failing(*args: object, **kwargs: object) -> dict[str, object]:
        raise failure

    monkeypatch.setattr(execution.Provider, "call", failing)
    plan, run = run_for(prepared)
    result = asyncio.run(execution.run_one(prepared, plan, run))
    assert result["status"] == "blocked"
    assert store.read(prepared / "runs" / f"{run['id']}.json") == result


def test_cancelled_attempt_records_block_and_propagates(
    prepared: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def cancelled(*args: object, **kwargs: object) -> dict[str, object]:
        raise asyncio.CancelledError

    monkeypatch.setattr(execution.Provider, "call", cancelled)
    plan, run = run_for(prepared)
    with pytest.raises(asyncio.CancelledError):
        asyncio.run(execution.run_one(prepared, plan, run))
    assert store.read(prepared / "runs" / f"{run['id']}.json")["status"] == "blocked"
