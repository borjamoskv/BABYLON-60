# C5-REAL EXERGY CERTIFIED
import sys
import json
import asyncio
from typing import Optional

class OpenRouterBFTNode:
    """Nodo validador asimétrico que consulta modelos de frontera sobre TCP crudo."""
    __slots__ = ("node_id", "model_endpoint", "api_key", "timeout_ms", "host", "port")

    def __init__(self, node_id: str, model_endpoint: str, api_key: str, timeout_ms: int = 1000):
        self.node_id: str = node_id
        self.model_endpoint: str = model_endpoint
        self.api_key: str = api_key
        self.timeout_ms: float = timeout_ms / 1000.0  # Transmutar a segundos para asyncio
        self.host: str = "openrouter.ai"
        self.port: int = 443  # Tráfico SSL/TLS cifrado estándar

    def _build_http_payload(self, system_prompt: str, user_prompt: str) -> bytes:
        """Construye manualmente la trama HTTP/1.1 POST para mitigar el peso de middleware."""
        body_dict = {
            "model": self.model_endpoint,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.0  # Forzar determinismo absoluto (C5-Fencing)
        }
        json_body = json.dumps(body_dict, separators=(',', ':'))

        # Cabeceras HTTP/1.1 manuales optimizadas para la API de OpenRouter
        http_request = (
            f"POST /api/v1/chat/completions HTTP/1.1\r\n"
            f"Host: {self.host}\r\n"
            f"Authorization: Bearer {self.api_key}\r\n"
            f"Content-Type: application/json\r\n"
            f"Content-Length: {len(json_body)}\r\n"
            f"User-Agent: C5-REAL-Kernel/1.0 (MOSKV-1)\r\n"
            f"Connection: close\r\n\r\n"
            f"{json_body}"
        )
        return http_request.encode('utf-8')

    async def query_oracle(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        """
        Envuelve la llamada al oráculo en un socket SSL puro de asyncio con Circuit Breaker.
        Garantiza tiempo de respuesta acotado O(1) ante degradaciones de red.
        """
        payload = self._build_http_payload(system_prompt, user_prompt)

        try:
            # Ejecución protegida bajo ventana temporal estricta contra anergía por latencia
            return await asyncio.wait_for(
                self._execute_ssl_transfer(payload),
                timeout=self.timeout_ms
            )
        except asyncio.TimeoutError:
            sys.stderr.write(f"[⚠️ CIRCUIT BREAKER] {self.node_id} abortó consulta por timeout (> {self.timeout_ms*1000}ms).\n")
            return None
        except Exception as e:
            sys.stderr.write(f"[💥 ERR_NET] Fallo en la comunicación TCP del nodo {self.node_id}: {e}\n")
            return None

    async def _execute_ssl_transfer(self, payload: bytes) -> Optional[str]:
        """Abre el socket SSL y procesa la trama de respuesta de la API."""
        import ssl
        ssl_context = ssl.create_default_context()
        reader, writer = await asyncio.open_connection(self.host, self.port, ssl=ssl_context)

        writer.write(payload)
        await writer.drain()

        response_bytes = await reader.read(-1)
        writer.close()
        await writer.wait_closed()

        response_text = response_bytes.decode('utf-8', errors='replace')

        # Segmentación manual del cuerpo de la respuesta HTTP
        if "\r\n\r\n" in response_text:
            json_body = response_text.split("\r\n\r\n", 1)[1]
            # Handle chunked transfer encoding if present (OpenRouter doesn't usually chunk short replies with Connection: close, but just in case we strip hexadecimal chunk sizes if needed. For simplicity we assume simple JSON)
            try:
                # Si el servidor responde con 200 OK
                if "200 OK" in response_text.split("\r\n")[0]:
                    # Limpiamos artefactos de chunking si los hay (Opcional, pero OpenRouter con HTTP/1.1 y Connection close lo manda limpio si evitamos chunked request)
                    # Intentamos extraer el primer objeto JSON válido
                    start_idx = json_body.find('{')
                    end_idx = json_body.rfind('}') + 1
                    if start_idx != -1 and end_idx != -1:
                        data = json.loads(json_body[start_idx:end_idx])
                        return data["choices"][0]["message"]["content"]
            except Exception:
                pass
        return None

class HeterogeneousBFTCoordinator:
    __slots__ = ("nodes",)

    def __init__(self, api_key: str):
        self.nodes = [
            OpenRouterBFTNode("NODE_0_SONNET", "anthropic/claude-3.5-sonnet", api_key),
            OpenRouterBFTNode("NODE_1_LLAMA", "meta-llama/llama-3.1-70b-instruct", api_key),
            OpenRouterBFTNode("NODE_2_GEMINI", "google/gemini-1.5-pro", api_key)
        ]

    async def audit_task_completion(self, task_description: str, agent_evidence: str) -> bool:
        """Somete la aserción de cierre al escrutinio del quórum de pesos cruzados."""
        sys.stdout.write("\\n[🛡️ L4 QUORUM] Iniciando escrutinio de aserción en malla heterogénea...\\n")

        sys_prompt = "Actúa como un validador formal de sistemas. Responde únicamente 'TRUE' si la evidencia física demuestra inequívocamente que la tarea ha finalizado con éxito, o 'FALSE' si es una alucinación o carece de pruebas en disco."
        user_prompt = f"Tarea: {task_description}\\nEvidencia del Agente: {agent_evidence}"

        tasks = [node.query_oracle(sys_prompt, user_prompt) for node in self.nodes]
        results = await asyncio.gather(*tasks)

        votos_validos = 0
        votos_falso_positivo = 0

        for node, res in zip(self.nodes, results):
            if res is None:
                sys.stdout.write(f"[⚙️ INTERNO] {node.node_id}: ABSTENCIÓN (Fallo de red/Circuit Breaker).\\n")
                continue

            decision = res.strip().upper()
            sys.stdout.write(f"[⚙️ INTERNO] {node.node_id} emitió veredicto: {decision}\\n")

            if "TRUE" in decision:
                votos_validos += 1
            elif "FALSE" in decision:
                votos_falso_positivo += 1

        sys.stdout.write(f"\\n[📊 CONVERGENCIA] Resultados finales: Válidos: {votos_validos} | Fraudes Detectados: {votos_falso_positivo}\\n")

        if votos_falso_positivo >= 1:
            return False
        return votos_validos >= 2
