# [C5-REAL] Exergy-Maximized

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TrendsConfig:
    """Configuration for the Google Trends Oracle sidecar."""

    watchlist: list[str] = field(default_factory=list)

    geos: list[str] = field(default_factory=lambda: [""])

    categories: list[int] = field(default_factory=lambda: [0])

    realtime_interval: int = 900  # 15 minutes by default
    daily_interval: int = 21600  # 6 hours by default
    interest_interval: int = 86400  # 24 hours by default

    max_retries: int = 3
    base_backoff: float = 1.5

    cache_ttl: int = 3600  # 1 hour deduplication window

    enable_realtime: bool = True
