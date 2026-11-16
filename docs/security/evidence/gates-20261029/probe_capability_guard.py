#!/usr/bin/env python3
"""Exercise the actual Python guard without executing any requested operation."""

import hashlib
import json
from pathlib import Path
import sys


root = Path(__file__).absolute().parents[4]
sys.path.insert(0, str(root / "01_KISH_ENGINE"))

from babylon60.guards.capabilities import RiskTier  # noqa: E402
from babylon60.guards.capability_guard import CapabilityGuard  # noqa: E402


guard = CapabilityGuard(allowed_capabilities=["read"])
observed = {
    "allowed_capabilities": guard.allowed_capabilities,
    "write_without_write_capability": guard.check_permission("write", RiskTier.LOW),
    "unrecognized_tool": guard.validate_tool_execution("unreviewed_effect", {"fixture": True}),
    "explicit_critical_action": guard.check_permission("write", RiskTier.CRITICAL),
    "effect_executed": False,
}
assert observed["write_without_write_capability"] is True
assert observed["unrecognized_tool"] is True
assert observed["explicit_critical_action"] is False
source = root / "01_KISH_ENGINE/babylon60/guards/capability_guard.py"
observed["source_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
print(json.dumps(observed, indent=2))
