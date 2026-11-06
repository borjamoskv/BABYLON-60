"""Isolated fixtures for the signed node/organisation bridge."""

import json
import os
from pathlib import Path
import sys
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).absolute().parents[2] / "01_KISH_ENGINE"))
from babylon60.guards.license_verifier import HybridLicenseVerifier, LicenseValidationError


class HybridLicenseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.env = patch.dict(os.environ, {"BABYLON60_LICENSE_SALT": "isolated-hybrid-fixture-secret-2026"}, clear=True)
        self.env.start()
        self.payload = HybridLicenseVerifier.generate_license_payload(
            "fixture-org", "fixture-host", int(time.time()) + 3600
        )

    def tearDown(self) -> None:
        self.env.stop()

    def test_valid_signed_binding(self) -> None:
        ok, value = HybridLicenseVerifier.verify_license_offline(json.dumps(self.payload), "fixture-host")
        self.assertTrue(ok)
        self.assertEqual(value["org"], "fixture-org")

    def test_unicode_identifiers_round_trip_at_the_supported_limit(self) -> None:
        for identifier in ["á" * 60, "𐍈" * 60, '"' * 60]:
            with self.subTest(identifier=identifier):
                payload = HybridLicenseVerifier.generate_license_payload(
                    identifier, identifier, int(time.time()) + 3600
                )
                ok, verified = HybridLicenseVerifier.verify_license_offline(json.dumps(payload), identifier)
                self.assertTrue(ok)
                self.assertEqual(verified, payload)

    def test_unsigned_fields_cannot_rebind_a_valid_key(self) -> None:
        for field, value in [
            ("org", "another-org"),
            ("node", "another-host"),
            ("tier", "admin"),
            ("expires_at", 9999999999),
        ]:
            payload = dict(self.payload)
            payload[field] = value
            with self.subTest(field=field), self.assertRaises(LicenseValidationError):
                HybridLicenseVerifier.verify_license_offline(json.dumps(payload), str(payload["node"]))

    def test_missing_payload_key_cannot_fall_back_to_environment(self) -> None:
        os.environ["BABYLON60_LICENSE_KEY"] = self.payload["key"]
        payload = dict(self.payload)
        payload.pop("key")
        with self.assertRaises(LicenseValidationError):
            HybridLicenseVerifier.verify_license_offline(json.dumps(payload), "fixture-host")

    def test_non_object_and_mismatched_node_fail(self) -> None:
        for payload in ["[]", "null", '"text"']:
            with self.assertRaises(LicenseValidationError):
                HybridLicenseVerifier.verify_license_offline(payload, "fixture-host")
        with self.assertRaises(LicenseValidationError):
            HybridLicenseVerifier.verify_license_offline(json.dumps(self.payload), "wrong-host")
