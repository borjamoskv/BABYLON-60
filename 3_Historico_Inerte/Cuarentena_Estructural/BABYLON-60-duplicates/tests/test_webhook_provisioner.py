# C5-REAL EXERGY CERTIFIED
import pytest
from babylon60.extensions.billing.webhook_handler import StripeTokenProvisioner


class TestStripeTokenProvisioner:
    def test_provision_token_on_checkout(self):
        """Tests that checkout.session.completed triggers token generation and idempotency hash."""
        provisioner = StripeTokenProvisioner()

        mock_payload = b'{"type": "checkout.session.completed", "data": {"object": {"id": "cs_test_123", "customer_details": {"email": "cto@enterprise.com"}, "metadata": {"plan": "pro_team"}}}}'
        mock_sig = "mock_sig_123"

        result = provisioner.process_webhook(mock_payload, mock_sig)

        assert result["status"] == "success"
        assert result["customer_email"] == "cto@enterprise.com"
        assert result["plan"] == "pro_team"
        assert result["api_token"].startswith("b60_live_")
        assert len(result["idempotency_hash"]) == 64

    def test_ignore_non_checkout_events(self):
        """Tests that non-checkout events are gracefully ignored."""
        provisioner = StripeTokenProvisioner()
        mock_payload = b'{"type": "payment_intent.created", "data": {}}'
        result = provisioner.process_webhook(mock_payload, "mock_sig")
        assert result["status"] == "ignored"
