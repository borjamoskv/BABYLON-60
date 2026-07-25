import pytest

from ultrathink.ultrathink_scheduler import ConsensusEngineStub, propose_with_backoff


class FailingEngine(ConsensusEngineStub):
    def __init__(self, fail_count: int = 2) -> None:
        self._fail_count = fail_count
        self._calls = 0

    def propose(self, payload: bytes) -> None:
        self._calls += 1
        if self._calls <= self._fail_count:
            raise RuntimeError(f"simulated failure #{self._calls}")


@pytest.mark.asyncio
async def test_propose_succeeds_immediately() -> None:
    engine = ConsensusEngineStub()
    result = await propose_with_backoff(engine, b"test_payload", task_id=0)
    assert result is True


@pytest.mark.asyncio
async def test_propose_retries_on_failure() -> None:
    engine = FailingEngine(fail_count=2)
    result = await propose_with_backoff(engine, b"retry_payload", task_id=1)
    assert result is True
    assert engine._calls == 3


@pytest.mark.asyncio
async def test_propose_exhausts_retries() -> None:
    engine = FailingEngine(fail_count=100)
    result = await propose_with_backoff(engine, b"fail_payload", task_id=2)
    assert result is False


def test_consensus_engine_stub_propose_noop() -> None:
    engine = ConsensusEngineStub()
    engine.propose(b"noop")
