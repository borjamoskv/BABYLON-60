"""Receipt encoding and Merkle position checks with authentic software signatures."""

import base64

import pytest
from nacl.signing import SigningKey

from babylon60.cli import llm_attest


@pytest.fixture
def signed_message():
    key = SigningKey.generate()
    message = b"receipt-test"
    public = base64.urlsafe_b64encode(bytes(key.verify_key)).decode()
    signature = base64.urlsafe_b64encode(key.sign(message).signature).decode()
    return public, signature, message


@pytest.mark.parametrize("padded", [False, True])
@pytest.mark.parametrize("prefixed", [False, True])
def test_valid_base64url_signatures_with_optional_prefix(signed_message, padded, prefixed):
    public, signature, message = signed_message
    if not padded:
        public, signature = public.rstrip("="), signature.rstrip("=")
    if prefixed:
        signature = "base64url:" + signature
    assert llm_attest.verify_ed25519(public, signature, message)


@pytest.mark.parametrize("field", ["public", "signature"])
@pytest.mark.parametrize("damage", ["garbage", "extra_padding", "pad_bits", "unicode", "short", "wrong_type"])
def test_malformed_signature_encodings_return_false(signed_message, field, damage):
    public, signature, message = signed_message
    value = public if field == "public" else signature
    if damage == "garbage":
        value += "!!!!"
    elif damage == "extra_padding":
        value += "="
    elif damage == "pad_bits":
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        raw = value.rstrip("=")
        value = raw[:-1] + alphabet[alphabet.index(raw[-1]) | 1]
    elif damage == "unicode":
        value = "ñ"
    elif damage == "short":
        value = "YQ"
    else:
        value = None
    public, signature = (value, signature) if field == "public" else (public, value)
    assert llm_attest.verify_ed25519(public, signature, message) is False


@pytest.mark.parametrize("index", [-2, -1, 1, 99, True, "0", None])
def test_single_leaf_proof_rejects_invalid_positions(index):
    leaf = "a" * 64
    assert llm_attest.verify_merkle_proof(leaf, [], leaf, index) is False


def test_two_leaf_proof_binds_position_and_rejects_index_aliases():
    left, right = "a" * 64, "b" * 64
    root = llm_attest.verify_merkle_node(left, right)
    assert llm_attest.verify_merkle_proof(left, [right], root, 0)
    assert llm_attest.verify_merkle_proof(right, [left], root, 1)
    for index in (-2, 1, 2, 4):
        assert not llm_attest.verify_merkle_proof(left, [right], root, index)


@pytest.mark.parametrize("sibling", ["", "gg" * 32, "00", None])
def test_malformed_merkle_hash_returns_false(sibling):
    assert llm_attest.verify_merkle_proof("a" * 64, [sibling], "b" * 64, 0) is False
