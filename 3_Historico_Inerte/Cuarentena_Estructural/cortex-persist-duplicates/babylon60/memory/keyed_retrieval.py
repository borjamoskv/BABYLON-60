import logging
import typing
from pathlib import Path
from typing import Any

import msgpack

logger = logging.getLogger(__name__)


class KeyedRetrievalIndex:
    """
    Keyed Retrieval Graph System (KRGS) - C5-REAL
    O(1) topological subgraph resolution with high-speed MessagePack flat-file persistence.
    """

    def __init__(self, storage_dir: str = "data/krgs", tenant_id: str = "default"):
        self.storage_dir = Path(storage_dir)
        self._tenant_id = tenant_id
        self.index_path = self.storage_dir / f"{tenant_id}_index.msgpack"
        self.graph_path = self.storage_dir / f"{tenant_id}_graph.msgpack"

        # Mapeo directo O(1): Clave -> Set de Hashes de Nodos
        self._index: dict[str, set[str]] = {}
        # Grafo local en RAM de hashes -> Nodos (Dict)
        self._memory_graph: dict[str, dict[str, Any]] = {}

        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._load_from_disk()

    def _load_from_disk(self):
        """Reconstruye el índice y el grafo desde MessagePack a velocidad C5-REAL."""
        if self.index_path.exists():
            with open(self.index_path, "rb") as f:
                raw_index = typing.cast(dict, msgpack.unpack(f, raw=False))
                # Convert list back to sets for O(1) ops
                self._index = {k: set(v) for k, v in raw_index.items()}

        if self.graph_path.exists():
            with open(self.graph_path, "rb") as f:
                self._memory_graph = typing.cast(dict, msgpack.unpack(f, raw=False))

        logger.info(
            "[KRGS] Loaded %d keys and %d nodes.", len(self._index), len(self._memory_graph)
        )

    def flush_to_disk(self):
        """Serializa el índice y el grafo usando MessagePack para mínima latencia I/O."""
        # Convert sets to lists for msgpack compatibility
        serializable_index = {k: list(v) for k, v in self._index.items()}
        with open(self.index_path, "wb") as f:
            msgpack.pack(serializable_index, f, use_bin_type=True)

        with open(self.graph_path, "wb") as f:
            msgpack.pack(self._memory_graph, f, use_bin_type=True)

    def register_node(self, keys: list[str], node: dict[str, Any]):
        """Indexa un nodo bajo múltiples claves conceptuales y lo persiste."""
        node_hash = node.get("hash_id")
        if not node_hash:
            raise ValueError("Node must contain a 'hash_id' for C5-REAL indexing.")

        self._memory_graph[node_hash] = node

        for key in keys:
            clean_key = key.lower().strip()
            if clean_key not in self._index:
                self._index[clean_key] = set()
            self._index[clean_key].add(node_hash)

    def resolve_context(self, required_keys: list[str]) -> list[dict[str, Any]]:
        """
        Resuelve el subgrafo mínimo necesario combinando las claves solicitadas.
        Garantiza una carga selectiva en RAM O(1).
        """
        target_hashes: set[str] = set()

        # Unión de hashes que coinciden con las claves solicitadas
        for key in required_keys:
            clean_key = key.lower().strip()
            if clean_key in self._index:
                target_hashes.update(self._index[clean_key])

        resolved_nodes = []
        visited = set()

        def depth_first_search(node_hash: str):
            if node_hash in visited or node_hash not in self._memory_graph:
                return
            visited.add(node_hash)

            # Cargar dependencias primero para mantener el orden cronológico/lógico estricto
            node = self._memory_graph[node_hash]
            for dep_hash in node.get("dependencies", []):
                depth_first_search(dep_hash)

            resolved_nodes.append(node)

        # Reconstruir el subgrafo ramificado para cada hash objetivo
        for n_hash in target_hashes:
            depth_first_search(n_hash)

        return resolved_nodes
