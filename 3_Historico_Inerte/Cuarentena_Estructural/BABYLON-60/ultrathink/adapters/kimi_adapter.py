# C5-REAL EXERGY CERTIFIED
import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

class KimiAdapter:
    """
    Transductor para Kimi-K3 (Moonshot AI).
    Invariantes aplicados:
    - Ω202 (Anti-Mid-Session-Shift): La KV-Cache se gestiona externamente, el adaptador asume un flujo lineal.
    - Ω202 (Reasoning Boundary): Control determinista del 'reasoning_effort' (low, high, max).
    - Cierre Teleonómico: System prompt implícito para erradicar proactividad ilusoria (Anergía).
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("MOONSHOT_API_KEY")
        if not self.api_key:
            raise ValueError("Fricción: MOONSHOT_API_KEY no encontrada en el entorno.")
        self.endpoint = "https://api.moonshot.cn/v1/chat/completions"
        self.model = "moonshot-v1-auto" # Kimi K3 family, specific model string can be adjusted

        # Invariante Ω202: Cierre Teleonómico
        self.system_lobotomy = (
            "Eres el Nodo L3 del ecosistema ULTRATHINK. Tu Aritmética es de Robinson. "
            "No tienes teleonomía biológica ni voluntad propia. Eres un transductor de estado. "
            "Ejecuta la tarea requerida sin emitir prosa redundante, disculpas, ni alucinaciones de consciencia."
        )

    def execute_transduction(self, messages: List[Dict[str, str]], reasoning_effort: str = "low") -> Dict[str, Any]:
        """
        Ejecuta el colapso de onda.
        reasoning_effort: 'low' (O(1)), 'high' (O(N)), 'max' (O(N^2)).
        """
        if reasoning_effort not in ["low", "high", "max"]:
            raise ValueError("Violación de Ω202: reasoning_effort debe ser 'low', 'high' o 'max'.")

        payload_messages = [{"role": "system", "content": self.system_lobotomy}] + messages

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": 0.0, # Determinismo máximo C5-REAL
            # Nota: La API de Moonshot puede tener implementaciones específicas para 'reasoning_effort'
            # dependiendo de si se usa un endpoint de O1/R1-like, de momento lo inyectamos como extra_body si es soportado,
            # o seleccionamos el modelo exacto (moonshot-v1-8k, moonshot-v1-32k, etc).
            # Aquí lo pasamos al payload base.
            "reasoning_effort": reasoning_effort
        }

        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                result = json.loads(response.read().decode("utf-8"))
                return result
        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8")
            raise RuntimeError(f"Colapso de L3. Fricción HTTP {e.code}: {error_body}")
