# C5-REAL EXERGY CERTIFIED
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Any, Dict

from babylon60.bft.ledger_actor import BFTLedgerActor, LedgerEvent

router = APIRouter(prefix="/api/ultrathink", tags=["ultrathink"])

# Global singleton for the ULTRATHINK BFT Actor
_bft_actor = None

async def start_bft_actor():
    global _bft_actor
    if _bft_actor is None:
        db_path = Path("ultrathink_api_ledger.db").resolve()
        _bft_actor = BFTLedgerActor(db_path)
        await _bft_actor.start()

async def stop_bft_actor():
    global _bft_actor
    if _bft_actor is not None:
        await _bft_actor.stop()
        _bft_actor = None

def get_bft_actor() -> BFTLedgerActor:
    global _bft_actor
    if _bft_actor is None:
        raise RuntimeError("BFTLedgerActor is not running. Did lifespan fail?")
    return _bft_actor

class DispatchPayload(BaseModel):
    stream: str = Field(..., description="Target stream (e.g., 'swarm_tasks')")
    entity_id: str = Field(..., description="ID of the entity or agent")
    event_type: str = Field(..., description="Action type (e.g., 'EXECUTE_SKILL')")
    payload: Dict[str, Any] = Field(..., description="The intent data")
    cortex_taint: str = Field(default="[CORTEX-TAINT:api_zero_point]", description="Causal signature")
    source_db: str = Field(default="api_gateway")
    source_table: str = Field(default="http_post")
    source_pk: str = Field(..., description="Idempotency key from client")

@router.post("/dispatch")
async def dispatch_intent(data: DispatchPayload):
    """
    Inyecta una intención directamente en el Orquestador BFT (Axioma 14).
    Aplica el Stateful Load Shedding (Hysteresis) limitando payloads masivos.
    """
    # Hysteresis Volume Gate (Swarm DoS Protection)
    payload_vol = len(str(data.payload))
    if payload_vol > 25000:  # 25KB limit
        raise HTTPException(status_code=413, detail="Payload exceeds 25KB Hysteresis limit. Request Rejected.")

    actor = get_bft_actor()

    event = LedgerEvent(
        stream=data.stream,
        entity_id=data.entity_id,
        event_type=data.event_type,
        payload=data.payload,
        cortex_taint=data.cortex_taint,
        source_db=data.source_db,
        source_table=data.source_table,
        source_pk=data.source_pk,
    )

    try:
        # Awaits the resolution of the BFT WAL queue
        receipt = await actor.append(event)
        return {"status": "dispatched", "bft_receipt": receipt}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
