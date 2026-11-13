"""Closed public-fixture exceptions must preserve detection beside the fixture."""

from __future__ import annotations

import base64
import hashlib
import json
from pathlib import Path
import re
from typing import Any

import pytest

from scripts.c5_quality_gates.secret_swarm_auditor import (
    PATTERNS,
    PUBLIC_FIXTURE_EXCEPTIONS,
    _is_public_fixture,
    scan_file,
)
from scripts.c5_quality_gates.verify_claims import is_excluded_from_public_tree


ROOT = Path(__file__).absolute().parents[1]
RULES = tuple(PUBLIC_FIXTURE_EXCEPTIONS)


def _rule_params() -> list[Any]:
    """One case per rule. A fixture under VAULT_ONLY_PREFIXES that is absent here (the
    public projection drops it) is reported NOT_CHECKED; it runs in the private repo.
    A missing fixture outside those prefixes still fails."""
    params = []
    for relative, pattern, fingerprint in RULES:
        if not (ROOT / relative).exists() and is_excluded_from_public_tree(relative):
            reason = f"NOT_CHECKED: vault-only fixture absent from the public projection ({relative})"
            params.append(pytest.param(relative, pattern, fingerprint, marks=pytest.mark.skip(reason=reason)))
        else:
            params.append(pytest.param(relative, pattern, fingerprint))
    return params


RULE_PARAMS = _rule_params()


@pytest.mark.parametrize("relative,pattern,fingerprint", RULE_PARAMS)
def test_exact_reviewed_fixture_requires_all_three_fields(
    relative: str,
    pattern: str,
    fingerprint: str,
) -> None:
    source = ROOT / relative
    strict = scan_file(str(source))
    assert any(item["type"] == pattern and item["fingerprint"] == fingerprint for item in strict), fingerprint
    qualified = scan_file(str(source), str(ROOT))
    assert not any(item["type"] == pattern and item["fingerprint"] == fingerprint for item in qualified), fingerprint


@pytest.mark.parametrize("relative,pattern,fingerprint", RULE_PARAMS)
def test_another_secret_on_the_same_line_and_file_is_still_detected(
    tmp_path: Path,
    relative: str,
    pattern: str,
    fingerprint: str,
) -> None:
    source = ROOT / relative
    strict = scan_file(str(source))
    line = next(item["line"] for item in strict if item["type"] == pattern and item["fingerprint"] == fingerprint)
    lines = source.read_text().splitlines(keepends=True)
    # Generated synthetic canary, never an external service credential.
    canary = "A" + base64.b64encode(hashlib.sha384(b"public-fixture-adversarial-canary").digest()).decode() + "Z"
    assignment = "{} = {}".format("api_key", json.dumps(canary))
    lines[line - 1] = lines[line - 1].rstrip("\n") + "; " + assignment + "\n"
    candidate = tmp_path / relative
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_text("".join(lines))
    observed = scan_file(str(candidate), str(tmp_path))
    canary_fingerprint = hashlib.sha3_256(canary.encode()).hexdigest()
    assert any(item["type"] == pattern and item["fingerprint"] == canary_fingerprint for item in observed)
    assert not any(item["type"] == pattern and item["fingerprint"] == fingerprint for item in observed)


@pytest.mark.parametrize("relative,pattern,fingerprint", RULE_PARAMS)
def test_a_different_path_does_not_inherit_a_public_fixture_exception(
    tmp_path: Path,
    relative: str,
    pattern: str,
    fingerprint: str,
) -> None:
    candidate = tmp_path / "different-path" / Path(relative).name
    candidate.parent.mkdir(parents=True, exist_ok=True)
    candidate.write_bytes((ROOT / relative).read_bytes())
    observed = scan_file(str(candidate), str(tmp_path))
    assert any(item["type"] == pattern and item["fingerprint"] == fingerprint for item in observed), fingerprint


def test_exception_does_not_match_a_different_detector_or_truncated_fingerprint() -> None:
    relative, pattern, fingerprint = RULES[0]
    finding = {"file": str(ROOT / relative), "type": pattern, "fingerprint": fingerprint}
    assert _is_public_fixture(finding, str(ROOT))
    assert not _is_public_fixture({**finding, "type": "PRIVATE_KEY"}, str(ROOT))
    assert not _is_public_fixture({**finding, "fingerprint": fingerprint[:16] + "0" * 48}, str(ROOT))
    assert not _is_public_fixture(finding, str(ROOT / "unrelated-root"))


def test_fixture_exceptions_are_closed_and_individually_justified() -> None:
    for (relative, pattern, fingerprint), reason in PUBLIC_FIXTURE_EXCEPTIONS.items():
        path = Path(relative)
        assert not path.is_absolute() and ".." not in path.parts
        assert not any(symbol in relative for symbol in "*?[]")
        assert pattern in PATTERNS or pattern == "HIGH_ENTROPY_STRING"
        assert re.fullmatch("[0-9a-f]{64}", fingerprint)
        assert reason.strip()
