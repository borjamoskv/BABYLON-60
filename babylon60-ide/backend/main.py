"""
BABYLON60 IDE — FastAPI application entry point.
Serves the API backend and static frontend files.
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .routes import arena, ledger, ontology, query, sentinel, telemetry

app = FastAPI(
    title="BABYLON60 IDE",
    description="Sovereign IDE for tamper-evident agent memory inspection",
    version="0.2.0",
)

# CORS — localhost only for v1
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routes
app.include_router(ledger.router)
app.include_router(ontology.router)
app.include_router(query.router)
app.include_router(sentinel.router)
app.include_router(telemetry.router)
app.include_router(arena.router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "babylon60-ide"}


# Serve static frontend (production build)
FRONTEND_DIST = Path(__file__).parent.parent / "frontend" / "dist"
if FRONTEND_DIST.is_dir():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIST), html=True), name="frontend")
