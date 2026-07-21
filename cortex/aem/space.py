"""
CAM-3.0 Abstract Object Space.
Provides low-level storage memory operations: Allocate, Lookup, Bind, Release.
"""

from typing import Any
from cortex.aem.isa import Handle, ImplementationError, ExecutionError


class ObjectSpace:
    def __init__(self) -> None:
        self.objects: dict[Handle, Any] = {}
        self.bindings: dict[tuple[Handle, Handle], str] = {}

    def allocate(self, payload: Any) -> Handle:
        try:
            handle = Handle()
            self.objects[handle] = payload
            return handle
        except Exception as e:
            raise ImplementationError(f"Failed to allocate in Object Space: {e}") from e

    def lookup(self, handle: Handle) -> Any:
        if handle not in self.objects:
            raise ExecutionError(f"Invalid Handle '{handle.id}': Object not allocated")
        return self.objects[handle]

    def bind(self, handle_a: Handle, handle_b: Handle, relation_tag: str) -> None:
        if handle_a not in self.objects or handle_b not in self.objects:
            raise ExecutionError("Cannot bind unallocated handles")
        self.bindings[(handle_a, handle_b)] = relation_tag

    def release(self, handle: Handle) -> None:
        if handle in self.objects:
            del self.objects[handle]
            # Clean up associated bindings
            keys_to_del = [k for k in self.bindings if handle in k]
            for k in keys_to_del:
                del self.bindings[k]
