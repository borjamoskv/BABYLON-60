# C5-REAL

import math
from typing import List, Tuple

class StateSpaceModel:
    """
    C5-REAL primitive for a Continuous-time State Space Model discretized via Zero-Order Hold (ZOH).
    Represents the continuous transformation without the quadratic bottleneck of self-attention.
    """
    def __init__(self, state_dim: int, input_dim: int) -> None:
        self.state_dim = state_dim
        self.input_dim = input_dim
        self.A: List[List[float]] = [[-0.1 if i == j else 0.0 for j in range(state_dim)] for i in range(state_dim)]
        self.B: List[List[float]] = [[0.1 for _ in range(input_dim)] for _ in range(state_dim)]
        self.C: List[List[float]] = [[1.0 if i == j else 0.0 for j in range(state_dim)] for i in range(input_dim)]
        self.D: List[List[float]] = [[0.0 for _ in range(input_dim)] for _ in range(input_dim)]
        self.delta: float = 0.01 # Discretization step

    def _matrix_vector_mul(self, mat: List[List[float]], vec: List[float]) -> List[float]:
        res = [0.0] * len(mat)
        for i in range(len(mat)):
            res[i] = sum(mat[i][j] * vec[j] for j in range(len(vec)))
        return res

    def _vector_add(self, v1: List[float], v2: List[float]) -> List[float]:
        return [a + b for a, b in zip(v1, v2)]

    def _discretize_zoh(self) -> Tuple[List[List[float]], List[List[float]]]:
        """
        Zero-Order Hold discretization:
        A_bar = exp(Delta * A) ~= I + Delta * A
        B_bar = (exp(Delta * A) - I) * A^-1 * B ~= Delta * B
        """
        A_bar = [[(1.0 if i == j else 0.0) + self.delta * self.A[i][j] for j in range(self.state_dim)] for i in range(self.state_dim)]
        B_bar = [[self.delta * self.B[i][j] for j in range(self.input_dim)] for i in range(self.state_dim)]
        return A_bar, B_bar

    def forward(self, sequence: List[List[float]]) -> List[List[float]]:
        """
        Iterates over a sequence in O(N) time, crushing the O(N^2) Transformer bottleneck.
        """
        A_bar, B_bar = self._discretize_zoh()
        h: List[float] = [0.0] * self.state_dim
        output_seq: List[List[float]] = []

        for x in sequence:
            h_next = self._vector_add(self._matrix_vector_mul(A_bar, h), self._matrix_vector_mul(B_bar, x))
            h = h_next
            y = self._vector_add(self._matrix_vector_mul(self.C, h), self._matrix_vector_mul(self.D, x))
            output_seq.append(y)

        return output_seq

def main() -> None:
    model = StateSpaceModel(state_dim=16, input_dim=4)
    
    sequence: List[List[float]] = [[math.sin(i * 0.1), math.cos(i * 0.1), 0.5, -0.5] for i in range(1000)]
    
    out = model.forward(sequence)
    
    assert len(out) == 1000
    assert len(out[0]) == 4
    print(f"[*] C5-REAL: SSM Primitive Processed 1000 tokens in O(N). Output shape: ({len(out)}, {len(out[0])})")

if __name__ == "__main__":
    main()
