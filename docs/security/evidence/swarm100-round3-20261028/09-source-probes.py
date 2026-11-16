"""Isolated source probes for review 09; no application import or protected effects.

Only named AST definitions are executed. The scaffolder's file writer is an
in-memory sink. No native compiler, database, network, synthesis, or real user
data is used. Run from the repository root with python3 <this file>.
"""

import ast
import asyncio
import hashlib
import io
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, Optional


def extract(path, names, namespace):
    source = Path(path).read_text()
    tree = ast.parse(source, filename=path)
    selected = [node for node in tree.body if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and node.name in names]
    assert {node.name for node in selected} == set(names)
    exec(compile(ast.Module(body=selected, type_ignores=[]), path, "exec"), namespace)
    return hashlib.sha256(source.encode()).hexdigest()


results = []
demo_path = "scripts/c5_demos/poc_mass_stage3_resolution.py"
namespace = {"dataclass": dataclass, "Dict": Dict, "Any": Any}
demo_hash = extract(demo_path, ["MockGatewayState", "SubordinatedCircuitBreakerDemo"], namespace)
gateway = namespace["MockGatewayState"](t1_alive=False, t2_alive=False, t3_alive=False)
demo = namespace["SubordinatedCircuitBreakerDemo"](delegate_to_kernel=True)
response = asyncio.run(demo.execute_request(gateway, 7))
assert response == {"task_id": 7, "status": "RESOLVED", "tier": "Tier1:Antigravity"}
assert gateway.calls_resolved == 0
results.append({"candidate_id": "SW100-C0234", "source_sha256": demo_hash, "observed": response,
                "calls_resolved_counter": gateway.calls_resolved,
                "scope": "Exact current pure demonstration classes, no gateway or kernel invoked"})


class Capture(io.StringIO):
    def close(self):
        pass


captured = Capture()
fake_os = SimpleNamespace(path=os.path, O_WRONLY=1, O_CREAT=2, O_EXCL=4, O_NOFOLLOW=8,
                          open=lambda *args: 0, fdopen=lambda *args, **kwargs: captured)
scaffold_path = "01_KISH_ENGINE/babylon60/kernel/mcp_scaffolder.py"
namespace = {"Optional": Optional, "McpCandidateContract": object, "os": fake_os,
             "json": json, "logger": logging.getLogger("isolated-review-09")}
scaffold_hash = extract(scaffold_path, ["McpCodeScaffolder"], namespace)
scaffolder = object.__new__(namespace["McpCodeScaffolder"])
scaffolder.output_dir = "/inert-capture"
contract = SimpleNamespace(server_name="Demo", tool_name="demo", description='text with """ delimiter',
                           parameters=[], implementation_body=None, max_invocations=1,
                           to_json_schema=lambda: {"type": "object", "properties": {}, "required": []})
reported_path = scaffolder.scaffold_fastmcp_python(contract)
try:
    ast.parse(captured.getvalue())
except SyntaxError as error:
    syntax_failure = {"message": error.msg, "line": error.lineno}
else:
    raise AssertionError("Triple-quoted description unexpectedly yielded valid source")
results.append({"candidate_id": "SW100-C0106", "source_sha256": scaffold_hash,
                "observed": {"reported_success_path": reported_path, "syntax_failure": syntax_failure},
                "scope": "Exact current scaffolder method with in-memory OS writer; generated source only parsed, never executed"})

print(json.dumps({"reviewer": "09", "protected_runtime_executed": False,
                  "pure_python_probes_executed": True, "results": results}, indent=2))
