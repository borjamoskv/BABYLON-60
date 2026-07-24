# C5-REAL

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from cortex_bpe_tokenizer import BPETokenizer


def test_bpe_compression() -> None:
    """Verifica que el BPE extrae exergía comprimiendo pares redundantes."""
    text = "abracadabra"
    tokenizer = BPETokenizer()

    raw_tokens = list(text)
    assert len(raw_tokens) == 11

    tokenizer.train(text, num_merges=2)

    encoded = tokenizer.encode(text)

    assert len(encoded) < 11, "Colapso BPE fallido: Sin reducción de entropía."


def test_bpe_isomorphism() -> None:
    """Aserción de isomorfismo bidireccional (Encode -> Decode = Identity)."""
    text = "Moskv-1 Singularity: Exergia Cinética."
    tokenizer = BPETokenizer()

    tokenizer.train(text, num_merges=10)

    encoded = tokenizer.encode(text)
    decoded = tokenizer.decode(encoded)

    assert text == decoded, "Violación Isomórfica: Pérdida de información en el proceso de codificación/decodificación."
