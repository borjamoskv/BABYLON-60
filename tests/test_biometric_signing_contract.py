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


def test_demo_gate_has_one_canonical_source() -> None:
    demo = REPO / "scripts/c5_demos/c5_biometric_gate.swift"
    canonical = REPO / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift"
    assert demo.is_symlink(), "The legacy demo must not retain its own key writer"
    assert demo.samefile(canonical), "The demo must use the canonical biometric gate"


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


@pytest.fixture(scope="module")
def inspection_binary(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Compile the real CLI plus a separate software-only key-loader harness."""
    compiler = shutil.which("swiftc")
    if sys.platform != "darwin" or compiler is None:
        pytest.skip("macOS and Swift CryptoKit required")
    temporary = tmp_path_factory.mktemp("public-key-inspection")
    source = temporary / "main.swift"
    gate = (REPO / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift").read_text()
    harness = r'''
if CommandLine.arguments.contains("--inspect-public-key") {
    main()
} else {
    do {
        let path = CommandLine.arguments[1]
        let invalid = CommandLine.arguments.contains("--invalid-public-key")
        let result = try inspectExistingBiometricKey(at: path) { opaqueData in
            guard opaqueData == Data([1, 2, 3]) else {
                throw PublicKeyInspectionError.keyRecordRejected
            }
            if invalid { return Data([4]) }
            return try P256.Signing.PrivateKey(rawRepresentation: Data(repeating: 7, count: 32))
                .publicKey.x963Representation
        }
        let report = ["test_source": "SOFTWARE_ONLY", "public_key_sec1": result.publicKeySec1,
                      "key_record_sha256": result.keyRecordSHA256]
        let json = try JSONSerialization.data(withJSONObject: report, options: [.sortedKeys])
        print(String(decoding: json, as: UTF8.self))
    } catch {
        print("INSPECTION_FAILED")
        exit(2)
    }
}
'''
    source.write_text(gate + "\n" + harness)
    binary = temporary / "inspection-contract"
    command = [
        compiler, "-D", "BIOMETRIC_CONTRACT_TEST", "-module-cache-path",
        os.environ.get("B60_SWIFT_TEST_MODULE_CACHE", str(temporary / "module-cache")),
        str(source), "-o", str(binary),
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, start_new_session=True)
    try:
        _, errors = process.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.communicate()
        raise
    assert process.returncode == 0, errors
    return binary


def _inspection_record(path: Path, *, version: int = 2) -> bytes:
    record = json.dumps({"version": version, "keyData": base64.b64encode(bytes([1, 2, 3])).decode()}).encode()
    path.write_bytes(record)
    path.chmod(0o600)
    return record


def test_inspection_binds_public_point_to_unchanged_record(inspection_binary: Path, tmp_path: Path) -> None:
    path = tmp_path / "key"
    record = _inspection_record(path)
    before = path.stat()
    result = subprocess.run([str(inspection_binary), str(path)], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["test_source"] == "SOFTWARE_ONLY"
    expected = ec.derive_private_key(int.from_bytes(bytes([7]) * 32), ec.SECP256R1()).public_key()
    actual = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), bytes.fromhex(report["public_key_sec1"]))
    assert actual.public_numbers() == expected.public_numbers()
    assert report["key_record_sha256"] == hashlib.sha256(record).hexdigest()
    assert path.read_bytes() == record
    assert path.stat().st_mtime_ns == before.st_mtime_ns


@pytest.mark.parametrize("case", ["missing", "symlink", "directory", "fifo", "permissions", "legacy", "oversized"])
def test_inspection_cli_rejects_before_loading_hardware(
    inspection_binary: Path, tmp_path: Path, case: str,
) -> None:
    path = tmp_path / "key"
    if case == "symlink":
        target = tmp_path / "target"
        _inspection_record(target)
        path.symlink_to(target)
    elif case == "directory":
        path.mkdir(mode=0o700)
    elif case == "fifo":
        os.mkfifo(path, mode=0o600)
    elif case in {"permissions", "legacy", "oversized"}:
        _inspection_record(path, version=1 if case == "legacy" else 2)
        if case == "permissions":
            path.chmod(0o644)
        if case == "oversized":
            path.write_bytes(b"x" * 65_537)
    before = sorted(item.name for item in tmp_path.iterdir())
    result = subprocess.run(
        [str(inspection_binary), "--inspect-public-key"],
        env={**os.environ, "BABYLON_ENCLAVE_KEY_PATH": str(path)},
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2, result.stderr
    report = json.loads(result.stdout)
    assert report["schema"] == "babylon60.public-key-inspection.v1"
    assert report["status"] == "INSPECTION_FAILED"
    assert "public_key_sec1" not in report
    assert sorted(item.name for item in tmp_path.iterdir()) == before


def test_inspection_rejects_mixed_signing_arguments(inspection_binary: Path, tmp_path: Path) -> None:
    result = subprocess.run(
        [str(inspection_binary), "--inspect-public-key", "--action", "forbidden"],
        env={**os.environ, "BABYLON_ENCLAVE_KEY_PATH": str(tmp_path / "missing")},
        capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2
    assert json.loads(result.stdout)["error"] == "invalidArguments"


def test_inspection_rejects_invalid_public_point(inspection_binary: Path, tmp_path: Path) -> None:
    path = tmp_path / "key"
    record = _inspection_record(path)
    result = subprocess.run(
        [str(inspection_binary), str(path), "--invalid-public-key"], capture_output=True, text=True, timeout=5,
    )
    assert result.returncode == 2
    assert path.read_bytes() == record
