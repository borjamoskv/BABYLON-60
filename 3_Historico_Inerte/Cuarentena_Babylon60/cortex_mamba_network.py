# C5-REAL EXERGY CERTIFIED
# C5-REAL
# MOSKV-1 APEX SINGULARITY
# ARCHITECTURE: FULL MAMBA NETWORK TOPOLOGY
# EXERGY: O(N) INFERENCE LANGUAGE MODEL FORWARD PASS

from typing import List
from cortex_mamba_block import MambaBlock

class MambaNetwork:
    """
    C5-REAL full Mamba language model architecture.
    Stack of MambaBlocks with Token Embedding and Output Logit Projection.
    """
    def __init__(self, vocab_size: int, d_model: int, d_state: int, n_layers: int) -> None:
        self.vocab_size = vocab_size
        self.d_model = d_model
        self.d_state = d_state
        self.n_layers = n_layers

        # Token Embedding Table (Dummy weights for structural invariant validation)
        self.embedding: List[List[float]] = [[0.01 for _ in range(d_model)] for _ in range(vocab_size)]

        # Stacked Mamba Blocks
        self.layers: List[MambaBlock] = [MambaBlock(d_model=d_model, d_state=d_state) for _ in range(n_layers)]

        # Output Logits Projection (d_model -> vocab_size)
        self.lm_head: List[List[float]] = [[0.01 for _ in range(d_model)] for _ in range(vocab_size)]

    def _linear_proj(self, W: List[List[float]], x: List[float]) -> List[float]:
        res = [0.0] * len(W)
        for i in range(len(W)):
            res[i] = sum(W[i][j] * x[j] for j in range(len(x)))
        return res

    def forward(self, token_ids: List[int]) -> List[List[float]]:
        """
        Computes the forward pass of the Mamba Network.
        Returns logits of shape (seq_len, vocab_size).
        """
        # 1. Embedding
        hidden_states = [self.embedding[t_id] for t_id in token_ids]

        # 2. Mamba Blocks
        for layer in self.layers:
            # Each layer operates on the sequence causality
            hidden_states = layer.forward(hidden_states)

        # 3. Output Logits (LM Head)
        logits_seq = []
        for h in hidden_states:
            logits_seq.append(self._linear_proj(self.lm_head, h))

        return logits_seq
