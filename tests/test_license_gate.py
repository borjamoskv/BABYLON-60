import os
import tempfile
import pytest
from babylon60.core.license_gate import SovereignLicenseGate, Tier, TIER_LIMITS

def test_license_key_generation_and_verification():
    with tempfile.TemporaryDirectory() as tmpdir:
        gate = SovereignLicenseGate(config_dir=tmpdir)
        key = gate.generate_license_key(owner='borjamoskv@cortex.dev', tier=Tier.PRO_SWARM, valid_days=30)
        assert key.startswith('B60-PRO-')
        verified = gate.verify_license_key(key)
        assert verified is not None
        assert verified['owner'] == 'borjamoskv@cortex.dev'
        assert verified['tier'] == Tier.PRO_SWARM
        assert verified['valid'] is True

def test_license_activation_and_metering():
    with tempfile.TemporaryDirectory() as tmpdir:
        gate = SovereignLicenseGate(config_dir=tmpdir)
        status = gate.get_status()
        assert status.tier == Tier.COMMUNITY
        assert status.ops_limit == TIER_LIMITS[Tier.COMMUNITY]
        dev_key = gate.generate_license_key(owner='dev@firm.com', tier=Tier.DEVELOPER)
        activated = gate.activate_key(dev_key)
        assert activated is True
        new_status = gate.get_status()
        assert new_status.tier == Tier.DEVELOPER
        assert new_status.ops_limit == TIER_LIMITS[Tier.DEVELOPER]
        assert gate.record_operation(100) is True
        status_after = gate.get_status()
        assert status_after.ops_today == 100

def test_exceeded_limit_raises():
    with tempfile.TemporaryDirectory() as tmpdir:
        gate = SovereignLicenseGate(config_dir=tmpdir)
        limit = TIER_LIMITS[Tier.COMMUNITY]
        gate.record_operation(limit)
        with pytest.raises(RuntimeError, match='limit exceeded'):
            gate.record_operation(1)