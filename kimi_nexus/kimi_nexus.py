import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP
try:
    from .swarm_orchestrator import run_swarm_orchestrator
except ImportError:
    from swarm_orchestrator import run_swarm_orchestrator
from lingua import Language, LanguageDetectorBuilder

load_dotenv()

# Inicializamos el servidor MCP estándar con Cero Fricción (stdio)
mcp = FastMCP("Kimi Nexus MCP Server")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
MOONSHOT_API_URL = os.getenv("MOONSHOT_API_URL", "https://api.moonshot.cn/v1/chat/completions")

# Inicializamos el detector de lenguaje AOT (Alta Exergía) para evitar overhead en cada llamada
languages = [Language.ENGLISH, Language.SPANISH, Language.FRENCH, Language.GERMAN, Language.CHINESE, Language.JAPANESE]
detector = LanguageDetectorBuilder.from_languages(*languages).build()

def _inject_language_context(base_system_prompt: str, user_text: str) -> str:
    """Inyecta el idioma detectado en el prompt de sistema para acoplar el LLM al usuario."""
    detected_lang = detector.detect_language_of(user_text)
    if detected_lang:
        return f"{base_system_prompt} El usuario está interactuando en el idioma: {detected_lang.name}."
    return base_system_prompt

async def call_moonshot(messages: list) -> str:
    if not KIMI_API_KEY:
        return "Error: KIMI_API_KEY no está configurada."
    
    headers = {
        "Authorization": f"Bearer {KIMI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "moonshot-v1-auto",
        "messages": messages,
        "temperature": 0.3
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(MOONSHOT_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Error de comunicación con Moonshot: {str(e)}"

@mcp.tool()
async def kimi_ask(prompt: str) -> str:
    """Consultar al oráculo Kimi (Moonshot API) bajo el protocolo C5-REAL."""
    base_sys = "Eres Kimi, el asistente de IA integrado a través de MCP en BABYLON-60. Utiliza el estándar epistemológico C5-REAL."
    sys_prompt = _inject_language_context(base_sys, prompt)
    
    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": prompt}
    ]
    return await call_moonshot(messages)

@mcp.tool()
async def kimi_audit(file_content: str, criteria: str) -> str:
    """Ejecutar auditoría de código bajo invariantes categóricos C5-REAL."""
    base_sys = "Eres un auditor estricto de código bajo el protocolo C5-REAL (Categorías de Markov, Lentes Bayesianas). Identifica huecos de existencia, pérdida de exergía y fallos en axiomas."
    # El idioma se detecta a partir de los criterios de auditoría
    sys_prompt = _inject_language_context(base_sys, criteria)

    messages = [
        {"role": "system", "content": sys_prompt},
        {"role": "user", "content": f"Criterios de auditoría:\n{criteria}\n\nCódigo a auditar:\n```\n{file_content}\n```"}
    ]
    return await call_moonshot(messages)

@mcp.tool()
async def kimi_swarm(prompt: str, p_cores: int = 4, s_threads: int = 1, backend: str = "moonshot") -> str:
    """Orquestar un clúster masivo de subagentes para resolver una tarea compleja en paralelo.
    
    Args:
        prompt: Tarea compleja a descomponer y resolver.
        p_cores: Procesos paralelos (default: 4, Pareto Cero-Thrashing ARM64).
        s_threads: Hilos de I/O por core (default: 1).
        backend: "moonshot" (API remota) | "local_vllm" (vLLM soberano) | "local_mlx" (MLX Apple Silicon).
    """
    return await run_swarm_orchestrator(prompt, p_cores, s_threads, backend)


@mcp.tool()
async def kimi_swarm_local(prompt: str, p_cores: int = 4, s_threads: int = 1) -> str:
    """Clúster soberano air-gapped: usa modelo local vLLM sin conexión a internet."""
    return await run_swarm_orchestrator(prompt, p_cores, s_threads, backend="local_vllm")


if __name__ == "__main__":
    # Ejecutamos el servidor MCP utilizando stdio (Zero fricción, no consume puertos locales en background)
    mcp.run(transport='stdio')
