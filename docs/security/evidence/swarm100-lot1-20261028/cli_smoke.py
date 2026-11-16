"""Exercise the actual Tamkarum CLI using only ephemeral signed evidence."""

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

ROOT = Path(__file__).absolute().parents[4]
CLI = ROOT / "tools/tamkarum_attestation_engine.py"


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()


def main():
    observations = []
    with tempfile.TemporaryDirectory(prefix="lot1-cli-") as directory:
        here = Path(directory)
        paths = {name: here / f"{name}.json" for name in ["outreach_manifest", "social_calendar", "compliance_pack"]}
        for name, path in paths.items():
            path.write_text(json.dumps({"global_consolidated_merkle_root": "a" * 64}
                                       if name == "outreach_manifest" else {"fixture": name}))
        payload = {"git_commit": "b" * 40, "topology_sha256": "c" * 64,
                   "outreach_root": "a" * 64,
                   "evidence_sha256": {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in paths.items()}}
        payload["compound_attestation_hash"] = hashlib.sha256(b"BABYLON60:TAMKARUM:PAYLOAD:v2\0" + canonical(payload)).hexdigest()
        body = {"header": {"schema": "tamkarum-evidence/v2", "algorithm": "Ed25519"}, "payload": payload}
        key = Ed25519PrivateKey.generate()
        signature = key.sign(b"BABYLON60:TAMKARUM:ATTESTATION:v2\0" + canonical(body))
        statement = {**body, "signature": {"algorithm": "Ed25519", "value": base64.b64encode(signature).decode()}}
        statement_path, key_path = here / "statement.json", here / "public.raw"
        statement_path.write_text(json.dumps(statement))
        key_path.write_bytes(key.public_key().public_bytes_raw())
        arguments = ["--verify", "--statement", str(statement_path), "--trusted-key", str(key_path),
                     "--expected-commit", "b" * 40, "--expected-topology-sha256", "c" * 64]
        for name, path in paths.items():
            arguments += ["--" + name.replace("_", "-"), str(path)]

        def run(name, args, expected):
            result = subprocess.run([sys.executable, str(CLI), *args], cwd=ROOT, capture_output=True,
                                    text=True, timeout=10, check=False)
            assert result.returncode == expected, (name, result.stdout, result.stderr)
            observations.append({"case": name, "expected_exit_code": expected,
                                 "actual_exit_code": result.returncode, "result": "PASS"})

        run("trusted signed current fixture", arguments, 0)
        paths["social_calendar"].write_text('{"changed":true}')
        run("changed artifact", arguments, 1)
        run("missing trust key", ["--verify", "--statement", str(statement_path)], 1)
        run("no implicit emission", [], 2)
        run("emit rejects verification paths", ["--emit", "--social-calendar", str(paths["social_calendar"])], 2)
    output = {"runtime_scope": "Actual Python CLI, synthetic keys and temporary files only; no --emit executed, no network or campaigns read.",
              "observations": observations}
    destination = Path(__file__).with_name("cli-smoke.json")
    destination.write_text(json.dumps(output, indent=2) + "\n")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
