"""Independent Lot3 checks: fixture-owned commands only; no ATTESTED objects."""
import ast
import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[4]
TEST = ROOT / "tests/test_swarm100_lot3_regressions.py"
spec = importlib.util.spec_from_file_location("lot3_fixture_only", TEST)
support = importlib.util.module_from_spec(spec)
spec.loader.exec_module(support)


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="lot3-independent-") as temporary:
        base = Path(temporary)

        def fixture(name):
            root = base / name
            root.mkdir()
            return support.Fixture(root)

        for label, output in (
            ("duplicate_keys", '{"status":"TEST_CONTROL_FLOW_ONLY","status":"TEST_CONTROL_FLOW_ONLY"}'),
            ("array_root", "[]"),
            ("null_root", "null"),
            ("oversized_output", "x" * 65537),
        ):
            f = fixture(label)
            f.install("c5_biometric_gate", "print(" + repr(output) + ")\n")
            result = f.run("c5_ship.sh")
            assert result.returncode != 0
            assert not (f.root / "pushed").exists()
            assert b"Recibo validado" not in result.stdout
            assert not list((f.root / "tmp").rglob("receipt.json"))
            checks.append({"case": label, "passed": True})

        for value in ("0", "61", "not-an-integer"):
            f = fixture("timeout-" + value)
            f.env["B60_GIT_GATE_TIMEOUT"] = value
            result = f.run("c5_ship.sh")
            assert result.returncode != 0
            assert not f.calls("gate")
            assert not (f.root / "pushed").exists()
            checks.append({"case": "timeout_rejected_before_gate_" + value, "passed": True})

        f = fixture("orphaned-gate-child")
        marker = f.root / "child-survived-timeout"
        child = "import pathlib,time; time.sleep(2); pathlib.Path(" + repr(str(marker)) + ").write_text('unexpected')"
        wrapper = "import os,subprocess\nsubprocess.Popen([" + repr(sys.executable) + ", '-c', " + repr(child) + "])\nos._exit(0)\n"
        f.install("c5_biometric_gate", wrapper)
        result = f.run("c5_ship.sh")
        assert result.returncode != 0 and not (f.root / "pushed").exists()
        time.sleep(1.5)
        assert not marker.exists(), "orphaned fixture gate child survived rejection deadline"
        checks.append({"case": "timeout_kills_group_after_gate_leader_exits", "passed": True})

        f = fixture("binding")
        result = f.helper("prepare", support.COMMIT, support.TREE, "public", "true",
                          "Fixture", "Fixture", str(f.root / "effect.json"))
        assert result.returncode == 0, result.stderr
        effect = json.loads(base64.b64decode(result.stdout))["effect"]
        source = (ROOT / "scripts/c5_git_utils/c5_distill_public_mirror.sh").read_text()
        python = source.split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
        tree = ast.parse(python)
        nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
        namespace = {}
        exec(compile(ast.Module(body=nodes, type_ignores=[]), "<pure-publication-functions>", "exec"), namespace)
        original = namespace["effect_hash"](effect)
        expected = hashlib.sha256(b"BABYLON60:GIT:PUBLISH:v1\0" + namespace["canonical"](effect)).hexdigest()
        assert original == expected and len(original) == 64
        for field in ("commit", "tree", "destination_sha256", "target_ref", "force", "action",
                      "scope", "agent", "nonce", "transport_config_sha256"):
            changed = dict(effect)
            changed[field] = not effect[field] if isinstance(effect[field], bool) else effect[field] + "changed"
            assert namespace["effect_hash"](changed) != original
        checks.append({"case": "all_ten_effect_fields_bound", "passed": True})

        f = fixture("raw-symlink")
        sentinel = f.root / "sentinel"
        sentinel.write_text("outside snapshot fixture")
        f.install("git", r'''
import sys
a = sys.argv[1:]
if a[:1] == ['--no-replace-objects']: a = a[1:]
if a[:1] == ['ls-tree']:
    sys.stdout.buffer.write(b'100644 blob '+b'4'*40+b'\t.gitleaks.toml\0'+b'120000 blob '+b'5'*40+b'\tlink.txt\0')
elif a[:1] == ['cat-file']:
    data = b'[extend]\nuseDefault = true\n' if a[-1] == '4'*40 else b'../sentinel'
    if '-s' in a: print(len(data))
    else: sys.stdout.buffer.write(data)
else: raise SystemExit('unsupported fixture command')
''')
        result = f.helper("snapshot", support.TREE, str(f.root / "snapshot"))
        assert result.returncode == 0, result.stderr
        materialized = f.root / "snapshot/link.txt"
        assert not materialized.is_symlink() and materialized.read_bytes() == b"../sentinel"
        assert sentinel.read_text() == "outside snapshot fixture"
        checks.append({"case": "symlink_is_scanned_as_raw_blob_not_followed", "passed": True})
    print(json.dumps({"checks": checks, "passed": len(checks),
                      "scope": "Temporary fixture-owned commands; no real Git, Swift, biometric gate, network, publish or ATTESTED objects."}, indent=2))


if __name__ == "__main__":
    main()
