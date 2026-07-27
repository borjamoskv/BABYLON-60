"""
FastAPI Server (Byzantine Boundary)
"""

import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any

import aiosqlite
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Align python path for engine imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from engine.consensus.sanhedrin import SanhedrinTribunal
from engine.database.connection import init_db

# Global DB connection reference
db_conn: aiosqlite.Connection | None = None
tribunal = SanhedrinTribunal()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # CORTEX Directiva Ω9: Inicialización asíncrona determinista antes del tráfico HTTP
    global db_conn
    db_conn = await init_db()
    yield
    # Cleanup on shutdown
    if db_conn:
        await db_conn.close()


app = FastAPI(title="MOSKV-1 Fullstack API", version="1.0.0", lifespan=lifespan)


class FactPayload(BaseModel):
    data: dict[str, Any]
    taint: str
    stripe_token: str | None = None


@app.post("/api/v1/facts")
async def persist_fact(fact: FactPayload):
    if not fact.taint.startswith("taint:"):
        raise HTTPException(
            status_code=403, detail="SAGA-1: Taint absent or invalid. C4-SIM execution blocked."
        )

    if db_conn:
        try:
            await db_conn.execute(
                "INSERT INTO facts (taint, data) VALUES (?, ?)", (fact.taint, json.dumps(fact.data))
            )
            await db_conn.commit()
        except aiosqlite.IntegrityError:
            # Idempotency
            pass
        except Exception as e:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"SAGA-6: DB write failed: {str(e)}")

    return {"status": "COMMITTED", "taint": fact.taint}


@app.post("/api/v1/sanhedrin/judge")
async def judge_fact(fact: FactPayload):
    """
    Endpoints de Monetización:
    1. Pre-autoriza el token de Stripe (Peaje Termodinámico).
    2. Delega al Sanedrín.
    3. Retorna la Firma de Alta Certeza (SANHEDRIN-SEAL) o aborta.
    """
    if not fact.stripe_token:
        raise HTTPException(
            status_code=402, detail="Payment Required: Peaje termodinámico no cubierto."
        )

    try:
        # 1. Ejecución BFT (Gathering)
        judgment = await tribunal.execute_judgment(fact.data)

        # 2. Facturación Stripe (Simulado post-quórum)
        # stripe.Charge.create(amount=50, currency="usd", source=fact.stripe_token)

        return judgment
    except Exception as e:  # noqa: BLE001
        # SAGA-1: Aborto y reverso de pre-autorización
        raise HTTPException(status_code=422, detail=str(e))
