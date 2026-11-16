"""Reviewer 17: isolated source-level reproductions; no native product runtime.

Runs only inspected stdlib modules or AST-selected functions. Fixtures are synthetic;
no operator data, credential APIs, network, subprocesses, native components or apps.
"""

import ast
import hashlib
import json
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).with_suffix(".json")
RESULTS = []


def record(candidate_id, path, observations):
    RESULTS.append({
        "candidate_id": candidate_id,
        "path": path,
        "source_sha256": hashlib.sha256((ROOT / path).read_bytes()).hexdigest(),
        "observations": observations,
        "scope": "Isolated pure Python source execution; no product integration executed",
    })


def load_stdlib_module(path):
    scope = {"__name__": "review17_isolated"}
    exec(compile((ROOT / path).read_text(), path, "exec"), scope)
    return scope


cbor_path = "01_KISH_ENGINE/babylon60/primitives/cbor.py"
cbor = load_stdlib_module(cbor_path)
observed_bytes = cbor["loads"](bytes.fromhex("4378"))
observed_text = cbor["loads"](bytes.fromhex("6378"))
observed_trailing = cbor["loads"](bytes.fromhex("0001"))
assert observed_bytes == b"x"
assert observed_text == "x"
assert observed_trailing == 0
record("SW100-C0259", cbor_path, {
    "4378_declares_three_bytes_returns_hex": observed_bytes.hex(),
    "6378_declares_three_text_bytes_returns": observed_text,
    "0001_has_trailing_item_returns": observed_trailing,
})

lint_path = "tools/skill_library/workspace/c5-anti-slop-ui/scripts/audit_ui_slop.py"
linter = load_stdlib_module(lint_path)
with tempfile.TemporaryDirectory(prefix="17-fixture-", dir=OUT.parent) as fixture_dir:
    fixture = Path(fixture_dir) / "build-review" / "src"
    fixture.mkdir(parents=True)
    source = fixture / "index.html"
    source.write_text('<p class="text-[17px]">Synthetic fixture</p>\n')
    direct = linter["audit_file"](str(source))
    tree = linter["audit_directory"](str(fixture))
    assert len(direct) == 1 and direct[0].rule_id == "C5-UI-002"
    assert tree == []
    record("SW100-C0174", lint_path, {
        "direct_file_violation_count": len(direct),
        "directory_violation_count": len(tree),
        "synthetic_parent_component": "build-review",
    })

asar_path = "tools/skill_library/global/c5-secops-infra-devtools/references/modules/electron-asar-forensic-audit/MODULE.md"
snippet = (ROOT / asar_path).read_text().split("```python\n", 1)[1].split("```", 1)[0]
scope = {"__name__": "review17_asar"}
exec(compile(snippet, asar_path, "exec"), scope)
with tempfile.TemporaryDirectory(prefix="17-fixture-", dir=OUT.parent) as fixture_dir:
    archive = Path(fixture_dir) / "fixture.asar"
    header = json.dumps({"files": {"x.js": {"size": 1, "offset": 0}}}).encode()
    archive.write_bytes(struct.pack("<IIII", 4, len(header) + 8, len(header), len(header)) + header + b"x")
    files, offset_base, stream = scope["scan_asar"](archive)
    assert stream.closed
    try:
        stream.seek(offset_base)
    except ValueError as exc:
        error = str(exc)
    else:
        raise AssertionError("Expected the documented returned stream to be closed")
    record("SW100-C0302", asar_path, {
        "returned_stream_closed": stream.closed,
        "documented_consumer_seek_error": error,
        "synthetic_file_entries": len(files),
    })

rhythm_path = "tools/skill_library/global/c5-audiovisual-acreativo-sota/references/modules/flstudio-mcp-production/examples/Euclidean_Polyrhythm_Generator.py"
tree = ast.parse((ROOT / rhythm_path).read_text(), rhythm_path)
selected = ast.Module(body=[node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"bjorklund", "generate_euclidean"}], type_ignores=[])
scope = {"HAS_FLPIANOROLL": False, "utils": SimpleNamespace(Note=SimpleNamespace)}
exec(compile(selected, rhythm_path, "exec"), scope)


class FixtureScore:
    def __init__(self):
        self.notes = []

    def clear(self):
        self.notes.clear()

    def addNote(self, note):
        self.notes.append(vars(note).copy())


scores = [FixtureScore(), FixtureScore()]
for mode, score in enumerate(scores):
    scope["generate_euclidean"](score, n1=16, k1=5, n2=12, k2=7, bars=4, mode=mode)
assert scores[0].notes == scores[1].notes
record("SW100-C0022", rhythm_path, {
    "mode_0_note_count": len(scores[0].notes),
    "mode_1_note_count": len(scores[1].notes),
    "all_note_attributes_equal": scores[0].notes == scores[1].notes,
    "limitation": "Score and Note are synthetic in-memory fixtures; FL Studio was not loaded",
})

OUT.write_text(json.dumps({"reviewer": "17", "checks": RESULTS}, indent=2) + "\n")
print(json.dumps({"checks_passed": len(RESULTS), "evidence": str(OUT.relative_to(ROOT))}))
