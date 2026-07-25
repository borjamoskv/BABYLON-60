# C5-REAL EXERGY CERTIFIED
"""
Unit test suite for CORTEX-OS v4.0 Microkernel Runtime.
"""

from cortex.os.kernel import CortexMicrokernel
from cortex.os.memory import MemoryTier
from cortex.os.scheduler import CognitiveScheduler, ProcessTask
from cortex.os.syscalls import SyscallRequest, SyscallType


def test_cortex_microkernel_spawn_and_syscalls() -> None:
    kernel = CortexMicrokernel()
    pid = kernel.spawn_process(
        "AuditorAgent", capabilities={"Syscall_OBSERVE", "Syscall_VERIFY", "Syscall_AUDIT"}
    )
    assert pid == 1000
    assert str(pid) in kernel.execution_graph

    # Test Syscall OBSERVE
    obs_req = SyscallRequest(
        syscall=SyscallType.OBSERVE,
        caller_pid=pid,
        payload={"target": "file:///tmp/audit_payload.json"},
    )
    res = kernel.dispatch_syscall(obs_req)
    assert res.success is True
    assert "observation_id" in res.data

    # Test Syscall VERIFY
    ver_req = SyscallRequest(
        syscall=SyscallType.VERIFY,
        caller_pid=pid,
        payload={"claim_id": "CLM_001", "evidence_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"},
    )
    res_ver = kernel.dispatch_syscall(ver_req)
    assert res_ver.success is True
    assert res_ver.data["verified"] is True
    assert kernel.memory.get("CLM_001") is not None

    # Test Permission Denied Syscall
    denied_req = SyscallRequest(
        syscall=SyscallType.PERSIST,
        caller_pid=pid,
        payload={"data": "unauthorized_write"},
    )
    res_denied = kernel.dispatch_syscall(denied_req)
    assert res_denied.success is False
    assert "Permission Denied" in res_denied.error


def test_epistemic_memory_promotion_and_gc() -> None:
    kernel = CortexMicrokernel()
    kernel.memory.store("temp_1", "junk_data", MemoryTier.SENSORY, confidence=0.1)
    kernel.memory.store("temp_2", "valid_data", MemoryTier.WORKING, confidence=0.9)
    kernel.memory.store("temp_3", "valid_data", MemoryTier.WORKING, confidence=0.9)  # Duplicate sha256

    stats = kernel.gc.collect()
    assert stats["purged_sensory"] == 1
    assert stats["deduplicated_working"] == 1


def test_cognitive_scheduler_priority_queue() -> None:
    scheduler = CognitiveScheduler()

    t1 = ProcessTask.calculate_priority(
        pid=1, name="LowPriority", weight=1.0, info_gain=1.0, risk_reduction=1.0, token_cost=10.0
    )
    t2 = ProcessTask.calculate_priority(
        pid=2, name="HighPriority", weight=10.0, info_gain=5.0, risk_reduction=5.0, token_cost=1.0
    )

    scheduler.schedule_task(t1)
    scheduler.schedule_task(t2)

    nxt = scheduler.next_task()
    assert nxt is not None
    assert nxt.pid == 2  # HighPriority task dispatched first
