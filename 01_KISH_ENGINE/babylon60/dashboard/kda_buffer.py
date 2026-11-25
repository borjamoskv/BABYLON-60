from collections.abc import Sequence

import io
import json
from typing import Dict, Optional, Any


class KdaMemoryBuffer:
    """
    KDA Memory Buffer (Kinetic Data Access).
    Provides a completely isolated, in-memory buffer for dashboard rendering.
    Prevents any disk-level path traversal or working directory leakage.
    """

    def __init__(self) -> None:
        self._assets: Dict[str, Dict[str, Any]] = {}
        self._telemetry_buffer = io.BytesIO()

    def store_asset(self, path: str, content: bytes, content_type: str) -> None:
        """Stores a static asset directly in memory."""
        self._assets[path] = {"content": content, "content_type": content_type}

    def get_asset(self, path: str) -> Optional[Dict[str, Any]]:
        """Retrieves a static asset from memory."""
        return self._assets.get(path)

    def write_telemetry(self, data: Sequence[object]) -> None:
        """Writes telemetry to the memory buffer, overwriting previous content."""
        self._telemetry_buffer.seek(0)
        self._telemetry_buffer.write(json.dumps(data).encode("utf-8"))
        self._telemetry_buffer.truncate()

    def read_telemetry(self) -> bytes:
        """Reads the currently buffered telemetry."""
        return self._telemetry_buffer.getvalue()


# Global KDA instance
kda_buffer = KdaMemoryBuffer()
