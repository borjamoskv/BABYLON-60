from typing import Protocol, runtime_checkable

@runtime_checkable
class Encoder(Protocol):
    def encode(self, text: str) -> list[float]: ...