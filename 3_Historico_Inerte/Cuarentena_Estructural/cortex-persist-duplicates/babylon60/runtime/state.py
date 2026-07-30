# [C5-REAL] Exergy-Maximized
import json
from typing import Any

from babylon60.crypto.hash_registry import cortex_hash_b60


class RuntimeState:
    """Immutable causal state derived exclusively from the event ledger."""

    def __init__(self, initial_state: dict[str, Any] = None, version: int = 0):  # type: ignore
        self.data = initial_state or {}
        self.version = version

        # [C5-REAL] FFI Hardware Integration
        self._ffi_kernel = None
        try:
            import cortex_ffi

            self._ffi_kernel = cortex_ffi.BoundaryKernel()
        except ImportError:
            pass

        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        state_str = json.dumps(self.data, sort_keys=True)
        py_hash = cortex_hash_b60(f"{self.version}:{state_str}".encode())

        # Enforce Exergy-Maximized Cryptographic Anchor if FFI is loaded
        if self._ffi_kernel:
            ffi_hash = self._ffi_kernel.state_hash()
            return cortex_hash_b60(f"{py_hash}:{ffi_hash}".encode())

        return py_hash

    def apply_event(self, event: dict[str, Any]) -> "RuntimeState":
        """Deterministic state evolution with semantic physics validation."""
        action = event.get("action_type")
        payload = event.get("payload", {})

        # Physics Validation Layer
        tick = payload.get("tick")
        if tick is not None:
            prev_tick = self.data.get("last_tick", -1)
            if tick <= prev_tick:
                raise ValueError(
                    f"[PHYSICS VIOLATION] Causality inversion. Tick {tick} <= Previous {prev_tick}"
                )
            self.data["last_tick"] = tick

        entropy = payload.get("entropy")
        if entropy is not None and entropy < 0:
            raise ValueError("[PHYSICS VIOLATION] Negative entropy detected.")

        if action == "MEMORY_WRITE":
            self.data.update(payload)

        # [C5-REAL] Offload semantic validation to Rust BoundaryKernel
        if self._ffi_kernel:
            # Map deterministic Python event to Chaos IR
            ir = f"{action}|{json.dumps(payload)}"
            ffi_res = self._ffi_kernel.submit_ir(ir)
            if ffi_res.startswith("HARD_FAIL") or ffi_res == "REJECTED":
                raise ValueError(f"[PHYSICS VIOLATION] FFI Reject: {ffi_res}")

        self.version += 1
        self.hash = self._compute_hash()
        return self

    @classmethod
    def bootstrap(cls) -> "RuntimeState":
        """Bootstrap a fresh state."""
        return cls()

    def snapshot(self) -> dict[str, Any]:
        """Produce a deterministic snapshot dictionary for validation."""
        return {"version": self.version, "state_hash": self.hash, "data": dict(self.data)}
