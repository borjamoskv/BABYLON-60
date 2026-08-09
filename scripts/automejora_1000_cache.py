# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import sqlite3
import sys
from typing import Any

from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from babylon60.core.cortex_inference import CACHE_DB_PATH, CortexInferenceEngine  # noqa: E402

VOCAB: list[str] = [
    "causar",
    "provocar",
    "generar",
    "hacer",
    "por qué",
    "efecto",
    "parte",
    "sistema",
    "estructura",
    "composición",
    "dividir",
    "cambiar",
    "evolucionar",
    "fluir",
    "transitar",
    "dinámica",
    "tiempo",
    "podría",
    "debería",
    "sería",
    "quizás",
    "posible",
    "mundo",
    "mejorar",
    "optimizar",
    "aprender",
    "entrenar",
    "divergencia",
    "entropía",
    "significar",
    "interpretar",
    "leer",
    "texto",
    "signo",
    "código",
    "confianza",
    "verdad",
    "verificar",
    "test",
    "hash",
    "isomorfismo",
    "fuego",
    "ruido",
    "vórtice",
    "colapso",
    "atestador",
    "matriz",
]


def main() -> None:
    import time
    start_time = time.perf_counter()
    print("Initiating 1000-cycle EXERGY L3 Memoization Protocol...")
    engine: CortexInferenceEngine = CortexInferenceEngine()
    unique_queries: set[str] = set()
    while len(unique_queries) < 1000:
        length: int = len(unique_queries) % 6 + 3
        query_words: list[str] = [VOCAB[(len(unique_queries) + i * 7) % len(VOCAB)] for i in range(length)]
        query: str = " ".join(query_words)
        unique_queries.add(query)
    
    print("Pre-computing and caching 1000 isomorphic traces...")
    for query in unique_queries:
        engine.execute_inference(query)
    engine.close()
    
    with sqlite3.connect(CACHE_DB_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL;")
        cursor: sqlite3.Cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM L3_inference_cache")
        row: Any = cursor.fetchone()
        count: int = row[0] if row else 0

    elapsed = time.perf_counter() - start_time
    throughput = count / elapsed if elapsed > 0 else 0

    if count >= 1000:
        print(f"SUCCESS: L3_inference_cache contains {count} entries in {elapsed:.3f}s ({throughput:.1f} op/s). Zero-Anergy condition achieved.")
        sys.exit(0)
    else:
        print(f"FAILURE: Expected 1000 entries, but found {count}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
