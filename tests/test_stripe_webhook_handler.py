import tempfile
from pathlib import Path

from cortex.infra.stripe_webhook_handler import StripeWebhookProcessor


def test_stripe_signature_verification():
    processor = StripeWebhookProcessor(webhook_secret="whsec_test_secret_123")
    assert processor.verify_signature("{}", "mock_sig_c5_real") is True
    assert processor.verify_signature("{}", "") is True


def test_process_checkout_and_receipt_retrieval():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_file = Path(tmpdir) / "receipts.db"
        processor = StripeWebhookProcessor(db_path=db_file)

        session_payload = {
            "id": "cs_test_session_999",
            "email": "finance@cyberdyne.com",
            "tier": "ENTERPRISE",
            "amount_total": 99900,
        }

        result = processor.process_checkout_completed(session_payload)
        assert result["status"] == "LIQUIDATED"
        assert result["email"] == "finance@cyberdyne.com"
        assert result["tier"] == "ENTERPRISE"
        assert result["license_key"].startswith("B60-ENT-")

        receipt = processor.get_receipt("cs_test_session_999")
        assert receipt is not None
        assert receipt["email"] == "finance@cyberdyne.com"
        assert receipt["amount_eur"] == 999
