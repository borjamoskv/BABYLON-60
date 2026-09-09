#!/usr/bin/env python3
import json
import subprocess
import time
import os
from pathlib import Path

REMOTION_DIR = str(Path.home()) + "/BABYLON-60/02_TRANSDUCERS/video_remotion"
KERNEL_DIR = str(Path.home()) + "/BABYLON-60/00_KERNEL/strike-rs"
PAYLOAD_PATH = os.path.join(REMOTION_DIR, "public", "payload.json")
OUTPUT_MP4 = os.path.join(REMOTION_DIR, "out", "masterclass.mp4")

def call_rust_oracle(topic: str):
    """Llama al Oráculo de Rust (00_KERNEL) vía tubería UNIX estándar."""
    print(f"[00_KERNEL] (RUST) Procesando concepto: '{topic}'...")
    
    # Compilamos y ejecutamos el binario Rust pasándole el tema
    cmd = ["cargo", "run", "--quiet", "--bin", "poc_oracle_nexus", "--", topic]
    
    start = time.perf_counter()
    result = subprocess.run(cmd, cwd=KERNEL_DIR, capture_output=True, text=True, check=True)
    end = time.perf_counter()
    
    print(f"[SISTEMA] Latencia del Gateway Rust: {(end-start)*1000:.2f} ms")
    
    # Parseamos el JSON exacto devuelto por Rust
    return json.loads(result.stdout)

def inject_to_transducer(payload: dict):
    os.makedirs(os.path.dirname(PAYLOAD_PATH), exist_ok=True)
    with open(PAYLOAD_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return PAYLOAD_PATH

def trigger_compilation(payload_path: str):
    print(f"[02_TRANSDUCERS] Renderizando vídeo en Remotion...")
    cmd = [
        "npx", "remotion", "render", 
        "src/index.ts", 
        "BabylonMasterclass", 
        "out/masterclass.mp4",
        f"--props={payload_path}",
        "--concurrency=2",
        "--timeout=120000",
        "--overwrite"
    ]
    process = subprocess.Popen(cmd, cwd=REMOTION_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    
    if process.returncode != 0:
        with open("remotion_error.log", "w") as f:
            f.write(stderr.decode("utf-8"))
        print("❌ ERROR. Ver remotion_error.log")
    else:
        print(f"✅ BUCLE AUTOPOYÉTICO COMPLETADO.")
        print(f"✅ Archivo listo en: {OUTPUT_MP4}")

if __name__ == "__main__":
    print("==================================================")
    print(" 👑 REY: EL BUCLE CERRADO (RUST -> PYTHON -> REACT) ")
    print("==================================================")
    
    tema_input = "La Burocracia de Hacienda como Sumidero Termodinámico"
    
    # 1. El cerebro Rust piensa (Kernel)
    cristal = call_rust_oracle(tema_input)
    print("Cristal Semántico Recibido de Rust:\n", json.dumps(cristal, indent=2, ensure_ascii=False))
    
    # 2. Python orquesta
    p_path = inject_to_transducer(cristal)
    
    # 3. React renderiza (Transducer)
    trigger_compilation(p_path)
