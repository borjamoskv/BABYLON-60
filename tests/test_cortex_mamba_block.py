import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_mamba_block import MambaBlock


def test_mamba_block_forward() -> None:
    d_model = 8
    d_state = 16
    seq_len = 50
    block = MambaBlock(d_model=d_model, d_state=d_state)
    sequence = [[0.5] * d_model for _ in range(seq_len)]
    out = block.forward(sequence)
    assert len(out) == seq_len, "El colapso de longitud de secuencia falló en el Bloque Mamba."
    assert len(out[0]) == d_model, "La proyección de salida divirgió del d_model."


def test_mamba_block_causality() -> None:
    d_model = 4
    d_state = 8
    seq_len = 20
    block = MambaBlock(d_model=d_model, d_state=d_state)
    seq_a = [[0.1] * d_model for _ in range(seq_len)]
    seq_b = [[0.1] * d_model for _ in range(seq_len)]
    seq_b[10] = [0.9] * d_model
    out_a = block.forward(seq_a)
    out_b = block.forward(seq_b)
    for t in range(10):
        for i in range(d_model):
            assert abs(out_a[t][i] - out_b[t][i]) < 1e-09, "Violación Causal: Filtro de información temporal roto."
    diverged = False
    for i in range(d_model):
        if abs(out_a[10][i] - out_b[10][i]) > 1e-09:
            diverged = True
            break
    assert diverged, "Entropía inyectada no registrada en el estado futuro."
