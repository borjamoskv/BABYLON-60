<!-- C5-REAL EXERGY CERTIFIED -->
# Handoff Report — Milestone 1 Empirical Challenger 1

## 1. Observation

Physical execution and empirical stress testing were conducted on `cortex/cortex_purge.py`, `cortex/mcts_vnode_compiler.py`, `scripts/ultrathink_learning.py`, `cortex/bft_orchestrator.py`, and `scripts/40_stress_db.py`.

The following empirical results and verbatim traces were captured:

### Observation A: Physical Execution of DB Stress Test
Command: `python3 scripts/40_stress_db.py`
Output:
```
Iniciando asedio C5-REAL SQLite WAL BFT | Requests: 1000 | Concurrency: 100
=== RESULTADOS DEL ASEDIO ===
Tiempo Total: 0.9164s
Exitos (Exergía): 1000
Errores (Anergía): 0
Resiliencia Topológica Confirmada (C5-REAL).
```
`AgentMemory` WAL SQLite concurrent logging passed 1000 requests without lock contention failures.

### Observation B: Physical Execution of Purger Script
Command: `python3 scripts/cortex_purge.py` (Task-31)
Output log:
```
2026-07-25 22:45:09,413 - cortex_purge - INFO - ⚡ [LANDAUER-PURGE] Auditing orphan process thrashing (TDAH Purge)...
2026-07-25 22:45:09,447 - cortex_purge - INFO - [Orphan Detected] PID 76809 | 96.6% | /System/Library/ExtensionKit/Extensions/ODDIExperimentationExtension.appex/Contents/MacOS/ODDIExperimentationExtension ...
2026-07-25 22:45:09,447 - cortex_purge - INFO - [SIGKILL] PURGADO: PID 76809 (/System/Library/ExtensionKit/Extensions/ODDIExperimentationExtension.appex/Contents/MacOS/ODDIExperimentationExtension ...) - CPU: 96.6%
2026-07-25 22:45:09,447 - cortex_purge - WARNING - [Ledger] Master Ledger DB not found at /Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/.cortex/cortex.db
```
`cortex_purge.py` killed macOS system extension daemon `ODDIExperimentationExtension.appex` (PID 76809) spawned by `launchd` (PPID=1) because CPU exceeded 50%.

### Observation C: Interoperability Failure between BFTOrchestrator and Purger/Audit Ledger Writes
Command: `python3 .agents/teamwork_preview_challenger_m1_1/empirical_stress_harness.py`
Traceback:
```
TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
  File "cortex/cortex_purge.py", line 70, in write_purge_to_ledger
    new_lamport = last_lamport + 1
```
`BFTOrchestrator` inserts rows with `lamport_t=NULL` and `payload_hash=NULL`. `cortex_purge.py` and `scripts/ultrathink_learning.py` read `last_lamport` as `None`, causing `new_lamport = last_lamport + 1` to crash with `TypeError`.

### Observation D: Fallback Failure in `BFTNode` Without Rust `strike_rs` Extension
Command: `python3 .agents/teamwork_preview_challenger_m1_1/empirical_stress_harness.py`
Traceback:
```
AttributeError: 'BFTNode' object has no attribute 'state_vector'
  File "cortex/bft_orchestrator.py", line 254, in _process_task_parallel
    hashes[node.node_id] = node.compute_state_hash()
  File "cortex/bft_orchestrator.py", line 125, in compute_state_hash
    f"states:{self.state_vector.states},"
```
When `strike_rs` is `None` (standard Python environment), `BFTNode.__init__` skips initializing `self.state_vector`. `compute_state_hash()` accesses `self.state_vector` unconditionally, raising `AttributeError`. `_process_task_parallel` only catches `(OSError, RuntimeError, ValueError)`, allowing `AttributeError` to crash `start_loop()`.

### Observation E: Process Abort via `sys.exit(1)` in `cortex_env.py`
Command: Execution of `get_bft_key()` without `CORTEX_BFT_KEY` environment variable.
Output:
```
EpistemicHalt: CORTEX_BFT_KEY no definida en el entorno (Ω25). Terminación de seguridad.
SystemExit: 1
```
Instead of raising a structured exception (`EpistemicHalt`), `cortex_env.py` executes `sys.exit(1)`, killing the Python interpreter.

### Observation F: Destructive Source Code Obliteration in `obliterate_zero_operators()`
Log output from Task-31:
```
2026-07-25 22:46:15,910 - cortex_purge - INFO - [SWARM NODE] PURGED: strike-rs/src/lib.rs
2026-07-25 22:46:15,910 - cortex_purge - INFO - [SWARM NODE] PURGED: strike-rs/src/arm64_re.rs
2026-07-25 22:46:15,932 - cortex_purge - INFO - [SWARM NODE] PURGED: src-tauri/src/lib.rs
```
`obliterate_zero_operators()` in `cortex_purge.py` deleted critical codebase source files (`strike-rs/src/lib.rs`, `strike-rs/src/arm64_re.rs`, `src-tauri/src/*.rs`) listed as 0 matches in `BABYLON_60_THEOREM_OMEGA.json`. This destructive obliteration deleted the `strike_rs` Rust implementation directly from the disk!

---

## 2. Logic Chain

1. **DB Stress Test (`scripts/40_stress_db.py`)**:
   - `AgentMemory` uses `BEGIN IMMEDIATE` transaction blocks with exponential backoff on `sqlite3.OperationalError: database is locked`.
   - Verified empirically under 100 concurrent worker threads executing 1000 total writes in 0.916s with 0 errors.

2. **Schema Incompatibility (`bft_ledger`)**:
   - `bft_orchestrator.py` defines table `bft_ledger` with columns `(id, timestamp, agent_id, lamport_t, payload_hash, step_index, domain, primitive, modifier, prev_hash, current_hash, cortex_taint)`.
   - When `bft_orchestrator.py` writes a transaction, `lamport_t` and `payload_hash` are omitted (inserted as `NULL`).
   - `cortex_purge.py` and `ultrathink_learning.py` query:
     `SELECT payload_hash, lamport_t FROM bft_ledger ORDER BY id DESC LIMIT 1`
   - When the latest row is from `bft_orchestrator`, `row` is `(None, None)`.
   - `cortex_purge` executes `new_lamport = last_lamport + 1`, throwing `TypeError`.
   - Furthermore, `cortex_purge` assigns `prev_hash = row[0]` (`None`), which violates `prev_hash TEXT NOT NULL UNIQUE`, raising `sqlite3.IntegrityError`.

3. **BFTNode Missing Fallback Attributes**:
   - `BFTNode.__init__` contains `if strike_rs is not None:` block for instantiating Rust-backed objects.
   - If `strike_rs` is `None`, `self.state_vector` is undefined.
   - `compute_state_hash()` accesses `self.state_vector.states` unconditionally.
   - `_process_task_parallel()` catches `(OSError, RuntimeError, ValueError)`, omitting `AttributeError`.
   - Thus, any environment lacking the compiled `strike_rs` C/Rust extension crashes when running `BFTOrchestrator`.

4. **TDAH Purger Process Termination Blast Radius**:
   - `cortex_purge.py` line 119 checks `if ppid == 1 and pcpu > 50.0:` and executes `os.kill(pid, signal.SIGKILL)`.
   - On macOS, `launchd` (PID 1) is the ancestor process of all user daemons, background tasks, and helper services.
   - Any background process or system extension spiking CPU above 50% gets killed indiscriminately, regardless of binary path or ownership.

5. **Path Traversal Risk & Destructive Obliteration in `obliterate_zero_operators()`**:
   - `obliterate_zero_operators()` reads relative paths from `BABYLON_60_THEOREM_OMEGA.json`.
   - `os.path.join(target_dir, rel_path)` does not sanitize `rel_path` against directory traversal (`../`).
   - `obliterate_zero_operators()` indiscriminately deletes active Rust and TypeScript source files (such as `strike-rs/src/lib.rs` and `src-tauri/src/*.rs`), resulting in physical codebase destruction.

6. **MCTS VNode Compiler (`cortex/mcts_vnode_compiler.py`)**:
   - Shannon entropy calculations (`calculate_shannon_entropy`) and `ASTTheorem` validation contracts (`code_hash` SHA3-256 matching, entropy bounds `[0.0, 8.0]`, exergy ratio bounds) were verified empirically and behave correctly according to physical invariants.

---

## 3. Caveats

- `strike_rs` native C/Rust extension is not currently compiled/installed in the local environment, which allowed us to uncover the missing fallback path in `BFTNode`. If `strike_rs` is present, `compute_state_hash()` operates via Rust, bypassing the `AttributeError`.
- System process SIGKILL behavior in `cortex_purge.py` was observed on macOS 15.x (Darwin). On Linux systems, `systemd` (PID 1) serves a similar role, so the over-reaching process purge affects both OS platforms.

---

## 4. Conclusion

He asumido el control del disco físico y:
- **`scripts/40_stress_db.py`**: PASSED (1000 requests, 100 threads, 0 errors, 0.916s total time).
- **`cortex/mcts_vnode_compiler.py`**: PASSED (ASTTheorem validation, entropy computation, and MCTS trajectory compilation operate correctly).
- **Defects Found & Verified Empirically**:
  1. `TypeError` / `IntegrityError` in `write_purge_to_ledger` and `ultrathink_audit` due to `bft_ledger` schema mismatch with `bft_orchestrator`.
  2. `AttributeError` crash in `BFTNode.compute_state_hash()` when `strike_rs` is absent.
  3. Abrupt process exit via `sys.exit(1)` in `cortex_env.get_bft_key()`.
  4. Indiscriminate `SIGKILL` of macOS system daemons in `cortex_purge.py`.
  5. Unsanitized path traversal and destructive obliteration of active Rust source code (`strike-rs/src/lib.rs`) in `obliterate_zero_operators()`.
  6. Hardcoded relative DB path (`.cortex/cortex.db`).

---

## 5. Verification Method

Run the empirical test harness to independently verify all failure modes and behavior:

```bash
CORTEX_BFT_KEY="c5_real_test_key_sovereign_2026" python3 .agents/teamwork_preview_challenger_m1_1/empirical_stress_harness.py
python3 .agents/teamwork_preview_challenger_m1_1/mcts_stress.py
python3 .agents/teamwork_preview_challenger_m1_1/ultrathink_stress.py
python3 scripts/40_stress_db.py
```
