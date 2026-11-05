#!/usr/bin/env python3
"""Exercise a final Docker image without mounts, host state, or external runtime networking.

Build mode performs a complete uncached build. --runtime-only deliberately does
not certify that build: combine its evidence with a separately recorded build.
The dashboard remains bound to the container's loopback; HTTP probes run inside
that container, and no host port is published.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import queue
import re
import subprocess
import sys
import threading
import time
from typing import Any
import uuid


class SmokeFailure(RuntimeError):
    """An observed result did not satisfy the smoke contract."""


IDENTITY_AND_RESOURCES = r'''
import json, os, tempfile
from pathlib import Path
import babylon60, z3
from babylon60.mcp.cortex_mcp_server import CortexMCPServer
from babylon60.mcp.skills_snapshot import ImmutableSkillsSnapshot
from babylon60.state_paths import state_home, causal_gate_path

if not __debug__:
    raise RuntimeError("smoke probes require enabled assertions")
uid = os.geteuid()
assert uid != 0, "runtime is root"
origin = Path(babylon60.__file__)
assert origin.is_relative_to(Path("/app/.venv")), f"project is not installed: {origin}"
assert z3.is_true(z3.simplify(z3.IntVal(2) + 3 == 5)), "Z3 native runtime failed"
pid1_uid = [line for line in Path("/proc/1/status").read_text().splitlines() if line.startswith("Uid:")][0]
assert all(int(value) != 0 for value in pid1_uid.split()[1:]), pid1_uid
home = Path.home()
state = state_home()
assert state.is_relative_to(home), f"state outside user home: {state}"
assert not state.exists(), f"image contains pre-existing runtime state: {state}"
state.mkdir(parents=True)
with tempfile.TemporaryFile(dir=state) as file:
    file.write(b"babylon60-container-write-probe")
    file.seek(0)
    assert file.read() == b"babylon60-container-write-probe"
assert state.stat().st_uid == uid
gate = causal_gate_path()
assert gate.is_relative_to(state), f"gate outside state: {gate}"
server = object.__new__(CortexMCPServer)
catalog = server._resolve_skills_json_path()
skills = server._resolve_skills_dir()
assert catalog is not None and catalog.is_file(), "required skills.json missing"
assert skills is not None and skills.is_dir(), "required physical skills missing"
pin = catalog.with_name("skills-lock.json")
assert pin.is_file(), "required skills-lock.json missing"
snapshot = ImmutableSkillsSnapshot.load(catalog, skills, lockfile_path=pin)
assert snapshot.to_lockfile() == json.loads(pin.read_text()), "snapshot/pin mismatch"
assert snapshot.total_skills > 0 and snapshot.workspace_skill_names, "empty skills snapshot"
for location in (Path.cwd(), Path("/app")):
    for relative in (".env", ".git", ".mypy_cache", ".pytest_cache", ".ruff_cache",
                     "causal_gate.db", "mcp_ledger.db", ".cortex/causal_gate.db"):
        assert not (location / relative).exists(), f"host state in image: {location / relative}"
print(json.dumps({"uid": uid, "pid1_uid": pid1_uid, "home": str(home), "state": str(state),
    "package_origin": str(origin), "z3_version": z3.get_version_string(),
    "state_writable": True, "catalog": str(catalog), "skills": str(skills), "pin": str(pin),
    "total_skills": snapshot.total_skills, "workspace_skills": len(snapshot.workspace_skill_names),
    "snapshot_root": snapshot.root_sha256}))
'''


DASHBOARD_HTTP = r'''
import json, os, sqlite3, time, urllib.request
from pathlib import Path
from babylon60.dashboard.server import _get_db_path
if not __debug__:
    raise RuntimeError("smoke probes require enabled assertions")
assert os.geteuid() != 0
pid1_uid = [line for line in Path("/proc/1/status").read_text().splitlines() if line.startswith("Uid:")][0]
assert all(int(value) != 0 for value in pid1_uid.split()[1:]), pid1_uid
deadline = time.monotonic() + float(os.environ.get("SMOKE_HTTP_TIMEOUT", "20"))
while True:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/", timeout=2) as response:
            html = response.read().decode()
            assert response.status == 200
            assert response.headers.get_content_type() == "text/html"
            assert "default-src 'none'" in response.headers["Content-Security-Policy"]
            assert "<title>BABYLON-60 · Exergy Dashboard</title>" in html
            assert 'src="/dashboard.js"' in html
        break
    except (OSError, TimeoutError):
        if time.monotonic() >= deadline:
            raise
        time.sleep(0.2)
with urllib.request.urlopen("http://127.0.0.1:8080/api/metrics", timeout=2) as response:
    assert response.status == 200 and response.headers.get_content_type() == "application/json"
    assert json.load(response) == [], "image contains unexpected telemetry"
nonce = os.environ["SMOKE_NONCE"]
db = _get_db_path()
assert not db.exists(), f"image contains telemetry DB: {db}"
db.parent.mkdir(parents=True, exist_ok=True)
with sqlite3.connect(db) as connection:
    connection.execute("CREATE TABLE ledger (timestamp TEXT, commit_hash TEXT, exergy_score REAL, private TEXT)")
    connection.execute("INSERT INTO ledger VALUES (?, ?, ?, ?)", ("smoke-time", nonce, 0.625, "private-canary"))
with urllib.request.urlopen("http://127.0.0.1:8080/api/metrics", timeout=2) as response:
    assert response.status == 200 and response.headers.get_content_type() == "application/json"
    rows = json.load(response)
expected = [{"timestamp": "smoke-time", "commit_hash": nonce, "exergy_score": 0.625}]
assert rows == expected, f"telemetry response mismatch: {rows!r}"
with urllib.request.urlopen("http://127.0.0.1:8080/dashboard.js", timeout=2) as response:
    assert response.status == 200 and "textContent" in response.read().decode()
print(json.dumps({"index_status": 200, "metrics_status": 200, "seeded_metrics": rows,
    "private_column_excluded": True, "scope": "container_loopback_http", "db": str(db)}))
'''


def checked_response(message: object, request_id: int) -> dict[str, Any]:
    """Reject malformed, error, duplicate, or unrelated JSON-RPC responses."""
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
        raise SmokeFailure(f"invalid JSON-RPC response: {message!r}")
    if type(message.get("id")) is not int or message["id"] != request_id:
        raise SmokeFailure(f"unexpected response id: {message.get('id')!r}; expected {request_id}")
    if "error" in message or not isinstance(message.get("result"), dict):
        raise SmokeFailure(f"request {request_id} failed or has no object result: {message!r}")
    return message["result"]


def validate_initialize(result: dict[str, Any]) -> None:
    if result.get("protocolVersion") != "2024-11-05":
        raise SmokeFailure(f"unexpected MCP protocol: {result.get('protocolVersion')!r}")
    server = result.get("serverInfo", {})
    if server.get("name") != "cortex-persist-bft" or not server.get("version"):
        raise SmokeFailure(f"unexpected MCP identity: {server!r}")
    if "tools" not in result.get("capabilities", {}):
        raise SmokeFailure("MCP did not advertise tools")


def validate_tools(result: dict[str, Any]) -> list[str]:
    tools = result.get("tools")
    if not isinstance(tools, list) or not all(isinstance(tool, dict) for tool in tools):
        raise SmokeFailure("tools/list did not return a list of descriptors")
    names = [tool.get("name") for tool in tools]
    if not all(isinstance(name, str) for name in names):
        raise SmokeFailure("invalid tool name")
    if "bft_query_ledger" not in names or len(set(names)) != len(names):
        raise SmokeFailure("required tool absent or duplicate names in tools/list")
    if not all(isinstance(name, str) and tool.get("inputSchema", {}).get("type") == "object"
               for name, tool in zip(names, tools, strict=True)):
        raise SmokeFailure("invalid tool name or input schema")
    return names


class DockerSmoke:
    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.run_id = "babylon60-smoke-" + uuid.uuid4().hex
        self.output = args.output_dir.absolute() / self.run_id
        self.output.mkdir(parents=True, exist_ok=False)
        self.docker = ["docker", "--context", args.docker_context]
        self.containers: list[str] = []
        self.result: dict[str, Any] = {
            "schema_version": 1, "run_id": self.run_id, "image_requested": args.image,
            "docker_context": args.docker_context, "status": "running", "acceptance_complete": False,
            "scope": "runtime_only" if args.runtime_only else "clean_build_and_runtime",
            "output_dir": str(self.output), "steps": [],
            "limits": ["HTTP is container-loopback only; no host port is published.",
                       "No host directories, credentials, or runtime state are mounted or forwarded."],
        }
        self.sequence = 0

    def run(self, args: list[str], label: str, *, timeout: float | None = None) -> str:
        self.sequence += 1
        prefix = f"{self.sequence:02d}-{label}"
        stdout = self.output / f"{prefix}.stdout.log"
        stderr = self.output / f"{prefix}.stderr.log"
        command = self.docker + args
        step: dict[str, Any] = {"name": label, "command": command,
                                "stdout": str(stdout), "stderr": str(stderr)}
        self.result["steps"].append(step)
        started = time.monotonic()
        try:
            with stdout.open("wb") as out, stderr.open("wb") as err:
                completed = subprocess.run(command, stdout=out, stderr=err,
                                           timeout=timeout or self.args.timeout, check=False)
            step["returncode"] = completed.returncode
            if completed.returncode:
                raise SmokeFailure(f"{label} exited {completed.returncode}; see {stderr}")
            step["status"] = "passed"
            return stdout.read_text(encoding="utf-8")
        except Exception as exc:
            step["status"] = "failed"
            step["error"] = str(exc)
            raise
        finally:
            step["duration_seconds"] = round(time.monotonic() - started, 3)

    def create(self, suffix: str, command: list[str], *, entrypoint: str | None = None,
               interactive: bool = False) -> str:
        name = f"{self.run_id}-{suffix}"
        args = ["create", "--name", name, "--network", "none",
                "--label", f"babylon60.smoke.owner={self.run_id}"]
        # Docker can inject client-config proxy credentials even without --env.
        # Explicit empty values suppress injection without reading that config.
        for variable in ("HTTP_PROXY", "HTTPS_PROXY", "FTP_PROXY", "ALL_PROXY",
                         "http_proxy", "https_proxy", "ftp_proxy", "all_proxy"):
            args += ["--env", f"{variable}="]
        for variable in ("NO_PROXY", "no_proxy"):
            args += ["--env", f"{variable}=127.0.0.1,localhost"]
        if interactive:
            args.append("--interactive")
        if entrypoint:
            args += ["--entrypoint", entrypoint]
        try:
            identifier = self.run(args + [self.image_id] + command, f"create-{suffix}").strip()
            if not re.fullmatch(r"[0-9a-f]{64}", identifier):
                raise SmokeFailure(f"invalid container id from create: {identifier!r}")
        except Exception:
            # A failed client can leave a successfully-created daemon object. Recover
            # only our exact UUID name with the matching owner label, never a listing.
            template = ('{"id":{{json .Id}},"image":{{json .Image}},"owner":'
                        '{{json (index .Config.Labels "babylon60.smoke.owner")}}}')
            try:
                recovered = json.loads(self.run(["inspect", "--format", template, name], f"recover-{suffix}"))
                if (recovered["owner"] == self.run_id and recovered["image"] == self.image_id
                        and re.fullmatch(r"[0-9a-f]{64}", recovered["id"])):
                    self.containers.append(recovered["id"])
            except Exception as exc:
                self.result.setdefault("recovery_errors", []).append(str(exc))
            raise
        self.containers.append(identifier)
        # Select only relevant fields; never log Config.Env or unrelated daemon metadata.
        template = ('{"image":{{json .Image}},"mounts":{{json .Mounts}},'
                    '"network":{{json .HostConfig.NetworkMode}},"ports":{{json .HostConfig.PortBindings}},'
                    '"privileged":{{json .HostConfig.Privileged}}}')
        inspect = json.loads(self.run(["inspect", "--format", template, identifier], f"isolation-{suffix}"))
        if (inspect["image"] != self.image_id or inspect["mounts"] or inspect["network"] != "none"
                or inspect["ports"] or inspect["privileged"]):
            raise SmokeFailure(f"unexpected container isolation: {inspect!r}")
        return identifier

    def state(self, identifier: str, label: str) -> dict[str, Any]:
        return json.loads(self.run(["inspect", "--format", "{{json .State}}", identifier], label))

    def mcp(self) -> None:
        identifier = self.create("mcp", ["-m", "babylon60.mcp.cortex_mcp_server"],
                                 entrypoint="python", interactive=True)
        command = self.docker + ["start", "--attach", "--interactive", identifier]
        stdout_path = self.output / "mcp-transport.stdout.jsonl"
        stderr_path = self.output / "mcp-transport.stderr.log"
        transcript: list[dict[str, Any]] = []
        lines: queue.Queue[bytes | None] = queue.Queue()
        with stderr_path.open("wb") as err, stdout_path.open("wb") as out:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=err)
            stdin, stdout = process.stdin, process.stdout
            assert stdin is not None and stdout is not None

            def read_stdout() -> None:
                while True:
                    line = stdout.readline(1024 * 1024 + 1)
                    if not line:
                        break
                    out.write(line)
                    out.flush()
                    lines.put(line)
                lines.put(None)

            reader = threading.Thread(target=read_stdout, daemon=True)
            reader.start()

            def send(method: str, request_id: int | None, params: dict[str, Any]) -> dict[str, Any]:
                message: dict[str, Any] = {"jsonrpc": "2.0", "method": method, "params": params}
                if request_id is not None:
                    message["id"] = request_id
                transcript.append({"direction": "request", "message": message})
                stdin.write((json.dumps(message) + "\n").encode())
                stdin.flush()
                if request_id is None:
                    return {}
                try:
                    line = lines.get(timeout=self.args.timeout)
                except queue.Empty as exc:
                    raise SmokeFailure(f"MCP response timeout for {method}") from exc
                if line is None or len(line) > 1024 * 1024:
                    raise SmokeFailure(f"MCP EOF or oversized response for {method}")
                response = json.loads(line)
                transcript.append({"direction": "response", "message": response})
                return checked_response(response, request_id)

            try:
                initialized = send("initialize", 1, {"protocolVersion": "2024-11-05", "capabilities": {},
                                                     "clientInfo": {"name": "babylon60-docker-smoke", "version": "1"}})
                validate_initialize(initialized)
                send("notifications/initialized", None, {})
                names = validate_tools(send("tools/list", 2, {}))
                skills = send("skills/list", 3, {"scope": "workspace"})
                if not skills.get("skills") or skills.get("total", 0) != len(skills["skills"]):
                    raise SmokeFailure("MCP returned empty or inconsistent physical skills")
                if send("ping", 4, {}) != {}:
                    raise SmokeFailure("MCP ping did not return an empty result")
                stdin.close()
                exitcode = process.wait(timeout=self.args.timeout)
                reader.join(timeout=self.args.timeout)
                if exitcode or reader.is_alive():
                    raise SmokeFailure(f"MCP did not exit cleanly after EOF: {exitcode}")
                if lines.get(timeout=self.args.timeout) is not None:
                    raise SmokeFailure("unexpected extra MCP stdout after final response")
                state = self.state(identifier, "mcp-exit-state")
                if state["Running"] or state["ExitCode"] != 0:
                    raise SmokeFailure(f"MCP container did not exit after EOF: {state!r}")
                self.result["mcp"] = {"protocol": initialized["protocolVersion"],
                                      "server": initialized["serverInfo"], "tools_count": len(names),
                                      "workspace_skills": skills["total"], "ping": "passed", "eof_exitcode": exitcode}
            finally:
                if process.poll() is None:
                    process.kill()
                    process.wait(timeout=10)
                reader.join(timeout=5)
                (self.output / "mcp-transcript.json").write_text(json.dumps(transcript, indent=2) + "\n")

    def execute(self) -> None:
        self.run(["version", "--format", "{{json .Server.Version}}"], "engine-version")
        if not self.args.runtime_only:
            self.run(["build", "--no-cache", "--iidfile", str(self.output / "built-image.iid"), "--tag", self.args.image,
                      str(self.args.build_context.absolute())], "build-final-image", timeout=self.args.build_timeout)
        self.image_id = self.run(["image", "inspect", "--format", "{{.Id}}", self.args.image], "image-id").strip()
        if not re.fullmatch(r"sha256:[0-9a-f]{64}", self.image_id):
            raise SmokeFailure("image inspect did not return a content-addressed image id")
        self.result["image_id"] = self.image_id
        if not self.args.runtime_only and (self.output / "built-image.iid").read_text().strip() != self.image_id:
            raise SmokeFailure("built image id does not match selected image")
        template = ('{"user":{{json .Config.User}},"command":{{json .Config.Cmd}},'
                    '"entrypoint":{{json .Config.Entrypoint}},"healthcheck":{{json .Config.Healthcheck}}}')
        config = json.loads(self.run(["image", "inspect", "--format", template, self.image_id], "image-runtime-config"))
        if (config["command"] != ["dashboard"] or not config["entrypoint"]
                or not config["healthcheck"] or config["healthcheck"].get("Test", ["NONE"])[0] == "NONE"):
            raise SmokeFailure(f"expected default dashboard entrypoint/healthcheck: {config!r}")
        self.result["image_runtime_config"] = config
        probe = self.create("probe", ["-c", IDENTITY_AND_RESOURCES], entrypoint="python")
        self.result["runtime"] = json.loads(self.run(["start", "--attach", probe], "runtime-identity-resources"))
        cli = self.create("cli", ["--help"])
        help_text = self.run(["start", "--attach", cli], "cli-help")
        if "usage:" not in help_text.lower() or "dashboard" not in help_text:
            raise SmokeFailure("CLI --help did not expose the expected interface")
        self.result["cli"] = {"help": "passed"}
        self.mcp()
        dashboard = self.create("dashboard", [])  # Intentionally retain image ENTRYPOINT and CMD.
        self.run(["start", dashboard], "dashboard-start")
        self.result["dashboard"] = json.loads(self.run(
            ["exec", "--env", f"SMOKE_NONCE={self.run_id}", dashboard, "python", "-c", DASHBOARD_HTTP],
            "dashboard-http"))
        deadline = time.monotonic() + self.args.timeout
        while True:
            state = self.state(dashboard, "dashboard-health")
            if not state["Running"]:
                raise SmokeFailure(f"default dashboard stopped: {state!r}")
            health = state.get("Health", {}).get("Status")
            if health == "healthy":
                self.result["dashboard"]["healthcheck"] = "healthy"
                break
            if health not in {"starting", "unhealthy"} or time.monotonic() >= deadline:
                raise SmokeFailure(f"Docker healthcheck did not become healthy: {health!r}")
            time.sleep(1)
        self.result["status"] = "runtime_passed" if self.args.runtime_only else "passed"
        self.result["acceptance_complete"] = not self.args.runtime_only

    def cleanup(self) -> None:
        for identifier in reversed(self.containers):
            try:
                self.run(["logs", identifier], f"logs-{identifier[:12]}")
                self.run(["rm", "--force", identifier], f"cleanup-{identifier[:12]}")
            except Exception as exc:
                self.result.setdefault("cleanup_errors", []).append(str(exc))
                # Failure to read logs must never skip removal of our own container.
                try:
                    self.run(["rm", "--force", identifier], f"cleanup-retry-{identifier[:12]}")
                except Exception as cleanup_exc:
                    self.result.setdefault("cleanup_errors", []).append(str(cleanup_exc))
        if self.result.get("cleanup_errors"):
            self.result["status"] = "failed"
            self.result["acceptance_complete"] = False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", required=True, help="Explicit local image reference/tag; never published")
    parser.add_argument("--docker-context", required=True, help="Explicit Docker daemon context")
    parser.add_argument("--output-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--build-context", type=Path, help="Build final image without cache before runtime checks")
    mode.add_argument("--runtime-only", action="store_true", help="Do not claim build acceptance")
    parser.add_argument("--timeout", type=float, default=75, help="Seconds per command/response/health deadline")
    parser.add_argument("--build-timeout", type=float, default=1800)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.build_timeout <= 0:
        parser.error("timeouts must be positive")
    if args.build_context is not None and not (args.build_context / "Dockerfile").is_file():
        parser.error("build context must contain Dockerfile")
    if args.image != args.image.lower() or args.image.startswith("-") or args.docker_context.startswith("-"):
        parser.error("image must be lowercase and image/context must not begin with '-' ")
    smoke = DockerSmoke(args)
    started = time.monotonic()
    try:
        smoke.execute()
    except (Exception, KeyboardInterrupt) as exc:
        smoke.result["status"] = "failed"
        smoke.result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        smoke.cleanup()
        smoke.result["duration_seconds"] = round(time.monotonic() - started, 3)
        result_path = smoke.output / "result.json"
        result_path.write_text(json.dumps(smoke.result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps({"status": smoke.result["status"], "acceptance_complete": smoke.result["acceptance_complete"],
                          "result": str(result_path)}, ensure_ascii=False))
    return 0 if smoke.result["status"] in {"passed", "runtime_passed"} else 1


if __name__ == "__main__":
    sys.exit(main())
