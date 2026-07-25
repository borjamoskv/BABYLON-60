import tempfile
import pytest
from unittest.mock import patch
from babylon60.cli.license_cli import print_status, activate_license, buy_license, main
from babylon60.core.license_gate import SovereignLicenseGate, Tier

def test_cli_print_status(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.object(SovereignLicenseGate, '__init__', lambda self: None):
            with patch.object(SovereignLicenseGate, 'get_status') as mock_status:
                from babylon60.core.license_gate import LicenseStatus
                mock_status.return_value = LicenseStatus(
                    active=True,
                    tier=Tier.PRO_SWARM,
                    owner="test@cortex.dev",
                    ops_today=50,
                    ops_limit=1000000,
                    expires_at=2000000000,
                    signature="SIG_TEST_C5"
                )
                print_status()
                captured = capsys.readouterr()
                assert "PRO_SWARM" in captured.out
                assert "test@cortex.dev" in captured.out

def test_cli_activate_success(capsys):
    with tempfile.TemporaryDirectory() as tmpdir:
        gate = SovereignLicenseGate(config_dir=tmpdir)
        key = gate.generate_license_key("cli@user.dev", Tier.DEVELOPER)
        
        with patch("babylon60.cli.license_cli.SovereignLicenseGate", return_value=gate):
            activate_license(key)
            captured = capsys.readouterr()
            assert "SUCCESS: Tier 'DEVELOPER' activated" in captured.out

def test_cli_main_status(capsys):
    with patch("babylon60.cli.license_cli.print_status") as mock_print:
        main(["status"])
        mock_print.assert_called_once()
