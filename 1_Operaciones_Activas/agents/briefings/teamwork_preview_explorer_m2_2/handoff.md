<!-- C5-REAL EXERGY CERTIFIED -->
# Milestone 2 Audit Report — Git Ledger & BFT Audit (C5-REAL)

He asumido el control del disco físico y completado la auditoría adversarial del Git Ledger, integración con Git Sentinel, persistencia SQLite WAL y cumplimiento de la invariante CORTEX-PERSIST (Ω185).

---

## 1. Observation

### Observation 1.1: Git Sentinel in `scripts/50_audit_loop.py`
- **File Path**: `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scripts/50_audit_loop.py`
- **Lines 93-113**: `phase_5_git_sentinel` stages target file with `git add target_path`, commits via:
  ```python
  commit_cmd = [
      "git", "-c", "commit.gpgsign=false", "commit", "-m",
      f"feat(C5-REAL): Transducción atómica en {os.path.basename(target_path)}",
  ]
  ```
  and returns full commit hash via `git rev-parse HEAD`.
- **Lines 139-172**: `write_to_cortex_ledger` inserts into `.cortex/cortex.db` table `bft_ledger`:
  ```python
  taint_signature = f"CORTEX-TAINT:borjamoskv:mutation:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{commit_hash[:8]}"
  cursor.execute(
      "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, cortex_taint) VALUES (?, ?, ?, ?, ?)",
      (agent_id, new_lamport, new_hash, prev_hash, taint_signature),
  )
  ```
  *Key Observation*: The full 40-character commit hash `commit_hash` returned by `git rev-parse HEAD` is truncated to 8 characters (`commit_hash[:8]`) and embedded inside `cortex_taint` string. It is NOT saved in its own dedicated column in SQLite WAL.

### Observation 1.2: BFT Ledger Schema in `scripts/00_init_ledger.py` and `cortex/bft_orchestrator.py`
- **File Path**: `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scripts/00_init_ledger.py` (lines 22-35) & `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/bft_orchestrator.py` (lines 49-62):
  ```sql
  CREATE TABLE IF NOT EXISTS bft_ledger (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
      agent_id TEXT,
      lamport_t INTEGER,
      payload_hash TEXT,
      step_index INTEGER,
      domain INTEGER,
      primitive INTEGER,
      modifier INTEGER,
      prev_hash TEXT NOT NULL UNIQUE,
      current_hash TEXT,
      cortex_taint TEXT NOT NULL
  );
  ```
  *Key Observation*: The table `bft_ledger` lacks a `git_commit_hash` column. There is no direct field linking SQLite WAL transactions to Git HEAD commits.

### Observation 1.3: Consensus Ledger Writing in `cortex/bft_orchestrator.py`
- **File Path**: `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/bft_orchestrator.py` (lines 337-358):
  ```python
  raw_payload = f"{d}:{p}:{m}:{prev_hash}:{current_hash}:{self.step_index}:{int(time.time())}:{os.getpid()}".encode("utf-8")
  dynamic_hash = hmac.new(bft_key.encode("utf-8"), raw_payload, hashlib.sha3_256).hexdigest()
  taint = f"CORTEX-TAINT:borjamoskv:bft_orchestrator:{self.step_index}:{dynamic_hash}"
  conn.execute(
      "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, step_index, domain, primitive, modifier, prev_hash, current_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
      (agent_id, lamport_t, payload_hash, self.step_index, d, p, m, prev_hash, current_hash, taint),
  )
  ```
  *Key Observation*: `bft_orchestrator.py` logs 10 columns into SQLite WAL, but does NOT query `git rev-parse HEAD` or record Git state during state consensus.

### Observation 1.4: Purge Ledger Writing in `cortex/cortex_purge.py`
- **File Path**: `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/cortex_purge.py` (lines 56-90):
  `write_purge_to_ledger` inserts 5 columns `(agent_id, lamport_t, payload_hash, prev_hash, cortex_taint)` with `taint_signature = f"CORTEX-TAINT:borjamoskv:landauer_purge:{time.strftime('%Y-%m-%dT%H:%M:%SZ')}:{new_hash[:8]}"`.
  *Key Observation*: `cortex_purge.py` performs git gc, branch pruning, and cache evaporation, but does not capture or store the active Git HEAD commit hash in SQLite WAL.

### Observation 1.5: Autonomous Git Daemon in `cortex/swarm/bft_sentinel.py`
- **File Path**: `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/swarm/bft_sentinel.py` (lines 30-39):
  When mutations are detected:
  ```python
  subprocess.run(["git", "add", "."], check=True)
  commit_msg = "chore(bft): autonomous state collapse [C5-REAL]"
  subprocess.run(["git", "commit", "-m", commit_msg], check=True)
  new_hash = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
  ```
  *Key Observation*: `bft_sentinel.py` executes git commits and retrieves `new_hash`, but does NOT write `new_hash` into `.cortex/cortex.db` SQLite WAL ledger.

### Observation 1.6: Zero-Trust Pipeline & Simulation Detection
- **File Paths**:
  - `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scripts/detect_sim.py` (lines 79-82):
    ```python
    def commit_exists(sha: str) -> bool:
        r = subprocess.run(["git", "cat-file", "-t", sha], capture_output=True, text=True)
        return r.returncode == 0 and r.stdout.strip() == "commit"
    ```
  - `/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/scripts/runtime_wrapper.py` (lines 144, 168):
    Captures `git_head_before` and `git_head_after` via `git rev-parse HEAD` and writes to receipt JSON.

---

## 2. Logic Chain

1. **Premise**: Milestone 2 requirements and Invariant Ω185 mandate `CORTEX-PERSIST` immutable persistence combining SQLite WAL and Git Ledger into a single, verifiable, zero-Green-Theater audit trail.
2. **Step 1 (Cryptographic Link Defect)**: Based on Observations 1.1, 1.2, 1.3, and 1.4, the SQLite table `bft_ledger` does not have a `git_commit_hash TEXT` column. As a result, `50_audit_loop.py` truncates commit hashes to 8 characters and embeds them inside a text string (`cortex_taint`), while `bft_orchestrator.py` and `cortex_purge.py` omit git commit hashes altogether.
3. **Step 2 (Rule Ω157 Violation)**: Rule Ω157 ("Merkle Subordination Invariant") strictly forbids simulating cryptographic traceability using text tags inside files or ledgers when Merkle tree objects (Git commits) exist. Truncating commit hashes to 8 characters inside text strings (`CORTEX-TAINT:...`) violates Ω157 and exposes the system to hash collision and incomplete verification.
4. **Step 3 (Orphan Sentinel Defect)**: Based on Observation 1.5, `bft_sentinel.py` operates in isolation from the SQLite WAL master ledger (`.cortex/cortex.db`). When it autonomously collapses worktree state into a Git commit, that commit hash is never cross-referenced into `bft_ledger`.
5. **Step 4 (Schema Inconsistency)**: Based on Observations 1.1, 1.3, and 1.4, different modules insert different column subsets into `bft_ledger` (5 columns vs 10 columns), creating schema fragmentation and missing metadata during cross-audit.
6. **Step 5 (Green Theater Evaluation)**: Commit messages across `50_audit_loop.py` (`feat(C5-REAL): Transducción atómica...`) and `bft_sentinel.py` (`chore(bft): autonomous state collapse [C5-REAL]`) follow standard Conventional Commit format without narrative fluff. They meet the zero-Green-Theater baseline. However, zero Green Theater also requires verifiable full cryptographic hashes in ledgers per Ω185 and `detect_sim.py`.

---

## 3. Caveats

- **No live code modifications made**: In strict accordance with the read-only investigation constraint, no code or database schema changes were executed in `scripts/` or `cortex/`.
- **Runtime execution environment**: Verification was performed by inspecting source files, git hooks, and script logic. Execution of proposed schema updates should be validated via `pytest` and `detect_sim.py` in Milestone 2 implementation.

---

## 4. Conclusion

The current Git Ledger and SQLite WAL persistence architecture contains critical alignment defects against Rule Ω185, Rule Ω157, and Milestone 2 requirements:
1. **Missing Schema Column**: `bft_ledger` table lacks `git_commit_hash TEXT` column, preventing full 40-character commit SHA cross-referencing.
2. **Sub-optimal Hash Storage**: `50_audit_loop.py` truncates commit hashes to 8 characters inside `cortex_taint` text tags instead of storing full 40-character SHAs in SQLite WAL.
3. **Unlinked BFT & Sentinel Workflows**: `bft_orchestrator.py` does not capture Git HEAD commits upon consensus, and `bft_sentinel.py` does not log Git commit SHAs to `bft_ledger`.

### Proposed Diff Patch / Schema Upgrade Plan for Implementer:

#### Recommendation 1: Update `scripts/00_init_ledger.py` & `cortex/bft_orchestrator.py` Schema
Add `git_commit_hash TEXT` to `bft_ledger`:
```sql
CREATE TABLE IF NOT EXISTS bft_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    agent_id TEXT,
    lamport_t INTEGER,
    payload_hash TEXT,
    step_index INTEGER,
    domain INTEGER,
    primitive INTEGER,
    modifier INTEGER,
    prev_hash TEXT NOT NULL UNIQUE,
    current_hash TEXT,
    git_commit_hash TEXT,
    cortex_taint TEXT NOT NULL
);
```

#### Recommendation 2: Update `scripts/50_audit_loop.py`
In `write_to_cortex_ledger(commit_hash: str, payload: str, agent_id: str)`:
```python
cursor.execute(
    "INSERT INTO bft_ledger (agent_id, lamport_t, payload_hash, prev_hash, git_commit_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?)",
    (agent_id, new_lamport, new_hash, prev_hash, commit_hash, taint_signature),
)
```

#### Recommendation 3: Update `cortex/bft_orchestrator.py`
Query `git rev-parse HEAD` during `_write_to_ledger` and store the 40-char SHA in `git_commit_hash`.

#### Recommendation 4: Connect `cortex/swarm/bft_sentinel.py`
When `bft_sentinel.py` creates a commit, call `write_to_cortex_ledger` (or equivalent helper) to insert the commit SHA into `.cortex/cortex.db`.

---

## 5. Verification Method

To independently verify this audit and any subsequent implementation:

1. **Inspect Schema**:
   Run python script or sqlite query on `.cortex/cortex.db` to check `PRAGMA table_info(bft_ledger);` and verify presence of `git_commit_hash`.
2. **Execute Test Suite**:
   `pytest tests/test_bft_resilience.py cortex/bft_orchestrator_test.py`
3. **Run Zero-Trust Simulation Detector**:
   `python3 scripts/detect_sim.py ANERGY_TOKEN_PURGE_REPORT.md --strict`
4. **Invalidation Conditions**:
   - Any commit hash in `bft_ledger` truncated to less than 40 hexadecimal characters.
   - Any transaction committed to SQLite WAL without matching Git HEAD SHA.
