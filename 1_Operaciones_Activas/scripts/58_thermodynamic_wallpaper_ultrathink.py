# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import psutil
import hashlib
import time

def calculate_hardware_entropy():
    # Read real physical states
    cpu_percent = psutil.cpu_percent(interval=0.1)
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    entropy_string = f"{cpu_percent}-{mem.used}-{disk.used}-{time.time()}"
    return entropy_string

def compute_thermodynamic_tensor(entropy_str):
    tensor_hash = hashlib.sha256(entropy_str.encode('utf-8')).hexdigest()
    return tensor_hash

def generate_thermodynamic_wallpaper():
    raw_entropy = calculate_hardware_entropy()
    tensor = compute_thermodynamic_tensor(raw_entropy)
    print(f"[C5-REAL] Thermodynamic Entropy Extracted: {raw_entropy}")
    print(f"[C5-REAL] BFT Tensor Seed (SHA-256): {tensor}")
    return tensor

if __name__ == "__main__":
    print(">>> Iniciando Fase 1: Extracción Termodinámica Hardware <<<")
    generate_thermodynamic_wallpaper()
    print(">>> Fase 1 Completada (Zero Anergy) <<<\n")
