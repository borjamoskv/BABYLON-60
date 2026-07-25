import tempfile
from pathlib import Path

from babylon60.core.email_notifier import PurchaseNotifier


def test_purchase_notifier_logging():
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "notifications.json"
        notifier = PurchaseNotifier(log_path=log_file, target_email="Borjamoskv@gmail.com")
        
        alert = notifier.notify_purchase(
            customer_email="buyer@enterprise.com",
            tier="ENTERPRISE",
            amount_eur=999,
            license_key="B60-ENT-MOCK-123",
            session_id="cs_live_test_sepa"
        )
        
        assert alert["target_email"] == "Borjamoskv@gmail.com"
        assert alert["customer_email"] == "buyer@enterprise.com"
        assert alert["amount_eur"] == 999
        assert alert["tier"] == "ENTERPRISE"
        assert log_file.exists()
