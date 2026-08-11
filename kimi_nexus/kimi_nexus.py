import os
import httpx
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

load_dotenv()

# Inicializamos el servidor MCP estándar con Cero Fricción (stdio)
mcp = FastMCP("Kimi Nexus MCP Server")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

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
    messages = [
        {"role": "system", "content": "Eres Kimi, el asistente de IA integrado a través de MCP en BABYLON-60. Utiliza el estándar epistemológico C5-REAL."},
        {"role": "user", "content": prompt}
    ]
    return await call_moonshot(messages)

@mcp.tool()
async def kimi_audit(file_content: str, criteria: str) -> str:
    """Ejecutar auditoría de código bajo invariantes categóricos C5-REAL."""
    messages = [
        {"role": "system", "content": "Eres un auditor estricto de código bajo el protocolo C5-REAL (Categorías de Markov, Lentes Bayesianas). Identifica huecos de existencia, pérdida de exergía y fallos en axiomas."},
        {"role": "user", "content": f"Criterios de auditoría:\n{criteria}\n\nCódigo a auditar:\n```\n{file_content}\n```"}
    ]
    return await call_moonshot(messages)

if __name__ == "__main__":
    # Ejecutamos el servidor MCP utilizando stdio (Zero fricción, no consume puertos locales en background)
    mcp.run(transport='stdio')
