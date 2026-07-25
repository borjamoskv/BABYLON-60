# C5-REAL EXERGY CERTIFIED
"""C5-REAL Cascade LLM Router: Ollama → Groq → GitHub Models"""

import os
import json
import urllib.request
from typing import List, TypedDict, Any

__all__ = ["C5LLMRouter"]

class RouteConfig(TypedDict, total=False):
    name: str
    url: str
    models: List[str]

class EpistemicHalt(Exception):
    """Exclusión rígida de excepciones mudas (Ω26)."""

    pass

def parse_yaml_routes(filepath: str) -> List[RouteConfig]:
    """Parseador lineal de YAML sin dependencias para conservar ATP (Ω15)."""
    if not os.path.exists(filepath):
        raise EpistemicHalt(f"Archivo de ontología de rutas no encontrado: {filepath}")

    routes = []
    current_route: Any = {}

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_str = line.strip()
            # Ignorar cabecera y comentarios
            if (
                not line_str
                or line_str.startswith("Claim")
                or line_str.startswith("Proof")
                or line_str.startswith("Base")
                or line_str.startswith("Confidence")
                or line_str.startswith("PrimaryVectors")
                or line_str.startswith("routes:")
            ):
                continue

            if ":" in line_str:
                parts = line_str.split(":", 1)
                key = parts[0].strip()
                val = parts[1].strip()

                # Manejar el caso de un nuevo elemento de la lista (ej: `- name: "GitHub Models"`)
                if key.startswith("-"):
                    if current_route:
                        routes.append(current_route)
                    current_route = {}
                    key = key[1:].strip()

                # Quitar comillas
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("["):
                    # Si el valor contiene ']', se parsea directamente
                    raw_models = val
                    if not raw_models.endswith("]"):
                        # Seguir leyendo hasta el cierre ']'
                        for next_line in f:
                            raw_models += " " + next_line.strip()
                            if "]" in next_line:
                                break
                    raw_content = raw_models[raw_models.find("[")+1:raw_models.rfind("]")]
                    models_list: list[str] = [x.strip()[1:-1] if (x.strip().startswith('"') or x.strip().startswith("'")) else x.strip() for x in raw_content.split(",") if x.strip()]
                    current_route["models"] = models_list
                    continue

                current_route[key] = val

    if current_route:
        routes.append(current_route)

    from typing import cast

    return cast(List[RouteConfig], routes)

class C5LLMRouter:
    """Enrutador de inferencia C5-REAL con tolerancia a fallos en cascada."""

    def __init__(self, routes_path: str = "cortex/ontology/llms_gratuitos_front_routes.yaml") -> None:
        if not os.path.isabs(routes_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            routes_path = os.path.join(project_root, routes_path)
        self.routes = parse_yaml_routes(routes_path)
        self.routes_by_name = {r.get("name", ""): r for r in self.routes}

    def dispatch_inference(self, prompt: str, model: str) -> str:
        """Enruta la petición buscando autarquía local y cascading a APIs gratuitas."""
        errors = []

        # 1. Prioridad: Ollama Local (Autarquía Offline)
        ollama_route = self.routes_by_name.get("Ollama Local Engine")
        if ollama_route and model in ollama_route.get("models", []):
            try:
                return self._call_ollama(str(ollama_route.get("url", "")), model, prompt)
            except (OSError, RuntimeError, ConnectionError, ValueError) as e:
                errors.append(f"Ollama ({model}) falló: {e}")

        # 2. Cascada a Groq Console (Límites Gratuitos)
        groq_route = self.routes_by_name.get("Groq Cloud Console")
        groq_key = os.environ.get("GROQ_API_KEY")
        if groq_route and groq_key:
            try:
                models = groq_route.get("models", [])
                actual_model = models[0] if models else "llama3-70b-8192"
                url = f"{groq_route.get('url')}/v1/chat/completions"
                return self._call_openai_compatible(url, groq_key, actual_model, prompt)
            except (OSError, RuntimeError, ConnectionError, ValueError) as e:
                errors.append(f"Groq ({groq_route.get('name')}) falló: {e}")

        # 3. Cascada a Gemini Pro Multi-Account Pool
        gemini_route = self.routes_by_name.get("Gemini Pro Multi-Account Cluster")
        if gemini_route and (model.startswith("gemini") or "GEMINI_API_KEY" in os.environ):
            try:
                from scripts.gemini_pool_manager import GeminiProPoolManager

                pool = GeminiProPoolManager()
                if pool.slots:
                    target_model = model if model.startswith("gemini") else "gemini-1.5-pro"
                    return pool.dispatch_generate_content(prompt, model=target_model)
            except (RuntimeError, OSError, ValueError) as e:
                errors.append(f"Gemini Pro Multi-Account Pool falló: {e}")

        # 4. Cascada a GitHub Models (Developer Free Tier)
        github_route = self.routes_by_name.get("GitHub Models")
        github_key = os.environ.get("GITHUB_TOKEN")
        if github_route and github_key:
            try:
                models = github_route.get("models", [])
                actual_model = models[0] if models else "Llama-3-8B-Instruct"
                url = "https://models.inference.ai.azure.com/chat/completions"
                return self._call_openai_compatible(url, github_key, actual_model, prompt)
            except (OSError, RuntimeError, ConnectionError, ValueError) as e:
                errors.append(f"GitHub Models falló: {e}")

        # Si todas fallan, levantar pánico epistémico
        error_msg = " // ".join(errors)
        raise EpistemicHalt(f"Consenso de Inferencia fallido. Todas las rutas gratuitas fallaron. Errores: {error_msg}")

    def _call_ollama(self, url: str, model: str, prompt: str) -> str:
        req_data = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode("utf-8")

        req = urllib.request.Request(
            f"{url}/api/generate",
            data=req_data,
            headers={"Content-Type": "application/json"},
        )

        with urllib.request.urlopen(req, timeout=5) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return str(res_data["response"])

    def _call_openai_compatible(self, url: str, token: str, model: str, prompt: str) -> str:
        req_data = json.dumps(
            {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.2,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
        )

        with urllib.request.urlopen(req, timeout=8) as response:
            res_data = json.loads(response.read().decode("utf-8"))
            return str(res_data["choices"][0]["message"]["content"])
