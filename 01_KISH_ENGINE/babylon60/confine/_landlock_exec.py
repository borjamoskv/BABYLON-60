"""Confinement trampoline: restrict this process, then exec the target.

Runs as ``python -I -S -B -c <this source> <config-json>``. It uses the standard
library only and never imports ``babylon60``. Order of operations:

1. Close every inherited descriptor except stdio and the status pipe.
2. If any capability is held (for example as root), lock the securebits, empty
   the bounding and ambient sets and clear every capability.
3. Set ``NO_NEW_PRIVS``.
4. Linux: build a Landlock ruleset from the granted paths, refusing any path
   whose ``(st_dev, st_ino)`` changed since the launcher checked it, and
   restrict this (single-threaded) process.
5. Optionally install a seccomp filter that rejects ``TIOCSTI``/``TIOCLINUX``
   terminal injection and syscalls from a foreign or x32 ABI.
6. Report the applied state as one JSON line on the status pipe, then ``execv``.

Any failure is reported on the pipe and ends the process with status 126,
before the target runs.
"""

import ctypes
import fcntl
import json
import os
import platform
import resource
import sys

EXIT_REFUSED = 126
LANDLOCK_CREATE_RULESET, LANDLOCK_ADD_RULE, LANDLOCK_RESTRICT_SELF = 444, 445, 446
LANDLOCK_CREATE_RULESET_VERSION, LANDLOCK_CREATE_RULESET_ERRATA = 1, 2
LANDLOCK_RULE_PATH_BENEATH = 1
LANDLOCK_RESTRICT_SELF_LOG_NEW_EXEC_ON = 2
PR_SET_SECCOMP, PR_CAPBSET_DROP, PR_SET_SECUREBITS = 22, 24, 28
PR_SET_NO_NEW_PRIVS, PR_GET_NO_NEW_PRIVS, PR_CAP_AMBIENT = 38, 39, 47
PR_CAP_AMBIENT_CLEAR_ALL, SECCOMP_MODE_FILTER = 4, 2
SECUREBITS_LOCKED_NOROOT = 0xEF  # NOROOT, NO_SETUID_FIXUP, KEEP_CAPS_LOCKED, NO_CAP_AMBIENT_RAISE (+ locks)
LINUX_CAPABILITY_VERSION_3 = 0x20080522
SECCOMP_ARCH = {"x86_64": (0xC000003E, 16, True), "aarch64": (0xC00000B7, 29, False)}
TIOCSTI, TIOCLINUX = 0x5412, 0x541C


class Refused(Exception):
    pass


class RulesetAttr(ctypes.Structure):
    _fields_ = [
        ("handled_access_fs", ctypes.c_uint64),
        ("handled_access_net", ctypes.c_uint64),
        ("scoped", ctypes.c_uint64),
    ]


class PathBeneath(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]


class CapHeader(ctypes.Structure):
    _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]


class CapData(ctypes.Structure):
    _fields_ = [("effective", ctypes.c_uint32), ("permitted", ctypes.c_uint32), ("inheritable", ctypes.c_uint32)]


class SockFilter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_uint16), ("jt", ctypes.c_uint8), ("jf", ctypes.c_uint8), ("k", ctypes.c_uint32)]


class SockFprog(ctypes.Structure):
    _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(SockFilter))]


def _libc():
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    libc.prctl.restype = ctypes.c_int
    return libc


def _check(result, what):
    if result < 0:
        err = ctypes.get_errno()
        raise Refused(f"{what} failed: {os.strerror(err)} (errno {err})")
    return result


def _proc_status():
    fields = {}
    try:
        with open("/proc/self/status", encoding="ascii") as handle:
            for line in handle:
                key, _, value = line.partition(":")
                fields[key] = value.strip()
    except OSError:
        pass
    return fields


def _close_inherited(keep):
    soft, _hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    top = 1 << 20 if soft == resource.RLIM_INFINITY else min(soft, 1 << 20)
    start = 3
    for fd in sorted(k for k in keep if k >= 3):
        if fd > start:
            os.closerange(start, fd)
        start = fd + 1
    os.closerange(start, top)


def _drop_capabilities(libc):
    status = _proc_status()
    held = any(int(status.get(key, "0"), 16) for key in ("CapEff", "CapPrm", "CapInh", "CapAmb"))
    if not held:
        return False
    _check(libc.prctl(PR_SET_SECUREBITS, SECUREBITS_LOCKED_NOROOT, 0, 0, 0), "lock securebits")
    with open("/proc/sys/kernel/cap_last_cap", encoding="ascii") as handle:
        last_cap = int(handle.read())
    for cap in range(last_cap + 1):
        _check(libc.prctl(PR_CAPBSET_DROP, cap, 0, 0, 0), f"drop bounding capability {cap}")
    _check(libc.prctl(PR_CAP_AMBIENT, PR_CAP_AMBIENT_CLEAR_ALL, 0, 0, 0), "clear ambient capabilities")
    header = CapHeader(LINUX_CAPABILITY_VERSION_3, 0)
    data = (CapData * 2)()
    _check(libc.capset(ctypes.byref(header), data), "capset")
    after = _proc_status()
    if any(int(after.get(key, "0"), 16) for key in ("CapEff", "CapPrm", "CapInh", "CapAmb", "CapBnd")):
        raise Refused("capabilities remain after dropping them")
    return True


def _restrict_landlock(libc, cfg):
    abi = _check(
        libc.syscall(
            LANDLOCK_CREATE_RULESET, None, ctypes.c_size_t(0), ctypes.c_uint32(LANDLOCK_CREATE_RULESET_VERSION)
        ),
        "landlock ABI query",
    )
    if abi < cfg["min_abi"]:
        raise Refused(f"Landlock ABI {abi} is below the required {cfg['min_abi']}")
    if abi != cfg["abi"]:
        raise Refused(f"Landlock ABI changed between launcher ({cfg['abi']}) and trampoline ({abi})")
    errata = 0
    if abi >= 7:
        errata = _check(
            libc.syscall(
                LANDLOCK_CREATE_RULESET, None, ctypes.c_size_t(0), ctypes.c_uint32(LANDLOCK_CREATE_RULESET_ERRATA)
            ),
            "landlock errata query",
        )
    attr = RulesetAttr(cfg["handled_fs"], 0, cfg["scoped"] if abi >= 6 else 0)
    size = 24 if abi >= 6 else (16 if abi >= 4 else 8)
    ruleset = _check(
        libc.syscall(LANDLOCK_CREATE_RULESET, ctypes.byref(attr), ctypes.c_size_t(size), ctypes.c_uint32(0)),
        "create ruleset",
    )
    try:
        for rule in cfg["rules"]:
            fd = os.open(rule["path"], os.O_PATH | os.O_CLOEXEC | os.O_NOFOLLOW)
            try:
                st = os.fstat(fd)
                if (st.st_dev, st.st_ino) != (rule["dev"], rule["ino"]):
                    raise Refused(f"granted path changed after it was checked: {rule['path']}")
                beneath = PathBeneath(rule["access"], fd)
                _check(
                    libc.syscall(LANDLOCK_ADD_RULE, ruleset, LANDLOCK_RULE_PATH_BENEATH, ctypes.byref(beneath), 0),
                    f"add rule {rule['path']}",
                )
            finally:
                os.close(fd)
        flags = LANDLOCK_RESTRICT_SELF_LOG_NEW_EXEC_ON if abi >= 7 else 0
        _check(libc.syscall(LANDLOCK_RESTRICT_SELF, ruleset, ctypes.c_uint32(flags)), "restrict self")
    finally:
        os.close(ruleset)
    return abi, errata


def _seccomp_filter(libc):
    machine = platform.machine()
    if machine not in SECCOMP_ARCH:
        raise Refused(f"terminal-injection filter unsupported on {machine}")
    arch, nr_ioctl, has_x32 = SECCOMP_ARCH[machine]
    ld, jeq, jge, ret = 0x20, 0x15, 0x35, 0x06
    allow, eperm = 0x7FFF0000, 0x00050000 | 1
    program = [(ld, 0, 0, 4)]
    if has_x32:
        program += [(jeq, 0, 7, arch), (ld, 0, 0, 0), (jge, 5, 0, 0x40000000)]
    else:
        program += [(jeq, 0, 6, arch), (ld, 0, 0, 0)]
    program += [
        (jeq, 0, 3, nr_ioctl),
        (ld, 0, 0, 24),
        (jeq, 2, 0, TIOCSTI),
        (jeq, 1, 0, TIOCLINUX),
        (ret, 0, 0, allow),
        (ret, 0, 0, eperm),
    ]
    filters = (SockFilter * len(program))(*[SockFilter(*item) for item in program])
    prog = SockFprog(len(program), filters)
    _check(libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog), 0, 0), "install seccomp filter")
    return "tiocsti"


def main():
    cfg = json.loads(sys.argv[1])
    status_fd = cfg["status_fd"]
    fcntl.fcntl(status_fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
    report = {"ok": False, "uid": os.getuid(), "platform": sys.platform}
    try:
        _close_inherited({status_fd})
        if sys.platform.startswith("linux"):
            libc = _libc()
            report["caps_dropped"] = _drop_capabilities(libc) if cfg.get("drop_caps", True) else False
            _check(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0), "set no_new_privs")
            report["no_new_privs"] = _check(libc.prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0), "get no_new_privs")
            if cfg.get("landlock"):
                report["landlock_abi"], report["landlock_errata"] = _restrict_landlock(libc, cfg)
                report["rules"] = len(cfg["rules"])
            if cfg.get("seccomp"):
                report["seccomp"] = _seccomp_filter(libc)
            status = _proc_status()
            report["caps"] = {key: status.get(key) for key in ("CapEff", "CapPrm", "CapBnd", "CapAmb")}
        elif cfg.get("landlock") or cfg.get("seccomp"):
            raise Refused("Landlock and seccomp are only available on Linux")
        report["ok"] = True
        os.write(status_fd, (json.dumps(report) + "\n").encode())
        os.execv(cfg["argv"][0], cfg["argv"])
    except (Refused, OSError, KeyError, ValueError) as exc:
        report["ok"] = False
        report["error"] = f"{type(exc).__name__}: {exc}"
        try:
            os.write(status_fd, (json.dumps(report) + "\n").encode())
        finally:
            os._exit(EXIT_REFUSED)


main()
