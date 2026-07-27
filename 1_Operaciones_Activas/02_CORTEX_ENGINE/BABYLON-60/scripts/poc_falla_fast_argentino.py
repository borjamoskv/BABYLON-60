# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import sys
import time
import sqlite3
import multiprocessing
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

try:
    import strike_rs
except ImportError as e:
    print(f"[!] Error importando strike_rs nativo: {e}")
    sys.exit(1)

def print_header(title):
    print("\n" + "="*70)
    print(f" ☢️  {title}")
    print("="*70)

def simulate_policy(name, latency_ms, topology, payload_override=None):
    print(f"\n[*] INYECTANDO POLÍTICA: {name}")
    print(f"    - Latencia Burocrática: {latency_ms}ms")
    print(f"    - Topología: {topology}")

    engine = strike_rs.BftSwarmEngine(50, 1000)

    for i in range(100):
        node_id = f"tx_{name}_{i}"
        deps = []
        payload_str = f"Inversión de Infraestructura #{i} (Exergía Validada)"

        # Override a specific node with a fallacy
        if payload_override and i == 42:
            payload_str = payload_override

        # Topology
        if topology == "Secuencial (Burocracia)":
            if i > 0:
                deps.append(f"tx_{name}_{i - 1}")
        else: # Wide DAG
            if i > 0:
                deps.append(f"tx_{name}_0")

        engine.add_node(node_id, deps, payload_str, latency_ms, False)

    start_t = time.perf_counter()
    db_path = "cortex_memory_bft.db"
    try:
        # Puntos base de exergía
        result = engine.run_dag(12.0, 12.0, 0.04, db_path)
        elapsed = time.perf_counter() - start_t
        print("\n[+] RESOLUCIÓN DEL KERNEL RUST:")
        print(f"    > RESULTADO: {result}")
        print(f"    > TIEMPO DE EJECUCIÓN (100 Nodos O(1)): {elapsed:.4f}s")
    except Exception as e:
        print("\n[!] RECHAZO SISTÉMICO DE LA MATRIZ:")
        print(f"    > {e}")

def run_collision_agent(name):
    simulate_policy(name, 2, "Asíncrono (Alta Velocidad)")

def main():
    print("\n\n")
    print("█▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█")
    print("█  M O S K V - 1   A P E X  ::  FALLA-FAST ARGENTINO SIMULATOR (PoC)   █")
    print("█▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█")
    print("\nSimulando colisiones termodinámicas y lógicas contra el BFT Engine en Rust...\n")
    time.sleep(1)

    # 1. Fricción Burocrática (GELABP Abort)
    print_header("ESCENARIO 1: EL FALLA-FAST BUROCRÁTICO")
    print("Narrativa: El estado intenta procesar una política encadenada con múltiples")
    print("           firmas y latencia (Entropy). GELABP evaluará el coste energético.")
    time.sleep(1)
    simulate_policy("Subsidios_Lentos", 10, "Secuencial (Burocracia)")
    time.sleep(2)

    # 2. Rollback Cognitivo (ATMS Contradiction)
    print_header("ESCENARIO 2: EL ROLLBACK COGNITIVO (EXTRACTIVISMO FINANCIERO)")
    print("Narrativa: Una política rápida, pero basada en una premisa falsa que viola")
    print("           las leyes de conservación (Nogood del ATMS).")
    time.sleep(1)
    simulate_policy("Bicicleta_Financiera", 2, "Asíncrono (Alta Velocidad)", payload_override="Emision de Leliqs sin Respaldo")
    time.sleep(2)

    # 3. Hysteresis Extractivista (OS-Lock Abort)
    print_header("ESCENARIO 3: LA HYSTERESIS EXTRACTIVISTA (COLISIÓN MULTI-FONDO)")
    print("Narrativa: Dos fondos buitre atacan los activos de la base de datos simultáneamente.")
    print("           El Sistema Operativo usará O_CREAT|O_EXCL para causar un Fail-Fast físico.")
    time.sleep(1)

    p1 = multiprocessing.Process(target=run_collision_agent, args=("Fondo_Buitre_A",))
    p2 = multiprocessing.Process(target=run_collision_agent, args=("Fondo_Buitre_B",))
    p1.start()
    p2.start()
    p1.join()
    p2.join()
    time.sleep(2)

    # 4. Soberanía Exergética (Exito SQLite WAL)
    print_header("ESCENARIO 4: SOBERANÍA EXERGÉTICA (SINGULARIDAD)")
    print("Narrativa: Política productiva, estructurada asíncronamente (Zero-Cost Wakeups)")
    print("           y lógicamente válida. Debe cruzar la matriz y cristalizar en disco.")
    time.sleep(1)
    simulate_policy("Cosecha_Algoritmica_Soberana", 2, "Asíncrono (Alta Velocidad)")

    print("\n[*] Validando cristalización inmutable en SQLite WAL...")
    try:
        conn = sqlite3.connect("cortex_memory_bft.db", timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM cortex_memory_bft;")
        count = cursor.fetchone()[0]
        print(f"[+] ÉXITO DE AUDITORÍA: {count} registros inmutables BFT consolidados en disco.")
    except Exception as e:
        print(f"[!] Error leyendo SQLite: {e}")

    print("\n\n>>> FIN DE LA SIMULACIÓN <<<")

if __name__ == "__main__":
    main()
