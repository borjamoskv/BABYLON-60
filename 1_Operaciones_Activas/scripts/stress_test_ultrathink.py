# C5-REAL EXERGY CERTIFIED
import concurrent.futures
import subprocess
import time
import os

def run_iter_ultrathink(thread_id):
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "43_iter_ultrathink.py")
    start = time.time()
    # Run 50 cycles per thread to stress I/O and CPU context switching
    result = subprocess.run(["python3", script_path, "50"], capture_output=True, text=True)
    duration = time.time() - start
    return thread_id, result.returncode, duration

def thermal_stress_test(num_threads=100):
    print(f"[C5-REAL] Iniciando Thermal Stress Test (Multi-Threading) sobre 43_iter_ultrathink.py con {num_threads} hilos...")
    start_time = time.time()

    success_count = 0
    failed_count = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = {executor.submit(run_iter_ultrathink, i): i for i in range(num_threads)}
        for future in concurrent.futures.as_completed(futures):
            tid, code, dur = future.result()
            if code == 0:
                success_count += 1
            else:
                failed_count += 1

    total_time = time.time() - start_time
    print(f"[C5-REAL] STRESS TEST RESULTADOS:")
    print(f" - Hilos Desplegados: {num_threads}")
    print(f" - Éxitos: {success_count} | Fallos (Necrosis): {failed_count}")
    print(f" - Tiempo Total de Ejecución: {total_time:.2f}s")

    if failed_count == 0:
        print("[C5-REAL] Prueba Superada. El stub sintético resiste el estrés concurrente sin colapso físico.")
    else:
        print("[FATAL] El stub no resiste. Violación de BFT detectada.")

if __name__ == "__main__":
    thermal_stress_test(100)  # 100 parallel threads

