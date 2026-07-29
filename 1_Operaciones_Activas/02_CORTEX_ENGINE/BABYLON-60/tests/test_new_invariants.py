# C5-REAL EXERGY CERTIFIED
import pytest
from babylon60.bft.logop_consensus import LogOPConsensusEngine
from babylon60.core.atms_bitmask import BitmaskATMSLattice
from babylon60.core.abft_ipc import Iceoryx2NodeBuilderEnforcer


class TestINV_BFT_LOGOP:
    def test_absolute_veto_collapses_to_zero(self):
        """INV_BFT_LOGOP: If any expert assigns P=0.0, aggregate MUST collapse to 0.0 (Absolute Veto)."""
        # 99 Byzantine agents vote 0.99, 1 honest agent votes 0.0 (Falsification)
        probs = [0.99] * 99 + [0.0]
        result = LogOPConsensusEngine.aggregate(probs)
        assert result == 0.0, "Absolute Veto P=0.0 failed to collapse LogOP pool to zero!"

    def test_logop_geometric_mean(self):
        """LogOP calculates weighted geometric mean correctly."""
        probs = [0.5, 0.5]
        result = LogOPConsensusEngine.aggregate(probs)
        assert pytest.approx(result, 0.001) == 0.5


class TestINV_C5_ATMS_O1:
    def test_bitmask_subset_and_union(self):
        """INV_C5_ATMS_O1: O(1) bitwise subset and union operations."""
        lattice = BitmaskATMSLattice()
        
        # Assumptions A0, A1, A2
        a0 = BitmaskATMSLattice.assumption_to_mask(0)  # 0b001
        a1 = BitmaskATMSLattice.assumption_to_mask(1)  # 0b010
        a2 = BitmaskATMSLattice.assumption_to_mask(2)  # 0b100

        # Nogood = {A0, A1} = 0b011
        nogood_a0_a1 = BitmaskATMSLattice.union_environments(a0, a1)
        lattice.add_nogood(nogood_a0_a1)

        # Env1 = {A0, A1, A2} = 0b111 (Inconsistent because it contains Nogood 0b011)
        env1 = BitmaskATMSLattice.union_environments(nogood_a0_a1, a2)
        assert not lattice.is_consistent(env1), "Inconsistent environment containing Nogood passed!"

        # Env2 = {A0, A2} = 0b101 (Consistent, doesn't contain A1)
        env2 = BitmaskATMSLattice.union_environments(a0, a2)
        assert lattice.is_consistent(env2), "Consistent environment was incorrectly marked Nogood!"


class TestINV_C5_ABFT_IPC:
    def test_iceoryx2_node_builder_initialization(self):
        """INV_C5_ABFT_IPC: NodeBuilder initialization pattern validation."""
        enforcer = Iceoryx2NodeBuilderEnforcer("abft_consensus_service")
        sig = enforcer.initialize_node_builder()
        assert "NodeBuilder::new().create" in sig
        assert enforcer.is_initialized
