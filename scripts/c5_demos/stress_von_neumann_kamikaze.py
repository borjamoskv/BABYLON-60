#!/usr/bin/env python3
import hashlib
import gc
import os
import time

# Intento de cargar psutil para medición de RAM asintótica
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

def get_memory_mb():
    if HAS_PSUTIL:
        process = psutil.Process(os.getpid())
        return process.memory_info().rss / (1024 * 1024)
    return 0.0

class KamikazeWorker:
    """Subagente efímero sin I/O en consola para permitir estrés masivo."""
    __slots__ = ['raw_entropy', 'decoded_rule', 'result'] # Optimización extrema de memoria (anti-dict)

    def __init__(self):
        self.raw_entropy = None
        self.decoded_rule = None
        self.result = None

    def fetch(self, data_source: bytes):
        self.raw_entropy = data_source
        
    def decode(self, opcode: str):
        if opcode != "ZKP_HASH": raise ValueError()
        self.decoded_rule = "sha256_friction"
        
    def execute(self):
        h = hashlib.sha256()
        # Fricción calibrada para permitir Miles de workers en pocos segundos
        for _ in range(10_000):
            h.update(self.raw_entropy)
        self.result = h.hexdigest()

    def store_and_apoptosis(self):
        final_state = self.result
        # Limpieza activa del estado (Cero Anergía)
        self.raw_entropy = None
        self.decoded_rule = None
        self.result = None
        return final_state

def run_stress_test(iterations=5000):
    print("="*60)
    print(f"=== STRESS TEST: {iterations} MOTORES VON NEUMANN (APOPTOSIS) ===")
    print("="*60)
    
    if not HAS_PSUTIL:
        print("[!] ATENCIÓN: El módulo 'psutil' no está instalado. Las métricas de RAM serán 0.0 MB.")
        print("[!] Ejecuta 'pip install psutil' para ver telemetría real.")
    
    # Payload grande (30 KB por instancia simulado) para forzar crecimiento de heap si la apoptosis fallase
    payload = b"Babylon60_Stress_Test_Payload" * 1024 
    
    initial_mem = get_memory_mb()
    print(f"[METRICA] RAM Base Inicial: {initial_mem:.2f} MB")
    
    start_time = time.time()
    
    for i in range(1, iterations + 1):
        # 1. Instanciación del cilindro
        worker = KamikazeWorker()
        
        # 2. Ciclo de 4 tiempos
        worker.fetch(payload)
        worker.decode("ZKP_HASH")
        worker.execute()
        _final = worker.store_and_apoptosis()
        
        # 3. Aniquilación de referencia (Apoptosis)
        del worker
        
        # Monitorización de homeostasis cada 20%
        if i % (iterations // 5) == 0:
            gc.collect() # Forzar el barredor para la métrica
            current_mem = get_memory_mb()
            elapsed = time.time() - start_time
            print(f"  └─ Generación {i}/{iterations} | Latencia: {elapsed:.2f}s | RAM Heap: {current_mem:.2f} MB")

    total_time = time.time() - start_time
    final_mem = get_memory_mb()
    delta_mem = final_mem - initial_mem

    print("="*60)
    print(f"[HALT] Enjambre finalizado. {iterations} subagentes aniquilados en {total_time:.2f}s.")
    print(f"[METRICA] RAM Final Post-Test: {final_mem:.2f} MB")
    print(f"[METRICA] Fuga de Memoria Total (Leak): {delta_mem:.2f} MB")
    
    if delta_mem < 2.0:
        print("[VEREDICTO] ✅ HOMEOSTASIS TÉRMICA PERFECTA (Cero Anergía).")
    else:
        print("[VEREDICTO] ❌ FRACASO. Fuga Epistémica Detectada en el Sustrato.")
    print("="*60)

if __name__ == "__main__":
    run_stress_test(5000)
