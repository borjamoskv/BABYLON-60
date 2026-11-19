"""RFC 8785 serialization for receipts, without optional runtime dependencies.

Integers outside the interoperable IEEE 754 safe range must be strings. Floats
use Python's shortest round-trip digits and ECMAScript's decimal/exponent layout.
"""

import json
import math


def _number(value: float) -> str:
    if not math.isfinite(value):
        raise ValueError("JCS rejects NaN and Infinity")
    if value == 0:
        return "0"
    sign = "-" if value < 0 else ""
    mantissa, _, exponent = repr(abs(value)).lower().partition("e")
    whole, _, fraction = mantissa.partition(".")
    digits = (whole + fraction).lstrip("0")
    # Decimal position includes leading zeroes removed above (e.g. 0.002).
    point = len(whole) + int(exponent or "0") - (len(whole + fraction) - len(digits))
    digits = digits.rstrip("0")
    if 0 < point <= 21:
        if point >= len(digits):
            return sign + digits + "0" * (point - len(digits))
        return sign + digits[:point] + "." + digits[point:]
    if -6 < point <= 0:
        return sign + "0." + "0" * -point + digits
    scientific = digits[0] + ("." + digits[1:] if len(digits) > 1 else "")
    return sign + scientific + "e" + ("+" if point > 0 else "-") + str(abs(point - 1))


def _string(value: str) -> str:
    value.encode("utf-8")  # Reject lone surrogates, including object property names.
    return json.dumps(value, ensure_ascii=False)


def _serialize(value: object) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is str:
        return _string(value)
    if type(value) is int:
        if abs(value) > 2**53 - 1:
            raise ValueError("JCS integers outside the safe IEEE 754 range must be strings")
        return str(value)
    if type(value) is float:
        return _number(value)
    if type(value) is list:
        return "[" + ",".join(_serialize(item) for item in value) + "]"
    if type(value) is dict:
        if any(type(key) is not str for key in value):
            raise TypeError("JCS object property names must be strings")
        keys = sorted(value, key=lambda key: key.encode("utf-16-be"))
        return "{" + ",".join(_string(key) + ":" + _serialize(value[key]) for key in keys) + "}"
    raise TypeError(f"Unsupported JCS value type: {type(value).__name__}")


def jcs_canonicalize(value: object) -> bytes:
    return _serialize(value).encode("utf-8")


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JCS rejects duplicate object property names")
        result[key] = value
    return result


def load_jcs_input(text: str) -> object:
    """Retain duplicate-key evidence before json.loads could silently discard it."""
    value = json.loads(text, object_pairs_hook=_unique_object)
    jcs_canonicalize(value)
    return value
