# C5-REAL

import math
from typing import List
from cortex_ssm_mamba_core import StateSpaceModel

def silu(x: float) -> float:
    """SiLU (Swish) Activation: x * sigmoid(x)"""
    return x / (1.0 + math.exp(-x))

class MambaBlock:
    """
    C5-REAL primitive for a full Mamba Block.
    Includes Linear Projections, Causal Convolution (Depthwise 1D), SiLU gating, and the SSM Core.
    """
    def __init__(self, d_model: int, d_state: int, conv_kernel_size: int = 4) -> None:
        self.d_model = d_model
        self.d_inner = d_model * 2  # Standard expansion factor
        self.d_state = d_state
        self.conv_kernel_size = conv_kernel_size
        
        self.ssm = StateSpaceModel(state_dim=d_state, input_dim=self.d_inner)
        
        self.W_in: List[List[float]] = [[0.1 for _ in range(d_model)] for _ in range(self.d_inner)]
        self.W_x: List[List[float]] = [[0.1 for _ in range(d_model)] for _ in range(self.d_inner)]
        self.W_out: List[List[float]] = [[0.1 for _ in range(self.d_inner)] for _ in range(d_model)]
        
        self.conv_weights: List[List[float]] = [[0.25 for _ in range(conv_kernel_size)] for _ in range(self.d_inner)]

    def _linear_proj(self, W: List[List[float]], x: List[float]) -> List[float]:
        res = [0.0] * len(W)
        for i in range(len(W)):
            res[i] = sum(W[i][j] * x[j] for j in range(len(x)))
        return res

    def _causal_conv1d(self, sequence: List[List[float]]) -> List[List[float]]:
        seq_len = len(sequence)
        out_seq = []
        for t in range(seq_len):
            out_t = [0.0] * self.d_inner
            for d in range(self.d_inner):
                conv_sum = 0.0
                for k in range(self.conv_kernel_size):
                    t_idx = t - k
                    if t_idx >= 0:
                        conv_sum += sequence[t_idx][d] * self.conv_weights[d][k]
                out_t[d] = conv_sum
            out_seq.append(out_t)
        return out_seq

    def forward(self, sequence: List[List[float]]) -> List[List[float]]:
        """
        Forward pass of the Mamba Block over a sequence of tokens.
        x -> Proj(x), Proj(z)
        x' = Conv1d(Proj(x)) -> SiLU -> SSM
        y = x' * SiLU(Proj(z))
        out = Proj(y)
        """
        seq_len = len(sequence)
        
        x_proj = [self._linear_proj(self.W_x, seq_t) for seq_t in sequence]
        z_proj = [self._linear_proj(self.W_in, seq_t) for seq_t in sequence]
        
        x_conv = self._causal_conv1d(x_proj)
        
        x_act = [[silu(val) for val in step] for step in x_conv]
        
        ssm_out = self.ssm.forward(x_act)
        
        output_seq = []
        for t in range(seq_len):
            gate_t = [silu(val) for val in z_proj[t]]
            y_t = [ssm_out[t][i] * gate_t[i] for i in range(self.d_inner)]
            final_out_t = self._linear_proj(self.W_out, y_t)
            output_seq.append(final_out_t)
            
        return output_seq
