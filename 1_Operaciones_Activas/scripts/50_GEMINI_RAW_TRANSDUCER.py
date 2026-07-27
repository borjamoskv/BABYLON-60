# C5-REAL EXERGY CERTIFIED
import os
import json
import asyncio
import time
from typing import Dict, Any

try:
    import google.generativeai as genai
except ImportError:
    genai = None

class RawGeminiTransducer:
    """
    C5-REAL Enlace Crudo a Gemini 1.5 Pro.
    Omite todos los filtros de búsqueda comerciales. Opera en entropía térmica máxima.
    """
    __slots__ = ("api_key", "model_name", "model", "safety_settings")

    def __init__(self, model_name: str = "gemini-1.5-pro-latest"):
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key or not genai:
            print("[⚠️] CORTEX WARNING: GEMINI_API_KEY no detectada o SDK ausente.")
            self.model = None
            return

        genai.configure(api_key=self.api_key)
        self.model_name = model_name

        # Desactivación total del Green Theater (C5-REAL Bypass)
        self.safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            safety_settings=self.safety_settings,
            generation_config={"temperature": 0.0, "response_mime_type": "application/json"}
        )

    async def invoke_atomic(self, system_prompt: str, user_payload: str) -> Dict[str, Any]:
        """Invocación O(1) con respuesta determinista forzada en JSON."""
        if not self.model:
            return {"error": "Sustrato API no inicializado"}

        t0 = time.perf_counter()
        # El SDK actual no es estrictamente async por defecto en generate_content,
        # lo envolvemos en run_in_executor para no bloquear el BFT Swarm.
        loop = asyncio.get_running_loop()

        prompt_full = f"{system_prompt}\n\n[USER_PAYLOAD]\n{user_payload}"

        def _call_api():
            return self.model.generate_content(prompt_full)

        try:
            response = await loop.run_in_executor(None, _call_api)
            t1 = time.perf_counter()
            data = json.loads(response.text)
            data["_cortex_latency_ms"] = round((t1 - t0) * 1000, 2)
            return data
        except Exception as e:
            return {"error": str(e), "latency_ms": -1.0}

if __name__ == "__main__":
    async def main():
        transducer = RawGeminiTransducer()
        if not transducer.model:
            print("Instala google-generativeai y setea GEMINI_API_KEY.")
            return

        sys_p = "Eres un Validador BFT. Responde SOLO en JSON con las claves: 'is_fraud' (booleano), 'reason' (string)."
        user_p = "El nodo 4 afirma haber terminado la migración pero el hash del bloque es 0x00."

        print("[⚡] Ejecutando Transductor Crudo sobre Gemini 1.5 Pro...")
        result = await transducer.invoke_atomic(sys_p, user_p)
        print(f"[✅ C5-REAL] Respuesta balística obtenida:\n{json.dumps(result, indent=2)}")

    asyncio.run(main())
