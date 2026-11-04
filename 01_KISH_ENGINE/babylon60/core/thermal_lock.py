import time
import logging
import asyncio

logger = logging.getLogger("babylon60.core.thermal_lock")

POISONED_STATE = 0xDEAD6060
RUNNING_STATE = 0x00000001


class ThermalLock:
    """
    ThermalLock with hysteresis for Kish Engine core.
    Prevents the core from accepting writes after entering a POISONED state.
    Enforces a cooldown/hysteresis period before any reset is allowed.
    """

    def __init__(self, cooldown_seconds: float = 30.0):
        self._state = RUNNING_STATE
        self._cooldown_seconds = cooldown_seconds
        self._poisoned_at: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def is_poisoned(self) -> bool:
        return self._state == POISONED_STATE

    async def poison(self) -> None:
        """Transitions the core to POISONED state and engages ThermalLock."""
        async with self._lock:
            if self._state != POISONED_STATE:
                self._state = POISONED_STATE
                self._poisoned_at = time.time()
                logger.critical(f"ThermalLock engaged: Core transitioned to POISONED ({hex(POISONED_STATE)}).")

    async def check_write_allowed(self) -> bool:
        """
        Checks if a write is allowed.
        Fails fast if the core is POISONED.
        """
        async with self._lock:
            if self._state == POISONED_STATE:
                logger.warning("Write rejected: Core is currently under ThermalLock (POISONED).")
                return False
            return True

    async def attempt_reset(self) -> bool:
        """
        Attempts to reset the ThermalLock after the hysteresis cooldown period.
        """
        async with self._lock:
            if self._state != POISONED_STATE:
                return True

            elapsed = time.time() - self._poisoned_at
            if elapsed < self._cooldown_seconds:
                logger.warning(
                    f"Reset rejected: ThermalLock hysteresis active. Cooldown remaining: {self._cooldown_seconds - elapsed:.2f}s"
                )
                return False

            self._state = RUNNING_STATE
            self._poisoned_at = 0.0
            logger.info("ThermalLock disengaged: Core reset to RUNNING state.")
            return True
