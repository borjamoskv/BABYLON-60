# Analysis Report — Upgrading IHelpPurgeDaemon to Dynamic T-Cell Monitoring

- **Author**: Borja Moskv (borjamoskv)
- **Reality Level**: C5-REAL
- **Date**: 2026-06-28T14:40:33+02:00
- **Task**: Upgrading `IHelpPurgeDaemon` to a dynamic T-Cell monitoring daemon targeting `BASE_MAFIA_NODES`.

---

## Executive Summary
This report analyzes the current implementations of `IHelpPurgeDaemon`, the target nodes list `BASE_MAFIA_NODES` in telemetry, the Adaptive Immunity Router (`MHCAntigenRouter`), the Master Ledger logging and verification protocols, and existing test suites in preparation for a dynamic T-Cell monitoring daemon upgrade. 

---

## 1. Current Implementation of `IHelpPurgeDaemon`
- **File Path**: `babylon60/extensions/daemon/t_cell_ihelp_purge.py`
- **Class**: `IHelpPurgeDaemon`
- **Agent ID**: `"t_cell_alpha_purge"`
- **Static Antigen Pattern**: `r"(?i)\b(ihelp|david\s+dominguez)\b"`

### Execution Mechanism
Upon initialization, the daemon registers itself to the central `MHCAntigenRouter`:
```python
self.mhc_router.register_t_cell(self.agent_id, self.antigen_signature)
```

When a payload matches this signature, the MHC router triggers the `phagocytize` method:
1. **Canonicalization**: The payload is canonicalized using `canonicalize_content(payload)`.
2. **Exergy Metrics**: Computes length (`waste_bytes`) and theoretical cycles saved (`tokens_saved = waste_bytes // 3`).
3. **Hashing**: Generates a SHA3-256 hash of the payload:
   ```python
   payload_hash = hashlib.sha3_256(canonical).hexdigest()
   ```
4. **Audit Trail Generation**: Returns an audit trail payload structure containing the execution metadata.
5. **Ledger Integration**: The current implementation has a placeholder comment pointing to `babylon60.audit.ledger.emit_rejection`. In the upgraded version, this must be integrated with `EnterpriseAuditLedger` to log actions under C5-REAL specifications.

---

## 2. Analysis of `BASE_MAFIA_NODES`
- **File Path**: `babylon60/routes/telemetry.py` (Lines 173–362)
- **Structure**: A static list of strings containing exactly **188 elements**.
- **Content Types**:
  - Personal names (e.g., `"david dominguez"`, `"manuel mas"`, `"gabi contreras aguilera"`).
  - Domains and Substack URLs (e.g., `"daviddominguez.substack.com"`, `"crecerensubstack.com"`, `"aimafia.substack.com"`).
  - Programs/Phrases (e.g., `"crecer en substack"`, `"newsletter exitosa"`, `"marca personal 2026"`, `"chiringuito digital"`).

### Telemetry Routes & State Interaction
1. **GET `/telemetry/nodes`**: Combines the static `BASE_MAFIA_NODES` with dynamic nodes retrieved from facts of type `"mafia_node"` under the project `"smoke-detector"`.
2. **POST `/telemetry/nodes`**: Allows adding new dynamic nodes to the database, broadcasting them to connected WebSocket clients via `broadcast_nodes_update(data.node)`.
3. **WS `/telemetry/nodes/ws`**: Provides connected extensions with an initial list `INIT_NODES` containing combined static and dynamic nodes, and listens for client telemetry ingest commands (`INGEST_TELEMETRY`).

---

## 3. Antigen Registration & `MHCAntigenRouter`
- **File Path**: `babylon60/engine/causal/taint_engine.py` (Lines 275–425)

### Registration Mechanics
Daemons are registered via `register_t_cell(self, agent_id: str, antigen_regex: str)` which compiles the regex case-insensitively and maps it in `self._t_cells`.

### Adaptive Immunology Routing Logic
1. **Presentation**: Payloads pass through `present_antigen(payload)`. If a match is found in the regex mesh, the assigned `agent_id` is returned.
2. **Dynamic Evolution (record_miss)**:
   - When a payload fails to match but resolves to an agent, it records a miss.
   - Payloads are normalized to lowercase alphanumeric signatures.
   - Recurring misses are tracked in `self._miss_tracker`.
   - If a signature's hit count reaches `self.promotion_threshold` (default 3), the antigen pattern is promoted to the active mesh and registered:
     ```python
     escaped_sig = re.escape(sig)
     pattern = rf"(?i)\b{escaped_sig}\b"
     self.register_t_cell(resolved_agent_id, pattern)
     ```
   - Dynamic antigens are persisted to `~/.babylon60/dynamic_antigens.json`.

### Static Invariants
- Pre-compiled SOTA constraints are loaded from `babylon60/engine/causal/sota_antigens.json`.
- These target:
  - `claude-fable-5`: `(?i)\b(steer|correct|adjust|wrong|fix approach)\b`
  - `gpt-5.5`: `(?i)\b(bash|exit code|stderr|traceback|panic|crash)\b`
  - `kimi-k2.7-code`: `(?i)\b(tool|function|api|hallucination|not found)\b`

---

## 4. Master Ledger API & Signature Protocol
- **File Path**: `babylon60/audit/ledger.py`

### Event Logging Protocol (`log_action`)
When log events are written, the following protocol is enforced:
1. **Event Hash (`audit_id`)**: Computes a SHA-256 hash representing the event block:
   ```python
   audit_id = hashlib.sha256(f"{timestamp}{tenant_id}{actor_role}{actor_id}{action}{resource}{status}".encode()).hexdigest()
   ```
2. **Chain Connection (`entry_hash`)**: Updates the Sparse Merkle Tree (`smt_engine`) and hashes the Merkle root with the prior block's hash:
   ```python
   entry_hash = hashlib.sha256(f"merkle_batch:{merkle_root_new}:{current_last_hash}".encode()).hexdigest()
   ```
3. **Cryptographic Signature**: Signs `entry_hash` using the Ed25519 private key:
   ```python
   signature = self.private_key.sign(entry_hash.encode()).hex()
   ```
4. **Anchoring**: Pushes logs asynchronously to Rekor public transparency logs and TSA servers using digitcert timestamping.

### Cryptographic Taint Token Validation (`verify_taint_token`)
- Enforces the `BABYLON60-TAINT` signature on fact proposals.
- Validates the token format: `taint:{curve}:{agent_id}:{session_id}:{timestamp}:{nonce}:{signature}`.
- Rejects tokens with timestamp drift > 5 minutes (300 seconds).
- Prevents replay attacks using an SQLite nonce database table `taint_nonces`.
- Verifies Ed25519 signature validity against the registered agent public key.

---

## 5. Existing Test Suites & Test Structure
1. **`tests/extensions/daemon/test_taint_enforcement.py`**:
   - Tests secure taint token generation, signature verification, timestamp expiration, replay attack prevention, and invariant validation under `verify_c5_state_machine`.
   - Tests `MHCAntigenRouter` routing integration and dynamic antigen evolution/promotion.
2. **`tests/test_telemetry_core.py`**:
   - Tests telemetry collection mechanisms using `Span` and `SpanContext`.
   - Verifies trace recording, metric exports, and decorator wrappers (`@traced`).
3. **`tests/test_tda_routing.py`**:
   - Verifies discrete memory graph traversal using the geodesic descent path over Hodge potential calculations.

---

## 6. Critical Architectural Mismatch and Verification Failure
During execution verification, a systemic import failure blocked the test collection:
- **Error**: `ModuleNotFoundError: No module named 'babylon60.engine.swarm'` in `babylon60/engine/__init__.py:88`.
- **Root Cause**: The facade module performs a relative import `from .swarm import ...` but the `swarm` folder was refactored and moved to the root level `babylon60/swarm/`.
- **Impact**: Pytest fails to collect any test files due to an autouse fixture `mock_local_embedder` in `tests/conftest.py` that transitively imports `Babylon60Engine` from `babylon60.engine`.
- **Proposed Resolution**: Apply the generated diff patch `babylon60_engine_import.patch` to update the import in `babylon60/engine/__init__.py` to:
  ```python
  from babylon60.swarm import (
      agent_mixin,
      ...
  )
  ```
