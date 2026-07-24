# [C5-REAL] 896-Primitive Space Algebra Verification

from dataclasses import dataclass
from typing import Final, Set

TOTAL_PRIMITIVES: Final[int] = 896
D_MAX: Final[int] = 3
F_MAX: Final[int] = 7
A_MAX: Final[int] = 6
M_MAX: Final[int] = 3


@dataclass(frozen=True)
class TensorCoordinate:
    domain: int
    family: int
    action: int
    modifier: int

    def validate_bounds(self) -> None:
        """Enforces strictly the boundaries of the tensor space."""
        if not (0 <= self.domain <= D_MAX):
            raise ValueError(f"Domain out of bounds: {self.domain}")
        if not (0 <= self.family <= F_MAX):
            raise ValueError(f"Family out of bounds: {self.family}")
        if not (0 <= self.action <= A_MAX):
            raise ValueError(f"Action out of bounds: {self.action}")
        if not (0 <= self.modifier <= M_MAX):
            raise ValueError(f"Modifier out of bounds: {self.modifier}")


def map_coordinates(index: int) -> TensorCoordinate:
    """Projects a scalar index into the 4D Tensor space."""
    if not (0 <= index < TOTAL_PRIMITIVES):
        raise ValueError(f"Index out of bounds: {index}")

    d: int = index // 224
    rem: int = index % 224
    f: int = rem // 28
    rem = rem % 28
    a: int = rem // 4
    m: int = rem % 4
    return TensorCoordinate(domain=d, family=f, action=a, modifier=m)


def map_index(coord: TensorCoordinate) -> int:
    """Collapses a 4D Tensor coordinate into a scalar index."""
    coord.validate_bounds()
    return (coord.domain * 224) + (coord.family * 28) + (coord.action * 4) + coord.modifier


def verify_bijectivity() -> None:
    """
    Executes a brute-force verification of the bijective mapping.
    Fails fast (SIGKILL) on any structural violation (INV_Ω26).
    """
    seen_indices: Set[int] = set()
    seen_coords: Set[TensorCoordinate] = set()

    for idx in range(TOTAL_PRIMITIVES):
        try:
            coord: TensorCoordinate = map_coordinates(idx)
            reconstructed_idx: int = map_index(coord)

            if reconstructed_idx != idx:
                raise ValueError(f"Non-bijective mapping at index {idx}: got {reconstructed_idx}")

            if coord in seen_coords:
                raise ValueError(f"Collision detected at coordinate {coord} for index {idx}")

            seen_indices.add(idx)
            seen_coords.add(coord)
        except ValueError as e:
            print(f"[-] FATAL: Invariant violated during verification: {e}")
            raise RuntimeError(f"FAIL-FAST: {e}")

    if len(seen_indices) != TOTAL_PRIMITIVES or len(seen_coords) != TOTAL_PRIMITIVES:
        print("[-] FATAL: Topological fracture. Missing mappings.")
        raise RuntimeError("FAIL-FAST: Topological fracture. Missing mappings.")

    print("[+] C5-REAL Verification SUCCESS: 896-Primitive algebra is strictly bijective.")
    print(f"    - Invariants mapped: {len(seen_coords)}")


if __name__ == "__main__":
    verify_bijectivity()
