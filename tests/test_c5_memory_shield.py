"""C5-REAL OPSEC Memory Shield — Verification Suite.

Tests anti-coredump enforcement and PT_DENY_ATTACH syscall on Darwin.
Executed under .venv isolation per INV_C5_09.

CORTEX-TAINT:borjamoskv:opsec_test:2026-07-18T00:13:25+02:00
"""

from __future__ import annotations

import resource
import sys

import pytest


def test_enforce_no_coredump() -> None:
    """RLIMIT_CORE must be (0, 0) after arm()."""
    from babylon60.core.c5_memory_shield import enforce_no_coredump

    enforce_no_coredump()
    soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
    assert soft == 0, f"Soft limit should be 0, got {soft}"
    assert hard == 0, f"Hard limit should be 0, got {hard}"


def test_enforce_anti_debug_darwin() -> None:
    """On Darwin, ptrace(PT_DENY_ATTACH) should succeed (return 0).

    Note: This test can only run once per process. A second call
    returns -1 because the flag is already set. We test that the
    function does not raise and does not SIGKILL.
    """
    if sys.platform != "darwin":
        pytest.skip("PT_DENY_ATTACH is macOS-only")

    from babylon60.core.c5_memory_shield import enforce_anti_debug

    enforce_anti_debug()


def test_arm_returns_status() -> None:
    """arm() must return a typed dict with the three expected keys."""
    from babylon60.core.c5_memory_shield import arm

    status = arm()
    assert isinstance(status, dict)
    assert status["coredump_disabled"] is True
    assert status["antidebug_armed"] is True
    assert status["platform"] == sys.platform
