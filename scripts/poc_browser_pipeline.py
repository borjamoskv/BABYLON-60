import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from babylon60.core.url_cache import URLCacheSync
from babylon60.core.popperian_filter import evaluate_payload

import time

def run_test():
    print("=== [C5-REAL] Verificación del Pipeline Completo del Browser Agent ===")
    
    url = f"https://example.org/rust-ownership-guide-{int(time.time())}"
    taint = "browser_agent_session_test_01"
    
    cache = URLCacheSync()
    
    # 1. Check cache miss
    cached_payload = cache.get(url)
    print("1. Intento de caché inicial (debe ser None):", cached_payload)
    assert cached_payload is None
    
    # 2. Simulate web fetch & Popperian filter validation
    fetched_content = (
        "The Rust language uses affine type system semantics to ensure zero-cost abstractions "
        "and memory safety without a garbage collector. "
        "Detailed documentation can be reviewed at https://doc.rust-lang.org/book/"
    )
    
    print("\n2. Evaluación con Popperian Filter:")
    res = evaluate_payload(fetched_content)
    print("Resultado del filtro:", res)
    assert res.passed is True
    
    # 3. Store in Level 0 Cache with causal taint
    print("\n3. Guardando en Caché SQLite WAL con causal_taint...")
    cache.put(url, fetched_content, causal_taint=taint)
    
    # 4. Check cache hit
    hit = cache.get(url)
    print("4. Intento de caché secundario (debe ser HIT):", hit is not None)
    assert hit == fetched_content
    print("\n[SUCCESS] Pipeline de Caché Termodinámica Nivel 0 y Filtro Popperiano Verificados en C5-REAL.")

if __name__ == "__main__":
    run_test()
