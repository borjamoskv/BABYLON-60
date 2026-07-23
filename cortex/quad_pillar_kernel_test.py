"""
Unit tests for C5-REAL Quad-Pillar Kernel (Ω159).
Verifies System, Orchestration, Memory, and Determinism pillars.
"""

import os
import pytest
import asyncio
import tempfile
from cortex.quad_pillar_kernel import (
    QuadPillarKernel,
    SystemPillar,
    OrchestrationPillar,
    MemoryPillar,
    DeterminismPillar,
    QuadPillarException,
    CausalHierarchyError,
    QuadPillarIdempotencyError,
)

@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    yield db_path
    if os.path.exists(db_path):
        os.remove(db_path)

def test_pillar_1_system():
    sys_p = SystemPillar()
    state = sys_p.inspect_system_state()
    assert state["os_type"] in ["Darwin", "Linux", "Windows"]
    assert state["pid"] > 0
    assert "timestamp_ns" in state
    assert "rss_memory" in state
    assert isinstance(state["rss_memory"], int)

def test_pillar_1_sovereignty_fail():
    sys_p = SystemPillar()
    with pytest.raises(QuadPillarException, match="Sovereignty Violation"):
        sys_p.verify_environment_sovereignty("NON_EXISTENT_C5_KEY_12345")

def test_pillar_2_orchestration_async(temp_db):
    orch = OrchestrationPillar(db_file=temp_db)
    hash_res = asyncio.run(orch.dispatch_task({"task_id": "test_async"}))
    assert len(hash_res) == 64  # SHA3-256 length

def test_pillar_2_orchestration_fallback_on_429(temp_db):
    orch = OrchestrationPillar(db_file=temp_db)
    hash_res = asyncio.run(orch.dispatch_task({"task_id": "test_fallback"}, simulate_rate_limit=True))
    assert len(hash_res) == 64

def test_pillar_3_memory_sharding():
    mem = MemoryPillar()
    shard_rules = mem.get_shard_rules("L15_Diamond")
    assert "Ω159" in shard_rules
    assert "Ω156" in shard_rules
    assert "Ω1" in shard_rules

def test_pillar_3_memory_4tier_schema():
    mem = MemoryPillar()
    entry = mem.record_4tier_entry(
        evidence={"measurement": 42.0, "hash": "abc123sha3"},
        repo_state={"branch": "master", "commit": "af6211fa2"},
        recorded_hypothesis={"model": "MCTS_BFT", "confidence": "C5"},
        governance={"bft_threshold": 3},
    )
    assert entry["tier_1_evidence"]["measurement"] == 42.0
    assert entry["tier_2_repository_state"]["branch"] == "master"

def test_pillar_4_determinism_disk_hash(temp_db):
    det = DeterminismPillar(db_file=temp_db)
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp:
        tmp.write(b"C5-REAL DISK GROUND TRUTH")
        tmp_path = tmp.name

    try:
        file_hash = det.verify_disk_file_hash(tmp_path)
        assert len(file_hash) == 64
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

def test_pillar_4_idempotency_lock(temp_db):
    orch = OrchestrationPillar(db_file=temp_db)
    det = DeterminismPillar(db_file=temp_db)
    
    # Dispatch a task to create a ledger entry
    payload_hash = asyncio.run(orch.dispatch_task({"task_id": "idem_test"}))
    
    # Verify that trying to run or check this hash raises the lock
    with pytest.raises(QuadPillarIdempotencyError, match="Idempotency Lock"):
        det.check_idempotency_lock(payload_hash)
        
    # Checking an unknown hash should pass
    assert det.check_idempotency_lock("00000000000000000000000000") is True

def test_pillar_4_causal_hierarchy(temp_db):
    det = DeterminismPillar(db_file=temp_db)
    assert det.validate_causal_hierarchy(
        topology="cortex/quad_pillar_kernel.py",
        mechanism="SIGABRT on invalid memory access",
        etiology="Compiler VFS buffer depletion under race condition",
    ) is True

    with pytest.raises(CausalHierarchyError):
        det.validate_causal_hierarchy(
            topology="same", mechanism="same", etiology="different"
        )

def test_unified_quad_pillar_kernel(temp_db):
    kernel = QuadPillarKernel(db_file=temp_db)
    audit = kernel.audit_quad_pillars()
    assert audit["pillar_1_system"]["status"] == "C5_REAL_ACTIVE"
    assert audit["pillar_2_orchestration"]["status"] == "WAL_ACTIVE"
    assert audit["pillar_3_memory"]["status"] == "SHARDING_ACTIVE"
    assert audit["pillar_4_determinism"]["status"] == "SHA3_256_ACTIVE"
