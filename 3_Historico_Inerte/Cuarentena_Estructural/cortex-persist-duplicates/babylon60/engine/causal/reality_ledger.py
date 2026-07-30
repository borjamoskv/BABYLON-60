# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass, field
from decimal import Decimal

logger = logging.getLogger(__name__)


@dataclass
class BeliefNode:
    """A node in the Belief Physics DAG."""

    id: str
    exergy: Decimal
    is_diamond: bool
    is_invalidated: bool = False
    parents: set[str] = field(default_factory=set)
    children: set[str] = field(default_factory=set)


class RealityLedger:
    """
    Belief Physics DAG (Issue #479 / Axiom Ω11).
    Evaluates topological integrity of causal statements in the Reality Ledger.
    """

    def __init__(self) -> None:
        self.nodes: dict[str, BeliefNode] = {}

    def add_belief(
        self, belief_id: str, exergy: Decimal, is_diamond: bool, parent_ids: list[str] | None = None
    ) -> None:
        """Add a belief to the DAG."""
        parents = set(parent_ids) if parent_ids else set()

        # Verify parents exist to maintain DAG integrity
        for p in parents:
            if p not in self.nodes:
                raise ValueError(f"Parent {p} does not exist in Reality Ledger.")

        if belief_id in self.nodes:
            logger.warning("[RealityLedger] Belief %s already exists, overwriting.", belief_id)

        node = BeliefNode(id=belief_id, exergy=exergy, is_diamond=is_diamond, parents=parents)
        self.nodes[belief_id] = node

        for p in parents:
            self.nodes[p].children.add(belief_id)

    def topological_sort(self) -> list[str]:
        """Return a topological sort of the belief DAG."""
        in_degree = {n: len(self.nodes[n].parents) for n in self.nodes}
        queue = deque(n for n in self.nodes if in_degree[n] == 0)
        sorted_nodes = []

        while queue:
            current = queue.popleft()
            sorted_nodes.append(current)

            for child in self.nodes[current].children:
                in_degree[child] -= 1
                if in_degree[child] == 0:
                    queue.append(child)

        if len(sorted_nodes) != len(self.nodes):
            raise ValueError("Cycle detected in Belief Physics DAG. Thermodynamic collapse.")

        return sorted_nodes

    def calculate_cumulative_exergy(self) -> dict[str, Decimal]:
        """
        Calculate cumulative exergy for each node based on the DAG structure.
        Children inherit a fraction (e.g. 0.9) of parent's cumulative exergy.
        """
        sorted_nodes = self.topological_sort()
        cumulative: dict[str, Decimal] = {}
        decay_factor = Decimal("0.9")

        for node_id in sorted_nodes:
            node = self.nodes[node_id]
            if node.is_invalidated:
                cumulative[node_id] = Decimal("0.0")
                continue

            base_exergy = node.exergy
            if node.is_diamond:
                base_exergy *= Decimal("1.5")  # Diamond multiplier

            parent_contrib = Decimal("0.0")
            if node.parents:
                parent_contrib = max(cumulative[p] for p in node.parents) * decay_factor

            cumulative[node_id] = base_exergy + parent_contrib

        return cumulative

    def invalidate_belief(self, belief_id: str) -> list[str]:
        """
        Invalidation flow (Axiom Ω11): Cascades invalidation through the DAG.
        When a belief is contradicted or proven false, it and all its causal
        descendants suffer thermodynamic collapse (exergy set to 0 and marked).
        Returns the list of affected node IDs.
        """
        if belief_id not in self.nodes:
            logger.warning("[RealityLedger] Cannot invalidate unknown belief: %s", belief_id)
            return []

        invalidated = []
        queue = deque([belief_id])

        while queue:
            current_id = queue.popleft()
            if current_id not in invalidated:
                invalidated.append(current_id)
                node = self.nodes[current_id]
                node.exergy = Decimal("0.0")
                node.is_invalidated = True

                # Cascade to children
                for child_id in node.children:
                    queue.append(child_id)

        logger.info(
            "[RealityLedger] Invalidated %d beliefs in causal chain starting at %s",
            len(invalidated),
            belief_id,
        )
        return invalidated

    def verifier_pass(self) -> dict[str, bool]:
        """
        Verifier pass: Audits the entire Reality Ledger for thermodynamic consistency.
        A node is valid if it is part of a cycle-free DAG and its cumulative exergy
        is computable without errors.
        Returns a mapping of belief_id to a boolean (True if structurally sound).
        """
        results = {node_id: True for node_id in self.nodes}

        # Step 1: Detect cycles
        try:
            self.topological_sort()
        except ValueError:
            # If cycle detected, mark all nodes involved or just fail the ledger
            logger.error(
                "[RealityLedger] Cycle detected during verifier pass. Entire ledger is unstable."
            )
            return {node_id: False for node_id in self.nodes}

        # Step 2: Validate exergy constraints
        try:
            cumulative = self.calculate_cumulative_exergy()
            for node_id, ex_val in cumulative.items():
                if ex_val < 0:
                    logger.warning(
                        "[RealityLedger] Node %s has negative cumulative exergy.", node_id
                    )
                    results[node_id] = False

                # Check dead branches (exergy == 0 but claims to be diamond)
                node = self.nodes[node_id]
                if node.exergy == 0 and node.is_diamond:
                    logger.warning(
                        "[RealityLedger] Node %s is diamond but collapsed (0 exergy).", node_id
                    )
                    results[node_id] = False
        except Exception as e:  # noqa: BLE001
            logger.error("[RealityLedger] Verifier pass failed during exergy calculation: %s", e)
            for node_id in self.nodes:
                results[node_id] = False

        return results
