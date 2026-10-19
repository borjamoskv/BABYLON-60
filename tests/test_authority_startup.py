"""Start the actual authority binary against temporary, read-only policy fixtures."""

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.mark.skipif(
    "BABYLON_TEST_AUTHORITY_BIN" not in os.environ, reason="requires compiled isolated authority binary"
)
@pytest.mark.parametrize("seed", [None, "short", "g" * 64, "0" * 64])
def test_authority_rejects_missing_or_invalid_key_before_socket(tmp_path, seed):
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {"policy_id": [1] * 32, "allowed_action": "test", "max_allowed_uses": 1, "admitted_authority_key": [2] * 32}
        )
    )
    policy.chmod(0o400)
    short_dir = tempfile.TemporaryDirectory(prefix="b60-p1-", dir="/private/tmp")
    socket = Path(short_dir.name) / "a.sock"
    env = os.environ.copy()
    env.pop("BABYLON_AUTHORITY_ED25519_SEED", None)
    if seed is not None:
        env["BABYLON_AUTHORITY_ED25519_SEED"] = seed
    try:
        result = subprocess.run(
            [os.environ["BABYLON_TEST_AUTHORITY_BIN"], "--policy", str(policy), "--socket", str(socket), "--once"],
            env=env,
            capture_output=True,
            text=True,
            timeout=1,
        )
    except subprocess.TimeoutExpired:
        pytest.fail("Authority opened a signing service without a valid explicit private key")
    assert result.returncode != 0
    assert not socket.exists()
    assert "panicked" not in result.stderr
    assert "private key" in result.stderr.lower()
    short_dir.cleanup()
