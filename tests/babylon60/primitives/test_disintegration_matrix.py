import pytest
from babylon60.primitives.disintegration_matrix import disintegrate, disintegration_matrix, pushforward, support, verify_symmetry

def test_bayesian_disintegration_valid():
    p = {"state_A": 0.7, "state_B": 0.3, "state_C": 0.0}
    F = {
        "state_A": {"obs_1": 0.8, "obs_2": 0.2},
        "state_B": {"obs_1": 0.1, "obs_2": 0.9},
        "state_C": {"obs_1": 0.5, "obs_2": 0.5},
    }
    
    # 1. Test pushforward
    q = pushforward(p, F)
    assert abs(q["obs_1"] - (0.7 * 0.8 + 0.3 * 0.1)) < 1e-6
    assert abs(q["obs_2"] - (0.7 * 0.2 + 0.3 * 0.9)) < 1e-6
    
    # 2. Test disintegration
    post_obs1 = disintegrate(p, F, "obs_1")
    assert "state_C" not in post_obs1 or post_obs1["state_C"] == 0.0
    
    # 3. Test full matrix
    D = disintegration_matrix(p, F)
    
    # 4. Verify AX-BD-1 Symmetry Invariant
    assert verify_symmetry(p, F, D) is True

def test_hallucination_prevention():
    p = {"A": 1.0, "B": 0.0}
    F = {
        "A": {"y1": 1.0, "y2": 0.0},
        "B": {"y1": 0.0, "y2": 1.0}
    }
    
    # Observation y2 is impossible under prior p because p(B)=0
    with pytest.raises(ValueError, match="hallucinated"):
        disintegrate(p, F, "y2")
    
    # strict=False should suppress the exception and omit y2 from the kernel
    D_loose = disintegration_matrix(p, F, strict=False)
    assert "y2" not in D_loose
    assert "y1" in D_loose
