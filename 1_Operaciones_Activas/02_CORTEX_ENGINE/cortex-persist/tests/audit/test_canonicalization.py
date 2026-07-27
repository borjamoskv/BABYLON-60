# [C5-REAL] Exergy-Maximized — Canonicalization Tests
import pytest
from babylon60.audit.ledger import canonical_json_bytes, normalize_json


def test_canonical_json_identical_keys_different_order():
    a = {"b": 2, "a": 1}
    b = {"a": 1, "b": 2}
    assert canonical_json_bytes(a) == canonical_json_bytes(b)


def test_canonical_json_rejects_floats():
    with pytest.raises(TypeError, match="must not be floats"):
        canonical_json_bytes({"value": 1.23})

    with pytest.raises(TypeError, match="must not be floats"):
        canonical_json_bytes({"value": float("nan")})


def test_canonical_json_normalizes_unicode():
    # 'é' as single char vs combined
    str1 = "\u00e9"
    str2 = "\u0065\u0301"

    bytes1 = canonical_json_bytes({"val": str1})
    bytes2 = canonical_json_bytes({"val": str2})
    assert bytes1 == bytes2


def test_reject_duplicate_keys():
    import json
    from babylon60.audit.ledger import reject_duplicate_keys

    raw = '{"a": 1, "a": 2}'
    with pytest.raises(ValueError, match="duplicate JSON key: a"):
        json.loads(raw, object_pairs_hook=reject_duplicate_keys)
