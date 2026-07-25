import glob
import json
import os
import subprocess
import sys
import zipfile


def run_cmd(cmd: list[str], env: dict[str, str] | None = None) -> str:
    print(f"[RUN] {' '.join(cmd)}")
    result = subprocess.run(cmd, env=env, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error executing {' '.join(cmd)}:\n{result.stderr}\n{result.stdout}")
        sys.exit(result.returncode)
    return result.stdout


def check_wheel_contents() -> None:
    print("\n--- Verifying Wheel Contents ---")
    run_cmd(["uv", "build"])
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
    import hashlib

    import cbor2

    vectors_dir = "tests/conformance/vectors"
    os.makedirs(vectors_dir, exist_ok=True)
    event_basic: dict[str, object] = {
        "event_id": "test_event_1",
        "timestamp": 1690000000000,
        "payload": {"action": "ping", "data": "pong"},
    }
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
    from babylon60.bft.consensus_ledger import BFT_Ledger, StateMutation

    db_path = "tests/conformance/test_ledger.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    ledger = BFT_Ledger(db_path)
    mutation = StateMutation(agent_id="test_agent", payload={"test": "data"}, timestamp=1000, signature="mock")
    from babylon60.core.crypto import canonicalize_cbor, hash_sha3_256

    m_hash: str = hash_sha3_256(canonicalize_cbor(mutation.payload))
    ledger.conn.execute(
        "INSERT INTO state_log (mutation_hash, agent_id, payload, ts, causal_taint) VALUES (?, ?, ?, ?, ?)",
        (m_hash, mutation.agent_id, canonicalize_cbor(mutation.payload), mutation.timestamp, mutation.causal_taint),
    )
    ledger.conn.commit()
    if not ledger.audit_integrity():
        print("Initial integrity check failed!")
        sys.exit(1)
    ledger.conn.execute("UPDATE state_log SET payload = ? WHERE agent_id = 'test_agent'", (b"corrupted_cbor_data",))
    ledger.conn.commit()
    if ledger.audit_integrity():
        print("ERROR: Corruption was NOT detected!")
        sys.exit(1)
    print("Replay verification PASSED. Corruption correctly triggers false on audit_integrity().")


def run_ci_checks() -> None:
    print("\n--- Running CI Scope Verification ---")
    run_cmd(["uv", "run", "--all-extras", "pytest", "tests/"])


def main() -> None:
    check_wheel_contents()
    create_crypto_vectors()
    test_replay_corruption()
    run_ci_checks()
    print("\n[SUCCESS] C5-REAL Conformance Checks PASSED.")


if __name__ == "__main__":
    main()
