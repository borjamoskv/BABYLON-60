#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ DYNAMIC SUBAGENT LIFECYCLE | DOMAIN: agents.archi | STATE: C5-REAL
# ============================================================================
"""
Dynamic Subagent Lifecycle & Deadlock Mitigation Engine (INV_C5_TURING_CASTRATION).

Enforces:
  - Bounded finite-state transitions for autonomous subagents
  - Automated watchdog timer per state to prevent thermodynamic stalls/deadlocks
  - Immutable state transition logging for post-mortem forensics
"""

import os
import fcntl
import resource
import time
import json
import logging
from enum import Enum
from typing import Dict, List, Any, Optional, Callable


logger = logging.getLogger("02_EDIN_SWARMS.orchestrator.lifecycle")


class SubagentState(Enum):
    """Observable states of a sovereign subagent."""

    IDLE = "idle"
    PLANNING = "planning"
    EXECUTING = "executing"
    VERIFYING = "verifying"
    WAITING_FOR_INPUT = "waiting_for_input"
    COMPLETED = "completed"
    DEADLOCKED = "deadlocked"
    POISONED = "poisoned"


# Valid state transition graph
VALID_TRANSITIONS = {
    SubagentState.IDLE: {SubagentState.PLANNING, SubagentState.EXECUTING, SubagentState.POISONED},
    SubagentState.PLANNING: {
        SubagentState.EXECUTING,
        SubagentState.WAITING_FOR_INPUT,
        SubagentState.DEADLOCKED,
        SubagentState.POISONED,
    },
    SubagentState.EXECUTING: {
        SubagentState.VERIFYING,
        SubagentState.WAITING_FOR_INPUT,
        SubagentState.DEADLOCKED,
        SubagentState.POISONED,
    },
    SubagentState.VERIFYING: {
        SubagentState.COMPLETED,
        SubagentState.PLANNING,
        SubagentState.EXECUTING,
        SubagentState.DEADLOCKED,
        SubagentState.POISONED,
    },
    SubagentState.WAITING_FOR_INPUT: {
        SubagentState.PLANNING,
        SubagentState.EXECUTING,
        SubagentState.DEADLOCKED,
        SubagentState.POISONED,
    },
    SubagentState.COMPLETED: {SubagentState.IDLE},
    SubagentState.DEADLOCKED: {SubagentState.POISONED, SubagentState.IDLE},
    SubagentState.POISONED: set(),  # Terminal fail-stop
}


class SubagentHandle:
    """Individual agent lifecycle handle with active watchdog monitoring."""

    def __init__(
        self,
        agent_id: str,
        role: str,
        max_state_duration_s: float = 30.0,
        transition_callback: Optional[Callable[[str, str, str], None]] = None,
    ):
        self.agent_id = agent_id
        self.role = role
        self.current_state: SubagentState = SubagentState.IDLE
        self.state_entered_at = time.time()
        self.max_state_duration_s = max_state_duration_s
        self.transition_callback = transition_callback
        self.history: List[Dict[str, Any]] = [
            {"from": None, "to": SubagentState.IDLE.value, "timestamp": self.state_entered_at, "reason": "genesis"}
        ]

    def transition_to(self, new_state: SubagentState, reason: str = "") -> bool:
        """Transitions agent to a new state if valid according to the FSM graph."""
        if self.current_state == SubagentState.POISONED:
            raise RuntimeError(f"Agent {self.agent_id} is POISONED (fail-stop active). Cannot transition.")

        if new_state not in VALID_TRANSITIONS.get(self.current_state, set()):
            raise ValueError(
                f"Invalid transition for agent {self.agent_id}: {self.current_state.value} -> {new_state.value}"
            )

        now = time.time()
        self.history.append(
            {
                "from": self.current_state.value,
                "to": new_state.value,
                "timestamp": now,
                "duration_s": round(now - self.state_entered_at, 4),
                "reason": reason,
            }
        )
        self.current_state = new_state
        self.state_entered_at = now

        if self.transition_callback:
            self.transition_callback(self.agent_id, new_state.value, reason)

        return True

    def check_watchdog(self, now: Optional[float] = None) -> bool:
        """
        Checks if agent has exceeded its allowable duration in an active state.
        If exceeded, automatically marks state as DEADLOCKED.
        """
        current_time = now if now is not None else time.time()
        duration = current_time - self.state_entered_at

        # Only check active/transient states
        if self.current_state in (SubagentState.PLANNING, SubagentState.EXECUTING, SubagentState.VERIFYING):
            if duration > self.max_state_duration_s:
                self.transition_to(
                    SubagentState.DEADLOCKED,
                    reason=f"Watchdog timeout ({duration:.1f}s > {self.max_state_duration_s}s)",
                )
                return True
        return False


class DynamicLifecycleManager:
    """
    Orchestration manager for dynamic subagent lifecycles.
    Maintains active subagent registries, lifecycle transitions, and deadlock watchdog scanning.

    [FRENTE-006] Implements a bounded proposal queue (maxsize=KUDURRU_QUEUE_DEPTH=256) to
    prevent Ring-2 swarm floods from causing OOM before proposals reach the KUDURRU-64 barrier.
    Excess proposals are silently Dropped (anergy discarded, emitter not notified).
    """

    # [INV_C5_KUDURRU_64] Max queued proposals before silent Drop. Matches L1 cache-line count.
    KUDURRU_QUEUE_DEPTH: int = 256
    WAL_PATH: str = os.path.expanduser("~/.audit/lifecycle.wal")
    NIVCSW_THROTTLE_THRESHOLD: int = 1500

    def __init__(self, default_timeout_s: float = 30.0):
        import queue

        self.default_timeout_s = default_timeout_s
        self._agents: Dict[str, SubagentHandle] = {}
        # Bounded FIFO queue for proposals from Ring-2 agents before KUDURRU-64 evaluation.
        self._proposal_queue: "queue.Queue[Any]" = queue.Queue(maxsize=self.KUDURRU_QUEUE_DEPTH)

        # [NEW] Telemetría de base para medir Delta de Fricción
        usage = resource.getrusage(resource.RUSAGE_SELF)
        self._last_nivcsw = usage.ru_nivcsw
        self._last_time = time.monotonic()
        self.throttled = False

        # [NEW] Inicialización WAL Lock-Free (Append-only)
        self._init_wal()

    def _init_wal(self) -> None:
        """Inicia el WAL y restaura la topología de agentes huérfanos (Causal Resurrection)."""
        wal_dir = os.path.dirname(self.WAL_PATH)
        if wal_dir:
            os.makedirs(wal_dir, exist_ok=True)

        if os.path.exists(self.WAL_PATH):
            logger.info(f"Restoring agent topology from WAL: {self.WAL_PATH}")
            with open(self.WAL_PATH, "r") as f:
                for line in f:
                    try:
                        record = json.loads(line)
                        if record.get("event") == "SPAWN":
                            self.spawn(record["agent_id"], record["role"], restore=True)
                        elif record.get("event") == "TRANSITION":
                            agent = self.get(record["agent_id"])
                            if agent:
                                # Restaurar estado sin disparar callbacks al WAL
                                agent.current_state = SubagentState(record["new_state"])
                                agent.state_entered_at = record.get("timestamp", time.time())
                    except Exception as e:
                        logger.warning(f"Failed to parse WAL record: {e}")

    def _log_causal_event(self, event_type: str, data: dict[str, str]) -> None:
        """Registra transiciones atómicamente en disco para evitar amnesia de Apoptosis."""
        record = json.dumps({"timestamp": time.time(), "event": event_type, **data})
        try:
            with open(self.WAL_PATH, "a") as f:
                fcntl.flock(f, fcntl.LOCK_EX)
                f.write(f"{record}\n")
                f.flush()
                os.fsync(f.fileno())
                fcntl.flock(f, fcntl.LOCK_UN)
        except IOError as e:
            logger.error(f"WAL write failed: {e}")

    def _on_agent_transition(self, agent_id: str, new_state: str, reason: str) -> None:
        self._log_causal_event("TRANSITION", {"agent_id": agent_id, "new_state": new_state, "reason": reason})

    def submit_proposal(self, proposal: Any) -> bool:
        """
        Submit a Ring-2 swarm proposal to the bounded queue.
        Returns True if accepted, False if the queue is full (silent Drop per KUDURRU-64 semantics).
        Emitter is intentionally NOT notified on Drop to prevent DDoS amplification.
        """
        try:
            self._proposal_queue.put_nowait(proposal)
            return True
        except Exception:
            # [FRENTE-006] Queue full — silent Drop. Anergy discarded without ACK.
            return False

    def spawn(
        self, agent_id: str, role: str = "generalist", timeout_s: Optional[float] = None, restore: bool = False
    ) -> SubagentHandle:
        """Spawns and registers a new subagent with bounded state duration."""
        effective_timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        handle = SubagentHandle(
            agent_id=agent_id,
            role=role,
            max_state_duration_s=effective_timeout,
            transition_callback=self._on_agent_transition,
        )
        self._agents[agent_id] = handle

        if not restore:
            self._log_causal_event("SPAWN", {"agent_id": agent_id, "role": role})

        return handle

    def get(self, agent_id: str) -> Optional[SubagentHandle]:
        """Retrieves an existing subagent handle by its identifier."""
        return self._agents.get(agent_id)

    def scan_deadlocks(self, now: Optional[float] = None) -> List[str]:
        """
        Executes an O(N) sweep across all registered subagents,
        tripping deadlocks if active state thresholds are exceeded.
        Returns a list of deadlocked agent IDs.
        """
        # [NEW] Auditoría de Fricción Termodinámica (Apple Silicon PxS)
        current_time = time.monotonic()
        usage = resource.getrusage(resource.RUSAGE_SELF)
        current_nivcsw = usage.ru_nivcsw

        dt = current_time - self._last_time
        d_nivcsw = current_nivcsw - self._last_nivcsw

        if dt > 0:
            rate = d_nivcsw / dt
            if rate > self.NIVCSW_THROTTLE_THRESHOLD:
                if not self.throttled:
                    logger.warning(
                        f"THERMODYNAMIC THROTTLE TRIGGERED! nivcsw_rate={rate:.1f}/s > {self.NIVCSW_THROTTLE_THRESHOLD}"
                    )
                    self.throttled = True
            elif self.throttled and rate < (self.NIVCSW_THROTTLE_THRESHOLD * 0.8):
                logger.info(f"THERMODYNAMIC THROTTLE RESOLVED. nivcsw_rate={rate:.1f}/s")
                self.throttled = False

        self._last_nivcsw = current_nivcsw
        self._last_time = current_time

        deadlocked: List[str] = []
        for aid, handle in self._agents.items():
            if handle.check_watchdog(now=now) or handle.current_state == SubagentState.DEADLOCKED:
                deadlocked.append(aid)
        return deadlocked

    def list_active(self) -> List[SubagentHandle]:
        """Returns all agents not in terminal states."""
        return [h for h in self._agents.values() if h.current_state != SubagentState.POISONED]
