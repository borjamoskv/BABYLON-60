"""Regressions for private tools/skill_library scripts, split from test_swarm100_lot1_regressions.py.

The public projection omits tools/skill_library/ and therefore omits this module.
"""

# ruff: noqa: F811  (pytest fixtures imported from the public module)
from __future__ import annotations

import copy
import json
import sys
from typing import Any
import pytest

from test_swarm100_lot1_regressions import (  # noqa: F401  shared helpers and fixtures
    load_source,
)

SOCINT_PATHS = [
    "tools/skill_library/global/c5-socint-extraction-suite/scripts/socint_extract.py",
    "tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py",
]


@pytest.fixture(params=SOCINT_PATHS, ids=["primary", "bundled"])
def socint(request):
    return load_source(request.param, "lot1_socint_fixture")


@pytest.mark.parametrize("change", ["swap", "rename", "type", "nested_type"])
def test_socint_seal_binds_names_types_and_values(socint, change):
    original: dict[str, Any] = {"author": "alice", "text": "hello", "nested": {"value": 1}}
    changed = copy.deepcopy(original)
    if change == "swap":
        changed["author"], changed["text"] = changed["text"], changed["author"]
    elif change == "rename":
        changed["renamed"] = changed.pop("author")
    elif change == "type":
        original, changed = {"value": 1}, {"value": "1"}
    else:
        changed["nested"]["value"] = 1.0
    assert socint.compute_merkle_root(original) != socint.compute_merkle_root(changed)


def test_socint_determinism_and_empty_odd_nested_records(socint):
    a = {"b": [None, True, {"value": 2.5}], "a": "á", "c": 3}
    b = {"c": 3, "a": "á", "b": [None, True, {"value": 2.5}]}
    assert socint.compute_merkle_root(a) == socint.compute_merkle_root(b)
    assert len(socint.compute_merkle_root({})) == 64
    assert socint.compute_merkle_root({}) != socint.compute_merkle_root({"empty": ""})


@pytest.mark.parametrize("value", [float("nan"), float("inf"), {1: "non-string-key"}, (1, 2)])
def test_socint_rejects_non_json_or_nonfinite_values(socint, value):
    with pytest.raises((TypeError, ValueError)):
        socint.compute_merkle_root({"value": value})


def test_socint_versioned_seal_verifies_exact_body(socint):
    original = {"author": "alice", "text": "fixture", "actor_network": {"nodes": ["alice"]}}
    result = socint.seal_evidence(original)
    assert "merkle_seal" not in original
    assert result["merkle_seal"]["scheme"] == "socint-fields-v2"
    assert result["merkle_seal"]["covered_fields"] == sorted(original)
    assert socint.verify_evidence_seal(result)
    changed = copy.deepcopy(result)
    changed["actor_network"]["nodes"].append("changed")
    assert not socint.verify_evidence_seal(changed)
    result["uncovered_addition"] = True
    assert not socint.verify_evidence_seal(result)
    assert not socint.verify_evidence_seal({"merkle_seal": {"merkle_root": "0" * 64}})


def test_socint_producer_seals_final_network_fields(socint, monkeypatch, tmp_path):
    monkeypatch.setattr(socint.XAdapter, "parse_url", lambda url: ("tweet", "fixture", "1"))
    monkeypatch.setattr(
        socint.XAdapter,
        "fetch_tweet",
        lambda *args: {
            "platform": "x",
            "author": "fixture",
            "text": "Synthetic fixture text",
            "id": "1",
        },
    )
    monkeypatch.setattr(socint, "http_get", lambda *a, **k: pytest.fail("No network in producer fixture"))
    output = tmp_path / "socint.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "socint",
            "--url",
            "https://example.invalid/post",
            "--platform",
            "x",
            "--network",
            "--centrality-check",
            "--format",
            "json",
            "--output",
            str(output),
        ],
    )
    socint.main()
    document = json.loads(output.read_text())
    assert "actor_network" in document and "network_centrality" in document
    assert socint.verify_evidence_seal(document)
    assert "actor_network" in document["merkle_seal"]["covered_fields"]
    assert "network_centrality" in document["merkle_seal"]["covered_fields"]
