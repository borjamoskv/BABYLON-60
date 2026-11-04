"""Adversarial tests in disposable directories; no kernel runtime attestation."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
from collections.abc import Iterator

from blake3 import blake3
import pytest

from tools.babylon60_mcp import (
    KernelHarness,
    LEAN_TOKEN,
    SOURCE_LIMIT,
    create_server,
    lean_code,
    run_command,
    validate_loopback_host,
)


@pytest.fixture
def root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    for name in ("src", "tests", "proof/lean"):
        (root / name).mkdir(parents=True, exist_ok=True)
    (root / "src/lib.rs").write_text("// café\nfn answer() -> u8 { 41 }\n")
    (root / "Cargo.toml").write_text('[package]\nname = "fixture"\n')
    (root / "proof/lean/Main.lean").write_text("-- sorry in a comment\ntheorem identity (n : Nat) : n = n := rfl\n")
    (root / "proof/lean/lake-manifest.json").write_text("{}")
    return root


@contextmanager
def harness(root: Path, *, patches: bool = False, execution: bool = False) -> Iterator[KernelHarness]:
    instance = KernelHarness(root, allow_patches=patches, allow_execution=execution)
    try:
        yield instance
    finally:
        instance.close()


def commit_fixture(root: Path) -> None:
    for args in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "user.name=Fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "-c",
            "core.hooksPath=/dev/null",
            "commit",
            "-qm",
            "fixture",
        ],
    ):
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


@pytest.mark.parametrize(
    "name",
    [
        "/etc/passwd",
        "../repo-copy/src/lib.rs",
        "src/../Cargo.toml",
        "src//lib.rs",
        "src/./lib.rs",
        ".git/config",
        "src/secret.env",
        "src/target/test.rs",
        "src/lib.rs\x00",
        "src\\lib.rs",
        "src/.secret.rs",
        "Cargo.lock",
    ],
)
def test_reject_paths(root: Path, name: str) -> None:
    with harness(root) as h, pytest.raises((ValueError, OSError)):
        h.read_source(name)


def test_symlinks_hardlinks_and_nonregular_files(root: Path, tmp_path: Path) -> None:
    outside = tmp_path / "outside.rs"
    outside.write_text("secret")
    (root / "src/link.rs").symlink_to(outside)
    (root / "tests/link").symlink_to(tmp_path, target_is_directory=True)
    os.link(outside, root / "src/hard.rs")
    os.mkfifo(root / "src/fifo.rs")
    with harness(root, patches=True) as h:
        for name in ("src/link.rs", "tests/link/outside.rs", "src/hard.rs", "src/fifo.rs"):
            with pytest.raises((ValueError, OSError)):
                h.read_source(name)
            with pytest.raises((ValueError, OSError)):
                h.apply_atomic_patch(name, "secret", "oops", blake3(b"secret").hexdigest())
    assert outside.read_text() == "secret"


def test_logical_root_symlink_supported(root: Path, tmp_path: Path) -> None:
    alias = tmp_path / "logical"
    alias.symlink_to(root, target_is_directory=True)
    with harness(alias) as h:
        assert h.root == alias.absolute()
        assert "answer" in str(h.read_source("src/lib.rs")["content"])


def test_pagination_and_limits(root: Path) -> None:
    with harness(root) as h:
        result = h.read_source("src/lib.rs", 2, 1)
        assert result["total_lines"] == 2
        assert result["content"] == "fn answer() -> u8 { 41 }\n"
        assert result["revision"] == blake3((root / "src/lib.rs").read_bytes()).hexdigest()
        for start, count in ((0, 1), (1, 0), (1, 201)):
            with pytest.raises(ValueError):
                h.read_source("src/lib.rs", start, count)
        (root / "src/large.rs").write_bytes(b"x" * (SOURCE_LIMIT + 1))
        with pytest.raises(ValueError):
            h.read_source("src/large.rs")


def test_patch_defaults_revision_unique_and_modes(root: Path) -> None:
    file = root / "src/lib.rs"
    file.chmod(0o640)
    revision = blake3(file.read_bytes()).hexdigest()
    with harness(root) as h, pytest.raises(ValueError, match="disabled"):
        h.apply_atomic_patch("src/lib.rs", "41", "42", revision)
    with harness(root, patches=True) as h:
        for old, new in (("", "x"), ("missing", "x"), (" ", "_"), ("41", "41")):
            with pytest.raises(ValueError):
                h.apply_atomic_patch("src/lib.rs", old, new, revision)
        with pytest.raises(ValueError, match="manifests"):
            h.apply_atomic_patch("Cargo.toml", "fixture", "different", revision)
        with pytest.raises(ValueError, match="Stale"):
            h.apply_atomic_patch("src/lib.rs", "41", "42", "0" * 64)
        assert h.apply_atomic_patch("src/lib.rs", "41", "42", revision)["status"] == "patched"
        assert file.stat().st_mode & 0o777 == 0o640
        assert "42" in file.read_text()
        with pytest.raises(ValueError, match="Stale"):
            h.apply_atomic_patch("src/lib.rs", "42", "43", revision)
    assert not list((root / "src").glob(".b60-patch-*"))


def test_replace_failure_keeps_original(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    original = (root / "src/lib.rs").read_bytes()

    def fail(*args: object, **kwargs: object) -> None:
        raise OSError("injected rename failure")

    monkeypatch.setattr(os, "replace", fail)
    with harness(root, patches=True) as h, pytest.raises(OSError, match="injected"):
        h.apply_atomic_patch("src/lib.rs", "41", "42", blake3(original).hexdigest())
    assert (root / "src/lib.rs").read_bytes() == original
    assert not list((root / "src").glob(".b60-patch-*"))


def test_overlapping_matches_are_ambiguous(root: Path) -> None:
    file = root / "src/lib.rs"
    file.write_text("aaa")
    with harness(root, patches=True) as h, pytest.raises(ValueError, match="exactly once"):
        h.apply_atomic_patch("src/lib.rs", "aa", "b", blake3(b"aaa").hexdigest())
    assert file.read_text() == "aaa"


def test_patch_detects_external_edit_before_commit(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    with harness(root, patches=True) as h:
        original_read = h._read
        calls = 0

        def edit(parent: int, name: str, limit: int) -> tuple[bytes, os.stat_result]:
            nonlocal calls
            calls += 1
            if calls == 2:
                (root / "src/lib.rs").write_text("// external writer\n")
            return original_read(parent, name, limit)

        monkeypatch.setattr(h, "_read", edit)
        revision = blake3((root / "src/lib.rs").read_bytes()).hexdigest()
        with pytest.raises(ValueError, match="changed"):
            h.apply_atomic_patch("src/lib.rs", "41", "42", revision)
    assert (root / "src/lib.rs").read_text() == "// external writer\n"


def test_stress_revision_serialization_after_warmup(root: Path) -> None:
    with harness(root, patches=True) as h:
        for _ in range(5):
            h.read_source("src/lib.rs")
        for n in range(40):
            file = root / "src/lib.rs"
            file.write_text(f"const N: u64 = {n};\n")
            revision = blake3(file.read_bytes()).hexdigest()

            def compete(_: int) -> bool:
                try:
                    h.apply_atomic_patch("src/lib.rs", f"= {n};", f"= {n + 1};", revision)
                    return True
                except ValueError:
                    return False

            with ThreadPoolExecutor(max_workers=8) as pool:
                outcomes = list(pool.map(compete, range(8)))
            assert sum(outcomes) == 1
            assert file.read_text() == f"const N: u64 = {n + 1};\n"


def test_bounded_subprocesses(root: Path) -> None:
    ok = run_command([sys.executable, "-c", "print('hello')"], root)
    assert ok.status == "completed" and ok.stdout == "hello\n"
    bad = run_command([sys.executable, "-c", "raise SystemExit(7)"], root)
    assert bad.status == "failed" and bad.exit_code == 7
    missing = run_command(["/no/such/executable"], root)
    assert missing.status == "unavailable"
    slow = run_command([sys.executable, "-c", "import time; time.sleep(10)"], root, timeout=0.1)
    assert slow.status == "timeout"
    flood = run_command([sys.executable, "-c", "print('x' * 1000000)"], root)
    assert flood.status == "output_limit" and len(flood.stdout) <= 128 * 1024
    binary = run_command([sys.executable, "-c", "import os; os.write(1, b'\\xff')"], root)
    assert binary.stdout == "\ufffd"


def test_execution_disabled_dirty_and_injection(root: Path) -> None:
    with harness(root) as h:
        for call in (h.run_nemesis_and_cargo, h.audit_spsc_miri_arm64, h.verify_lean4_bijection):
            with pytest.raises(ValueError, match="disabled"):
                call()
        for arg in ("--help", "spsc;id", "spsc\n", "$(id)", "a " * 200):
            with pytest.raises(ValueError):
                h.run_nemesis_and_cargo(arg)
    commit_fixture(root)
    (root / "src/lib.rs").write_text("// dirty\n")
    with harness(root, execution=True) as h, pytest.raises(ValueError, match="clean"):
        h.run_nemesis_and_cargo()


def install_fake_tool(bin_dir: Path, name: str, body: str) -> None:
    file = bin_dir / name
    file.write_text(f"#!{sys.executable}\n" + body)
    file.chmod(0o700)


def test_execution_cannot_walk_up_from_subdirectory(root: Path) -> None:
    commit_fixture(root)
    with harness(root / "src", execution=True) as h, pytest.raises(ValueError, match="worktree root"):
        h.run_nemesis_and_cargo()


def test_dispatch_and_no_empty_success(root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    commit_fixture(root)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    install_fake_tool(bin_dir, "protoc", "pass\n")
    install_fake_tool(
        bin_dir,
        "cargo",
        "import json,os,sys\nprint(json.dumps([sys.argv[1:],os.getenv('MIRIFLAGS')]))\nprint('test result: ok. 3 passed; 0 failed;')\n",
    )
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    monkeypatch.setenv("MIRIFLAGS", "-Zmiri-disable-validation")
    with harness(root, execution=True) as h:
        result = h.run_nemesis_and_cargo("nemesis_v3")
        assert result["status"] == "completed" and result["tests_passed"] == 3
        args, flags = json.loads(str(result["stdout"]).splitlines()[0])
        assert "--locked" in args and "--offline" in args and "nemesis_v3" in args
        assert flags is None
        result = h.audit_spsc_miri_arm64("tree")
        args, flags = json.loads(str(result["stdout"]).splitlines()[0])
        assert "aarch64-apple-darwin" in args and "--locked" in args
        assert "-Zmiri-tree-borrows" in flags and "-Zmiri-disable-validation" not in flags
        install_fake_tool(bin_dir, "cargo", "print('test result: ok. 0 passed; 0 failed;')\n")
        assert h.run_nemesis_and_cargo()["status"] == "no_tests"
        install_fake_tool(bin_dir, "cargo", "raise SystemExit(2)\n")
        assert h.run_nemesis_and_cargo()["status"] == "failed"


def test_lean_comments_strings_and_nested_comments() -> None:
    text = '-- sorry\n/- outer /- admit -/ sorryAx -/\n#eval "sorry \\" admit"\nexample : False := sorry\n'
    code = lean_code(text)
    assert [m.group() for m in LEAN_TOKEN.finditer(code)] == ["sorry"]
    assert code.count("\n") == text.count("\n")


def test_lean_veto_and_compilation_is_not_bijection(
    root: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commit_fixture(root)
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    install_fake_tool(bin_dir, "lake", "print('build complete')\n")
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ["PATH"])
    with harness(root, execution=True) as h:
        result = h.verify_lean4_bijection()
        assert result["status"] == "completed" and result["bijection_verified"] is False
        assert result["argv"] == ["lake", "--wfail", "--no-cache", "build"]
    (root / "proof/lean/Main.lean").write_text("-- ñ\nexample : False := sorry\n")
    commit_fixture(root)
    with harness(root, execution=True) as h:
        result = h.verify_lean4_bijection()
        assert result["status"] == "formal_veto"
        assert result["violations"] == ["proof/lean/Main.lean:2:sorry"]


def test_sqlite_snapshot_does_not_write_or_claim_invariants(root: Path) -> None:
    db = root / "tests/export ?#.sqlite"
    conn = sqlite3.connect(db)
    conn.executescript(
        "CREATE TABLE events(id INTEGER PRIMARY KEY, payload TEXT); CREATE TRIGGER immutable BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT, 'immutable'); END;"
    )
    conn.close()
    before = db.read_bytes()
    mtime = db.stat().st_mtime_ns
    with harness(root) as h:
        result = h.inspect_sqlite_l0_invariants("tests/export ?#.sqlite")
        assert result["runtime_invariants"] == "not_verified"
        objs = result["objects"]
        assert isinstance(objs, list)
        assert {obj["type"] for obj in objs} == {"table", "trigger"}
        assert db.read_bytes() == before and db.stat().st_mtime_ns == mtime
        for suffix in ("-wal", "-shm", "-journal"):
            sidecar = Path(str(db) + suffix)
            sidecar.write_bytes(b"x")
            with pytest.raises(ValueError, match="checkpointed"):
                h.inspect_sqlite_l0_invariants("tests/export ?#.sqlite")
            sidecar.unlink()
    assert list((root / "tests").iterdir()) == [db]


def test_stdio_six_tools_and_denied_patch(root: Path) -> None:
    pytest.importorskip("fastmcp")
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    import tools.babylon60_mcp as module

    async def scenario() -> None:
        params = StdioServerParameters(
            command=sys.executable, args=[str(Path(module.__file__).absolute()), "--root", str(root)]
        )
        async with stdio_client(params) as (reader, writer), ClientSession(reader, writer) as session:
            await session.initialize()
            listing = await session.list_tools()
            assert {tool.name for tool in listing.tools} == {
                "read_source",
                "apply_atomic_patch",
                "run_nemesis_and_cargo",
                "audit_spsc_miri_arm64",
                "verify_lean4_bijection",
                "inspect_sqlite_l0_invariants",
                "babylon_signature_render",
            }
            read = await session.call_tool("read_source", {"rel_path": "src/lib.rs"})
            assert not read.is_error
            assert "answer" in json.dumps(read.model_dump(by_alias=True))
            denied = await session.call_tool(
                "apply_atomic_patch",
                {
                    "rel_path": "src/lib.rs",
                    "old_block": "41",
                    "new_block": "42",
                    "expected_revision": blake3((root / "src/lib.rs").read_bytes()).hexdigest(),
                },
            )
            assert denied.is_error
            escape = await session.call_tool("read_source", {"rel_path": "../outside.rs"})
            assert escape.is_error

    asyncio.run(scenario())


def test_loopback_host_confinement() -> None:
    assert validate_loopback_host("127.0.0.1") == "127.0.0.1"
    assert validate_loopback_host("::1") == "::1"
    assert validate_loopback_host("localhost") == "localhost"
    for forbidden in ("0.0.0.0", "192.168.1.10", "10.0.0.1", "example.com"):
        with pytest.raises(ValueError, match="Refusing non-loopback"):
            validate_loopback_host(forbidden)


def test_openapi_contract_parity_with_mcp_tools(root: Path) -> None:
    from tools.babylon60_mcp import build_openapi_spec

    repo_root = Path(__file__).absolute().parents[1]
    openapi_path = repo_root / "contracts" / "openapi_babylon60_kernel.json"
    spec = json.loads(openapi_path.read_text(encoding="utf-8"))
    assert spec == build_openapi_spec()
    assert spec["openapi"] == "3.1.0"
    operation_ids = {op["post"]["operationId"] for op in spec["paths"].values()}
    pytest.importorskip("fastmcp")
    harness = KernelHarness(root)
    try:
        server = create_server(harness)
        registered_tools = asyncio.run(server.list_tools())
        mcp_names = {tool.name for tool in registered_tools}
    finally:
        harness.close()
    assert operation_ids == mcp_names


def test_openapi_http_loopback_server_e2e(root: Path) -> None:
    import threading
    from urllib import error as urlerror, request as urlrequest
    from tools.babylon60_mcp import create_openapi_http_server

    token = "b60-secret-loopback-token-2026"
    harness = KernelHarness(root)
    try:
        with pytest.raises(ValueError, match="at least 16 characters"):
            create_openapi_http_server(harness, host="127.0.0.1", port=0, bearer_token="short")
        server = create_openapi_http_server(harness, host="127.0.0.1", port=0, bearer_token=token)
        host, port = server.server_address[:2]
        host_str = host.decode("utf-8") if isinstance(host, bytes) else str(host)
        base_url = f"http://{host_str}:{port}"
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with urlrequest.urlopen(f"{base_url}/openapi.json", timeout=3) as resp:
                assert resp.status == 200
                assert resp.headers.get("cache-control") == "no-store"
                assert resp.headers.get("x-content-type-options") == "nosniff"
                spec_data = json.loads(resp.read().decode("utf-8"))
                assert spec_data["openapi"] == "3.1.0"

            unauth_req = urlrequest.Request(
                f"{base_url}/tools/read_source",
                data=b'{"rel_path":"src/lib.rs"}',
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with pytest.raises(urlerror.HTTPError) as exc_info:
                urlrequest.urlopen(unauth_req, timeout=3)
            assert exc_info.value.code == 401

            auth_req = urlrequest.Request(
                f"{base_url}/tools/read_source",
                data=b'{"rel_path":"src/lib.rs","start_line":1,"max_lines":2}',
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with urlrequest.urlopen(auth_req, timeout=3) as resp:
                assert resp.status == 200
                assert resp.headers.get("cache-control") == "no-store"
                assert resp.headers.get("x-content-type-options") == "nosniff"
                payload = json.loads(resp.read().decode("utf-8"))
                assert payload["path"] == "src/lib.rs"
                assert "41" in payload["content"]

            bad_ct_req = urlrequest.Request(
                f"{base_url}/tools/read_source",
                data=b'{"rel_path":"src/lib.rs"}',
                headers={
                    "Content-Type": "text/plain",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with pytest.raises(urlerror.HTTPError) as exc_ct:
                urlrequest.urlopen(bad_ct_req, timeout=3)
            assert exc_ct.value.code == 415

            del_req = urlrequest.Request(
                f"{base_url}/tools/read_source",
                headers={
                    "Authorization": f"Bearer {token}",
                },
                method="DELETE",
            )
            with pytest.raises(urlerror.HTTPError) as exc_del:
                urlrequest.urlopen(del_req, timeout=3)
            assert exc_del.value.code == 405

            escape_req = urlrequest.Request(
                f"{base_url}/tools/read_source",
                data=b'{"rel_path":"../outside.rs"}',
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {token}",
                },
                method="POST",
            )
            with pytest.raises(urlerror.HTTPError) as exc_escape:
                urlrequest.urlopen(escape_req, timeout=3)
            assert exc_escape.value.code == 400
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=3)
    finally:
        harness.close()
