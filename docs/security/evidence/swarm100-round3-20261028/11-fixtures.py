"""Read current source, execute isolated stdlib fixtures; never start product runtime."""
from __future__ import annotations

import ast
import contextlib
import io
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
from typing import cast

ROOT = Path(__file__).absolute().parents[4]
RESULTS = []


def tree(path):
    return ast.parse((ROOT / path).read_text())


def node_named(nodes, name):
    return next(n for n in nodes if getattr(n, "name", None) == name)


def run_nodes(nodes, namespace, path, optimize=0):
    nodes = [n for n in nodes if not (isinstance(n, ast.ImportFrom) and n.module == "__future__")]
    module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0), *nodes], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), path, "exec", optimize=optimize), namespace)


def record(candidate, scope, observed):
    RESULTS.append({"candidate_id": candidate, "scope": scope, "observed": observed})


# Exact current revocation closure SQL, synthetic in-memory chain only.
p = "01_KISH_ENGINE/babylon60/memory/governance.py"
cls = node_named(tree(p).body, "MemoryGovernanceEngine")
revoke = node_named(cls.body, "revoke_record")
sql = next(n.value for n in ast.walk(revoke) if isinstance(n, ast.Constant) and isinstance(n.value, str) and "WITH RECURSIVE closure" in n.value)
with sqlite3.connect(":memory:") as conn:
    conn.execute("CREATE TABLE cortex_memory_edges (parent_id TEXT, child_id TEXT, edge_kind TEXT)")
    conn.executemany("INSERT INTO cortex_memory_edges VALUES (?, ?, 'DEPENDS_ON')", [(str(i), str(i+1)) for i in range(1026)])
    rows = conn.execute(sql, ("0",)).fetchall()
    ids = {int(row[0]) for row in rows}
    assert len(ids) == 1025 and max(ids) == 1024 and 1026 not in ids
    record("SW100-C0186", "Current SQL query over an isolated 1026-edge fixture; no governance engine or ledger started", {"chain_nodes": 1027, "selected_nodes": len(ids), "highest_selected_depth": max(ids)})

# Current acceptance statement, executed with Python optimizer off/on.
p = "01_KISH_ENGINE/babylon60/cli/onco_transducer.py"
pipeline = node_named(tree(p).body, "execute_pipeline")
assertion = next(n for n in pipeline.body if isinstance(n, ast.Assert))
outcomes = {}
for optimize in (0, 1):
    ns = {"delta": 0.0, "falsifiability_threshold": 40.0}
    try:
        run_nodes([assertion], ns, p, optimize)
        outcomes[str(optimize)] = "no rejection"
    except AssertionError:
        outcomes[str(optimize)] = "AssertionError"
assert outcomes == {"0": "AssertionError", "1": "no rejection"}
record("SW100-C0541", "Current assert AST only; no biological model, graph, data or CLI run", outcomes)

# Same SQLite lexical predicate as example, with a fixed clock for repeatability.
with sqlite3.connect(":memory:") as conn:
    lexical, normalized = conn.execute("SELECT ? > ?, datetime(?) > datetime(?)", ("2026-10-28T08:00:00.000Z", "2026-10-28 09:00:00", "2026-10-28T08:00:00.000Z", "2026-10-28 09:00:00")).fetchone()
    assert (lexical, normalized) == (1, 0)
    record("SW100-C0580", "SQLite in-memory comparison with a fixed clock; no Cloudflare service used", {"text_predicate_accepts_expired": bool(lexical), "normalized_predicate_accepts_expired": bool(normalized)})

# Execute current parser and argument conversion methods without constructor or runtime.
p = "01_KISH_ENGINE/babylon60/mcp/cortex_mcp_server.py"
cls = node_named(tree(p).body, "CortexMCPServer")
methods = [node_named(cls.body, name) for name in ("_read_message", "_tool_query_ledger")]
ns = {"json": json, "sys": sys, "cast": cast}
run_nodes(methods, ns, p)
errors = []
for method, arg in (("_read_message", io.StringIO("{broken\n")), ("_tool_query_ledger", {"limit": "invalid"})):
    try:
        ns[method](None, arg)
    except (ValueError, json.JSONDecodeError) as exc:
        errors.append(type(exc).__name__)
assert errors == ["JSONDecodeError", "ValueError"]
record("SW100-C0149", "Current two method ASTs without CortexMCPServer construction, stdio loop, authorization gate, or DB access", errors)

# Current synchronizer runs only against a temporary synthetic repository.
p = "scripts/c5_quality_gates/sync_version.py"
ns = {"__file__": str(ROOT / p), "__name__": "isolated_review_fixture"}
run_nodes(tree(p).body, ns, p)
with tempfile.TemporaryDirectory(prefix="b60-review11-") as temp:
    fake = Path(temp)
    (fake / "babylon.toml").write_text('[release]\nversion = "1.2.3"\nlicense-file = "LICENSE"\n')
    (fake / "LICENSE").write_text("Fixture only\n")
    ns["REPO_ROOT"] = fake
    capture = io.StringIO()
    with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
        result = ns["sync_all"](dry_run=False)
    assert result is True and capture.getvalue().count("Missing target file") == 4
    record("SW100-C0225", "Current synchronizer functions against a temporary fixture containing only babylon.toml and LICENSE", {"result": result, "missing_required_targets": 4, "output": capture.getvalue()})

# Exact current generator loop body, manually bounded; engine import omitted.
p = "scripts/c5_thermo/cache_1000_memoization_bench.py"
t = tree(p)
vocab = next(n for n in t.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name) and n.target.id == "VOCAB")
loop = next(n for n in node_named(t.body, "main").body if isinstance(n, ast.While))
ns = {"VOCAB": ast.literal_eval(vocab.value), "unique_queries": set()}
for iteration in range(1000):
    before = len(ns["unique_queries"])
    run_nodes(loop.body, ns, p)
    if len(ns["unique_queries"]) == before:
        break
assert iteration == 282 and len(ns["unique_queries"]) == 282
record("SW100-C0447", "Exact current loop body with a bounded harness; CortexInferenceEngine never imported or constructed", {"vocabulary_size": len(ns["VOCAB"]), "unique_queries_at_first_stall": len(ns["unique_queries"]), "first_stalled_iteration_zero_based": iteration})

output = Path(__file__).with_name("11-fixtures.json")
output.write_text(json.dumps({"scope": "isolated source/stdlib fixtures; not protected runtime validation", "results": RESULTS}, ensure_ascii=False, indent=2) + "\n")
print(json.dumps({"fixtures_passed": len(RESULTS), "output": str(output)}, indent=2))
