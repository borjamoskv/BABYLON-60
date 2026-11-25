"""Runner scheduling fixtures; these tests make no inference or efficacy claims."""

import asyncio
from pathlib import Path
import subprocess
import sys
from typing import cast

import pytest

from babylon60.cognitive_pilot import __main__ as runner
from babylon60.cognitive_pilot import execution, store


@pytest.fixture
def prepared(tmp_path: Path) -> Path:
    directory = tmp_path / "runner"
    runner.register(
        directory,
        {
            "backend": "local_mlx",
            "model": "FIXTURE-NOT-EXECUTED",
            "endpoint": "http://127.0.0.1:8080/v1/chat/completions",
            "max_tokens": 6000,
            "max_calls": 2,
            "timeout": 120,
            "temperature": 0,
            "memory_bytes": 2048,
        },
        42,
        1,
        12000,
    )
    return directory


@pytest.fixture
def synthetic_provider(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    counts = {"active": 0, "maximum": 0, "calls": 0}

    async def call(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        counts["active"] += 1
        counts["maximum"] = max(counts["maximum"], counts["active"])
        counts["calls"] += 1
        await asyncio.sleep(0.001)
        counts["active"] -= 1
        self.calls += 1
        self.tokens += 6000
        source = "def solve(p):\n    return 0"
        return {
            "action": "final",
            "source": source,
            "candidates": [{"source": source, "mechanism": "fixture constant"}],
            "selected": 0,
            "memory": "fixture memory",
        }

    async def evaluate(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
        return {"quality": 0.0, "passed": 0, "total": len(tests), "source_digest": store.digest(source)}

    monkeypatch.setattr(execution.Provider, "call", call)
    monkeypatch.setattr(execution, "evaluate", evaluate)
    return counts


def test_reservations_parallelism_and_resume(prepared: Path, synthetic_provider: dict[str, int]) -> None:
    summary = asyncio.run(runner.run_batch(prepared))
    assert summary["attempted_now"] == 2
    assert summary["provider_reported_tokens"] == summary["total_token_cap"] == 12000
    assert summary["stop"] == "total token reservation cap reached"
    assert synthetic_provider == {"active": 0, "maximum": 2, "calls": 2}
    assert asyncio.run(runner.run_batch(prepared))["attempted_now"] == 0
    assert synthetic_provider["calls"] == 2


def test_orphan_claim_blocks_before_inference(prepared: Path, synthetic_provider: dict[str, int]) -> None:
    plan = store.load(prepared)
    run = cast(list[dict[str, object]], plan["runs"])[0]
    store.write(prepared / "claims" / f"{run['id']}.json", {"interrupted": True})
    with pytest.raises(store.PilotError, match="Orphan claim"):
        asyncio.run(runner.run_batch(prepared))
    assert synthetic_provider["calls"] == 0


def test_provider_block_stops_current_batch_and_subsequent_resume(
    prepared: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = 0

    async def blocked(self: execution.Provider, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        nonlocal calls
        calls += 1
        raise RuntimeError("fixture provider unavailable")

    monkeypatch.setattr(execution.Provider, "call", blocked)
    assert asyncio.run(runner.run_batch(prepared))["attempted_now"] == 2
    assert asyncio.run(runner.run_batch(prepared))["stop"] == "previously blocked run requires investigation"
    assert calls == 2


def test_altered_registration_rejected_before_inference(prepared: Path, synthetic_provider: dict[str, int]) -> None:
    value = store.read(prepared / "execution.json")
    value["total_token_cap"] = 1000000
    store.write(prepared / "execution.json", value, replace=True)
    with pytest.raises(store.PilotError, match="registration digest"):
        asyncio.run(runner.run_batch(prepared))
    assert synthetic_provider["calls"] == 0


def test_cli_report_is_offline_and_pending(prepared: Path) -> None:
    result = subprocess.run(
        [sys.executable, "-m", "babylon60.cognitive_pilot", "report", str(prepared)],
        capture_output=True,
        timeout=30,
        check=True,
    )
    report = store.decode(result.stdout)
    assert report["planned_runs"] == 120
    assert report["recorded_runs"] == 0
    assert all(store.mapping(domain)["status"] == "pending" for domain in store.mapping(report["domains"]).values())
