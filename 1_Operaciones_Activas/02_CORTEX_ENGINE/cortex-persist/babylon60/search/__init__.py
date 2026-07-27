# [C5-REAL] Exergy-Maximized
# This file is part of CORTEX.
# Licensed under the Apache License, Version 2.0.
# See top-level LICENSE file for details.
# Change Date: 2030-01-01 (Transitions to Apache 2.0)

"""CORTEX Search Package.

Status: IMPLEMENTED (Ω₁₃ - causal gap wired into hybrid search).
"""

from __future__ import annotations

import importlib
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from babylon60.search.causal_gap import (
        CausalGap,
        SearchCandidate,
        compute_candidate_score,
        retrieve_for_causal_gap,
    )
    from babylon60.search.hybrid import hybrid_search, hybrid_search_sync
    from babylon60.search.models import SearchResult
    from babylon60.search.text import text_search, text_search_sync
    from babylon60.search.vector import semantic_search, semantic_search_sync

__all__ = [
    "CausalGap",
    "SearchCandidate",
    "SearchResult",
    "compute_candidate_score",
    "hybrid_search",
    "hybrid_search_sync",
    "retrieve_for_causal_gap",
    "semantic_search",
    "semantic_search_sync",
    "text_search",
    "text_search_sync",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "CausalGap": ("babylon60.search.causal_gap", "CausalGap"),
    "SearchCandidate": ("babylon60.search.causal_gap", "SearchCandidate"),
    "SearchResult": ("babylon60.search.models", "SearchResult"),
    "compute_candidate_score": ("babylon60.search.causal_gap", "compute_candidate_score"),
    "hybrid_search": ("babylon60.search.hybrid", "hybrid_search"),
    "hybrid_search_sync": ("babylon60.search.hybrid", "hybrid_search_sync"),
    "retrieve_for_causal_gap": ("babylon60.search.causal_gap", "retrieve_for_causal_gap"),
    "semantic_search": ("babylon60.search.vector", "semantic_search"),
    "semantic_search_sync": ("babylon60.search.vector", "semantic_search_sync"),
    "text_search": ("babylon60.search.text", "text_search"),
    "text_search_sync": ("babylon60.search.text", "text_search_sync"),
}


def __getattr__(name: str):
    if name in _LAZY_IMPORTS:
        module_path, attr_name = _LAZY_IMPORTS[name]
        module = importlib.import_module(module_path)
        value = getattr(module, attr_name)
        globals()[name] = value
        return value
    try:
        return importlib.import_module(f"babylon60.search.{name}")
    except ImportError as e:
        raise AttributeError(f"module 'babylon60.search' has no attribute {name!r}") from e


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
