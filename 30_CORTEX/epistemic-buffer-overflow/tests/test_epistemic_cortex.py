# [C5-REAL] Epistemic Cortex Test Suite
# Author: borjamoskv
# Estilo: Sin comillas simples (exclusivo comillas dobles)

from __future__ import annotations
import os
import shutil
import tempfile
import pytest
from epistemic_cortex.entangled_ledger import EntangledLedger
from epistemic_cortex.federated_search import FederatedSearchEngine
from epistemic_cortex.mejoralo_16d import Mejoralo16DScanner
from epistemic_cortex.diversity_consensus import DiversityConsensusManager
from epistemic_cortex.actor_storage import DatabaseActor
from epistemic_cortex.apoptosis_engine import ApoptosisOntologicaEngine

class TestEpistemicCortex:
    @pytest.fixture(autouse=True)
    def setup_and_teardown(self) -> None:
        self.tmp_dir = tempfile.mkdtemp()
        yield
        shutil.rmtree(self.tmp_dir)

    def test_entangled_ledger(self) -> None:
        # Arrange
        anchors: list[str] = []
        def mock_anchor(root_hash: str) -> None:
            anchors.append(root_hash)
            
        ledger = EntangledLedger(anchor_callback=mock_anchor)
        ledger.update_peer_state("agent_b", "hash_alpha_99")

        # Act & Assert
        # Inject 10 transactions to trigger anchoring
        for i in range(10):
            ledger.append_fact(i, "INSERT", f"Fact content {i}")

        assert len(ledger.chain) == 10
        assert len(anchors) == 1
        assert ledger.verify_chain_integrity() is True

    def test_federated_search(self) -> None:
        # Arrange
        engine = FederatedSearchEngine(self.tmp_dir)

        # Act
        fact_id_1 = engine.store_fact("tenant_a", "Authentic BFT cryptographic consensus proof")
        fact_id_2 = engine.store_fact("tenant_b", "Decentralized storage with zero lock contention")

        # Assert
        # Search coordinates across database shards using Central Index Router
        results = engine.federated_search("cryptographic consensus")
        assert len(results) >= 1
        assert results[0].tenant_id == "tenant_a"
        assert results[0].fact_id == fact_id_1

    def test_mejoralo_16d_scanner(self) -> None:
        # Arrange
        scanner = Mejoralo16DScanner("epistemic-cortex")
        source = (
            "def handle_state():\n"
            "    global system_state\n"
            "    system_state = 100\n"
            "    if not system_state:\n"
            "        return\n"
        )
        dependencies = ["pytest", "sqlite3", "cryptography", "qdrant-client", "fastapi", "numpy", "pandas", "scipy", "requests"]

        # Act
        result = scanner.scan_code(source, dependencies=dependencies)

        # Assert
        dimensions = {d.name: d for d in result.dimensions}
        assert "Dependency Entropy" in dimensions
        assert "State Friction" in dimensions
        assert "Causal Isomorphism" in dimensions
        
        # High dependency count should lower dependency score
        assert dimensions["Dependency Entropy"].score <= 50
        # Found global state should decrease State Friction
        assert dimensions["State Friction"].score < 100

    def test_diversity_consensus(self) -> None:
        # Arrange
        manager = DiversityConsensusManager()
        # Register 3 agents sharing the same destilled weights
        manager.register_agent("agent_1", 1.0, "claude", "anthropic-moe")
        manager.register_agent("agent_2", 1.0, "claude", "anthropic-moe")
        manager.register_agent("agent_3", 1.0, "claude", "anthropic-moe")
        # Register 1 independent agent with a different model family
        manager.register_agent("agent_4", 1.0, "qwen", "alibaba-dense")

        # Act
        # Clustered nodes vote +1, independent node votes -1
        votes = {
            "agent_1": 1,
            "agent_2": 1,
            "agent_3": 1,
            "agent_4": -1
        }
        consensus_reached, score, weights = manager.compute_consensus(votes)

        # Assert
        # Diversity coefficient should reduce weights of the destilled cluster agent nodes
        assert weights["agent_4"] > weights["agent_1"]

    def test_actor_storage(self) -> None:
        # Arrange
        db_path = os.path.join(self.tmp_dir, "shared.db")
        actor = DatabaseActor(db_path, batch_interval_ms=10)
        actor.start()

        # Act
        fact_id_1 = actor.request_write("tenant_1", "Actor queue data 1")
        fact_id_2 = actor.request_write("tenant_2", "Actor queue data 2")
        actor.shutdown()

        # Assert
        assert fact_id_1 > 0
        assert fact_id_2 > 0

    def test_apoptosis_engine(self) -> None:
        # Arrange
        engine = ApoptosisOntologicaEngine()
        source = (
            "def dead_function():\n"
            "    pass\n"
            "def active_function():\n"
            "    return True\n"
        )

        # Act
        purged = engine.run_apoptosis(source)

        # Assert
        assert "dead_function" not in purged
        assert "active_function" in purged
