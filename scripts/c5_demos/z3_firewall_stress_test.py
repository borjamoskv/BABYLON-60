#!/usr/bin/env python3
"""
[AX-23] TOPOLOGY: Z3 SMT Firewall Stress Test
Ejecuta 1000 iteraciones empíricas para certificar latencias de Falsación Temprana.
"""

import time
import os
import sys
import psutil

# Ajuste del path para importar el firewall desde el kernel
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from babylon60.kernel.z3_firewall import Z3Firewall, Saga1ApoptosisError


def measure_memory_mb() -> float:
    process = psutil.Process(os.getpid())
    return process.memory_info().rss / (1024 * 1024)


def run_stress_test(iterations: int = 1000) -> None:
    print(f"=== INICIANDO PRUEBA DE ESTRÉS Z3 FIREWALL ({iterations} ITERACIONES) ===")
    firewall = Z3Firewall(timeout_ms=500)

    # Reducimos los logs de Z3Firewall para evitar asfixia I/O en consola
    import logging

    logging.getLogger("babylon60.kernel.z3_firewall").setLevel(logging.CRITICAL)

    # Warmup para que Z3 cargue su DLL y Contexto Global (evita falso positivo de leak)
    try:
        firewall.validate_mcp_contract(1, 1.0)
    except Exception:
        pass

    start_mem = measure_memory_mb()
    print(f"Memoria Inicial (Post-Warmup): {start_mem:.2f} MB")

    start_time = time.perf_counter()
    apoptosis_count = 0
    success_count = 0

    for i in range(iterations):
        # Alternamos entre propuestas válidas y alucinaciones estocásticas
        if i % 2 == 0:
            # Valid (Exergy 0.70, 5 params)
            if firewall.validate_mcp_contract(parameters_count=5, estimated_exergy=0.70):
                success_count += 1
        else:
            # Invalid (Exergy 0.50, 2 params) -> Debería disparar apoptosis
            try:
                firewall.validate_mcp_contract(parameters_count=2, estimated_exergy=0.50)
            except Saga1ApoptosisError:
                apoptosis_count += 1

        if (i + 1) % 250 == 0:
            current_mem = measure_memory_mb()
            print(f"Iteración {i + 1}/{iterations} | Memoria: {current_mem:.2f} MB")

    total_time = time.perf_counter() - start_time
    end_mem = measure_memory_mb()
    mem_delta = end_mem - start_mem
    avg_latency = (total_time / iterations) * 1000

    print("\n=== REPORTE TERMODINÁMICO ===")
    print(f"Iteraciones Totales : {iterations}")
    print(f"Validaciones (SAT)  : {success_count}")
    print(f"Apoptosis (UNSAT)   : {apoptosis_count}")
    print(f"Tiempo Total        : {total_time:.3f} s")
    print(f"Latencia Promedio   : {avg_latency:.3f} ms / llamada")
    print(f"Deriva de Memoria   : {mem_delta:+.2f} MB")
    print("===============================\n")

    if avg_latency > 50.0:
        print("[WARNING] Fricción Térmica Detectada: Latencia promedio supera 50ms.")
        sys.exit(1)
    if mem_delta > 10.0:
        print("[WARNING] Fuga de Memoria Detectada: Deriva superior a 10MB.")
        sys.exit(1)

    print("[OK] Prueba de estrés superada. Firewall Z3 opera en Ring-0 bajo límites de Landauer.")
    sys.exit(0)


if __name__ == "__main__":
    run_stress_test(1000)
