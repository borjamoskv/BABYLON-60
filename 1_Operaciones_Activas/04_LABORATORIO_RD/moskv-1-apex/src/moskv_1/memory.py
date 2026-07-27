import json
import time
from typing import Optional, Union, Dict, Any, List
from moskv_1.event_bus import CortexEvent
from moskv_1.immunity import ImmunityLayer, ImmuneState

try:
    from neo4j import AsyncGraphDatabase
except ImportError:
    AsyncGraphDatabase = None

class InMemoryNode:
    def __init__(self, element_id: str, labels: list, properties: dict):
        self.element_id = element_id
        self.labels = labels
        self._properties = properties

    @property
    def id(self):
        return self.element_id

    def __getitem__(self, key):
        return self._properties[key]

    def get(self, key, default=None):
        return self._properties.get(key, default)

    def keys(self):
        return self._properties.keys()

    def values(self):
        return self._properties.values()

    def items(self):
        return self._properties.items()

class InMemoryRecord:
    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self._data.values())[key]
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

class MemoryStore:
    """
    Sovereign Graph Database interface. Simulates the Neo4j API in-memory
    when no real driver is connected, but uses the Neo4j transaction context properly when driver is set.
    """
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver: Any = None
        self._nodes: Dict[str, Dict[str, Any]] = {}
        self._regions: Dict[str, Dict[str, Any]] = {}
        self._relationships: List[tuple] = []
        self.immunity = ImmunityLayer()

    async def connect(self):
        """
        Connects to the Neo4j instance if the library is available, or defaults to in-memory mode.
        """
        if AsyncGraphDatabase is not None:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    self.uri,
                    auth=(self.user, self.password),
                    max_connection_pool_size=50,
                    connection_acquisition_timeout=20.0
                )
                await self.driver.verify_connectivity()
                print("[MemoryStore] Neo4j Driver connected. Graph mutation active.")
                return
            except Exception as e:
                print(f"[MemoryStore] Failed to connect to Neo4j: {e}")
                raise e
        print("[MemoryStore] Using in-memory mode (Neo4j driver not available).")

    async def crystallize(self, event: CortexEvent) -> List[Any]:
        """
        Creates/updates a MemoryNode from a CortexEvent structure and links it to its BrainRegion.
        Also evaluates the signal using the Immunity Layer.
        """
        payload = event.payload
        source_region = payload.get("sourceRegion", "Unknown")
        entropy = payload.get("entropy")
        content = payload.get("content", "Void")

        if isinstance(content, (dict, list)):
            content_str = json.dumps(content)
        else:
            content_str = str(content)

        # Evaluate via Immunity Layer if is_quarantined is not explicitly passed
        immune_state_obj, calculated_entropy = self.immunity.evaluate_signal(content_str)
        if entropy is None:
            entropy = calculated_entropy
        
        is_quarantined = payload.get("is_quarantined")
        if is_quarantined is None:
            is_quarantined = (immune_state_obj == ImmuneState.QUARANTINED or immune_state_obj == ImmuneState.NECROTIC)
            
        immune_state = payload.get("immune_state", immune_state_obj.value)

        node_id = payload.get("nodeId") or event.hash

        # Event-driven Apoptosis: If the incoming entropy is extreme, trigger a full graph prune asynchronously.
        if entropy > self.immunity.high_threshold * 1.5:
            print("[MemoryStore] Event-Driven Apoptosis Triggered due to high entropy spike.")
            # We schedule it asynchronously to avoid blocking the current transaction
            import asyncio
            asyncio.create_task(self.prune(self.immunity.high_threshold))

        if self.driver:
            cypher = """
                MERGE (r:BrainRegion {name: $sourceRegion})
                MERGE (n:MemoryNode {id: $id}) 
                SET n.entropy = $entropy, 
                    n.content = $content, 
                    n.lastUpdated = timestamp(),
                    n.spawnHash = $hash,
                    n.is_quarantined = $is_quarantined,
                    n.immune_state = $immune_state
                MERGE (n)-[:SYNTHESIZED_BY]->(r)
                RETURN n
            """
            async def work(tx):
                res = await tx.run(
                    cypher,
                    id=node_id,
                    entropy=entropy,
                    content=content_str,
                    sourceRegion=source_region,
                    hash=event.hash,
                    is_quarantined=is_quarantined,
                    immune_state=immune_state
                )
                # Consume and materialize results INSIDE transaction callback
                return [record async for record in res]

            async with self.driver.session() as session:
                records = await session.execute_write(work)
                return records
        else:
            # In-memory graph store crystallization
            self._regions[source_region] = {"name": source_region}
            now_ms = time.time() * 1000.0
            node_props = {
                "id": node_id,
                "entropy": entropy,
                "content": content_str,
                "lastUpdated": now_ms,
                "spawnHash": event.hash,
                "sourceRegion": source_region,
                "is_quarantined": is_quarantined,
                "immune_state": immune_state
            }
            self._nodes[node_id] = node_props
            rel = (node_id, "SYNTHESIZED_BY", source_region)
            if rel not in self._relationships:
                self._relationships.append(rel)

            node_obj = InMemoryNode(element_id=node_id, labels=["MemoryNode"], properties=node_props)
            record = InMemoryRecord({"n": node_obj})
            return [record]

    async def quarantine(self, node_id: str, reason: str) -> bool:
        """Manually put a memory node into quarantine status."""
        if self.driver:
            cypher = """
                MATCH (n:MemoryNode {id: $id})
                SET n.is_quarantined = true,
                    n.quarantine_reason = $reason,
                    n.immune_state = "quarantined"
                RETURN n
            """
            async def work(tx):
                res = await tx.run(cypher, id=node_id, reason=reason)
                return [record async for record in res]
            async with self.driver.session() as session:
                records = await session.execute_write(work)
                return len(records) > 0
        else:
            if node_id in self._nodes:
                self._nodes[node_id]["is_quarantined"] = True
                self._nodes[node_id]["quarantine_reason"] = reason
                self._nodes[node_id]["immune_state"] = "quarantined"
                return True
            return False

    async def unquarantine(self, node_id: str) -> bool:
        """Lift quarantine status from a memory node."""
        if self.driver:
            cypher = """
                MATCH (n:MemoryNode {id: $id})
                SET n.is_quarantined = false,
                    n.immune_state = "promotable"
                REMOVE n.quarantine_reason
                RETURN n
            """
            async def work(tx):
                res = await tx.run(cypher, id=node_id)
                return [record async for record in res]
            async with self.driver.session() as session:
                records = await session.execute_write(work)
                return len(records) > 0
        else:
            if node_id in self._nodes:
                self._nodes[node_id]["is_quarantined"] = False
                self._nodes[node_id]["immune_state"] = "promotable"
                self._nodes[node_id].pop("quarantine_reason", None)
                return True
            return False

    async def prune(self, entropy_threshold: float) -> int:
        """
        Purges memory nodes with entropy higher than the threshold that haven't crystallized (older than 24 hours).
        """
        if self.driver:
            cypher = """
                MATCH (n:MemoryNode)
                WHERE n.entropy > $threshold AND n.lastUpdated < (timestamp() - 86400000)
                DETACH DELETE n
                RETURN count(n) as pruned
            """
            async def work(tx):
                res = await tx.run(cypher, threshold=entropy_threshold)
                record = await res.single()
                return record["pruned"] if record else 0

            async with self.driver.session() as session:
                pruned_count = await session.execute_write(work)
                print(f"[MemoryStore] Pruned {pruned_count} high-entropy nodes.")
                return pruned_count
        else:
            now_ms = time.time() * 1000.0
            cutoff = now_ms - 86400000.0  # 24 hours in ms
            to_prune = []
            for node_id, props in list(self._nodes.items()):
                if props["entropy"] > entropy_threshold and props["lastUpdated"] < cutoff:
                    to_prune.append(node_id)

            for node_id in to_prune:
                if node_id in self._nodes:
                    del self._nodes[node_id]
                self._relationships = [r for r in self._relationships if r[0] != node_id]

            pruned_count = len(to_prune)
            print(f"[MemoryStore] Pruned {pruned_count} high-entropy nodes (in-memory).")
            return pruned_count

    async def close(self):
        """
        Closes the Neo4j driver connection.
        """
        if self.driver:
            await self.driver.close()
            print("[MemoryStore] Neo4j Connection Closed.")
        else:
            print("[MemoryStore] In-memory Connection Closed.")
