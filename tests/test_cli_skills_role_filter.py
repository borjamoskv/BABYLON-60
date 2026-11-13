"""Routing honors the same role boundary as skill listing."""

from __future__ import annotations

import argparse
import json

import pytest

from babylon60.cli.main_dispatcher import cmd_skills


@pytest.mark.parametrize("role", ["auditor", "arquitecto", "ejecutor"])
def test_route_only_elects_candidates_from_requested_role(
    role: str, capsys: pytest.CaptureFixture[str]
) -> None:
    args = argparse.Namespace(scope="workspace", role=role, query="wizard", skills_action="route", json=True)
    result = cmd_skills(args)
    payload = json.loads(capsys.readouterr().out)
    if result == 0:
        assert payload["role"] == role
    else:
        assert result == 1
        assert payload["elected"] is None


def test_route_without_role_keeps_exact_match(capsys: pytest.CaptureFixture[str]) -> None:
    args = argparse.Namespace(scope="workspace", role="all", query="wizard", skills_action="route", json=True)
    assert cmd_skills(args) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["name"] == "wizard"
    assert payload["role"] == "ejecutor"
