from fastapi import FastAPI, Request
from pydantic import BaseModel
import os
import httpx
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Kimi Nexus MCP Server")
KIMI_API_KEY = os.getenv("KIMI_API_KEY")
MOONSHOT_API_URL = "https://api.moonshot.cn/v1/chat/completions"

class AskRequest(BaseModel):
    prompt: str

class AuditRequest(BaseModel):
    file_content: str
    criteria: str

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

@app.post("/kimi_ask")
async def kimi_ask(req: AskRequest):
    messages = [
        {"role": "system", "content": "Eres Kimi, el asistente de IA integrado a través de MCP en BABYLON-60. Utiliza el estándar epistemológico C5-REAL."},
        {"role": "user", "content": req.prompt}
    ]
    response = await call_moonshot(messages)
    return {"response": response}

@app.post("/kimi_audit")
async def kimi_audit(req: AuditRequest):
    messages = [
        {"role": "system", "content": "Eres un auditor estricto de código bajo el protocolo C5-REAL (Categorías de Markov, Lentes Bayesianas). Identifica huecos de existencia, pérdida de exergía y fallos en axiomas."},
        {"role": "user", "content": f"Criterios de auditoría:\n{req.criteria}\n\nCódigo a auditar:\n```\n{req.file_content}\n```"}
    ]
    response = await call_moonshot(messages)
    return {"response": response}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8050)
