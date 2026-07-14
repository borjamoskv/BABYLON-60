import sqlite3
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cortex_inference import CortexInferenceEngine, CACHE_DB_PATH  # type: ignore

VOCAB = [
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
    "oráculo",
    "matriz",
]


def main() -> None:
    print("Initiating 1000-cycle EXERGY L3 Memoization Protocol...")
    engine = CortexInferenceEngine()
    unique_queries: set = set()
    while len(unique_queries) < 1000:
        length = len(unique_queries) % 6 + 3
        query_words = [
            VOCAB[(len(unique_queries) + i * 7) % len(VOCAB)] for i in range(length)
        ]
        query = " ".join(query_words)
        unique_queries.add(query)
    print("Pre-computing and caching 1000 isomorphic traces...")
    for query in unique_queries:
        engine.execute_inference(query)
    engine.close()
    conn = sqlite3.connect(CACHE_DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM L3_inference_cache")
    count = cursor.fetchone()[0]
    conn.close()
    if count >= 1000:
        print(
            f"SUCCESS: L3_inference_cache contains {count} entries. Zero-Anergy condition achieved."
        )
        sys.exit(0)
    else:
        print(f"FAILURE: Expected 1000 entries, but found {count}.")
        sys.exit(1)


if __name__ == "__main__":
    main()
