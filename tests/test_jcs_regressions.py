"""RFC 8785 counterexamples observed in the public wheel's receipt CLI."""

import base64
import hashlib
import json
import struct

import pytest

from babylon60.cli import attest_character_count, llm_attest


@pytest.mark.parametrize("module", [llm_attest, attest_character_count])
@pytest.mark.parametrize(
    "number,expected",
    [(-0.0, "0"), (1.0, "1"), (1e-6, "0.000001"), (1e20, "100000000000000000000"), (1e21, "1e+21"), (1e-7, "1e-7")],
)
def test_ecmascript_number_serialization(module, number, expected):
    assert module.jcs_canonicalize({"n": number}) == ('{"n":' + expected + "}").encode()


@pytest.mark.parametrize("module", [llm_attest, attest_character_count])
@pytest.mark.parametrize("number", [float("nan"), float("inf"), float("-inf"), 2**53 + 1])
def test_nonfinite_and_unsafe_integers_rejected(module, number):
    with pytest.raises(ValueError):
        module.jcs_canonicalize({"n": number})


def test_utf16_order_is_recursive_and_array_order_is_preserved():
    assert (
        llm_attest.jcs_canonicalize({"z": [{"\ufb33": 1, "\U0001f600": 2}, 3]}) == '{"z":[{"😀":2,"דּ":1},3]}'.encode()
    )


@pytest.mark.parametrize("value", [{"s": "\ud800"}, {"\ud800": "value"}, {1: "non-string-key"}])
def test_invalid_strings_and_keys_rejected(value):
    with pytest.raises((ValueError, TypeError)):
        llm_attest.jcs_canonicalize(value)


@pytest.mark.parametrize(
    "bits,expected",
    [
        ("0000000000000001", "5e-324"),
        ("7fefffffffffffff", "1.7976931348623157e+308"),
        ("4430000000000000", "295147905179352830000"),
        ("44b52d02c7e14af5", "9.999999999999997e+22"),
        ("44b52d02c7e14af6", "1e+23"),
        ("44b52d02c7e14af7", "1.0000000000000001e+23"),
        ("3eb0c6f7a0b5ed8c", "9.999999999999997e-7"),
        ("3eb0c6f7a0b5ed8d", "0.000001"),
        ("43143ff3c1cb0959", "1424953923781206.2"),
    ],
)
def test_rfc8785_appendix_b_vectors(bits, expected):
    number = struct.unpack(">d", bytes.fromhex(bits))[0]
    assert llm_attest.jcs_canonicalize({"n": number}) == ('{"n":' + expected + "}").encode()


def test_real_signed_receipt_with_jcs_numbers_and_unicode(tmp_path):
    from nacl.signing import SigningKey

    key = SigningKey.generate()
    payload = {"\ufb33": -0.0, "\U0001f600": [1.0, 1e-6]}
    # Independent expected bytes, rather than the serializer under test.
    expected = '{"😀":[1,0.000001],"דּ":0}'.encode()
    digest = "sha3-256:" + hashlib.sha3_256(expected).hexdigest()
    receipt = {
        "payload": payload,
        "payload_hash": digest,
        "signature": {
            "algorithm": "Ed25519",
            "key_id": "did:key:" + base64.urlsafe_b64encode(bytes(key.verify_key)).decode().rstrip("="),
            "value": base64.urlsafe_b64encode(key.sign(digest.encode()).signature).decode().rstrip("="),
        },
    }
    path = tmp_path / "receipt.json"
    path.write_text(json.dumps(receipt))
    assert llm_attest.verify_receipt(str(path))["status"] == "verified"


@pytest.mark.parametrize("text", ['{"payload":{"x":1,"x":2}}', '{"payload":{"x":NaN}}'])
def test_receipt_loader_rejects_ambiguous_or_nonfinite_json(tmp_path, text):
    path = tmp_path / "receipt.json"
    path.write_text(text)
    with pytest.raises(ValueError):
        llm_attest.verify_receipt(str(path))
