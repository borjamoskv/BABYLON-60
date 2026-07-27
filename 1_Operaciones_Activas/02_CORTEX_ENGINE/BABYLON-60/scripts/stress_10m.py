# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import strike_rs
except ImportError as e:
    print(f"[!] Error importando strike_rs nativo: {e}")
    sys.exit(1)

def main():
    print(" 🚀  MOSKV-1 APEX :: 100,000 NODE SINGULARITY STRESS TEST")
    print("="*80)
    sys.stdout.flush()

    count = 100_000
    print(f"[*] Solicitando inyección de {count:,} nodos BFT directamente en la memoria C/Rust...")
    print("[*] Advertencia: Esto consumirá RAM masiva. Preparando Generador DAG Nativo...\n")

    engine = strike_rs.BftSwarmEngine(500, count) # High concurrency limit

    db_path = "stress_memory_10m.db"

    # We will measure the raw performance of native DAG execution
    print("[*] Iniciando explosión termodinámica (Zero-Cost Wakeups + Bulk SQLite WAL)...")
    start_t = time.perf_counter()

    try:
        # Calls the Rust native loop which bypasses PyO3 completely
        engine.stress_test_native(count)
        result = engine.run_dag(100.0, 100.0, 0.0, db_path)
        elapsed = time.perf_counter() - start_t

        print("\n[+] SUPERVIVENCIA CONFIRMADA. EL KERNEL NO COLAPSÓ.")
        print(f"    > RESULTADO: {result}")
        print(f"    > TIEMPO TOTAL: {elapsed:.4f}s")
        print(f"    > THROUGHPUT: {count / elapsed:,.2f} hashes/s")
    except Exception as e:
        print("\n[!] COLAPSO TERMODINÁMICO:")
        print(f"    > {e}")
    sys.stdout.flush()

if __name__ == "__main__":
    main()
