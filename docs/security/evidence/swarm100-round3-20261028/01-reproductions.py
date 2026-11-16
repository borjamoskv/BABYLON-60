"""Isolated source-extracted Python checks; no product entry points or external effects.

Run from repository root with python3 <this file>. JSON goes only to stdout.
This verifies the named in-memory behavior, not protected or deployed runtime.
"""
import ast
import asyncio
from dataclasses import asdict, dataclass, field
from enum import Enum
import hashlib
import json
import logging
from pathlib import Path
import re
import time
from typing import Any, Dict, Tuple

ROOT = Path(__file__).absolute().parents[4]
SOCINT = "tools/skill_library/global/c5-secops-infra-devtools/references/modules/c5-socint-extraction-suite/scripts/socint_extract.py"
results = {}


def extract(path, names):
    tree = ast.parse((ROOT / path).read_text())
    selected = [n for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and n.name in names]
    assert {n.name for n in selected} == set(names)
    # These stdlib dependencies are referenced by the extracted AST definitions.
    namespace = {
        "__name__": __name__,
        "asyncio": asyncio,
        "dataclass": dataclass,
        "field": field,
        "Enum": Enum,
        "hashlib": hashlib,
        "json": json,
        "re": re,
        "time": time,
        "Any": Any,
        "Dict": Dict,
        "Tuple": Tuple,
        "ActionTuple": Tuple[str, str | None, str | None],
        "logger": logging.getLogger("isolated-review-01"),
    }
    exec(compile(ast.Module(body=selected, type_ignores=[]), path, "exec"), namespace)
    return namespace


ns = extract(SOCINT, {"compute_merkle_root", "EpistemicClassifier"})
merkle = ns["compute_merkle_root"]
swapped = merkle({"author": "A", "text": "B"}) == merkle({"author": "B", "text": "A"})
renamed = merkle({"author": "A"}) == merkle({"text": "A"})
retyped = merkle({"value": 1}) == merkle({"value": "1"})
assert swapped and renamed and retyped
results["SW100-C0264"] = {"scope": "actual extracted pure function", "swapped_fields_same_digest": swapped, "renamed_field_same_digest": renamed, "scalar_type_change_same_digest": retyped}

classification = ns["EpistemicClassifier"].classify_text("RFC 9999 proves that two plus two equals five")
assert classification["counts"]["hechos_verificados"] == 1
results["SW100-C0270"] = {"scope": "actual extracted pure classifier", "input": "RFC 9999 proves that two plus two equals five", "counts": classification["counts"]}

tree = ast.parse((ROOT / SOCINT).read_text())
main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "main")
join = next(n.value for n in ast.walk(main) if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "final_output" for t in n.targets) and isinstance(n.value, ast.Call) and isinstance(n.value.func, ast.Attribute) and n.value.func.attr == "join")
batch_output = eval(compile(ast.Expression(join), SOCINT, "eval"), {"all_reports": [json.dumps({"id": "one"}), json.dumps({"id": "two"})]})
try:
    json.loads(batch_output)
except json.JSONDecodeError as exc:
    results["SW100-C0268"] = {"scope": "actual extracted final_output expression with two synthetic serialized reports", "parse_error": str(exc), "output": batch_output}
else:
    raise AssertionError("Expected invalid JSON for the batch")

ns = extract("01_KISH_ENGINE/babylon60/c5_telemetry.py", {"TelemetryEvent", "ThermodynamicValve"})


async def queue_check():
    valve = ns["ThermodynamicValve"]()
    valve.start()
    await valve.ingest("synthetic-test-event", 0.0)
    await valve.stop()
    assert valve.queue.qsize() == 1 and valve._worker_task is None
    return {"scope": "actual extracted classes, in-memory asyncio queue only", "pending_after_stop": valve.queue.qsize(), "worker_cleared": valve._worker_task is None}


results["SW100-C0466"] = asyncio.run(queue_check())
ns = extract("01_KISH_ENGINE/babylon60/genomics/hygiene.py", {"FASTASequenceValidator"})
sequence = ns["FASTASequenceValidator"].validate_sequence("synthetic", " \t\n ")
assert sequence["is_valid"] and sequence["length"] == 0
results["SW100-C0451"] = {"scope": "actual extracted pure validator", "result": sequence}

ns = extract("scripts/c5_cortex/poc_fl014_holdout.py", {"ExploitFamily", "PatchProposal", "DynamicExecutionResult", "BrokerAuditRecord", "Ring0BrokerGuard"})
patch = ns["PatchProposal"]("PATCH-0001", ns["ExploitFamily"].COMMAND_INJECTION, "synthetic", "synthetic", "synthetic", True, "synthetic diff", 0.0)
dynamic = ns["DynamicExecutionResult"]("PATCH-0002", False, None)
record = ns["Ring0BrokerGuard"]().enforce(patch, dynamic)
assert not record.artifact_mismatch_detected
results["SW100-C0519"] = {"scope": "actual extracted pure simulator; no real broker or effect", "patch_id": patch.patch_id, "dynamic_patch_id": dynamic.patch_id, "audit": asdict(record)}

ns = extract("scripts/c5_demos/falsacion_llm_gate.py", {"C5DeductiveGate"})
accepted, message = ns["C5DeductiveGate"]().verify_trace([("UNKNOWN_SYNTHETIC_OPCODE", None, None)])
assert accepted
results["SW100-C0084"] = {"scope": "actual extracted simulator class; no demo loop, solver, external LLM or Ring-0 effect", "unknown_opcode_accepted": accepted, "message": message}

print(json.dumps({"reviewer": "01", "execution_scope": "isolated in-memory Python source subsets only", "results": results}, indent=2, ensure_ascii=False))
