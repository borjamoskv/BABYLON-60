# C5-REAL EXERGY CERTIFIED
"""
Unit tests for DeliverabilityValidator in cortex.
"""

from __future__ import annotations
import unittest
from cortex.core.deliverability_validator import DeliverabilityValidator

class TestDeliverabilityValidator(unittest.TestCase):
    def test_valid_syntax(self) -> None:
        self.assertTrue(DeliverabilityValidator.validate_syntax("test.user@gmail.com"))
        self.assertTrue(DeliverabilityValidator.validate_syntax("alex@foundersfund.com"))
        self.assertFalse(DeliverabilityValidator.validate_syntax("invalid-email"))
        self.assertFalse(DeliverabilityValidator.validate_syntax("@domain.com"))
        self.assertFalse(DeliverabilityValidator.validate_syntax("user@"))

    def test_extract_domain(self) -> None:
        self.assertEqual(DeliverabilityValidator.extract_domain("user@gmail.com"), "gmail.com")
        self.assertEqual(DeliverabilityValidator.extract_domain("bad_email"), "")

    def test_validate_email(self) -> None:
        res = DeliverabilityValidator.validate_email("contact@gmail.com", verify_dns=False)
        self.assertTrue(res.is_valid_syntax)
        self.assertEqual(res.domain, "gmail.com")

        res_bad = DeliverabilityValidator.validate_email("bad_email", verify_dns=False)
        self.assertFalse(res_bad.is_valid_syntax)
        self.assertEqual(res_bad.error_reason, "INVALID_SYNTAX")

if __name__ == "__main__":
    unittest.main()
