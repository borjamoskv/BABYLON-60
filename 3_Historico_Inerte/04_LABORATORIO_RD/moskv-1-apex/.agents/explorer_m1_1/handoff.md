# Handoff Report — Moskv-1 Cognitive Architecture Python Core

**Status:** COMPLETE (Initial Exploration & Architecture Formulation)  
**Assigned Folder:** `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/.agents/explorer_m1_1`  
**Execution Level:** C5-REAL (Assessment & Design)

---

## 1. Observation

Direct observations made within the workspace `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`:

1. **Workspace Files and Subdirectories:**
   - There are no Python files (`.py`), virtual environments (`.venv`), or Python package configs (`pyproject.toml`, `requirements.txt`) currently in the workspace root.
   - An existing Node.js architecture is present in the `kernel/` folder:
     - `kernel/event-bus.js`: Handles NATS JetStream connectivity, message serialization/deserialization, and SHA-256 hash chaining.
     - `kernel/brain-region.js`: Defines the base worker node class.
     - `kernel/autopoiesis.js`: Implements Neo4j graph mutations upon receiving high-entropy signals (`cortex.entropy.high`).
     - `kernel/metacognition.js`: Conducts graph auditing and noise pruning during sleep/freeze cycles.
     - `kernel/index.js`: Boots the swarm.
   - `docker-compose.yml` specifies the local services stack:
     - NATS client port `4222:4222` with JetStream enabled (`-js`).
     - Neo4j Live Memory Bolt port `7687:7687`.
     - Neo4j Sandbox Bolt port `7688:7687` for replay logic.
   - Docs are available under `docs/ARCHITECTURE.md` and `docs/DATA_MODEL.md`.

2. **Project Path Verification:**
   - Attempted listing of `~/teamwork_projects` yielded:
     ```
     total 0
     drwxr-xr-x@   3 borjafernandezangulo  staff    96 Jun 16 02:43 .
     drwxr-x---+ 200 borjafernandezangulo  staff  6400 Jun 16 13:55 ..
     drwxr-xr-x@  14 borjafernandezangulo  staff   448 Jun 16 02:43 substack_signal_harvester
     ```
     No `moskv_1` directory exists inside `~/teamwork_projects`.

---

## 2. Logic Chain

1. **Path Alignment via Symlinking:**
   - **Premise:** The user request specifies `Working directory: ~/teamwork_projects/moskv_1` but the active development environment/workspace URI mapped by the system is `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`.
   - **Reasoning:** In order to prevent path conflicts, duplicate repositories, or git tracking fragmentation, a symbolic link must be created at `~/teamwork_projects/moskv_1` pointing to the workspace root.
   - **Action:** Propose executing `ln -s /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell ~/teamwork_projects/moskv_1`.

2. **Asynchronous Python Architecture:**
   - **Premise:** Node.js implements the swarm nodes (`BrainRegion`) and event bus concurrently and asynchronously using NATS JetStream client.
   - **Reasoning:** In Python, the official library `nats-py` operates strictly using Python's `asyncio` paradigm. The Neo4j driver also supports asynchronous sessions (`neo4j.AsyncGraphDatabase`).
   - **Action:** Design all core components (`EventBus`, `BrainRegion`, `MemoryStore`) to be async-first (using `async` and `await`).

3. **Verifiable Ledger & SHA-256 Hash Chaining:**
   - **Premise:** The event bus uses hash-chained events where `hash = SHA256(prevHash + payload)`.
   - **Reasoning:** Different languages and standard libraries serialize JSON structures with different whitespace or key sorting order, which causes hash mismatch.
   - **Action:** The Python EventBus must serialize payloads deterministically by using `json.dumps(payload, sort_keys=True, separators=(',', ':'))` before hashing.

4. **Dependency Protocol Alignment:**
   - **Premise:** The C5-REAL `managing-python-dependencies` protocol forbids global `pip` installation.
   - **Reasoning:** The project needs isolated environments. Since standard packaging with `pyproject.toml` is requested, we can use `venv` to initialize `.venv` and then run pip in editable mode to install local packages.

---

## 3. Caveats

- **NATS Connection Stability:** The Python `nats-py` library might require specific reconnect strategies when the NATS container restarts. It is assumed the docker-compose services are running.
- **Neo4j Transaction Lifetime:** The autopoiesis engine performs writes to Neo4j. In async Python, sessions must be carefully closed using async context managers (`async with`) to prevent socket leaks.
- **Initial Genesis State:** If the event bus is restarted and the stream already has history, `last_hash` initialized to `"GENESIS"` in memory will create a fork in the chain unless the `EventBus` retrieves the latest stream message to resume the chain. The design addresses both patterns.

---

## 4. Conclusion

### A. Directory & Package Layout

We recommend the following layout inside the workspace:

```
/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/
├── pyproject.toml
├── .venv/                      # Python isolated virtual environment
├── src/
│   └── moskv_1/
│       ├── __init__.py         # Package entry point and exports
│       ├── event_bus.py        # Async event bus with hash chaining
│       ├── brain.py            # Base BrainRegion class and executors
│       └── memory.py           # Neo4j and local memory store interface
└── tests/
    ├── conftest.py             # Shared fixtures (NATS mock/test instance, Neo4j mock)
    ├── test_event_bus.py       # Event bus verification
    ├── test_brain.py           # Brain region verification
    └── test_memory.py          # Memory storage and pruning verification
```

### B. Python Package Specifications (Proposed Skeletal Code)

#### 1. `src/moskv_1/event_bus.py`
```python
import asyncio
import hashlib
import json
import time
from typing import Callable, Any, Dict, Optional
from nats.aio.client import Client as NATS
from nats.js.errors import NotFoundError

class CortexEvent:
    def __init__(self, hash: str, prev_hash: str, timestamp: float, payload: dict):
        self.hash = hash
        self.prev_hash = prev_hash
        self.timestamp = timestamp
        self.payload = payload

    def to_dict(self) -> dict:
        return {
            "hash": self.hash,
            "prevHash": self.prev_hash,
            "timestamp": self.timestamp,
            "payload": self.payload
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CortexEvent":
        return cls(
            hash=data["hash"],
            prev_hash=data["prevHash"],
            timestamp=data["timestamp"],
            payload=data["payload"]
        )

class EventBus:
    def __init__(self, server_url: str = "nats://localhost:4222", stream_name: str = "CORTEX_STREAM"):
        self.server_url = server_url
        self.stream_name = stream_name
        self.nc: Optional[NATS] = None
        self.js = None
        self.last_hash = "GENESIS"

    async def init(self, recover_chain: bool = True):
        """Connects to NATS, initializes JetStream, and verifies stream configuration."""
        self.nc = NATS()
        await self.nc.connect(self.server_url, max_reconnect_attempts=-1)
        self.js = self.nc.jetstream()
        
        # Verify or create stream
        jsm = self.nc.jetstream_manager()
        try:
            await jsm.stream_info(self.stream_name)
        except NotFoundError:
            await jsm.add_stream(
                name=self.stream_name,
                subjects=["cortex.>"],
                retention="limits",
                storage="file"
            )
            
        if recover_chain:
            await self._recover_last_hash()

    async def _recover_last_hash(self):
        """Attempts to pull the latest message from JetStream to maintain chain continuity."""
        try:
            jsm = self.nc.jetstream_manager()
            info = await jsm.stream_info(self.stream_name)
            if info.state.messages > 0:
                # Retrieve last message on subject cortex.>
                msg = await self.js.get_last_msg(self.stream_name, "cortex.>")
                data = json.loads(msg.data.decode("utf-8"))
                self.last_hash = data.get("hash", "GENESIS")
        except Exception:
            # Fall back to GENESIS if stream is empty or retrieval fails
            self.last_hash = "GENESIS"

    def _hash(self, payload: dict, prev_hash: str) -> str:
        """Deterministically hashes (prev_hash + payload)."""
        serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
        combined = f"{prev_hash}{serialized}"
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    async def publish(self, topic: str, payload: dict) -> CortexEvent:
        if not self.js:
            raise RuntimeError("EventBus is not initialized. Call init() first.")
        
        current_hash = self._hash(payload, self.last_hash)
        event = CortexEvent(
            hash=current_hash,
            prev_hash=self.last_hash,
            timestamp=time.time() * 1000, # ms timestamp to align with JS
            payload=payload
        )
        
        # Update ledger pointer
        self.last_hash = current_hash
        
        encoded_data = json.dumps(event.to_dict()).encode("utf-8")
        await self.js.publish(topic, encoded_data)
        return event

    async def subscribe(self, topic: str, callback: Callable[[CortexEvent], Any], durable_name: Optional[str] = None):
        if not self.js:
            raise RuntimeError("EventBus is not initialized. Call init() first.")
        
        # Set up a subscription (pull subscription is recommended for modern JetStream)
        sub = await self.js.subscribe(topic, durable=durable_name)
        
        async def message_loop():
            async for msg in sub.messages:
                try:
                    data = json.loads(msg.data.decode("utf-8"))
                    event = CortexEvent.from_dict(data)
                    
                    # Verify integrity chain
                    expected_hash = self._hash(event.payload, event.prev_hash)
                    if event.hash != expected_hash:
                        print(f"[EventBus] Integrity Violation! Hash: {event.hash} Expected: {expected_hash}")
                    
                    await callback(event)
                    await msg.ack()
                except Exception as e:
                    print(f"[EventBus] Callback processing error: {e}")
                    await msg.nak()

        # Run connection loop in background
        asyncio.create_task(message_loop())
        return sub

    async def close(self):
        if self.nc:
            await self.nc.drain()
            await self.nc.close()
```

#### 2. `src/moskv_1/brain.py`
```python
import asyncio
from typing import List, Optional
from .event_bus import EventBus, CortexEvent

class BrainRegion:
    def __init__(self, region_name: str, server_url: str = "nats://localhost:4222"):
        self.region_name = region_name
        self.bus = EventBus(server_url=server_url)
        self.subscriptions: List[Any] = []

    async def run(self):
        """Boots the brain region, connecting to the central event bus."""
        await self.bus.init()
        print(f"[CEN-Cluster] BrainRegion <{self.region_name}> Online.")

    async def emit(self, topic: str, payload: dict) -> CortexEvent:
        """Helper to publish events, automatically injecting the source region metadata."""
        enriched_payload = {**payload, "sourceRegion": self.region_name}
        return await self.bus.publish(topic, enriched_payload)

    async def process_event(self, event: CortexEvent):
        """To be overridden by subclasses to implement specific regional cognitive execution."""
        raise NotImplementedError("BrainRegions must implement process_event.")

    async def listen(self, topic: str, durable_name: Optional[str] = None):
        """Subscribes to a topic, linking the handler to process_event."""
        async def handler(event: CortexEvent):
            print(f"[{self.region_name}] Processing Event Hash: {event.hash}")
            await self.process_event(event)

        sub = await self.bus.subscribe(topic, handler, durable_name=durable_name)
        self.subscriptions.append(sub)

    async def shutdown(self):
        print(f"[CEN-Cluster] BrainRegion <{self.region_name}> shutting down...")
        await self.bus.close()
```

#### 3. `src/moskv_1/memory.py`
```python
import json
from typing import Optional
from neo4j import AsyncGraphDatabase
from .event_bus import CortexEvent

class MemoryStore:
    def __init__(self, uri: str = "bolt://localhost:7687", user: str = "neo4j", password: str = "password"):
        self.uri = uri
        self.user = user
        self.password = password
        self.driver = None

    async def init(self):
        """Initializes the Neo4j Async Driver and verifies connectivity."""
        self.driver = AsyncGraphDatabase.driver(self.uri, auth=(self.user, self.password))
        await self.driver.verify_connectivity()
        print("[MemoryStore] Neo4j connection established.")

    async def crystallize(self, event: CortexEvent):
        """Merges MemoryNode into the live graph based on event context."""
        if not self.driver:
            raise RuntimeError("MemoryStore not initialized.")
        
        payload = event.payload
        node_id = payload.get("nodeId", event.hash)
        entropy = payload.get("entropy", 1.0)
        content = payload.get("content", "Void")
        
        # Serialize dict to JSON string for Neo4j property storage
        content_str = json.dumps(content) if isinstance(content, dict) else str(content)
        source_region = payload.get("sourceRegion", "Unknown")

        cypher = """
        MERGE (r:BrainRegion {name: $sourceRegion})
        MERGE (n:MemoryNode {id: $id})
        SET n.entropy = $entropy,
            n.content = $content,
            n.lastUpdated = timestamp(),
            n.spawnHash = $hash
        MERGE (n)-[:SYNTHESIZED_BY]->(r)
        RETURN n
        """
        
        async with self.driver.session() as session:
            await session.run(
                cypher,
                id=node_id,
                entropy=entropy,
                content=content_str,
                source_region=source_region,
                hash=event.hash
            )

    async def prune(self, entropy_threshold: float):
        """Prunes old high-entropy nodes from the graph."""
        if not self.driver:
            raise RuntimeError("MemoryStore not initialized.")

        # Match nodes with high entropy that haven't been updated in 60s
        cypher = """
        MATCH (n:MemoryNode)
        WHERE n.entropy > $threshold AND n.lastUpdated < (timestamp() - 60000)
        DETACH DELETE n
        RETURN count(n) as pruned_count
        """
        
        async with self.driver.session() as session:
            result = await session.run(cypher, threshold=entropy_threshold)
            record = await result.single()
            pruned = record["pruned_count"] if record else 0
            print(f"[MemoryStore] Pruned {pruned} high-entropy nodes.")
            return pruned

    async def close(self):
        if self.driver:
            await self.driver.close()
```

### C. Dependency Strategy & isolated Setup

To strictly comply with the C5-REAL `managing-python-dependencies` protocol:

1. **`pyproject.toml` Configuration:**
   Create a standard `pyproject.toml` declaring dependencies for `nats-py`, `neo4j`, and `pytest`.
   
   ```toml
   [build-system]
   requires = ["setuptools>=61.0.0"]
   build-backend = "setuptools.build_meta"

   [project]
   name = "moskv_1"
   version = "1.0.0"
   description = "Moskv-1 Python Core Cognitive Architecture"
   readme = "README.md"
   requires-python = ">=3.9"
   dependencies = [
       "nats-py>=2.7.0",
       "neo4j>=5.14.0",
   ]

   [project.optional-dependencies]
   dev = [
       "pytest>=7.4.0",
       "pytest-asyncio>=0.21.0",
   ]
   ```

2. **Isolated Environment Instantiation:**
   Use the `venv` module to isolate package execution from the global system Python environment. Run:
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install --upgrade pip setuptools
   .venv/bin/pip install -e ".[dev]"
   ```
   This performs an editable installation (`-e .`), which adds the package to the PYTHONPATH inside `.venv` without polluting the global user directories.

---

## 5. Verification Method

To verify the setup, run the following commands sequentially:

1. **Symlink Initialization Verification:**
   ```bash
   ln -s /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell ~/teamwork_projects/moskv_1
   ls -la ~/teamwork_projects/moskv_1
   ```
   *Expected outcome:* The symbolic link lists the contents of the `lively-maxwell` workspace correctly.

2. **Environment & Dependency Verification:**
   ```bash
   python3 -m venv .venv
   .venv/bin/pip install --upgrade pip setuptools
   .venv/bin/pip install -e ".[dev]"
   .venv/bin/pytest --version
   ```
   *Expected outcome:* Pytest command prints version successfully indicating setup isolation.

3. **Running the Test Suite:**
   Once code is implemented, run:
   ```bash
   .venv/bin/pytest
   ```
   *Expected outcome:* Pytest discovers tests under `tests/` and executes them. Tests should mock NATS and Neo4j connections to verify logic without depending on running Docker containers in isolated unit environments.
