from __future__ import annotations
import resource
import sys
import pytest

def test_enforce_no_coredump() -> None:
    from babylon60.core.c5_memory_shield import enforce_no_coredump
    enforce_no_coredump()
    soft, hard = resource.getrlimit(resource.RLIMIT_CORE)
    assert soft == 0, f'Soft limit should be 0, got {soft}'
    assert hard == 0, f'Hard limit should be 0, got {hard}'

def test_enforce_anti_debug_darwin() -> None:
    if sys.platform != 'darwin':
        pytest.skip('PT_DENY_ATTACH is macOS-only')
    from babylon60.core.c5_memory_shield import enforce_anti_debug
    enforce_anti_debug()

def test_arm_returns_status() -> None:
    from babylon60.core.c5_memory_shield import arm
    status = arm()
    assert isinstance(status, dict)
    assert status['coredump_disabled'] is True
    assert status['antidebug_armed'] is True
    assert status['platform'] == sys.platform