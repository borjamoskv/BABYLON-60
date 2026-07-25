# C5-REAL EXERGY CERTIFIED
"""C6-REAL Deterministic Fault Injector (Chaos Monkey)."""

import os
import signal
import time
from typing import Dict, Any


class DeterministicChaosMonkey:
    def __init__(self, target_campaigns: Dict[str, int]):
        """
        target_campaigns: e.g., {"WAL_APPEND": 10, "CHECKPOINT": 10}
        """
        self.campaigns = target_campaigns.copy()
        self.current_counts = {k: 0 for k in target_campaigns.keys()}

    def try_inject_fault(self, target_pid: int, phase: str) -> bool:
        """Injects SIGKILL if the quota for the current phase is not exhausted."""
        if phase in self.campaigns and self.current_counts[phase] < self.campaigns[phase]:
            try:
                # C5-REAL: 0 Entropy, unrecoverable OS termination
                os.kill(target_pid, signal.SIGKILL)
                self.current_counts[phase] += 1
                return True
            except ProcessLookupError:
                pass
        return False


def chaos_orchestrator(target_pid: int, target_campaigns: Dict[str, int], shared_phase: Any, stop_event: Any) -> None:
    """Runs in a separate thread/process to assassinate the target deterministically."""
    monkey = DeterministicChaosMonkey(target_campaigns)

    while not stop_event.is_set():
        current_phase = shared_phase.value.decode("utf-8").strip("\x00")
        if current_phase and monkey.try_inject_fault(target_pid, current_phase):
            break  # Target is dead
        time.sleep(0.001)  # 1ms resolution polling
