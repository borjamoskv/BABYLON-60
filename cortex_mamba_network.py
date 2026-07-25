import numpy as np
import numpy.typing as npt

from cortex_mamba_block import MambaBlock


class MambaNetwork:
    def __init__(self, vocab_size: int, d_model: int, d_state: int, n_layers: int) -> None:
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.d_state = d_state
        self.n_layers = n_layers
        self.embedding: npt.NDArray[np.float64] = np.full((vocab_size, d_model), 0.01, dtype=np.float64)
        self.layers: list[MambaBlock] = [MambaBlock(d_model=d_model, d_state=d_state) for _ in range(n_layers)]
        self.lm_head: npt.NDArray[np.float64] = np.full((vocab_size, d_model), 0.01, dtype=np.float64)

    def forward(self, token_ids: npt.NDArray[np.int_]) -> npt.NDArray[np.float64]:
        hidden_states = self.embedding[token_ids]

        for layer in self.layers:
            hidden_states = layer.forward(hidden_states)

        logits_seq = hidden_states @ self.lm_head.T
        return logits_seq
