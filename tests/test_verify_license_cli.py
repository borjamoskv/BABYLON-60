import tempfile
import pytest
from babylon60.core.license_gate import SovereignLicenseGate, Tier
from babylon60.cli.verify_license import verify_offline_key

def test_verify_offline_key_valid(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        gate = SovereignLicenseGate(config_dir=tmpdir)
        key = gate.generate_license_key("ci_runner@github.dev", Tier.PRO_SWARM)
        
        assert verify_offline_key(key) is True
        captured = capsys.readouterr()
        assert "VALID LICENSE" in captured.out
        assert "ci_runner@github.dev" in captured.out
        assert "PRO_SWARM" in captured.out

def test_verify_offline_key_invalid(capsys):
    assert verify_offline_key("B60-PRO-invalid_hex_payload") is False
    captured = capsys.readouterr()
    assert "INVALID LICENSE" in captured.out
