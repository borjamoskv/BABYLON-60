"""
C5-REAL CTRE (Commit-Time Reconciliation Engine) Guardian.
Prevents TOCTOU vulnerabilities in UI agents and Concurrent State execution.
"""

import logging

logger = logging.getLogger(__name__)


class CTRECollisionError(RuntimeError):
    """Raised when an atomic commit fails due to a TOCTOU collision."""

    def __init__(self, expected: int, current: int, epsilon: int):
        super().__init__(
            f"CTRE SAGA ABORT: UI TOCTOU Collision (Epsilon: {epsilon}µs). Expected {expected}, got {current}."
        )
        self.epsilon = epsilon
        self.expected_hash = expected
        self.current_hash = current


# Fallback in case cortex_rs is not compiled
try:
    import cortex_rs

    HAS_RUST_CTRE = True
except ImportError:
    HAS_RUST_CTRE = False


class CTREGuard:
    """
    CTRE Engine for CORTEX Persist.
    Implements optimistic concurrency via atomic Test-and-Set delegated to Rust.
    """

    @staticmethod
    def validate_commit(
        expected_hash: int, current_hash: int, target_x: float = 0.0, target_y: float = 0.0
    ) -> tuple[bool, int]:
        """
        Executes atomic verification (state isomorphism).

        Args:
            expected_hash: State hash when the Agent (VLM/LLM) planned the action (t0).
            current_hash: State hash microscopically before injection (t1).
            target_x: X coordinate (for UI agents).
            target_y: Y coordinate (for UI agents).

        Returns:
            Tuple[bool, int]: (True if commit is successful / False if TOCTOU divergence exists, time in microseconds epsilon)
        """
        if HAS_RUST_CTRE and hasattr(cortex_rs, "ctre_atomic_commit"):
            # C5-REAL execution via FFI
            try:
                success, epsilon_us = getattr(cortex_rs, "ctre_atomic_commit")(  # noqa: B009
                    expected_hash, target_x, target_y, current_hash
                )
                if not success:
                    logger.warning(
                        "[CTRE] SAGA ABORT: Mutation detected (TOCTOU). Epsilon=%sµs", epsilon_us
                    )
                else:
                    logger.info(
                        "[CTRE] COMMIT SUCCESS: Structural isomorphism verified in %sµs", epsilon_us
                    )
                return success, epsilon_us
            except (ValueError, TypeError, KeyError, AssertionError) as e:
                logger.error("[CTRE] FFI Error in atomic validation: %s", e)
                # Fallback on error
                return CTREGuard._python_fallback(expected_hash, current_hash)
        else:
            # Fallback to Python GIL (jitter prone)
            return CTREGuard._python_fallback(expected_hash, current_hash)

    @staticmethod
    def _python_fallback(expected_hash: int, current_hash: int) -> tuple[bool, int]:
        import time

        t_start = time.perf_counter_ns()
        success = expected_hash == current_hash
        epsilon_us = (time.perf_counter_ns() - t_start) // 1000

        if not success:
            logger.warning(
                "[CTRE-PY] SAGA ABORT (GIL Warning): Mutation detected. Epsilon=%sµs", epsilon_us
            )
        return success, epsilon_us
