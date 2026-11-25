"""Start the actual authority binary against temporary, read-only policy fixtures."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from nacl.signing import SigningKey


AUTHORITY_STARTUP_TIMEOUT_SECONDS = 10


@pytest.mark.skipif(
    "BABYLON_TEST_AUTHORITY_BIN" not in os.environ, reason="requires compiled isolated authority binary"
)
@pytest.mark.parametrize("seed", [None, "short", "g" * 64, "0" * 64])
def test_authority_rejects_missing_or_invalid_key_before_socket(tmp_path: Path, seed: str | None) -> None:
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {"policy_id": [1] * 32, "allowed_action": "test", "max_allowed_uses": 1, "admitted_authority_key": [2] * 32}
        )
    )
    policy.chmod(0o400)
    env = os.environ.copy()
    # Isolated software transport identities let this test reach the authority-key
    # guard. They neither authorize an effect nor replace hardware attestation.
    env["BABYLON_IPC_SIGNING_SEED"] = SigningKey.generate().encode().hex()
    env["BABYLON_IPC_PEER_PUBLIC_KEY"] = SigningKey.generate().verify_key.encode().hex()
    env["BABYLON_IPC_PEER_UID"] = str(os.geteuid())
    env.pop("BABYLON_AUTHORITY_ED25519_SEED", None)
    if seed is not None:
        env["BABYLON_AUTHORITY_ED25519_SEED"] = seed
    with tempfile.TemporaryDirectory(prefix="b60-p1-", dir="/tmp") as short_dir:
        socket = Path(short_dir) / "a.sock"
        try:
            result = subprocess.run(
                [os.environ["BABYLON_TEST_AUTHORITY_BIN"], "--policy", str(policy), "--socket", str(socket), "--once"],
                env=env,
                capture_output=True,
                text=True,
                # Allow bounded cold-loader startup; a timeout still fails.
                timeout=AUTHORITY_STARTUP_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            pytest.fail(
                f"Authority startup exceeded {AUTHORITY_STARTUP_TIMEOUT_SECONDS}s; "
                f"socket path present={os.path.lexists(socket)}"
            )
        assert result.returncode != 0
        assert not os.path.lexists(socket), "Rejected authority key created a socket path"
        assert "panicked" not in result.stderr
        assert "private key" in result.stderr.lower()
