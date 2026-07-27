# Handoff Report — Moskv-1 System Design & Exploration

## 0. C5-REAL Justification Matrix
```yaml
Claim: The Moskv-1 Python Core architecture assessment and path structures have been verified in the C5-REAL workspace.
Proof: { Base: "FS scan and read operations on /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell", Range: [1, 1], Confidence: C5 }
```

---

## 1. Observation
- **Workspace Scan**: Directly scanned `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell` and identified a Node.js-based distributed cognitive OS using NATS JetStream and Neo4j.
- **Docker Topology (`docker-compose.yml`)**:
  - NATS JetStream client port: `4222` (line 8: `4222:4222`) with JS enabled (line 10: `command: ["-js"]`).
  - Neo4j graph database Bolt port: `7687` (line 21: `7687:7687`), Web Browser: `7474`, Auth: `neo4j/password`.
  - Neo4j Sandbox Bolt port: `7688` (line 37: `7688:7687`), Web Browser: `7475`.
- **Event Bus Hashing (`kernel/event-bus.js`)**:
  - Initial hash: `this.lastHash = 'GENESIS'` (line 16).
  - Hashing function: `_hash(payload, prevHash) { return crypto.createHash('sha256').update(prevHash + JSON.stringify(payload)).digest('hex'); }` (lines 47-51).
- **Autopoietic Graph Mutation (`kernel/autopoiesis.js`)**:
  - Cypher query used (lines 44-51):
    ```javascript
    const cypher = `
        MERGE (r:BrainRegion {name: $sourceRegion})
        MERGE (n:MemoryNode {id: $id}) 
        SET n.entropy = $entropy, 
            n.content = $content, 
            n.lastUpdated = timestamp(),
            n.spawnHash = $hash
        MERGE (n)-[:SYNTHESIZED_BY]->(r)
        RETURN n
    `;
    ```
- **Project Structure Specifications (`PROJECT.md`)**:
  - Target Python layout (lines 8-19):
    ```
    - src/moskv_1/: Main source package
      - __init__.py: Entry point and versioning
      - event_bus.py: Hash-chained event bus for message passing
      - brain.py: Brain region executor and Swarm nodes
      - memory.py: Neo4j/graph or local crystallized memory store interface
    - tests/: Automated unit and integration tests
      - test_event_bus.py
      - test_brain.py
      - test_memory.py
    - pyproject.toml: Project configuration and dependency matrix
    - .venv/: Local virtual environment
    ```
- **Path Checking**:
  - Command `ls -la ~/teamwork_projects` confirms `~/teamwork_projects/moskv_1` does not exist in the host file system.

---

## 2. Logic Chain
1. **Target Working Directory vs Workspace**: The operator expects the project working directory to be `~/teamwork_projects/moskv_1`, but the active workspace is `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`.
   - **Reasoning**: A symlink from `~/teamwork_projects/moskv_1` pointing to the git workspace `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell` resolves the difference dynamically while preventing untracked project files outside the git repository.
2. **Hash Integrity**: The EventBus hash chain must remain C5-REAL verifiable and language-independent.
   - **Reasoning**: To avoid hash mismatches between JS and Python, Python's `event_bus.py` must serialize JSON payloads deterministically using `json.dumps(payload, sort_keys=True, separators=(',', ':'))` before hashing.
3. **Async Neo4j Driver**: The brain runs an asynchronous NATS listener.
   - **Reasoning**: To prevent thread blocking, `memory.py` must use Neo4j's `AsyncGraphDatabase` driver.
4. **Dependency Protocol**: Standardized packaging requires dependency isolation.
   - **Reasoning**: As per the C5-REAL `managing-python-dependencies` fallback protocol, we must construct a `pyproject.toml` configuration and install it in editable mode inside a clean `.venv` using `.venv/bin/pip install -e ".[dev]"`.

---

## 3. Caveats
- Since this is a read-only exploration subagent, no code was written or executed. 
- Environment variables (`NATS_URL`, `NEO4J_URI`, etc.) must be forwarded to the Python execution loop to override the default local ports if they change.
- In multi-language environments, `JSON.stringify` in JavaScript might format floating-point values slightly differently than Python's `json.dumps`. Handlers must ensure strict string or integer values inside the payload's hashed sections to prevent float representation mismatches.

---

## 4. Conclusion

### Proposed Python Package Design
The "Moskv-1" Python package must be implemented as follows:

#### A. `src/moskv_1/event_bus.py`
- Utilizes `nats-py` for async connection and JetStream.
- Maintains `self.last_hash = "GENESIS"`.
- Uses `hashlib.sha256` on deterministic JSON strings:
  ```python
  def _hash(self, payload: dict, prev_hash: str) -> str:
      serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
      return hashlib.sha256(f"{prev_hash}{serialized}".encode('utf-8')).hexdigest()
  ```
- Implements:
  - `publish(topic: str, payload: dict) -> CortexEvent`
  - `subscribe(topic: str, callback: Callable, durable_name: str = None)`
  - `close()`

#### B. `src/moskv_1/brain.py`
- Implements `BrainRegion` as the execution swarm node.
- Automatically appends `sourceRegion: self.region_name` to all emitted event payloads.
- Implements:
  - `boot()`: Initializes the underlying `EventBus`.
  - `emit(topic: str, payload: dict)`: Emits to the bus.
  - `listen(topic: str, handler: Callable, durable_name: str = None)`: Attaches callback.
  - `shutdown()`: Closes event bus subscriptions.

#### C. `src/moskv_1/memory.py`
- Implements `MemoryStore` mapping node creation and pruning.
- Uses `neo4j.AsyncGraphDatabase.driver`.
- Implements:
  - `crystallize(event: dict)`: Inserts a `MemoryNode` node using Cypher.
  - `prune(entropy_threshold: float, age_ms: int)`: Removes volatile nodes.
  - `close()`: Closes connection.

### Local Environment Setup (C5-REAL Python Dependencies)
Create a `pyproject.toml` file in the root directory:
```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "moskv_1"
version = "1.0.0"
description = "Python implementation of the Moskv-1 cognitive architecture"
requires-python = ">=3.9"
dependencies = [
    "nats-py>=2.7.2",
    "neo4j>=5.21.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0"
]
```

To initialize and setup the isolated virtual environment:
```bash
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e ".[dev]"
```

### Symlink Setup
Execute the following to map the working directory:
```bash
ln -s /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell ~/teamwork_projects/moskv_1
```

---

## 5. Verification Method
1. **Directory Structure Verification**: Ensure `src/moskv_1/` contains the targeted modules and `pyproject.toml` exists in `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`.
2. **Environment Activation Verification**: Run `.venv/bin/pytest --version` to verify isolated installation of `pytest`.
3. **Functional Contract Tests**: Write test cases in `tests/test_event_bus.py` to confirm that the SHA-256 hash chaining of an event matches the exact hash output produced by the JS EventBus for the identical payload and parent hash.
