import logging
import os
import sqlite3
import sys
from typing import Any
import babylon60.database.core
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cortex_inference import CACHE_DB_PATH, CortexInferenceEngine
VOCAB: list[str] = ['causar', 'provocar', 'generar', 'hacer', 'por qué', 'efecto', 'parte', 'sistema', 'estructura', 'composición', 'dividir', 'cambiar', 'evolucionar', 'fluir', 'transitar', 'dinámica', 'tiempo', 'podría', 'debería', 'sería', 'quizás', 'posible', 'mundo', 'mejorar', 'optimizar', 'aprender', 'entrenar', 'divergencia', 'entropía', 'significar', 'interpretar', 'leer', 'texto', 'signo', 'código', 'confianza', 'verdad', 'verificar', 'test', 'hash', 'isomorfismo', 'fuego', 'ruido', 'vórtice', 'colapso', 'oráculo', 'matriz']

def main() -> None:
    logging.info('Initiating 1000-cycle EXERGY L3 Memoization Protocol...')
    engine: CortexInferenceEngine = CortexInferenceEngine()
    unique_queries: set[str] = set()
    while len(unique_queries) < 1000:
        length: int = len(unique_queries) % 6 + 3
        query_words: list[str] = [VOCAB[(len(unique_queries) + i * 7) % len(VOCAB)] for i in range(length)]
        query: str = ' '.join(query_words)
        unique_queries.add(query)
    logging.info('Pre-computing and caching 1000 isomorphic traces...')
    for query in unique_queries:
        engine.execute_inference(query)
    engine.close()
    conn: sqlite3.Connection = babylon60.database.core.connect_sync(CACHE_DB_PATH)
    conn.execute('PRAGMA journal_mode=WAL;')
    cursor: sqlite3.Cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM L3_inference_cache')
    row: Any = cursor.fetchone()
    count: int = row[0]
    conn.close()
    if count >= 1000:
        logging.info(f'SUCCESS: L3_inference_cache contains {count} entries. Zero-Anergy condition achieved.')
        sys.exit(0)
    else:
        logging.info(f'FAILURE: Expected 1000 entries, but found {count}.')
        sys.exit(1)
if __name__ == '__main__':
    main()