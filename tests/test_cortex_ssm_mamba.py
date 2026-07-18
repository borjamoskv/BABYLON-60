# C5-REAL
# MOSKV-1 APEX SINGULARITY
# FALSACIÓN EMPÍRICA: STATE SPACE MODEL CORE

import sys
import os
import time
import math

# Add parent directory to path to import cortex_ssm_mamba_core
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_ssm_mamba_core import StateSpaceModel


def test_ssm_causal_shape() -> None:
    """Verifica que la matriz causal preserva las dimensiones del tensor en T=0."""
    state_dim = 16
    input_dim = 4
    seq_len = 100
    model = StateSpaceModel(state_dim=state_dim, input_dim=input_dim)

    sequence = [[math.sin(i * 0.1)] * input_dim for i in range(seq_len)]
    out = model.forward(sequence)

    assert len(out) == seq_len, "El colapso de longitud de secuencia falló."
    assert len(out[0]) == input_dim, "La topología de salida es divergente."


def test_ssm_thermodynamic_stability() -> None:
    """Aserción de estabilidad frente a explosión de gradientes (NaN) en horizonte de 5000 iteraciones."""
    model = StateSpaceModel(state_dim=8, input_dim=2)
    sequence = [[1.0, -1.0] for _ in range(5000)]
    out = model.forward(sequence)

    # Check the last output for stability
    for val in out[-1]:
        assert not math.isnan(val), "Exergía colapsada: Detectado NaN en horizonte temporal."
        assert not math.isinf(val), "Exergía colapsada: Explosión asintótica (Inf) detectada."


def test_ssm_linear_time_invariant() -> None:
    """Falsación empírica de la cota O(N). El crecimiento debe ser estrictamente lineal, no cuadrático."""
    model = StateSpaceModel(state_dim=8, input_dim=2)

    seq_1000 = [[0.5, -0.5] for _ in range(1000)]
    seq_2000 = [[0.5, -0.5] for _ in range(2000)]

    start_t1 = time.perf_counter()
    model.forward(seq_1000)
    t1 = time.perf_counter() - start_t1

    start_t2 = time.perf_counter()
    model.forward(seq_2000)
    t2 = time.perf_counter() - start_t2

    # 2000 tokens shouldn't take more than ~2.5x the time of 1000 tokens (linear scaling with margin)
    ratio = t2 / max(t1, 1e-9)
    assert ratio < 3.0, (
        f"Violación de Invariante O(N): Ratio de crecimiento termodinámico {ratio:.2f} excede la cota teórica."
    )
