"""
Comprehensive Unit & Integration Test Suite for Enterprise Inbound Email Service.
"""

import hmac
import hashlib
import json
import base64
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from babylon60.services.inbound_email import (
    InboundEmailPayload,
    InboundEmailProcessor,
    EmailAttachmentMetadata,
    EmailIntent,
    EmailSeverity,
    verify_hmac_signature,
    create_inbound_email_router,
    EnglishSupportAgentHandler,
)

SECRET = "test_secret_key_12345"


def compute_signature(secret: str, payload_bytes: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()


def test_hmac_signature_verification():
    raw_body = b'{"from":"test@example.com","to":"borja@babylon60.com"}'
    valid_sig = compute_signature(SECRET, raw_body)

    assert verify_hmac_signature(SECRET, raw_body, valid_sig) is True
    assert verify_hmac_signature(SECRET, raw_body, "invalid_sig") is False
    assert verify_hmac_signature("wrong_secret", raw_body, valid_sig) is False


def test_intent_and_severity_classification():
    # Security Incident
    sec_payload = InboundEmailPayload(
        **{
            "from": "security@cert.org",
            "to": "security@babylon60.com",
            "subject": "CVE Vulnerability Report",
            "text_body": "Critical security incident detected in auth module.",
            "timestamp": "2026-08-11T19:24:00Z",
        }
    )
    intent, severity = sec_payload.classify_intent_and_severity()
    assert intent == EmailIntent.SECURITY_INCIDENT
    assert severity == EmailSeverity.URGENT

    # Bug Report
    bug_payload = InboundEmailPayload(
        **{
            "from": "qa@client.org",
            "to": "borja@babylon60.com",
            "subject": "Crash in parser module",
            "text_body": "Unhandled panic exception in parser.rs line 42.",
            "timestamp": "2026-08-11T19:24:00Z",
        }
    )
    intent, severity = bug_payload.classify_intent_and_severity()
    assert intent == EmailIntent.BUG_REPORT
    assert severity == EmailSeverity.HIGH


def test_attachment_base64_decoding():
    sample_log = "ERROR [2026-08-11] Kernel panic at 0x7fff"
    log_b64 = base64.b64encode(sample_log.encode("utf-8")).decode("utf-8")

    att = EmailAttachmentMetadata(
        filename="error_log.log",
        mimeType="text/plain",
        size=len(sample_log),
        content_b64=log_b64,
    )

    decoded = att.decode_text_content()
    assert decoded == sample_log


def test_idempotency_tracker():
    processor = InboundEmailProcessor(secret=SECRET)
    payload = InboundEmailPayload(
        **{
            "from": "user@domain.com",
            "to": "borja@babylon60.com",
            "subject": "Unique message",
            "timestamp": "2026-08-11T19:24:00Z",
            "message_id": "msg_unique_12345",
        }
    )

    import asyncio
    res1 = asyncio.run(processor.process_email(payload))
    assert res1["status"] == "processed"

    res2 = asyncio.run(processor.process_email(payload))
    assert res2["status"] == "duplicate_skipped"


def test_fastapi_webhook_full_pipeline():
    processor = InboundEmailProcessor(secret=SECRET)
    handler = EnglishSupportAgentHandler()
    processor.register_handler(handler.handle)

    router = create_inbound_email_router(processor)
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    payload_data = {
        "from": "alice@client.org",
        "to": "support@babylon60.com",
        "subject": "Help with API authentication issue",
        "text_body": "Hello support team, I am encountering an HTTP 401 error. Please advise.",
        "attachments_count": 0,
        "attachments_metadata": [],
        "timestamp": "2026-08-11T19:24:00Z",
        "message_id": "msg_api_test_999",
    }
    raw_bytes = json.dumps(payload_data).encode("utf-8")
    sig = compute_signature(SECRET, raw_bytes)

    response = client.post(
        "/api/v1/inbound-email",
        content=raw_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Babylon-Signature": sig,
            "Authorization": f"Bearer {SECRET}",
        },
    )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["status"] == "processed"
    assert res_json["detected_language"] == "en"
    assert res_json["intent"] == "technical_support"
