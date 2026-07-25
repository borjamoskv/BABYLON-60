# C5-REAL EXERGY CERTIFIED
"""
Test suite for CORTEX Claude Code Bridge (C5-REAL).
"""

from cortex.claude_bridge import ClaudeCodeBridge

def test_claude_bridge_availability() -> None:
    bridge = ClaudeCodeBridge()
    assert isinstance(bridge.is_available(), bool)

def test_claude_bridge_query_structure() -> None:
    bridge = ClaudeCodeBridge(binary_path="/nonexistent/bin/claude")
    assert not bridge.is_available()

    res = bridge.query("Test prompt")
    assert res["status"] in ("EXEC_ERROR", "QUOTA_EXHAUSTED", "TIMEOUT")
    assert res["fallback_required"] is True
