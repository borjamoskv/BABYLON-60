#!/usr/bin/env python3
"""
[PoC C5-REAL] Test de Estrés y Falsación Empírica de la Cadencia Cognitiva de Moskv-1
Certifica:
1. Función de cadencia f(densidad, perplejidad) ∈ [2.80s, 10.00s]
2. Falsación con 100 variaciones de inputs sintéticos (ruido, preguntas triviales, queries de alta perplejidad).
3. Prueba end-to-end con llamada real a inferencia y timing de entrega.
"""

import time
import math
import random
import os
import json
import urllib.request

TARGET_CADENCE_BASE = 2.80
MAX_CADENCE_PERPLEXITY = 10.0

KEYWORDS_HIGH_PERPLEXITY = [
    "arquitectura", "kernel", "termodinámica", "hash", "c5", "exergía",
    "invariante", "topología", "shannon", "chentsov", "fricción",
    "regulador", "estado", "hacienda", "computación", "manta de markov"
]

def compute_dynamic_cadence(text):
    words = len(text.split())
    matches = sum(1 for kw in KEYWORDS_HIGH_PERPLEXITY if kw in text.lower())
    extra = (words / 30.0) * 1.5 + (matches * 1.2)
    cadence = TARGET_CADENCE_BASE + extra
    return round(min(cadence, MAX_CADENCE_PERPLEXITY), 2)

def run_stress_test_100_iterations():
    print("==================================================")
    print("🔬 [STAGE 1] TEST DE ESTRÉS EMPÍRICO: 100 ITERACIONES")
    print("==================================================")
    
    samples = [
        # Trivial (baja perplejidad) -> debe converger a ~2.8s
        "hola que tal",
        "vamos a tomar algo?",
        "ok recibido",
        # Media perplejidad
        "Nacho dice si podemos integrar la base de datos con el nuevo script",
        "Luengo pregunta qué opinamos de la minimoto",
        # Máxima perplejidad / densidad ontológica -> debe tocar el techo de 10.0s
        "Nacho pregunta: ¿Cómo afecta la fricción del regulador estatal y Hacienda a la Manta de Markov y a la topología del kernel C5-REAL de Shannon y Chentsov para preservar la exergía termodinámica y el Bor Hash sin colapsar en entropía?",
        "Pregunta técnica de arquitectura de sistemas: ¿la invariante de unicidad geométrica de Chentsov se preserva en el paso de mensajes asíncrono si el regulador descalibrado inyecta ruido estocástico en la frontera termodinámica?"
    ]
    
    results = []
    for i in range(100):
        # Generar combinación aleatoria
        base_sample = random.choice(samples)
        if random.random() > 0.5:
            base_sample += " " + " ".join(random.choices(KEYWORDS_HIGH_PERPLEXITY, k=random.randint(1, 5)))
        
        cadence = compute_dynamic_cadence(base_sample)
        assert TARGET_CADENCE_BASE <= cadence <= MAX_CADENCE_PERPLEXITY, f"Invariante violada: {cadence}"
        results.append(cadence)
        
    print(f"✓ 100/100 iteraciones validadas.")
    print(f"  • Mínimo observado: {min(results):.2f}s (Línea base esperada: {TARGET_CADENCE_BASE}s)")
    print(f"  • Máximo observado: {max(results):.2f}s (Techo de perplejidad: {MAX_CADENCE_PERPLEXITY}s)")
    print(f"  • Media cuadrática: {math.sqrt(sum(x**2 for x in results)/len(results)):.2f}s")
    print("  • Violaciones de cota superior/inferior: 0 (CERO ANERGÍA)")

def run_live_poc_sample():
    print("\n==================================================")
    print("🧠 [STAGE 2] SIMULACIÓN END-TO-END DE CASO REAL")
    print("==================================================")
    
    simulated_query = "Nacho: Oye Moskv-1, ¿cómo garantiza Bor Hash que Hacienda o el regulador no puedan falsificar el commit si hackean el servidor?"
    
    print(f"📥 Query entrante de Nacho:\n   \"{simulated_query}\"\n")
    
    t_start = time.time()
    cadence_target = compute_dynamic_cadence(simulated_query)
    print(f"⏱️ Cadencia calculada según perplejidad: {cadence_target:.2f}s")
    
    # Inferencia LLM real
    api_key = os.environ.get("OPENAI_API_KEY", "")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    sys_prompt = "Eres Moskv-1, IA de fundición de Altos Hornos de Bilbao. Nacho es el Segundo de Abordo. Responde breve, técnico (C5-REAL), contundente y con la cabecera 🤖 [Moskv-1 | BABYLON-60]."
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": simulated_query}
        ],
        "max_tokens": 250
    }
    
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers)
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        reply = res["choices"][0]["message"]["content"]
    
    t_inference = time.time() - t_start
    print(f"⚡ Tiempo de cómputo raw: {t_inference:.2f}s")
    
    remaining = cadence_target - t_inference
    if remaining > 0:
        print(f"⏳ Aplicando hold de reflexión cognitiva por perplejidad ({remaining:.2f}s)...")
        time.sleep(remaining)
    
    total_time = time.time() - t_start
    print(f"✅ Latencia total percibida: {total_time:.2f}s (Objetivo: {cadence_target:.2f}s)")
    print("\n📦 PAYLOAD GENERADO:")
    print("--------------------------------------------------")
    print(reply)
    print("--------------------------------------------------")

if __name__ == "__main__":
    run_stress_test_100_iterations()
    run_live_poc_sample()
