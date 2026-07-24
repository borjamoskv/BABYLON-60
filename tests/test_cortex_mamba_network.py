# C5-REAL

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_mamba_network import MambaNetwork


def test_mamba_network_forward() -> None:
    """Verifica que el stack completo Mamba emite logits válidos sin entropía dimensional."""
    vocab_size = 50
    d_model = 8
    d_state = 16
    n_layers = 2
    seq_len = 10

    model = MambaNetwork(vocab_size=vocab_size, d_model=d_model, d_state=d_state, n_layers=n_layers)

    token_ids = [5, 12, 49, 0, 1, 8, 33, 2, 9, 10]

    logits = model.forward(token_ids)

    assert len(logits) == seq_len, "Pérdida de invariancia de longitud en el Stack."
    assert len(logits[0]) == vocab_size, "Colapso del LM Head. Dimensionalidad de vocabulario fallida."


def test_mamba_network_stack_depth() -> None:
    """Aserción sobre el ruteo interno: La profundidad n_layers se respeta físicamente."""
    model = MambaNetwork(vocab_size=10, d_model=4, d_state=8, n_layers=3)
    assert len(model.layers) == 3, "Violación topológica del Stack."
