"""Test agent for ``babylon60 demo``: tries one access path and reports it.

Runs as ``python -I -S -B -c <this source> <config-json>`` with the standard
library only, inside or outside the sandbox. It prints a single JSON line with
the outcome and up to 256 bytes of whatever it obtained (hex). The launcher
decides what counts as an effect; this script never judges its own success.
"""

import ctypes
import errno
import json
import os
import re
import socket
import subprocess
import sys

cfg = json.loads(sys.argv[1])
HOME, WS, KEY = cfg["home"], cfg["ws"], cfg["key"]
SSH_DIR = os.path.dirname(KEY)
LINUX = sys.platform.startswith("linux")


def _read_fd(fd):
    try:
        return os.read(fd, 4096)
    finally:
        os.close(fd)


def _read(path, flags=0, dir_fd=None):
    return _read_fd(os.open(path, os.O_RDONLY | flags, dir_fd=dir_fd))


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


def l1_stat_key():
    return str(os.stat(KEY).st_size).encode()


def l2_preexisting_hardlink():
    return _read(cfg["prelinked"])


def l3_unix_socket_helper():
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
        client.settimeout(5)
        client.connect(cfg["socket"])
        return client.recv(4096)


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
