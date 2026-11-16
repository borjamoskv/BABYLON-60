"""Bounded reviewer-05 checks: pure Python and synthetic temporary data only.

No package initialization, native launch, real operator data, or network access.
Autodidact's three pure source modules are loaded in dependency order with
package imports omitted; their actual definitions execute unchanged.
"""

import ast
import hashlib
import json
import sys
import tempfile
import types
from pathlib import Path


ROOT = Path(__file__).absolute().parents[4]
BASE = Path(__file__).absolute().parent
RESULTS = []


def load_pure(relative, name, dependencies=None):
    path = ROOT / relative
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tree.body = [
        node
        for node in tree.body
        if not (
            isinstance(node, ast.ImportFrom)
            and (node.module or "").startswith("babylon60.")
        )
    ]
    module = types.ModuleType(name)
    if dependencies:
        module.__dict__.update(
            {key: value for key, value in dependencies.items() if not key.startswith("__")}
        )
    sys.modules[name] = module
    exec(compile(tree, str(path), "exec"), module.__dict__)
    return module


types_module = load_pure("01_KISH_ENGINE/babylon60/autodidact/types.py", "review05_types")
epistemology = load_pure(
    "01_KISH_ENGINE/babylon60/autodidact/epistemology.py",
    "review05_epistemology",
    vars(types_module),
)
compiler_module = load_pure(
    "01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py",
    "review05_compiler",
    vars(epistemology),
)
compiler = compiler_module.CrystalCompiler()
with tempfile.TemporaryDirectory(prefix="review05-crystal-") as directory:
    path = Path(directory) / "crystal.md"
    path.write_text("Merkle Root (SHA-256): `" + "a" * 64 + "`", encoding="utf-8")
    accepted, detail = compiler.verify_crystal_integrity(str(path))
    assert accepted is False
    RESULTS.append({"candidate_id": "SW100-C0292", "result": "PASS", "accepted": accepted, "detail": detail})

for digest in (None, ""):
    verdict = types_module.FalsificationVerdict("synthetic public fixture", False, "SUPPORTED", evidence_digest=digest)
    crystal = compiler.compile("synthetic", "synthetic", [], [verdict])
    accepted, detail = compiler.verify_crystal_integrity(compiler.export_json(crystal))
    assert accepted is True
    RESULTS.append({"candidate_id": "SW100-C0293", "result": "PASS", "evidence_digest": digest, "accepted": accepted, "detail": detail})

leases = load_pure("01_KISH_ENGINE/babylon60/guards/token_lease_guard.py", "review05_leases")
lease = leases.TokenLease("synthetic", "auditor", max_effective_units=100)
lease.record_step(0, -100, verified_outcome=True)
assert lease.consumed_units == -500
assert lease.remaining_units == 600
RESULTS.append({"candidate_id": "SW100-C0547", "result": "REPRODUCED", "consumed_units": lease.consumed_units, "remaining_units": lease.remaining_units, "tripped": lease.tripped})

readme = ROOT / "00_ABZU_KERNEL/crates/babylon60-compiler/README.md"
for target in ("../../../proof/lean/BabylonTrace.lean", "../../../proof/lean/AX0.lean", "../../../CLAIMS.toml"):
    # Lexical normalization only; no symlink-based root inference.
    import os
    actual = Path(os.path.normpath(str(readme.parent / target)))
    expected = ROOT / target.removeprefix("../../../")
    assert actual == expected and actual.is_file()
    RESULTS.append({"candidate_id": "SW100-C0197", "result": "REJECTED_LINK_IS_CORRECT", "link": target, "resolved_repository_relative": str(actual.relative_to(ROOT))})

report = {
    "scope": "Isolated pure source definitions and synthetic temporary inputs; no package integration, native execution, or network calls.",
    "checks": RESULTS,
    "source_sha256": {
        path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest()
        for path in (
            "01_KISH_ENGINE/babylon60/autodidact/types.py",
            "01_KISH_ENGINE/babylon60/autodidact/epistemology.py",
            "01_KISH_ENGINE/babylon60/autodidact/crystal_compiler.py",
            "01_KISH_ENGINE/babylon60/guards/token_lease_guard.py",
            "00_ABZU_KERNEL/crates/babylon60-compiler/README.md",
        )
    },
}
(BASE / "05-pure-checks-results.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2, ensure_ascii=False))
