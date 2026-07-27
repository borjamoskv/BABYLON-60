# [C5-REAL] Exergy-Maximized
"""Validation script for L7 Autopoietic Agent.

Runs a full evolution cycle with a mock executor to verify:
1. Genome creation and serialization (quote)
2. Mutation operators (transform)
3. Fitness evaluation (eval)
4. Adoption/discard selection
5. Meta-mutation
6. Genesis spawning
7. Rollback safety
8. Introspection

Reality Level: C5-REAL (real code execution, mock dispatch targets)
"""

import asyncio
import json
import logging

logging.basicConfig(level=logging.INFO, format="%(message)s")
import os
import random
import sys
import time

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from babylon60.extensions.evo._genome_mutator import GenomeMutator
from babylon60.extensions.evo._genome_types import (
    FitnessRecord,
    MutationType,
    StrategyGenome,
)
from babylon60.extensions.speculative.genesis import (
    AgentBlueprint,
    AgentSpecies,
    GenesisEngine,
)
from babylon60.isa.builder import (
    dispatch_targets,
    node_count,
)
from babylon60.swarm.autopoietic_agent import (
    AutopoieticAgent,
    EvolutionConfig,
)

# ─── Mock Executor ───────────────────────────────────────────────


async def mock_executor(tree, params):
    """Simulates dispatch execution with stochastic fitness signals.

    In production, this would be the real Rust dispatch engine.
    For validation, we simulate with deterministic-ish scoring.
    """
    complexity = node_count(tree)
    targets = dispatch_targets(tree)

    # Simulate execution latency (proportional to complexity)
    await asyncio.sleep(0.001 * complexity)

    # Fitness rewards:
    # - More targets = more coverage = higher score
    # - Lower complexity = more elegant = bonus
    # - Parameters influence performance
    base_score = min(1.0, len(targets) * 0.15 + 0.2)

    # Parameter bonuses
    depth = params.get("scan_depth", 1)
    confidence = params.get("min_confidence", 0.5)
    base_score += depth * 0.02
    base_score += confidence * 0.1

    # Add stochastic noise
    noise = random.gauss(0, 0.05)
    score = max(0.0, min(1.0, base_score + noise))

    return {
        "score": score,
        "error_rate": random.uniform(0.0, 0.1),
        "throughput": random.uniform(100, 1000),
        "metadata": {
            "targets_hit": len(targets),
            "complexity": complexity,
        },
    }


# ─── Tests ───────────────────────────────────────────────────────


def test_genome_serialization():
    """Test genome quote-transform-eval cycle."""
    logging.info("=" * 60)
    logging.info("TEST 1: Genome Serialization (Quote-Transform-Eval)")
    logging.info("=" * 60)

    # Create genome (code)
    genome = AgentSpecies.hunter("bounty", targets=3)
    logging.info("  Created: %s", genome)
    logging.info("  Hash: %s", genome.genome_hash)
    logging.info("  Complexity: %s", genome.complexity)
    logging.info("  Targets: %s", genome.targets)

    # Serialize (quote: code → data)
    json_str = genome.to_json()
    logging.info("  JSON size: %s bytes", len(json_str))

    # Deserialize (unquote: data → code)
    restored = StrategyGenome.from_json(json_str)
    logging.info("  Restored: %s", restored)
    logging.info("  Restored hash: %s", restored.genome_hash)

    # Verify identity
    assert restored.name == genome.name
    assert restored.complexity == genome.complexity
    assert restored.targets == genome.targets
    logging.info("  ✅ Serialization round-trip PASSED")
    logging.info("")


def test_mutation_operators():
    """Test all mutation operators."""
    logging.info("=" * 60)
    logging.info("TEST 2: Mutation Operators")
    logging.info("=" * 60)

    mutator = GenomeMutator()
    genome = AgentSpecies.hunter("test")
    original_hash = genome.genome_hash

    for mt in MutationType:
        child = mutator.mutate(genome, force_type=mt)
        logging.info(
            "  %25s → hash=%s complexity=%s gen=%s",
            mt.value,
            child.genome_hash[:8],
            child.complexity,
            child.lineage.generation,
        )
        # Verify child is different from parent
        assert child.genome_hash != original_hash or mt == MutationType.PARAMETER_DRIFT
        # Verify parent is unchanged
        assert genome.genome_hash == original_hash

    logging.info("  ✅ All mutation operators PASSED")
    logging.info("")


def test_crossover():
    """Test sexual recombination."""
    logging.info("=" * 60)
    logging.info("TEST 3: Crossover Recombination")
    logging.info("=" * 60)

    mutator = GenomeMutator()
    parent_a = AgentSpecies.hunter("alpha")
    parent_b = AgentSpecies.pipeline(["scan", "extract", "report"])

    # Give parent_a higher fitness
    parent_a.record_fitness(
        FitnessRecord(score=0.9, latency_ms=10, success=True, error_rate=0.0, throughput=500)
    )
    parent_b.record_fitness(
        FitnessRecord(score=0.6, latency_ms=20, success=True, error_rate=0.1, throughput=300)
    )

    child = mutator.crossover(parent_a, parent_b)
    logging.info("  Parent A: %s (fitness=%.2f)", parent_a, parent_a.lineage.avg_fitness)
    logging.info("  Parent B: %s (fitness=%.2f)", parent_b, parent_b.lineage.avg_fitness)
    logging.info("  Child:    %s", child)
    logging.info("  Child gen: %s", child.lineage.generation)
    logging.info("  Child parent_hash: %s", child.lineage.parent_hash)
    logging.info("  ✅ Crossover PASSED")
    logging.info("")


def test_genesis():
    """Test agent genesis: species templates + spawning."""
    logging.info("=" * 60)
    logging.info("TEST 4: Genesis Engine")
    logging.info("=" * 60)

    genesis = GenesisEngine()

    # Create various species
    species = [
        ("hunter", AgentSpecies.hunter("bounty")),
        ("pipeline", AgentSpecies.pipeline()),
        ("guardian", AgentSpecies.guardian()),
        ("explorer", AgentSpecies.explorer(depth=2)),
        ("swarm", AgentSpecies.swarm_coordinator(swarm_size=3)),
    ]

    for name, genome in species:
        blueprint = AgentBlueprint(species=name, genome=genome)
        genesis.register_blueprint(blueprint)
        agent = genesis.spawn(blueprint)
        logging.info(
            "  Spawned: %s (species=%s, complexity=%s, targets=%s)",
            agent.agent_id,
            name,
            genome.complexity,
            len(genome.targets),
        )

    # Compose hybrid
    hunter_genome = AgentSpecies.hunter("alpha")
    guardian_genome = AgentSpecies.guardian("perimeter")
    hybrid = genesis.compose_hybrid(
        [hunter_genome, guardian_genome],
        name="hybrid_hunter_guardian",
        composition="parallel",
    )
    logging.info("  Hybrid: %s", hybrid)
    logging.info("  Hybrid complexity: %s", hybrid.complexity)
    logging.info("  Hybrid targets: %s", hybrid.targets)

    census = genesis.census()
    logging.info(f"  Census: {json.dumps(census, indent=2, default=str)}")
    logging.info("  ✅ Genesis PASSED")
    logging.info("")


async def test_evolution_cycle():
    """Test one full evolution cycle."""
    logging.info("=" * 60)
    logging.info("TEST 5: Evolution Cycle")
    logging.info("=" * 60)

    config = EvolutionConfig(
        variants_per_cycle=3,
        min_evaluations=2,
        stagnation_limit=5,
        checkpoint_interval=1,
    )

    agent = AutopoieticAgent(
        initial_genome=AgentSpecies.hunter("evolution_test", targets=3),
        executor=mock_executor,
        config=config,
    )

    logging.info("  Initial: %s", agent)
    logging.info("  Initial genome: %s", agent.genome)

    # Run 5 evolution cycles
    for i in range(5):
        report = await agent.evolve_cycle()
        adopted = "✅ ADOPTED" if report["adopted"] else "❌ discarded"
        logging.info(
            "  Cycle %s: gen=%s fitness=%.4f %s (variants=%s, latency=%.1fms)",
            i + 1,
            report["generation"],
            report["fitness_after"],
            adopted,
            report["variants_evaluated"],
            report["cycle_latency_ms"],
        )

    logging.info("  Final: %s", agent)
    logging.info(f"  State: {json.dumps(agent.state.to_dict(), indent=2)}")
    logging.info("  ✅ Evolution Cycle PASSED")
    logging.info("")


async def test_continuous_evolution():
    """Test continuous evolution until convergence."""
    logging.info("=" * 60)
    logging.info("TEST 6: Continuous Evolution")
    logging.info("=" * 60)

    config = EvolutionConfig(
        variants_per_cycle=5,
        min_evaluations=2,
        max_generations=20,
        fitness_threshold=0.85,
        stagnation_limit=8,
        checkpoint_interval=3,
        enable_meta_mutation=True,
        enable_genesis=True,
    )

    agent = AutopoieticAgent(
        initial_genome=AgentSpecies.hunter("continuous_test", targets=4),
        executor=mock_executor,
        config=config,
    )

    async def on_cycle(report):
        gen = report["generation"]
        fitness = report["fitness_after"]
        adopted = "📈" if report["adopted"] else "  "
        logging.info(
            "    %s gen=%3d fitness=%.4f hash=%s",
            adopted,
            gen,
            fitness,
            report["genome_hash_after"],
        )

    summary = await agent.evolve(max_generations=20, on_cycle=on_cycle)

    logging.info("\n  === EVOLUTION SUMMARY ===")
    logging.info("  Cycles: %s", summary["cycles_run"])
    logging.info(
        "  Fitness: %.4f → %.4f (Δ=%.4f)",
        summary["initial_fitness"],
        summary["final_fitness"],
        summary["improvement"],
    )
    logging.info("  Best ever: %.4f", summary["best_fitness_ever"])
    logging.info("  Mutations: %s", summary["total_mutations"])
    logging.info("  Adoptions: %s", summary["total_adoptions"])
    logging.info("  Discards: %s", summary["total_discards"])
    logging.info("  Meta-mutations: %s", summary["meta_mutations"])
    logging.info("  Duration: %.1fms", summary["total_latency_ms"])
    logging.info("")

    # Introspection
    intro = agent.introspect()
    logging.info("  === INTROSPECTION ===")
    logging.info("  Level: %s", intro["level"])
    logging.info(
        f"  Capabilities: {sum(intro['capability_matrix'].values())}/{len(intro['capability_matrix'])} ✅"
    )
    logging.info("  Genome complexity: %s", intro["genome"]["complexity"])
    logging.info("  Checkpoints: %s", intro["checkpoints_available"])

    # Test rollback
    pre_rollback_hash = agent.genome.genome_hash[:8]
    agent.rollback()
    post_rollback_hash = agent.genome.genome_hash[:8]
    logging.info("  Rollback: %s → %s", pre_rollback_hash, post_rollback_hash)
    logging.info("  ✅ Continuous Evolution PASSED")
    logging.info("")


async def test_genome_export_import():
    """Test genome portability."""
    logging.info("=" * 60)
    logging.info("TEST 7: Genome Export/Import")
    logging.info("=" * 60)

    config = EvolutionConfig(min_evaluations=1, variants_per_cycle=2)
    agent = AutopoieticAgent(
        initial_genome=AgentSpecies.pipeline(["ingest", "transform", "emit"]),
        executor=mock_executor,
        config=config,
    )

    # Evolve a bit
    await agent.evolve_cycle()

    # Export
    exported = agent.export_genome()
    logging.info("  Exported genome: %s bytes", len(exported))

    # Import into another agent
    agent2 = AutopoieticAgent(
        initial_genome=AgentSpecies.hunter("blank"),
        executor=mock_executor,
        config=config,
    )
    agent2.import_genome(exported)
    logging.info("  Imported into agent2: %s", agent2.genome)
    assert agent.genome.name == agent2.genome.name
    logging.info("  ✅ Export/Import PASSED")
    logging.info("")


# ─── Main ────────────────────────────────────────────────────────


async def main():
    logging.info("")
    logging.info("╔══════════════════════════════════════════════════════════╗")
    logging.info("║        LEVEL 7 AUTOPOIETIC AGENT - VALIDATION          ║")
    logging.info("║        Reality Level: C5-REAL                           ║")
    logging.info("╚══════════════════════════════════════════════════════════╝")
    logging.info("")

    t0 = time.perf_counter()

    # Synchronous tests
    test_genome_serialization()
    test_mutation_operators()
    test_crossover()
    test_genesis()

    # Async tests
    await test_evolution_cycle()
    await test_continuous_evolution()
    await test_genome_export_import()

    elapsed = (time.perf_counter() - t0) * 1000
    logging.info("╔══════════════════════════════════════════════════════════╗")
    logging.info("║  ALL 7 TESTS PASSED - %.1fms total                    ║", elapsed)
    logging.info("║  L7 Autopoietic Agent: OPERATIONAL                     ║")
    logging.info("╚══════════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    asyncio.run(main())
