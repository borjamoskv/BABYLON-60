# Handoff Report: Review of Moskv-1 Python Core

## 1. Observation

Direct code observations from `src/moskv_1/` and `tests/`:

1. **`src/moskv_1/event_bus.py` (lines 9-28):**
   ```python
   @dataclass
   class CortexEvent:
       hash: str
       prev_hash: str
       timestamp: float
       payload: dict

       def to_json(self) -> str:
           # Deterministic serialization for reliable cross-language hash chains
           return json.dumps(asdict(self), sort_keys=True, separators=(',', ':'))

       @classmethod
       def from_json(cls, json_str: str) -> 'CortexEvent':
           data = json.loads(json_str)
           return cls(
               hash=data['hash'],
               prev_hash=data['prev_hash'],
               timestamp=data['timestamp'],
               payload=data['payload']
           )
   ```

2. **`src/moskv_1/event_bus.py` (lines 68-74):**
   ```python
   def _hash(self, payload: dict, prev_hash: str) -> str:
       """
       Deterministic SHA-256 hash calculation over stringified payload and previous hash.
       """
       serialized = json.dumps(payload, sort_keys=True, separators=(',', ':'))
       hash_input = f"{prev_hash}{serialized}".encode('utf-8')
       return hashlib.sha256(hash_input).hexdigest()
   ```

3. **`kernel/event-bus.js` (lines 24-37) JS implementation of hash chaining:**
   ```javascript
   _hash(payload, prevHash) {
       return crypto.createHash('sha256')
           .update(prevHash + JSON.stringify(payload))
           .digest('hex');
   }

   async emit(subject, payload) {
       const currentHash = this._hash(payload, this.lastHash);
       const event = {
           timestamp: Date.now(),
           payload,
           prevHash: this.lastHash,
           hash: currentHash
       };
   ```

4. **`src/moskv_1/memory.py` (lines 61-74) Neo4j execution logic:**
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

5. **`src/moskv_1/memory.py` (lines 90-97) Neo4j pruning logic:**
   ```python
   async with self.driver.session() as session:
       result = await session.execute_write(
           lambda tx: tx.run(cypher, threshold=entropy_threshold)
       )
       record = await result.single()
       pruned_count = record["pruned"] if record else 0
       print(f"[MemoryStore] Pruned {pruned_count} high-entropy nodes.")
       return pruned_count
   ```

---

## 2. Logic Chain

1. **Schema Incompatibility (`prev_hash` vs `prevHash`):**
   - **Observation 1:** Python defines the field `prev_hash` in `CortexEvent` (line 12), and its `to_json` serializes it as-is.
   - **Observation 3:** JS expects `prevHash` (line 35) and defines `prevHash` in `docs/DATA_MODEL.md`.
   - **Deduction:** When Python publishes to NATS, other subscribers (like the JS autopoiesis engine or replay tool) will look for `prevHash` and find `undefined`. Conversely, when JS publishes `prevHash`, Python's `from_json` (line 25) will crash with a `KeyError: 'prev_hash'`.

2. **Hash Mismatch (Divergent serialization):**
   - **Observation 2:** Python's `_hash` uses `json.dumps(payload, sort_keys=True)`.
   - **Observation 3:** JS's `_hash` uses `JSON.stringify(payload)` (which does not sort keys).
   - **Deduction:** If a payload has multiple keys in a non-sorted insertion order (e.g. `sourceRegion` and `entropy` as in `brain.py`), Python and JS will serialize it differently. Thus, the resulting SHA-256 hash will diverge, breaking hash-chain verification in a multi-language swarm.

3. **Neo4j Transaction Context Lifetime Violation:**
   - **Observation 4 & 5:** Python's `MemoryStore` runs Cypher queries using `session.execute_write(lambda tx: tx.run(...))`. It returns the raw `AsyncResult` from the callback context, and then attempts async iteration `[record async for record in result]` or `await result.single()` *outside* the `execute_write` block.
   - **Deduction:** Once the transaction callback returns, the transaction is committed and closed. Accessing records from an `AsyncResult` after the transaction context has closed throws a `ResultExpired` or driver-specific runtime exception. Unit tests (`tests/test_memory.py`) bypass this by mocking the session result stream synchronously, presenting a "mock facade bypass".

---

## 3. Caveats

- **No caveats.** The logic issues and data model discrepancies were verified via cross-file static code analysis and comparison with specification schemas.

---

## 4. Conclusion

**Verdict**: `REQUEST_CHANGES`. The Python implementation contains critical defects in schema compatibility, hash-chain verifiability, and database session lifecycles that will cause immediate integration failures and runtime crashes when running in a multi-language NATS/Neo4j environment.

---

## 5. Verification Method

To verify these findings:
1. **Schema Check:** Create a dummy event using JS schema and pass it into Python `CortexEvent.from_json()`. It will fail with `KeyError: 'prev_hash'`.
2. **Hash Chain Verification Check:** Execute Python `_hash({"sourceRegion": "Reasoning", "entropy": 0.95}, "GENESIS")` and compare the value with the Node.js `_hash({"sourceRegion": "Reasoning", "entropy": 0.95}, "GENESIS")`. Observe the divergent hex outputs.
3. **Neo4j Transaction Check:** Spin up a local Neo4j container, instantiate a real `MemoryStore` (removing mocks), and attempt `await store.crystallize(event)`. Observe the runtime driver error as records are accessed outside the write transaction.

---

# QUALITY REVIEW REPORT

## Review Summary

**Verdict**: REQUEST_CHANGES

## Findings

### [Critical] Finding 1: Neo4j Transaction Context Violation
- **What**: Query results are consumed outside the transaction function (`execute_write`).
- **Where**: `src/moskv_1/memory.py`, lines 73 and 94.
- **Why**: Returning `AsyncResult` from `execute_write` commits the transaction and closes the cursor. Consuming it afterwards throws driver exceptions.
- **Suggestion**: Materialize records inside the write callback, e.g.:
  ```python
  async def write_tx(tx):
      res = await tx.run(cypher, params)
      return [record async for record in res]
  records = await session.execute_write(write_tx)
  ```

### [Critical] Finding 2: `prev_hash` vs `prevHash` Field Incompatibility
- **What**: Snake case field definition in `CortexEvent` dataclass.
- **Where**: `src/moskv_1/event_bus.py`, lines 12, 18, 25.
- **Why**: Violates the specification in `docs/DATA_MODEL.md` (which mandates `prevHash`). Breaks parsing/serializations across language boundaries (Python <-> JS).
- **Suggestion**: Use `prevHash` as the field name, or customize serialization in `to_json` and `from_json` to translate `prev_hash` to `prevHash`.

### [Major] Finding 3: Divergent Hashing Serializations
- **What**: Python sorts JSON keys for payload hashing, whereas JS does not.
- **Where**: `src/moskv_1/event_bus.py`, line 72 vs `kernel/event-bus.js`, line 26.
- **Why**: Causes hash outputs to diverge for multi-key dictionaries, breaking chain verifiability in the swarm.
- **Suggestion**: Define a strict canonical JSON sorting rule for both JS and Python (e.g. using a stable stringify library in JS, or aligning both to a standard key order).

### [Minor] Finding 4: Interface Contract Differences
- **What**: Difference in signatures between implementation and `PROJECT.md`.
- **Where**: `src/moskv_1/event_bus.py`, lines 76 and 99.
- **Why**: `PROJECT.md` specifies `publish(payload)` and `subscribe(topic, callback)`, but the Python implementation adds required arguments like `topic` in `publish` and secondary arguments in `subscribe`.
- **Suggestion**: Update `PROJECT.md` to reflect the actual parameters needed for a NATS publisher/subscriber model.

## Verified Claims

- Python event serialization/deserialization correctness → verified via `test_cortex_event_serialization` → **PASS (Self-certifying only, hides schema incompatibility)**
- Event bus mocking verification → verified via mock assertion tests → **PASS (Bypasses runtime transaction bugs)**

## Coverage Gaps

- **Integration Hashing verification** — risk level: **HIGH** — recommendation: Implement cross-language hash validation tests comparing output values with the JS implementation.
- **Neo4j integration path** — risk level: **HIGH** — recommendation: Add integration tests that execute against a real Neo4j container to catch transaction scope violations.

## Unverified Items

- NATS Stream creation parameters and durability at runtime — reason: local environment connection was not accessible.

---

# ADVERSARIAL REVIEW REPORT

## Challenge Summary

**Overall risk assessment**: CRITICAL

## Challenges

### [Critical] Challenge 1: Key Mismatch Parser Crash
- **Assumption challenged**: Event wrapper format is isolated within languages.
- **Attack scenario**: A Node.js brain region emits an event containing `prevHash`. A Python worker listens to this subject and passes it to `from_json()`.
- **Blast radius**: The Python worker crashes with `KeyError: 'prev_hash'` inside the NATS subscription callback, automatically NAK'ing the message and entering an infinite message-redelivery processing loop.
- **Mitigation**: Update the Python dataclass to maps `prevHash` correctly on serialization/deserialization.

### [High] Challenge 2: Ledger Verification Verification Breakage
- **Assumption challenged**: Python and JS hash values match for the same event payload.
- **Attack scenario**: A Python BrainRegion emits an event payload enriched with `sourceRegion` and `entropy`. The JS Autopoiesis Engine receives this, recalculates the hash based on the JS event bus, and attempts to compare it.
- **Blast radius**: The hashes do not match because Python sorted the keys during serialization before hashing. Verification fails, raising a false security/integrity alarm in the cognitive chain.
- **Mitigation**: Standardize stable/canonical sorting on both sides.

### [High] Challenge 3: Neo4j Driver Connection Error
- **Assumption challenged**: Query execution results are usable after transaction commits.
- **Attack scenario**: Swarm undergoes high-frequency crystallization. `MemoryStore` executes `crystallize` and tries to evaluate records outside `execute_write`.
- **Blast radius**: Throws driver runtime exceptions, causing high-entropy events to fail crystallization. Topology mutations fail.
- **Mitigation**: Materialize/collect records inside transaction lambdas.

## Stress Test Results

- **JSON serialization under key ordering changes** → Expected JS-compatible hash → Actual: Divergent hash → **FAIL**
- **Neo4j record fetch outside transaction block** → Expected: Fetched records -> Actual: Connection closed/transaction terminated exception → **FAIL**

## Unchallenged Areas

- **NATS jetstream durability and speed** — reason not challenged: local broker is mock-only and unavailable.
