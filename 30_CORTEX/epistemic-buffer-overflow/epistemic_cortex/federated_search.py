# [C5-REAL] SQLite-per-tenant with Federated Central Index
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import sqlite3
from pathlib import Path
from dataclasses import dataclass

@dataclass
class SearchResult:
    tenant_id: str
    fact_id: int
    content: str
    similarity_score: float

class CentralVectorIndex:
    """
    Central Index representing Qdrant cluster mock.
    Maintains flat vector metadata mapped back to tenants for fast O(1) routing.
    """
    def __init__(self) -> None:
        # Maps query keyword -> list of (tenant_id, fact_id, vector_stub_score)
        self.vector_space: dict[str, list[tuple[str, int, float]]] = {}

    def index_fact(self, tenant_id: str, fact_id: int, content: str) -> None:
        words = content.lower().split()
        for word in words:
            if word not in self.vector_space:
                self.vector_space[word] = []
            self.vector_space[word].append((tenant_id, fact_id, 0.95))

    def query_index(self, query: str, limit: int = 5) -> list[tuple[str, int, float]]:
        query_words = query.lower().split()
        hits: list[tuple[str, int, float]] = []
        for word in query_words:
            if word in self.vector_space:
                hits.extend(self.vector_space[word])
        # Sort by simulated score descending
        hits.sort(key=lambda x: x[2], reverse=True)
        return hits[:limit]

class FederatedSearchEngine:
    """
    Sovereign Federated search resolver.
    Avoids O(N) lookup loops across tenant DB files by using the central index as a router.
    """
    def __init__(self, data_root: str) -> None:
        self.data_root = Path(data_root)
        self.data_root.mkdir(parents=True, exist_ok=True)
        self.central_index = CentralVectorIndex()

    def get_tenant_db_path(self, tenant_id: str) -> Path:
        return self.data_root / f"{tenant_id}.db"

    def init_tenant_db(self, tenant_id: str) -> None:
        db_path = self.get_tenant_db_path(tenant_id)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "CREATE TABLE IF NOT EXISTS facts ("
            "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
            "  content TEXT NOT NULL"
            ")"
        )
        conn.commit()
        conn.close()

    def store_fact(self, tenant_id: str, content: str) -> int:
        self.init_tenant_db(tenant_id)
        db_path = self.get_tenant_db_path(tenant_id)
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("INSERT INTO facts (content) VALUES (?)", (content,))
        fact_id = cursor.lastrowid or 0
        conn.commit()
        conn.close()

        # Update Central Vector Index for O(1) multi-tenant routing
        self.central_index.index_fact(tenant_id, fact_id, content)
        return fact_id

    def retrieve_fact(self, tenant_id: str, fact_id: int) -> str | None:
        db_path = self.get_tenant_db_path(tenant_id)
        if not db_path.exists():
            return None
        
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT content FROM facts WHERE id = ?", (fact_id,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None

    def federated_search(self, query: str, limit: int = 5) -> list[SearchResult]:
        # 1. Ask central index for active coordinate mappings (O(1) hop)
        index_hits = self.central_index.query_index(query, limit=limit)
        
        # 2. Parallel fetch only target shards (never full iteration scan)
        results: list[SearchResult] = []
        for tenant_id, fact_id, score in index_hits:
            content = self.retrieve_fact(tenant_id, fact_id)
            if content:
                results.append(SearchResult(
                    tenant_id=tenant_id,
                    fact_id=fact_id,
                    content=content,
                    similarity_score=score
                ))
        return results
