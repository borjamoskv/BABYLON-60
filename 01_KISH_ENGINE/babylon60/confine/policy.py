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

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, field
import os
import pwd
import stat

from babylon60.confine import aliases
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
# /dev/tty is always the caller's own controlling terminal. Opening /dev/ptmx only
# allocates a new pseudo-terminal pair whose slave lives in /dev/pts: openpty(),
# forkpty() and posix_openpt()+ptsname() fail with EACCES without PTY_DIRS. A session
# leader can still make that new slave its controlling terminal and open it as
# /dev/tty: a terminal of its own, never an existing one.
DEVICE_FILES = ("/dev/null", "/dev/zero", "/dev/full", "/dev/random", "/dev/urandom", "/dev/tty", "/dev/ptmx")
# Every pseudo-terminal slave of the user, other tabs and windows included: granted only
# with ``allow_ptys``. The session's own terminals are granted one by one (``ttys``).
PTY_DIRS = ("/dev/pts",)
PTYS_WARNING = "allow_ptys: every terminal of this user, other tabs and windows included, is readable and writable"
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
    ".config/hub",
    ".config/op",
    ".config/git/credentials",
    ".config/containers/auth.json",
    ".npmrc",
    ".pypirc",
    ".cargo/credentials",
    ".cargo/credentials.toml",
    ".vault-token",
    ".terraform.d/credentials.tfrc.json",
    ".local/share/keyrings",
    "Library/Keychains",
)
# Sticky and writable by everyone (/tmp, /var/tmp): other programs of the user keep sockets,
# credential caches and private directories there. Never the workspace or a user grant.
SHARED_DIR_BITS = stat.S_ISVTX | stat.S_IWOTH

# Agent presets grant only the agent's own state and common install prefixes. Every preset also
# grants the global git configuration read-only, file by file, and its hooks directory (gitconfig.py,
# origin "preset:<name>:git").
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
    origin: str  # "system", "workspace", "tmp", "preset:<name>", "preset:<name>:git", "user", "runtime"


@dataclass(frozen=True)
class Policy:
    workspace: str
    homes: tuple[str, ...]
    protected: tuple[str, ...]
    grants: tuple[Grant, ...]
    skipped: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    allow_ptys: bool = False
    links: tuple[str, ...] = field(default_factory=tuple)  # symbolic links to the command, readable (Seatbelt)

    def as_dict(self) -> dict[str, object]:
        return {
            "workspace": self.workspace,
            "homes": list(self.homes),
            "protected": list(self.protected),
            "grants": [asdict(grant) for grant in self.grants],
            "skipped": list(self.skipped),
            "warnings": list(self.warnings),
            "allow_ptys": self.allow_ptys,
            "links": list(self.links),
        }

    def digest(self) -> str:
        """Digest of paths and access only: inode numbers differ between machines."""
        portable = {
            "workspace": self.workspace,
            "protected": list(self.protected),
            "grants": sorted([grant.path, grant.access] for grant in self.grants),
            "allow_ptys": self.allow_ptys,
            "links": sorted(self.links),
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


def _absolute(path: str | os.PathLike[str]) -> str:
    """Absolute path without lexical normalization: the kernel resolves ``..`` after symbolic links."""
    text = os.fspath(path)
    return text if os.path.isabs(text) else os.path.join(os.getcwd(), text)


def ancestry(path: str | os.PathLike[str]) -> list[Identity]:
    """Identities of ``path`` and every physical ancestor up to ``/``."""
    if not hasattr(os, "O_PATH"):
        return _ancestry_by_stat(path)
    chain: list[Identity] = []
    fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
    try:
        if not stat.S_ISDIR(os.fstat(fd).st_mode):
            chain.append(_identity_of_fd(fd))
            parent_path = os.path.dirname(_absolute(path)) or "/"
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
    current = _absolute(path)
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
    """The account home, ``$HOME`` and, under ``sudo``, the home of the user who invoked it."""
    homes = [account_home()]
    env_home = os.environ.get("HOME")
    if env_home and os.path.abspath(env_home) not in homes:
        homes.append(os.path.abspath(env_home))
    sudo_user = os.environ.get("SUDO_USER")
    if sudo_user:
        try:
            sudo_home = pwd.getpwnam(sudo_user).pw_dir
        except (KeyError, ValueError, OSError):
            sudo_home = ""
        if sudo_home and os.path.abspath(sudo_home) not in homes:
            homes.append(os.path.abspath(sudo_home))
    return tuple(homes)


def _expand(path: str, home: str) -> str:
    if path == "~" or path.startswith("~/"):
        path = home + path[1:]
    return os.path.abspath(path)


def _future_ancestry(path: str) -> list[Identity]:
    """Ancestry of ``path`` or, while it does not exist yet, of the directory it would be created in.

    The longest existing prefix is resolved by the kernel, ``..`` and symbolic
    links included. The missing rest is applied to that chain the way
    ``mkdir -p`` lays it out: a name goes one level down into a directory still
    to be created and ``..`` climbs back up.
    """
    head, rest = path, []
    while True:
        try:
            chain = ancestry(head or ".")
            break
        except (FileNotFoundError, NotADirectoryError):
            parent, name = os.path.split(head)
            if parent == head:
                raise
            rest.append(name)
            head = parent
    if len(chain) > 1 and not stat.S_ISDIR(os.stat(head or ".").st_mode):
        # ``ancestry`` takes a file's directory lexically; resolve it as the kernel does, ``..`` included.
        chain = chain[:1] + ancestry(os.path.dirname(head) or ".")
    below = 0
    for name in reversed(rest):
        if name == "..":
            if below:
                below -= 1
            elif len(chain) > 1:
                chain = chain[1:]
        elif name not in ("", "."):
            below += 1
    return chain


class _Guard:
    """Identity checks for one policy. Findings that refuse nothing go to ``warnings``."""

    LINK_WARNINGS = 16  # protected files with outside links named one by one; the rest are counted

    def __init__(self, homes: Sequence[str], protected: Sequence[str], self_paths: Sequence[str]) -> None:
        self.warnings: list[str] = []
        self.home_ids: list[set[Identity]] = []  # ancestry of each home, home itself first
        for home in homes:
            try:
                self.home_ids.append(set(ancestry(home)))
            except FileNotFoundError:
                continue
        self.protected_ids: dict[Identity, str] = {}
        self.protected_parents: dict[Identity, list[Identity]] = {}
        self.protected_chains: list[tuple[str, list[Identity]]] = []
        for path in protected:
            try:
                chain = ancestry(path)
            except FileNotFoundError:
                continue
            self.protected_ids[chain[0]] = path
            self.protected_parents[chain[0]] = chain[1:2]
            self.protected_chains.append((path, chain))
        # Directories and regular files below a protected directory: a grant with one of these
        # identities is another name for protected content (a hardlink or a bind mount).
        self.members: dict[Identity, str] = {}
        self._scan_protected()
        # A self path that does not exist yet (the journal before its first use) is protected
        # through the directory it will be created in.
        self.self_chains: list[tuple[str, list[Identity]]] = [(path, _future_ancestry(path)) for path in self_paths]
        # Directories of the launcher's own code (its virtual environment, this package, the standard
        # library the trampoline imports before it confines itself): a write grant inside one could
        # change what the next session runs unconfined.
        self.self_dirs: list[tuple[str, Identity]] = []
        for path in self_paths:
            try:
                st = os.stat(path)
            except OSError:
                continue
            if stat.S_ISDIR(st.st_mode):
                self.self_dirs.append((path, (st.st_dev, st.st_ino)))

    def _scan_protected(self) -> None:
        visited: set[Identity] = set()
        links: dict[Identity, tuple[str, int, set[tuple[Identity, str]]]] = {}
        for path, chain in self.protected_chains:
            try:
                scan = aliases.scan_tree(path, visited=visited)
            except NotADirectoryError:
                if chain[0] in visited:  # the same file through another home
                    continue
                visited.add(chain[0])
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                if stat.S_ISREG(st.st_mode) and st.st_nlink > 1:
                    first, nlink, names = links.get(chain[0], (path, st.st_nlink, set()))
                    names.add((chain[1], os.path.basename(path)))
                    links[chain[0]] = (min(first, path), nlink, names)
                continue
            except FileNotFoundError:
                continue
            except OSError as exc:
                self.warnings.append(
                    f"{path} could not be listed ({exc.strerror}); hardlinks and bind mounts of its entries are not detected"
                )
                continue
            for ident, member in scan.entries.items():
                self.members.setdefault(ident, member)
            for item in scan.linked:
                first, nlink, names = links.get(item.ident, (item.path, item.nlink, set()))
                names.add(item.dentry)
                links[item.ident] = (min(first, item.path), nlink, names)
            if scan.stopped:
                self.warnings.append(
                    f"{path}: alias scan stopped at {scan.stopped}; hardlinks and bind mounts of entries beyond it are not detected"
                )
            if scan.errors:
                self.warnings.append(
                    f"{path}: {len(scan.errors)} directories below it could not be listed (first: {scan.errors[0]}); "
                    "hardlinks and bind mounts of their entries are not detected"
                )
        # A link count above the names found inside the protected paths means a name elsewhere.
        outside = sorted((path, nlink) for path, nlink, names in links.values() if len(names) < nlink)
        for path, nlink in outside[: self.LINK_WARNINGS]:
            self.warnings.append(f"{path} has {nlink} links; another path to it may be readable (declared limit L2)")
        if len(outside) > self.LINK_WARNINGS:
            self.warnings.append(
                f"{len(outside) - self.LINK_WARNINGS} more protected files have links outside the protected paths "
                "(declared limit L2)"
            )

    def check(self, path: str, access: str, chain: list[Identity]) -> None:
        own = chain[0]
        for ids in self.home_ids:
            if own in ids:
                raise PolicyError(f"Refusing to grant a home directory or one of its ancestors: {path}")
        for index, ident in enumerate(chain):
            if ident in self.protected_ids:
                if index == 0 and chain[1:2] != self.protected_parents[ident]:
                    raise PolicyError(f"Refusing an alias of protected {self.protected_ids[ident]}: {path}")
                raise PolicyError(f"Refusing a grant inside protected path {self.protected_ids[ident]}: {path}")
        for protected, protected_chain in self.protected_chains:
            if own in protected_chain:
                raise PolicyError(f"Refusing a grant that contains protected path {protected}: {path}")
        for index, ident in enumerate(chain):  # an ancestor also covers entries beyond the scan bounds
            if ident in self.members:
                if index == 0:
                    raise PolicyError(f"Refusing an alias of protected {self.members[ident]}: {path}")
                raise PolicyError(f"Refusing a grant inside an alias of protected {self.members[ident]}: {path}")
        if access == "rw":
            own_state = self._own_state(own)
            if own_state:
                raise PolicyError(f"Refusing write access over {own_state}: {path}")
            inside = next((target for target, ident in self.self_dirs if ident in chain[1:]), None)
            if inside is not None:
                raise PolicyError(f"Refusing write access inside the launcher's own state ({inside}): {path}")

    def _exposed(self, ident: Identity) -> str | None:
        """What a mount whose root has identity ``ident`` exposes, if ``check`` refuses it for every access."""
        if any(ident in ids for ids in self.home_ids):
            return "a home directory or one of its ancestors"
        if ident in self.protected_ids:
            return f"protected path {self.protected_ids[ident]}"
        for protected, protected_chain in self.protected_chains:
            if ident in protected_chain:
                return f"an ancestor of protected path {protected}"
        if ident in self.members:
            return f"protected {self.members[ident]}"
        return None

    def _own_state(self, ident: Identity) -> str | None:
        for target, target_chain in self.self_chains:
            if ident in target_chain:
                return f"the launcher's own state ({target})"
        return None

    def _inside_self(self, mount: aliases.Mount, root: Identity, mounts: Sequence[aliases.Mount]) -> str | None:
        """The launcher directory that the tree ``mount`` shows (its root has identity ``root``) lies inside.

        Below a mount point ``..`` leads to the mount point's parent, not to where the mounted tree
        comes from, so the identity walk of ``check`` cannot see that a bind mount of a directory of
        the launcher's own code sits in it. The mount table can: the source is the mount's root
        field below another mount of the same filesystem whose root holds it (``/`` usually). Where
        that path shows the same tree, its ancestry is checked as ``check`` checks a write grant.
        """
        if not self.self_dirs:
            return None
        for other in mounts:
            if other.mount_id == mount.mount_id or other.device != mount.device:
                continue
            rest = _below(mount.root, other.root)
            if rest is None:
                continue
            source = os.path.join(other.mount_point, rest) if rest else other.mount_point
            try:
                chain = ancestry(source)
            except (OSError, ValueError):
                continue
            if chain[0] != root:  # another tree is mounted over that path: not where this one comes from
                continue
            inside = next((target for target, ident in self.self_dirs if ident in chain[1:]), None)
            if inside is not None:
                return inside
        return None

    def mount_refusals(self, grants: Iterable[Grant]) -> dict[str, str]:
        """``{path: reason}`` for directory grants with a mount below them that ``check`` would refuse.

        Landlock follows the mount hierarchy of the path used, so a rule on a
        directory also covers every mount below it, wherever the mounted tree
        lives. A mount's root is judged as a grant with the directory's access
        would be: a home or an ancestor of one, a protected path, an ancestor of
        one or an entry below one, and for write access the launcher's own state
        or, found through the mount table, a path inside a directory of it.
        """
        directories: dict[Identity, list[Grant]] = {}
        for grant in grants:
            if grant.is_dir:
                directories.setdefault((grant.dev, grant.ino), []).append(grant)
        if not directories:
            return {}
        try:
            mounts = aliases.read_mountinfo()
        except (OSError, aliases.MountinfoError) as exc:
            self.warnings.append(f"Mount table unreadable ({exc}); mounts inside the grants were not checked")
            return {}
        refusals: dict[str, str] = {}
        for mount, containing, root in aliases.mounts_beneath(directories, mounts or (), ancestry):
            exposed = self._exposed(root)
            writable: str | None = None
            if not exposed and any(grant.access == "rw" for ident in containing for grant in directories[ident]):
                writable = self._own_state(root)
                if writable is None:
                    inside = self._inside_self(mount, root, mounts or ())
                    writable = f"a path inside the launcher's own state ({inside})" if inside else None
            for ident in containing:
                for grant in directories[ident]:
                    what = exposed or (writable if grant.access == "rw" else None)
                    if what and grant.path not in refusals:
                        refusals[grant.path] = (
                            f"Refusing a grant with a mount of {what} inside it ({mount.mount_point}): {grant.path}"
                        )
        return refusals


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
    ttys: Sequence[str] = (),
    allow_ptys: bool = False,
    links: Sequence[str] = (),
    git_env: Mapping[str, str] | None = None,
) -> Policy:
    """Build and check a policy. User grants that fail a guard raise ``PolicyError``.

    ``git_env``: ``HOME`` and ``XDG_CONFIG_HOME`` as git inside the sandbox sees them, for the
    git configuration a preset grants (the launcher passes its own environment, which the
    agent inherits); by default ``HOME`` is the first home.
    """
    homes = tuple(os.path.abspath(h) for h in (homes or default_homes()))
    protected = tuple(dict.fromkeys(_expand(f"~/{rel}", home) for home in homes for rel in PROTECTED_RELATIVE))
    guard = _Guard(homes, protected, self_paths)
    grants: dict[str, Grant] = {}
    skipped: list[str] = []
    warnings: list[str] = []

    def add(
        path: str,
        access: str,
        origin: str,
        *,
        strict: bool,
        accept: Callable[[str, os.stat_result, list[Identity]], bool] | None = None,
    ) -> bool:
        """Grant ``path`` when the guards and then ``accept`` allow it; whether it was granted."""
        path = os.path.abspath(path)
        try:
            st = os.lstat(path)
        except FileNotFoundError:
            if strict:
                raise PolicyError(f"Grant does not exist: {path}") from None
            skipped.append(path)
            return False
        if stat.S_ISLNK(st.st_mode):
            if strict:
                raise PolicyError(f"Refusing a symbolic link as a grant; pass its target: {path}")
            skipped.append(path)
            return False
        if (
            origin in ("workspace", "user")
            and stat.S_ISDIR(st.st_mode)
            and st.st_mode & SHARED_DIR_BITS == SHARED_DIR_BITS
        ):
            raise PolicyError(
                f"Refusing a shared directory that everyone can write to (sticky, like /tmp): {path}. Other programs "
                "keep sockets and credential caches there; use a directory of your own (each run gets a private TMPDIR)"
            )
        chain = ancestry(path)
        try:
            guard.check(path, access, chain)
        except PolicyError as exc:
            if strict:
                raise
            skipped.append(f"{path}: {exc}")
            return False
        if accept is not None and not accept(path, st, chain):
            return False
        previous = grants.get(path)
        if previous and previous.access == "rw":
            return True
        grants[path] = Grant(path, access, chain[0][0], chain[0][1], stat.S_ISDIR(st.st_mode), origin)
        return True

    workspace_path = os.path.abspath(workspace)
    add(workspace_path, "rw", "workspace", strict=True)
    if system:
        for path in SYSTEM_READ_EXEC:
            add(path, "ro", "system", strict=False)
        for path in DEVICE_FILES:
            add(path, "dev", "system", strict=False)
        # /tmp is shared with every program of the user (Kerberos caches, other tools'
        # files, socket directories): never granted; ``private_tmp`` is the temp dir.
        # /dev/shm stays: POSIX semaphores and shared memory (Python multiprocessing).
        add("/dev/shm", "rw", "tmp", strict=False)
    for path in ttys:
        path = os.path.abspath(path)
        try:
            st = os.lstat(path)
        except OSError:
            skipped.append(path)
            continue
        if not stat.S_ISCHR(st.st_mode) or not _contains("/dev", path):
            skipped.append(f"{path}: not a terminal device under /dev")
            continue
        add(path, "dev", "tty", strict=False)
    if allow_ptys:
        for path in PTY_DIRS:
            add(path, "dev", "ptys", strict=False)
        warnings.append(PTYS_WARNING)
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
    git_links: list[str] = []  # symbolic links git follows to its configuration, readable like links
    if preset:
        # Last, so a file another grant already covers gets no grant of its own, and includes named
        # by a file the agent can write are ignored.
        from babylon60.confine import gitconfig  # imports persistence, which imports this module

        gitconfig.grant_global_config(
            add,
            git_env if git_env is not None else {"HOME": homes[0]},
            grants.values(),
            protected=protected,
            origin=f"preset:{preset}:git",
            skipped=skipped,
            warnings=warnings,
            links=git_links,
        )
    # Post-pass: mounts below directory grants (bind mounts of protected paths or homes).
    refused = guard.mount_refusals(grants.values())
    strict_tmp = os.path.abspath(private_tmp) if private_tmp else None
    for grant in [g for g in grants.values() if g.path in refused]:
        if grant.origin in ("workspace", "user") or grant.path == strict_tmp:
            raise PolicyError(refused[grant.path])
        del grants[grant.path]
        skipped.append(f"{grant.path}: {refused[grant.path]}")
    warnings.extend(guard.warnings)
    # Symbolic links on the way to the command, and to the git configuration: Seatbelt checks following
    # a link as a read of the link itself (Landlock does not mediate it). Only the links are allowed,
    # never their directories.
    readable_links: list[str] = []
    for link in [*links, *git_links]:
        link = _absolute(link)
        try:
            if not stat.S_ISLNK(os.lstat(link).st_mode):
                skipped.append(f"{link}: not a symbolic link")
                continue
            parent = ancestry(os.path.dirname(link) or "/")
        except OSError:
            skipped.append(link)
            continue
        inside = next((guard.protected_ids[ident] for ident in parent if ident in guard.protected_ids), None)
        if inside is not None:
            skipped.append(f"{link}: Refusing a link inside protected path {inside}")
            continue
        readable_links.append(link)
    return Policy(
        workspace_path,
        homes,
        protected,
        tuple(grants.values()),
        tuple(skipped),
        tuple(warnings),
        allow_ptys,
        tuple(dict.fromkeys(readable_links)),
    )


def _below(path: str, base: str) -> str | None:
    """``path`` relative to ``base`` when ``base`` is ``path`` or a lexical ancestor of it, else None."""
    if base == "/":
        return path.lstrip("/")
    base = base.rstrip("/")
    if path == base:
        return ""
    return path[len(base) + 1 :] if path.startswith(base + "/") else None


def _contains(parent: str, child: str) -> bool:
    """Physical containment (``parent`` is ``child`` or one of its ancestors)."""
    try:
        parent_id = ancestry(parent)[0]
        return parent_id in ancestry(child)
    except FileNotFoundError:
        return False
