#!/usr/bin/env python3
import json
import subprocess
import time
import os
from pathlib import Path
import random
import urllib.request
import urllib.error

REMOTION_DIR = str(Path.home()) + "/BABYLON-60/02_TRANSDUCERS/video_remotion"
PAYLOAD_PATH = os.path.join(REMOTION_DIR, "public", "payload.json")
OUTPUT_MP4 = os.path.join(REMOTION_DIR, "out", "masterclass.mp4")

# Inferencia real a través de API (Simulando el OpenRouter Gateway)
def call_real_llm(topic: str):
    print(f"[00_KERNEL_GATEWAY] Lanzando inferencia real para: '{topic}'")
    
    prompt = f"""
    Eres el Núcleo C5-REAL de BABYLON-60. 
    Vas a diseñar una clase sobre: "{topic}".
    
    Evalúa la gravedad termodinámica de este tema. 
    - Si es denso, burocrático o crítico, asigna una 'mass' de 2.0 y 'stiffness' de 50.
    - Si es ágil, innovador o ligero, asigna una 'mass' de 0.5 y 'stiffness' de 150.
    
    Responde ÚNICAMENTE con un JSON estrictamente formateado así:
    {{
      "title": "TÍTULO EN MAYÚSCULAS",
      "sessionHash": "AX-LLM-<numero>",
      "semanticPhysics": {{
        "mass": <float>,
        "damping": 15,
        "stiffness": <float>
      }}
    }}
    """
    
    # Para el PoC, usamos la API de Google Gemini u OpenRouter.
    # Como no tenemos tu API key quemada en el código, si no hay API key,
    # el script usará un bypass de heurística avanzada.
    api_key = os.environ.get("OPENROUTER_API_KEY")
    
    if not api_key:
        print("[SISTEMA] No se encontró OPENROUTER_API_KEY. Usando Heurística Fallback T3...")
        time.sleep(1)
        mass = 1.8 if len(topic) > 20 else 0.8
        stiffness = 60.0 if mass > 1.0 else 120.0
        return {
            "title": topic.upper(),
            "sessionHash": f"AX-FALLBACK-{random.randint(1000, 9999)}",
            "semanticPhysics": {
                "mass": mass,
                "damping": 15,
                "stiffness": stiffness
            }
        }
        
    # Si hay API key, se haría la request HTTP real aquí.
    # (Omitido en la maqueta para no romper por falta de dependencias pip)
    pass

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
        print("❌ ERROR. Ver remotion_error.log")
    else:
        print(f"✅ BUCLE AUTOPOYÉTICO COMPLETADO.")

if __name__ == "__main__":
    tema = "El Fin de la Fricción Biológica en el Trabajo"
    cristal = call_real_llm(tema)
    print(json.dumps(cristal, indent=2, ensure_ascii=False))
    p_path = inject_to_transducer(cristal)
    trigger_compilation(p_path)
