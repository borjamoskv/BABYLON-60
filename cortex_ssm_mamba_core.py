import math
from typing import Any

import numpy as np
import numpy.typing as npt


class StateSpaceModel:

    def __init__(self, state_dim: int, input_dim: int) -> None:
        self.state_dim = state_dim
        self.input_dim = input_dim
        self.A: npt.NDArray[np.float64] = -0.1 * np.eye(state_dim, dtype=np.float64)
        self.B: npt.NDArray[np.float64] = np.full((state_dim, input_dim), 0.1, dtype=np.float64)
        self.C: npt.NDArray[np.float64] = np.eye(input_dim, state_dim, dtype=np.float64)
        self.D: npt.NDArray[np.float64] = np.zeros((input_dim, input_dim), dtype=np.float64)
        self.delta: float = 0.01

    def _discretize_zoh(self) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
        A_bar = np.eye(self.state_dim, dtype=np.float64) + self.delta * self.A
        B_bar = self.delta * self.B
        return A_bar, B_bar

    def forward(self, sequence: npt.NDArray[np.float64] | list[Any]) -> npt.NDArray[np.float64]:
        A_bar, B_bar = self._discretize_zoh()
        h: npt.NDArray[np.float64] = np.zeros(self.state_dim, dtype=np.float64)
        
        seq_arr: npt.NDArray[np.float64] = np.asarray(sequence, dtype=np.float64)
        seq_len = seq_arr.shape[0]
        output_seq: npt.NDArray[np.float64] = np.zeros((seq_len, self.input_dim), dtype=np.float64)
        
        for t in range(seq_len):
            h = A_bar @ h + B_bar @ seq_arr[t]
            output_seq[t] = self.C @ h + self.D @ seq_arr[t]
            
        return output_seq

def main() -> None:
    model = StateSpaceModel(state_dim=16, input_dim=4)
    sequence: npt.NDArray[np.float64] = np.array([[math.sin(i * 0.1), math.cos(i * 0.1), 0.5, -0.5] for i in range(1000)], dtype=np.float64)
    out = model.forward(sequence)
    assert out.shape[0] == 1000
    assert out.shape[1] == 4
    print(f'[*] C5-REAL: SSM Primitive Processed 1000 tokens in O(N). Output shape: {out.shape}')

if __name__ == '__main__':
    main()
