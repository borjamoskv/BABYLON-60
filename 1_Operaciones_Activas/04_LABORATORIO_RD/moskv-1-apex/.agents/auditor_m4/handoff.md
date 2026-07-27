# Forensic Audit Report & Handoff — Moskv-1 Python Core

## Forensic Audit Report

**Work Product**: `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell` (Moskv-1 Python package)  
**Profile**: General Project (Integrity Mode: `benchmark` from `ORIGINAL_REQUEST.md`)  
**Verdict**: **INTEGRITY VIOLATION**

### Phase Results
- **Hardcoded test results & Facade implementations**: **PASS** — Main codebase files (`event_bus.py`, `brain.py`, `memory.py`) contain genuine implementation logic rather than static facades or fake returns.
- **Self-certifying tests**: **FAIL** — `tests/test_event_bus.py` line 46 contains a self-certifying assertion that verifies the cryptographic hash using the implementation's own hash calculation.
- **Pre-populated artifact detection**: **PASS** — No pre-populated logs, result files, or verification artifacts were found in the repository root or source package.
- **Layout compliance**: **FAIL** — Draft source and test files (`proposed_*.py`, `proposed_pyproject.toml`) exist inside the `.agents/explorer_m1_2/` directory, violating the rule that `.agents/` must hold metadata only.
- **Dependency audit (Benchmark Mode)**: **FAIL** — Benchmark Mode permits the language standard library only. The package uses third-party libraries (`nats-py` and `neo4j` for core features EventBus and MemoryStore) defined in `pyproject.toml`.
- **Correctness & Logic Verification**: **FAIL** — The codebase contains active defects:
  1. `EventBus.publish` mutates state (`last_hash`) before the NATS JetStream write succeeds.
  2. `MemoryStore` retrieves and iterates Neo4j results outside the `execute_write` transaction context.

---

## 5-Component Handoff Report

### 1. Observation
1. **Self-Certifying Assertion**:
   In `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/tests/test_event_bus.py` at line 46:
   ```python
   assert event.hash == bus._hash(payload, "GENESIS")
   ```
2. **State Mutation / Chain Gap**:
   In `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/src/moskv_1/event_bus.py` at lines 91-96:
   ```python
        # Update last hash state
        self.last_hash = current_hash
        
        # Publish
        data = event.to_json().encode('utf-8')
        await self.js.publish(topic, data)
   ```
3. **Transaction Lifecycle Closed-Result Access**:
   In `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/src/moskv_1/memory.py` at lines 61-74:
   ```python
        async with self.driver.session() as session:
            result = await session.execute_write(
                lambda tx: tx.run(
                    cypher,
                    id=payload.get("nodeId") or event.hash,
                    entropy=entropy,
                    content=content_str,
                    sourceRegion=source_region,
                    hash=event.hash
                )
            )
            # Retrieve records (useful for verifying or return)
            records = [record async for record in result]
            return records
   ```
4. **Layout Compliance Files**:
   Draft python source and test files were found inside `.agents/explorer_m1_2/`:
   - `proposed_brain.py`
   - `proposed_event_bus.py`
   - `proposed_memory.py`
   - `proposed_pyproject.toml`
   - `proposed_test_brain.py`
   - `proposed_test_event_bus.py`
   - `proposed_test_memory.py`
5. **Third-Party Dependencies in pyproject.toml**:
   In `/Users/borjafernandezangulo/Documents/antigravity/lively-maxwell/pyproject.toml` at lines 11-14:
   ```toml
   dependencies = [
       "nats-py>=2.7.2",
       "neo4j>=5.18.0",
   ]
   ```

### 2. Logic Chain
1. Under **Benchmark Mode** (obtained from `ORIGINAL_REQUEST.md` line 8), the system permits standard library usage only. The use of third-party `nats-py` and `neo4j` for core components (`event_bus.py` and `memory.py` respectively) is a direct dependency violation.
2. The assertion `assert event.hash == bus._hash(payload, "GENESIS")` uses the implementation under test (`bus._hash`) to calculate the expected value. If `_hash` contains a calculation bug, the assertion will still pass, constituting a **Self-Certifying Test** integrity violation.
3. In `event_bus.py`, mutating `self.last_hash = current_hash` before `await self.js.publish` means that if publishing fails (due to connection loss or serialization type errors), `self.last_hash` is left in an updated state. Subsequent publishes will chain off this unpublished hash, creating a gap in the published event chain. This logic error is verified by `tests/test_adversarial.py::test_hash_chain_gap_on_publish_failure` and `test_non_serializable_payload_crashes_and_mutates`.
4. In `memory.py`, reading from `result` (a Neo4j `Result` object) using `[record async for record in result]` occurs outside `session.execute_write`. This violates the Neo4j async driver transaction lifecycle, raising errors in production because the transaction is closed once `execute_write` returns. This is verified by `tests/test_adversarial.py::test_neo4j_transaction_lifecycle_violation`.
5. The presence of `.py` draft files in `.agents/explorer_m1_2` violates the layout requirement that `.agents/` must contain *only* metadata.

### 3. Caveats
- No integration tests were executed against real running containers of Neo4j or NATS because environment command approval timed out, and the environment is isolated under CODE_ONLY network constraints. However, behavioral unit tests were run using custom conftest mocks to confirm the findings.

### 4. Conclusion
The codebase does not meet the necessary integrity and correctness criteria due to:
1. Benchmark Mode dependency violations (importing `nats` and `neo4j`).
2. Self-certifying test implementation in `test_event_bus.py`.
3. Critical architectural flaws in NATS hash chain state preservation and Neo4j transaction handling.
4. Layout non-compliance within the `.agents/` folder.
Therefore, the verdict is a strict **INTEGRITY VIOLATION** and the work product is rejected.

### 5. Verification Method
To reproduce the findings:
1. Run the test suite with a mock conftest to bypass imports:
   ```bash
   PYTHONPATH=src pytest tests/
   ```
   *Observations*: Pytest will run 17 tests successfully, confirming the presence of the adversarial test assertions exposing transaction closed and hash gap errors.
2. Inspect the source file locations and lines cited under section 1 to verify the code structures.
