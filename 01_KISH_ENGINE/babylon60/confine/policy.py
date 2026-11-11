"""What a confined agent may read, write and execute.

The policy is an allow-list. Anything not granted, including the whole home
directory, stays out of reach of the confined process tree on Linux (Landlock).
On macOS the same grants are rendered as Seatbelt rules (see ``seatbelt.py``).

Grants are checked by inode identity, walking ``..`` with ``O_PATH``
descriptors, never with ``Path.resolve`` (INV_C5_PATH_SYMLINK_CONFINEMENT).
The trampoline re-opens every granted path and refuses to start if its
``(st_dev, st_ino)`` changed between this check and the restriction.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass, field
import os
import pwd
import stat

from babylon60.confine.journal import digest

# Landlock filesystem access rights (include/uapi/linux/landlock.h).
EXECUTE = 1 << 0
WRITE_FILE = 1 << 1
READ_FILE = 1 << 2
READ_DIR = 1 << 3
REMOVE_DIR = 1 << 4
REMOVE_FILE = 1 << 5
MAKE_CHAR = 1 << 6
MAKE_DIR = 1 << 7
MAKE_REG = 1 << 8
MAKE_SOCK = 1 << 9
MAKE_FIFO = 1 << 10
MAKE_BLOCK = 1 << 11
MAKE_SYM = 1 << 12
REFER = 1 << 13
TRUNCATE = 1 << 14
IOCTL_DEV = 1 << 15
FILE_RIGHTS = EXECUTE | WRITE_FILE | READ_FILE | TRUNCATE | IOCTL_DEV
MIN_LANDLOCK_ABI = 3

SYSTEM_READ_EXEC = (
    "/usr",
    "/bin",
    "/sbin",
    "/lib",
    "/lib32",
    "/lib64",
    "/libx32",
    "/etc",
    "/opt",
    "/nix/store",
    "/snap",
    "/proc",
    "/sys",
    "/run/systemd/resolve",
)
DEVICE_FILES = ("/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom", "/dev/tty", "/dev/ptmx")
DEVICE_DIRS = ("/dev/pts",)
PROTECTED_RELATIVE = (
    ".ssh",
    ".gnupg",
    ".aws",
    ".azure",
    ".kube",
    ".docker",
    ".netrc",
    ".git-credentials",
    ".password-store",
    ".config/gcloud",
    ".config/gh",
    "Library/Keychains",
)

# Agent presets grant only the agent's own state and common install prefixes.
PRESETS: dict[str, dict[str, tuple[str, ...]]] = {
    "claude-code": {
        "write": ("~/.claude", "~/.claude.json", "~/.cache/claude"),
        "read": ("~/.local/share/claude", "~/.local/bin", "~/.npm-global", "~/.nvm", "~/.volta", "~/.bun"),
    },
    "codex": {
        "write": ("~/.codex",),
        "read": ("~/.local/bin", "~/.npm-global", "~/.nvm", "~/.volta", "~/.bun"),
    },
}


class PolicyError(ValueError):
    """A grant would weaken the policy (home, protected path, self-tampering)."""


Identity = tuple[int, int]


@dataclass(frozen=True)
class Grant:
    path: str
    access: str  # "ro", "rw" or "dev"
    dev: int
    ino: int
    is_dir: bool
    origin: str  # "system", "workspace", "tmp", "preset:<name>", "user", "runtime"


@dataclass(frozen=True)
class Policy:
    workspace: str
    homes: tuple[str, ...]
    protected: tuple[str, ...]
    grants: tuple[Grant, ...]
    skipped: tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, object]:
        return {
            "workspace": self.workspace,
            "homes": list(self.homes),
            "protected": list(self.protected),
            "grants": [asdict(grant) for grant in self.grants],
            "skipped": list(self.skipped),
        }

    def digest(self) -> str:
        """Digest of paths and access only: inode numbers differ between machines."""
        portable = {
            "workspace": self.workspace,
            "protected": list(self.protected),
            "grants": sorted([grant.path, grant.access] for grant in self.grants),
        }
        return digest(portable, domain=b"BABYLON60-CONFINE-POLICY/v1\x00")

    def landlock_rules(self, abi: int) -> tuple[int, int, list[dict[str, object]]]:
        """Return (handled_fs, scoped, rules) for a kernel exposing ``abi``."""
        handled = landlock_handled_fs(abi)
        rules: list[dict[str, object]] = []
        for grant in self.grants:
            if grant.access == "ro":
                access = EXECUTE | READ_FILE | READ_DIR
            elif grant.access == "dev":
                access = READ_FILE | WRITE_FILE | IOCTL_DEV | (READ_DIR if grant.is_dir else 0)
            else:
                access = handled & ~(MAKE_CHAR | MAKE_BLOCK)
            access &= handled
            if not grant.is_dir:
                access &= FILE_RIGHTS
            rules.append({"path": grant.path, "dev": grant.dev, "ino": grant.ino, "access": access})
        return handled, (3 if abi >= 6 else 0), rules


def landlock_handled_fs(abi: int) -> int:
    if abi < 1:
        raise PolicyError("Landlock is unavailable")
    handled = (1 << 13) - 1
    if abi >= 2:
        handled |= REFER
    if abi >= 3:
        handled |= TRUNCATE
    if abi >= 5:
        handled |= IOCTL_DEV
    return handled


def _identity_of_fd(fd: int) -> Identity:
    st = os.fstat(fd)
    return st.st_dev, st.st_ino


def ancestry(path: str | os.PathLike[str]) -> list[Identity]:
    """Identities of ``path`` and every physical ancestor up to ``/``."""
    if not hasattr(os, "O_PATH"):
        return _ancestry_by_stat(path)
    chain: list[Identity] = []
    fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            chain.append(_identity_of_fd(fd))
            parent_path = os.path.dirname(os.path.abspath(path)) or "/"
            parent = os.open(parent_path, os.O_PATH | os.O_CLOEXEC | os.O_DIRECTORY)
            os.close(fd)
            fd = parent
        while True:
            ident = _identity_of_fd(fd)
            chain.append(ident)
            parent = os.open("..", os.O_PATH | os.O_CLOEXEC | os.O_DIRECTORY, dir_fd=fd)
            os.close(fd)
            fd = parent
            if _identity_of_fd(fd) == ident:
                return chain
    finally:
        os.close(fd)


def _ancestry_by_stat(path: str | os.PathLike[str]) -> list[Identity]:
    """Platforms without ``O_PATH`` (macOS): stat ``..`` repeatedly; the kernel resolves it physically.

    Nothing is opened, so device nodes such as ``/dev/tty`` without a controlling
    terminal and directories without read permission are handled too.
    """
    current = os.path.abspath(path)
    st = os.stat(current)
    chain: list[Identity] = []
    if not stat.S_ISDIR(st.st_mode):
        chain.append((st.st_dev, st.st_ino))
        current = os.path.dirname(current) or "/"
    while True:
        st = os.stat(current)
        ident = (st.st_dev, st.st_ino)
        chain.append(ident)
        parent = os.stat(os.path.join(current, ".."))
        if (parent.st_dev, parent.st_ino) == ident:
            return chain
        current = os.path.join(current, "..")


def account_home() -> str:
    """Home directory from the account database, not from ``$HOME``."""
    return pwd.getpwuid(os.getuid()).pw_dir


def default_homes() -> tuple[str, ...]:
    homes = [account_home()]
    env_home = os.environ.get("HOME")
    if env_home and os.path.abspath(env_home) not in homes:
        homes.append(os.path.abspath(env_home))
    return tuple(homes)


def _expand(path: str, home: str) -> str:
    if path == "~" or path.startswith("~/"):
        path = home + path[1:]
    return os.path.abspath(path)


class _Guard:
    def __init__(self, homes: Sequence[str], protected: Sequence[str], self_paths: Sequence[str]) -> None:
        self.home_ids: list[set[Identity]] = []  # ancestry of each home, home itself first
        for home in homes:
            try:
                self.home_ids.append(set(ancestry(home)))
            except FileNotFoundError:
                continue
        self.protected_ids: dict[Identity, str] = {}
        self.protected_chains: list[tuple[str, list[Identity]]] = []
        for path in protected:
            try:
                chain = ancestry(path)
            except FileNotFoundError:
                continue
            self.protected_ids[chain[0]] = path
            self.protected_chains.append((path, chain))
        self.self_chains: list[tuple[str, list[Identity]]] = []
        for path in self_paths:
            try:
                self.self_chains.append((path, ancestry(path)))
            except FileNotFoundError:
                continue

    def check(self, path: str, access: str, chain: list[Identity]) -> None:
        own = chain[0]
        for ids in self.home_ids:
            if own in ids:
                raise PolicyError(f"Refusing to grant a home directory or one of its ancestors: {path}")
        for ident in chain:
            if ident in self.protected_ids:
                raise PolicyError(f"Refusing a grant inside protected path {self.protected_ids[ident]}: {path}")
        for protected, protected_chain in self.protected_chains:
            if own in protected_chain:
                raise PolicyError(f"Refusing a grant that contains protected path {protected}: {path}")
        if access == "rw":
            for target, target_chain in self.self_chains:
                if own in target_chain:
                    raise PolicyError(f"Refusing write access over the launcher's own state ({target}): {path}")


def build_policy(
    workspace: str | os.PathLike[str],
    *,
    homes: Sequence[str] | None = None,
    read: Iterable[str] = (),
    write: Iterable[str] = (),
    runtime: Iterable[str] = (),
    preset: str | None = None,
    private_tmp: str | None = None,
    self_paths: Sequence[str] = (),
    system: bool = True,
) -> Policy:
    """Build and check a policy. User grants that fail a guard raise ``PolicyError``."""
    homes = tuple(os.path.abspath(h) for h in (homes or default_homes()))
    protected = tuple(dict.fromkeys(_expand(f"~/{rel}", home) for home in homes for rel in PROTECTED_RELATIVE))
    guard = _Guard(homes, protected, self_paths)
    grants: dict[str, Grant] = {}
    skipped: list[str] = []

    def add(path: str, access: str, origin: str, *, strict: bool) -> None:
        path = os.path.abspath(path)
        try:
            st = os.lstat(path)
        except FileNotFoundError:
            if strict:
                raise PolicyError(f"Grant does not exist: {path}") from None
            skipped.append(path)
            return
        if stat.S_ISLNK(st.st_mode):
            if strict:
                raise PolicyError(f"Refusing a symbolic link as a grant; pass its target: {path}")
            skipped.append(path)
            return
        chain = ancestry(path)
        try:
            guard.check(path, access, chain)
        except PolicyError as exc:
            if strict:
                raise
            skipped.append(f"{path}: {exc}")
            return
        previous = grants.get(path)
        if previous and previous.access == "rw":
            return
        grants[path] = Grant(path, access, chain[0][0], chain[0][1], stat.S_ISDIR(st.st_mode), origin)

    workspace_path = os.path.abspath(workspace)
    add(workspace_path, "rw", "workspace", strict=True)
    if system:
        for path in SYSTEM_READ_EXEC:
            add(path, "ro", "system", strict=False)
        for path in DEVICE_FILES + DEVICE_DIRS:
            add(path, "dev", "system", strict=False)
        if not any(_contains("/tmp", home) for home in homes):
            add("/tmp", "rw", "tmp", strict=False)
        add("/dev/shm", "rw", "tmp", strict=False)
    if private_tmp:
        add(private_tmp, "rw", "tmp", strict=True)
    for path in runtime:
        add(path, "ro", "runtime", strict=False)
    if preset:
        if preset not in PRESETS:
            raise PolicyError(f"Unknown preset {preset!r}; expected one of {sorted(PRESETS)}")
        for home in homes[:1]:
            for path in PRESETS[preset]["read"]:
                add(_expand(path, home), "ro", f"preset:{preset}", strict=False)
            for path in PRESETS[preset]["write"]:
                add(_expand(path, home), "rw", f"preset:{preset}", strict=False)
    for path in read:
        add(_expand(path, homes[0]), "ro", "user", strict=True)
    for path in write:
        add(_expand(path, homes[0]), "rw", "user", strict=True)
    return Policy(workspace_path, homes, protected, tuple(grants.values()), tuple(skipped))


def _contains(parent: str, child: str) -> bool:
    """Physical containment (``parent`` is ``child`` or one of its ancestors)."""
    try:
        parent_id = ancestry(parent)[0]
        return parent_id in ancestry(child)
    except FileNotFoundError:
        return False
