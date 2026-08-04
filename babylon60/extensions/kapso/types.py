# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
from typing import Any

from pydantic import BaseModel, Field


class TextMessage(BaseModel):
    body: str


class WhatsAppTemplateLanguage(BaseModel):
    code: str


class WhatsAppTemplate(BaseModel):
    name: str
    language: WhatsAppTemplateLanguage
    components: list[dict[str, Any]] | None = None


class WhatsAppMessage(BaseModel):
    messaging_product: str = "whatsapp"
    recipient_type: str = "individual"
    to: str
    type: str = Field(..., description="Message type: text, template, interactive, etc.")
    text: TextMessage | None = None
    template: WhatsAppTemplate | None = None
