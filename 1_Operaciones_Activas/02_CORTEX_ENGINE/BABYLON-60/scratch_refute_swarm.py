#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Protocolo FALSABILIZA (Ω206) - Swarm Research
Objetivo: Destruir la presunción de éxito de la inyección física de AST/Tests.
"""
import urllib.request
import json
import time
import sys

def refute_ast_transduction():
    url = "http://127.0.0.1:8000/api/swarm/research"
    payload = {
        "topic": "execute",
        "max_workers": 2,
        "enable_cloud_transduction": False,
        "reasoning_effort": "low",
        "cortex_taint": "[CORTEX-TAINT:falsabiliza]"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )

    print("\n[!] DETONANDO FALSABILIZA: Fuego contra AST y Epistemic Invariants")
    try:
        t0 = time.time()
        with urllib.request.urlopen(req) as response:
            res_body = json.loads(response.read().decode('utf-8'))
            latency = time.time() - t0

            # Analizar el nodo AST
            ast_node = next((n for n in res_body.get('synthesis', []) if n.get('node') == 'codebase_ast'), None)
            epistemic_node = next((n for n in res_body.get('synthesis', []) if n.get('node') == 'epistemic_invariants'), None)

            print(f"HTTP 200 (Latencia: {latency:.3f}s)")

            # Condición de Falsación (Rotura termodinámica)
            if ast_node and ast_node.get('ast_modules_parsed', 0) == 0:
                print("\n[CRITICAL FAILURE - FALSADO] El AST Parser retornó PHYSICAL_EXECUTION_SUCCESS pero analizó 0 módulos.")
                print("Causa probable: Rutas de hardware equivocadas o excepciones silenciadas (except pass).")
                print("Anergía detectada: Green Theater (Simulación pasiva disfrazada de código físico).")
                sys.exit(1)
            else:
                print(f"\n[OK] AST Modules Parsed: {ast_node.get('ast_modules_parsed')}")

            if epistemic_node and epistemic_node.get('total_modules', 0) == 0:
                print("\n[CRITICAL FAILURE - FALSADO] El verificador Epistémico retornó SUCCESS pero encontró 0 módulos.")
                sys.exit(1)

    except Exception as e:
        print(f"Error de red: {e}")
        sys.exit(2)

if __name__ == "__main__":
    refute_ast_transduction()
