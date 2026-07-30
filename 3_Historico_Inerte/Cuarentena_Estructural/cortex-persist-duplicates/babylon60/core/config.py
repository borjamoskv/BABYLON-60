# [C5-REAL] Exergy-Maximized
"""
Configuration.

Shared settings and paths for the entire codebase.
Modernized: frozen dataclass with env-var loading + backwards-compat module proxy.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from babylon60.core.paths import (
    CORTEX_DB as DEFAULT_DB_PATH,
)

# ─── Base Paths (canonical, from babylon60.core.paths) ─────────────────
from babylon60.core.paths import (
    CORTEX_DIR,
)


def _moskv_env(key: str, default: str = "") -> str:
    """Helper to fetch env vars with MOSKV_ prefix and CORTEX_ fallback (ADR-0005 L4)."""
    val = os.environ.get(f"MOSKV_{key}")
    if val is not None:
        return val
    return os.environ.get(f"CORTEX_{key}", default)


_AUTH_PEPPER_WARNED = False

# ─── Configuration Dataclass ─────────────────────────────────────────


@dataclass
class CortexConfig:
    """Immutable configuration loaded from environment variables."""

    # Database
    DB_PATH: str = ""
    PG_URL: str = ""  # PostgreSQL/AlloyDB URL for v6 L3

    # Security
    ALLOWED_ORIGINS: list[str] = field(default_factory=list)
    STRICT_CRYPTO_MODE: bool = False
    HKDF_SALT: str = "cortex_v6_tenant_isolation_salt"
    AUTH_PEPPER: str = "cortex_default_pepper_v6_exergy"

    # Boot Mode (v6)
    RUNBOOT_MODE: str = "local"  # local | cloud

    # Rate Limiting
    RATE_LIMIT: int = 300
    RATE_WINDOW: int = 60

    # Graph Backend is exclusively SQLite now
    GRAPH_BACKEND: str = "sqlite"

    # Ledger
    CHECKPOINT_BATCH_SIZE: int = 1000
    CHECKPOINT_MIN: int = 100
    CHECKPOINT_MAX: int = 1000
    CONNECTION_POOL_SIZE: int = 5

    # Federation
    FEDERATION_MODE: str = "single"
    SHARD_DIR: Path = field(default_factory=lambda: CORTEX_DIR / "shards")

    # MCP Guard
    MCP_MAX_CONTENT_LENGTH: int = 50000
    MCP_MAX_TAGS: int = 50
    MCP_MAX_QUERY_LENGTH: int = 2000

    # Cloud Storage
    STORAGE_MODE: str = "local"
    TURSO_DATABASE_URL: str = ""
    TURSO_AUTH_TOKEN: str = ""
    TURBOPUFFER_API_KEY: str = ""

    # Embeddings
    EMBEDDINGS_MODE: str = "local"
    EMBEDDINGS_PROVIDER: str = "gemini"
    EMBEDDINGS_DIMENSION: int = 768
    EMBEDDINGS_MODEL: str = ""  # Override model name (empty = provider default)
    EMBEDDINGS_TASK_TYPE: str = "RETRIEVAL_DOCUMENT"

    # L2 Vector Store
    VECTOR_STORE_PATH: str = ""
    VECTOR_STORE_MODE: str = "local"  # local exclusively (SQLite-vec)

    # LLM Provider
    LLM_PROVIDER: str = "deepseek"
    LLM_MODEL: str = "deepseek-v4"
    LLM_BASE_URL: str = ""
    LLM_API_KEY: str = ""
    LLM_LOCAL_FIRST: bool = False
    LLM_STEALTH_MODE: bool = True

    # Langbase
    LANGBASE_API_KEY: str = ""
    LANGBASE_BASE_URL: str = "https://api.langbase.com/v1"

    # Stripe (SaaS billing)
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    _STRIPE_PRICE_TABLE_RAW: str = ""

    @property
    def STRIPE_PRICE_TABLE(self) -> dict[str, str]:
        """Lazy parsing of Stripe price table."""
        if not self._STRIPE_PRICE_TABLE_RAW:
            return {"pro": "", "team": ""}
        try:
            return json.loads(self._STRIPE_PRICE_TABLE_RAW)
        except json.JSONDecodeError:
            return {"pro": "", "team": ""}

    # Notifications
    TELEGRAM_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""
    NOTIFICATIONS_MIN_SEVERITY: str = "warning"

    # Deployment
    DEPLOY_MODE: str = "local"

    # Context Engine
    CONTEXT_MAX_SIGNALS: int = 20
    CONTEXT_WORKSPACE_DIR: str = ""
    CONTEXT_GIT_ENABLED: bool = True

    # Swarm-Prime (LEGION-10k)
    MAX_SWARM_NODES: int = 10000
    SWARM_SHARD_COUNT: int = 100

    @property
    def PROD(self) -> bool:
        """Helper to check if we are in cloud/production mode."""
        return self.DEPLOY_MODE == "cloud"

    @property
    def IS_PROD(self) -> bool:
        """Alias for PROD."""
        return self.PROD

    @classmethod
    def from_env(cls) -> CortexConfig:
        """Build configuration from environment variables.

        ADR-0005 L4: MOSKV_* takes priority, CORTEX_* is deprecated fallback.
        Third-party vars (TURSO_*, STRIPE_*, LANGBASE_*, TURBOPUFFER_*) are
        NOT namespaced and remain unchanged.
        """
        global _AUTH_PEPPER_WARNED
        storage_mode = _moskv_env("STORAGE", "local")
        deploy_mode = _moskv_env("DEPLOY", "local")
        auth_pepper = _moskv_env("AUTH_PEPPER", "")
        if not auth_pepper:
            if deploy_mode == "cloud":
                raise ValueError(
                    "AUTH_PEPPER must be configured when running in cloud deploy mode."
                )
            else:
                if not _AUTH_PEPPER_WARNED:
                    import logging

                    logging.getLogger("babylon60.config").warning(
                        "AUTH_PEPPER is empty. Falling back to default pepper. Set MOSKV_AUTH_PEPPER in environment."
                    )
                    _AUTH_PEPPER_WARNED = True
                auth_pepper = "cortex_default_pepper_v6_exergy"

        return cls(
            DB_PATH=_moskv_env("DB", str(DEFAULT_DB_PATH)),
            PG_URL=_moskv_env("PG_URL", ""),
            STRICT_CRYPTO_MODE=_moskv_env("STRICT_CRYPTO", "0") == "1",
            HKDF_SALT=_moskv_env("HKDF_SALT", "cortex_v6_tenant_isolation_salt"),
            AUTH_PEPPER=auth_pepper,
            RUNBOOT_MODE=_moskv_env("RUNBOOT", "local"),
            ALLOWED_ORIGINS=[
                o.strip()
                for o in _moskv_env(
                    "ALLOWED_ORIGINS",
                    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:5173,http://localhost:4321,http://127.0.0.1:4321",
                ).split(",")
                if o.strip() != "*" or deploy_mode != "cloud"
            ],
            RATE_LIMIT=int(_moskv_env("RATE_LIMIT", "300")),
            RATE_WINDOW=int(_moskv_env("RATE_WINDOW", "60")),
            CHECKPOINT_BATCH_SIZE=int(_moskv_env("CHECKPOINT_BATCH", "1000")),
            CHECKPOINT_MIN=int(_moskv_env("CHECKPOINT_MIN", "100")),
            CHECKPOINT_MAX=int(_moskv_env("CHECKPOINT_MAX", "1000")),
            CONNECTION_POOL_SIZE=int(_moskv_env("POOL_SIZE", "5")),
            FEDERATION_MODE=_moskv_env("FEDERATION_MODE", "single"),
            SHARD_DIR=Path(_moskv_env("SHARD_DIR", str(CORTEX_DIR / "shards"))),
            MCP_MAX_CONTENT_LENGTH=int(_moskv_env("MCP_MAX_CONTENT", "50000")),
            MCP_MAX_TAGS=int(_moskv_env("MCP_MAX_TAGS", "50")),
            MCP_MAX_QUERY_LENGTH=int(_moskv_env("MCP_MAX_QUERY", "2000")),
            STORAGE_MODE=storage_mode,
            # Third-party: no MOSKV_ prefix (not our namespace)
            TURSO_DATABASE_URL=os.environ.get("TURSO_DATABASE_URL", ""),
            TURSO_AUTH_TOKEN=os.environ.get("TURSO_AUTH_TOKEN", ""),
            TURBOPUFFER_API_KEY=os.environ.get("TURBOPUFFER_API_KEY", ""),
            EMBEDDINGS_MODE=_moskv_env("EMBEDDINGS", "local"),
            EMBEDDINGS_PROVIDER=_moskv_env("EMBEDDINGS_PROVIDER", "gemini"),
            EMBEDDINGS_DIMENSION=int(_moskv_env("EMBEDDINGS_DIM", "768")),
            EMBEDDINGS_MODEL=_moskv_env("EMBEDDINGS_MODEL", ""),
            EMBEDDINGS_TASK_TYPE=_moskv_env("EMBEDDINGS_TASK_TYPE", "RETRIEVAL_DOCUMENT"),
            VECTOR_STORE_PATH=_moskv_env("VECTOR_STORE_PATH", str(CORTEX_DIR / "vectors")),
            VECTOR_STORE_MODE=_moskv_env("VECTOR_STORE_MODE", "local"),
            LLM_PROVIDER=_moskv_env("LLM_PROVIDER", "deepseek"),
            LLM_MODEL=_moskv_env("LLM_MODEL", "deepseek-v4"),
            LLM_BASE_URL=_moskv_env("LLM_BASE_URL", ""),
            LLM_API_KEY=_moskv_env("LLM_API_KEY", ""),
            LLM_LOCAL_FIRST=_moskv_env("LLM_LOCAL_FIRST", "0") == "1",
            LLM_STEALTH_MODE=_moskv_env("LLM_STEALTH", "1") == "1",
            # Third-party: no MOSKV_ prefix
            LANGBASE_API_KEY=os.environ.get("LANGBASE_API_KEY", ""),
            LANGBASE_BASE_URL=os.environ.get("LANGBASE_BASE_URL", "https://api.langbase.com/v1"),
            STRIPE_PUBLISHABLE_KEY=os.environ.get("STRIPE_PUBLISHABLE_KEY", ""),
            STRIPE_SECRET_KEY=os.environ.get("STRIPE_SECRET_KEY", ""),
            STRIPE_WEBHOOK_SECRET=os.environ.get("STRIPE_WEBHOOK_SECRET", ""),
            _STRIPE_PRICE_TABLE_RAW=os.environ.get("STRIPE_PRICE_TABLE", ""),
            DEPLOY_MODE=deploy_mode,
            CONTEXT_MAX_SIGNALS=int(_moskv_env("CONTEXT_MAX_SIGNALS", "20")),
            CONTEXT_WORKSPACE_DIR=_moskv_env("CONTEXT_WORKSPACE", str(Path.home())),
            CONTEXT_GIT_ENABLED=_moskv_env("CONTEXT_GIT", "1") == "1",
            TELEGRAM_TOKEN=_moskv_env("TELEGRAM_TOKEN", ""),
            TELEGRAM_CHAT_ID=_moskv_env("TELEGRAM_CHAT_ID", ""),
            NOTIFICATIONS_MIN_SEVERITY=_moskv_env("NOTIFY_MIN_SEVERITY", "warning"),
        )


# ─── Module-level singleton ──────────────────────────────────────────

_cfg = CortexConfig.from_env()


def reload() -> None:
    """Reload configuration from environment variables."""
    global _cfg
    _cfg = CortexConfig.from_env()
    # Update module-level attributes for backwards compat
    _module = sys.modules[__name__]
    for attr in CortexConfig.__dataclass_fields__:
        if attr.startswith("_"):
            continue
        setattr(_module, attr, getattr(_cfg, attr))

    # Set properties/helpers
    _module.PROD = _cfg.PROD  # type: ignore[reportAttributeAccessIssue]
    _module.IS_PROD = _cfg.IS_PROD  # type: ignore[reportAttributeAccessIssue]


def __getattr__(name: str) -> Any:
    # Evaluate at module level lazily when imported config.STRIPE_PRICE_TABLE
    if name == "STRIPE_PRICE_TABLE":
        return _cfg.STRIPE_PRICE_TABLE
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


# Initialize module-level attributes for backwards compatibility
# (so `from babylon60.config import DB_PATH` still works)
# Static type annotations for module-level variables (Ruff F822, Pyright)
DB_PATH: str
PG_URL: str
ALLOWED_ORIGINS: list[str]
STRICT_CRYPTO_MODE: bool
HKDF_SALT: str
AUTH_PEPPER: str
RUNBOOT_MODE: str
RATE_LIMIT: int
RATE_WINDOW: int
CHECKPOINT_BATCH_SIZE: int
CHECKPOINT_MIN: int
CHECKPOINT_MAX: int
CONNECTION_POOL_SIZE: int
FEDERATION_MODE: str
SHARD_DIR: Path
MCP_MAX_CONTENT_LENGTH: int
MCP_MAX_TAGS: int
MCP_MAX_QUERY_LENGTH: int
STORAGE_MODE: str
TURSO_DATABASE_URL: str
TURSO_AUTH_TOKEN: str
TURBOPUFFER_API_KEY: str
EMBEDDINGS_MODE: str
EMBEDDINGS_PROVIDER: str
EMBEDDINGS_DIMENSION: int
EMBEDDINGS_MODEL: str
EMBEDDINGS_TASK_TYPE: str
VECTOR_STORE_PATH: str
VECTOR_STORE_MODE: str
LLM_PROVIDER: str
LLM_MODEL: str
LLM_BASE_URL: str
LLM_API_KEY: str
LLM_LOCAL_FIRST: bool
LLM_STEALTH_MODE: bool
LANGBASE_API_KEY: str
LANGBASE_BASE_URL: str
STRIPE_PUBLISHABLE_KEY: str
STRIPE_SECRET_KEY: str
STRIPE_WEBHOOK_SECRET: str
TELEGRAM_TOKEN: str
TELEGRAM_CHAT_ID: str
NOTIFICATIONS_MIN_SEVERITY: str
DEPLOY_MODE: str
CONTEXT_MAX_SIGNALS: int
CONTEXT_WORKSPACE_DIR: str
CONTEXT_GIT_ENABLED: bool
MAX_SWARM_NODES: int
SWARM_SHARD_COUNT: int
PROD: bool
IS_PROD: bool
STRIPE_PRICE_TABLE: dict[str, str]

reload()

# Bound the star-import surface of the config.py compat shim (FIND-005).
# Exactly: the config class, reload(), the derived helpers, and every public
# dataclass field mirrored onto the module by reload().
__all__ = [
    "CortexConfig",
    "reload",
    "PROD",
    "IS_PROD",
    "STRIPE_PRICE_TABLE",
    *[f for f in CortexConfig.__dataclass_fields__ if not f.startswith("_")],
]
