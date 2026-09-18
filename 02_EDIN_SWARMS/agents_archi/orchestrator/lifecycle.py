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

import time
from enum import Enum
from typing import Dict, List, Any, Optional


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
    SubagentState.PLANNING: {SubagentState.EXECUTING, SubagentState.WAITING_FOR_INPUT, SubagentState.DEADLOCKED, SubagentState.POISONED},
    SubagentState.EXECUTING: {SubagentState.VERIFYING, SubagentState.WAITING_FOR_INPUT, SubagentState.DEADLOCKED, SubagentState.POISONED},
    SubagentState.VERIFYING: {SubagentState.COMPLETED, SubagentState.PLANNING, SubagentState.EXECUTING, SubagentState.DEADLOCKED, SubagentState.POISONED},
    SubagentState.WAITING_FOR_INPUT: {SubagentState.PLANNING, SubagentState.EXECUTING, SubagentState.DEADLOCKED, SubagentState.POISONED},
    SubagentState.COMPLETED: {SubagentState.IDLE},
    SubagentState.DEADLOCKED: {SubagentState.POISONED, SubagentState.IDLE},
    SubagentState.POISONED: set(),  # Terminal fail-stop
}


class SubagentHandle:
    """Individual agent lifecycle handle with active watchdog monitoring."""

    def __init__(self, agent_id: str, role: str, max_state_duration_s: float = 30.0):
        self.agent_id = agent_id
        self.role = role
        self.current_state = SubagentState.IDLE
        self.state_entered_at = time.time()
        self.max_state_duration_s = max_state_duration_s
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
        self.history.append({
            "from": self.current_state.value,
            "to": new_state.value,
            "timestamp": now,
            "duration_s": round(now - self.state_entered_at, 4),
            "reason": reason,
        })
        self.current_state = new_state
        self.state_entered_at = now
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
                self.transition_to(SubagentState.DEADLOCKED, reason=f"Watchdog timeout ({duration:.1f}s > {self.max_state_duration_s}s)")
                return True
        return False


class DynamicLifecycleManager:
    """
    Orchestration manager for dynamic subagent lifecycles.
    Maintains active subagent registries, lifecycle transitions, and deadlock watchdog scanning.
    """

    def __init__(self, default_timeout_s: float = 30.0):
        self.default_timeout_s = default_timeout_s
        self._agents: Dict[str, SubagentHandle] = {}

    def spawn(self, agent_id: str, role: str = "generalist", timeout_s: Optional[float] = None) -> SubagentHandle:
        """Spawns and registers a new subagent with bounded state duration."""
        effective_timeout = timeout_s if timeout_s is not None else self.default_timeout_s
        handle = SubagentHandle(agent_id=agent_id, role=role, max_state_duration_s=effective_timeout)
        self._agents[agent_id] = handle
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
        deadlocked: List[str] = []
        for aid, handle in self._agents.items():
            if handle.check_watchdog(now=now) or handle.current_state == SubagentState.DEADLOCKED:
                deadlocked.append(aid)
        return deadlocked

    def list_active(self) -> List[SubagentHandle]:
        """Returns all agents not in terminal states."""
        return [h for h in self._agents.values() if h.current_state != SubagentState.POISONED]



