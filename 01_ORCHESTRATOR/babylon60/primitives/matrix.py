#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
matrix.py - Zero-Dependency Linear Algebra & Stochastic Matrix Primitives.

Replaces NumPy/SciPy heavy dependencies for core stochastic matrix transformations,
Markov disintegration kernels, and vector spaces with pure Python C5-REAL invariants.
"""

from array import array
from typing import Dict, List, Tuple, Union


class Vector:
    """Zero-dependency dense vector wrapper based on standard library array."""

    def __init__(self, data: Union[List[float], Tuple[float, ...]]):
        self._data = array("d", data)

    def __len__(self) -> int:
        return len(self._data)

    def __getitem__(self, idx: int) -> float:
        return self._data[idx]

    def __setitem__(self, idx: int, value: float) -> None:
        self._data[idx] = value

    def dot(self, other: "Vector") -> float:
        if len(self) != len(other):
            raise ValueError(f"Vector dimensions mismatch: {len(self)} vs {len(other)}")
        return sum(self._data[i] * other._data[i] for i in range(len(self)))

    def norm_l1(self) -> float:
        return sum(abs(x) for x in self._data)

    def normalize(self) -> "Vector":
        s = self.norm_l1()
        if s == 0:
            return Vector([0.0] * len(self))
        return Vector([x / s for x in self._data])

    def to_list(self) -> List[float]:
        return list(self._data)


class Matrix:
    """Zero-dependency dense 2D matrix wrapper."""

    def __init__(self, rows: int, cols: int, fill: float = 0.0):
        self.rows = rows
        self.cols = cols
        self._data = array("d", [fill] * (rows * cols))

    def __getitem__(self, pos: Tuple[int, int]) -> float:
        r, c = pos
        return self._data[r * self.cols + c]

    def __setitem__(self, pos: Tuple[int, int], val: float) -> None:
        r, c = pos
        self._data[r * self.cols + c] = val

    def row(self, r: int) -> Vector:
        start = r * self.cols
        return Vector(self._data[start : start + self.cols])

    def col(self, c: int) -> Vector:
        return Vector([self._data[r * self.cols + c] for r in range(self.rows)])

    def matmul(self, other: "Matrix") -> "Matrix":
        if self.cols != other.rows:
            raise ValueError(f"Matrix dimensions incompatible: ({self.rows}x{self.cols}) * ({other.rows}x{other.cols})")
        res = Matrix(self.rows, other.cols, 0.0)
        for r in range(self.rows):
            r_vec = self.row(r)
            for c in range(other.cols):
                c_vec = other.col(c)
                res[r, c] = r_vec.dot(c_vec)
        return res


def dict_to_vector(dist: Dict[str, float], keys: List[str]) -> Vector:
    """Converts a probability distribution dict into an ordered Vector."""
    return Vector([dist.get(k, 0.0) for k in keys])


def vector_to_dict(vec: Vector, keys: List[str]) -> Dict[str, float]:
    """Converts a Vector back into a probability distribution dict."""
    return {k: vec[i] for i, k in enumerate(keys) if vec[i] > 1e-12}
