# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
Finite acceptance/rejection checks for the WL filter and exact isomorphism API.
"""

import pytest
from scripts.c5_demos.poc_graph_isomorphism_wl import verify_isomorphism, weisfeiler_lehman_hash


def test_inv_c5_28_isomorphic_pass() -> None:
    """This renamed graph passes the filter and the exact bijection check."""
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_b = {10: [11, 12], 11: [10, 12, 13], 12: [10, 11], 13: [11]}

    wl_a = weisfeiler_lehman_hash(g_a)
    wl_b = weisfeiler_lehman_hash(g_b)

    assert wl_a == wl_b, "WL color hashes for isomorphic graphs MUST match"
    assert verify_isomorphism(g_a, g_b) is True


def test_inv_c5_28_non_isomorphic_fail_fast() -> None:
    """This pair has different filter digests and is rejected."""
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_c = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}

    wl_a = weisfeiler_lehman_hash(g_a)
    wl_c = weisfeiler_lehman_hash(g_c)

    assert wl_a != wl_c, "The selected pair is distinguishable by this WL profile"
    assert verify_isomorphism(g_a, g_c) is False


def test_inv_c5_28_bypass_attempt_raises_error() -> None:
    """Malformed graph input cannot bypass validation via the size fast path."""
    with pytest.raises(ValueError, match="referenced vertex"):
        verify_isomorphism({0: [1]}, {})
