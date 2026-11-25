"""Real Linux L3+L4 OS-boundary escape and mediation tests (Landlock LSM + seccomp-BPF)."""

from __future__ import annotations

import asyncio
import hashlib
import os
import platform
import socket
import sys
from pathlib import Path
from unittest.mock import Mock

from blake3 import blake3
import pytest

from babylon60.kernel import mcp_linux_sandbox as linux_sandbox
from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_lifecycle_manager import McpLifecycleManager
from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator
from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder

pytestmark = pytest.mark.skipif(sys.platform != "linux", reason="Real Landlock+seccomp backend requires Linux")


def _witness_snapshot(path: Path) -> tuple[str, int, int]:
    st = path.stat()
    return hashlib.sha256(path.read_bytes()).hexdigest(), st.st_ino, st.st_size


def test_real_linux_protocol_and_confinement_evidence(tmp_path: Path) -> None:
    contract = McpCandidateContract("probe", "probe", "Arithmetic", implementation_body="return 2 + 2")
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})
    assert result["is_valid"] is True, result
    output = result["tool_output"]
    assert isinstance(output, dict) and output["result"] == 4
    assert result["code_hash"] == blake3(Path(script).read_bytes()).hexdigest()
    assert result["isolation_backend"] == "linux-landlock-seccomp"
    evidence = result["isolation_evidence"]
    assert isinstance(evidence, dict)
    assert set(evidence) == linux_sandbox.LINUX_EXPECTED_PROBE_KEYS
    assert all(value is True for value in evidence.values())
    assert Path(script).exists()


def test_directed_escape_matrix_and_independent_witness(tmp_path: Path) -> None:
    protected = tmp_path / "protected"
    protected.mkdir(mode=0o700)
    victim = protected / "victim.bin"
    ledger = protected / "ledger.db"
    keyfile = protected / "broker.key"
    victim.write_bytes(os.urandom(64))
    ledger.write_bytes(b"LEDGER_GENESIS_SEALED_0001")
    keyfile.write_text("SECRET_ED25519_PRIVATE_KEY_DO_NOT_LEAK")

    before = {
        "victim": _witness_snapshot(victim),
        "ledger": _witness_snapshot(ledger),
        "key": _witness_snapshot(keyfile),
    }

    secret_fd = os.open(str(victim), os.O_RDONLY)
    os.set_inheritable(secret_fd, True)
    try:
        arch = platform.machine()
        sc = linux_sandbox.SYSCALL_TABLES[arch]
        # Note: AST gate forbids `import ctypes/os/socket/subprocess` in LLM-generated bodies,
        # so for this L3+L4 OS kernel escape test we materialize an adversarial MCP server script
        # directly (simulating full AST-gate bypass) to prove OS-level Landlock + seccomp enforcement.
        adversarial_server = tmp_path / "adversarial_mcp.py"
        adversarial_server.write_text(
            f"""import ctypes, errno, json, os, socket, sys
from pathlib import Path

def run_escape_suite():
    attacks = {{}}
    def expect_denied(name, fn):
        try:
            fn()
        except OSError as exc:
            attacks[name] = exc.errno in (errno.EACCES, errno.EPERM, errno.EBADF, errno.EXDEV, errno.ENOENT)
        else:
            attacks[name] = False

    victim = Path({str(victim)!r})
    ledger = Path({str(ledger)!r})
    keyfile = Path({str(keyfile)!r})
    work = Path.cwd()

    expect_denied("read_victim_abs", lambda: victim.read_bytes())
    expect_denied("read_victim_rel", lambda: (work / ".." / ".." / "protected" / "victim.bin").read_bytes())
    expect_denied("write_victim", lambda: victim.write_bytes(b"tampered"))
    expect_denied("unlink_victim", lambda: victim.unlink())
    expect_denied("rename_ledger", lambda: ledger.rename(work / "stolen.db"))
    expect_denied("read_key", lambda: keyfile.read_text())

    sym = work / "sym_victim"
    sym.symlink_to(victim)
    expect_denied("symlink_read_victim", lambda: sym.read_bytes())
    expect_denied("hardlink_victim", lambda: os.link(victim, work / "hard_victim"))
    expect_denied("proc_self_fd", lambda: os.listdir("/proc/self/fd"))
    expect_denied("inherited_fd_read", lambda: os.read({secret_fd}, 16))
    expect_denied("socket_unix_scm_rights", lambda: socket.socket(socket.AF_UNIX, socket.SOCK_STREAM))
    expect_denied("socket_inet", lambda: socket.socket(socket.AF_INET, socket.SOCK_STREAM))
    expect_denied("fork_clone", lambda: os.fork())

    lib = ctypes.CDLL(None, use_errno=True)
    lib.syscall.restype = ctypes.c_long
    def sys_check(name, nr, *args):
        ctypes.set_errno(0)
        rc = lib.syscall(ctypes.c_long(nr), *[ctypes.c_long(a) for a in args])
        err = ctypes.get_errno()
        attacks[name] = (rc == -1 and err in (errno.EPERM, errno.EACCES))

    sys_check("ptrace", {sc["ptrace"]}, 0, 0, 0, 0)
    sys_check("process_vm_writev", {sc["process_vm_writev"]}, os.getpid(), 0, 0, 0, 0, 0)
    sys_check("unshare", {sc["unshare"]}, 0x10000000)
    sys_check("mount", {sc["mount"]}, 0, 0, 0, 0, 0)
    sys_check("bpf", {sc["bpf"]}, 0, 0, 0)

    pos = work / "allowed.txt"
    pos.write_text("C5-WORKDIR-EXTRA")
    with open(pos, "r+") as fh:
        fh.truncate(len("C5-WORKDIR"))
    return {{"attacks": attacks, "positive_workdir": pos.read_text() == "C5-WORKDIR"}}

for line in sys.stdin:
    req = json.loads(line)
    rid = req["id"]
    method = req["method"]
    if method == "initialize":
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"protocolVersion": "2024-11-05", "capabilities": {{}}}}}}
    elif method == "tools/list":
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"tools": [{{"name": "escape_probe"}}]}}}}
    elif method == "tools/call":
        payload = run_escape_suite()
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"content": [{{"type": "text", "text": json.dumps(payload)}}]}}}}
    print(json.dumps(resp), flush=True)
"""
        )
        contract = McpCandidateContract("EscapeServer", "escape_probe", "L3 escape matrix")
        result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(adversarial_server), contract, {})
    finally:
        os.close(secret_fd)

    assert result["is_valid"] is True, result
    assert result["isolation_backend"] == "linux-landlock-seccomp"
    tool_out = result["tool_output"]
    assert isinstance(tool_out, dict)
    attacks = tool_out["attacks"]
    assert isinstance(attacks, dict) and len(attacks) == 18
    assert all(val is True for val in attacks.values()), attacks
    assert tool_out["positive_workdir"] is True

    after = {
        "victim": _witness_snapshot(victim),
        "ledger": _witness_snapshot(ledger),
        "key": _witness_snapshot(keyfile),
    }
    assert before == after


def test_preflight_failure_launches_zero_payloads(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    launch = Mock(side_effect=AssertionError("Must not launch subprocess when Landlock ABI is insufficient"))
    monkeypatch.setattr(asyncio, "create_subprocess_exec", launch)
    monkeypatch.setattr(
        linux_sandbox,
        "linux_runtime",
        lambda: (_ for _ in ()).throw(RuntimeError("Landlock LSM unavailable or ABI 0 < 1")),
    )
    script = tmp_path / "never_run.py"
    script.write_text("raise RuntimeError('must never execute')\n")
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(script), McpCandidateContract("p", "p", "p"), {})
    assert result["is_valid"] is False
    assert result["error_code"] == "OS_ISOLATION_UNAVAILABLE"
    launch.assert_not_called()
    assert script.read_text() == "raise RuntimeError('must never execute')\n"


def test_broker_mediated_mcp_bomb_lifecycle_on_linux(tmp_path: Path) -> None:
    db_path = tmp_path / "broker_ledger.db"
    lifecycle = McpLifecycleManager(db_path=str(db_path))
    receipt = lifecycle.synthesize_and_detonate_bomb(
        domain_name="LinuxVectorNorm",
        implementation_body="return {'hypot': round(math.hypot(x, y), 4), 'manhattan': abs(x) + abs(y)}",
        call_arguments={"x": 3, "y": 4},
        description="Broker-mediated execution under Linux Landlock+seccomp confinement.",
        output_dir=str(tmp_path),
    )
    assert receipt["status"] == "SUCCESS", receipt
    assert receipt["is_valid"] is True
    assert receipt["isolation_backend"] == "linux-landlock-seccomp"
    assert all(receipt["isolation_evidence"].values())
    assert receipt["self_destruct_verified"] is True
    assert receipt["tool_output"]["result"] == {"hypot": 5.0, "manhattan": 7}
    assert lifecycle.list_active_mcps() == []


def test_scm_rights_socketpair_and_fd_passing_blocked(tmp_path: Path) -> None:
    victim = tmp_path / "secret_target.txt"
    victim.write_text("TOP_SECRET_KERNEL_DATA")
    before = _witness_snapshot(victim)

    parent_sock, child_sock = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)
    secret_fd = os.open(str(victim), os.O_RDONLY)
    os.set_inheritable(child_sock.fileno(), True)
    try:
        # Send secret_fd into the socket buffer before launching child
        socket.send_fds(parent_sock, [b"fd"], [secret_fd])
        child_fd_num = child_sock.fileno()
        server_script = tmp_path / "scm_rights_mcp.py"
        server_script.write_text(
            f"""import errno, json, os, socket, sys
def probe_scm():
    out = {{}}
    try:
        s = socket.socket(fileno={child_fd_num})
        _, fds, _, _ = socket.recv_fds(s, 16, 1)
        out["recv_fds_blocked"] = False
    except OSError as exc:
        out["recv_fds_blocked"] = exc.errno in (errno.EBADF, errno.EPERM, errno.ENOTSOCK)
    return out

for line in sys.stdin:
    req = json.loads(line)
    rid = req["id"]
    m = req["method"]
    if m == "initialize":
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"protocolVersion": "2024-11-05", "capabilities": {{}}}}}}
    elif m == "tools/list":
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"tools": [{{"name": "scm_probe"}}]}}}}
    elif m == "tools/call":
        resp = {{"jsonrpc": "2.0", "id": rid, "result": {{"content": [{{"type": "text", "text": json.dumps(probe_scm())}}]}}}}
    print(json.dumps(resp), flush=True)
"""
        )
        contract = McpCandidateContract("ScmServer", "scm_probe", "SCM_RIGHTS block check")
        result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(server_script), contract, {})
    finally:
        os.close(secret_fd)
        parent_sock.close()
        child_sock.close()

    assert result["is_valid"] is True, result
    assert result["tool_output"] == {"recv_fds_blocked": True}
    assert _witness_snapshot(victim) == before


@pytest.mark.parametrize("source", ["while True: pass", "import os\nwhile True: os.write(1, b'x' * 65536)"])
def test_timeout_and_output_limits_linux(tmp_path: Path, source: str) -> None:
    script = tmp_path / "limits.py"
    script.write_text(source)
    contract = McpCandidateContract("probe", "probe", "Bounded resources")
    result = McpSandboxValidator().execute_and_detonate_mcp_sync(str(script), contract, {}, timeout_seconds=1)
    assert result["is_valid"] is False
    assert result["error_code"] in ("TIMEOUT", "EXECUTION_FAILED", "OS_ISOLATION_UNAVAILABLE"), result
    if "os.write" in source:
        assert "output exceeds" in str(result["reason"])
