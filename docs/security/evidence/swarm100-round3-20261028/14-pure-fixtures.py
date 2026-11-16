"""Pure extracted-source fixtures. No application imports, processes or operational data."""

import ast
import dataclasses
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
from typing import List, Sequence

ROOT = Path(__file__).absolute().parents[4]


def load_selected(path, names, method=None):
    source = (ROOT / path).read_text()
    selected = [n for n in ast.parse(source).body if isinstance(n, ast.ClassDef) and n.name in names]
    if method:
        for node in selected:
            if node.name == method[0]:
                node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name == method[1]]
    namespace = {"dataclass": dataclasses.dataclass, "field": dataclasses.field, "List": List, "Sequence": Sequence}
    exec(compile(ast.Module(body=selected, type_ignores=[]), path, "exec"), namespace)
    return namespace, hashlib.sha256(source.encode()).hexdigest()


records = []
path = "scripts/c5_demos/c5_darknode_core.py"
ns, digest = load_selected(path, {"Sexagesimal60"})
results = []
for numerator, denominator in [(1, 1), (59, 60)]:
    converted = ns["Sexagesimal60"].from_rational(numerator, denominator)
    actual = converted.to_scalar()
    expected = numerator / denominator
    assert actual != expected
    results.append({"input": [numerator, denominator], "fields": dataclasses.asdict(converted), "actual": actual, "expected": expected})
records.append({"candidate_id": "SW100-C0592", "source_sha256": digest, "results": results, "scope": "Only extracted pure Sexagesimal60 class executed; no attestation/native code imported."})

path = "01_KISH_ENGINE/babylon60/memory/metamemory.py"
ns, digest = load_selected(path, {"FokJudgment", "MetamemoryMonitor"}, ("MetamemoryMonitor", "judge_procedural_fok"))
monitor = ns["MetamemoryMonitor"]()
results = []
for intent, names in [("alpha beta", ["alpha"]), ("alpha beta", ["unrelated"]), ("a", ["skill"]), ("alpha", [])]:
    judgment = monitor.judge_procedural_fok(intent, [SimpleNamespace(name=n) for n in names])
    assert not judgment.tip_of_tongue
    results.append({"intent": intent, "candidate_names": names, "judgment": dataclasses.asdict(judgment)})
records.append({"candidate_id": "SW100-C0199", "source_sha256": digest, "results": results, "scope": "Extracted pure FOK method and result dataclass only; no ledger imports. Universal unreachability is additionally established from score floor >= 0.5 versus < 0.35 predicate."})

path = "tools/skill_library/codex_overrides/cloudflare/references/workers-for-platforms/api.md"
source = (ROOT / path).read_text()
section = source.split("## Deploy with Bindings", 1)[1]
metadata = section.split("-F 'metadata=", 1)[1].split(";type=application/json'", 1)[0]
metadata = metadata.replace("'$KV_ID'", "fixture-kv")
try:
    json.loads(metadata)
except json.JSONDecodeError as error:
    assert "// Use current date" in metadata
    records.append({"candidate_id": "SW100-C0015", "source_sha256": hashlib.sha256(source.encode()).hexdigest(), "result": "JSONDecodeError", "line": error.lineno, "column": error.colno, "message": error.msg, "scope": "Extracted metadata parsed in memory after replacing only the shell KV substitution; curl and Cloudflare not called."})
else:
    raise AssertionError("Malformed metadata unexpectedly parsed")

print(json.dumps({"fixture_kind": "isolated_pure_source_fragments", "production_runtime_executed": False, "records": records}, indent=2))
