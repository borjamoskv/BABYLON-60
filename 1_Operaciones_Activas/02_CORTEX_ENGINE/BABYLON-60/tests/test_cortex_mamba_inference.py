# C5-REAL EXERGY CERTIFIED
# C5-REAL
# MOSKV-1 APEX SINGULARITY
# FALSACIÓN EMPÍRICA: AUTOREGRESSIVE LOOP

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_mamba_network import MambaNetwork
from cortex_mamba_inference import MambaGenerator, softmax


def test_softmax_invariants() -> None:
    """Verifica que la distribución de probabilidad sume 1 (Invariante Físico)."""
    logits = [2.0, 1.0, 0.1, -1.0, 5.0]
    probs = softmax(logits, temperature=1.0)
    assert abs(sum(probs) - 1.0) < 1e-6, "Pérdida de energía. Las probabilidades no suman 1."


def test_autoregressive_generation() -> None:
    """Verifica la emisión autoregresiva de N tokens cinéticos."""
    vocab_size = 20
    d_model = 4
    d_state = 8
    n_layers = 1

    network = MambaNetwork(vocab_size=vocab_size, d_model=d_model, d_state=d_state, n_layers=n_layers)
    generator = MambaGenerator(network)

    prompt = [1, 5, 2]
    max_new = 10

    output = generator.generate(prompt, max_new_tokens=max_new, temperature=0.8, k=3)

    assert len(output) == len(prompt) + max_new, "El colapso autoregresivo falló en longitud."
    for token in output:
        assert 0 <= token < vocab_size, "Token generado fuera del horizonte de vocabulario (Alucinación estructural)."
