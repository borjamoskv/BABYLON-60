import logging
import math
from typing import Any
from .models import CortexFactModel

logger = logging.getLogger('babylon60.memory.sqlite_vec_store')


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class SovereignVectorStoreL2:
    """In-memory vector store with cosine similarity search.
    
    Uses a simple brute-force approach for small-to-medium datasets.
    For production use with >10k facts, migrate to sqlite-vec or FAISS.
    """

    def __init__(self, encoder: Any = None) -> None:
        self.encoder = encoder
        self._store: dict[str, CortexFactModel] = {}
        self._embeddings: dict[str, list[float]] = {}

    async def recall(self, query: str, limit: int = 1, project: str = 'autodidact_knowledge', tenant_id: str = 'sovereign') -> list[CortexFactModel]:
        if not self._store:
            return []
        
        if self.encoder is not None:
            query_embedding = self.encoder.encode(query)
        else:
            # Fallback: simple character-level hash embedding
            query_embedding = self._fallback_encode(query)
        
        scored: list[tuple[float, CortexFactModel]] = []
        for fact_id, fact in self._store.items():
            if fact_id in self._embeddings:
                sim = _cosine_similarity(query_embedding, self._embeddings[fact_id])
                scored.append((sim, fact))
        
        scored.sort(key=lambda x: x[0], reverse=True)
        return [fact for _, fact in scored[:limit]]

    async def memorize(self, fact: CortexFactModel) -> None:
        self._store[fact.id] = fact
        if self.encoder is not None:
            self._embeddings[fact.id] = self.encoder.encode(fact.content)
        else:
            self._embeddings[fact.id] = self._fallback_encode(fact.content)
        logger.info('SovereignVectorStoreL2 memorized fact: %s', fact.id)
    
    async def forget(self, fact_id: str) -> bool:
        if fact_id in self._store:
            del self._store[fact_id]
            self._embeddings.pop(fact_id, None)
            return True
        return False
    
    async def count(self) -> int:
        return len(self._store)
    
    @staticmethod
    def _fallback_encode(text: str, dim: int = 64) -> list[float]:
        """Simple deterministic hash-based embedding for testing without a real encoder."""
        import hashlib
        h = hashlib.sha256(text.encode('utf-8')).digest()
        # Expand hash to desired dimension
        result: list[float] = []
        for i in range(dim):
            byte_idx = i % len(h)
            result.append((h[byte_idx] - 128) / 128.0)
        return result