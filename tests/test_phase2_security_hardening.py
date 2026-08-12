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
        "aws_access": "AKIAIOSFODNN7EXAMPLE",
        "private_key": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...\n-----END RSA PRIVATE KEY-----",
    }
    redacted = EUAIActComplianceExporter.redact_sensitive_data(raw_data)

    assert redacted["api_key"] == "[REDACTED_AUDIT_SAFE]"
    assert redacted["aws_access"] == "[REDACTED_AWS_AKIA]"
    assert redacted["private_key"] == "[REDACTED_PRIVATE_KEY]"


def test_merkle_causal_anchor_grace_period_fallback():
    anchor = MerkleCausalAnchor()
    root_hash = "a3f8c1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0"

    # Test simulated network failure -> fallback to local mode
    chk = anchor.generate_notary_checkpoint(root_hash, simulate_network_failure=True)
    assert chk["attestation_status"] == "LOCAL_ONLY_UNATTESTED_MODE"
    assert chk["warning_flag"] == "NETWORK_UNREACHABLE_FALLBACK_ACTIVE"
    assert chk["retry_queued"] == "TRUE"


def test_serialization_boundary_f60_to_float_buffer():
    # Test valid F60 tuples: (1, 1) = 1/60, (20, 1) = 20/60 = 0.333333...
    f60_tuples = [(1, 1), (20, 1), (60, 1)]
    buf, checksum = SerializationBoundary.convert_f60_to_float_buffer(f60_tuples)

    assert len(buf) == 12  # 3 x float32 (4 bytes each)
    assert len(checksum) == 64
    assert SerializationBoundary.validate_tensor_checksum(buf, checksum) is True


def test_serialization_boundary_checksum_mismatch():
    buf = b"sample_binary_buffer_data"
    with pytest.raises(SerializationBoundaryError):
        SerializationBoundary.validate_tensor_checksum(buf, "invalid_checksum_hash")


def test_hybrid_license_verifier(monkeypatch):
    monkeypatch.setenv("BABYLON60_LICENSE_SALT", "test_sovereign_salt_2026")
    org = "Enterprise_Bank_Corp"
    node = "NODE_PROD_01"
    expires = int(time.time()) + 86400  # 1 day in future

    license_dict = HybridLicenseVerifier.generate_license_payload(org, node, expires)
    license_json = json.dumps(license_dict)

    # Test valid offline verification
    valid, data = HybridLicenseVerifier.verify_license_offline(license_json, node)
    assert valid is True
    assert data["org"] == org

    # Test expired license failure
    expired_dict = HybridLicenseVerifier.generate_license_payload(org, node, int(time.time()) - 100)
    with pytest.raises(LicenseValidationError):
        HybridLicenseVerifier.verify_license_offline(json.dumps(expired_dict), node)

    # Test heartbeat check
    is_active, status = HybridLicenseVerifier.check_heartbeat_attestation(int(time.time()) - 100)
    assert is_active is True
    assert status == "HEARTBEAT_NOMINAL_ACTIVE"
