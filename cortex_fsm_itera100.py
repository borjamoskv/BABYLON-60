import time
from cortex.swarm.engine_fsm import run_fsm_cycle

def itera_100():
    print("=== CORTEX-OMEGA: INICIANDO BUCLE ITERA 100 (TERCER COROLARIO) ===")
    start_time = time.time()
    
    success_count = 0
    failure_count = 0
    
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
