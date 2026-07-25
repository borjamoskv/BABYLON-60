# C5-REAL EXERGY CERTIFIED
"""
CAM-5.0 Minimal Object Memory Space.
Provides allocation, lookup, and release over opaque Handles.
"""

from typing import Any
from cortex.aem.isa import ExecutionError, Handle, ImplementationError


class ObjectSpace:
    def __init__(self) -> None:
        self.objects: dict[Handle, Any] = {}

    def allocate(self, payload: Any) -> Handle:
        try:
            handle = Handle()
            self.objects[handle] = payload
            return handle
        except (MemoryError, ValueError) as e:
            raise ImplementationError(f"Failed to allocate in Object Space: {e}") from e

    def lookup(self, handle: Handle) -> Any:
        if handle not in self.objects:
            raise ExecutionError(f"Invalid Handle '{handle.id}': Object not allocated")
        return self.objects[handle]

    def release(self, handle: Handle) -> None:
        if handle in self.objects:
            del self.objects[handle]
