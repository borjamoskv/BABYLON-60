"""Historical regulatory-native challenge checks, split from test_regulatory_native_validation.py.

They read docs/security/evidence/, which the public projection omits, so it omits this module too.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import pytest
from cryptography.exceptions import InvalidSignature
from scripts.guards.validate_regulatory_hardware import verify_challenge


@pytest.fixture
def proof():
    path = Path(__file__).parents[1] / "docs/security/evidence/regulatory-native-20261030/challenge.json"
    return json.loads(path.read_text())


def test_real_historical_challenge_signature(proof):
    verify_challenge(proof["response"], proof["expected_challenge"], proof["provisioned_public_key_hex"])


@pytest.mark.parametrize("field", ["nonce", "binary_sha256", "backend_digest", "purpose"])
def test_challenge_is_bound_to_exact_candidate(proof, field):
    changed = copy.deepcopy(proof["expected_challenge"])
    changed[field] = "changed"
    with pytest.raises(ValueError, match="binding differs"):
        verify_challenge(proof["response"], changed, proof["provisioned_public_key_hex"])


def test_signature_rejects_relabelled_payload(proof):
    changed = copy.deepcopy(proof["expected_challenge"])
    changed["nonce"] = "ff" * 32
    proof["response"]["challenge"] = changed
    with pytest.raises(InvalidSignature):
        verify_challenge(proof["response"], changed, proof["provisioned_public_key_hex"])


def test_no_publication_or_key_substitution(proof):
    for field, value in [("publication_authorized", True), ("public_key_hex", "04" + "00" * 64)]:
        response = copy.deepcopy(proof["response"])
        response[field] = value
        with pytest.raises(ValueError):
            verify_challenge(response, proof["expected_challenge"], proof["provisioned_public_key_hex"])
