# [C5-REAL] Exergy-Maximized Unit Test
import sys
import pytest


def test_namespace_compatibility():
    # Import babylon60 to initialize system-level hooks
    import babylon60

    # Attempt importing from legacy namespace
    try:
        import cortex.guards.ouroboros_entropy_guard as compat_guard
        import babylon60.guards.ouroboros_entropy_guard as real_guard
    except ImportError as e:
        pytest.fail(f"Compatibility alias import failed: {e}")

    assert compat_guard is real_guard
    assert compat_guard.OuroborosEntropyGuard is real_guard.OuroborosEntropyGuard
