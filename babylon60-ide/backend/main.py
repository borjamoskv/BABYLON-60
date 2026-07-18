"""
BABYLON60 IDE — FastAPI application entry point.
Serves the API backend and static frontend files.
"""

from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from .routes import analytics, delegation, ledger, ontology, query, sentinel, telemetry, inference
from .services import cortex_ledger

logger = logging.getLogger("babylon60")

app = FastAPI(
    title="BABYLON60 IDE",
    description="Sovereign IDE for tamper-evident agent memory inspection",
    version="0.4.0",
)

# Initialize the IDE's own CortexLedger (append-only, hash-chained).
cortex_ledger.init(Path(__file__).parent.parent.parent)

# GZip — comprime bundle estático + respuestas JSON grandes por el puente.
app.add_middleware(GZipMiddleware, minimum_size=1024)

# CORS — solo localhost. Verbos/headers acotados a lo que los routers usan
# (defensa en profundidad; la extensión MV3 no depende de CORS: usa
# host_permissions que ya evitan la comprobación en el navegador).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    """Cualquier fallo no controlado en un handler sync (threadpool) devuelve
    un 500 JSON estable, sin filtrar el traceback al cliente (Ley 1: Falla =
    Crash Causal, pero contenida y auditable en el log del servidor)."""
    logger.exception("unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Error interno (ver log del servidor)"})

# Mount API routes
app.include_router(ledger.router)
app.include_router(analytics.router)
app.include_router(ontology.router)
app.include_router(query.router)
app.include_router(sentinel.router)
app.include_router(delegation.router)
app.include_router(telemetry.router)
app.include_router(inference.router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "babylon60-ide"}


# Serve static frontend (production build)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
