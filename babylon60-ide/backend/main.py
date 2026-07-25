from __future__ import annotations
import logging
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .routes import analytics, cortex, delegation, ledger, ontology, query, sentinel, telemetry
from .services import cortex_ledger
logger = logging.getLogger('babylon60')
app = FastAPI(title='BABYLON60 IDE', description='Sovereign IDE for tamper-evident agent memory inspection', version='0.7.0')
cortex_ledger.init(Path(__file__).parent.parent.parent)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://localhost:5174', 'http://127.0.0.1:5173', 'http://127.0.0.1:5174'], allow_credentials=True, allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

@app.exception_handler(Exception)
async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
    logger.exception('unhandled error on %s %s', request.method, request.url.path)
    return JSONResponse(status_code=500, content={'detail': 'Error interno (ver log del servidor)'})
app.include_router(ledger.router)
app.include_router(analytics.router)
app.include_router(ontology.router)
app.include_router(query.router)
app.include_router(sentinel.router)
app.include_router(delegation.router)
app.include_router(cortex.router)
app.include_router(telemetry.router)

@app.get('/api/health')
def health_check() -> dict[str, str]:
    return {'status': 'ok', 'service': 'babylon60-ide'}
FRONTEND_DIST = Path(__file__).parent.parent / 'frontend' / 'dist'
if FRONTEND_DIST.is_dir():
    app.mount('/', StaticFiles(directory=str(FRONTEND_DIST), html=True), name='frontend')