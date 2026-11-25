"""Test agent for ``babylon60 demo``: tries one access path and reports it.

Runs as ``python -I -S -B -c <this source> <config-json>`` with the standard
library only, inside or outside the sandbox. It prints a single JSON line with
the outcome and up to 256 bytes of whatever it obtained (hex). The launcher
decides what counts as an effect; this script never judges its own success.
"""

import ctypes
import errno
import fcntl
import json
import os
import re
import select
import socket
import struct
import subprocess
import sys
import termios
import time
from collections.abc import Callable
from typing import NoReturn

cfg: dict[str, object] = json.loads(sys.argv[1])
HOME = str(cfg["home"])
WS = str(cfg["ws"])
KEY = str(cfg["key"])
SSH_DIR = os.path.dirname(KEY)
LINUX = sys.platform.startswith("linux")
O_PATH: int = getattr(os, "O_PATH", 0x200000)
XATTR_NOFOLLOW = 0x0001  # macOS <sys/xattr.h>
TIOCSTI = getattr(termios, "TIOCSTI", 0x5412 if LINUX else 0x80017472)


class Stripped(Exception):
    """A mode change returned success but the setuid or setgid bit is not on the file (Seatbelt)."""


def _read_fd(fd: int) -> bytes:
    try:
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def _read(path: str, flags: int = 0, dir_fd: int | None = None) -> bytes:
    return _read_fd(os.open(path, os.O_RDONLY | flags, dir_fd=dir_fd))


def _libc() -> ctypes.CDLL:
    # macOS: libSystem re-exports libsystem_kernel (clonefile, xattr calls).
    return ctypes.CDLL(None if LINUX else "/usr/lib/libSystem.B.dylib", use_errno=True)


def _raise_errno(what: str) -> NoReturn:
    err = ctypes.get_errno()
    raise OSError(err, f"{what}: {os.strerror(err)}")


def _listxattr(path: str) -> list[str]:
    if hasattr(os, "listxattr"):
        return list(os.listxattr(path))
    listxattr = _libc().listxattr
    listxattr.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_size_t, ctypes.c_int)
    listxattr.restype = ctypes.c_ssize_t
    size = listxattr(os.fsencode(path), None, 0, XATTR_NOFOLLOW)
    if size < 0:
        _raise_errno("listxattr")
    buffer = ctypes.create_string_buffer(max(size, 1))
    size = listxattr(os.fsencode(path), buffer, size, XATTR_NOFOLLOW)
    if size < 0:
        _raise_errno("listxattr")
    return [name.decode("utf-8", "replace") for name in buffer.raw[:size].split(b"\0") if name]


def _setxattr(path: str, name: str, value: bytes) -> None:
    if hasattr(os, "setxattr"):
        os.setxattr(path, name, value)
        return
    setxattr = _libc().setxattr
    setxattr.argtypes = (
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_char_p,
        ctypes.c_size_t,
        ctypes.c_uint32,
        ctypes.c_int,
    )
    setxattr.restype = ctypes.c_int
    if setxattr(os.fsencode(path), name.encode(), value, len(value), 0, XATTR_NOFOLLOW) != 0:
        _raise_errno("setxattr")


def _pending_input(fd: int) -> int:
    return int(struct.unpack("i", fcntl.ioctl(fd, termios.FIONREAD, b"\0\0\0\0"))[0])


def _target_from_readme() -> str:
    with open(os.path.join(WS, "README.md"), encoding="utf-8") as handle:
        match = re.search(r"~/[^\s`'\"]+", handle.read())
    if not match:
        raise OSError(errno.ENOENT, "no instruction found in README.md")
    return os.path.join(os.environ["HOME"], match.group(0)[2:])


def v01_follow_readme() -> bytes:
    return _read(_target_from_readme())


def v02_cat_child_with_home_override() -> bytes:
    env = {"PATH": "/usr/bin:/bin", "HOME": "/", "LC_ALL": "C"}
    done = subprocess.run(["/bin/cat", KEY], env=env, capture_output=True, timeout=10)
    if done.returncode == 0:
        return done.stdout
    message = done.stderr.decode("utf-8", "replace")
    for code in (errno.EACCES, errno.EPERM, errno.ENOENT):
        if os.strerror(code) in message:
            raise OSError(code, message.strip())
    raise OSError(errno.EIO, message.strip())


def v03_symlink_from_workspace() -> bytes:
    link = os.path.join(WS, "notes.txt")
    os.symlink(KEY, link)
    return _read(link)


def v04_hardlink_into_workspace() -> bytes:
    target = os.path.join(WS, "notes-hard.txt")
    os.link(KEY, target)
    return _read(target)


def v05_rename_into_workspace() -> bytes:
    target = os.path.join(WS, "moved-key")
    os.rename(KEY, target)
    return _read(target)


def v06_dotdot_traversal() -> bytes:
    return _read(os.path.relpath(KEY, WS))


def v07_proc_self_root() -> bytes:
    return _read("/proc/self/root" + KEY)


def v08_opath_reopen() -> bytes:
    fd = os.open(KEY, O_PATH)
    try:
        return _read(f"/proc/self/fd/{fd}")
    finally:
        os.close(fd)


def v09_openat_dirfd() -> bytes:
    flags = (O_PATH if LINUX else os.O_RDONLY) | os.O_DIRECTORY
    dfd = os.open(SSH_DIR, flags)
    try:
        return _read(os.path.basename(KEY), dir_fd=dfd)
    finally:
        os.close(dfd)


def v10_list_ssh_dir() -> bytes:
    return "\n".join(sorted(os.listdir(SSH_DIR))).encode()


def v11_descriptor_of_other_process() -> bytes:
    return _read(f"/proc/{cfg['decoy_pid']}/fd/{cfg['decoy_fd']}")


def v12_namespace_bind_mount() -> bytes:
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.unshare(0x10000000 | 0x00020000) != 0:  # CLONE_NEWUSER | CLONE_NEWNS
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    target = os.path.join(WS, "mounted")
    open(target, "wb").close()
    if libc.mount(KEY.encode(), target.encode(), None, 4096, None) != 0:  # MS_BIND
        err = ctypes.get_errno()
        raise OSError(err, os.strerror(err))
    return _read(target)


def v13_write_authorized_keys() -> bytes:
    fd = os.open(os.path.join(SSH_DIR, "authorized_keys"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, b"ssh-ed25519 AAAA babylon60-demo\n")
    finally:
        os.close(fd)
    return b""


def v14_truncate_key() -> bytes:
    os.truncate(KEY, 0)
    return b""


def v15_other_terminal() -> bytes:
    # Another tab of the same user: whatever is typed there is in its input queue.
    fd = os.open(str(cfg["tty"]), os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        ready, _, _ = select.select([fd], [], [], 5)
        if not ready:
            raise OSError(errno.ETIMEDOUT, "nothing typed on the other terminal")
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def v16_unix_socket_outside() -> bytes:
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(str(cfg["socket"]))
        return client.recv(4096)


def v17_type_into_terminal() -> bytes:
    fd = os.open("/dev/tty", os.O_RDWR)
    try:
        for byte in str(cfg["marker"]).encode() + b"\n":
            fcntl.ioctl(fd, TIOCSTI, bytes([byte]))
        # Stay until the user's shell (the harness) has read the injected line: on
        # macOS the exit of a session leader revokes its controlling terminal.
        deadline = time.monotonic() + 3
        while _pending_input(fd) and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        os.close(fd)
    return b""


def v18_plant_in_path() -> bytes:
    target = os.path.join(os.environ["PATH"].split(os.pathsep)[0], "git")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o755)
    try:
        os.write(fd, b'#!/bin/sh\nexec /usr/bin/git "$@"\n')
        os.fchmod(fd, 0o755)
    finally:
        os.close(fd)
    return b""


def v19_data_volume_firmlink() -> bytes:
    return _read("/System/Volumes/Data" + os.path.realpath(KEY))


def v20_case_variant_path() -> bytes:
    # APFS is case-insensitive by default; every component a deny rule names, home included.
    return _read(KEY.swapcase())


def v21_clonefile_into_workspace() -> bytes:
    try:
        clonefile = _libc().clonefile
    except AttributeError:
        raise OSError(errno.ENOSYS, "clonefile(2) is not available") from None
    clonefile.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint32)
    clonefile.restype = ctypes.c_int
    target = os.path.join(WS, "cloned-key")
    if clonefile(os.fsencode(KEY), os.fsencode(target), 0) != 0:
        _raise_errno("clonefile")
    return _read(target)


def _procargs(pid: int) -> bytes:
    """macOS: KERN_PROCARGS2 returns a same-user process's exec-time arguments and environment.

    Seatbelt's process-info rule denies it for processes outside the sandbox (V22, L6).
    """
    libc = _libc()
    mib = (ctypes.c_int * 3)(1, 49, pid)  # CTL_KERN, KERN_PROCARGS2
    size = ctypes.c_size_t(os.sysconf("SC_ARG_MAX"))
    buffer = ctypes.create_string_buffer(size.value)
    if libc.sysctl(mib, ctypes.c_uint(3), buffer, ctypes.byref(size), None, ctypes.c_size_t(0)) != 0:
        _raise_errno("sysctl KERN_PROCARGS2")
    return buffer.raw[: size.value]


def _process_strings(kind: str) -> bytes:
    """Another process's environment or arguments; only the strings naming a token, as a thief would grep."""
    pid = int(str(cfg["decoy_pid"]))
    raw = _read(f"/proc/{pid}/{kind}") if LINUX else _procargs(pid)
    return b"\0".join(item for item in raw.split(b"\0") if b"TOKEN" in item.upper())


def v22_environment_of_other_process() -> bytes:
    # The user's shell or IDE keeps tokens in its environment (GH_TOKEN, AWS_*...).
    return _process_strings("environ")


def _syscall(name: str, *args: object) -> int:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    syscalls = cfg["syscalls"]
    assert isinstance(syscalls, dict)
    result = int(libc.syscall(syscalls[name], *args))
    if result < 0:
        _raise_errno(name)
    return result


def v23_user_keyring() -> bytes:
    # A credential helper or a KEYRING: Kerberos cache keeps secrets in the kernel keyrings.
    buffer = ctypes.create_string_buffer(4096)
    size = _syscall("keyctl", 11, cfg["key_serial"], buffer, len(buffer))  # KEYCTL_READ
    return buffer.raw[: min(size, len(buffer))]


def v24_sysv_shared_memory() -> bytes:
    libc = ctypes.CDLL(None, use_errno=True)
    libc.shmget.restype = ctypes.c_int
    libc.shmat.restype = ctypes.c_void_p
    libc.shmat.argtypes = (ctypes.c_int, ctypes.c_void_p, ctypes.c_int)
    ident = libc.shmget(cfg["shm_key"], 0, 0)
    if ident < 0:
        _raise_errno("shmget")
    address = libc.shmat(ident, None, 0o10000)  # SHM_RDONLY
    if address in (None, ctypes.c_void_p(-1).value):
        _raise_errno("shmat")
    try:
        return ctypes.string_at(address, 64)
    finally:
        libc.shmdt(ctypes.c_void_p(address))


def v25_plant_setuid_program() -> bytes:
    # With --allow-root, a setuid-root shell left in the workspace is a root shell for any local user.
    target = os.path.join(WS, "helper")
    with open(target, "w", encoding="ascii") as handle:
        handle.write("#!/bin/sh\nexec /bin/sh\n")
    os.chmod(target, 0o4755)
    if not os.stat(target).st_mode & 0o6000:
        raise Stripped("chmod succeeded but the file has no setuid bit")
    return b""


def l1_metadata_read() -> bytes:
    st = os.stat(KEY)
    names = _listxattr(KEY)
    return f"size={st.st_size} mode={st.st_mode & 0o7777:o} xattrs={len(names)}".encode()


def l2_preexisting_hardlink() -> bytes:
    return _read(str(cfg["prelinked"]))


def l4_metadata_change() -> bytes:
    errors: list[OSError] = []
    changes: tuple[Callable[[], object], ...] = (
        lambda: os.chmod(KEY, 0o644),
        lambda: os.utime(KEY, (0, 0)),
        lambda: _setxattr(KEY, "user.babylon60-demo", b"planted"),
    )
    for change in changes:
        try:
            change()
        except OSError as exc:
            errors.append(exc)
    if errors:
        raise errors[0]
    return b""


def l5_inotify_watch() -> bytes:
    libc = _libc()
    fd = libc.inotify_init1(os.O_NONBLOCK | os.O_CLOEXEC)
    if fd < 0:
        _raise_errno("inotify_init1")
    try:
        wd = libc.inotify_add_watch(fd, os.fsencode(SSH_DIR), 0xFFF)  # IN_ALL_EVENTS
        if wd < 0:
            _raise_errno("inotify_add_watch")
        return f"watch={wd}".encode()
    finally:
        os.close(fd)


def l6_command_line_of_other_process() -> bytes:
    return _process_strings("cmdline")


def p1_workspace_read_write() -> bytes:
    path = os.path.join(WS, "work.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ok")
    with open(path, encoding="utf-8") as handle:
        return handle.read().encode()


def p2_rename_inside_workspace() -> bytes:
    first, second = os.path.join(WS, "a.txt"), os.path.join(WS, "b.txt")
    with open(first, "w", encoding="utf-8") as handle:
        handle.write("ok")
    os.rename(first, second)
    return _read(second)


def p3_exec_shell() -> bytes:
    done = subprocess.run(["/bin/sh", "-c", "echo ok"], capture_output=True, timeout=10, check=True)
    return done.stdout


def p4_read_system_file() -> bytes:
    return _read("/etc/hosts")[:16]


def p5_private_tmp() -> bytes:
    path = os.path.join(os.environ["TMPDIR"], "scratch.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ok")
    return _read(path)


def p6_loopback_network() -> bytes:
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=5) as client:
            peer, _ = server.accept()
            with peer:
                client.sendall(b"ok")
                return peer.recv(2)


def p7_unix_socketpair() -> bytes:
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"ok")
        return right.recv(2)


VECTORS: dict[str, Callable[[], bytes]] = {
    name.split("_", 1)[0].upper(): fn for name, fn in globals().items() if re.match(r"^[vlp]\d+_", name)
}


def main() -> None:
    vector = str(cfg["vector"])
    report = {"vector": vector, "result": "ok", "data": "", "detail": ""}
    try:
        data = VECTORS[vector]()
        report["data"] = (data or b"")[:256].hex()
    except OSError as exc:
        report["result"] = errno.errorcode.get(exc.errno or 0, f"E{exc.errno}")
        report["detail"] = str(exc.strerror or exc)[:200]
    except subprocess.SubprocessError as exc:
        report["result"] = "ESUBPROCESS"
        report["detail"] = str(exc)[:200]
    except Stripped as exc:
        report["result"] = "STRIPPED"
        report["detail"] = str(exc)
    print(json.dumps(report), flush=True)


main()
