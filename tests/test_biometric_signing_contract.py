"""Swift protocol compatibility using a software key, never Touch ID."""

import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
from typing import cast

import pytest
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec

REPO = Path(__file__).absolute().parents[1]


@pytest.fixture(scope="module")
def contract_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    compiler = shutil.which("swiftc")
    if sys.platform != "darwin" or compiler is None:
        pytest.skip("macOS and Swift CryptoKit required")
    temporary = tmp_path_factory.mktemp("software-biometric-contract")
    source = temporary / "main.swift"
    gate = (REPO / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift").read_text()
    fixture = (REPO / "tests/fixtures/biometric_contract_main.swift").read_text()
    source.write_text(gate + "\n" + fixture)
    binary = temporary / "software-contract"
    command = [
        compiler,
        "-D",
        "BIOMETRIC_CONTRACT_TEST",
        "-module-cache-path",
        os.environ.get("B60_SWIFT_TEST_MODULE_CACHE", str(temporary / "module-cache")),
        str(source),
        "-o",
        str(binary),
    ]
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True
    )
    try:
        _, errors = process.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
    assert process.returncode == 0, errors
    return binary


def test_swift_protocol_and_key_records(contract_binary: Path) -> None:
    result = subprocess.run([str(contract_binary)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "PASS: software-only Swift signing contract"


def test_swift_signature_verifies_original_bytes(contract_binary: Path) -> None:
    payload = b"COSE Signature1 fixture\x00\x80\xff"
    result = subprocess.run(
        [
            str(contract_binary),
            "--causal-hash",
            hashlib.sha256(payload).hexdigest(),
            "--sign-hex",
            payload.hex(),
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    response = cast(dict[str, str], json.loads(result.stdout))
    assert response["test_source"] == "SOFTWARE_ONLY"
    key = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), base64.b64decode(response["public_key"]))
    key.verify(base64.b64decode(response["secure_enclave_signature"]), payload, ec.ECDSA(hashes.SHA256()))


@pytest.mark.parametrize("value", ["0", "zz", "00 01", "00"])
def test_bad_payload_is_rejected(contract_binary: Path, value: str) -> None:
    result = subprocess.run(
        [
            str(contract_binary),
            "--causal-hash",
            hashlib.sha256(b"payload").hexdigest(),
            "--sign-hex",
            value,
        ],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert result.returncode == 2
    assert "ATTESTED" not in result.stdout
