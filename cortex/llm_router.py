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
    """Parseador de YAML para ontología de rutas (Ω15)."""
    if not os.path.exists(filepath):
        raise EpistemicHalt(f"Archivo de ontología de rutas no encontrado: {filepath}")

    try:
        import yaml
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if isinstance(data, dict) and "routes" in data:
                return data["routes"]
    except ImportError:
        pass

    routes = []
    current_route: Any = {}

    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse simple routes manually if PyYAML is not installed
    import re
    route_blocks = content.split("- name:")
    for block in route_blocks[1:]:
        lines = block.strip().splitlines()
        name_line = lines[0].strip().strip('"').strip("'")
        route_obj: Any = {"name": name_line}

        models_match = re.search(r"models:\s*\[(.*?)\]", block, re.DOTALL)
        if models_match:
            raw_models = models_match.group(1)
            models = [m.strip().strip('"').strip("'") for m in raw_models.split(",") if m.strip()]
            route_obj["models"] = models

        url_match = re.search(r"url:\s*\"?(.*?)\"?\s*$", block, re.MULTILINE)
        if url_match:
            route_obj["url"] = url_match.group(1).strip('"')

        routes.append(route_obj)

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
