"""Confinement trampoline: restrict this process, then exec the target.

Runs as ``python -I -S -B -c <this source> <config-json>``. It uses the standard
library only and never imports ``babylon60``. Order of operations:

1. Test hook ``acquire_ctty``: the launcher's session holder made fd 0 the
   controlling terminal, as when the target inherits the user's terminal;
   refuse unless ``/dev/tty`` opens.
2. Close every inherited descriptor except stdio and the status pipe.
3. ``new_session``: leave the terminal session (``setsid``, or ``TIOCNOTTY`` when
   this process already leads a process group) and refuse unless ``/dev/tty``
   then fails with ENXIO. Without a controlling terminal ``TIOCSTI`` fails; this
   is the defence on macOS, where Seatbelt does not filter ioctls.
4. If any capability is held (for example as root), lock the securebits, empty
   the bounding and ambient sets and clear every capability.
5. Set ``NO_NEW_PRIVS``.
6. Linux: build a Landlock ruleset from the granted paths, refusing any path
   whose ``(st_dev, st_ino)`` changed since the launcher checked it, and
   restrict this (single-threaded) process.
7. Optionally install a seccomp filter that returns EPERM for syscalls from a
   foreign or x32 ABI, ``TIOCSTI``/``TIOCLINUX`` terminal injection,
   ``socket(AF_UNIX)`` unless Unix sockets are allowed (Landlock ABI <= 7 does
   not restrict connecting to a socket path: ssh-agent, gpg-agent, tmux, D-Bus,
   Docker) and io_uring, which creates and connects sockets without ``socket()``.
8. Restore the signals Python ignores at startup, report the applied state as
   one JSON line on the status pipe, then ``execv``.

Any failure is reported on the pipe and ends the process with status 126,
before the target runs.
"""

import ctypes
import errno
import fcntl
import json
import os
import platform
import resource
import signal
import sys
import termios

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
# machine: (AUDIT_ARCH_*, __NR_ioctl, __NR_socket, x32 shares the audit arch)
SECCOMP_ARCH = {"x86_64": (0xC000003E, 16, 41, True), "aarch64": (0xC00000B7, 29, 198, False)}
IO_URING_SYSCALLS = (425, 426, 427)  # io_uring_setup, io_uring_enter, io_uring_register on every architecture
X32_SYSCALL_BIT = 0x40000000
TIOCSTI, TIOCLINUX = 0x5412, 0x541C
AF_UNIX = 1
BPF_LD_W_ABS, BPF_JEQ_K, BPF_JGE_K, BPF_RET_K = 0x20, 0x15, 0x35, 0x06
SECCOMP_RET_ALLOW, SECCOMP_RET_EPERM = 0x7FFF0000, 0x00050000 | errno.EPERM
# struct seccomp_data: nr, arch, then args[]; the low 32 bits of an argument come first (little endian).
DATA_NR, DATA_ARCH, DATA_ARG0_LOW, DATA_ARG1_LOW = 0, 4, 16, 24


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


def _assemble(lines):
    """Classic BPF from instructions whose jump targets may name a label (a plain string line)."""
    labels, program = {}, []
    for line in lines:
        if isinstance(line, str):
            labels[line] = len(program)
        else:
            program.append(line)

    def offset(target, index):
        if not isinstance(target, str):
            return target
        distance = labels[target] - index - 1
        if not 0 <= distance <= 255:
            raise Refused(f"seccomp jump to {target} out of range")
        return distance

    return [(code, offset(jt, i), offset(jf, i), k) for i, (code, jt, jf, k) in enumerate(program)]


def _seccomp_program(machine, unix_sockets):
    """Return (rule names, program): EPERM for each rule, every other syscall allowed."""
    if machine not in SECCOMP_ARCH:
        raise Refused(f"seccomp filter unsupported on {machine}")
    arch, nr_ioctl, nr_socket, has_x32 = SECCOMP_ARCH[machine]
    rules = ["foreign_arch", "tiocsti", "tioclinux"]
    lines = [(BPF_LD_W_ABS, 0, 0, DATA_ARCH), (BPF_JEQ_K, 0, "deny", arch), (BPF_LD_W_ABS, 0, 0, DATA_NR)]
    if has_x32:
        lines.append((BPF_JGE_K, "deny", 0, X32_SYSCALL_BIT))
    lines.append((BPF_JEQ_K, "ioctl", 0, nr_ioctl))
    if not unix_sockets:
        rules.append("af_unix")
        lines.append((BPF_JEQ_K, "socket", 0, nr_socket))
    rules.append("io_uring")
    lines += [(BPF_JEQ_K, "deny", 0, nr) for nr in IO_URING_SYSCALLS]
    lines += [
        (BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW),
        "ioctl",
        (BPF_LD_W_ABS, 0, 0, DATA_ARG1_LOW),  # the kernel truncates the request to 32 bits
        (BPF_JEQ_K, "deny", 0, TIOCSTI),
        (BPF_JEQ_K, "deny", 0, TIOCLINUX),
        (BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW),
    ]
    if not unix_sockets:
        # socketpair() stays allowed: its sockets are connected to each other, not to a path.
        lines += [
            "socket",
            (BPF_LD_W_ABS, 0, 0, DATA_ARG0_LOW),  # the domain is an int: high bits cannot hide AF_UNIX
            (BPF_JEQ_K, "deny", 0, AF_UNIX),
            (BPF_RET_K, 0, 0, SECCOMP_RET_ALLOW),
        ]
    lines += ["deny", (BPF_RET_K, 0, 0, SECCOMP_RET_EPERM)]
    return rules, _assemble(lines)


def _seccomp_filter(libc, unix_sockets):
    rules, program = _seccomp_program(platform.machine(), unix_sockets)
    filters = (SockFilter * len(program))(*[SockFilter(*item) for item in program])
    prog = SockFprog(len(program), filters)
    _check(libc.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog), 0, 0), "install seccomp filter")
    return rules


def _open_ctty():
    """The controlling terminal, or None when there is none (ENXIO)."""
    try:
        return os.open("/dev/tty", os.O_RDWR | os.O_NOCTTY | os.O_CLOEXEC)
    except OSError as exc:
        if exc.errno == errno.ENXIO:
            return None
        raise Refused(f"cannot check the controlling terminal: /dev/tty: {exc.strerror}") from None


def _leave_terminal_session():
    """The target must start without a controlling terminal, so TIOCSTI and /dev/tty cannot reach it."""
    try:
        os.setsid()
    except PermissionError:  # already leads a process group (or its session): release the terminal instead
        fd = _open_ctty()
        if fd is not None:
            # A session leader releasing its terminal makes the kernel send SIGHUP to the foreground group,
            # which can be this process; the disposition is restored before exec.
            previous = signal.signal(signal.SIGHUP, signal.SIG_IGN)
            try:
                fcntl.ioctl(fd, termios.TIOCNOTTY)
            except OSError as exc:
                raise Refused(f"cannot release the controlling terminal: {exc.strerror}") from None
            finally:
                signal.signal(signal.SIGHUP, previous)
                os.close(fd)
    fd = _open_ctty()
    if fd is not None:
        os.close(fd)
        raise Refused("the target would keep a controlling terminal")
    return True


def _restore_default_signals():
    """Python ignores these at startup and exec keeps ignored signals; the target gets the defaults."""
    for name in ("SIGPIPE", "SIGXFSZ"):
        if hasattr(signal, name):
            signal.signal(getattr(signal, name), signal.SIG_DFL)


def main():
    cfg = json.loads(sys.argv[1])
    status_fd = cfg["status_fd"]
    fcntl.fcntl(status_fd, fcntl.F_SETFD, fcntl.FD_CLOEXEC)
    report = {"ok": False, "uid": os.getuid(), "platform": sys.platform}
    try:
        if cfg.get("acquire_ctty"):  # test hook: the launcher's session holder handed over its terminal
            fd = _open_ctty()
            if fd is None:
                raise Refused("acquire_ctty: the target would start without a controlling terminal")
            os.close(fd)
            report["acquire_ctty"] = True
        _close_inherited({status_fd})
        if cfg.get("new_session"):
            report["new_session"] = _leave_terminal_session()
        if sys.platform.startswith("linux"):
            libc = _libc()
            report["caps_dropped"] = _drop_capabilities(libc) if cfg.get("drop_caps", True) else False
            _check(libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0), "set no_new_privs")
            report["no_new_privs"] = _check(libc.prctl(PR_GET_NO_NEW_PRIVS, 0, 0, 0, 0), "get no_new_privs")
            if cfg.get("landlock"):
                report["landlock_abi"], report["landlock_errata"] = _restrict_landlock(libc, cfg)
                report["rules"] = len(cfg["rules"])
            if cfg.get("seccomp"):
                report["seccomp"] = _seccomp_filter(libc, bool(cfg.get("unix_sockets")))
            status = _proc_status()
            report["caps"] = {key: status.get(key) for key in ("CapEff", "CapPrm", "CapBnd", "CapAmb")}
        elif cfg.get("landlock") or cfg.get("seccomp"):
            raise Refused("Landlock and seccomp are only available on Linux")
        _restore_default_signals()
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
