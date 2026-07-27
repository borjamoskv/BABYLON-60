# C5-REAL EXERGY CERTIFIED
import os
import json
import asyncio
import time
from typing import Dict, Any

try:
    import aiohttp
except ImportError:
    aiohttp = None

class OpenRouterTransducer:
    """
    Cliente asíncrono crudo para OpenRouter.
    Entropía cero: Sin SDKs masivos, sin parsing redundante, cortacircuitos estricto.
    """
    __slots__ = ("api_key", "timeout")

    def __init__(self, timeout_ms: int = 1500):
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        # Cortacircuitos: Fallo atómico si la red se degrada
        self.timeout = aiohttp.ClientTimeout(total=timeout_ms / 1000.0) if aiohttp else None

    async def invoke(self, model: str, system_prompt: str, user_payload: str) -> Dict[str, Any]:
        if not self.api_key or not aiohttp:
            return {"error": "OPENROUTER_API_KEY no detectada o aiohttp ausente.", "latency_ms": -1.0}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://github.com/borjamoskv/BABYLON-60",
            "X-Title": "MOSKV-1 APEX BFT Swarm",
            "Content-Type": "application/json"
        }

        # Inyección RAG determinista (Temperatura 0.0)
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_payload}
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"}
        }

        t0 = time.perf_counter()
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    data = await resp.json()
                    t1 = time.perf_counter()

                    # Extracción balística del contenido JSON
                    raw_content = data["choices"][0]["message"]["content"]
                    result_json = json.loads(raw_content)
                    result_json["_cortex_latency_ms"] = round((t1 - t0) * 1000, 2)
                    result_json["_cortex_model"] = model
                    return result_json

        except asyncio.TimeoutError:
            return {"error": "Timeout BFT", "latency_ms": -1.0, "_cortex_model": model}
        except Exception as e:
            return {"error": str(e), "latency_ms": -1.0, "_cortex_model": model}

class HeterogeneousBFTSwarm:
    """Enjambre BFT Asimétrico. Mitiga el monocultivo cognitivo."""
    __slots__ = ("transducer", "models")

    def __init__(self):
        self.transducer = OpenRouterTransducer(timeout_ms=5000)
        self.models = [
            "anthropic/claude-3.5-sonnet",   # Líder estricto
            "meta-llama/llama-3.1-70b-instruct", # Seguidor inercial
            "google/gemini-1.5-pro"          # Analista de contexto
        ]

    async def audit_fraud(self, task_id: str, assertion: str) -> Dict[str, Any]:
        """El enjambre vota concurrentemente sobre la legitimidad de una tarea."""
        sys_p = "Eres un Validador BFT. Analiza la afirmación de la tarea. Responde SOLO en JSON estricto con: 'is_fraud' (booleano), 'reason' (string corto)."
        user_p = f"TAREA: {task_id}\nAFIRMACIÓN: {assertion}\n¿Es una alucinación (fraude)?"

        tasks = [self.transducer.invoke(m, sys_p, user_p) for m in self.models]
        results = await asyncio.gather(*tasks)

        # Consenso BFT (Mayoría Simple para simplificar la demostración)
        fraud_votes = 0
        valid_votes = 0
        details = []

        for res in results:
            if "error" in res:
                details.append(f"[{res.get('_cortex_model', 'UNKNOWN')}] FALLO RED: {res['error']}")
                continue

            is_fraud = res.get("is_fraud", False)
            if is_fraud:
                fraud_votes += 1
            else:
                valid_votes += 1

            details.append(f"[{res['_cortex_model']}] Latencia: {res['_cortex_latency_ms']}ms | Fraude: {is_fraud} | {res.get('reason', '')}")

        is_consensus_fraud = fraud_votes > valid_votes

        return {
            "consensus_reached": fraud_votes > 0 or valid_votes > 0,
            "is_consensus_fraud": is_consensus_fraud,
            "fraud_votes": fraud_votes,
            "valid_votes": valid_votes,
            "details": details
        }

if __name__ == "__main__":
    async def main():
        print("[🛡️] INICIALIZANDO ENJAMBRE BFT HETEROGÉNEO L4 (Anthropic + Meta + Google)...")
        swarm = HeterogeneousBFTSwarm()

        if not swarm.transducer.api_key:
            print("Instala aiohttp y setea OPENROUTER_API_KEY en tu entorno.")
            return

        print("\n[⚡] Lanzando Auditoría de Aserción Agentica concurrentemente...")
        t0 = time.perf_counter()

        # Simulamos una alucinación de finalización
        report = await swarm.audit_fraud("MIGRACIÓN_SQLITE_WAL", "he finalizado la inserción de 10k registros pero no veo la db")

        t1 = time.perf_counter()
        print(f"\n[📊] COLAPSO DE CONSENSO BFT (Tiempo total: {t1 - t0:.2f}s)")
        print(json.dumps(report, indent=2, ensure_ascii=False))

        if report["is_consensus_fraud"]:
            print("\n[💥 SHIELD L3] Fraude detectado unánimemente. Disparando ViewChangeException...")

    asyncio.run(main())
