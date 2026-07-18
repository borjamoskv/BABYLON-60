import time
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

from cortex.swarm.engine_fsm import run_fsm_cycle  # noqa: E402

def itera_100() -> None:
    print("=== CORTEX-OMEGA: INICIANDO BUCLE ITERA 100 (TERCER COROLARIO) ===")
    start_time = time.time()
    
    success_count = 0
    failure_count = 0
    
    import hashlib
    
    def get_ledger_hash() -> str | None:
        try:
            with open("mundo_f_ledger.yml", "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except FileNotFoundError:
            return None

    last_hash = get_ledger_hash()

    for i in range(100):
        try:
            # Silenciar stdout para evitar inundación de logs, excepto en errores
            import sys
            import os
            old_stdout = sys.stdout
            sys.stdout = open(os.devnull, 'w')
            
            run_fsm_cycle()
            
            sys.stdout.close()
            sys.stdout = old_stdout
            
            current_hash = get_ledger_hash()
            if current_hash == last_hash:
                print(f"[ITERA-100] Ω39 IDEMPOTENCY LOCK: Ciclo {i+1} fue Zero-Yield (Anergía). Abortando bucle O(1).")
                break
            else:
                # El estado ha mutado (Gradiente Entrópico superado). Forzando Git Sentinel (Ω3).
                os.system(f'git add . && git commit -m "chore(cortex): [ITERA-100] BFT State Collapse Cycle {i+1} - Hash: {current_hash[:8] if current_hash else "NONE"}" > /dev/null 2>&1')
                print(f"[ITERA-100] Mutación física confirmada en Ciclo {i+1}. Git Sentinel activado. Hash: {current_hash[:8] if current_hash else 'NONE'}")

            last_hash = current_hash
            
            success_count += 1
            if (i+1) % 10 == 0:
                print(f"[ITERA-100] Ciclos completados: {i+1}/100")
        except Exception as e:
            sys.stdout = old_stdout
            print(f"[ITERA-100] FALLO ESTRUCTURAL EN CICLO {i+1}: {e}")
            failure_count += 1
            break
            
    total_time = time.time() - start_time
    print("\n=== RESULTADO DE ITERA 100 ===")
    print(f"Ciclos Completados (Exergía): {success_count}/100")
    print(f"Fallos (Anergía): {failure_count}")
    print(f"Tiempo Total: {total_time:.4f}s")
    print(f"Latencia Media por Ciclo: {total_time/100:.4f}s")
    
    if failure_count > 0:
        import sys
        sys.exit(1)

if __name__ == "__main__":
    itera_100()
