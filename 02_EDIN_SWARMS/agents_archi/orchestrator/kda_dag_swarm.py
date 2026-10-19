"""
kda_dag_swarm.py — Orquestación Swarm Nivel 3 (Memoria KDA) y Nivel 4 (DAG de Kahn)
==================================================================================
Implementa:
  - Memoria KDA Acotada O(1) bajo axiomas AX-KDA-1 a AX-KDA-6 con evicción LFU.
  - Planificador Acíclico de Kahn O(V + E) con detección determinista de ciclos.
  - Cerrojo de histéresis térmica (ThermalLock) para prevenir ejecución simultánea.
"""

import asyncio
from dataclasses import dataclass
import inspect
import math
import os
import time
from types import TracebackType
from typing import Dict, List, Optional, Callable

# ============================================================================
# 1. NIVEL 3: MEMORIA KDA ACOTADA O(1) (AX-KDA-1 A AX-KDA-6)
# ============================================================================

MAX_SLOT_BYTES = 8192


class KdaEntry:
    def __init__(self, value: bytes, version: int = 1, freq: int = 1):
        self.value = value
        self.version = version
        self.freq = freq
        self.updated_at = time.time_ns()


class KdaSwarmMemory:
    """Buffer de memoria acotada O(1) para enjambres.
    Cumple AX-KDA-1 (Capacidad), AX-KDA-2 (Versión), AX-KDA-3 (Evicción LFU) y AX-KDA-6 (Frecuencia).
    """

    def __init__(self, capacity: int = 256):
        self.capacity = capacity
        self.entries: Dict[str, KdaEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[bytes]:
        """AX-KDA-6: La lectura incrementa la frecuencia protegiendo la clave de evicción."""
        async with self._lock:
            if key in self.entries:
                entry = self.entries[key]
                entry.freq += 1
                return entry.value
            return None

    async def put(self, key: str, value: bytes) -> int:
        """AX-KDA-1, AX-KDA-2, AX-KDA-3: Inserción acotada con evicción determinista LFU."""
        if len(value) > MAX_SLOT_BYTES:
            raise ValueError(f"FRACTURA KDA: El valor excede el límite de {MAX_SLOT_BYTES} bytes")

        async with self._lock:
            if key in self.entries:
                # Clave existente: actualizar valor e incrementar versión monotónicamente
                entry = self.entries[key]
                entry.value = value
                entry.version += 1
                entry.updated_at = time.time_ns()
                return entry.version

            # Nueva clave: si se alcanzó la capacidad máxima, evictar por LFU (AX-KDA-3)
            if len(self.entries) >= self.capacity:
                self._evict_lfu()

            self.entries[key] = KdaEntry(value=value, version=1, freq=1)
            return 1

    def _evict_lfu(self) -> None:
        """Evicta la clave con menor frecuencia de acceso (y menor versión ante empate)."""
        if not self.entries:
            return
        victim_key = min(
            self.entries.keys(),
            key=lambda k: (self.entries[k].freq, self.entries[k].version, self.entries[k].updated_at),
        )
        del self.entries[victim_key]

    async def size(self) -> int:
        async with self._lock:
            return len(self.entries)


# ============================================================================
# 2. NIVEL 4: PLANIFICADOR DAG DE KAHN Y CERROJO TÉRMICO
# ============================================================================


class CyclicDependencyError(Exception):
    """Disparado cuando el DAG de enjambre contiene un ciclo cerrado (violación de aciclicidad)."""

    pass


class ThermalLock:
    """Cerrojo atómico en sistema de archivos para mitigar carreras de enjambres."""

    def __init__(self, lock_path: str):
        self.lock_path = lock_path
        self._acquired = False

    def __enter__(self) -> "ThermalLock":
        try:
            # Creación atómica exclusiva (O_CREAT | O_EXCL) for .cortex_thermal_lock
            fd = os.open(self.lock_path, os.O_CREAT | os.O_EXCL | os.O_RDWR)
            os.write(fd, f"pid:{os.getpid()};time:{time.time_ns()}".encode())
            os.close(fd)
            self._acquired = True
            return self
        except FileExistsError:
            raise RuntimeError(f"FRACTURA TÉRMICA: Lock activo en {self.lock_path}")

    def __exit__(
        self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None
    ) -> None:
        if self._acquired and os.path.exists(self.lock_path):
            try:
                os.remove(self.lock_path)
            except OSError:
                pass
            self._acquired = False


class SwarmDagNode:
    def __init__(self, node_id: str, dependencies: List[str], task: Callable[[KdaSwarmMemory], object]):
        self.node_id = node_id
        self.dependencies = dependencies
        self.task = task


class KahnDagSwarmScheduler:
    """Planificador topológico basado en el algoritmo de Kahn O(V + E).
    Garantiza ejecución acíclica estricta sin bloqueos mutuos.
    """

    def __init__(self, concurrency_limit: int = 16):
        self.concurrency_limit = concurrency_limit
        self.nodes: Dict[str, SwarmDagNode] = {}

    def add_node(self, node: SwarmDagNode) -> None:
        nid = getattr(node, "node_id", getattr(node, "id", None))
        if nid is None:
            raise ValueError("El nodo debe poseer node_id o id")
        self.nodes[nid] = node

    def topological_sort(self) -> List[str]:
        """Calcula el orden topológico O(V + E) y detecta ciclos deterministamente."""
        in_degree: Dict[str, int] = {nid: 0 for nid in self.nodes}
        adj: Dict[str, List[str]] = {nid: [] for nid in self.nodes}

        for nid, node in self.nodes.items():
            for dep in node.dependencies:
                if dep not in self.nodes:
                    raise ValueError(f"Dependencia huérfana en el DAG: {dep} requerida por {nid}")
                adj[dep].append(nid)
                in_degree[nid] += 1

        queue = [nid for nid, deg in in_degree.items() if deg == 0]
        sorted_nodes: List[str] = []

        while queue:
            curr = queue.pop(0)
            sorted_nodes.append(curr)

            for neighbor in adj[curr]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_nodes) != len(self.nodes):
            cycle_nodes = [nid for nid, deg in in_degree.items() if deg > 0]
            raise CyclicDependencyError(f"Ciclo causal detectado en el enjambre: {cycle_nodes}")

        return sorted_nodes

    async def execute_dag(self, memory: KdaSwarmMemory, lock_path: Optional[str] = None) -> List[str]:
        """Ejecuta el grafo topológico respetando dependencias bajo el semáforo concurrente."""
        if lock_path is None:
            import tempfile

            lock_path = os.path.join(tempfile.gettempdir(), ".swarm_kda_dag_global.lock")

        with ThermalLock(lock_path):
            sorted_order = self.topological_sort()
            semaphore = asyncio.Semaphore(self.concurrency_limit)
            completed_events: Dict[str, asyncio.Event] = {nid: asyncio.Event() for nid in self.nodes}

            async def run_single(node_id: str) -> None:
                node = self.nodes[node_id]
                # Esperar a que todas las dependencias hayan finalizado
                for dep in node.dependencies:
                    await completed_events[dep].wait()

                async with semaphore:
                    # Ejecutar la transición cognitiva
                    if inspect.iscoroutinefunction(node.task):
                        await node.task(memory)
                    else:
                        node.task(memory)
                    completed_events[node_id].set()

            tasks = [run_single(nid) for nid in sorted_order]
            await asyncio.gather(*tasks)
            return sorted_order


# ============================================================================
# 3. FAST-SLOW THINKING: MCTS + PRM & BUCLE OUROBOROS (ROADMAP v5.0 FASE 3)
# ============================================================================


@dataclass(frozen=True)
class PrmStepScore:
    """Evaluación de un paso intermedio por el Process Reward Model (PRM)."""

    branch_id: str
    step_reward: float
    visits: int
    invariant_holds: bool = True


class MctsBranchSelector:
    """Selector de ramas Monte Carlo Tree Search (MCTS) guiado por PRM local.
    Poda deterministamente cualquier rama que viole invariantes o caiga bajo tau_prm,
    y selecciona entre las supervivientes la que maximiza UCB1.
    """

    def __init__(self, tau_prm: float = 0.5, exploration_c: float = 1.41421356237):
        self.tau_prm = tau_prm
        self.exploration_c = exploration_c

    def prune_and_select(self, candidates: List[PrmStepScore]) -> PrmStepScore:
        survivors = [c for c in candidates if c.invariant_holds and c.step_reward >= self.tau_prm and c.visits > 0]
        if not survivors:
            raise ValueError("MCTS_ALL_BRANCHES_PRUNED: Ninguna rama superó el filtro PRM/invariante")

        total_visits = sum(c.visits for c in survivors)
        log_total = math.log(max(total_visits, 1))

        def ucb1(c: PrmStepScore) -> tuple[float, str]:
            score = c.step_reward + self.exploration_c * math.sqrt(log_total / c.visits)
            return (score, c.branch_id)

        return max(survivors, key=ucb1)


class ThermodynamicBudgetExhausted(RuntimeError):
    """Disparado cuando el Bucle Ouroboros agota max_iterations sin converger en verde."""

    pass


class OuroborosRepairLoop:
    """Arnés de autocorrección en bucle cerrado acotado por presupuesto termodinámico (N_max)."""

    def __init__(self, max_iterations: int = 5):
        if max_iterations < 1:
            raise ValueError("max_iterations debe ser >= 1")
        self.max_iterations = max_iterations

    def run(
        self,
        initial_state: str,
        verifier: Callable[[str], tuple[bool, str]],
        patcher: Callable[[str, str, int], str],
    ) -> tuple[str, int]:
        state = initial_state
        last_diag = ""
        for attempt in range(1, self.max_iterations + 1):
            ok, diag = verifier(state)
            if ok:
                return state, attempt
            last_diag = diag
            if attempt < self.max_iterations:
                state = patcher(state, diag, attempt)

        raise ThermodynamicBudgetExhausted(
            f"OUROBOROS_BUDGET_EXHAUSTED: No convergió tras {self.max_iterations} iteraciones. Último fallo: {last_diag}"
        )
