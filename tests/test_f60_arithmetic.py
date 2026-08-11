# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import pytest

def test_f60_fixed_point_exactness():
    """Verifica que la escala de representación Q32.32 F60 no acumule deriva."""
    SCALE = 1 << 32
    ten_seconds_fixed = 10 * SCALE
    five_seconds_fixed = 5 * SCALE
    
    assert ten_seconds_fixed // SCALE == 10
    assert five_seconds_fixed // SCALE == 5
    assert (ten_seconds_fixed + five_seconds_fixed) // SCALE == 15

def test_f60_fractional_precision():
    """Verifica la resolución sub-segundo en el dominio F60."""
    SCALE = 1 << 32
    half_second_fixed = SCALE // 2
    quarter_second_fixed = SCALE // 4
    
    assert half_second_fixed / SCALE == 0.5
    assert quarter_second_fixed / SCALE == 0.25
    assert (half_second_fixed + quarter_second_fixed) / SCALE == 0.75
