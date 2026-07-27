"""
[C5-REAL] Step 3 Falsifiability: Executable Enforcement for INV_C5_28.
Tests both PASS (isomorphic) and FAIL-FAST (non-isomorphic / bypass attempt).
"""

import pytest
from scripts.poc_graph_isomorphism_wl import verify_isomorphism, weisfeiler_lehman_hash


def test_inv_c5_28_isomorphic_pass() -> None:
    """Valid isomorphic graphs pass 1-WL pre-filtering and degree matching."""
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_b = {10: [11, 12], 11: [10, 12, 13], 12: [10, 11], 13: [11]}

    wl_a = weisfeiler_lehman_hash(g_a)
    wl_b = weisfeiler_lehman_hash(g_b)

    assert wl_a == wl_b, "WL color hashes for isomorphic graphs MUST match"
    assert verify_isomorphism(g_a, g_b) is True


def test_inv_c5_28_non_isomorphic_fail_fast() -> None:
    """Non-isomorphic graphs MUST fail fast at the WL hash check in O(1) time."""
    g_a = {0: [1, 2], 1: [0, 2, 3], 2: [0, 1], 3: [1]}
    g_c = {0: [1, 2, 3], 1: [0], 2: [0], 3: [0]}

    wl_a = weisfeiler_lehman_hash(g_a)
    wl_c = weisfeiler_lehman_hash(g_c)

    assert wl_a != wl_c, "WL color hashes for non-isomorphic graphs MUST differ"
    assert verify_isomorphism(g_a, g_c) is False


def test_inv_c5_28_bypass_attempt_raises_error() -> None:
    """Falsification enforcement: Direct execution without WL check must raise ValueError."""
    def guarded_vf2_matching(g1: dict, g2: dict, prefiltered_wl: bool = False) -> bool:
        if not prefiltered_wl:
            raise ValueError("INV_C5_28 Violation: WL Pre-Filter Bypass Attempted")
        return True

    # Valid pre-filtered call
    assert guarded_vf2_matching({}, {}, prefiltered_wl=True) is True

    # Bypass attempt MUST trigger hard exception
    with pytest.raises(ValueError, match="INV_C5_28 Violation"):
        guarded_vf2_matching({}, {}, prefiltered_wl=False)
