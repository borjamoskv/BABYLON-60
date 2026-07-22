import asyncio
import sqlite3
import time
from typing import Dict, Tuple, Set

# C5-REAL NEUROMORPHIC PRIMITIVES (V2 - STDP & LEAKY INTEGRATE-AND-FIRE)
# Bypass Von Neumann CPU/Memory segregation. Memory (SQLite WAL) dictates routing weights in real-time.


class STDPMemristor:
    """
    Invariante Físico de Memoria + Resistencia con Plasticidad STDP.
    (Spike-Timing-Dependent Plasticity). La asimetría causal determina el peso.
    """

    def __init__(self, db_path: str, pre_id: str, post_id: str):
        self.db_path = db_path
        self.synapse_id = f"{pre_id}_{post_id}"
        self.pre_id = pre_id
        self.post_id = post_id
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            with conn:
                conn.execute("PRAGMA journal_mode=WAL;")
                conn.execute("PRAGMA busy_timeout=5000;")
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS memristor_weights (
                        synapse_id TEXT PRIMARY KEY,
                        weight REAL NOT NULL,
                        last_pre_spike_ts REAL,
                        last_post_spike_ts REAL
                    )
                """)
                conn.execute(
                    "INSERT OR IGNORE INTO memristor_weights VALUES (?, 1.0, 0.0, 0.0)",
                    (self.synapse_id,),
                )
        finally:
            conn.close()

    def register_pre_spike(self) -> float:
        """Registra el pulso de la neurona origen y calcula STDP si la destino disparó recientemente."""
        now = time.time()
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            with conn:
                conn.execute("PRAGMA busy_timeout=5000;")
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.execute(
                    "SELECT weight, last_post_spike_ts FROM memristor_weights WHERE synapse_id = ?",
                    (self.synapse_id,),
                )
                weight, last_post_ts = cur.fetchone()

                # STDP Asimétrico: Si PRE dispara DESPUÉS de POST, la causalidad es inversa -> Atrofia (LTD)
                if last_post_ts > 0 and (now - last_post_ts) < 1.0:
                    weight = max(0.1, weight - 0.2)  # Depresión a largo plazo

                conn.execute(
                    "UPDATE memristor_weights SET weight = ?, last_pre_spike_ts = ? WHERE synapse_id = ?",
                    (weight, now, self.synapse_id),
                )
                return float(weight)
        finally:
            conn.close()

    def register_post_spike(self) -> float:
        """Registra el pulso de la neurona destino y calcula STDP si la origen disparó recientemente."""
        now = time.time()
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        try:
            with conn:
                conn.execute("PRAGMA busy_timeout=5000;")
                conn.execute("BEGIN IMMEDIATE")
                cur = conn.execute(
                    "SELECT weight, last_pre_spike_ts FROM memristor_weights WHERE synapse_id = ?",
                    (self.synapse_id,),
                )
                weight, last_pre_ts = cur.fetchone()

                # STDP Asimétrico: Si POST dispara DESPUÉS de PRE, la causalidad es correcta -> Fortalecimiento (LTP)
                if last_pre_ts > 0 and (now - last_pre_ts) < 1.0:
                    weight += 0.5  # Potenciación a largo plazo

                conn.execute(
                    "UPDATE memristor_weights SET weight = ?, last_post_spike_ts = ? WHERE synapse_id = ?",
                    (weight, now, self.synapse_id),
                )
                return float(weight)
        finally:
            conn.close()


class LeakySpikingNode:
    """
    Leaky Integrate-and-Fire (LIF).
    La energía decae termodinámicamente en el tiempo (Leak). Previene Zombie States por acumulación pasiva.
    """

    def __init__(self, node_id: str, threshold: float = 10.0, leak_rate: float = 2.0):
        self.node_id = node_id
        self.threshold = threshold
        self.leak_rate = leak_rate
        self._current_potential = 0.0
        self.last_update_ts = time.time()
        self._fire_event = asyncio.Event()

    def _apply_leak(self) -> None:
        """Aplica la caída termodinámica basada en el tiempo transcurrido."""
        now = time.time()
        delta_t = now - self.last_update_ts
        self._current_potential = max(
            0.0, self._current_potential - (self.leak_rate * delta_t)
        )
        self.last_update_ts = now

    @property
    def current_potential(self) -> float:
        self._apply_leak()
        return self._current_potential

    async def accumulate(self, energy: float) -> None:
        """Acumulación asíncrona de Iones (Tokens/Señales)."""
        self._apply_leak()
        self._current_potential += energy
        if self._current_potential >= self.threshold:
            self._fire_event.set()

    async def wait_and_fire(self) -> float:
        """Idle Absoluto. Suspende el hilo O(1) hasta el evento físico."""
        await self._fire_event.wait()

        # Fire
        spiked_energy = self._current_potential
        self._current_potential = 0.0
        self._fire_event.clear()
        self.last_update_ts = time.time()

        return spiked_energy


class SelfHealingMesh:
    """
    Topología Descentralizada Neuromórfica.
    Redirección O(1) en caso de nodo muerto por radiación/crash.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.nodes: Dict[str, LeakySpikingNode] = {}
        self.synapses: Dict[Tuple[str, str], STDPMemristor] = {}
        self.dead_nodes: Set[str] = set()

    def get_node(self, node_id: str) -> LeakySpikingNode:
        if node_id not in self.nodes:
            self.nodes[node_id] = LeakySpikingNode(node_id)
        return self.nodes[node_id]

    def connect(self, pre: str, post: str) -> None:
        edge = (pre, post)
        if edge not in self.synapses:
            self.synapses[edge] = STDPMemristor(self.db_path, pre, post)

    def kill_node(self, node_id: str) -> None:
        """Simula fallo catastrófico (radiación térmica/kernel panic)."""
        print(
            f"[SelfHealingMesh] FALLO FÍSICO DETECTADO en nodo {node_id}. Ejecutando Apoptosis."
        )
        self.dead_nodes.add(node_id)

    def find_surrogate_path(self, start_node: str, end_node: str) -> list[str]:
        """Búsqueda BFS de ruta sustituta que evite nodos muertos (Métrica de Lawvere)."""
        if start_node in self.dead_nodes or end_node in self.dead_nodes:
            return []
        
        queue = [[start_node]]
        visited = {start_node}
        
        while queue:
            path = queue.pop(0)
            curr = path[-1]
            if curr == end_node:
                return path
            
            for (pre, post) in self.synapses.keys():
                if pre == curr and post not in visited and post not in self.dead_nodes:
                    visited.add(post)
                    queue.append(path + [post])
        return []

    async def route_pulse(self, start_node: str, end_node: str, energy: float) -> None:
        """Enrutamiento tolerante a fallos buscando atajos (Plasticidad Topológica)."""
        if start_node in self.dead_nodes or end_node in self.dead_nodes:
            print(
                f"[SelfHealingMesh] Ruta {start_node}->{end_node} destruida. Abortando pulso."
            )
            return

        # Pre-spike
        if (start_node, end_node) in self.synapses:
            weight = self.synapses[(start_node, end_node)].register_pre_spike()
            delivered_energy = energy * weight
        else:
            delivered_energy = energy  # Baseline if no synapse recorded

        target = self.get_node(end_node)
        await target.accumulate(delivered_energy)

    async def route_pulse_with_auto_healing(self, start_node: str, end_node: str, energy: float) -> bool:
        """Enrutamiento con auto-sanación dinámica de Malla Neuromórfica en caso de bypass."""
        path = self.find_surrogate_path(start_node, end_node)
        if not path or len(path) < 2:
            print(f"[SelfHealingMesh] Imposible reparar ruta {start_node}->{end_node}. Métrica Lawvere = inf.")
            return False
        
        current_energy = energy
        for i in range(len(path) - 1):
            hop_pre, hop_post = path[i], path[i+1]
            await self.route_pulse(hop_pre, hop_post, current_energy)
        return True
