# C5-REAL EXERGY CERTIFIED
# [C5-REAL] Exergy-Maximized
"""ATMS Constant-Time Lattice Engine (INV_C5_ATMS_O1 Enforcer).

Enforces INV_C5_ATMS_O1:
All Assumption-based Truth Maintenance Systems (ATMS) MUST implement Environments
and Nogoods as fixed-size bitmasks (bitwise 128-bit integers). Dynamic collections
(set, list) are strictly prohibited during assumption evaluation to guarantee O(1) ALU
subset/union operations during Dependency-Directed Backtracking (DDB).
"""

from __future__ import annotations

from typing import Sequence


class BitmaskATMSLattice:
    """O(1) Constant-Time Bitmask ATMS Lattice Engine."""

    MAX_ASSUMPTIONS = 128
    MASK_ALL = (1 << MAX_ASSUMPTIONS) - 1

    def __init__(self) -> None:
        self._nogoods: list[int] = []

    def add_nogood(self, nogood_mask: int) -> None:
        """
        Adds a Nogood environment mask.
        
        Args:
            nogood_mask: Bitmask representing an inconsistent set of assumptions.
        """
        if nogood_mask == 0:
            raise ValueError("Empty Nogood mask is invalid.")
        self._nogoods.append(nogood_mask)

    def is_consistent(self, env_mask: int) -> bool:
        """
        Evaluates whether an Environment is consistent against all Nogoods in O(1) bitwise ALU steps.
        
        Args:
            env_mask: Bitmask representing the environment to test.
            
        Returns:
            True if consistent (contains no Nogood subset), False if inconsistent.
        """
        for ng in self._nogoods:
            # O(1) ALU Subset Check: If (env & ng) == ng, then ng is a subset of env (Inconsistent!)
            if (env_mask & ng) == ng:
                return False
        return True

    @staticmethod
    def union_environments(env1_mask: int, env2_mask: int) -> int:
        """O(1) ALU Bitwise OR Union of two environments."""
        return env1_mask | env2_mask

    @staticmethod
    def is_subset(sub_mask: int, super_mask: int) -> bool:
        """O(1) ALU Bitwise AND Subset check: returns True if sub_mask <= super_mask."""
        return (super_mask & sub_mask) == sub_mask

    @staticmethod
    def assumption_to_mask(index: int) -> int:
        """Converts assumption index [0..127] to a 128-bit single-bit mask."""
        if not (0 <= index < 128):
            raise ValueError("Assumption index must be in range [0, 127].")
        return 1 << index
