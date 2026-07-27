# [C5-REAL] Exergy-Maximized
"""
Embedding providers - Abstraction layer for survival-ready embeddings.
"""

from __future__ import annotations

import logging
from typing import Protocol, runtime_checkable

logger = logging.getLogger("babylon60")


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for embedding providers."""

    @property
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    @property
    def supports_multimodal(self) -> bool:
        """Return True if current embedder supports multimodal input."""
        ...

    def is_available(self) -> bool:
        """Check if the provider is available in the current environment."""
        ...

    def embed(self, text: str | list[str]) -> list[float] | list[list[float]]:
        """Generate an embedding for the given text(s)."""
        ...

    def embed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        ...

    async def aembed(self, text: str | list[str]) -> list[float] | list[list[float]]:
        """Async embedding API."""
        ...

    async def aembed_batch(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Async batch embedding API."""
        ...


class NullEmbeddingProvider:
    """survival-ready provider that does nothing. (Axiom Ω₃)"""

    def is_available(self) -> bool:
        return True

    def embed(self, text: str) -> list[float]:
        logger.debug("NullEmbeddingProvider: ignoring request for '%s'", text[:20])
        return []


class TorchEmbeddingProvider:
    """Legacy provider using LocalEmbedder (depends on torch)."""

    def __init__(self, embedder: any):  # pyright: ignore
        self._embedder = embedder

    def is_available(self) -> bool:
        try:
            import torch  # pyright: ignore[reportMissingImports]

            return torch.cuda.is_available() or torch.backends.mps.is_available() or True
        except ImportError:
            return False

    def embed(self, text: str) -> list[float]:
        return self._embedder.embed(text)
