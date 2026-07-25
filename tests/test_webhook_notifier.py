from unittest.mock import MagicMock, patch

from babylon60.core.webhook_notifier import EnterpriseWebhookNotifier


def test_webhook_payload_creation_and_signing():
    notifier = EnterpriseWebhookNotifier(secret_salt="TEST_SALT_123")
    event = notifier.create_event(
        event_type="BILLING_THRESHOLD_WARNING",
        org_name="Cyberdyne Inc",
        data={"usage_percent": 95, "ops_count": 950000},
    )

    assert event["payload"]["event_type"] == "BILLING_THRESHOLD_WARNING"
    assert event["payload"]["org_name"] == "Cyberdyne Inc"
    assert "X-B60-Signature" in event["headers"]
    assert event["headers"]["X-C5-REAL"] == "Verified"


def test_webhook_dispatch_mock_success():
    notifier = EnterpriseWebhookNotifier()
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        success = notifier.dispatch(
            url="https://enterprise.client.com/webhook",
            event_type="LEDGER_STATE_SEALED",
            org_name="Cyberdyne Inc",
            data={"height": 1024, "hash": "0xabc123"},
        )
        assert success is True


def test_webhook_dispatch_mock_failure():
    notifier = EnterpriseWebhookNotifier()
    with patch("urllib.request.urlopen", side_effect=OSError("Network failure")):
        success = notifier.dispatch(
            url="https://invalid.client.com/webhook",
            event_type="LEDGER_STATE_SEALED",
            org_name="Cyberdyne Inc",
            data={},
        )
        assert success is False
