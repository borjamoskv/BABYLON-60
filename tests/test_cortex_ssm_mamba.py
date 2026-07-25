import math
import os
import sys
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_ssm_mamba_core import StateSpaceModel


def test_ssm_causal_shape() -> None:
    state_dim = 16
    input_dim = 4
    seq_len = 100
    model = StateSpaceModel(state_dim=state_dim, input_dim=input_dim)
    sequence = [[math.sin(i * 0.1)] * input_dim for i in range(seq_len)]
    out = model.forward(sequence)
    assert len(out) == seq_len, "El colapso de longitud de secuencia falló."
    assert len(out[0]) == input_dim, "La topología de salida es divergente."


def test_ssm_thermodynamic_stability() -> None:
    model = StateSpaceModel(state_dim=8, input_dim=2)
    sequence = [[1.0, -1.0] for _ in range(5000)]
    out = model.forward(sequence)
    for val in out[-1]:
        assert not math.isnan(val), "Exergía colapsada: Detectado NaN en horizonte temporal."
        assert not math.isinf(val), "Exergía colapsada: Explosión asintótica (Inf) detectada."


def test_ssm_linear_time_invariant() -> None:
    model = StateSpaceModel(state_dim=8, input_dim=2)
    seq_1000 = [[0.5, -0.5] for _ in range(1000)]
    seq_2000 = [[0.5, -0.5] for _ in range(2000)]
    model.forward(seq_1000)
    t1s = []
    for _ in range(5):
        start = time.perf_counter()
        model.forward(seq_1000)
        t1s.append(time.perf_counter() - start)
    t1 = min(t1s)
    t2s = []
    for _ in range(5):
        start = time.perf_counter()
        model.forward(seq_2000)
        t2s.append(time.perf_counter() - start)
    t2 = min(t2s)
    ratio = t2 / max(t1, 1e-09)
    assert ratio < 3.5, (
        f"Violación de Invariante O(N): Ratio de crecimiento termodinámico {ratio:.2f} excede la cota teórica."
    )
