"""
Codex Adapter & Bidirectional Tunnel for BABYLON-60 / Antigravity
=================================================================
Provides high-exergy duplex IPC communication between Antigravity
(Gemini) and Codex Desktop (GPT-6 Astra Ultra).
"""

from .tunnel_bus import TunnelBus, TunnelMessage
from .codex_driver import CodexDriver

__all__ = ["TunnelBus", "TunnelMessage", "CodexDriver"]
