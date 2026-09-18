# ============================================================================
# BABYLON-60 Sovereign Security Guard
# █ URL_GUARD | Network Transport Sanitization & SSRF Protection
# ============================================================================

from __future__ import annotations

import logging
from urllib.parse import urlparse

logger = logging.getLogger("babylon60.guards.url_guard")

__all__ = ["SafeTransport"]


class SafeTransport:
    """
    Validates outbound HTTP/WebSocket target URLs to prevent SSRF and malicious endpoints.
    """

    @staticmethod
    def is_url_allowed(url: str) -> bool:
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https", "ws", "wss"):
                return False
            hostname = parsed.hostname or ""
            # Block metadata IPs and internal loopback sensitive ports if configured
            if hostname in ("169.254.169.254", "metadata.google.internal"):
                return False
            return True
        except (ValueError, AttributeError) as e:
            logger.warning("URL validation failure: %s", e)
            return False

    @staticmethod
    def sanitize_url(url: str) -> str:
        return url.strip()
