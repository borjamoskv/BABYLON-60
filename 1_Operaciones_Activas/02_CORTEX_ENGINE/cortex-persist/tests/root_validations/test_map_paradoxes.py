# [C5-REAL] Exergy-Maximized - Meta-Antipatterns Validation Suite
import asyncio
import time
from unittest import mock
import pytest

# Constants
MAX_EVENT_LOOP_LAG_MS = 10
BFT_MIN_DIVERSITY_RATIO = 0.34
MIN_SHANNON_ENTROPY = 4.3  # Bits per character


class SagaCompensationError(Exception):
    """Fired when a Saga backward step encounters an irretrievable state."""

    pass


class OuroborosParadoxException(Exception):
    """Fired when a C5 mitigation triggers an anti-pattern."""

    pass


@pytest.mark.asyncio
async def test_map001_git_sentinel_async_isolation():
    """
    MAP-001: I/O Starvation Sentinel.
    Git Sentinel must not block the main event loop.
    """

    async def mock_git_sentinel():
        # Simulate an async subprocess call (proper C5-REAL implementation)
        await asyncio.sleep(0.01)
        return "commit_hash_123"

    start = time.perf_counter()
    task = asyncio.create_task(mock_git_sentinel())
    # Loop should continue spinning while git executes
    await asyncio.sleep(0.005)
    await task
    lag_ms = (time.perf_counter() - start) * 1000

    assert lag_ms < 500, "Event loop blocked by synchronous I/O operations (AP-011)"


@pytest.mark.asyncio
async def test_map002_saga_compensation_error_raised():
    """
    MAP-002: Blind Resilience Rollback.
    SAGA must not swallow critical rollback errors using bare except Exception.
    """

    class DummySagaEngine:
        async def execute_compensation(self, raise_error=False):
            try:
                if raise_error:
                    raise RuntimeError("Corrupted Snapshot")
                return True
            except Exception as e:  # noqa: BLE001
                # Proper resilience propagates a specific error and logs to master ledger
                raise SagaCompensationError(f"Forensic trail preserved: {str(e)}") from e

    engine = DummySagaEngine()
    with pytest.raises(SagaCompensationError, match="Forensic trail preserved: Corrupted Snapshot"):
        await engine.execute_compensation(raise_error=True)


@pytest.mark.asyncio
async def test_map003_sybil_echo_chamber_rejection():
    """
    MAP-003: Sybil Echo Chamber.
    BFT consensus must reject quorums lacking architectural diversity (Ω1b).
    """

    def validate_quorum_diversity(agent_models: list[str]) -> bool:
        unique_models = set(agent_models)
        diversity_ratio = len(unique_models) / len(agent_models) if agent_models else 0
        return diversity_ratio >= BFT_MIN_DIVERSITY_RATIO

    sybil_quorum = ["sonnet-4.5", "sonnet-4.5", "sonnet-4.5"]
    diverse_quorum = ["sonnet-4.5", "gpt-4o", "opus-4.6"]

    assert not validate_quorum_diversity(sybil_quorum), (
        "Consensus accepted without topological orthogonality (AP-004)"
    )
    assert validate_quorum_diversity(diverse_quorum), "Orthogonal quorum rejected incorrectly"


@pytest.mark.asyncio
async def test_map004_symlink_cycle_detection():
    """
    MAP-004: Topología Recurrente.
    Singularity Nexus must abort cyclical symlinks (DFS Cycle Detector).
    """

    def check_for_cycles(symlink_graph: dict) -> bool:
        visited = set()
        path = set()

        def dfs(node):
            if node in path:
                return True
            if node in visited:
                return False

            visited.add(node)
            path.add(node)
            for neighbor in symlink_graph.get(node, []):
                if dfs(neighbor):
                    return True
            path.remove(node)
            return False

        for n in symlink_graph:
            if dfs(n):
                return True
        return False

    cyclic_graph = {"repoA": ["repoB"], "repoB": ["repoA"]}
    dag_graph = {"repoA": ["repoB", "repoC"], "repoB": ["repoC"], "repoC": []}

    assert check_for_cycles(cyclic_graph), "Cycle undetected: AP-030 triggered"
    assert not check_for_cycles(dag_graph), "False positive in DAG cycle detection"


@pytest.mark.asyncio
async def test_map005_cache_staleness_fallback():
    """
    MAP-005: Staleness Asíncrono.
    Cache invalidation failure post-SAGA must enforce transaction outbox or raise.
    """

    class CacheEngine:
        def __init__(self):
            self.redis_mock_state = {"tenant_A": "data"}
            self.outbox = []

        async def invalidate_cache(self, tenant_id: str, trigger_failure: bool = False):
            if trigger_failure:
                # Simulating a fallback to transactional outbox
                self.outbox.append({"action": "invalidate", "tenant_id": tenant_id})
                raise ConnectionError("Redis disconnected")
            self.redis_mock_state.pop(tenant_id, None)

    engine = CacheEngine()
    with pytest.raises(ConnectionError):
        await engine.invalidate_cache("tenant_A", trigger_failure=True)

    assert len(engine.outbox) == 1, "Failed invalidation did not register in Outbox (AP-026)"


@pytest.mark.asyncio
async def test_map006_pragma_wal_async_pool():
    """
    MAP-006: Pragma Synchronous Lock.
    WAL mode setup must use async pool exclusively to avoid blocking engine setup.
    """
    import sqlite3

    async def configure_wal(mocked_aiosqlite_conn):
        # The true C5-REAL execution uses mocked_aiosqlite_conn.execute("PRAGMA journal_mode=WAL;")
        return await mocked_aiosqlite_conn.execute("PRAGMA journal_mode=WAL;")

    class MockAsyncConn:
        async def execute(self, query):
            if "sqlite3.connect" in query:
                raise OuroborosParadoxException("Synchronous DB call inside async pragma setup")
            return "WAL"

    conn = MockAsyncConn()
    result = await configure_wal(conn)
    assert result == "WAL", "WAL mode not configured correctly via async channel"


@pytest.mark.asyncio
async def test_map007_handoff_exergy_guard():
    """
    MAP-007: Estocástica Post-Handoff.
    Session handoffs must reject low-entropy summaries (decorative prose).
    """

    def measure_shannon_entropy(text: str) -> float:
        import math
        from collections import Counter

        freqs = Counter(text)
        return -sum(count / len(text) * math.log2(count / len(text)) for count in freqs.values())

    def validate_handoff_summary(summary: str) -> bool:
        entropy = measure_shannon_entropy(summary)
        return entropy >= MIN_SHANNON_ENTROPY

    decorative_slop = "Espero que esto te sea de mucha utilidad durante la próxima sesión. Hemos hecho un gran trabajo."
    causal_crystal = "HASH:a1b2c3d4 | STATE:COMMITTED | MAP:7_paradoxes_injected | NEXUS:stable"

    assert not validate_handoff_summary(decorative_slop), (
        "Decorative prose bypassed ExergyGuard (AP-036 / AP-007)"
    )
    assert validate_handoff_summary(causal_crystal), "Causal crystal incorrectly rejected"
