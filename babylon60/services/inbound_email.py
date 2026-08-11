"""
Advanced Enterprise Inbound Email Receiver Service for BABYLON-60.
Provides HMAC signature verification, idempotency tracking, MIME attachment extraction,
intent & severity classification, and automated multi-agent response generation.
"""

import hmac
import hashlib
import logging
import base64
import time
from enum import Enum
from typing import List, Optional, Callable, Dict, Any, Set
from pydantic import BaseModel, Field, ConfigDict
from fastapi import APIRouter, Request, Header, HTTPException, status

logger = logging.getLogger("babylon60.services.inbound_email")


class EmailIntent(str, Enum):
    TECHNICAL_SUPPORT = "technical_support"
    BUG_REPORT = "bug_report"
    SECURITY_INCIDENT = "security_incident"
    FEATURE_REQUEST = "feature_request"
    BILLING = "billing"
    GENERAL = "general"


class EmailSeverity(str, Enum):
    URGENT = "urgent"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class EmailAttachmentMetadata(BaseModel):
    filename: str
    mimeType: str = Field(default="application/octet-stream")
    size: int = 0
    content_b64: Optional[str] = None

    def decode_text_content(self) -> Optional[str]:
        """Decodes base64 attachment if it is plain text, JSON, code, or markdown."""
        if not self.content_b64:
            return None
        text_mime_prefixes = ("text/", "application/json", "application/javascript", "application/xml")
        if any(self.mimeType.startswith(p) for p in text_mime_prefixes) or self.filename.endswith(
            (".txt", ".py", ".rs", ".js", ".json", ".md", ".yml", ".yaml", ".log")
        ):
            try:
                decoded_bytes = base64.b64decode(self.content_b64)
                return decoded_bytes.decode("utf-8", errors="replace")
            except Exception as e:
                logger.warning(f"Could not decode text attachment {self.filename}: {e}")
        return None


class InboundEmailPayload(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_addr: str = Field(..., alias="from")
    to: str
    subject: str
    text_body: Optional[str] = Field(default="")
    html_body: Optional[str] = Field(default="")
    attachments_count: int = 0
    attachments_metadata: List[EmailAttachmentMetadata] = Field(default_factory=list)
    timestamp: str
    message_id: Optional[str] = None
    detected_language: Optional[str] = Field(default="auto")
    intent: Optional[EmailIntent] = Field(default=EmailIntent.GENERAL)
    severity: Optional[EmailSeverity] = Field(default=EmailSeverity.MEDIUM)

    def detect_language(self) -> str:
        """Heuristic language detector for English vs Spanish."""
        text = f"{self.subject} {self.text_body or ''}".lower()
        english_keywords = {"the", "is", "help", "support", "issue", "please", "thanks", "regards", "error", "bug", "account", "request"}
        spanish_keywords = {"el", "la", "que", "gracias", "saludos", "ayuda", "soporte", "problema", "por favor", "cuenta"}

        en_count = sum(1 for kw in english_keywords if f" {kw} " in f" {text} ")
        es_count = sum(1 for kw in spanish_keywords if f" {kw} " in f" {text} ")

        if en_count > es_count:
            self.detected_language = "en"
        elif es_count > en_count:
            self.detected_language = "es"
        else:
            self.detected_language = "en"
        return self.detected_language

    def classify_intent_and_severity(self) -> (EmailIntent, EmailSeverity):
        """Classifies the email intent and urgency level."""
        text = f"{self.subject} {self.text_body or ''}".lower()

        # Security check
        if any(w in text for w in ("cve", "vulnerability", "exploit", "security incident", "data leak", "vulnerabilidad")):
            self.intent = EmailIntent.SECURITY_INCIDENT
            self.severity = EmailSeverity.URGENT
            return self.intent, self.severity

        # Bug check
        if any(w in text for w in ("crash", "panic", "exception", "traceback", "bug", "failing test", "error 500")):
            self.intent = EmailIntent.BUG_REPORT
            self.severity = EmailSeverity.HIGH
            return self.intent, self.severity

        # Feature request check
        if any(w in text for w in ("feature", "proposal", "enhancement", "idea", "propuesta", "mejora")):
            self.intent = EmailIntent.FEATURE_REQUEST
            self.severity = EmailSeverity.LOW
            return self.intent, self.severity

        # Support check
        if "support@" in self.to.lower() or any(w in text for w in ("help", "ayuda", "support", "soporte")):
            self.intent = EmailIntent.TECHNICAL_SUPPORT
            self.severity = EmailSeverity.MEDIUM
            return self.intent, self.severity

        self.intent = EmailIntent.GENERAL
        self.severity = EmailSeverity.LOW
        return self.intent, self.severity


class IdempotencyTracker:
    """In-memory idempotency cache to reject duplicate webhook deliveries."""

    def __init__(self, ttl_seconds: int = 86400):
        self.seen_ids: Set[str] = set()
        self.timestamps: Dict[str, float] = {}
        self.ttl = ttl_seconds

    def is_duplicate(self, message_id: Optional[str]) -> bool:
        if not message_id:
            return False
        now = time.time()
        self._cleanup(now)
        if message_id in self.seen_ids:
            return True
        self.seen_ids.add(message_id)
        self.timestamps[message_id] = now
        return False

    def _cleanup(self, now: float):
        expired = [mid for mid, ts in self.timestamps.items() if now - ts > self.ttl]
        for mid in expired:
            self.seen_ids.discard(mid)
            del self.timestamps[mid]


def verify_hmac_signature(secret: str, raw_body: bytes, expected_signature: str) -> bool:
    """Verifies HMAC-SHA256 signature."""
    if not secret or not expected_signature:
        return False
    computed_hmac = hmac.new(
        secret.encode("utf-8"),
        raw_body,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(computed_hmac, expected_signature)


class InboundEmailProcessor:
    """Enterprise Inbound Email Dispatcher Pipeline."""

    def __init__(self, secret: str = "default_babylon60_inbound_secret"):
        self.secret = secret
        self.handlers: List[Callable[[InboundEmailPayload], Any]] = []
        self.idempotency = IdempotencyTracker()

    def register_handler(self, handler: Callable[[InboundEmailPayload], Any]):
        self.handlers.append(handler)

    async def process_email(self, payload: InboundEmailPayload) -> Dict[str, Any]:
        if payload.message_id and self.idempotency.is_duplicate(payload.message_id):
            logger.info(f"Duplicate email webhook skipped: {payload.message_id}")
            return {
                "status": "duplicate_skipped",
                "message_id": payload.message_id,
            }

        # Auto-enrich payload metadata
        payload.detect_language()
        payload.classify_intent_and_severity()

        logger.info(
            f"Processing inbound email from '{payload.from_addr}' | Subject: '{payload.subject}' | "
            f"Lang: {payload.detected_language} | Intent: {payload.intent.value} | Severity: {payload.severity.value}"
        )

        results = []
        for handler in self.handlers:
            try:
                res = handler(payload)
                results.append(res)
            except Exception as e:
                logger.error(f"Error executing email handler {handler}: {e}", exc_info=True)

        return {
            "status": "processed",
            "from": payload.from_addr,
            "to": payload.to,
            "detected_language": payload.detected_language,
            "intent": payload.intent.value,
            "severity": payload.severity.value,
            "attachments_decoded": sum(1 for a in payload.attachments_metadata if a.decode_text_content() is not None),
            "handlers_executed": len(self.handlers),
        }


def create_inbound_email_router(processor: InboundEmailProcessor) -> APIRouter:
    router = APIRouter(prefix="/api/v1", tags=["Inbound Email"])

    @router.post("/inbound-email")
    async def handle_inbound_email(
        request: Request,
        x_babylon_signature: Optional[str] = Header(None, alias="X-Babylon-Signature"),
        authorization: Optional[str] = Header(None, alias="Authorization"),
    ):
        raw_body = await request.body()

        # 1. Signature Verification
        is_valid_hmac = False
        if x_babylon_signature:
            is_valid_hmac = verify_hmac_signature(processor.secret, raw_body, x_babylon_signature)

        is_valid_token = False
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split("Bearer ", 1)[1]
            if hmac.compare_digest(token, processor.secret):
                is_valid_token = True

        if not is_valid_hmac and not is_valid_token:
            logger.warning("Rejected unauthorized inbound email webhook attempt.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing X-Babylon-Signature or Authorization Bearer token"
            )

        # 2. Parse & Process
        try:
            payload = InboundEmailPayload.model_validate_json(raw_body.decode("utf-8"))
        except Exception as e:
            logger.error(f"Failed to parse inbound email payload: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid email payload format: {str(e)}"
            )

        result = await processor.process_email(payload)
        return result

    return router


class EnglishSupportAgentHandler:
    """AI Support Agent Handler tailored for English & Multilingual Queries."""

    def __init__(self, agent_name: str = "BABYLON-60 Enterprise AI Support"):
        self.agent_name = agent_name

    def handle(self, payload: InboundEmailPayload) -> Dict[str, Any]:
        lang = payload.detected_language or payload.detect_language()
        intent = payload.intent or EmailIntent.GENERAL
        severity = payload.severity or EmailSeverity.MEDIUM

        # Extract decoded attachments for agent prompt
        attachments_summary = []
        for att in payload.attachments_metadata:
            content_text = att.decode_text_content()
            if content_text:
                attachments_summary.append(f"--- Attachment: {att.filename} ---\n{content_text[:1000]}")

        attachments_block = "\n\n".join(attachments_summary) if attachments_summary else "No attachments."

        system_prompt = (
            f"You are {self.agent_name}. Respond in clear, professional English.\n"
            f"Intent: {intent.value.upper()} | Urgency: {severity.value.upper()}"
        ) if lang == "en" else (
            f"Eres {self.agent_name}. Responde en español profesional.\n"
            f"Intención: {intent.value.upper()} | Urgencia: {severity.value.upper()}"
        )

        prompt_context = {
            "system_prompt": system_prompt,
            "sender": payload.from_addr,
            "recipient": payload.to,
            "subject": payload.subject,
            "language": lang,
            "intent": intent.value,
            "severity": severity.value,
            "body": payload.text_body,
            "attachments": attachments_block,
        }

        return {
            "agent": self.agent_name,
            "target_language": lang,
            "intent": intent.value,
            "severity": severity.value,
            "prompt_context": prompt_context,
            "status": "ready_for_llm",
        }
