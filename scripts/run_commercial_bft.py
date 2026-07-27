import sys
import time
import sqlite3
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import strike_rs
except ImportError as e:
    print(f"[!] Error importando strike_rs nativo: {e}")
    sys.exit(1)

def run_swarm(pass_name):
    print(f"\n[*] Iniciando {pass_name} (Hyper-Exergy: 2ms)")
    engine = strike_rs.BftSwarmEngine(50, 1000)
    for i in range(150):
        node_id = f"tx_arb_{pass_name}_{i}"
        deps = []
        payload_str = f"Payload {i}"
        latency_ms = 2
        
        if pass_name == "COGNITIVE_PASS" and i == 42:
            payload_str = "Infinite Fiat Issuance" # Trampa lógica inyectada

        if pass_name == "CHAOS_PASS":
            if i > 0:
                deps.append(f"tx_arb_{pass_name}_{i - 1}")
        else:
            if i > 0:
                deps.append(f"tx_arb_{pass_name}_0")
        engine.add_node(node_id, deps, payload_str, latency_ms, False)

    start_t = time.perf_counter()
    db_path = "cortex_memory_bft.db"
    try:
        result = engine.run_dag(12.0, 12.0, 0.04, db_path)
        elapsed = time.perf_counter() - start_t
        print(f"[+] RESULTADO ({pass_name}): {result}")
        print(f"[+] Tiempo Total ({pass_name}): {elapsed:.4f}s")
    except Exception as e:
        print(f"[!] BFT ROLLBACK ({pass_name}): {e}")

def main():
    print("==================================================")
    print("  MOSKV-1 APEX: MULTI-SWARM HYSTERESIS COLLISION")
    print("==================================================")
    
    # PASS 1: Chaos Engineering (Sequential, to fail GELABP)
    run_swarm("CHAOS_PASS")
    
    # PASS 2: Hyper-Exergy (Wide DAG, 2ms, to succeed)
    run_swarm("EXERGY_PASS")
    
    # PASS 3: Cognitive Rollback (Wide DAG, 2ms, Logical Impossibility)
    run_swarm("COGNITIVE_PASS")

    # VERIFY SQLITE WAL FLUSH
    print("\n[*] Validando cristalización inmutable en SQLite WAL...")
    try:
        conn = sqlite3.connect("cortex_memory_bft.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cortex_memory_bft;")
        count = cursor.fetchone()[0]
        print(f"[+] Validación DB: {count} registros BFT consolidados en disco.")
        
        cursor.execute("SELECT node_id, proof FROM cortex_memory_bft LIMIT 1;")
        sample = cursor.fetchone()
        if sample:
            print(f"[+] Muestra Criptográfica -> Nodo: {sample[0]} | Hash BLAKE3: {sample[1][:16]}...")
    except Exception as e:
        print(f"[!] Error leyendo SQLite: {e}")

    print("==================================================")

if __name__ == "__main__":
    main()
