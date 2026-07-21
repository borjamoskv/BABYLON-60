import pytest
from babylon60.utils import base60


def test_base60_integer() -> None:
    assert base60.encode_base60(0) == "0"
    assert base60.decode_base60("0") == 0

    # 60
    assert base60.encode_base60(60) == "10"
    assert base60.decode_base60("10") == 60

    # Large integer
    num = 12345678901234567890
    encoded = base60.encode_base60(num)
    assert base60.decode_base60(encoded) == num


def test_base60_bytes() -> None:
    b = b"C5-REAL"
    encoded = base60.bytes_to_base60(b)
    decoded = base60.base60_to_bytes(encoded, len(b))
    assert decoded == b


def test_base60_validation() -> None:
    with pytest.raises(ValueError):
        base60.decode_base60("invalid_char_I")  # 'I' is excluded
    with pytest.raises(ValueError):
        base60.decode_base60("invalid_char_O")  # 'O' is excluded
    with pytest.raises(ValueError):
        base60.decode_base60("invalid_char_l")  # 'l' is excluded
