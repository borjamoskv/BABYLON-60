import fcntl
import json
import os
import shutil
import tempfile


class ThermodynamicLedgerApoptosis:
    """
    Motor de Poda Semántica de Entropía (C5-REAL).
    Comprime un AOF lineal en su snapshot termodinámicamente óptimo, erradicando
    subgrafos huérfanos y nodos explícitamente podados mediante cierre transitivo causal.
    """

    def __init__(self, ledger_path: str):
        self.ledger_path = ledger_path

    def _compress_state(self) -> dict[str, dict]:
        """Calcula el estado topológico activo en memoria O(N_Active)."""
        active_state = {}
        if not os.path.exists(self.ledger_path):
            return active_state

        with open(self.ledger_path, "rb") as f:
            for line in f:
                try:
                    node = json.loads(line.decode("utf-8"))
                    if "hash_id" in node:
                        active_state[node["hash_id"]] = node
                except json.JSONDecodeError:
                    continue  # Purga de bytes corruptos

        # --- Lógica de Poda Semántica (Apoptosis Ouroboros) ---
        pruned_hashes = set()

        # 1. Singularidad de Origen: Detectar explícitos
        for h, node in active_state.items():
            if node.get("status") in ("pruned", "deleted") or node.get("action") == "delete":
                pruned_hashes.add(h)

        # 2. Cierre Transitivo Causal: Destrucción de subgrafos huérfanos
        # Iterar la topología hasta colapsar toda la onda de choque
        wave_active = True
        while wave_active:
            wave_active = False
            for h, node in active_state.items():
                if h not in pruned_hashes:
                    parent_hash = node.get("parent_hash")
                    if parent_hash and parent_hash in pruned_hashes:
                        pruned_hashes.add(h)
                        wave_active = True

        # 3. Cristalización Final
        for h in pruned_hashes:
            active_state.pop(h, None)

        return active_state

    def trigger_snapshot(self) -> int:
        """
        Ejecuta la purga semántica con bloqueo atómico POSIX (fcntl).
        """
        if not os.path.exists(self.ledger_path):
            return 0

        with open(self.ledger_path, "ab") as origin_fd:
            fcntl.flock(origin_fd.fileno(), fcntl.LOCK_EX)
            try:
                state = self._compress_state()

                fd, temp_path = tempfile.mkstemp(suffix=".aof")
                with os.fdopen(fd, "w") as temp_f:
                    for node in state.values():
                        temp_f.write(json.dumps(node) + "\n")

                # Reemplazo atómico a nivel de sistema operativo
                shutil.move(temp_path, self.ledger_path)
                return len(state)
            finally:
                fcntl.flock(origin_fd.fileno(), fcntl.LOCK_UN)
