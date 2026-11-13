#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import glob
import json
import os
import shutil
import subprocess
import sys
import zipfile

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> str:
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {' '.join(cmd)}:\n{result.stderr}\n{result.stdout}")
        sys.exit(result.returncode)
    return result.stdout


def check_wheel_contents() -> None:
    print("\n--- Verifying Wheel Contents ---")
    uv_bin = shutil.which("uv")
    if uv_bin:
        run_cmd([uv_bin, "build"])
    else:
        run_cmd([sys.executable, "-m", "pip", "wheel", ".", "--no-deps", "-w", "dist/"])
    wheels = glob.glob("dist/*.whl")
    if not wheels:
        print("ERROR: No wheels found in dist/")
        sys.exit(1)

    latest_wheel = max(wheels, key=os.path.getctime)
    with zipfile.ZipFile(latest_wheel, "r") as z:
        files = z.namelist()

    invalid_roots = ["tests", "cortex", "experimental", "scripts"]
    for f in files:
        root_dir = f.split("/")[0]
        if root_dir in invalid_roots:
            print(f"ERROR: Wheel contains invalid root directory '{root_dir}' -> {f}")
            sys.exit(1)

    print("Wheel verification PASSED. The distribution is clean.")


def create_crypto_vectors() -> None:
    print("\n--- Creating Cryptographic Vectors ---")
    import cbor2
    import hashlib

    vectors_dir = "tests/conformance/vectors"
    os.makedirs(vectors_dir, exist_ok=True)

    event_basic: dict[str, object] = {
        "event_id": "test_event_1",
        "timestamp": 1690000000000,
        "payload": {"action": "ping", "data": "pong"},
    }

    # Generate canonical cbor
    cbor_bytes: bytes = cbor2.dumps(event_basic, canonical=True)
    cbor_hex: str = cbor_bytes.hex()
    sha3_hash: str = hashlib.sha3_256(cbor_bytes).hexdigest()

    event_basic["_cbor_hex"] = cbor_hex
    event_basic["_sha3_256"] = sha3_hash

    with open(f"{vectors_dir}/event_basic.json", "w") as fh:
        json.dump(event_basic, fh, indent=2)
    print(f"Crypto vectors written. SHA3: {sha3_hash}")


def test_replay_corruption() -> None:
    print("\n--- Testing Replay / Corruption ---")
    import tempfile

    from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation
    from babylon60.core.crypto_utils import Ed25519Signer

    # Authenticate a real quorum before testing tamper detection. Unsigned rows
    # would be invalid before corruption and cannot be a positive control.
    f = 1
    signers = {f"node{i}": Ed25519Signer() for i in range(3 * f + 1)}
    with tempfile.TemporaryDirectory(prefix="babylon-conformance-") as directory:
        ledger = BFT_Ledger(
            os.path.join(directory, "ledger.db"),
            {node: signer.public_key_hex for node, signer in signers.items()},
        )
        try:
            mutation = StateMutation(agent_id="test_agent", payload={"test": "data"}, timestamp=1000, signature="")
            votes = {node: signer.sign(mutation.signing_hash(f)) for node, signer in signers.items()}
            if not ledger.invoke_subagent(mutation, f, votes):
                raise RuntimeError("Authenticated commit failed")
            if not ledger.audit_integrity():
                raise RuntimeError("Initial authenticated integrity check failed")
            ledger.conn.execute(
                "UPDATE state_log SET payload = ? WHERE agent_id = 'test_agent'", (b"corrupted_cbor_data",)
            )
            ledger.conn.commit()
            if ledger.audit_integrity():
                raise RuntimeError("Corruption was not detected")
        finally:
            ledger.close()
    print("Replay verification PASSED. Authenticated history passed and corruption was rejected.")


def run_ci_checks() -> None:
    print("\n--- Running CI Scope Verification ---")
    # The workflow creates the locked environment. Preserve its interpreter and
    # the first failure; retrying under another environment can hide that failure.
    run_cmd([sys.executable, "-m", "pytest", "tests/", "--maxfail=0"])


def main() -> None:
    check_wheel_contents()
    create_crypto_vectors()
    test_replay_corruption()
    run_ci_checks()
    print("\n[SUCCESS] Causal-Determinist Conformance Checks PASSED.")


if __name__ == "__main__":
    main()
