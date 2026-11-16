"""Storage failure fixtures only; no authorization, Git or network execution."""
import ast
import hashlib
import json
from pathlib import Path
import tempfile
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / "scripts/c5_git_utils/c5_distill_public_mirror.sh"


def main():
    raw = SOURCE.read_bytes()
    code = raw.decode().split("<<'PY'\n", 1)[1].split("\nPY\n", 1)[0]
    tree = ast.parse(code)
    nodes = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom, ast.FunctionDef))]
    namespace = {}
    exec(compile(ast.Module(body=nodes, type_ignores=[]), "<storage-only>", "exec"), namespace)
    results = []
    with tempfile.TemporaryDirectory(prefix="lot3-retention-") as temporary_root:
        for case in ("collision", "unsafe-directory", "malformed-json", "replace-failure"):
            directory = Path(temporary_root) / case
            directory.mkdir(mode=0o700)
            pending = directory / "receipt-storage-fixture.tmp"
            previous = directory / "last_ship_receipt.json"
            previous.write_bytes(b"previous fixture receipt")
            if case in ("collision", "unsafe-directory"):
                pending.write_bytes(b"preexisting fixture temporary")
            if case == "unsafe-directory":
                directory.chmod(0o770)
            receipt = b"[" if case == "malformed-json" else b'{"fixture":"storage-only"}'
            try:
                if case == "replace-failure":
                    with patch.object(namespace["os"], "replace", side_effect=OSError("fixture failure")):
                        namespace["retain_receipt"](directory, receipt, {"nonce": "storage-fixture"})
                else:
                    namespace["retain_receipt"](directory, receipt, {"nonce": "storage-fixture"})
            except (FileExistsError, ValueError, OSError) as error:
                exception = type(error).__name__
            else:
                raise AssertionError("storage fixture should refuse")
            assert previous.read_bytes() == b"previous fixture receipt"
            if case in ("collision", "unsafe-directory"):
                assert pending.read_bytes() == b"preexisting fixture temporary"
            else:
                assert not pending.exists()
            results.append({"case": case, "passed": True, "exception": exception})
    print(json.dumps({"source_sha256": hashlib.sha256(raw).hexdigest(), "checks": results,
                      "passed": len(results), "scope": "Temporary storage-only data; no ATTESTED, gate, Git, Swift or network."}, indent=2))


if __name__ == "__main__":
    main()
