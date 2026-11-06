"""Manual, one-attempt MCP/CLI hardware acceptance; never collected by pytest.

Run with the candidate's installed Python environment and an independently
provisioned BABYLON_ENCLAVE_PINNED_PUBKEY. The compiled helper must already exist
at its production path. Nothing here compiles, provisions keys, or retries.
Software tests exercise observers only; they do not establish hardware origin.
"""

from __future__ import annotations

import argparse
import base64
from contextlib import closing
import hashlib
import importlib
import json
import os
from pathlib import Path
import pwd
import secrets
import selectors
import sqlite3
import stat
import subprocess
import sys
import time
from typing import Any, Mapping

from blake3 import blake3
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec


ROOT = Path(__file__).absolute().parents[2]
EVENT = "FL_MCP01_HARDWARE_WITNESS"
IMPORTS = (
    "babylon60.cli.main_dispatcher",
    "babylon60.mcp.cortex_mcp_server",
    "babylon60.mcp.effect_dispatch",
    "babylon60.mcp.mail_integration",
    "babylon60.bft.cortex_persist_ledger",
    "babylon60.database.core",
    "babylon60.verification.verification_gate",
    "babylon60.verification.hardware_attestation",
)
MACHO_MAGICS = {b"\xcf\xfa\xed\xfe", b"\xfe\xed\xfa\xcf", b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca"}
MCP_DEADLINE_SECONDS = 20.0
MCP_RESPONSE_LIMIT = 256 * 1024


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def json_bytes(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()


def save(path: Path, value: object) -> None:
    with path.open("xb") as output:
        output.write(json_bytes(value) + b"\n")
        output.flush()
        os.fsync(output.fileno())


def reserve_attempt(directory: Path, task: Mapping[str, object]) -> None:
    """A durable exclusive marker precedes the only possible biometric call."""
    save(directory / "attempt-started.json", {"task": task, "started_at": time.time(), "attempt": 1})
    descriptor = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def regular_bytes(path: Path) -> bytes:
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    with os.fdopen(descriptor, "rb") as source:
        require(stat.S_ISREG(os.fstat(source.fileno()).st_mode), f"Not a regular file: {path}")
        return source.read()


def file_hash(path: Path) -> str:
    return blake3(regular_bytes(path)).hexdigest()


def pinned_key() -> bytes:
    # This reads only the independently provisioned pin, never the inspection.
    from babylon60.verification.hardware_attestation import configured_public_key

    return configured_public_key()


def validate_inspection(report: Mapping[str, object], key: bytes, record_hash: str) -> None:
    require(report.get("schema") == "babylon60.public-key-inspection.v1", "Unknown inspection schema")
    require(report.get("status") == "PUBLIC_KEY_INSPECTED", "Public-key inspection failed")
    require(
        report.get("origin") == "CryptoKit.SecureEnclave.P256.Signing.PrivateKey(existing_dataRepresentation)",
        "Unexpected key inspection origin",
    )
    require(report.get("token_id") is None, "Unexpected token_id claim")
    require(report.get("key_record_sha256") == record_hash, "Key record changed during inspection")
    require(report.get("public_key_sec1") == key.hex(), "Inspected key does not match the provisioned pin")


def verify_signed_record(proof_raw: str, receipt_raw: str, task: Mapping[str, object], key: bytes) -> dict[str, object]:
    """Independent cryptographic check over the exact SQLite payload bytes."""
    proof, receipt = json.loads(proof_raw), json.loads(receipt_raw)
    require(isinstance(proof, dict) and isinstance(receipt, dict), "Malformed signed record")
    payload = proof_raw.encode("utf-8")
    require(receipt.get("status") == "ATTESTED" and receipt.get("success") is not False, "Receipt did not attest")
    require(
        receipt.get("operator_user") == pwd.getpwuid(os.getuid()).pw_name, "Receipt operator does not match the OS user"
    )
    operator_name = receipt.get("operator_name")
    require(isinstance(operator_name, str) and bool(operator_name.strip()), "Receipt operator name is missing")
    digest = hashlib.sha256(payload).hexdigest()
    require(receipt.get("causal_hash") == digest, "Receipt hash differs from the complete signed proof")
    public = ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), key)
    returned = ec.EllipticCurvePublicKey.from_encoded_point(
        ec.SECP256R1(), base64.b64decode(receipt["public_key"], validate=True)
    )
    require(public.public_numbers() == returned.public_numbers(), "Receipt key differs from provisioned pin")
    public.verify(
        base64.b64decode(receipt["secure_enclave_signature"], validate=True), payload, ec.ECDSA(hashes.SHA256())
    )
    require(proof.get("version") == 1 and proof.get("decision") == "APPROVED", "Unexpected signed decision")
    require(
        json_bytes(proof.get("task")) == json_bytes(dict(task)), "Signed task differs from the task prepared by MCP"
    )
    require(isinstance(proof.get("nonce"), str) and len(proof["nonce"]) == 64, "Invalid proof nonce")
    require(proof["issued_at"] <= time.time() < proof["expires_at"], "Approval expired or issued in the future")
    require(0 < proof["expires_at"] - proof["issued_at"] <= 300, "Invalid approval lifetime")
    return {"signature_verified": True, "causal_sha256": digest, "proof_blake3": blake3(payload).hexdigest()}


def observe(ledger: Path, gate: Path, task: Mapping[str, object], key: bytes) -> dict[str, object]:
    """Read committed rows through separate mode=ro connections, including WAL."""
    with closing(sqlite3.connect(ledger.absolute().as_uri() + "?mode=ro", uri=True)) as conn:
        rows = conn.execute(
            "SELECT event_id,event_type,payload_json,entry_hash FROM cortex_ledger WHERE event_type=? ORDER BY seq",
            (EVENT,),
        ).fetchall()
        total = conn.execute("SELECT count(*) FROM cortex_ledger").fetchone()[0]
    with closing(sqlite3.connect(gate.absolute().as_uri() + "?mode=ro", uri=True)) as conn:
        approvals = conn.execute(
            "SELECT a.decision,s.payload,s.evidence FROM audit_ledger a "
            "JOIN signed_approvals s ON s.ledger_id=a.id WHERE a.execution_id=? ORDER BY a.id",
            (task["execution_id"],),
        ).fetchall()
        has_consumption = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='consumed_mcp_effects'"
        ).fetchone()
        consumed = (
            conn.execute("SELECT execution_id FROM consumed_mcp_effects ORDER BY execution_id").fetchall()
            if has_consumption
            else []
        )
    signed: list[dict[str, object]] = []
    for decision, proof, receipt in approvals:
        require(decision == "APPROVED", "Signed record has an unexpected audit decision")
        signed.append({"proof_raw": proof, "receipt_raw": receipt, **verify_signed_record(proof, receipt, task, key)})
    identity = ledger.stat()
    return {
        "pid": os.getpid(),
        "ledger_identity": [identity.st_dev, identity.st_ino],
        "total_events": total,
        "events": [
            {"event_id": r[0], "event_type": r[1], "payload": json.loads(r[2]), "entry_hash": r[3]} for r in rows
        ],
        "approvals": signed,
        "consumed": [row[0] for row in consumed],
    }


def check_observation(observation: Mapping[str, Any], task: Mapping[str, object], *, executed: bool) -> None:
    require(len(observation["approvals"]) == 1, "Expected exactly one verified signed approval")
    expected = 1 if executed else 0
    require(
        len(observation["events"]) == expected and observation["total_events"] == expected,
        "Unexpected durable event count",
    )
    require(
        observation["consumed"] == ([task["execution_id"]] if executed else []), "Unexpected durable consumption record"
    )
    if executed:
        event = observation["events"][0]
        require(
            event["payload"] == {"execution_id": task["execution_id"]},
            "Observed event payload differs from requested effect",
        )
        require(bool(event["event_id"]) and bool(event["entry_hash"]), "Event identity or hash is absent")


def probe_consumed(gate_path: Path, task: Mapping[str, object], sentinel: Path) -> dict[str, object]:
    """A fresh process must reject the original still-valid task for consumption."""
    from babylon60.verification.verification_gate import VerificationGate

    gate = VerificationGate(str(gate_path))
    try:
        require(
            gate.is_allowed(task), "Original signature is no longer valid; cannot isolate durable-consumption rejection"
        )
        try:
            gate.execute_once(task, lambda: sentinel.write_text("UNEXPECTED REPLAY"))
        except PermissionError as exc:
            require("already been consumed" in str(exc), f"Rejected for another reason: {exc}")
            require(not sentinel.exists(), "Replay produced an effect")
            return {"status": "CONSUMED_REJECTED", "execution_id": task["execution_id"], "pid": os.getpid()}
        raise ValueError("Consumed task executed again")
    finally:
        gate._conn.close()


class Peer:
    def __init__(self, directory: Path, library: Path, env: Mapping[str, str], name: str) -> None:
        self.log = (directory / f"{name}-stderr.log").open("xb")
        self.process = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-m",
                "babylon60.mcp.cortex_mcp_server",
                "--ledger",
                str(directory / "ledger.db"),
                "--causal-gate",
                str(directory / "gate.db"),
                "--capability-library",
                str(library),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=self.log,
            env=dict(env),
            cwd=ROOT,
            text=True,
        )
        self.counter = 0
        self.buffer = b""

    def call(self, method: str, params: dict[str, object]) -> dict[str, Any]:
        self.counter += 1
        request = {"jsonrpc": "2.0", "id": self.counter, "method": method, "params": params}
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(json.dumps(request) + "\n")
        self.process.stdin.flush()
        deadline = time.monotonic() + MCP_DEADLINE_SECONDS
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            while b"\n" not in self.buffer:
                remaining = deadline - time.monotonic()
                require(remaining > 0 and bool(selector.select(max(0, remaining))), "MCP response timeout; no retry")
                chunk = os.read(self.process.stdout.fileno(), 64 * 1024)
                require(bool(chunk), "MCP closed stdout before completing its response")
                self.buffer += chunk
                require(len(self.buffer) <= MCP_RESPONSE_LIMIT, "MCP response exceeds the bounded message limit")
        line, self.buffer = self.buffer.split(b"\n", 1)
        response = json.loads(line)
        require(response.get("id") == self.counter and "error" not in response, f"Invalid MCP response: {response}")
        return dict(response["result"])

    def initialize(self) -> None:
        self.call(
            "initialize",
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "hardware-acceptance", "version": "1"},
            },
        )
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n")
        self.process.stdin.flush()

    def close(self) -> None:
        if self.process.stdin is not None:
            self.process.stdin.close()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait(timeout=5)
        if self.process.stdout is not None:
            self.process.stdout.close()
        self.log.close()


def child_json(arguments: list[str], env: Mapping[str, str]) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, "-I", str(Path(__file__).absolute()), *arguments],
        capture_output=True,
        text=True,
        check=True,
        timeout=30,
        env=dict(env),
        cwd=ROOT,
    )
    return dict(json.loads(result.stdout))


def origins() -> dict[str, str]:
    result: dict[str, str] = {}
    for name in IMPORTS:
        module = importlib.import_module(name)
        require(module.__file__ is not None, f"Import has no source: {name}")
        path = Path(str(module.__file__)).absolute()
        require(path.is_relative_to(ROOT / "01_KISH_ENGINE"), f"Import escaped candidate: {name}: {path}")
        result[name] = str(path)
    return result


def run_once(args: argparse.Namespace) -> None:
    directory = args.evidence_dir.absolute()
    # Never reuse even a failed preflight's evidence directory or attempt marker.
    directory.mkdir(mode=0o700, parents=False, exist_ok=False)
    peer: Peer | None = None
    try:
        require(sys.platform == "darwin", "Hardware acceptance requires macOS")
        key = pinned_key()  # Must fail before inspection/approval if no trusted pin.
        gate = ROOT / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate"
        library = args.capability_library.absolute()
        for path in (gate, library):
            require(regular_bytes(path)[:4] in MACHO_MAGICS, f"A compiled Mach-O candidate is required: {path}")
        require(os.access(gate, os.X_OK), "Compiled helper is not executable")
        require(file_hash(gate) == args.gate_blake3, "Compiled helper hash differs from reviewed candidate")
        require(file_hash(library) == args.library_blake3, "Native library hash differs from reviewed candidate")
        status = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT)
        require(not status, "Hardware acceptance requires a clean candidate checkout")
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env["BABYLON_HOME"] = str(directory)
        record = Path(
            env.get("BABYLON_ENCLAVE_KEY_PATH", str(Path.home() / ".config/cortex/enclave_p256.key"))
        ).absolute()
        env["BABYLON_ENCLAVE_KEY_PATH"] = str(record)
        record_hash = hashlib.sha256(regular_bytes(record)).hexdigest()
        inspected = subprocess.run(
            [str(gate), "--inspect-public-key"],
            capture_output=True,
            text=True,
            check=True,
            timeout=15,
            env=env,
            cwd=ROOT,
        )
        inspection = json.loads(inspected.stdout)
        validate_inspection(inspection, key, record_hash)
        save(directory / "key-inspection.json", inspection)
        imported = child_json(["--origins"], env)
        sources = {path: file_hash(Path(path)) for path in imported.values()}
        sources[str(Path(__file__).absolute())] = file_hash(Path(__file__).absolute())
        sources[str(ROOT / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift")] = file_hash(
            ROOT / "01_KISH_ENGINE/babylon60/guards/c5_biometric_gate.swift"
        )
        hashes_before = {**sources, str(gate): file_hash(gate), str(library): file_hash(library)}
        save(
            directory / "candidate.json",
            {
                "revision": revision,
                "python": sys.executable,
                "imports": imported,
                "hashes_blake3": hashes_before,
                "pin_sec1": key.hex(),
                "pin_sha256": hashlib.sha256(key).hexdigest(),
                "key_record_sha256": record_hash,
            },
        )
        peer = Peer(directory, library, env, "first")
        peer.initialize()
        execution_id = "hardware-" + secrets.token_hex(16)
        params: dict[str, Any] = {
            "name": "bft_append_event",
            "arguments": {
                "event_type": EVENT,
                "payload": {"execution_id": execution_id},
                "cortex_taint": "hardware-acceptance",
            },
            "_meta": {"babylon60/authorization": {"execution_id": execution_id, "mode": "prepare"}},
        }
        prepared = peer.call("tools/call", params)
        require(
            prepared.get("isError") is False and isinstance(prepared.get("approval_task"), dict),
            "MCP did not prepare a task",
        )
        task = prepared["approval_task"]
        task_path = directory / "task.json"
        save(task_path, task)
        before = child_json(["--observe", str(directory), str(task_path)], env)
        require(
            before["total_events"] == 0 and before["consumed"] == [] and before["approvals"] == [],
            "Prepare produced an effect or approval",
        )
        save(directory / "observation-before.json", before)
        require({p: file_hash(Path(p)) for p in hashes_before} == hashes_before, "Candidate changed before approval")
        reserve_attempt(directory, task)
        approved = subprocess.run(
            [
                sys.executable,
                "-I",
                "-m",
                "babylon60.cli.main_dispatcher",
                "approve",
                execution_id,
                "--task-file",
                str(task_path),
                "--db",
                str(directory / "gate.db"),
            ],
            capture_output=True,
            text=True,
            timeout=40,
            env=env,
            cwd=ROOT,
        )
        save(
            directory / "approval-command.json",
            {"returncode": approved.returncode, "stdout": approved.stdout, "stderr": approved.stderr},
        )
        require(approved.returncode == 0, "Biometric approval failed; no retry is permitted")
        signed = child_json(["--observe", str(directory), str(task_path)], env)
        check_observation(signed, task, executed=False)
        save(directory / "observation-approved.json", signed)
        # Preserve the exact signed bytes, not a re-serialized proof or receipt.
        for field, filename in (("proof_raw", "signed-proof.json"), ("receipt_raw", "hardware-receipt.json")):
            with (directory / filename).open("xb") as output:
                output.write(signed["approvals"][0][field].encode("utf-8"))
                output.flush()
                os.fsync(output.fileno())
        require({p: file_hash(Path(p)) for p in hashes_before} == hashes_before, "Candidate changed after approval")
        params["_meta"]["babylon60/authorization"]["mode"] = "execute"
        executed = peer.call("tools/call", params)
        save(directory / "execution-response.json", executed)
        require(executed.get("isError") is False, "Execution failed or outcome unknown; no retry")
        after = child_json(["--observe", str(directory), str(task_path)], env)
        check_observation(after, task, executed=True)
        save(directory / "observation-executed.json", after)
        peer.close()
        peer = None
        reopened = child_json(["--observe", str(directory), str(task_path)], env)
        check_observation(reopened, task, executed=True)
        require(
            reopened["events"] == after["events"] and reopened["ledger_identity"] == before["ledger_identity"],
            "Reopen changed the witnessed effect",
        )
        save(directory / "observation-reopened.json", reopened)
        peer = Peer(directory, library, env, "restarted")
        peer.initialize()
        replay = peer.call("tools/call", params)
        save(directory / "replay-response.json", replay)
        require(replay.get("isError") is True, "Restarted MCP accepted a replay")
        consumed = child_json(["--probe-consumed", str(directory), str(task_path)], env)
        require(consumed.get("status") == "CONSUMED_REJECTED", "Consumption was not rejected independently")
        save(directory / "consumption-probe.json", consumed)
        final = child_json(["--observe", str(directory), str(task_path)], env)
        check_observation(final, task, executed=True)
        require(final["events"] == after["events"], "Replay changed the witnessed event")
        save(directory / "observation-final.json", final)
        hashes_after = {p: file_hash(Path(p)) for p in hashes_before}
        save(directory / "hashes-after.json", hashes_after)
        require(hashes_before == hashes_after, "Candidate changed during acceptance")
        require(
            hashlib.sha256(regular_bytes(record)).hexdigest() == record_hash, "Key record changed during acceptance"
        )
        save(
            directory / "result.json",
            {
                "status": "PASS",
                "execution_id": execution_id,
                "attempts": 1,
                "scope": "One signed MCP ledger append, durable consumption and rejection after restart; no OS sandbox claim.",
            },
        )
    except Exception as exc:
        save(
            directory / "result.json",
            {
                "status": "FAIL",
                "error": f"{type(exc).__name__}: {exc}",
                "attempt_started": (directory / "attempt-started.json").exists(),
                "retry_permitted": False,
            },
        )
        raise
    finally:
        if peer is not None:
            peer.close()


def main() -> None:
    if sys.argv[1:] == ["--origins"]:
        print(json.dumps(origins()))
        return
    if len(sys.argv) == 4 and sys.argv[1] in {"--observe", "--probe-consumed"}:
        directory, task_path = Path(sys.argv[2]), Path(sys.argv[3])
        task = json.loads(task_path.read_text())
        value = (
            observe(directory / "ledger.db", directory / "gate.db", task, pinned_key())
            if sys.argv[1] == "--observe"
            else probe_consumed(directory / "gate.db", task, directory / "UNEXPECTED-REPLAY")
        )
        print(json.dumps(value))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute-once", action="store_true", required=True)
    parser.add_argument("--evidence-dir", type=Path, required=True, help="New private directory; its parent must exist")
    parser.add_argument("--capability-library", type=Path, required=True)
    parser.add_argument("--gate-blake3", required=True, help="Reviewed compiled helper hash")
    parser.add_argument("--library-blake3", required=True, help="Reviewed native library hash")
    run_once(parser.parse_args())


if __name__ == "__main__":
    main()
