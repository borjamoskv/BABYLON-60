"""Isolated cryptographic fixtures, never production licence material."""

import hashlib
import hmac
import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).absolute().parents[2]
spec = importlib.util.spec_from_file_location(
    "license_validator", ROOT / "01_KISH_ENGINE/babylon60/guards/license_sovereign_validator.py"
)
assert spec is not None and spec.loader is not None
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
SIGNING_KEY = "isolated-test-fixture-secret-not-production"


def signed(owner: str = "fixture", tier: str = "enterprise", expiry: int = 2000000000) -> str:
    payload = f"{owner}:{tier}:{expiry}"
    return payload + ":" + hmac.new(SIGNING_KEY.encode(), payload.encode(), hashlib.sha256).hexdigest()[:16]


class LicenseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.environ = patch.dict(os.environ, {"BABYLON60_LICENSE_SALT": SIGNING_KEY}, clear=True)
        self.environ.start()
        self.clock = patch.object(validator.time, "time", return_value=1900000000)
        self.clock.start()

    def tearDown(self) -> None:
        self.clock.stop()
        self.environ.stop()

    def test_no_key_does_not_grant_enterprise(self) -> None:
        status = validator.verify_license_key("")
        self.assertFalse(status.is_valid)
        self.assertEqual(status.tier, "community")

    def test_forged_and_test_credentials_fail(self) -> None:
        for key in ["forged", signed()[:-1] + "x", "b60_test_fixture", "owner:enterprise:2000000000:0000000000000000"]:
            with self.subTest(key=key):
                self.assertFalse(validator.verify_license_key(key).is_valid)

    def test_expired_and_boundary_timestamp_fail(self) -> None:
        for expiry in [1899999999, 1900000000, -1, 0]:
            self.assertFalse(validator.verify_license_key(signed(expiry=expiry)).is_valid)

    def test_unsupported_tier_even_with_valid_signature_fails(self) -> None:
        for tier in ["admin", "individual", "trial", "ENTERPRISE", ""]:
            self.assertFalse(validator.verify_license_key(signed(tier=tier)).is_valid)

    def test_missing_signing_secret_fails_closed(self) -> None:
        os.environ.pop("BABYLON60_LICENSE_SALT")
        self.assertFalse(validator.verify_license_key(signed()).is_valid)

    def test_public_historical_default_secret_is_refused(self) -> None:
        os.environ["BABYLON60_LICENSE_SALT"] = "default_sovereign_hardened_salt_2026"
        with self.assertRaises((RuntimeError, ValueError)):
            validator.generate_license_key("fixture", "enterprise", 2000000000)
        self.assertFalse(validator.verify_license_key(signed()).is_valid)

    def test_valid_legacy_fixture_still_validates(self) -> None:
        for tier in ["pro", "enterprise"]:
            status = validator.verify_license_key(signed(tier=tier))
            self.assertTrue(status.is_valid)
            self.assertEqual(status.tier, tier)

    def test_generation_rejects_unsafe_payload_and_expiry(self) -> None:
        for owner, tier, expiry in [
            ("", "pro", 2000000000),
            ("owner:extra", "pro", 2000000000),
            ("fixture", "admin", 2000000000),
            ("fixture", "pro", 1900000000),
        ]:
            with self.assertRaises(ValueError):
                validator.generate_license_key(owner, tier, expiry)

    def test_expanded_bridge_owner_limit_remains_bounded(self) -> None:
        owner = "x" * validator.MAX_OWNER_LENGTH
        key = validator.generate_license_key(owner, "enterprise", 2000000000)
        self.assertTrue(validator.verify_license_key(key).is_valid)
        with self.assertRaises(ValueError):
            validator.generate_license_key(owner + "x", "enterprise", 2000000000)
        self.assertFalse(validator.verify_license_key(signed(owner=owner + "x")).is_valid)
        self.assertFalse(validator.verify_license_key("x" * (validator.MAX_KEY_LENGTH + 1)).is_valid)

    def test_warmup_and_repeated_forgery_rejection(self) -> None:
        for _ in range(32):
            validator.verify_license_key(signed())
        for n in range(2000):
            self.assertFalse(validator.verify_license_key(f"fixture:enterprise:2000000000:{n:016x}").is_valid)


if __name__ == "__main__":
    unittest.main()
