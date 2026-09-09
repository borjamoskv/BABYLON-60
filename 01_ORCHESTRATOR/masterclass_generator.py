import json
import urllib.request
import urllib.error
import os
import subprocess
import time

# Usando la API de OpenAI rescatada del entorno (GPT-4o)
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "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")
REMOTION_DIR = "/Users/borjafernandezangulo/BABYLON-60/02_TRANSDUCERS/video_remotion"
PAYLOAD_PATH = os.path.join(REMOTION_DIR, "public", "payload.json")

def generate_script_via_llm(topic: str):
    print(f"\n[01_ORCHESTRATOR] 🧠 Contactando Reactor OpenAI (GPT-4o) para: '{topic}'")
    
    prompt = f"""
    Eres el núcleo de inteligencia C5-REAL. Escribe el guion para un vídeo corto sobre: '{topic}'.
    El vídeo se divide en 3 escenas secuenciales.
    Para cada escena, calcula la física del movimiento de la tipografía:
    - Conceptos densos/pesados: mass > 1.5, stiffness < 80.
    - Conceptos ligeros/ágiles: mass < 0.8, stiffness > 120.

    Responde ÚNICAMENTE con un JSON puro, con esta estructura exacta:
    {{
      "title": "TÍTULO CORTO",
      "sessionHash": "AX-GPT4O",
      "scenes": [
        {{
          "durationInFrames": 200,
          "text": "Frase de impacto sobre el tema que quepa en la pantalla",
          "physics": {{"mass": 1.0, "damping": 15, "stiffness": 100}}
        }},
        {{
          "durationInFrames": 200,
          "text": "Frase 2",
          "physics": {{"mass": 2.0, "damping": 15, "stiffness": 50}}
        }},
        {{
          "durationInFrames": 200,
          "text": "Frase 3",
          "physics": {{"mass": 0.5, "damping": 15, "stiffness": 150}}
        }}
      ]
    }}
    """

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        data=json.dumps({
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": prompt}]
        }).encode("utf-8")
    )

    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode("utf-8"))
        raw_json = data["choices"][0]["message"]["content"]
        if raw_json.startswith("```json"):
            raw_json = raw_json[7:-3]
        return json.loads(raw_json.strip())
    except Exception as e:
        print(f"❌ Fallo en la comunicación con OpenAI: {e}")
        exit(1)

def build_video(payload: dict):
    with open(PAYLOAD_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
        
    print(f"\n[02_TRANSDUCERS] 🎞️ Cristal inyectado. Renderizando {len(payload['scenes'])} escenas en React...")
    
    cmd = [
        "npx", "remotion", "render", "src/index.ts", "BabylonMasterclass", 
        "out/clase_sota.mp4", f"--props={PAYLOAD_PATH}", "--concurrency=2"
    ]
    
    start = time.perf_counter()
    subprocess.run(cmd, cwd=REMOTION_DIR, check=True)
    print(f"✅ VÍDEO SOTA CREADO en {time.perf_counter() - start:.2f}s: out/clase_sota.mp4")

if __name__ == "__main__":
    import sys
    tema = sys.argv[1] if len(sys.argv) > 1 else "Estética SOTA 2026: Brutalismo Matemático y Física Semántica"
    cristal = generate_script_via_llm(tema)
    print("\n💎 Cristal Generado:\n", json.dumps(cristal, indent=2, ensure_ascii=False))
    build_video(cristal)
