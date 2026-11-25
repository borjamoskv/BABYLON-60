"""
test_swarm_kda_dag_scheduler.py — Suite de Verificación Nivel 3 (KDA) y Nivel 4 (Kahn DAG)
========================================================================================
Valida la evicción LFU O(1) de la memoria KDA, la detección determinista de ciclos
en el grafo causal y la ejecución topológica libre de deadlocks.
"""

import os
import pytest

from agents_archi.orchestrator.kda_dag_swarm import (
    CyclicDependencyError,
    KahnDagSwarmScheduler,
    KdaSwarmMemory,
    MAX_SLOT_BYTES,
    MctsBranchSelector,
    OuroborosRepairLoop,
    PrmStepScore,
    SwarmDagNode,
    ThermalLock,
    ThermodynamicBudgetExhausted,
)


@pytest.mark.asyncio
async def test_kda_memory_bounded_capacity_and_lfu() -> None:
    """Valida los axiomas AX-KDA-1 (Capacidad), AX-KDA-2 (Versión) y AX-KDA-3 (LFU)."""
    mem = KdaSwarmMemory(capacity=3)

    # 1. Insertar 3 elementos (Capacidad máxima)
    v1 = await mem.put("k1", b"val_1")
    v2 = await mem.put("k2", b"val_2")
    v3 = await mem.put("k3", b"val_3")
    assert v1 == 1 and v2 == 1 and v3 == 1
    assert await mem.size() == 3

    # 2. Incrementar frecuencia de k1 y k3 mediante lecturas (AX-KDA-6)
    _ = await mem.get("k1")  # freq(k1) = 2
    _ = await mem.get("k1")  # freq(k1) = 3
    _ = await mem.get("k3")  # freq(k3) = 2
    # k2 tiene freq = 1 (Víctima de evicción LFU)

    # 3. Insertar k4: debe evictar k2
    await mem.put("k4", b"val_4")
    assert await mem.size() == 3
    assert await mem.get("k2") is None  # Evictado por LFU
    assert await mem.get("k1") == b"val_1"
    assert await mem.get("k3") == b"val_3"
    assert await mem.get("k4") == b"val_4"

    # 4. Actualizar k1: incrementa versión (AX-KDA-2)
    v1_new = await mem.put("k1", b"val_1_mod")
    assert v1_new == 2
    assert await mem.get("k1") == b"val_1_mod"


@pytest.mark.asyncio
async def test_kda_memory_payload_size_enforcement() -> None:
    """Valida que valores mayores a 8.192 bytes sean rechazados."""
    mem = KdaSwarmMemory(capacity=10)
    oversized = b"x" * (MAX_SLOT_BYTES + 1)
    with pytest.raises(ValueError, match="FRACTURA KDA"):
        await mem.put("bad_key", oversized)


@pytest.mark.asyncio
async def test_kahn_dag_topological_execution() -> None:
    """Valida la ejecución topológica causal estricta de un grafo de 5 nodos."""
    scheduler = KahnDagSwarmScheduler(concurrency_limit=4)
    mem = KdaSwarmMemory(capacity=10)
    execution_order = []

    async def task_a(m: KdaSwarmMemory) -> None:
        execution_order.append("A")
        await m.put("res_a", b"data_a")

    async def task_b(m: KdaSwarmMemory) -> None:
        execution_order.append("B")
        await m.put("res_b", b"data_b")

    async def task_c(m: KdaSwarmMemory) -> None:
        execution_order.append("C")
        await m.put("res_c", b"data_c")

    async def task_d(m: KdaSwarmMemory) -> None:
        execution_order.append("D")
        await m.put("res_d", b"data_d")

    # A -> B, A -> C; [B, C] -> D
    scheduler.add_node(SwarmDagNode("A", dependencies=[], task=task_a))
    scheduler.add_node(SwarmDagNode("B", dependencies=["A"], task=task_b))
    scheduler.add_node(SwarmDagNode("C", dependencies=["A"], task=task_c))
    scheduler.add_node(SwarmDagNode("D", dependencies=["B", "C"], task=task_d))

    await scheduler.execute_dag(mem)

    # Invariantes de precedencia causal:
    assert execution_order[0] == "A"
    assert "B" in execution_order[1:3]
    assert "C" in execution_order[1:3]
    assert execution_order[3] == "D"
    assert await mem.get("res_d") == b"data_d"


def test_kahn_dag_cycle_detection() -> None:
    """Valida la detección determinista de dependencias circulares (A -> B -> C -> A)."""
    scheduler = KahnDagSwarmScheduler()

    async def dummy(m: KdaSwarmMemory) -> None:
        return None

    scheduler.add_node(SwarmDagNode("A", dependencies=["C"], task=dummy))
    scheduler.add_node(SwarmDagNode("B", dependencies=["A"], task=dummy))
    scheduler.add_node(SwarmDagNode("C", dependencies=["B"], task=dummy))

    with pytest.raises(CyclicDependencyError, match="Ciclo causal detectado"):
        scheduler.topological_sort()


def test_thermal_lock_mutual_exclusion() -> None:
    """Valida la exclusión mutua de ejecución con ThermalLock."""
    lock_file = f"/tmp/.test_thermal_{os.getpid()}.lock"
    if os.path.exists(lock_file):
        os.remove(lock_file)

    with ThermalLock(lock_file):
        # Intentar adquirir el mismo lock debe disparar excepción
        with pytest.raises(RuntimeError, match="FRACTURA TÉRMICA"):
            with ThermalLock(lock_file):
                pass

    # Al salir, el lock debe estar liberado
    assert not os.path.exists(lock_file)


def test_mcts_branch_selector_prunes_and_selects_ucb1() -> None:
    """Valida la poda de ramas alucinadas y la selección UCB1 en MctsBranchSelector."""
    selector = MctsBranchSelector(tau_prm=0.6)
    candidates = [
        PrmStepScore(branch_id="b_hallucinated", step_reward=0.95, visits=1, invariant_holds=False),
        PrmStepScore(branch_id="b_low_reward", step_reward=0.40, visits=2, invariant_holds=True),
        PrmStepScore(branch_id="b_solid_explored", step_reward=0.75, visits=10, invariant_holds=True),
        PrmStepScore(branch_id="b_high_potential", step_reward=0.82, visits=2, invariant_holds=True),
    ]
    winner = selector.prune_and_select(candidates)
    assert winner.branch_id == "b_high_potential"

    with pytest.raises(ValueError, match="MCTS_ALL_BRANCHES_PRUNED"):
        selector.prune_and_select([candidates[0], candidates[1]])


def test_ouroboros_repair_loop_convergence_and_budget_exhaustion() -> None:
    """Valida la convergencia en bucle cerrado y el aborto fail-closed por presupuesto agotado."""
    loop = OuroborosRepairLoop(max_iterations=3)

    def verifier(code: str) -> tuple[bool, str]:
        if "FIXED_ASSERT" in code:
            return True, "PASS"
        return False, "AssertionError: missing FIXED_ASSERT"

    def patcher(code: str, diag: str, attempt: int) -> str:
        if attempt == 2:
            return code + "\n# FIXED_ASSERT"
        return code + f"\n# attempt_{attempt}"

    final_state, attempts = loop.run("def f(): pass", verifier, patcher)
    assert attempts == 3
    assert "FIXED_ASSERT" in final_state

    # Si el patcher nunca repara el fallo, debe abortar con ThermodynamicBudgetExhausted
    with pytest.raises(ThermodynamicBudgetExhausted, match="OUROBOROS_BUDGET_EXHAUSTED"):
        loop.run("def broken(): pass", verifier, lambda c, d, a: c)
