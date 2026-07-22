"""C6-REAL Probabilistic Fault Injector (Chaos Monkey)."""
import os
import signal
import random
import multiprocessing
import time
from typing import Dict

class ProbabilisticChaosMonkey:
    def __init__(self, probabilities: Dict[str, float]):
        """
        probabilities: e.g., {"WAL_APPEND": 0.25, "CHECKPOINT": 0.25, "FSYNC_BOUNDARY": 0.25}
        """
        self.probabilities = probabilities
    
    def try_inject_fault(self, target_pid: int, phase: str) -> bool:
        """Attempts to inject a SIGKILL based on the phase's configured probability."""
        prob = self.probabilities.get(phase, 0.0)
        if random.random() < prob:
            try:
                # C5-REAL: 0 Entropy, unrecoverable OS termination
                os.kill(target_pid, signal.SIGKILL)
                return True
            except ProcessLookupError:
                pass
        return False

def chaos_orchestrator(target_pid: int, probabilities: Dict[str, float], shared_phase: multiprocessing.Array, stop_event: multiprocessing.Event) -> None: # type: ignore
    """Runs in a separate thread/process to assassinate the target probabilistically."""
    monkey = ProbabilisticChaosMonkey(probabilities)
    
    while not stop_event.is_set():
        # Read the current phase from the shared memory array (byte string)
        current_phase = shared_phase.value.decode('utf-8').strip('\x00')
        if current_phase and monkey.try_inject_fault(target_pid, current_phase):
            break  # Target is dead
        time.sleep(0.001)  # 1ms resolution polling
