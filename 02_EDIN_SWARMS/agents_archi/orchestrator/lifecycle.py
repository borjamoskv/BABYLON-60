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
import queue
import resource
import threading
import time
import json
import logging
from collections import deque
from enum import Enum
from typing import Deque, Dict, List, Any, Optional, Callable


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
    """Individual agent lifecycle handle with active watchdog monitoring and bounded FSM budget."""

    def __init__(
        self,
        agent_id: str,
        role: str,
        max_state_duration_s: float = 30.0,
        transition_callback: Optional[Callable[[str, str, str], None]] = None,
        max_transitions: int = 128,
        max_history: int = 64,
    ):
        self.agent_id = agent_id
        self.role = role
        self.current_state: SubagentState = SubagentState.IDLE
        self.state_entered_at = time.time()
        self.max_state_duration_s = max_state_duration_s
        self.transition_callback = transition_callback
        self.max_transitions = max(1, max_transitions)
        self.transition_count: int = 0
        self.history: Deque[Dict[str, Any]] = deque(
            [{"from": None, "to": SubagentState.IDLE.value, "timestamp": self.state_entered_at, "reason": "genesis"}],
            maxlen=max(1, max_history),
        )

    def transition_to(self, new_state: SubagentState, reason: str = "") -> bool:
        """Transitions agent to a new state if valid according to the FSM graph and within budget."""
        if self.current_state == SubagentState.POISONED:
            raise RuntimeError(f"Agent {self.agent_id} is POISONED (fail-stop active). Cannot transition.")

        if new_state not in VALID_TRANSITIONS.get(self.current_state, set()):
            raise ValueError(
                f"Invalid transition for agent {self.agent_id}: {self.current_state.value} -> {new_state.value}"
            )

        now = time.time()
        if self.transition_count >= self.max_transitions and new_state != SubagentState.POISONED:
            poison_reason = f"Transition budget exceeded ({self.transition_count} >= {self.max_transitions})"
            self.history.append(
                {
                    "from": self.current_state.value,
                    "to": SubagentState.POISONED.value,
                    "timestamp": now,
                    "duration_s": round(now - self.state_entered_at, 4),
                    "reason": poison_reason,
                }
            )
            self.current_state = SubagentState.POISONED
            self.state_entered_at = now
            if self.transition_callback:
                self.transition_callback(self.agent_id, SubagentState.POISONED.value, poison_reason)
            raise RuntimeError(f"Agent {self.agent_id} poisoned: {poison_reason}")

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
        self.transition_count += 1

        if self.transition_callback:
            self.transition_callback(self.agent_id, new_state.value, reason)

        return True

    def check_watchdog(self, now: Optional[float] = None) -> bool:
        """
        Checks if agent has exceeded its allowable duration in an active or waiting state.
        If exceeded, automatically marks state as DEADLOCKED.
        """
        current_time = now if now is not None else time.time()
        duration = current_time - self.state_entered_at

        # Monitor active transient states AND blocked waiting states (H4)
        if self.current_state in (
            SubagentState.PLANNING,
            SubagentState.EXECUTING,
            SubagentState.VERIFYING,
            SubagentState.WAITING_FOR_INPUT,
        ):
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
    Excess proposals are dropped with observable backpressure telemetry.
    """

    # [INV_C5_KUDURRU_64] Max queued proposals before Drop. Matches L1 cache-line count.
    KUDURRU_QUEUE_DEPTH: int = 256
    WAL_PATH: str = os.path.expanduser("~/.audit/lifecycle.wal")
    NIVCSW_THROTTLE_THRESHOLD: int = 1500
    DEFAULT_WAL_FSYNC_BATCH_SIZE: int = 64

    def __init__(
        self,
        default_timeout_s: float = 30.0,
        wal_fsync_batch_size: int = DEFAULT_WAL_FSYNC_BATCH_SIZE,
        enforce_throttle: bool = True,
        default_max_transitions: int = 128,
        default_max_history: int = 64,
    ):
        self.default_timeout_s = default_timeout_s
        self.wal_fsync_batch_size = max(1, wal_fsync_batch_size)
        self.enforce_throttle = enforce_throttle
        self.default_max_transitions = max(1, default_max_transitions)
        self.default_max_history = max(1, default_max_history)
        self._agents: Dict[str, SubagentHandle] = {}
        # Bounded FIFO queue for proposals from Ring-2 agents before KUDURRU-64 evaluation.
        self._proposal_queue: "queue.Queue[Any]" = queue.Queue(maxsize=self.KUDURRU_QUEUE_DEPTH)

        # Observable backpressure & drop telemetry (H6)
        self.proposals_accepted: int = 0
        self.proposals_dropped: int = 0
        self.throttled_rejections: int = 0

        # Telemetría de base para medir Delta de Fricción
        usage = resource.getrusage(resource.RUSAGE_SELF)
        self._last_nivcsw = usage.ru_nivcsw
        self._last_time = time.monotonic()
        self.throttled = False

        # WAL append-only con descriptor persistente y group-commit fsync (H1)
        self._wal_path: str = self.WAL_PATH
        self._wal_lock = threading.Lock()
        self._wal_fd: Optional[int] = None
        self._wal_pending_sync: int = 0
        self._init_wal()

    def _init_wal(self) -> None:
        """Inicia el WAL y restaura la topología de agentes huérfanos (Causal Resurrection)."""
        wal_dir = os.path.dirname(self._wal_path)
        if wal_dir:
            os.makedirs(wal_dir, exist_ok=True)

        if os.path.exists(self._wal_path):
            logger.info(f"Restoring agent topology from WAL: {self._wal_path}")
            with open(self._wal_path, "r") as f:
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

        self._wal_fd = os.open(self._wal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)

    def _log_causal_event(self, event_type: str, data: dict[str, str]) -> None:
        """Registra transiciones en WAL append-only con O_APPEND y group-commit fsync."""
        payload = (json.dumps({"timestamp": time.time(), "event": event_type, **data}) + "\n").encode("utf-8")
        try:
            with self._wal_lock:
                if self._wal_fd is None:
                    self._wal_fd = os.open(self._wal_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
                os.write(self._wal_fd, payload)
                self._wal_pending_sync += 1
                if self._wal_pending_sync >= self.wal_fsync_batch_size:
                    os.fsync(self._wal_fd)
                    self._wal_pending_sync = 0
        except OSError as e:
            logger.error(f"WAL write failed: {e}")

    def flush_wal(self) -> None:
        """Forces an fsync of any buffered WAL writes."""
        with self._wal_lock:
            if self._wal_fd is not None and self._wal_pending_sync > 0:
                try:
                    os.fsync(self._wal_fd)
                except OSError as e:
                    logger.error(f"WAL fsync failed: {e}")
                finally:
                    self._wal_pending_sync = 0

    def close(self) -> None:
        """Flushes and closes the persistent WAL file descriptor."""
        with self._wal_lock:
            if self._wal_fd is not None:
                try:
                    if self._wal_pending_sync > 0:
                        os.fsync(self._wal_fd)
                except OSError:
                    pass
                finally:
                    try:
                        os.close(self._wal_fd)
                    except OSError:
                        pass
                    self._wal_fd = None
                    self._wal_pending_sync = 0

    def __del__(self) -> None:
        try:
            self.close()
        except Exception:
            pass

    def _on_agent_transition(self, agent_id: str, new_state: str, reason: str) -> None:
        self._log_causal_event("TRANSITION", {"agent_id": agent_id, "new_state": new_state, "reason": reason})

    def submit_proposal(self, proposal: Any) -> bool:
        """
        Submit a Ring-2 swarm proposal to the bounded queue.
        Returns True if accepted, False if rejected by throttle or full queue.
        Updates observable drop/throttle counters for backpressure.
        """
        if self.enforce_throttle and self.throttled:
            self.throttled_rejections += 1
            self.proposals_dropped += 1
            return False

        try:
            self._proposal_queue.put_nowait(proposal)
            self.proposals_accepted += 1
            return True
        except queue.Full:
            # [FRENTE-006] Queue full — drop with observable telemetry.
            self.proposals_dropped += 1
            return False

    def spawn(
        self,
        agent_id: str,
        role: str = "generalist",
        timeout_s: Optional[float] = None,
        restore: bool = False,
        max_transitions: Optional[int] = None,
    ) -> SubagentHandle:
        """Spawns and registers a new subagent with bounded state duration and FSM budget."""
        if not restore and self.enforce_throttle and self.throttled:
            self.throttled_rejections += 1
            raise RuntimeError(f"Thermodynamic throttle active: spawn rejected for {agent_id}")

        effective_timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        effective_max_transitions = max_transitions if max_transitions is not None else self.default_max_transitions
        handle = SubagentHandle(
            agent_id=agent_id,
            role=role,
            max_state_duration_s=effective_timeout,
            transition_callback=self._on_agent_transition,
            max_transitions=effective_max_transitions,
            max_history=self.default_max_history,
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
        tripping deadlocks if active/waiting state thresholds are exceeded.
        Returns a list of deadlocked agent IDs.
        """
        # Auditoría de Fricción Termodinámica (Apple Silicon PxS)
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

    def telemetry(self) -> Dict[str, Any]:
        """Returns observable entropy, backpressure, and lifecycle metrics."""
        total_proposals = self.proposals_accepted + self.proposals_dropped
        poisoned_count = sum(1 for h in self._agents.values() if h.current_state == SubagentState.POISONED)
        return {
            "total_agents": len(self._agents),
            "active_agents": len(self._agents) - poisoned_count,
            "poisoned_agents": poisoned_count,
            "throttled": self.throttled,
            "throttled_rejections": self.throttled_rejections,
            "queue_depth": self._proposal_queue.qsize(),
            "queue_capacity": self.KUDURRU_QUEUE_DEPTH,
            "proposals_accepted": self.proposals_accepted,
            "proposals_dropped": self.proposals_dropped,
            "drop_rate": round(self.proposals_dropped / total_proposals, 4) if total_proposals > 0 else 0.0,
            "wal_pending_sync": self._wal_pending_sync,
        }

    def list_active(self) -> List[SubagentHandle]:
        """Returns all agents not in terminal states."""
        return [h for h in self._agents.values() if h.current_state != SubagentState.POISONED]
