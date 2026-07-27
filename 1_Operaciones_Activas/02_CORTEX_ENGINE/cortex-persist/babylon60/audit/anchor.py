# [C5-REAL] Exergy-Maximized
"""
Anchor Provider Protocol and Implementations.

Defines a pluggable interface for external anchoring of ledger entries.
Default: local file. Optional: Sigstore Rekor transparency log.
"""

import logging
import os
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from babylon60.edge_runtime import EdgeEnv

logger = logging.getLogger("babylon60.audit.anchor")


class AnchorError(Exception):
    """Raised when an anchor operation fails irrecoverably."""


@runtime_checkable
class AnchorProvider(Protocol):
    """Protocol for external anchoring of ledger audit entries.

    Implementations must be async-capable and return an anchor reference
    string suitable for storage in the `external_anchor` column of
    security_audit_log.
    """

    async def anchor(self, audit_id: str, timestamp: str) -> str:
        """Anchor an audit entry and return a reference string.

        Args:
            audit_id: The Base60-encoded SHA-256 hash of the envelope.
            timestamp: ISO 8601 timestamp of the ledger event.

        Returns:
            An anchor reference string (e.g., 'local_file:~/.babylon60/anchors.log'
            or 'rekor:<uuid>').

        Raises:
            AnchorError: If anchoring fails irrecoverably.
        """
        ...


class LocalFileAnchor:
    """Default anchor provider: appends to ~/.babylon60/anchors.log."""

    def __init__(self, anchor_dir: str | None = None) -> None:
        if anchor_dir:
            self._anchor_dir = anchor_dir
        else:
            cortex_base = EdgeEnv.get("CORTEX_DIR") or EdgeEnv.get("BABYLON_DIR")
            if cortex_base:
                self._anchor_dir = os.path.join(cortex_base, ".babylon60")
            else:
                self._anchor_dir = os.path.join(
                    os.path.expanduser("~"), ".babylon60"
                )

    async def anchor(self, audit_id: str, timestamp: str) -> str:
        """Append audit_id to local anchors.log file."""
        try:
            os.makedirs(self._anchor_dir, exist_ok=True)
            anchor_file = os.path.join(self._anchor_dir, "anchors.log")
            with open(anchor_file, "a") as f:
                f.write(f"{timestamp} | {audit_id}\n")
            return f"local_file:{anchor_file}"
        except Exception as e:
            raise AnchorError(f"Local file anchor failed: {e}") from e


class RekorAnchor:
    """Sigstore Rekor transparency log anchor provider.

    Delegates to the existing RekorClient for actual Rekor API interaction.
    Requires the `rekor` extra (httpx).
    """

    def __init__(self, rekor_url: str | None = None) -> None:
        self._rekor_url = rekor_url
        self._client = None

    async def _get_client(self):
        if self._client is None:
            from babylon60.audit.rekor_client import RekorClient

            if self._rekor_url:
                self._client = RekorClient(rekor_url=self._rekor_url)
            else:
                self._client = RekorClient()
        return self._client

    async def anchor(self, audit_id: str, timestamp: str) -> str:
        """Submit entry hash to Rekor and return rekor:<uuid> reference."""
        try:
            client = await self._get_client()
            # RekorClient.log_entry requires signature and public key;
            # those are not available at the anchor layer alone.
            # This is a stub — full integration requires passing signature
            # and public key from the ledger's log_action call.
            logger.warning(
                "[Rekor] RekorAnchor.anchor() is a stub. "
                "Full integration requires signature passthrough."
            )
            return f"rekor:pending:{audit_id}"
        except Exception as e:
            raise AnchorError(f"Rekor anchor failed: {e}") from e


def get_default_anchor_provider() -> AnchorProvider:
    """Factory: returns the configured anchor provider.

    Uses CORTEX_ANCHOR_PROVIDER / BABYLON_ANCHOR_PROVIDER env var.
    Values: 'local' (default), 'rekor'.
    """
    provider_name = (
        EdgeEnv.get("CORTEX_ANCHOR_PROVIDER")
        or EdgeEnv.get("BABYLON_ANCHOR_PROVIDER")
        or "local"
    )
    if provider_name == "rekor":
        return RekorAnchor()
    return LocalFileAnchor()
