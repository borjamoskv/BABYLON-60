import tempfile

from babylon60.core.api_key_manager import EnterpriseAPIKeyManager


def test_issue_and_validate_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = EnterpriseAPIKeyManager(storage_dir=tmpdir)
        key_id = mgr.issue_key(org_name="Acme Corp", tier="ENTERPRISE", valid_days=30)

        assert key_id.startswith("b60_live_")
        meta = mgr.validate_key(key_id)
        assert meta is not None
        assert meta.org_name == "Acme Corp"
        assert meta.tier == "ENTERPRISE"
        assert meta.is_active is True


def test_revoke_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = EnterpriseAPIKeyManager(storage_dir=tmpdir)
        key_id = mgr.issue_key(org_name="Stark Industries", tier="PRO")

        assert mgr.validate_key(key_id) is not None
        assert mgr.revoke_key(key_id) is True
        assert mgr.validate_key(key_id) is None


def test_invalid_key():
    with tempfile.TemporaryDirectory() as tmpdir:
        mgr = EnterpriseAPIKeyManager(storage_dir=tmpdir)
        assert mgr.validate_key("b60_live_invalid_hash") is None
