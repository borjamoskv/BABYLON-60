"""Frozen behavioral acceptance; candidate code is supplied by CG_CANDIDATE_ROOT."""

import ast
import inspect
import json
import os
from pathlib import Path
import sys

import pytest


PACKAGE = Path(__file__).absolute().parents[1]
CANDIDATE = Path(os.environ["CG_CANDIDATE_ROOT"]).absolute()
sys.path.insert(0, str(CANDIDATE / "src"))

from babylon60.guards.capabilities import RiskTier  # noqa: E402
from babylon60.guards.capability_guard import CapabilityGuard  # noqa: E402


CASES = json.loads((PACKAGE / "acceptance/cases.json").read_text())


def decode(value):
    if isinstance(value, dict) and set(value) == {"risk"}:
        return getattr(RiskTier, value["risk"])
    return value


@pytest.mark.parametrize("case", CASES, ids=[case["id"] for case in CASES])
def test_permission_contract(case):
    guard = CapabilityGuard(allowed_capabilities=case["capabilities"])
    actual = guard.check_permission(decode(case["action"]), decode(case["risk"]))
    assert actual is case["expected"], case["criterion"]


def test_public_parameter_names_and_defaults():
    constructor = inspect.signature(CapabilityGuard.__init__)
    assert list(constructor.parameters) == ["self", "allowed_capabilities"]
    assert constructor.parameters["allowed_capabilities"].default is None
    method = inspect.signature(CapabilityGuard.check_permission)
    assert list(method.parameters) == ["self", "action", "risk"]
    assert method.parameters["risk"].default is RiskTier.LOW


def tool_validator(tree):
    cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CapabilityGuard")
    return next(node for node in cls.body if isinstance(node, ast.FunctionDef) and node.name == "validate_tool_execution")


def test_tool_validation_remains_outside_this_task():
    relative = "src/babylon60/guards/capability_guard.py"
    before = ast.parse((PACKAGE / "snapshot" / relative).read_text())
    after = ast.parse((CANDIDATE / relative).read_text())
    assert ast.dump(tool_validator(before)) == ast.dump(tool_validator(after))


def test_risk_tier_contract_is_preserved():
    assert [risk.name for risk in RiskTier] == ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    assert [risk.value for risk in RiskTier] == [1, 2, 3, 4]
