from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes_memory import router as memory_router
from app.api.routes_health import router as health_router
import os

app = FastAPI(title="Cortex Memory")

# Enable CORS for local development and frontend integrations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(memory_router, prefix="/memory")
app.include_router(health_router, prefix="/health")

@app.get("/", response_class=HTMLResponse)
async def read_playground():
    filepath = os.path.join(os.path.dirname(__file__), "templates", "playground.html")
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    return HTMLResponse(content="<h1>Cortex Memory Playground</h1><p>Template playground.html not found.</p>", status_code=404)


