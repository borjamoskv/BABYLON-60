#!/usr/bin/env python3
"""Compatibility entrypoint for the maintained loopback-only dashboard.

Running this source checkout directly and using ``babylon60-dashboard`` share
the same handler, telemetry fields and error policy.
"""

import sys
from pathlib import Path


_SOURCE_ROOT = Path(__file__).absolute().parents[2] / "01_KISH_ENGINE"
if (_SOURCE_ROOT / "babylon60" / "dashboard" / "server.py").is_file():
    sys.path.insert(0, str(_SOURCE_ROOT))

from babylon60.dashboard.server import ExergyDashboardHandler, main  # noqa: E402

__all__ = ["ExergyDashboardHandler", "main"]


if __name__ == "__main__":
    main()
