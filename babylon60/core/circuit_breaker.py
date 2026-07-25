import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = 'closed'      # Normal operation
    OPEN = 'open'          # Failing, reject requests
    HALF_OPEN = 'half_open' # Testing recovery

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, reset_timeout: int = 60) -> None:
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._failure_threshold = failure_threshold
        self._reset_timeout = reset_timeout
        self._last_failure_time: float = 0.0
    
    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self._reset_timeout:
                self._state = CircuitState.HALF_OPEN
        return self._state
    
    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED
    
    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self._failure_threshold:
            self._state = CircuitState.OPEN
    
    def can_execute(self) -> bool:
        return self.state != CircuitState.OPEN
