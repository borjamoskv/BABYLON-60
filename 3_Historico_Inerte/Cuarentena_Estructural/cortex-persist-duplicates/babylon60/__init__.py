# [C5-REAL] Exergy-Maximized
"""
BABYLON-60 - The Sovereign Ledger for AI Agents.

Local-first memory infrastructure with vector search, temporal facts,
and cryptographic vaults. Zero network dependencies.
"""

import sys

try:
    # Use pysqlite3 if available (allows newer SQLite versions + extensions)
    __import__("pysqlite3")
    sys.modules["sqlite3"] = sys.modules.pop("pysqlite3")
except ImportError:
    pass

import logging

import babylon60.compat  # noqa: F401

# [C5-REAL] Global PII Scrubbing
_original_get_message = logging.LogRecord.getMessage


def _scrubbed_get_message(self):
    msg = _original_get_message(self)
    if "[REDACTED_PII]" in msg:
        msg = msg.replace("~", "~").replace("[REDACTED_PII]", "[REDACTED]")
    return msg


logging.LogRecord.getMessage = _scrubbed_get_message

__version__ = "1.1.1"
__author__ = "by borjamoskv.com"

# Lazy imports - CortexEngine, client SDK, and core modules
_LAZY_IMPORTS = {
    "CortexEngine": "babylon60.engine",
    "api": "babylon60.api",
    "routes": "babylon60.routes",
    "CortexClient": "babylon60.api.client",
    "CortexError": "babylon60.api.client",
    "Fact": "babylon60.api.client",
    "AsyncCortexClient": "babylon60.api.async_client",
    "search": "babylon60.search",
    "storage": "babylon60.storage",
    "guards": "babylon60.guards",
}

_EXPERIMENTAL_MODULES = (
    "autopoiesis",
    "circadian_cycle",
    "digital_endocrine",
    "epigenetic_memory",
    "strategic_disobedience",
    "zero_prompting",
)


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        import importlib

        mod = importlib.import_module(_LAZY_IMPORTS[name])
        if _LAZY_IMPORTS[name] == f"babylon60.{name}":
            globals()[name] = mod
            return mod
        attr = getattr(mod, name)
        globals()[name] = attr  # Cache for subsequent access
        return attr
    if name in _EXPERIMENTAL_MODULES:
        try:
            import importlib

            mod = importlib.import_module(f"babylon60.experimental.{name}")
            globals()[name] = mod
            return mod
        except ImportError as err:
            raise AttributeError(f"module 'babylon60' has no attribute {name!r}") from err
    raise AttributeError(f"module 'babylon60' has no attribute {name!r}")


__all__ = [
    "CortexEngine",
    "__version__",
    "api",
    "routes",
    "CortexClient",
    "AsyncCortexClient",
    "CortexError",
    "Fact",
]  # pyright: ignore[reportUnsupportedDunderAll]
