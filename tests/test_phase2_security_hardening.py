"""
Unit tests for Phase II Security Hardening (BABYLON-60 v4.0).
Tests Redaction Layer, Grace Period Local-Only Fallback, Serialization Boundary Bounds Checking,
and Hybrid License Verification.
"""

import pytest
import time
import json
from babylon60.compliance_exporter import EUAIActComplianceExporter
from babylon60.attestation import MerkleCausalAnchor
from babylon60.primitives.serialization_boundary import (
    SerializationBoundary,
    SerializationBoundaryError,
)
from babylon60.guards.license_verifier import (
    HybridLicenseVerifier,
    LicenseValidationError,
)


def test_redaction_layer_sanitizes_pii_and_secrets():
    raw_data = {
        "user_email": "admin@company.com",
        "api_key": "api_key_secret_1234567890_super_secret",
        "aws_access": "<REDACTED_AWS_KEY>",
