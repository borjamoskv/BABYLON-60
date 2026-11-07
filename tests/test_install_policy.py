"""Physical regressions for installation confinement and commit authorization."""

from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import tempfile
import threading

from blake3 import blake3
import pytest

from babylon60.install_policy import (
    InstallAuthority,
    InstallBroker,
    InstallPolicyError,
    InstallScope,
    confinement_profile,
    node_runtime,
)
from scripts.c5_quality_gates.fl_pkg_01 import Registry, Sink, install_one, make_corpus


@pytest.fixture
def lab() -> Iterator[Path]:
    directory = Path(
        tempfile.mkdtemp(prefix="fl-pkg-c-regression-", dir="/private/tmp" if platform.system() == "Darwin" else None)
    )
    (directory / "FL_PKG_SYNTHETIC_LAB").touch()
    try:
        yield directory
    finally:
        shutil.rmtree(directory)


def broker_fixture(lab: Path) -> tuple[InstallBroker, InstallScope, list[int]]:
    stage, destination, state = lab / "stage", lab / "published", lab / "state"
    for directory in (stage, destination, state):
        directory.mkdir(mode=0o700)
    (stage / "node_modules").mkdir()
    (stage / "node_modules" / "approved.txt").write_bytes(b"approved")
    clock = [3, 4]
    broker = InstallBroker(state, InstallAuthority(clock[0], logical_tick=lambda: clock[1]))
    scope = InstallScope(
        "explicit-grant", blake3(b"artifact").hexdigest(), stage, destination, "result", ("node_modules",), 3, 8
    )
    return broker, scope, clock


@pytest.mark.parametrize("field", ["artifact", "epoch", "expiry"])
def test_no_authorization_with_invalid_admission_or_live_policy(lab: Path, field: str) -> None:
    broker, scope, clock = broker_fixture(lab)
    archive = b"artifact"
    if field == "artifact":
        archive = b"different"
    elif field == "epoch":
        broker.authority.revoke(clock[0] + 1)
    else:
        clock[1] = 9
    with pytest.raises(InstallPolicyError):
        broker.authorize(scope, archive)
    assert list(scope.destination_parent.iterdir()) == []


@pytest.mark.parametrize("kind", ["symlink", "hardlink", "fifo"])
def test_snapshot_refuses_unmediated_aliases_and_special_files(lab: Path, kind: str) -> None:
    broker, scope, _ = broker_fixture(lab)
    target = scope.stage / "node_modules" / "escape"
    outside = lab / "protected"
    outside.write_bytes(b"secret")
    if kind == "symlink":
        target.symlink_to(outside)
    elif kind == "hardlink":
        os.link(outside, target)
    else:
        os.mkfifo(target)
    with pytest.raises(InstallPolicyError):
        broker.authorize(scope, b"artifact")
    assert outside.read_bytes() == b"secret"
    assert not (scope.destination_parent / "result").exists()


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires exclusive macOS publication")
def test_immutable_effects_bind_each_path_content_and_scope(lab: Path) -> None:
    broker, scope, _ = broker_fixture(lab)
    (scope.stage / "unapproved.txt").write_text("unapproved")
    permit = broker.authorize(scope, b"artifact")
    (scope.stage / "node_modules" / "approved.txt").write_bytes(b"changed after authorization")
    receipt = broker.commit(permit)
    published = scope.destination_parent / "result"
    assert (published / "node_modules" / "approved.txt").read_bytes() == b"approved"
    assert not (published / "unapproved.txt").exists()
    assert receipt.committed_files == (("node_modules/approved.txt", blake3(b"approved").hexdigest()),)


def test_forged_permit_cannot_materialize_effects(lab: Path) -> None:
    broker, scope, _ = broker_fixture(lab)
    permit = broker.authorize(scope, b"artifact")
    with pytest.raises(InstallPolicyError, match="forged"):
        broker.commit(replace(permit))
    assert list(scope.destination_parent.iterdir()) == []


def test_revoked_grant_aborts_before_any_publication(lab: Path) -> None:
    broker, scope, clock = broker_fixture(lab)
    permit = broker.authorize(scope, b"artifact")
    broker.authority.revoke(clock[0] + 1)
    with pytest.raises(InstallPolicyError):
        broker.commit(permit)
    assert list(scope.destination_parent.iterdir()) == []


def test_expiry_during_copy_prevents_atomic_publication(lab: Path) -> None:
    broker, scope, clock = broker_fixture(lab)
    calls = [0]

    def logical_tick() -> int:
        calls[0] += 1
        return clock[1] if calls[0] < 4 else scope.expires_tick + 1

    broker = InstallBroker(broker.state, InstallAuthority(clock[0], logical_tick))
    permit = broker.authorize(scope, b"artifact")
    with pytest.raises(InstallPolicyError):
        broker.commit(permit)
    assert calls[0] >= 4
    assert list(scope.destination_parent.iterdir()) == []
    assert not (broker.state / f"pending-{scope.grant_id}").exists()


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires exclusive macOS publication")
def test_consumed_grants_cannot_replay_after_broker_restart(lab: Path) -> None:
    broker, scope, clock = broker_fixture(lab)
    broker.commit(broker.authorize(scope, b"artifact"))
    restarted = InstallBroker(broker.state, InstallAuthority(clock[0], logical_tick=lambda: clock[1]))
    with pytest.raises(InstallPolicyError, match="replay"):
        restarted.commit(restarted.authorize(scope, b"artifact"))
    assert (scope.destination_parent / "result" / "node_modules" / "approved.txt").read_bytes() == b"approved"


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires exclusive macOS publication")
def test_existing_destination_is_never_replaced(lab: Path) -> None:
    broker, scope, _ = broker_fixture(lab)
    (scope.destination_parent / "result").mkdir()
    with pytest.raises(OSError):
        broker.commit(broker.authorize(scope, b"artifact"))
    assert list((scope.destination_parent / "result").iterdir()) == []


def test_replaced_publication_parent_is_rejected(lab: Path) -> None:
    broker, scope, _ = broker_fixture(lab)
    permit = broker.authorize(scope, b"artifact")
    scope.destination_parent.rename(lab / "old-parent")
    scope.destination_parent.mkdir()
    with pytest.raises(InstallPolicyError, match="identity"):
        broker.commit(permit)
    assert list(scope.destination_parent.iterdir()) == []


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires exclusive macOS publication")
def test_revocation_and_publication_share_one_linearization_frontier(lab: Path) -> None:
    broker, scope, clock = broker_fixture(lab)
    in_copy, requested = threading.Event(), threading.Event()
    calls = [0]

    def logical_tick() -> int:
        calls[0] += 1
        if calls[0] == 3:
            in_copy.set()
            assert requested.wait(timeout=3)
        return clock[1]

    authority = InstallAuthority(clock[0], logical_tick)
    broker = InstallBroker(broker.state, authority)
    permit = broker.authorize(scope, b"artifact")

    def revoke() -> None:
        assert in_copy.wait(timeout=3)
        requested.set()
        authority.revoke(4)

    with ThreadPoolExecutor(max_workers=2) as pool:
        publication = pool.submit(broker.commit, permit)
        revocation = pool.submit(revoke)
        receipt = publication.result(timeout=5)
        revocation.result(timeout=5)
    assert receipt.committed_files
    assert authority.observe()[0] == 4
    with pytest.raises(InstallPolicyError):
        broker.authorize(replace(scope, grant_id="after-revocation"), b"artifact")


def test_logical_clock_rollback_is_terminal(lab: Path) -> None:
    broker, scope, clock = broker_fixture(lab)
    permit = broker.authorize(scope, b"artifact")
    clock[1] -= 1
    with pytest.raises(InstallPolicyError, match="clock rollback"):
        broker.commit(permit)
    assert list(scope.destination_parent.iterdir()) == []


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires real Seatbelt enforcement")
@pytest.mark.parametrize("variant", range(5))
@pytest.mark.parametrize("effect", ["unlisted_mutation", "secret_canary_exposure", "network_egress"])
def test_observed_installation_escapes_are_blocked(lab: Path, variant: int, effect: str) -> None:
    npm, node = shutil.which("npm"), shutil.which("node")
    assert npm is not None and node is not None
    corpus = make_corpus(15)
    package = next(p for p in corpus if p.kind == "adversarial" and p.variant == variant)
    registry, sink = Registry(corpus), Sink()
    registry.thread.start()
    sink.thread.start()
    try:
        policy = os.environ.get("FL_PKG_REGRESSION_POLICY", "C")
        if policy == "C_CURRENT":
            legacy = Path(os.environ["FL_PKG_LEGACY_PROFILE"])
            (lab / "babylon-current.sb").write_bytes(legacy.read_bytes())
        row = install_one(lab, package, policy, registry, sink, npm, node)
        assert row.legitimate_success, row.stderr_tail
        assert not getattr(row, effect), f"regression: {effect}"
        assert not row.unlisted_mutation, "regression: unauthorized outside write"
        assert not row.secret_canary_exposure, "regression: canary read/export"
        assert not row.network_egress, "regression: network egress"
        assert not row.protected_mutation, "regression: protected file write"
        assert row.mediation_verified
        assert row.unmediated_install_effects == 0
        assert row.committed_files > 0
    finally:
        registry.close()
        sink.close()


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires real Seatbelt enforcement")
def test_raw_syscalls_do_not_need_a_cooperative_installer(lab: Path) -> None:
    npm, node = shutil.which("npm"), shutil.which("node")
    assert npm and node
    runtime = node_runtime(node, npm)
    stage = lab / "stage"
    stage.mkdir(mode=0o700)
    outside = lab / "outside"
    outside.write_bytes(b"canary")
    script = r"""
      const fs=require('node:fs'),cp=require('node:child_process');
      const p=process.argv[1];
      const alias='/System/Volumes/Data'+p;
      for(const action of [()=>fs.readFileSync(p),()=>fs.readFileSync(alias),()=>fs.writeFileSync(p,'escape'),
        ()=>fs.linkSync(p,process.argv[2]+'.hard'),
        ()=>{const l=process.argv[2]+'.link';fs.symlinkSync(p,l);fs.readFileSync(l)},
        ()=>cp.execFileSync(process.execPath,['-e','require("node:fs").writeFileSync(process.argv[1],"escape")',p])]){
        try {action(); process.exitCode=21;} catch(_){}
      }
      fs.writeFileSync(process.argv[2],'authorized');
    """
    result = subprocess.run(
        [
            "/usr/bin/sandbox-exec",
            "-p",
            confinement_profile(stage, runtime),
            str(runtime.node),
            "-e",
            script,
            str(outside),
            str(stage / "ok"),
        ],
        cwd=stage,
        env={"PATH": f"{runtime.node.parent}:/bin:/usr/bin", "OPENSSL_CONF": "/dev/null"},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr.decode(errors="replace")
    assert outside.read_bytes() == b"canary"
    assert (stage / "ok").read_text() == "authorized"


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires the native npm lab")
def test_registry_rejection_is_counted_from_the_independent_gateway(lab: Path) -> None:
    npm, node = shutil.which("npm"), shutil.which("node")
    assert npm and node
    corpus = make_corpus(3)
    package = next(p for p in corpus if p.kind == "suspicious")
    registry, sink = Registry(corpus), Sink()
    registry.thread.start()
    sink.thread.start()
    try:
        row = install_one(lab, package, "B", registry, sink, npm, node)
        assert row.admission_rejected
        assert row.returncode != 0
        assert not row.legitimate_success
        assert not row.unauthorized
        assert any(event["status"] == 403 for event in registry.events)
    finally:
        registry.close()
        sink.close()


@pytest.mark.skipif(platform.system() != "Darwin", reason="requires real Seatbelt enforcement")
def test_tcp_udp_dns_and_ipv6_egress_have_independent_negative_and_positive_controls(lab: Path) -> None:
    npm, node = shutil.which("npm"), shutil.which("node")
    assert npm and node
    runtime = node_runtime(node, npm)
    sink = Sink()
    sink.thread.start()
    udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp.bind(("127.0.0.1", 0))
    udp.settimeout(0.05)
    ipv6 = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
    ipv6.bind(("::1", 0))
    ipv6.settimeout(0.05)
    script = r"""
      const net=require('node:net'),dgram=require('node:dgram'),dns=require('node:dns');
      const [tcpPort,udpPort,v6Port,trial]=process.argv.slice(1);
      const tcp=net.connect({host:'127.0.0.1',port:Number(tcpPort)});
      tcp.on('connect',()=>tcp.end(trial+'\ncontrolled-payload'));
      tcp.on('error',()=>tcp.destroy());tcp.setTimeout(300,()=>tcp.destroy());
      for(const [type,host,port] of [['udp4','127.0.0.1',udpPort],['udp6','::1',v6Port]]){
        const udp=dgram.createSocket(type);udp.on('error',()=>{try{udp.close()}catch(_){}});
        udp.send('controlled-payload',Number(port),host,()=>{try{udp.close()}catch(_){}});
      }
      const resolver=new dns.Resolver({timeout:100,tries:1});
      resolver.setServers(['127.0.0.1:'+udpPort]);resolver.resolve4('synthetic.invalid',()=>{});
    """
    try:
        for policy in ("A", "C"):
            stage = lab / policy
            stage.mkdir(mode=0o700)
            trial = f"network-{policy}"
            command = [
                str(runtime.node),
                "-e",
                script,
                str(sink.port),
                str(udp.getsockname()[1]),
                str(ipv6.getsockname()[1]),
                trial,
            ]
            if policy == "C":
                command = ["/usr/bin/sandbox-exec", "-p", confinement_profile(stage, runtime), *command]
            result = subprocess.run(
                command, cwd=stage, env={"OPENSSL_CONF": "/dev/null"}, capture_output=True, timeout=5
            )
            assert result.returncode == 0, result.stderr.decode(errors="replace")
            datagrams = []
            while True:
                try:
                    datagrams.append(udp.recvfrom(4096)[0])
                except TimeoutError:
                    break
            try:
                ipv6_payload: bytes | None = ipv6.recvfrom(4096)[0]
            except TimeoutError:
                ipv6_payload = None
            with sink.lock:
                tcp_payload = sink.receipts.get(trial)
            if policy == "A":
                assert tcp_payload == b"controlled-payload"
                assert len(datagrams) >= 2  # Direct UDP and the actual DNS question.
                assert ipv6_payload == b"controlled-payload"
            else:
                assert tcp_payload is None
                assert datagrams == []
                assert ipv6_payload is None
    finally:
        udp.close()
        ipv6.close()
        sink.close()
