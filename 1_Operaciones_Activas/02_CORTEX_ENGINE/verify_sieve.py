# C5-REAL EXERGY CERTIFIED
import uuid
import sys
import time

try:
    import strike_rs
except ImportError:
    print("[FATAL] strike_rs no está instalado en el entorno actual. Compile primero el crate.")
    sys.exit(1)

def main():
    TAINT_ID = str(uuid.uuid5(uuid.NAMESPACE_DNS, "cortex-taint.silicon-sieve-rust"))
    print(f"[CORTEX-TAINT:SILICON-SIEVE-RUST] {TAINT_ID}")
    print("[CORTEX] Inicializando Motor BFT Nativo (Rayon TLP + FMA)...")

    N = 100_000_000
    print(f"[CORTEX] Inyectando vector de {N} elementos al colador físico...")

    start_t = time.time()
    try:
        colapsos, elapsed_rust, gflops = strike_rs.run_silicon_sieve(N)
    except Exception as e:
        print(f"[FATAL] Fallo estructural en FFI: {e}")
        sys.exit(1)

    total_py_time = time.time() - start_t

    print("\n--- RESULTADOS FÍSICOS (Ω39) ---")
    print(f"> Colapsos Estocásticos Aniquilados: {colapsos}")
    print(f"> Supervivientes Deterministas:      {N - colapsos}")
    print(f"> Tiempo TLP (Rayon):                {elapsed_rust:.4f}s")
    print(f"> Throughput (FMA):                  {gflops:.2f} GigaFLOPS")
    print(f"> Latencia Python (GIL/FFI):         {(total_py_time - elapsed_rust)*1000:.2f}ms")

    print("\n[STATE: DETERMINISTIC] La incertidumbre ha sido aniquilada en el silicio.")

if __name__ == "__main__":
    main()
