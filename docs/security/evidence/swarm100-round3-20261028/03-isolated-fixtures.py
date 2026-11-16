"""Source-isolated checks: no product imports, native gates, network, or operator data.

Run from repository root with Python 3. The only output is synthetic JSON to stdout.
AST extraction executes selected Python functions with controlled standard-library
dependencies. Models and injected failures are explicitly labeled below.
"""

import ast
import contextlib
import ctypes
import dataclasses
import hashlib
import io
import json
import logging
import re
import sqlite3
import subprocess
import types
from pathlib import Path


def select(path, names, namespace):
    source = ast.parse(Path(path).read_text(encoding="utf-8"), filename=path)
    nodes = [n for n in source.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in nodes} == set(names)
    future = ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)
    module = ast.fix_missing_locations(ast.Module(body=[future, *nodes], type_ignores=[]))
    exec(compile(module, path, "exec"), namespace)
    return namespace


results = []

exergy = "scripts/c5_thermo/exergy_arbitrage_engine.py"
ns = select(exergy, ["extract_ast", "verify_ast_syntax"], {"re": re, "json": json})
code, count = ns["extract_ast"]("```python\nx = 1\n```")
with contextlib.redirect_stdout(io.StringIO()):
    valid = ns["verify_ast_syntax"](code, "fixture.py")
assert code.startswith("```python") and not valid
results.append({"candidate_id": "SW100-C0457", "kind": "isolated_source_function", "fences_retained": True, "syntax_valid": valid, "lines": count})

socint = "tools/skill_library/global/c5-socint-extraction-suite/scripts/socint_extract.py"
ns = select(socint, ["compute_merkle_root"], {"json": json})
first = ns["compute_merkle_root"]({"author": "alice", "text": "hello"})
swapped = ns["compute_merkle_root"]({"author": "hello", "text": "alice"})
renamed = ns["compute_merkle_root"]({"other": "alice", "renamed": "hello"})
assert first == swapped == renamed
results.append({"candidate_id": "SW100-C0501", "kind": "isolated_source_function", "swapped_and_renamed_fields_same_root": True, "root": first})

conformal = "01_KISH_ENGINE/babylon60/attestation/conformal_tree.py"
function = next(n for n in ast.parse(Path(conformal).read_text()).body if isinstance(n, ast.FunctionDef) and n.name == "compute_claim_leaf_hash")
preimage_expr = next(n.value for n in function.body if isinstance(n, ast.Assign))
expr = compile(ast.Expression(body=preimage_expr), conformal, "eval")
common = {"domain": "example", "payload_hash": "p", "attestation_merkle_root": "r"}
a = eval(expr, {**common, "claim_id": "a:b", "advisory_id": "c"})
b = eval(expr, {**common, "claim_id": "a", "advisory_id": "b:c"})
assert a == b
results.append({"candidate_id": "SW100-C0272", "kind": "source_preimage_expression", "distinct_fields_identical_preimage": True, "preimage": a})

grounding = "01_KISH_ENGINE/babylon60/kernel/grounding_interceptor.py"
namespace = {"__name__": "__main__", "contextlib": contextlib, "dataclasses": dataclasses, "hashlib": hashlib, "json": json, "re": re, "sqlite3": sqlite3, "logger": logging.getLogger("isolated-fixture"), "EMPTY_SHA256": hashlib.sha256(b"").hexdigest()}
ns = select(grounding, ["UnverifiedGroundingError", "SyntheticPlaceholderError", "EvidenceRecord", "InterceptResult", "GroundingRegistry", "GroundingInterceptor"], namespace)
record = ns["EvidenceRecord"]("DOI", "10.1234/fixture", "a" * 64, "fixture", "fixture", "2000-01-01", "REVOKED")
registry = ns["GroundingRegistry"]()
registry.register(record)
verdict = ns["GroundingInterceptor"](registry).intercept("10.1234/fixture", "STRICT_ABORT")
assert verdict.status == "COMMITTED" and verdict.verified_citations[0].status == "REVOKED"
results.append({"candidate_id": "SW100-C0074", "kind": "isolated_source_classes", "record_status": "REVOKED", "intercept_status": verdict.status, "verified_count": len(verdict.verified_citations)})

registry = ns["GroundingRegistry"]()
registry._db_path = "unused-fixture-path"
def fail_connect(*args, **kwargs):
    raise sqlite3.OperationalError("injected fixture failure; no database opened")
ns["sqlite3"] = types.SimpleNamespace(connect=fail_connect)
failed = False
try:
    registry.register(record)
except sqlite3.OperationalError:
    failed = True
assert failed and registry.lookup("DOI", "10.1234/fixture") is record
results.append({"candidate_id": "SW100-C0075", "kind": "isolated_source_class_with_injected_connect_failure", "registration_raised": True, "record_still_cached": True, "database_opened": False})

mail = "01_KISH_ENGINE/babylon60/transducers/c5_mail_transducer.py"
def fail_curl(cmd, **kwargs):
    raise subprocess.CalledProcessError(7, cmd, stderr="")
ns = select(mail, ["C5MailTransducer"], {"json": json, "subprocess": types.SimpleNamespace(run=fail_curl, CalledProcessError=subprocess.CalledProcessError)})
transducer = ns["C5MailTransducer"](api_key="SYNTHETIC_FIXTURE_TOKEN")
answer = transducer.dispatch(["recipient@example.invalid"], "fixture", "fixture")
assert "SYNTHETIC_FIXTURE_TOKEN" in answer["detail"]
results.append({"candidate_id": "SW100-C0373", "kind": "isolated_source_class_with_injected_curl_failure", "synthetic_token_in_error_detail": True, "network_executed": False, "keychain_read": False})

tamkarum = "tools/tamkarum_attestation_engine.py"
payload = {"git_commit": "arbitrary-edited-value", "agent_topology": {"topology_sha256": "t"}, "outreach_campaigns": {"global_merkle_root": "o"}, "social_dissemination": {"calendar_sha256": "c"}, "eu_ai_act_compliance": {"evidence_pack_sha256": "e"}}
payload["compound_attestation_hash"] = hashlib.sha256(b"arbitrary-edited-value:t:o:c:e").hexdigest()
class SyntheticPath:
    def exists(self):
        return True
    def read_text(self, **kwargs):
        return json.dumps({"payload": payload})
ns = select(tamkarum, ["verify_attestation"], {"json": json, "hashlib": hashlib, "ATTESTATION_STATEMENT_PATH": SyntheticPath()})
with contextlib.redirect_stdout(io.StringIO()):
    accepted = ns["verify_attestation"]()
assert accepted
results.append({"candidate_id": "SW100-C0420", "kind": "isolated_source_function_with_synthetic_statement", "editable_self_checksum_accepted": accepted, "source_artifacts_read": False})

seqlock = "02_EDIN_SWARMS/agents_archi/orchestrator/seqlock_swarm_ring0.py"
ns = select(seqlock, ["SwarmTransitionManifest"], {"ctypes": ctypes})
manifest = ns["SwarmTransitionManifest"]()
digest = b"abc\x00defghijklmno"
assert len(digest) == 16
manifest.payload_hash = digest
returned = bytes(manifest.payload_hash)
assert returned == b"abc"
results.append({"candidate_id": "SW100-C0535", "kind": "isolated_source_structure_in_local_memory", "stored_input_length": len(digest), "returned_length": len(returned), "returned_hex": returned.hex(), "shared_memory_opened": False})

uri = "file:sw100_review03_snapshot_fixture?mode=memory&cache=shared"
reader = sqlite3.connect(uri, uri=True)
writer = sqlite3.connect(uri, uri=True)
writer.execute("CREATE TABLE entries (seq INTEGER, digest TEXT)")
writer.execute("INSERT INTO entries VALUES (1, 'a')")
writer.commit()
cursor = reader.execute("SELECT COUNT(*), MAX(seq) FROM entries")
head = cursor.fetchone()
writer.execute("INSERT INTO entries VALUES (2, 'b')")
writer.commit()
cursor = reader.execute("SELECT digest FROM entries ORDER BY seq")
leaves = cursor.fetchall()
assert head[0] == 1 and len(leaves) == 2 and not reader.in_transaction
reader.close()
writer.close()
results.append({"candidate_id": "SW100-C0431", "kind": "sqlite_in_memory_read_sequence_model", "aggregate_count_before": head[0], "leaf_count_after": len(leaves), "product_ledger_executed": False})

print(json.dumps({"scope": "Isolated Python source functions and explicit models only; no product/native runtime, protected effects, network, operator data, or repository source writes.", "checks": results}, indent=2))
