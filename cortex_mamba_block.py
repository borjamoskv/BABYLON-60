import numpy as np
import numpy.typing as npt

from cortex_ssm_mamba_core import StateSpaceModel


def silu(x: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
    return x / (1.0 + np.exp(-x))

class MambaBlock:

    def __init__(self, d_model: int, d_state: int, conv_kernel_size: int=4) -> None:
        self.d_model = d_model
        self.d_inner = d_model * 2
        self.d_state = d_state
        self.conv_kernel_size = conv_kernel_size
        self.ssm = StateSpaceModel(state_dim=d_state, input_dim=self.d_inner)
        
        self.W_in: npt.NDArray[np.float64] = np.full((self.d_inner, d_model), 0.1, dtype=np.float64)
        self.W_x: npt.NDArray[np.float64] = np.full((self.d_inner, d_model), 0.1, dtype=np.float64)
        self.W_out: npt.NDArray[np.float64] = np.full((d_model, self.d_inner), 0.1, dtype=np.float64)
        self.conv_weights: npt.NDArray[np.float64] = np.full((self.d_inner, conv_kernel_size), 0.25, dtype=np.float64)

    def _causal_conv1d(self, sequence: npt.NDArray[np.float64]) -> npt.NDArray[np.float64]:
        seq_len = sequence.shape[0]
        out_seq = np.zeros((seq_len, self.d_inner), dtype=np.float64)
        
        for d in range(self.d_inner):
            kernel = self.conv_weights[d]
            out_seq[:, d] = np.convolve(sequence[:, d], kernel, mode='full')[:seq_len]
            
        return out_seq

    def forward(self, sequence: npt.NDArray[np.float64] | list[list[float]]) -> npt.NDArray[np.float64]:
        seq_arr: npt.NDArray[np.float64] = np.asarray(sequence, dtype=np.float64)
        seq_len = seq_arr.shape[0]
        
        x_proj = seq_arr @ self.W_x.T
        z_proj = seq_arr @ self.W_in.T
        
        x_conv = self._causal_conv1d(x_proj)
        x_act = silu(x_conv)
        
        ssm_out = self.ssm.forward(x_act)
        
        gate = silu(z_proj)
        y = ssm_out * gate
        
        output_seq = y @ self.W_out.T
        return output_seq
