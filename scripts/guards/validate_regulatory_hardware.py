"""One native challenge, independently verified before activating operator policy.

This creates no dossier, reviewer, L0 transition or release authorization. An
attempt marker prevents automatic retries, including after cancellation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import stat
import subprocess
import sys
import time
from typing import Any

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import encode_dss_signature

sys.path.insert(0, str(Path(__file__).absolute().parents[2] / "01_KISH_ENGINE"))
from babylon60.compliance_exporter.regulatory import canonical, digest, load_json  # noqa: E402


def protected_hash(path: Path) -> str:
    metadata = path.lstat()
    if not path.is_absolute() or not stat.S_ISREG(metadata.st_mode):
        raise ValueError("Expected an absolute regular file, without symlinks")
    if metadata.st_uid != os.getuid() or stat.S_IMODE(metadata.st_mode) & 0o022:
        raise ValueError("Candidate must be owned by the operator and not writable by others")
    return hashlib.sha256(path.read_bytes()).hexdigest()


# These documents cross the JSON evidence boundary; individual fields are checked
# by the native and independent verification protocols before acceptance.
JsonObject = dict[str, Any]


def save(path: Path, value: JsonObject) -> bytes:
    data: bytes = canonical(value) + b"\n"
    with path.open("xb") as stream:
        os.chmod(path, 0o600)
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return data


def verify_challenge(response: JsonObject, expected: JsonObject, public_key_hex: str) -> None:
    if response.get("challenge") != expected or response.get("status") != "REQUIRES_INDEPENDENT_REVIEW":
        raise ValueError("Native challenge, nonce or candidate binding differs")
    if response.get("publication_authorized") is not False or response.get("measurement_status") != "UNAVAILABLE":
        raise ValueError("Unexpected authorization or measurement claim")
    public = bytes.fromhex(public_key_hex)
    if len(public) != 65 or public[0] != 4 or bytes.fromhex(response["public_key_hex"]) != public:
        raise ValueError("Untrusted hardware public key")
    signature = bytes.fromhex(response["signature_hex"])
    if len(signature) != 64:
        raise ValueError("Invalid signature length")
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), public)
    key.verify(
        encode_dss_signature(int.from_bytes(signature[:32], "big"), int.from_bytes(signature[32:], "big")),
        canonical(expected),
        ec.ECDSA(hashes.SHA256()),
    )


def run(binary: Path, policy_path: Path, directory: Path, *, activate: bool) -> JsonObject:
    if sys.platform != "darwin":
        raise ValueError("Native validation requires macOS")
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    policy_before = protected_hash(policy_path)
    policy = load_json(policy_path)
    backend = policy["hardware_backend"]
    helper, key_path = Path(backend["helper_path"]), Path(backend["key_path"])
    candidate = {
        str(binary): protected_hash(binary),
        str(helper): protected_hash(helper),
        str(key_path): protected_hash(key_path),
    }
    if candidate[str(helper)] != backend["helper_sha256"] or candidate[str(key_path)] != backend["key_record_sha256"]:
        raise ValueError("Provisioned backend changed")
    env = {**os.environ, "BABYLON_ENCLAVE_KEY_PATH": str(key_path)}
    inspected = subprocess.run([str(helper), "--inspect-public-key"], capture_output=True, timeout=15, env=env)
    if inspected.returncode:
        raise ValueError("Noninteractive inspection failed; no authentication attempted")
    inspection = json.loads(inspected.stdout)
    if (
        inspection.get("status") != "PUBLIC_KEY_INSPECTED"
        or inspection.get("origin") != "CryptoKit.SecureEnclave.P256.Signing.PrivateKey(existing_dataRepresentation)"
        or inspection.get("public_key_sec1") != policy["hardware_public_key_hex"]
        or inspection.get("key_record_sha256") != candidate[str(key_path)]
    ):
        raise ValueError("Public inspection differs from provisioned key")
    save(directory / "inspection.json", inspection)
    request = {"mode": "validate-hardware", "nonce": secrets.token_hex(32)}
    expected = {
        "schema": "babylon60.euai.native_validation.v1",
        "binary_sha256": candidate[str(binary)],
        "backend_digest": digest(backend),
        "nonce": request["nonce"],
        "purpose": "INDEPENDENT_VALIDATION_ONLY",
    }
    save(directory / "request.json", request)
    save(directory / "candidate.json", {"files_sha256": candidate, "challenge": expected})
    # Persistent, exclusive marker; never remove it or retry after a rejected request.
    save(
        policy_path.with_suffix(".validation-attempt.json"),
        {"evidence_directory": str(directory), "challenge": expected},
    )
    ledger = directory / "unused.sqlite"
    try:
        result = subprocess.run(
            [str(binary), "--policy", str(policy_path), "--ledger", str(ledger)],
            input=canonical(request),
            capture_output=True,
            timeout=55,
            env=env,
        )
        save(
            directory / "native-process.json",
            {
                "exit_code": result.returncode,
                "stdout": result.stdout.decode(errors="replace"),
                "stderr": result.stderr.decode(errors="replace"),
            },
        )
        if result.returncode:
            raise ValueError("Native challenge rejected; no retry and no activation")
        response = json.loads(result.stdout)
        verify_challenge(response, expected, policy["hardware_public_key_hex"])
        if ledger.exists() or candidate != {name: protected_hash(Path(name)) for name in candidate}:
            raise ValueError("Validation produced a ledger or changed its candidate")
        if protected_hash(policy_path) != policy_before:
            raise ValueError("Operator policy changed during validation")
        evidence = {
            "schema": "babylon60.euai.independent_native_evidence.v1",
            "status": "VERIFIED",
            "verifier": "Python cryptography ECDSA/SHA256 (independent of Rust verifier)",
            "response": response,
            "files_sha256": candidate,
            "key_record_unchanged": True,
            "publication_authorized": False,
            "dossier_created": False,
            "attempts": 1,
            "observed_at": int(time.time()),
            "measurement_status": "UNAVAILABLE",
        }
        data = save(directory / "verification.json", evidence)
        validation = {
            "status": "VERIFIED",
            "binary_sha256": candidate[str(binary)],
            "backend_digest": digest(backend),
            "evidence_sha256": hashlib.sha256(data).hexdigest(),
        }
        if activate:
            policy["native_validation"] = validation
            pending = policy_path.with_suffix(".activated.json")
            save(pending, policy)
            os.replace(pending, policy_path)
        return {
            "status": "VERIFIED",
            "activated": activate,
            "native_validation": validation,
            "publication_authorized": False,
            "evidence_directory": str(directory),
        }
    except Exception as exc:
        save(
            directory / "failure.json",
            {
                "status": "NO_VERIFICADO",
                "error": str(exc),
                "attempts": 1,
                "retry_performed": False,
                "policy_activated": False,
            },
        )
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True)
    parser.add_argument("--activate", action="store_true")
    args = parser.parse_args()
    try:
        print(
            json.dumps(
                run(
                    args.binary.absolute(), args.policy.absolute(), args.evidence_dir.absolute(), activate=args.activate
                )
            )
        )
        return 0
    except Exception as exc:
        print(f"NATIVE_VALIDATION_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
