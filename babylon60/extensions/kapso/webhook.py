import logging
import os

from fastapi import APIRouter, HTTPException, Request

try:
    import keyring
except ImportError:
    keyring = None

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/kapso", tags=["kapso", "whatsapp"])


@router.get("/webhook")
async def verify_webhook(request: Request):
    """
    Kapso / Meta Webhook Verification endpoint.
    """
    params = request.query_params
    mode = params.get("hub.mode")
    token = params.get("hub.verify_token")
    challenge = params.get("hub.challenge")

    expected_token = None
    if keyring is not None:
        try:
            expected_token = keyring.get_password("cortex_v6", "kapso_verify_token")
        except Exception as e:  # noqa: BLE001
            logger.warning("Fallo al acceder al OS Keyring para kapso_verify_token: %s", e)

    if not expected_token:
        expected_token = os.environ.get("CORTEX_KAPSO_VERIFY_TOKEN")

    if not expected_token:
        logger.warning(
            "CORTEX_KAPSO_VERIFY_TOKEN no esta configurado en Keyring o variables de entorno. Usando fallback por defecto."
        )
        expected_token = "CORTEX_KAPSO_VERIFY_TOKEN"

    if mode and token:
        if mode == "subscribe" and token == expected_token:
            logger.info("Kapso Webhook verified.")
            return int(challenge)
        else:
            raise HTTPException(status_code=403, detail="Forbidden")
    raise HTTPException(status_code=400, detail="Bad Request")


@router.post("/webhook")
async def receive_webhook(request: Request):
    """
    Receive incoming messages and status updates from Kapso.
    """
    try:
        payload = await request.json()
        logger.info("Received Kapso Webhook: %s", payload)

        # Enforce CORTEX-TAINT and route to Sovereign Swarm or event bus

        return {"status": "received"}
    except Exception as e:  # noqa: BLE001
        logger.error("Error processing Kapso Webhook: %s", e)
        return {"status": "error"}
