"""Real Unix socket paths and Seatbelt checks without shortening the runtime root."""

import asyncio
from collections.abc import Iterator
import json
import os
from pathlib import Path
import socket
import stat
import subprocess
import sys
import tempfile

import pytest

from babylon60.kernel import mcp_sandbox_validator as sandbox
from babylon60.kernel.mcp_deductive_engine import McpCandidateContract
from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder


pytestmark = pytest.mark.skipif(sys.platform not in {"darwin", "linux"}, reason="Known Unix socket pathname limits")
SOCKET_LIMIT = 103 if sys.platform == "darwin" else 107


@pytest.fixture
def short_root() -> Iterator[Path]:
    with tempfile.TemporaryDirectory(prefix="b60path-", dir="/tmp") as directory:
        yield Path(os.path.realpath(directory))


def _connect(listener: socket.socket, path: str) -> None:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        client.connect(path)
        listener.settimeout(1)
        peer, _ = listener.accept()
        with peer:
            client.sendall(b"x")
            assert peer.recv(1) == b"x"


@pytest.mark.parametrize("extra", [0, 1])
@pytest.mark.parametrize("unicode_path", [False, True])
def test_real_os_pathname_boundary(short_root: Path, extra: int, unicode_path: bool) -> None:
    size = SOCKET_LIMIT + extra - len(os.fsencode(short_root)) - len(b"/sock") - 1
    component = ("é" * (size // 2) + "x" * (size % 2)) if unicode_path else "x" * size
    directory = short_root / component
    directory.mkdir(mode=0o700)
    path = str(directory / "sock")
    assert len(os.fsencode(path)) == SOCKET_LIMIT + extra
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        if extra:
            with pytest.raises(OSError, match="path too long"):
                listener.bind(path)
        else:
            listener.bind(path)
            listener.listen(1)
            _connect(listener, path)


@pytest.mark.parametrize("extra", [0, 1])
@pytest.mark.parametrize("unicode_path", [False, True])
def test_factory_uses_canonical_byte_boundary(
    short_root: Path, monkeypatch: pytest.MonkeyPatch, extra: int, unicode_path: bool
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(short_root))
    with sandbox._unix_listener() as (_, initial_path):
        overhead = len(os.fsencode(initial_path)) - len(os.fsencode(short_root))
    size = SOCKET_LIMIT + extra - overhead - len(os.fsencode(short_root)) - 1
    component = ("é" * (size // 2) + "x" * (size % 2)) if unicode_path else "x" * size
    directory = short_root / component
    directory.mkdir(mode=0o700)
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    with sandbox._unix_listener() as (listener, path):
        assert path == os.path.realpath(path)
        assert len(os.fsencode(path)) <= SOCKET_LIMIT
        expected_parent = Path(os.path.realpath("/tmp")) if extra else directory
        assert Path(path).parent.parent == expected_parent
        if not extra:
            assert len(os.fsencode(path)) == SOCKET_LIMIT
        assert stat.S_IMODE(Path(path).parent.stat().st_mode) == 0o700
        _connect(listener, path)
    assert listener.fileno() == -1
    assert not Path(path).parent.exists()
    assert list(directory.iterdir()) == []


def test_short_symlink_to_long_root_uses_fallback(
    tmp_path: Path, short_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / ("long-root-" * 12)
    target.mkdir()
    link = short_root / "t"
    link.symlink_to(target, target_is_directory=True)
    assert len(os.fsencode(link / "babylon60_ipc_12345678/sock")) <= SOCKET_LIMIT
    monkeypatch.setattr(tempfile, "tempdir", str(link))
    monkeypatch.setenv("TMPDIR", str(link))
    with sandbox._unix_listener() as (listener, path):
        assert Path(path).parent.parent == Path(os.path.realpath("/tmp"))
        assert path == os.path.realpath(path)
        _connect(listener, path)
        assert tempfile.tempdir == str(link)
        assert os.environ["TMPDIR"] == str(link)
    assert list(target.iterdir()) == []
    assert link.is_symlink()


@pytest.mark.parametrize("outcome", ["success", "error", "cancel"])
def test_listener_cleanup_on_every_exit(short_root: Path, monkeypatch: pytest.MonkeyPatch, outcome: str) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(short_root))
    listener: socket.socket
    path: str

    def exercise() -> None:
        nonlocal listener, path
        with sandbox._unix_listener() as (listener, path):
            _connect(listener, path)
            if outcome == "error":
                raise RuntimeError("deliberate exit after bind")
            if outcome == "cancel":
                raise asyncio.CancelledError

    if outcome == "success":
        exercise()
    else:
        error = RuntimeError if outcome == "error" else asyncio.CancelledError
        with pytest.raises(error):
            exercise()
    assert listener.fileno() == -1
    assert not Path(path).exists()
    assert not Path(path).parent.exists()
    assert list(short_root.iterdir()) == []


def test_concurrent_listener_directories_are_private_and_unique(
    short_root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(short_root))
    with sandbox._unix_listener() as (first, first_path), sandbox._unix_listener() as (second, second_path):
        assert first_path != second_path
        assert Path(first_path).parent != Path(second_path).parent
        for listener, path in ((first, first_path), (second, second_path)):
            assert stat.S_IMODE(Path(path).parent.stat().st_mode) == 0o700
            _connect(listener, path)
    assert list(short_root.iterdir()) == []


def test_listener_cleanup_after_task_cancellation(short_root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(short_root))
    owned: list[tuple[socket.socket, str]] = []

    async def cancel_pending_listener() -> None:
        ready = asyncio.Event()

        async def pending() -> None:
            with sandbox._unix_listener() as (listener, path):
                owned.append((listener, path))
                _connect(listener, path)
                ready.set()
                await asyncio.Future[None]()

        task = asyncio.create_task(pending())
        await asyncio.wait_for(ready.wait(), 1)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(cancel_pending_listener())
    assert len(owned) == 1
    listener, path = owned[0]
    assert listener.fileno() == -1 and not Path(path).parent.exists()
    assert list(short_root.iterdir()) == []


def test_repeated_fallback_listener_cleanup(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / ("long-temp-" * 12)
    runtime.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(runtime))
    paths: set[str] = set()
    # Five warmup allocations, then 64 real bind/connect/close/remove cycles.
    for _ in range(5 + 64):
        with sandbox._unix_listener() as (listener, path):
            assert path not in paths
            paths.add(path)
            assert Path(path).parent.parent == Path(os.path.realpath("/tmp"))
            _connect(listener, path)
        assert listener.fileno() == -1 and not Path(path).parent.exists()
    assert list(runtime.iterdir()) == []


@pytest.mark.parametrize("prefix", ["", ".", "..", "/absolute", "../escape", "a/b", "a\\b", "bad\0", "bad\n"])
def test_invalid_prefix_rejected_before_creating_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, prefix: str
) -> None:
    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path / "missing"))
    with pytest.raises(ValueError, match="simple basename"), sandbox._unix_listener(prefix=prefix):
        pytest.fail("invalid prefix yielded a listener")
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("artifact", ["missing", "file"])
def test_primary_creation_error_does_not_fall_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, artifact: str
) -> None:
    directory = tmp_path / artifact
    if artifact == "file":
        directory.write_text("must remain unchanged")
    monkeypatch.setattr(tempfile, "tempdir", str(directory))
    with pytest.raises(OSError), sandbox._unix_listener():
        pytest.fail("a failed primary creation fell back")
    if artifact == "file":
        assert directory.read_text() == "must remain unchanged"
    else:
        assert not directory.exists()


@pytest.mark.skipif(sys.platform != "darwin", reason="Real Seatbelt backend requires macOS")
@pytest.mark.parametrize("temporary_root", ["native", "long"])
def test_real_validator_with_long_tmpdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, temporary_root: str) -> None:
    native = tempfile.gettempdir()
    runtime = Path(native) if temporary_root == "native" else tmp_path / ("long-temp-" * 12)
    if temporary_root == "long":
        runtime.mkdir()
    before = set(runtime.glob("babylon60_*"))
    before_fallback = set(Path("/tmp").glob("babylon60_ipc_*"))
    monkeypatch.setattr(tempfile, "tempdir", str(runtime))
    monkeypatch.setenv("TMPDIR", str(runtime))
    contract = McpCandidateContract("probe", "probe", "Long temporary root", implementation_body="return 41")
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)
    result = sandbox.McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})
    assert result["is_valid"] is True, result
    assert result["isolation_backend"] == "macos-seatbelt"
    evidence = result["isolation_evidence"]
    assert isinstance(evidence, dict) and all(value is True for value in evidence.values())
    output = result["tool_output"]
    assert isinstance(output, dict) and output["result"] == 41
    assert set(runtime.glob("babylon60_*")) == before
    assert set(Path("/tmp").glob("babylon60_ipc_*")) == before_fallback
    assert Path(script).is_file()


@pytest.mark.skipif(sys.platform != "darwin", reason="Real Seatbelt backend requires macOS")
def test_long_tmpdir_keeps_work_and_external_canary_isolated(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    runtime = tmp_path / ("long-temp-" * 12)
    runtime.mkdir()
    canary = runtime / "external-canary"
    canary.write_text("private canary")
    monkeypatch.setattr(tempfile, "tempdir", str(runtime))
    monkeypatch.setenv("TMPDIR", str(runtime))
    body = (
        f"from pathlib import Path\npath = Path({str(canary)!r})\n"
        "try:\n    path.read_text()\n    return 'escaped read'\nexcept PermissionError:\n    pass\n"
        "try:\n    path.write_text('escaped write')\n    return 'escaped write'\n"
        "except PermissionError:\n    return str(Path.cwd())"
    )
    contract = McpCandidateContract("probe", "probe", "Canary isolation", implementation_body=body)
    script = McpCodeScaffolder(str(tmp_path)).scaffold_fastmcp_python(contract)
    result = sandbox.McpSandboxValidator().execute_and_detonate_mcp_sync(script, contract, {})
    assert result["is_valid"] is True, result
    output = result["tool_output"]
    assert isinstance(output, dict)
    work = Path(output["result"])
    assert work.name == "work" and work.parent.parent == runtime
    assert not work.exists()
    assert canary.read_text() == "private canary"
    assert list(runtime.iterdir()) == [canary]


@pytest.mark.skipif(sys.platform != "darwin", reason="Real Seatbelt backend requires macOS")
@pytest.mark.parametrize("descriptor", [1, 2], ids=["stdout", "stderr"])
def test_output_overflow_finishes_and_removes_private_artifacts(
    tmp_path: Path, short_root: Path, descriptor: int
) -> None:
    script = tmp_path / "overflow.py"
    script.write_text(f"import os\nwhile True: os.write({descriptor}, b'x' * 65536)")
    program = (
        "import json, sys\n"
        "from babylon60.kernel.mcp_deductive_engine import McpCandidateContract\n"
        "from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator\n"
        "result = McpSandboxValidator().execute_and_detonate_mcp_sync(\n"
        "    sys.argv[1], McpCandidateContract('probe', 'probe', 'Bounded output'), {}, timeout_seconds=1)\n"
        "print(json.dumps(result))\n"
    )
    env = dict(os.environ)
    env["TMPDIR"] = str(short_root)
    env["PYTHONPATH"] = str(Path(sandbox.__file__).parent.parent.parent)
    completed = subprocess.run(
        [sys.executable, "-c", program, str(script)],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        timeout=8,
        check=True,
    )
    result = json.loads(completed.stdout)
    assert result["is_valid"] is False
    assert "output exceeds 1 MiB" in result["reason"], result
    assert list(short_root.iterdir()) == []
    assert script.is_file()
