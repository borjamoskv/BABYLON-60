"""SDK for BYOC compute providers — shared hardening + lifecycle for every
confined process. A provider is a `provider.py` that exports
`PROVIDER = <ByocProvider impl>`; the `__main__` entrypoint loads it and runs
either the per-op oneshot helper or the long-lived repl kernel.

Two entrypoints share one prologue:
  - run_oneshot() per-op helper (argv + stage/req.json → stage/reply.json),
    spawned per-op by the CLI's BYOC transport
  - run_repl()    long-lived compute_provider kernel (cell-by-cell, idle-timeout),
    spawned by the host's kernel manager for BYOC kernels

The prologue runs BEFORE any provider import and BEFORE reading the
credential (stdin for oneshot, fd-3 for repl), so /proc/<pid>/environ and
kern.procargs2 are empty by construction. run_oneshot self-enforces
confinement (exit 71) before touching stdin; run_repl reports it via
{ready,confined} for the host to gate.

Stdlib-only. Provider shims (the only files that import the third-party SDK)
live in core/skills/remote-compute-<id>/provider.py."""
from __future__ import annotations

import ctypes
import io
import json
import os
import re
import resource
import signal
import sys
import threading
import time
import traceback
from typing import Any, Callable, Iterable, NoReturn, Protocol

__all__ = ["ByocError", "ByocProvider", "ByocResident", "ExecResult"]

TAIL_BYTES = 8 * 1024
TAIL_RING_BYTES = 256 * 1024
CHUNK = 64 * 1024
IDLE_TIMEOUT_S = 15 * 60

STAGE_PREFIX = "/tmp/claude-science-byoc-stage-"


WORK = "/work"


COMPRESSED_CAP_DEFAULT = 10 * 2**30
EXIT_PROTOCOL = 70


def _fmt_bytes(n: int) -> str:
    for unit, sh in (("GiB", 30), ("MiB", 20), ("KiB", 10)):
        if n >= 1 << sh:
            return f"{n / (1 << sh):.1f} {unit}"
    return f"{n} B"





_CRED_KEY_RE = re.compile(
    r"(?i)(?:^|_)(?:TOKEN|SECRET|KEY|PASS(?:WORD|WD)?|PWD|PW|PAT|CREDENTIAL|AUTH|BEARER|COOKIE)(?:_|$)"
)
BASE_ERROR_KINDS = frozenset({
    "not_found", "unauthorized", "rate_limited", "quota_exhausted",
    "invalid_request", "transient", "image_build_failed", "network_denied",
    "network_bridge_down", "ownership_mismatch", "provider_degraded",
    "result_rejected",
})










FD_CTRL = 3
LINE_CAP = 256 * 1024


def _fd3_write(obj: dict[str, Any]) -> None:
    line = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    os.write(FD_CTRL, line[:LINE_CAP] + b"\n")


def write_ready(*, confined: bool) -> None:
    _fd3_write({"ready": True, "confined": confined})


def write_event(kind: str, **extra: Any) -> None:
    _fd3_write({"event": True, "kind": kind, **extra})


def read_auth(*, fd: int = FD_CTRL) -> dict[str, str]:
    """Block for the single newline-terminated {op:"auth", ...} message the
    host writes then closes. Oneshot reads stdin (fd=0); repl reads fd-3.
    Any other shape (or EOF before newline) is a protocol violation — exit
    rather than run unauthenticated."""
    buf = bytearray()
    while b"\n" not in buf:
        chunk = os.read(fd, 65536)
        if not chunk or len(buf) > LINE_CAP:
            sys.exit(EXIT_PROTOCOL)
        buf.extend(chunk)
    try:
        msg = json.loads(bytes(buf).split(b"\n", 1)[0])
    except ValueError:
        sys.exit(EXIT_PROTOCOL)
    if not isinstance(msg, dict) or msg.get("op") != "auth":
        sys.exit(EXIT_PROTOCOL)
    return {k: v for k, v in msg.items() if k != "op"}





class ExecResult(Protocol):
    stdout: Iterable[bytes]
    stderr: Iterable[bytes]
    def wait(self) -> int: ...


class ByocProvider(Protocol):
    secret_env_prefixes: tuple[str, ...]
    token_scrub_regex: re.Pattern[str]

    def import_and_patch(self) -> None: ...
    def apply_auth(self, creds: dict[str, str]) -> None: ...
    def install_unauth_hook(self, on_expired: Callable[[], NoReturn]) -> None: ...
    def create_sandbox(self, spec: dict[str, Any], install_id: str,
                       tags: dict[str, str] | None = None) -> str:
        """Provision a sandbox. ``tags`` are host-built identity tags
        (claude-science-session/claude-science-job/…, already sanitized
        to the provider's tag constraints); implementations that support
        tagging MUST apply them at create time and merge the
        ``claude-science-install-id=install_id`` owner tag LAST so an
        incoming entry can never override ownership."""
        ...
    def exec(self, sandbox_id: str, argv: list[str], *, stdin: Iterable[bytes] | None = None, env: dict[str, str] | None = None, timeout: int | None = None) -> ExecResult: ...
    def list_owned(self, install_id: str) -> list[dict[str, Any]]: ...
    def read_owner(self, sandbox_id: str) -> str | None: ...
    def terminate(self, sandbox_id: str) -> None: ...
    def list_dir(self, root: str, path: str, *, limit: int | None = None) -> list[dict[str, Any]]:
        """List ``path`` inside the provider's persistent store named ``root``
        (for Modal, a named Volume). Returns
        ``[{name, type: "file"|"dir", size, mtime}, ...]``. ``limit`` caps
        the entry count so very wide directories don't serialize the full
        iterator through the helper. Providers without a browsable store
        omit this method; ``_op_list_dir`` surfaces that as
        ``invalid_request``."""
        ...
    def list_volumes(self) -> list[dict[str, Any]]:
        """List the provider's persistent stores (for Modal, all Volumes in
        the workspace). Returns ``[{name, created_at}, ...]``. Backs the
        file browser's landing view at ``/``. Optional for the same reason
        as ``list_dir``."""
        ...
    def read_file(self, root: str, path: str) -> Iterable[bytes]:
        """Stream ``path`` from the provider's persistent store named
        ``root`` as a bytes iterator (for Modal, ``Volume.read_file``).
        Backs the file browser's Import and Download actions for byoc.
        Optional for the same reason as ``list_dir``."""
        ...


class ByocError(Exception):
    def __init__(self, kind: str, msg: str = ""):
        self.kind = kind
        self.msg = msg


class _ScrubWriter(io.TextIOBase):
    """Courtesy filter for naive print(token). Not a control on deliberate
    exfil — the kernel grant already accepts the agent has the token's
    capabilities."""

    def __init__(self, inner: Any, pattern: re.Pattern[str]):
        self._inner = inner
        self._pat = pattern

    def write(self, s: str) -> int:
        return self._inner.write(self._pat.sub("***", s))

    def flush(self) -> None:
        self._inner.flush()

    def fileno(self) -> int:
        return self._inner.fileno()


class ByocResident:
    def __init__(self, provider: ByocProvider, *, idle_timeout_s: int = IDLE_TIMEOUT_S):
        self._p = provider
        self._idle_s = idle_timeout_s
        self._idle_timer: threading.Timer | None = None
        self._creds: dict[str, str] = {}
        self._scrub: list[str] = []



    def run_repl(self) -> NoReturn:
        self._prologue()
        self._handshake()



        signal.signal(signal.SIGINT, signal.default_int_handler)
        self._p.install_unauth_hook(self._on_auth_expired)
        sys.stdout = _ScrubWriter(sys.stdout, self._p.token_scrub_regex)
        sys.stderr = _ScrubWriter(sys.stderr, self._p.token_scrub_regex)





        sys._operon_protocol_stdout_wrap = (
            lambda s: _ScrubWriter(s, self._p.token_scrub_regex)
        )
        self._arm_idle()
        self._serve_repl()

    EXIT_UNCONFINED = 71

    def run_oneshot(self, argv: list[str]) -> NoReturn:
        signal.signal(signal.SIGINT, lambda *_: os._exit(EXIT_PROTOCOL))
        op, stage, expect_confined = argv[1], argv[2], argv[3] == "1"
        self._prologue()
        if expect_confined and not self._probe_confined():
            os._exit(self.EXIT_UNCONFINED)
        self._creds = read_auth(fd=0)
        self._scrub = [v for v in self._creds.values() if isinstance(v, str) and v]
        try:
            if op not in self._OPS:
                raise ByocError("invalid_request", f"unknown op {op!r}")
            self._p.apply_auth(self._creds)
            self._p.import_and_patch()
            with open(os.path.join(stage, "req.json"), encoding="utf-8") as f:
                req = json.load(f)



            set_app = getattr(self._p, "set_app_name", None)
            if callable(set_app):
                set_app(req.get("app_name"))


            set_prior = getattr(self._p, "set_prior_app_names", None)
            if callable(set_prior):
                set_prior(req.get("prior_app_names"))




            set_env = getattr(self._p, "set_environment", None)
            if callable(set_env):
                set_env(req.get("environment"))
            reply = getattr(self, f"_op_{op}")(req)
        except ByocError as e:
            sys.stderr.write(self._redact(traceback.format_exc()))
            kind = e.kind if e.kind in BASE_ERROR_KINDS else "transient"
            reply = {"ok": False, "kind": kind, "msg": self._redact(e.msg)}
        except Exception as e:
            sys.stderr.write(self._redact(traceback.format_exc()))
            reply = {"ok": False, "kind": "transient", "msg": self._redact(repr(e))}
        fd = os.open(os.path.join(stage, "reply.json"),
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(reply, f)
        os._exit(0)



    def _prologue(self) -> None:
        resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
        for k in [k for k in os.environ if k.startswith(self._p.secret_env_prefixes)]:
            os.environ.pop(k, None)
        if sys.platform == "linux":
            try:
                ctypes.CDLL(None).prctl(4, 0, 0, 0, 0)
            except Exception:
                pass
        elif sys.platform == "darwin":
            try:
                ctypes.CDLL(None).ptrace(31, 0, 0, 0)
            except Exception:
                pass
        signal.signal(signal.SIGTERM, lambda *_: os._exit(EXIT_PROTOCOL))

    def _probe_confined(self) -> bool:
        if sys.platform == "darwin":




            try:
                os.listdir(os.path.expanduser("~"))
                return False
            except PermissionError:
                return True
            except Exception:
                return False





        try:
            mine = os.stat("/proc/self/ns/net").st_ino
        except OSError:
            return True
        host = os.environ.get("OPERON_HOST_NETNS_INO")
        if host:
            return mine != int(host)
        try:
            return mine != os.stat("/proc/1/ns/net").st_ino
        except OSError:
            return True

    def _handshake(self) -> None:
        write_ready(confined=self._probe_confined())
        self._creds = read_auth()
        self._p.apply_auth(self._creds)
        self._p.import_and_patch()



    def _arm_idle(self) -> None:
        if self._idle_timer is not None:
            self._idle_timer.cancel()
        t = threading.Timer(self._idle_s, self._on_idle)
        t.daemon = True
        t.start()
        self._idle_timer = t

    def _on_idle(self) -> NoReturn:
        write_event("idle_exit")
        os._exit(0)

    def _on_auth_expired(self) -> NoReturn:
        write_event("auth_expired")
        os._exit(0)

    def _serve_repl(self) -> NoReturn:







        worker = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "..", "kernels", "kernel_worker.py",
        )
        ns: dict[str, Any] = {"__name__": "__main__", "__file__": worker}
        with open(worker, "r", encoding="utf-8") as f:
            code = compile(f.read(), worker, "exec")

        def readline_with_idle() -> str:











            self._arm_idle()
            try:
                proto = getattr(sys, "_operon_protocol_stdin", None)
                if proto is None:
                    raise OSError(
                        "protocol stdin not published — worker recovery "
                        "will republish"
                    )
                line = proto.readline()
            finally:
                self._idle_timer.cancel()
            return line









        sys._operon_protocol_readline = readline_with_idle
        exec(code, ns)
        os._exit(0)



    _OPS = ("create", "submit", "wait", "probe_many", "reconcile", "terminate",
            "tail", "list_dir", "list_volumes", "read_file")

    def _op_create(self, req: dict[str, Any]) -> dict[str, Any]:
        sid = self._p.create_sandbox(
            req["spec"], req["install_id"], tags=req.get("tags") or {},
        )




        try:
            stage = self._stage(req)
            fd = os.open(os.path.join(stage, "sandbox_id"),
                         os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
            try:
                os.write(fd, sid.encode("utf-8"))
            finally:
                os.close(fd)
        except Exception:
            pass
        try:
            owner = self._p.read_owner(sid)
        except Exception:
            self._best_effort_terminate(sid)
            raise
        if owner != req["install_id"]:
            self._best_effort_terminate(sid)
            raise ByocError(
                "ownership_mismatch",
                f"created sandbox {sid} but its owner tag read back as {owner!r}, "
                f"not this Operon install — refusing to proceed (sandbox has been "
                f"best-effort terminated).",
            )
        return {"ok": True, "sandbox_id": sid}

    def _best_effort_terminate(self, sid: str) -> None:
        try:
            self._p.terminate(sid)
        except Exception:
            pass

    @staticmethod
    def _drain_wait(r) -> int:

        for _ in r.stdout:
            pass
        return r.wait()

    def _op_submit(self, req: dict[str, Any]) -> dict[str, Any]:
        sid = req["sandbox_id"]
        stage = self._stage(req)
        if self._p.read_owner(sid) != req["install_id"]:
            raise ByocError("ownership_mismatch", self._owner_msg(sid))
        in_tgz = os.path.join(stage, "in.tar.gz")

        job_timeout = int(req.get("timeout") or 14400)




        deadline_epoch = int(req.get("sandbox_deadline_epoch") or 0)
        remaining_s = int(req.get("sandbox_remaining_s") or 0)
        harvest_margin = int(req.get("harvest_margin_s") or 0)
        term_grace = int(req.get("term_grace_s") or 0)













        wrapper_new = False
        try:
            import tarfile
            with tarfile.open(in_tgz, "r:gz") as tf:







                for member in tf:





                    name = member.name
                    if name.startswith("./"):
                        name = name[2:]
                    if name != "_operon_wrapper.sh":
                        continue
                    fobj = tf.extractfile(member)
                    wrapper_new = (
                        fobj is not None
                        and b"OPERON_JOB_TIMEOUT_S" in fobj.read()
                    )
                    break
        except Exception:
            wrapper_new = False

        def _disarm_keepalive() -> None:











            try:
                c = self._p.exec(sid, ["bash", "-c", f"rm -f {WORK}/run.sh"])
                self._drain_wait(c)
            except Exception:
                pass











        try:
            with open(in_tgz, "rb") as f:
                r = self._p.exec(
                    sid,
                    ["bash", "-c",
                     f"rm -rf {WORK} && mkdir {WORK} && cd {WORK} && tar -xzf -"],
                    stdin=iter(lambda: f.read(CHUNK), b""),
                )
            rc = self._drain_wait(r)
        except Exception:
            _disarm_keepalive()
            raise
        finally:
            try: os.unlink(in_tgz)
            except OSError: pass
        if rc != 0:
            _disarm_keepalive()
            raise ByocError(
                "invalid_request",
                f"untar to {WORK} failed (rc={rc}; rc=127 → image missing tar/bash, "
                f"rc=2 → corrupt input archive, rc=1 → {WORK} not writable)",
            )











        if remaining_s > 0 and deadline_epoch > 0:
            remaining_s = max(1, deadline_epoch - int(time.time()))
        wrapper_env = f"OPERON_JOB_TIMEOUT_S={job_timeout}"





        if remaining_s > 0:
            wrapper_env += f" OPERON_SANDBOX_REMAINING_S={remaining_s}"
        if deadline_epoch > 0:
            wrapper_env += f" OPERON_SANDBOX_DEADLINE_EPOCH={deadline_epoch}"
        if harvest_margin > 0:
            wrapper_env += f" OPERON_HARVEST_MARGIN_S={harvest_margin}"
        if term_grace > 0:
            wrapper_env += f" OPERON_TERM_GRACE_S={term_grace}"
        launch = (
            f"setsid env {wrapper_env} "
            if wrapper_new
            else f"setsid env {wrapper_env} "
                 f"timeout --kill-after=30 {job_timeout} "
        )







        try:
            r2 = self._p.exec(
                sid,
                ["bash", "-c",
                 f"cd {WORK} && {{ {launch}"
                 "bash _operon_wrapper.sh </dev/null >/dev/null 2>&1 & }"],
            )
            rc2 = self._drain_wait(r2)
        except Exception:
            _disarm_keepalive()
            raise
        if rc2 != 0:



            _disarm_keepalive()
            raise ByocError(
                "invalid_request",
                f"wrapper launch failed (rc={rc2}; inputs were staged to "
                f"{WORK} but the job did not start)",
            )


        return {"ok": True, "wrapper_deadline_aware": wrapper_new}

    def _probe_one(self, sid: str, *, poll_s: int,
                   flags: bool = True) -> dict[str, Any]:
        """Probe-only core shared by `_op_wait(probe_only=True)` and
        `_op_probe_many`. Ownership check + bounded `.phase` poll + tails;
        never streams `out.tar.gz`. Raises ByocError for ownership/not_found
        — callers map that into the per-slot error shape."""
        if self._p.read_owner(sid) != self._install_id:
            raise ByocError("ownership_mismatch", self._owner_msg(sid))


        probe = self._p.exec(
            sid,
            ["bash", "-c",
             f"for i in $(seq {max(1, poll_s // 2)}); do "
             f"[ -f {WORK}/.phase ] && exit 0; sleep 2; done; exit 2"],
        )
        if self._drain_wait(probe) != 0:
            return {"ok": True, "ready": False}






        try:
            envcat = self._p.exec(
                sid,
                ["bash", "-c",
                 f"set -a; source {WORK}/.job_env 2>/dev/null; env -0"],
            )
            envdump = b"".join(envcat.stdout)
            envcat.wait()
            for entry in envdump.split(b"\0"):
                k, eq, v = entry.partition(b"=")
                if not eq:
                    continue
                ks = k.decode("utf-8", "replace")
                if not _CRED_KEY_RE.search(ks):
                    continue
                vs = v.decode("utf-8", "replace")
                if len(vs) >= 8:
                    self._scrub.append(vs)
        except Exception:
            pass


        job_rc: int | None = None
        job_wall_s: int | None = None
        phase_err: str | None = None







        phase: str | None = None
        cat_err: Exception | None = None
        for _ in range(2):
            try:
                phasecat = self._p.exec(sid, ["cat", f"{WORK}/.phase"])
                phase = b"".join(phasecat.stdout).decode("ascii", "replace").strip()
                phasecat.wait()
                cat_err = None
                break
            except Exception as e:
                cat_err = e
        if cat_err is not None:
            return {
                "ok": False, "kind": "transient",
                "msg": self._redact(f".phase read failed twice: {cat_err!r}"),
            }
        assert phase is not None
        tag, _, rest = phase.partition(":")
        parts = rest.split(":")
        if tag in ("done", "harvest_failed"):
            try:
                job_rc = int(parts[0])
                if len(parts) > 1:
                    job_wall_s = int(parts[1])
            except ValueError:
                phase_err = self._redact(
                    f"unparseable .phase fields: {phase!r}")
            if job_rc is not None and tag == "harvest_failed":
                phase_err = self._redact(
                    "tar/mv failed in wrapper (likely disk-full or "
                    f"read-only /work); job rc was {parts[0]}"
                )
        else:
            phase_err = self._redact(f"unrecognized .phase content: {phase!r}")
















        deadline_fired = False
        job_timeout_fired = False









        flags_err: Exception | None = None






        for _ in range(2 if flags else 0):
            try:
                flags = self._p.exec(
                    sid, ["bash", "-c",
                          f"[ -f {WORK}/.deadline_fired ] && "
                          f"[ ! {WORK}/.deadline_fired -nt {WORK}/.phase ] && "
                          "printf D; "
                          f"[ -f {WORK}/.job_timeout_fired ] && "
                          f"[ ! {WORK}/.job_timeout_fired -nt {WORK}/.phase ] && "
                          "printf J; "
                          "true"])
                flag_bytes = b"".join(flags.stdout)
                flags.wait()
                deadline_fired = b"D" in flag_bytes
                job_timeout_fired = b"J" in flag_bytes
                flags_err = None
                break
            except Exception as e:
                flags_err = e
        if flags and flags_err is not None:
            return {
                "ok": False, "kind": "transient",
                "msg": self._redact(
                    f"deadline-sentinel read failed twice: {flags_err!r}"
                ),
            }
        tails = self._tails(sid)
        out: dict[str, Any] = {
            "ok": True, "ready": True,
            "job_exit_code": job_rc, "job_wall_s": job_wall_s,
            "deadline_fired": deadline_fired,
            "job_timeout_fired": job_timeout_fired,
            **tails,
        }
        if phase_err:
            out["phase_read_error"] = phase_err
        return out

    def _op_wait(self, req: dict[str, Any]) -> dict[str, Any]:
        sid = req["sandbox_id"]
        stage = self._stage(req)
        self._install_id = req["install_id"]
        poll_s = int(req.get("poll_seconds") or 30)
        head = self._probe_one(sid, poll_s=poll_s,
                               flags=bool(req.get("probe_only")))




        if req.get("probe_only") or not head.get("ready"):
            return head
        job_rc = head.get("job_exit_code")
        job_wall_s = head.get("job_wall_s")
        phase_err = head.get("phase_read_error")
        tails = {k: head[k] for k in ("stdout_tail", "stderr_tail")}
        cap = int(req.get("output_cap_bytes") or COMPRESSED_CAP_DEFAULT)
        written = 0
        rc = -1
        stream_err: tuple[str, str] | None = None
        try:
            r = self._p.exec(sid, ["cat", f"{WORK}/out.tar.gz"])
            with open(os.path.join(stage, "out.tar.gz"), "wb") as out:
                for chunk in r.stdout:
                    out.write(chunk)
                    written += len(chunk)
                    if written > cap:
                        stream_err = (
                            "result_rejected",
                            f"compressed harvest exceeds {_fmt_bytes(cap)} cap",
                        )
                        break




            try:
                for _ in r.stdout:
                    pass
                rc = r.wait()
            except Exception:
                pass
        except Exception as e:
            if stream_err is None:
                stream_err = (
                    "transient", self._redact(f"harvest stream failed: {e!r}")
                )
        if stream_err:
            kind, msg = stream_err
            return {
                "ok": False, "kind": kind, "msg": msg,
                "job_exit_code": job_rc, "job_wall_s": job_wall_s,
                "bytes_written": written, **tails,
            }
        out: dict[str, Any] = {
            "ok": True, "ready": True, "exit_code": rc,
            "job_exit_code": job_rc, "job_wall_s": job_wall_s,
            "bytes_written": written, **tails,
        }
        if phase_err:
            out["phase_read_error"] = phase_err
        return out

    def _op_probe_many(self, req: dict[str, Any]) -> dict[str, Any]:
        """Batched probe-only for `ByocAdapter.statusBatch()`: probe N
        sandboxes in one helper round-trip so the poller's 15s tick spawns
        one confined subprocess per provider, not one per sandbox. Per-slot
        errors are caught and returned as `{ok:False, kind, msg}` so one bad
        sandbox doesn't kill the batch — the host maps each slot through the
        same retriable/definitive/orphaned classification as single
        `probe()`."""
        self._install_id = req["install_id"]
        sids = req.get("sandbox_ids")
        if not isinstance(sids, list):
            raise ByocError("invalid_request", "sandbox_ids must be a list")





        results: list[dict[str, Any]] = []
        for sid in sids:
            if not isinstance(sid, str):
                results.append({"sandbox_id": str(sid), "ok": False,
                                "kind": "invalid_request",
                                "msg": "sandbox_id must be a string"})
                continue
            try:
                r = self._probe_one(sid, poll_s=2)
            except ByocError as e:
                kind = e.kind if e.kind in BASE_ERROR_KINDS else "transient"
                r = {"ok": False, "kind": kind, "msg": self._redact(e.msg)}
            except Exception as e:
                r = {"ok": False, "kind": "transient",
                     "msg": self._redact(repr(e))}
            results.append({"sandbox_id": sid, **r})
        return {"ok": True, "results": results}

    def _op_reconcile(self, req: dict[str, Any]) -> dict[str, Any]:
        return {"ok": True, "sandboxes": self._p.list_owned(req["install_id"])}

    def _op_list_dir(self, req: dict[str, Any]) -> dict[str, Any]:
        fn = getattr(self._p, "list_dir", None)
        if not callable(fn):
            raise ByocError(
                "invalid_request",
                "this byoc provider has no persistent store to browse",
            )
        limit = req.get("limit")
        entries = fn(
            str(req["root"]), str(req.get("path") or "/"),
            limit=int(limit) if limit is not None else None,
        )
        return {"ok": True, "entries": entries}

    def _op_list_volumes(self, req: dict[str, Any]) -> dict[str, Any]:
        fn = getattr(self._p, "list_volumes", None)
        if not callable(fn):
            raise ByocError(
                "invalid_request",
                "this byoc provider has no persistent store to browse",
            )
        return {"ok": True, "volumes": fn()}

    def _op_read_file(self, req: dict[str, Any]) -> dict[str, Any]:
        """Stream a file from the provider's persistent store to
        ``stage/out.bin`` so the host can import/download it. The host
        passes ``cap_bytes`` (the browser-download or import limit); the
        stream is cut off there with ``result_rejected`` so a misclick on a
        multi-GB blob doesn't fill the daemon's tmp."""
        fn = getattr(self._p, "read_file", None)
        if not callable(fn):
            raise ByocError(
                "invalid_request",
                "this byoc provider has no persistent store to read from",
            )
        stage = self._stage(req)
        cap = int(req.get("cap_bytes") or COMPRESSED_CAP_DEFAULT)
        written = 0
        fd = os.open(os.path.join(stage, "out.bin"),
                     os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            for chunk in fn(str(req["root"]), str(req.get("path") or "/")):
                if not isinstance(chunk, (bytes, bytearray)):
                    chunk = bytes(chunk)
                os.write(fd, chunk)
                written += len(chunk)
                if written > cap:
                    raise ByocError(
                        "result_rejected",
                        f"file exceeds the {_fmt_bytes(cap)} transfer cap",
                    )
        finally:
            os.close(fd)
        return {"ok": True, "size": written}

    def _op_tail(self, req: dict[str, Any]) -> dict[str, Any]:
        """Follow ``/work/{stdout,stderr}.log`` in the sandbox and stream each
        line to this process's own stdout as newline-delimited JSON
        ``{"s":"out"|"err","c":text}`` — one record per log line, with
        ``_redact()`` applied before it leaves the confined helper.

        This op is unlike every other in ``_OPS``: it does not return under
        normal operation. The host (``ByocTransport.tail()``) reads our stdout
        line-by-line for as long as a viewer is subscribed and SIGKILLs the
        helper when the last viewer disconnects, so ``run_oneshot`` never
        reaches its ``reply.json`` write. We only fall through and return
        ``{"ok": True}`` when both follows have ended on their own — which in
        practice means the sandbox is gone.
        """
        sid = req["sandbox_id"]
        if self._p.read_owner(sid) != req["install_id"]:
            raise ByocError("ownership_mismatch", self._owner_msg(sid))
        lock = threading.Lock()
        out = os.fdopen(sys.stdout.fileno(), "w", buffering=1, encoding="utf-8")

        def emit(tag: str, line: str) -> None:
            rec = json.dumps({"s": tag, "c": self._redact(line)},
                             separators=(",", ":"))
            with lock:
                out.write(rec + "\n")

        def follow(tag: str, log_path: str) -> None:
            try:
                r = self._p.exec(
                    sid, ["tail", "-c", str(TAIL_RING_BYTES), "-F", log_path])
                buf = b""
                for chunk in r.stdout:
                    buf += chunk
                    *lines, buf = buf.split(b"\n")
                    for ln in lines:
                        emit(tag, ln.decode("utf-8", "replace"))
            except Exception as e:
                emit(tag, f"[tail ended: {self._redact(repr(e))}]")

        threads = [
            threading.Thread(target=follow, args=("out", f"{WORK}/stdout.log"),
                             daemon=True),
            threading.Thread(target=follow, args=("err", f"{WORK}/stderr.log"),
                             daemon=True),
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        return {"ok": True}

    def _op_terminate(self, req: dict[str, Any]) -> dict[str, Any]:
        sid = req["sandbox_id"]
        if self._p.read_owner(sid) != req["install_id"]:
            raise ByocError("ownership_mismatch", self._owner_msg(sid))
        self._p.terminate(sid)
        return {"ok": True}

    @staticmethod
    def _stage(req: dict[str, Any]) -> str:




        stage = req.get("stage")
        if not isinstance(stage, str):
            raise ByocError("invalid_request", "bad stage path")
        real = os.path.realpath(stage)
        prefix = os.path.join(
            os.path.realpath(os.path.dirname(STAGE_PREFIX)),
            os.path.basename(STAGE_PREFIX),
        )
        if not (real.startswith(prefix) and os.path.isdir(real)):
            raise ByocError("invalid_request", "bad stage path")
        return real

    @staticmethod
    def _owner_msg(sid: str) -> str:
        return (
            f"sandbox {sid} is not tagged for this Operon install — refusing to touch "
            f"it. Either it was created outside Operon or by another machine; "
            f"compute.create() will return a fresh one."
        )

    def _tails(self, sid: str) -> dict[str, str]:
        sep = b"\0---SEP---\0"
        try:
            r = self._p.exec(sid, [
                "bash", "-c",
                f"tail -c {TAIL_BYTES} {WORK}/stdout.log 2>/dev/null;"
                f" printf '\\0---SEP---\\0';"
                f" tail -c {TAIL_BYTES} {WORK}/stderr.log 2>/dev/null",
            ])
            buf = b"".join(r.stdout)
            r.wait()
        except Exception:
            return {"stdout_tail": "", "stderr_tail": ""}
        out, _, err = buf.partition(sep)
        return {
            "stdout_tail": self._redact(out.decode("utf-8", "replace")),
            "stderr_tail": self._redact(err.decode("utf-8", "replace")),
        }

    def _redact(self, s: str) -> str:
        s = self._p.token_scrub_regex.sub("***", s)
        for v in self._scrub:
            s = s.replace(v, "***")
        return "".join(c if c.isprintable() or c in "\n\t\r" else "?" for c in s)[:TAIL_BYTES]
