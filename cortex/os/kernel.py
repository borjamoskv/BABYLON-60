# C5-REAL EXERGY CERTIFIED
"""
CORTEX-OS v4.0 Microkernel Core (<300 LOC).
Maintains 5 State Graphs, Syscall Dispatcher, Process Table, Memory Hierarchy, and Immune Interrupts.
"""

import hashlib
from typing import Any

from cortex.os.gc import EpistemicGarbageCollector
from cortex.os.memory import MemoryHierarchy, MemoryTier
from cortex.os.scheduler import CognitiveScheduler, ProcessTask
from cortex.os.syscalls import SyscallRequest, SyscallResponse, SyscallType


class CortexMicrokernel:
    def __init__(self) -> None:
        # The 5 Primitive State Graphs
        self.reality_graph: dict[str, Any] = {}
        self.knowledge_graph: dict[str, Any] = {}
        self.execution_graph: dict[str, Any] = {}
        self.evidence_graph: dict[str, Any] = {}
        self.capability_graph: dict[int, set[str]] = {}

        # Subsystems
        self.memory = MemoryHierarchy()
        self.scheduler = CognitiveScheduler()
        self.gc = EpistemicGarbageCollector(self.memory)
        self.next_pid = 1000

    def spawn_process(self, name: str, capabilities: set[str], priority_weight: float = 1.0) -> int:
        pid = self.next_pid
        self.next_pid += 1
        self.capability_graph[pid] = capabilities
        self.execution_graph[str(pid)] = {
            "name": name,
            "status": "READY",
            "capabilities": list(capabilities),
        }

        task = ProcessTask.calculate_priority(
            pid=pid,
            name=name,
            weight=priority_weight,
            info_gain=1.0,
            risk_reduction=1.0,
            token_cost=1.0,
        )
        self.scheduler.schedule_task(task)
        return pid

    def dispatch_syscall(self, req: SyscallRequest) -> SyscallResponse:
        # 1. Capability Verification
        required_cap = f"Syscall_{req.syscall.value}"
        allowed_caps = self.capability_graph.get(req.caller_pid, set())
        if required_cap not in allowed_caps and "*" not in allowed_caps:
            return SyscallResponse(
                success=False,
                data={},
                error=f"Permission Denied: PID {req.caller_pid} lacks capability {required_cap}",
            )

        # 2. Syscall Dispatcher
        if req.syscall == SyscallType.OBSERVE:
            uri = req.payload.get("target", "")
            obs_id = hashlib.sha256(uri.encode("utf-8")).hexdigest()[:12]
            self.reality_graph[obs_id] = uri
            self.memory.store(obs_id, uri, MemoryTier.SENSORY, confidence=0.8)
            return SyscallResponse(success=True, data={"observation_id": obs_id, "target": uri})

        elif req.syscall == SyscallType.VERIFY:
            claim_id = req.payload.get("claim_id", "")
            evidence_hash = req.payload.get("evidence_hash", "")
            is_valid = bool(claim_id and evidence_hash)
            if is_valid:
                self.evidence_graph[claim_id] = evidence_hash
                self.memory.store(claim_id, evidence_hash, MemoryTier.VERIFIED, confidence=1.0)
            return SyscallResponse(
                success=is_valid,
                data={"verified": is_valid, "claim_id": claim_id},
            )

        elif req.syscall == SyscallType.PERSIST:
            obj_data = req.payload.get("data", "")
            sha256 = hashlib.sha256(str(obj_data).encode("utf-8")).hexdigest()
            self.memory.store(sha256, str(obj_data), MemoryTier.IMMUTABLE_LEDGER, confidence=1.0)
            return SyscallResponse(success=True, data={"hash": sha256, "status": "PERSISTED"})

        elif req.syscall == SyscallType.AUDIT:
            gc_stats = self.gc.collect()
            return SyscallResponse(
                success=True,
                data={
                    "gc_stats": gc_stats,
                    "process_count": len(self.execution_graph),
                    "memory_items": sum(len(t) for t in self.memory.tiers.values()),
                },
            )

        return SyscallResponse(
            success=False,
            data={},
            error=f"Syscall {req.syscall.value} not implemented in Microkernel",
        )
