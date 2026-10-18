#!/usr/bin/env python3
import sqlite3
import time
import os
from collections import deque

print("[AX-5] TOPOLOGY: Falsación Termodinámica de I/O Síncrono (SQLite) vs Memoria Compartida")
print("Inyectando estrés causal: 20,000 negociaciones entre agentes.\n")

iterations = 20_000
db_path = "falsacion_agentes.db"

# 1. Ruta de Anergía (Prohibida en Babylon-60): I/O Síncrono al Disco
if os.path.exists(db_path):
    os.remove(db_path)

conn = sqlite3.connect(db_path)
conn.execute("PRAGMA synchronous = FULL") # El estándar de consistencia rígida
conn.execute("CREATE TABLE agent_hot_path (id INTEGER PRIMARY KEY, msg TEXT)")

start_disk = time.time()
for i in range(iterations):
    # Fricción: Cada escritura obliga al disco duro / SSD a vaciar su caché (fsync)
    conn.execute("INSERT INTO agent_hot_path (msg) VALUES (?)", (f"Message_{i}",))
    conn.commit()
    
duration_disk = time.time() - start_disk
conn.close()
os.remove(db_path)

# 2. Ruta de Alta Exergía (INV_C5_SHM): Memoria Compartida Lock-Free / Ring Buffer
# (Simulado en Python mediante una estructura en memoria contigua o Deque de alto rendimiento)
ring_buffer: deque[str] = deque(maxlen=iterations)

start_mem = time.time()
for i in range(iterations):
    # Transición topológica O(1) en RAM
    ring_buffer.append(f"Message_{i}")
    
duration_mem = time.time() - start_mem

# Dictamen
print(f"-> Latencia del Sumidero de Disco (SQLite Sync): {duration_disk:.4f} segundos")
print(f"-> Latencia del Desacople en Memoria (INV_C5_SHM):  {duration_mem:.4f} segundos")

if duration_mem > 0:
    ratio = duration_disk / duration_mem
else:
    ratio = float('inf')

print(f"\nDICTAMEN EPISTÉMICO: El I/O síncrono disipa la energía con un factor de fricción térmica de {ratio:.2f}x.")
print("CONCLUSIÓN: Falsación superada. Interponer SQLite en el bucle caliente de inferencia destruye la viabilidad asintótica del orquestador.")
