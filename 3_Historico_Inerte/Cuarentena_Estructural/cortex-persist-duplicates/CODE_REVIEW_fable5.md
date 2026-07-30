# babylon60 (cortex-persist v1.0.2) — Forensic Audit v2

Auditor: fable-5 · Date: 2026-07-07 · Scope: `babylon60/` + repo alerts · Depth: expanded (§5)

**Headline change vs v1:** the deeper pass found what a lint-clean surface hid — **two real
integrity breaks** that ruff can't see: a fact write that bypasses the entire guard/taint/encrypt
path, and a second `ledger_events` writer that doesn't chain `prev_hash`. Both are reachable in
production. v1's "mostly clean" verdict was correct about *style*; it was too generous about
*data-path integrity*. One v1 suspicion (`database/writer.py`) is now cleared as a false alarm.
Still not run here: pyright, pytest (absent in sandbox). Not exhaustive over 263k LOC.

---

## 1. audit_report

```yaml
audit_report:
  timestamp: "2026-07-07T00:00:00Z"
  target: "babylon60 v1.0.2"
  auditor: "fable-5-forensic"
  method: "ruff(project cfg)=clean + AST scans + full INSERT-path trace + repo alert files"
  not_run: ["pyright (absent)", "pytest (absent)"]
  exhaustive: false
  total_findings: 9
  by_severity: { P0: 0, CRITICAL: 2, HIGH: 2, MEDIUM: 2, LOW: 3 }
  findings:
    - id: "FIND-001"
      severity: "CRITICAL"
      file: "babylon60/swarm/state_store.py"
      line: 170
      invariant_violated: "§2.1 Validation-First · §2.5 Encryption-at-Rest · §2.7 CORTEX-TAINT"
      description: >
        Epistemic-loop closure writes a fact via a raw `INSERT INTO facts` that deliberately
        bypasses insert_fact_record ("bypass engine indexes for speed"). Result: no OSINT/Secret/
        MemoryFirewall guards, no taint token, and content is stored as PLAINTEXT
        model_dump_json() instead of enc.encrypt_str(). Any untrusted signal.payload persists
        unguarded, unencrypted, untainted — taint-laundering by construction.
      current_code: |
        # Directly inject into raw epistemological stream (bypass engine indexes for speed ...)
        await self._db.execute(
            "INSERT INTO facts (tenant_id, project, content, fact_type, confidence, source, metadata, is_tombstoned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("default", "global", raw_ev.model_dump_json(), "raw_evidence", "C5-REAL",
             f"sanedrin:{signal.agent_id}", "{}", 0),
        )
      fixed_code: |
        # Route through the guarded write path (guards + taint + AES-GCM + ledger).
        from babylon60.engine.core.fact_store_core import insert_fact_record
        await insert_fact_record(
            self._db, tenant_id="default", project="global",
            content=raw_ev.model_dump_json(), fact_type="raw_evidence",
            tags=None, confidence="C5-REAL", ts=None,
            source=f"sanedrin:{signal.agent_id}", meta={}, tx_id=None,
        )  # taint auto-resolved/enforced; content encrypted at rest

    - id: "FIND-002"
      severity: "CRITICAL"
      file: "babylon60/ledger/billing_gateway.py"
      line: 55
      invariant_violated: "§2.2 Ledger Continuity (SHA-256 hash-chain)"
      description: >
        append_billing_event() inserts into ledger_events with db_path defaulting to DB_PATH —
        the SAME table the master LedgerWriter chains — but writes NO prev_hash/hash. LedgerWriter
        .append computes prev_hash from `SELECT hash ... ORDER BY rowid DESC LIMIT 1`; a Stripe
        webhook landing between two appends makes that read return NULL, so the next real event
        chains off NULL and verify_chain() fails. Unchained rows are also individually
        unverifiable. Two writers, one chain, no coordination.
      current_code: |
        INSERT INTO ledger_events (event_id, ts, tool, actor, action, payload_json, semantic_status)
        VALUES (?, ?, ?, ?, ?, ?, 'pending')
      fixed_code: |
        # Chain like LedgerWriter, OR write to a dedicated billing table. Minimal in-place chain:
        cur = await conn.execute("SELECT hash FROM ledger_events ORDER BY rowid DESC LIMIT 1")
        row = await cur.fetchone()
        prev_hash = row[0] if row and row[0] else "GENESIS"
        new_hash = _sha256_chain(prev_hash, event_id, ts, payload_json)  # same fn as LedgerEvent
        await conn.execute(
            "INSERT INTO ledger_events (event_id, ts, tool, actor, action, payload_json, prev_hash, hash, semantic_status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')",
            (event_id, ts, "billing_gateway", actor, event_type, payload_json, prev_hash, new_hash),
        )

    - id: "FIND-003"
      severity: "HIGH"
      file: "dependabot_alerts.json"
      line: 0
      invariant_violated: "§5.9 Dependency CVEs"
      description: >
        17 OPEN Dependabot alerts (6 HIGH / 4 MED / 7 LOW) on the Rust runtime/SDK. Notable:
        jsonwebtoken type-confusion (auth-bypass risk — critical for trust infra), multiple
        rust-openssl memory-safety HIGHs (OOB write in CipherCtxRef, digest_final past buffer,
        AES key-wrap bounds, X509 UB), rustls-webpki DoS via malformed CRL, ring AES panic.
      current_code: |
        # Cargo.lock pins with known advisories (rust-openssl, rustls-webpki, jsonwebtoken, ring, rand, lru)
      fixed_code: |
        # cargo update -p openssl rustls-webpki jsonwebtoken ring rand lru
        # then `cargo audit` must be clean; pin to patched minors in Cargo.toml

    - id: "FIND-004"
      severity: "HIGH"
      file: "babylon60/cli/memory_cmds.py"
      line: 63
      invariant_violated: "§2.7 CORTEX-TAINT (fail-open)"
      description: >
        Taint-token failure sets os.environ["CORTEX_NO_TAINT_ENFORCE"]="1" PROCESS-WIDE (also
        line 66 when no key exists), disabling SAGA-1 taint for every later write. A transient
        hiccup permanently downgrades enforcement. Fail-open where it must fail-closed (or skip
        only the current op).
      current_code: |
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to generate taint token: {e}[/]")
            os.environ["CORTEX_NO_TAINT_ENFORCE"] = "1"
      fixed_code: |
        except (ValueError, OSError, RuntimeError) as e:
            console.print(f"[yellow]Warning: taint token unavailable for this op: {e}[/]")
            meta["_taint_skipped_reason"] = str(e)  # per-op only; never flip global state

    - id: "FIND-005"
      severity: "MEDIUM"
      file: "babylon60/engine/flow/saga_protocol.py"
      line: 184
      invariant_violated: "§2.8 SAGA — abstraction drift / dead-ish scaffold"
      description: >
        SagaOrchestrator is exported + used in tests, but db_exec returns hard-coded "tx_123",
        ledger_exec never appends, index_exec is empty. Reads like the canonical write path yet
        persists nothing; real path is fact_store_core. Risk: a future caller wires into the stub
        (see FIND-001 for how bypasses happen). Mark reference-only or make steps delegate.
      current_code: |
        async def db_exec(ctx): ctx["db_tx_id"] = "tx_123"
      fixed_code: |
        async def db_exec(ctx):
            raise NotImplementedError("reference contract; real writes go through fact_store_core")

    - id: "FIND-006"
      severity: "MEDIUM"
      file: "babylon60/ledger/writer.py"
      line: 64
      invariant_violated: "§5.4 anchoring integrity"
      description: >
        _async_anchor wraps the raw b64 pubkey in PEM headers; the comment admits it is not real
        PEM. Runs in a background thread under broad except, so a bad PEM silently drops the Rekor
        transparency-log anchor while the product advertises external attestation.
      current_code: |
        pem = f"-----BEGIN PUBLIC KEY-----\n{keypair.public_key_b64}\n-----END PUBLIC KEY-----"
      fixed_code: |
        pem = _spki_pem_from_b64(keypair.public_key_b64)  # proper DER SPKI -> PEM, raises on bad key

    - id: "FIND-007"
      severity: "LOW"
      file: "babylon60/engine/flow/saga_protocol.py"
      line: 7
      invariant_violated: "§3 hygiene"
      description: 'Inert `# noqa: intruder` ("intruder" is no ruff code) — also genesis.py:16, sandbox_jit.py:5. Suppresses nothing; delete.'
      current_code: "# noqa: intruder"
      fixed_code: "(removed)"

    - id: "FIND-008"
      severity: "LOW"
      file: "babylon60/core/config.py"
      line: 1
      invariant_violated: "§3 import * / missing __all__"
      description: "config.py shim does `from core.config import *`; core/config.py defines no __all__, so the whole public surface leaks. Bound it."
      current_code: "# no __all__ in core/config.py"
      fixed_code: "__all__ = [ ...explicit names... ]"

    - id: "FIND-009"
      severity: "LOW"
      file: "babylon60/engine/core/cost_scheduler.py"
      line: 219
      invariant_violated: "§3 float in financial var"
      description: "Token-cost `float(max_tokens)/1000.0*0.01` — Decimal only if it feeds billing; other float scores are ranking heuristics, leave as-is."
      current_code: "return float(max_tokens) / 1000.0 * 0.01"
      fixed_code: 'return Decimal(max_tokens) / Decimal(1000) * Decimal("0.01")  # if billing-facing'
```

---

## 2. Verified negatives & cleared alarms

```yaml
verified_negatives:
  - { check: "time.sleep() in async def", method: "async-aware AST, whole pkg", result: "0" }
  - { check: "naked print() in engine/memory/guards/crypto/ledger/audit/core", result: "0" }
  - { check: "ruff E,F,W,I,UP,B,G,TID (project cfg)", result: "exit 0 clean" }
  - { check: "key material in logs/repr/json", method: "grep priv/secret/aes/master key + log/print/repr/dumps", result: "none leaked; only crypto/shredder HKDF info-string, benign" }
  - { check: "SQL injection via f-string", result: "no user input reaches an f-string; PRAGMA-constants / allowlisted identifiers / ?-bound values" }
  - { check: "master LedgerWriter.append prev_hash", result: "correct (GENESIS fallback + compute_hash(prev)) — but see FIND-002 second writer" }
cleared_false_alarms:
  - file: "babylon60/database/writer.py"
    note: "The `INSERT INTO facts (project, content)` is docstring EXAMPLE text (Usage block), not a code path. Worker is a generic serialized SQL executor. Not a guard bypass."
could_not_verify:
  - "pyright / pytest: absent in sandbox — gates NOT run"
  - "guards/ crypto/ audit/ test coverage depth (§5.10) — not measured without pytest"
  - "full migrate.py <-> live schema drift (§5.7) — 21 migrations present, not diffed vs a DB"
```

---

## 3. Executable diffs (CRITICAL/HIGH)

```diff
--- a/babylon60/swarm/state_store.py
+++ b/babylon60/swarm/state_store.py
@@ -166,13 +166,12 @@
-                                # Directly inject into raw epistemological stream (bypass engine indexes for speed, rely on async consolidators)
-                                await self._db.execute(
-                                    "INSERT INTO facts (tenant_id, project, content, fact_type, confidence, source, metadata, is_tombstoned) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
-                                    (
-                                        "default", "global", raw_ev.model_dump_json(),
-                                        "raw_evidence", "C5-REAL",
-                                        f"sanedrin:{signal.agent_id}", "{}", 0,
-                                    ),
-                                )
+                                # Route through the guarded write path: guards + taint + AES-GCM + ledger.
+                                from babylon60.engine.core.fact_store_core import insert_fact_record
+                                await insert_fact_record(
+                                    self._db, tenant_id="default", project="global",
+                                    content=raw_ev.model_dump_json(), fact_type="raw_evidence",
+                                    tags=None, confidence="C5-REAL", ts=None,
+                                    source=f"sanedrin:{signal.agent_id}", meta={}, tx_id=None,
+                                )
```

```diff
--- a/babylon60/ledger/billing_gateway.py
+++ b/babylon60/ledger/billing_gateway.py
@@ -52,9 +52,15 @@
         async with connect_async_ctx(self.db_path) as conn:
+            cur = await conn.execute("SELECT hash FROM ledger_events ORDER BY rowid DESC LIMIT 1")
+            row = await cur.fetchone()
+            prev_hash = row[0] if row and row[0] else "GENESIS"
+            new_hash = LedgerEvent.chain_hash(prev_hash, event_id, ts, "billing_gateway", actor, event_type, payload_json)
             await conn.execute(
                 """
-                INSERT INTO ledger_events (event_id, ts, tool, actor, action, payload_json, semantic_status)
-                VALUES (?, ?, ?, ?, ?, ?, 'pending')
+                INSERT INTO ledger_events (event_id, ts, tool, actor, action, payload_json, prev_hash, hash, semantic_status)
+                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
                 """,
-                (event_id, ts, "billing_gateway", actor, event_type, payload_json),
+                (event_id, ts, "billing_gateway", actor, event_type, payload_json, prev_hash, new_hash),
             )
             await conn.commit()
```

```diff
--- a/babylon60/cli/memory_cmds.py
+++ b/babylon60/cli/memory_cmds.py
@@ -59,6 +59,6 @@
-        except Exception as e:
-            from babylon60.cli.common import console
-            console.print(f"[yellow]Warning: Failed to generate taint token: {e}[/]")
-            os.environ["CORTEX_NO_TAINT_ENFORCE"] = "1"
+        except (ValueError, OSError, RuntimeError) as e:
+            from babylon60.cli.common import console
+            console.print(f"[yellow]Warning: taint token unavailable for this op: {e}[/]")
+            meta["_taint_skipped_reason"] = str(e)
```

> Apply-order caveats: FIND-001 needs `insert_fact_record` to accept the `self._db` aiosqlite conn
> (it does) and will now enforce taint — if the swarm loop runs without a provisioned key it will
> raise instead of silently persisting; that is the intended behavior change. FIND-002 references a
> `LedgerEvent.chain_hash` helper — if the real hash fn has a different signature, match it exactly
> so billing rows verify under the same `verify_chain()`. Both change security semantics: review,
> don't blind-apply.

---

## 4. Verification

```bash
ruff check babylon60/ --fix                 # already clean; keeps it clean
pyright babylon60/                          # NOT run here — run locally
pytest tests/ -v --timeout=30               # NOT run here; FIND-001/002/005 will move tests
python -c "from babylon60.ledger.verifier import verify_chain; verify_chain()"  # must pass AFTER FIND-002
cargo audit --file sdks/rust/Cargo.lock     # must be clean AFTER FIND-003
```

---

## 5. summary_metrics

```yaml
summary_metrics:
  verdict: "NOT CLEAN — 2 CRITICAL data-integrity breaks reachable in production"
  total_files_modified_by_diffs: 3
  total_lines_changed: ~28
  p0_resolved: 0/0
  critical_resolved: 0/2        # diffs provided, NOT auto-applied to your repo
  high_resolved: 0/2
  biggest_risks:
    - "FIND-001: unguarded/unencrypted/untainted fact write in swarm epistemic loop"
    - "FIND-002: Stripe webhook can poison the master ledger hash-chain (prev_hash=NULL)"
  estimated_test_impact: >
    FIND-001 makes swarm evidence writes require taint (may fail keyless test envs — set
    CORTEX_NO_TAINT_ENFORCE=1 in test fixtures). FIND-002 changes billing row schema usage;
    add a verify_chain() test with an interleaved billing event. FIND-005 NotImplementedError
    breaks p0_singularity_test if it drives db_exec. Net new coverage recommended: guards on
    swarm path, chain-continuity across writers.
  applied: 0
```
