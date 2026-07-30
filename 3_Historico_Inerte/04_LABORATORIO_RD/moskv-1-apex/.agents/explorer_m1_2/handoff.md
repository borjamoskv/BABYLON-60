# Handoff Report — Moskv-1 System Design Assessment

## 1. Observation

### 1.1 Workspace Directory Structure
Scanning `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell` revealed the following directory topology:
* `kernel/`: Contains the reference Node.js implementation:
  * `event-bus.js` (121 lines): Implements NATS JetStream interaction and SHA-256 hashing.
  * `brain-region.js` (50 lines): Implements a class representing a worker node.
  * `autopoiesis.js` (93 lines): Neo4j-driven self-modifying graph mutations.
  * `metacognition.js` (84 lines): Audit & sleep cycles (memory pruning).
* `docs/`: Reference architecture and data model:
  * `ARCHITECTURE.md`: Topology and execution flow details.
  * `DATA_MODEL.md`: Ontology specifications for `(:MemoryNode)` and `(:BrainRegion)` nodes, as well as the `CortexEvent` interface contract.
* `docker-compose.yml` (50 lines): Configures services including NATS JetStream (port 4222), Neo4j Live Database (port 7687), and Neo4j Sandbox (port 7688).

### 1.2 Missing Target Path
Running the check command for the requested working directory yielded:
```bash
$ ls -la ~/teamwork_projects/moskv_1
ls: /Users/borjafernandezangulo/teamwork_projects/moskv_1: No such file or directory
```
This confirms the path `~/teamwork_projects/moskv_1` does not exist on the filesystem.

---

## 2. Logic Chain

### 2.1 Package Architecture & Verification (EventBus, Brain, Memory)
* **Observation (event-bus.js):** Uses standard SHA-256 of `(prevHash + payload)` to build the ledger chain.
* **Logic:** To replicate this in Python, the event serialization must be deterministic. Standard Python dictionaries do not guarantee insertion order in all contexts, and serializing dicts to JSON via `json.dumps()` without sorting keys can lead to non-deterministic string outputs, which breaks the SHA-256 hash chaining.
* **Derivation:** We must use `json.dumps(payload, sort_keys=True, separators=(',', ':'))` for deterministic outputs.
* **Observation (brain-region.js):** Each `BrainRegion` enriches the event payload with `sourceRegion` before publishing.
* **Logic:** Subclassing `BrainRegion` or utilizing a wrapper pattern in Python ensures that when standard methods are called, the metadata properties are automatically injected.
* **Observation (autopoiesis.js & metacognition.js):** Neo4j updates are executed using Cypher queries via the official Neo4j driver.
* **Logic:** The Python `neo4j` package includes `AsyncGraphDatabase` (v5.x+), which supports asyncio-based database calls. This integrates natively with `nats-py`'s asyncio loops.

### 2.2 Python Dependency Strategy
* **Observation (managing-python-dependencies SKILL):** Enforces isolated environments without global package modifications.
* **Logic:** We can define standard package settings inside `pyproject.toml` using `hatchling` as the build system.
* **Derivation:** This allows us to define core dependencies (`nats-py`, `neo4j`) and optional dev dependencies (`pytest`, `pytest-asyncio`). Installing via `.venv/bin/pip install -e .[dev]` will set up the workspace in editable mode.

### 2.3 Working Directory & Symlink Setup
* **Observation (ls -la ~/teamwork_projects/moskv_1):** The target directory is absent, yet the active workspace is `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`.
* **Logic:** Establishing a symlink from `~/teamwork_projects/moskv_1` to `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell` bridges the gap. Any operations inside the target folder will execute directly against the source code workspace, preserving Git history and indexing.

---

## 3. Caveats
* **NATS/Neo4j Services:** The design assumes NATS JetStream and Neo4j are active on their default ports (4222 and 7687 respectively) as defined in the project's `docker-compose.yml`. If these ports change or are blocked, connection errors will arise.
* **Replay Sandbox Port:** Replay utilizes `bolt://localhost:7688` by default in JS. Python tests and implementations must mirror this environment separation if sandbox testing is executed.

---

## 4. Conclusion

### 4.1 Recommended Package Structure
The following structure must be created in the workspace:
```
/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/
├── pyproject.toml              # Build & dependency settings (Hatchling)
├── src/
│   └── moskv_1/
│       ├── __init__.py         # Package entry point & version
│       ├── event_bus.py        # Async NATS JetStream + Hash Chaining
│       ├── brain.py            # BrainRegion base executor
│       └── memory.py           # Neo4j Graph database integration
└── tests/
    ├── test_event_bus.py       # EventBus tests
    ├── test_brain.py           # BrainRegion tests
    └── test_memory.py          # MemoryStore tests
```

### 4.2 Proposed Layout Blueprints
We have written the complete, fully formed code templates to the following paths in our agent folder for the implementer agent to deploy:
* `proposed_pyproject.toml`
* `proposed_event_bus.py`
* `proposed_brain.py`
* `proposed_memory.py`
* `proposed_test_event_bus.py`
* `proposed_test_brain.py`
* `proposed_test_memory.py`

---

## 5. Verification Method

### 5.1 Environment Setup Verification
Verify that the virtual environment compiles successfully and includes only the isolated packages:
```bash
# 1. Create the virtual environment
python3 -m venv .venv

# 2. Upgrade core tools
.venv/bin/pip install --upgrade pip setuptools

# 3. Install packages in editable mode
.venv/bin/pip install -e .[dev]

# 4. Verify version and packages
.venv/bin/pip list
```

### 5.2 Test Suite Verification
Run the automated tests using the local pytest executable:
```bash
.venv/bin/pytest tests/
```
**Expected Outcome:** All mock tests pass with 100% success.

### 5.3 Symlink Verification
To verify the symlink mechanism:
```bash
# Create the symlink
ln -s /Users/borjafernandezangulo/Documents/antigravity/lively-maxwell /Users/borjafernandezangulo/teamwork_projects/moskv_1

# Verify the link target
ls -la ~/teamwork_projects/moskv_1
```
**Expected Outcome:** Directory contents match `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell`.
