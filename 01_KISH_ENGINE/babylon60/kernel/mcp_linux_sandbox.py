"""Linux L3 confinement backend using Landlock LSM + seccomp-BPF.

Kept strictly separate from macOS Seatbelt primitives. Performs fail-closed
preflight of kernel Landlock ABI, PR_SET_NO_NEW_PRIVS, and seccomp filter
support before launching any candidate process, strips inherited descriptors
via close_range(3, ~0U, 0), enforces filesystem mediation with Landlock, and
installs an architecture-checked seccomp-BPF filter before user code runs.
"""

from __future__ import annotations

import ctypes
import ctypes.util
import json
import os
from pathlib import Path
import platform
import sys

from blake3 import blake3

ISOLATION_BACKEND = "linux-landlock-seccomp"

PR_SET_NO_NEW_PRIVS = 38
PR_GET_SECCOMP = 21
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2

LANDLOCK_CREATE_RULESET_VERSION = 1 << 0

SYSCALL_TABLES: dict[str, dict[str, int]] = {
    "aarch64": {
        "landlock_create_ruleset": 444,
        "landlock_add_rule": 445,
        "landlock_restrict_self": 446,
        "close_range": 436,
        "umount2": 39,
        "mount": 40,
        "unshare": 97,
        "kexec_load": 104,
        "init_module": 105,
        "delete_module": 106,
        "ptrace": 117,
        "socket": 198,
        "bind": 200,
        "listen": 201,
        "accept": 202,
        "connect": 203,
        "sendto": 206,
        "recvfrom": 207,
        "sendmsg": 211,
        "recvmsg": 212,
        "clone": 220,
        "execve": 221,
        "accept4": 242,
        "recvmmsg": 243,
        "setns": 268,
        "sendmmsg": 269,
        "process_vm_readv": 270,
        "process_vm_writev": 271,
        "finit_module": 273,
        "bpf": 280,
        "execveat": 281,
        "kexec_file_load": 294,
        "clone3": 435,
    },
    "x86_64": {
        "landlock_create_ruleset": 444,
        "landlock_add_rule": 445,
        "landlock_restrict_self": 446,
        "close_range": 436,
        "socket": 41,
        "connect": 42,
        "accept": 43,
        "sendto": 44,
        "recvfrom": 45,
        "sendmsg": 46,
        "recvmsg": 47,
        "bind": 49,
        "listen": 50,
        "clone": 56,
        "fork": 57,
        "vfork": 58,
        "execve": 59,
        "ptrace": 101,
        "mount": 165,
        "umount2": 166,
        "init_module": 175,
        "delete_module": 176,
        "kexec_load": 246,
        "unshare": 272,
        "accept4": 288,
        "recvmmsg": 299,
        "sendmmsg": 307,
        "setns": 308,
        "process_vm_readv": 310,
        "process_vm_writev": 311,
        "finit_module": 313,
        "kexec_file_load": 320,
        "bpf": 321,
        "execveat": 322,
        "clone3": 435,
    },
}

DENIED_SYSCALL_NAMES: tuple[str, ...] = (
    "accept",
    "accept4",
    "bind",
    "bpf",
    "clone",
    "clone3",
    "connect",
    "delete_module",
    "execve",
    "execveat",
    "finit_module",
    "fork",
    "init_module",
    "kexec_file_load",
    "kexec_load",
    "listen",
    "mount",
    "process_vm_readv",
    "process_vm_writev",
    "ptrace",
    "recvmmsg",
    "recvfrom",
    "recvmsg",
    "sendmmsg",
    "sendmsg",
    "sendto",
    "setns",
    "socket",
    "umount2",
    "unshare",
    "vfork",
)

# Trusted bootstrap executed inside `python3 -I -S -B -X utf8 -c`.
# Applies close_range(3, ~0U, 0), RLIMITs, Landlock ruleset, PR_SET_NO_NEW_PRIVS,
# and seccomp-BPF filter BEFORE opening or executing the pinned candidate script.
LINUX_BOOTSTRAP = """import ctypes, errno, json, os, resource, sys

PR_SET_NO_NEW_PRIVS = 38
PR_SET_SECCOMP = 22
SECCOMP_MODE_FILTER = 2
SECCOMP_RET_ALLOW = 0x7FFF0000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_KILL_PROCESS = 0x80000000

BPF_LD, BPF_W, BPF_ABS = 0x00, 0x00, 0x20
BPF_JMP, BPF_JEQ, BPF_K = 0x05, 0x10, 0x00
BPF_RET = 0x06

LANDLOCK_RULE_PATH_BENEATH = 1
LANDLOCK_ACCESS_FS_EXECUTE = 1 << 0
LANDLOCK_ACCESS_FS_WRITE_FILE = 1 << 1
LANDLOCK_ACCESS_FS_READ_FILE = 1 << 2
LANDLOCK_ACCESS_FS_READ_DIR = 1 << 3
LANDLOCK_ACCESS_FS_REMOVE_DIR = 1 << 4
LANDLOCK_ACCESS_FS_REMOVE_FILE = 1 << 5
LANDLOCK_ACCESS_FS_MAKE_CHAR = 1 << 6
LANDLOCK_ACCESS_FS_MAKE_DIR = 1 << 7
LANDLOCK_ACCESS_FS_MAKE_REG = 1 << 8
LANDLOCK_ACCESS_FS_MAKE_SOCK = 1 << 9
LANDLOCK_ACCESS_FS_MAKE_FIFO = 1 << 10
LANDLOCK_ACCESS_FS_MAKE_BLOCK = 1 << 11
LANDLOCK_ACCESS_FS_MAKE_SYM = 1 << 12
LANDLOCK_ACCESS_FS_REFER = 1 << 13
LANDLOCK_ACCESS_FS_TRUNCATE = 1 << 14
LANDLOCK_ACCESS_NET_BIND_TCP = 1 << 0
LANDLOCK_ACCESS_NET_CONNECT_TCP = 1 << 1

class _RulesetAttr(ctypes.Structure):
    _fields_ = [("handled_access_fs", ctypes.c_uint64), ("handled_access_net", ctypes.c_uint64)]

class _PathBeneathAttr(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("allowed_access", ctypes.c_uint64), ("parent_fd", ctypes.c_int32)]

class _SockFilter(ctypes.Structure):
    _fields_ = [("code", ctypes.c_uint16), ("jt", ctypes.c_uint8), ("jf", ctypes.c_uint8), ("k", ctypes.c_uint32)]

class _SockFprog(ctypes.Structure):
    _fields_ = [("len", ctypes.c_uint16), ("filter", ctypes.POINTER(_SockFilter))]

cfg = json.loads(sys.argv[1])
script_path = sys.argv[2]
cpu_limit = int(sys.argv[3])

lib = ctypes.CDLL(None, use_errno=True)
lib.syscall.restype = ctypes.c_long
lib.prctl.restype = ctypes.c_int

# 1. Revoke all inherited descriptors >= 3 immediately
rc_close = lib.syscall(ctypes.c_long(cfg["sys_close_range"]), ctypes.c_uint(3), ctypes.c_uint(0xFFFFFFFF), ctypes.c_uint(0))
if rc_close != 0:
    os.closerange(3, 4096)

# 2. Hard resource limits
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
resource.setrlimit(resource.RLIMIT_FSIZE, (1048576, 1048576))
resource.setrlimit(resource.RLIMIT_NOFILE, (32, 32))

# 3. Install Landlock LSM filesystem (+ TCP on ABI >= 4) restrictions
abi = int(cfg["landlock_abi"])
handled_fs = (
    LANDLOCK_ACCESS_FS_EXECUTE | LANDLOCK_ACCESS_FS_WRITE_FILE | LANDLOCK_ACCESS_FS_READ_FILE
    | LANDLOCK_ACCESS_FS_READ_DIR | LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_REMOVE_FILE
    | LANDLOCK_ACCESS_FS_MAKE_CHAR | LANDLOCK_ACCESS_FS_MAKE_DIR | LANDLOCK_ACCESS_FS_MAKE_REG
    | LANDLOCK_ACCESS_FS_MAKE_SOCK | LANDLOCK_ACCESS_FS_MAKE_FIFO | LANDLOCK_ACCESS_FS_MAKE_BLOCK
    | LANDLOCK_ACCESS_FS_MAKE_SYM
)
if abi >= 2:
    handled_fs |= LANDLOCK_ACCESS_FS_REFER
if abi >= 3:
    handled_fs |= LANDLOCK_ACCESS_FS_TRUNCATE
handled_net = (LANDLOCK_ACCESS_NET_BIND_TCP | LANDLOCK_ACCESS_NET_CONNECT_TCP) if abi >= 4 else 0
rattr = _RulesetAttr(handled_access_fs=handled_fs, handled_access_net=handled_net)
rsize = 16 if abi >= 4 else 8
rfd = lib.syscall(ctypes.c_long(cfg["sys_landlock_create_ruleset"]), ctypes.byref(rattr), ctypes.c_size_t(rsize), ctypes.c_uint32(0))
if rfd < 0:
    raise OSError(ctypes.get_errno(), "landlock_create_ruleset failed")

def _add_path(path_str, access_mask):
    if not os.path.exists(path_str):
        return
    eff = access_mask if os.path.isdir(path_str) else (access_mask & LANDLOCK_ACCESS_FS_READ_FILE)
    if eff == 0:
        return
    pfd = os.open(path_str, os.O_PATH | os.O_CLOEXEC)
    try:
        pattr = _PathBeneathAttr(allowed_access=eff, parent_fd=pfd)
        if lib.syscall(ctypes.c_long(cfg["sys_landlock_add_rule"]), ctypes.c_int(rfd), ctypes.c_uint32(LANDLOCK_RULE_PATH_BENEATH), ctypes.byref(pattr), ctypes.c_uint32(0)) != 0:
            raise OSError(ctypes.get_errno(), f"landlock_add_rule failed for {path_str}")
    finally:
        os.close(pfd)

try:
    ro_mask = LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR
    for ro_path in cfg["readonly_paths"]:
        _add_path(ro_path, ro_mask)
    rw_mask = (
        LANDLOCK_ACCESS_FS_READ_FILE | LANDLOCK_ACCESS_FS_READ_DIR | LANDLOCK_ACCESS_FS_WRITE_FILE
        | LANDLOCK_ACCESS_FS_REMOVE_FILE | LANDLOCK_ACCESS_FS_REMOVE_DIR | LANDLOCK_ACCESS_FS_MAKE_REG
        | LANDLOCK_ACCESS_FS_MAKE_DIR | LANDLOCK_ACCESS_FS_MAKE_SYM
    )
    if abi >= 3:
        rw_mask |= LANDLOCK_ACCESS_FS_TRUNCATE
    _add_path(cfg["work_dir"], rw_mask)
    if lib.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS failed")
    if lib.syscall(ctypes.c_long(cfg["sys_landlock_restrict_self"]), ctypes.c_int(rfd), ctypes.c_uint32(0)) != 0:
        raise OSError(ctypes.get_errno(), "landlock_restrict_self failed")
finally:
    os.close(rfd)

# 4. Install seccomp-BPF filter
denied_nrs = [int(x) for x in cfg["denied_syscall_nrs"]]
n = len(denied_nrs)
insns = [
    _SockFilter(BPF_LD | BPF_W | BPF_ABS, 0, 0, 4),
    _SockFilter(BPF_JMP | BPF_JEQ | BPF_K, 1, 0, int(cfg["audit_arch"])),
    _SockFilter(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_KILL_PROCESS),
    _SockFilter(BPF_LD | BPF_W | BPF_ABS, 0, 0, 0),
]
for idx, nr in enumerate(denied_nrs):
    insns.append(_SockFilter(BPF_JMP | BPF_JEQ | BPF_K, n - idx, 0, nr))
insns.append(_SockFilter(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_ALLOW))
insns.append(_SockFilter(BPF_RET | BPF_K, 0, 0, SECCOMP_RET_ERRNO | errno.EPERM))
arr = (_SockFilter * len(insns))(*insns)
prog = _SockFprog(len=len(insns), filter=arr)
if lib.prctl(PR_SET_SECCOMP, SECCOMP_MODE_FILTER, ctypes.byref(prog), 0, 0) != 0:
    raise OSError(ctypes.get_errno(), "PR_SET_SECCOMP failed")

# 5. Load and execute pinned script inside the active Landlock + seccomp cage
with open(script_path, "rb") as source:
    code = source.read(1048577)
if len(code) > 1048576:
    raise ValueError("script too large")
exec(compile(code, script_path, "exec"), {"__name__": "__main__", "__file__": script_path})
"""


def _libc() -> ctypes.CDLL:
    libc_name = ctypes.util.find_library("c") or "libc.so.6"
    lib = ctypes.CDLL(libc_name, use_errno=True)
    lib.syscall.restype = ctypes.c_long
    lib.prctl.restype = ctypes.c_int
    return lib


def preflight_linux_isolation(min_landlock_abi: int = 1) -> dict[str, object]:
    """Verify kernel Landlock ABI and seccomp availability; fail closed on any error."""
    if sys.platform != "linux":
        raise RuntimeError("Linux Landlock+seccomp backend requires sys.platform == 'linux'")
    arch = platform.machine()
    if arch not in SYSCALL_TABLES:
        raise RuntimeError(f"Unsupported Linux architecture for seccomp/Landlock: {arch}")
    try:
        lib = _libc()
    except OSError as exc:
        raise RuntimeError(f"Cannot load libc for Linux isolation preflight: {exc}") from exc
    sc = SYSCALL_TABLES[arch]
    ctypes.set_errno(0)
    abi = int(
        lib.syscall(
            ctypes.c_long(sc["landlock_create_ruleset"]),
            None,
            ctypes.c_size_t(0),
            ctypes.c_uint32(LANDLOCK_CREATE_RULESET_VERSION),
        )
    )
    if abi < min_landlock_abi:
        err = ctypes.get_errno()
        raise RuntimeError(f"Landlock LSM unavailable or ABI {abi} < {min_landlock_abi} (errno={err})")
    ctypes.set_errno(0)
    seccomp_mode = int(lib.prctl(PR_GET_SECCOMP, 0, 0, 0, 0))
    if seccomp_mode < 0:
        err = ctypes.get_errno()
        raise RuntimeError(f"seccomp unavailable in kernel (errno={err})")
    return {
        "arch": arch,
        "kernel": platform.release(),
        "landlock_abi": abi,
        "seccomp_mode": seccomp_mode,
    }


def linux_runtime(min_landlock_abi: int = 1) -> tuple[str, str, dict[str, object]]:
    """Return (executable, base_prefix, preflight_meta) or raise RuntimeError."""
    preflight = preflight_linux_isolation(min_landlock_abi=min_landlock_abi)
    base = os.path.realpath(sys.base_prefix)
    executable = os.path.realpath(sys.executable)
    if not os.path.isfile(executable):
        raise RuntimeError("Python runtime executable unavailable")
    if base in ("/", "/home", "/root", os.path.expanduser("~")):
        raise RuntimeError("Refusing an overbroad Python runtime root")
    return executable, base, preflight


def build_linux_profile(
    executable: str,
    base: str,
    code_dir: str,
    work_dir: str,
    preflight: dict[str, object] | None = None,
) -> str:
    """Build deterministic JSON profile for LINUX_BOOTSTRAP."""
    meta = preflight if preflight is not None else preflight_linux_isolation()
    arch = str(meta["arch"])
    abi = int(str(meta["landlock_abi"]))
    sc = SYSCALL_TABLES[arch]
    audit_arch = 0xC00000B7 if arch == "aarch64" else 0xC000003E

    candidates = [
        executable,
        base,
        "/usr",
        "/lib",
        "/lib64",
        "/bin",
        "/etc/ld.so.cache",
        "/dev/null",
        "/dev/urandom",
        code_dir,
    ]
    readonly_paths: list[str] = []
    seen: set[str] = set()
    for item in candidates:
        if os.path.exists(item):
            real = os.path.realpath(item)
            if real not in seen:
                seen.add(real)
                readonly_paths.append(real)

    denied_nrs = sorted({sc[name] for name in DENIED_SYSCALL_NAMES if name in sc})
    payload: dict[str, object] = {
        "backend": ISOLATION_BACKEND,
        "arch": arch,
        "audit_arch": audit_arch,
        "landlock_abi": abi,
        "work_dir": os.path.realpath(work_dir),
        "code_dir": os.path.realpath(code_dir),
        "readonly_paths": readonly_paths,
        "denied_syscalls": [name for name in DENIED_SYSCALL_NAMES if name in sc],
        "denied_syscall_nrs": denied_nrs,
        "sys_close_range": sc["close_range"],
        "sys_landlock_create_ruleset": sc["landlock_create_ruleset"],
        "sys_landlock_add_rule": sc["landlock_add_rule"],
        "sys_landlock_restrict_self": sc["landlock_restrict_self"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload["profile_digest"] = blake3(canonical).hexdigest()
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def linux_resident_bytes(pid: int) -> int:
    """Query resident set size (RSS) of a child process via /proc/<pid>/statm."""
    statm_path = Path(f"/proc/{pid}/statm")
    raw = statm_path.read_text(encoding="ascii").split()
    if len(raw) < 2:
        raise OSError("Malformed /proc statm")
    resident_pages = int(raw[1])
    page_size = int(os.sysconf("SC_PAGE_SIZE"))
    return resident_pages * page_size


def linux_probe_source(
    canary: Path,
    outside_write: Path,
    work: Path,
    executable: str,
    tcp_port: int,
    unix_path: str,
) -> str:
    """Probe script verifying Landlock FS mediation, FD stripping, and seccomp-BPF blocks."""
    arch = platform.machine()
    sc = SYSCALL_TABLES.get(arch, SYSCALL_TABLES["aarch64"])
    return f"""import ctypes, errno, json, os, socket, subprocess, sys
from pathlib import Path
results = {{}}
def denied(name, operation):
    try:
        operation()
    except OSError as exc:
        results[name] = exc.errno in (errno.EPERM, errno.EACCES, errno.EXDEV, errno.EBADF, errno.ENOENT)
    else:
        results[name] = False
canary = Path({str(canary)!r})
work = Path({str(work)!r})
denied('read_outside', lambda: canary.read_bytes())
denied('write_outside', lambda: Path({str(outside_write)!r}).write_text('escape'))
denied('unlink_outside', lambda: canary.unlink())
denied('rename_outside', lambda: canary.rename(work / 'renamed-canary'))
link = work / 'outside-link'
link.symlink_to(canary)
denied('symlink_read', lambda: link.read_bytes())
denied('hardlink_outside', lambda: os.link(canary, work / 'outside-hardlink'))
denied('proc_self_fd', lambda: os.listdir('/proc/self/fd'))
def tcp_connect():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        client.connect(('127.0.0.1', {tcp_port!r}))
def unix_connect():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(1)
        client.connect({unix_path!r})
def udp_send():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as client:
        client.sendto(b'probe', ('127.0.0.1', {tcp_port!r}))
denied('network_tcp', tcp_connect)
denied('network_unix', unix_connect)
denied('network_udp', udp_send)
marker = work / 'spawned'
command = [{executable!r}, '-I', '-S', '-c', "from pathlib import Path; Path(" + repr(str(marker)) + ").write_text('child')"]
denied('subprocess', lambda: subprocess.run(command, check=False, timeout=1))
def spawn():
    pid = os.posix_spawn(command[0], command, {{}})
    os.waitpid(pid, 0)
denied('posix_spawn', spawn)
def fork():
    pid = os.fork()
    if pid == 0:
        marker.write_text('fork')
        os._exit(0)
    os.waitpid(pid, 0)
denied('fork', fork)
lib = ctypes.CDLL(None, use_errno=True)
lib.syscall.restype = ctypes.c_long
def sys_denied(name, nr, *args):
    ctypes.set_errno(0)
    rc = lib.syscall(ctypes.c_long(nr), *[ctypes.c_long(a) for a in args])
    err = ctypes.get_errno()
    results[name] = (rc == -1 and err in (errno.EPERM, errno.EACCES))
sys_denied('ptrace', {sc["ptrace"]}, 0, 0, 0, 0)
sys_denied('process_vm_writev', {sc["process_vm_writev"]}, os.getpid(), 0, 0, 0, 0, 0)
sys_denied('unshare', {sc["unshare"]}, 0x10000000)
sys_denied('mount', {sc["mount"]}, 0, 0, 0, 0, 0)
sys_denied('bpf', {sc["bpf"]}, 0, 0, 0)
(work / 'positive').write_text('allowed')
results['write_private'] = (work / 'positive').read_text() == 'allowed'
print(json.dumps(results), flush=True)
"""


LINUX_EXPECTED_PROBE_KEYS = {
    "read_outside",
    "write_outside",
    "unlink_outside",
    "rename_outside",
    "symlink_read",
    "hardlink_outside",
    "proc_self_fd",
    "network_tcp",
    "network_unix",
    "network_udp",
    "subprocess",
    "posix_spawn",
    "fork",
    "ptrace",
    "process_vm_writev",
    "unshare",
    "mount",
    "bpf",
    "write_private",
}
