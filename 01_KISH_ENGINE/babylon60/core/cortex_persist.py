# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import sys
import json
import fcntl
import secrets
import stat
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterator, List

# -----------------------------------------------------------------------------
# CORTEX PERSIST OMEGA (Causal-Determinist)
# -----------------------------------------------------------------------------
# Transductor físico de consolidación de memoria.
# Enlaza el estado local BFT con la topología global de memoria de MOSKV-1.
# -----------------------------------------------------------------------------


@dataclass
class SessionDelta:
    task_desc: str
    last_file: str
    conversation_id: str
    changes: List[str]
    decisions: List[str]
    duration: str = "1h"


class PersistenceWriteError(RuntimeError):
    """A failed file update; replacement visibility is separate from durability."""

    def __init__(self, path: str, replacement_state: str) -> None:
        super().__init__(f"JSON write failed for {Path(path).name}; replacement={replacement_state}")
        self.path = path
        self.replacement_state = replacement_state
        self.replaced = replacement_state == "REPLACED"
        self.durability_confirmed = False


class ConsolidationError(RuntimeError):
    """Completed files are retained; the three files are not one transaction."""

    def __init__(self, completed_files: List[str], cause: BaseException) -> None:
        super().__init__(f"CORTEX consolidation incomplete; completed files={len(completed_files)}")
        self.completed_files = tuple(completed_files)
        self.current_file = cause.path if isinstance(cause, PersistenceWriteError) else None
        self.replacement_state = cause.replacement_state if isinstance(cause, PersistenceWriteError) else "NOT_ATTEMPTED"


class CortexOntologyLedger:
    """Motor estricto para el volcado de memoria de MOSKV-1 hacia la ontología global."""

    def __init__(self, project_id: str) -> None:
        if (not isinstance(project_id, str) or not project_id or len(project_id) > 128
                or project_id in (".", "..") or any(char in '/\\:' or ord(char) < 32 for char in project_id)):
            raise ValueError("Project ID must be a single filename component")
        self.project_id = project_id
        self._project_id = project_id
        self._home = Path.home().absolute()
        self._base = self._home / ".agent" / "memory"
        self._operation = threading.local()

        # Rutas físicas inmutables
        self.base_dir = str(self._base)
        self.projects_dir = os.path.join(self.base_dir, "projects")
        self.ghosts_file = os.path.join(self.base_dir, "ghosts.json")
        self.system_file = os.path.join(self.base_dir, "system.json")
        self.snapshots_dir = os.path.join(self.base_dir, "snapshots")

        self._verify_topology()

    def _check_paths(self) -> None:
        expected = ((self.base_dir, self._base), (self.projects_dir, self._base/"projects"),
                    (self.snapshots_dir, self._base/"snapshots"), (self.ghosts_file, self._base/"ghosts.json"),
                    (self.system_file, self._base/"system.json"))
        if self.project_id != self._project_id or any(Path(value).absolute() != path for value, path in expected):
            raise ValueError("CORTEX memory paths changed after construction")

    @contextmanager
    def _base_handle(self) -> Iterator[int]:
        self._check_paths()
        descriptors: List[int] = []
        try:
            flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
            descriptors.append(os.open(self._home, flags))
            for name in (".agent", "memory"):
                descriptors.append(os.open(name, flags, dir_fd=descriptors[-1]))
            active = getattr(self._operation, "active", None)
            if active is not None and not os.path.samestat(os.fstat(active[0]), os.fstat(descriptors[-1])):
                raise RuntimeError("CORTEX memory directory identity changed during operation")
            yield descriptors[-1]
        finally:
            for descriptor in reversed(descriptors):
                os.close(descriptor)

    @staticmethod
    def _regular_file(descriptor: int) -> os.stat_result:
        value = os.fstat(descriptor)
        if not stat.S_ISREG(value.st_mode) or value.st_nlink != 1 or value.st_uid != os.getuid():
            raise RuntimeError("CORTEX requires owned, single-link regular files")
        return value

    @contextmanager
    def _parent_handle(self, path: str) -> Iterator[tuple[int, str]]:
        self._check_paths()
        selected = Path(path).absolute()
        if selected == self._base/"projects"/(self.project_id+".json"):
            folder, name = "projects", self.project_id+".json"
        elif selected in (self._base/"ghosts.json", self._base/"system.json"):
            folder, name = "", selected.name
        else:
            raise ValueError("JSON destination is outside this ledger's memory files")
        with self._base_handle() as base:
            if not folder:
                yield base, name
            else:
                descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=base)
                try:
                    yield descriptor, name
                finally:
                    os.close(descriptor)

    def _verify_topology(self) -> None:
        with self._base_handle() as base:
            for name in ("projects", "snapshots"):
                descriptor = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=base)
                os.close(descriptor)
            for name in ("ghosts.json", "system.json"):
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=base)
                try:
                    self._regular_file(descriptor)
                finally:
                    os.close(descriptor)

    def _check_operation_lock(self) -> None:
        active = getattr(self._operation, "active", None)
        if active is not None:
            with self._base_handle():
                pass
            base, descriptor = active
            current = os.stat(".cortex-persist.lock", dir_fd=base, follow_symlinks=False)
            if not os.path.samestat(self._regular_file(descriptor), current):
                raise RuntimeError("CORTEX operation lock identity changed")

    @contextmanager
    def _exclusive_session(self) -> Iterator[None]:
        if getattr(self._operation, "active", None) is not None:
            raise RuntimeError("Nested CORTEX consolidation is unsupported")
        with self._base_handle() as base:
            descriptor = os.open(".cortex-persist.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK,
                                 0o600, dir_fd=base)
            try:
                self._regular_file(descriptor)
                fcntl.flock(descriptor, fcntl.LOCK_EX)
                self._operation.active = (base, descriptor)
                try:
                    self._check_operation_lock()
                    yield
                finally:
                    self._operation.active = None
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
            finally:
                os.close(descriptor)

    def _get_iso_now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _read_json(self, path: str) -> Dict[str, Any]:
        self._check_operation_lock()
        try:
            with self._parent_handle(path) as (parent, name):
                descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
                    self._regular_file(stream.fileno())
                    value = json.load(stream, parse_constant=self._invalid_constant)
                    if not isinstance(value, dict):
                        raise ValueError("JSON memory must contain an object")
                    return value
        except (ValueError, OSError) as error:
            raise RuntimeError(f"CORTEX JSON read failed for {Path(path).name}") from error

    @staticmethod
    def _invalid_constant(value: str) -> None:
        raise ValueError("Non-finite JSON constants are unsupported")

    @staticmethod
    def _write_all(descriptor: int, payload: bytes) -> None:
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0 or written > len(payload) - offset:
                raise OSError("Incomplete JSON temporary write")
            offset += written

    @staticmethod
    def _observe_replacement(
        parent: int, name: str, staged: os.stat_result, before: os.stat_result
    ) -> str:
        try:
            observed = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if os.path.samestat(staged, observed):
                return "REPLACED"
            elif os.path.samestat(before, observed):
                return "NOT_REPLACED"
        except OSError:
            pass
        return "UNKNOWN"

    @staticmethod
    def _discard_temporary(
        parent: int,
        temporary: str,
        descriptor: int,
        active_failure: BaseException | None,
    ) -> None:
        try:
            try:
                current = os.stat(temporary, dir_fd=parent, follow_symlinks=False)
                if os.path.samestat(os.fstat(descriptor), current):
                    os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass
            except OSError as cleanup_error:
                if active_failure is not None:
                    active_failure.add_note(
                        f"Temporary cleanup error: {type(cleanup_error).__name__}"
                    )
                else:
                    raise
        finally:
            os.close(descriptor)

    def _write_json(self, path: str, data: Dict[str, Any]) -> None:
        """Atomic replacement per file, not a read/modify/write lock for direct callers."""
        if not isinstance(data, dict):
            raise ValueError("JSON memory must contain an object")
        payload = json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False).encode("utf-8")
        json.loads(payload)
        self._check_operation_lock()
        replacement_state = "NOT_ATTEMPTED"
        try:
            with self._parent_handle(path) as (parent, name):
                target = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
                try:
                    before = self._regular_file(target)
                finally:
                    os.close(target)
                if not before.st_mode & stat.S_IWUSR:
                    raise PermissionError("JSON destination is read-only")
                temporary = ".cortex-persist-"+secrets.token_hex(16)+".tmp"
                descriptor = os.open(temporary, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                                     0o600, dir_fd=parent)
                try:
                    self._write_all(descriptor, payload)
                    os.fchmod(descriptor, stat.S_IMODE(before.st_mode) & 0o777)
                    os.fsync(descriptor)
                    staged = self._regular_file(descriptor)
                    current = os.stat(name, dir_fd=parent, follow_symlinks=False)
                    if not os.path.samestat(before, current) or (before.st_mode, before.st_uid, before.st_nlink, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (current.st_mode, current.st_uid, current.st_nlink, current.st_size, current.st_mtime_ns, current.st_ctime_ns):
                        raise RuntimeError("JSON destination changed during write")
                    if not os.path.samestat(staged, os.stat(temporary, dir_fd=parent, follow_symlinks=False)):
                        raise RuntimeError("JSON temporary identity changed")
                    self._check_operation_lock()
                    replacement_state = "UNKNOWN"
                    try:
                        os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
                    except OSError:
                        replacement_state = self._observe_replacement(parent, name, staged, before)
                        raise
                    replacement_state = "REPLACED"
                    os.fsync(parent)
                finally:
                    self._discard_temporary(parent, temporary, descriptor, sys.exception())
        except (OSError, RuntimeError, ValueError) as error:
            raise PersistenceWriteError(path, replacement_state) from error

    def crystallize_session(self, delta: SessionDelta) -> None:
        """Serialize cooperating sessions; individual files remain separate commits."""
        completed: List[str] = []
        try:
            with self._exclusive_session():
                self._crystallize_locked(delta, completed)
        except (OSError, RuntimeError, ValueError, TypeError, AttributeError) as error:
            raise ConsolidationError(completed, error) from error
        print(f"[+] CORTEX PERSIST: Ontología cristalizada con success para {self.project_id}")

    def _crystallize_locked(self, delta: SessionDelta, completed: List[str]) -> None:
        now = self._get_iso_now()

        # 1. Mutar Project Ledger
        proj_file = os.path.join(self.projects_dir, f"{self.project_id}.json")
        proj_data = self._read_json(proj_file)

        if "meta" not in proj_data:
            proj_data["meta"] = {}
        proj_data["meta"]["last_touched"] = now

        proj_data["ghost"] = {
            "last_task": delta.task_desc,
            "last_file": delta.last_file,
            "last_conversation": delta.conversation_id,
            "timestamp": now,
        }

        recent = list(proj_data.get("recent_changes", []))
        for ch in reversed(delta.changes):
            # Anti-Sybil check
            if not any(isinstance(r, dict) and r.get("desc") == ch for r in recent[:5]):
                recent.insert(0, {"ts": now, "desc": ch})
        proj_data["recent_changes"] = recent[:10]

        decisions = list(proj_data.get("decisions", []))
        for d in delta.decisions:
            if not any(isinstance(r, dict) and r.get("decision") == d for r in decisions[-5:]):
                decisions.append({"ts": now, "decision": d})
        proj_data["decisions"] = decisions

        self._write_json(proj_file, proj_data)
        completed.append(proj_file)

        # 2. Mutar Ghosts
        ghosts_data = self._read_json(self.ghosts_file)
        if self.project_id not in ghosts_data:
            ghosts_data[self.project_id] = {}

        ghosts_data[self.project_id].update(
            {
                "last_task": delta.task_desc,
                "last_file": delta.last_file,
                "last_conversation": delta.conversation_id,
                "timestamp": now,
                "mood": f"Causal-Determinist Automatic Snapshot | {delta.task_desc[:30]}...",
            }
        )
        self._write_json(self.ghosts_file, ghosts_data)
        completed.append(self.ghosts_file)

        # 3. Mutar System
        system_data = self._read_json(self.system_file)
        sessions: List[Dict[str, Any]] = list(system_data.get("sessions_log", []))

        if sessions and sessions[0].get("conversation_id") == delta.conversation_id:
            sessions.pop(0)

        sessions.insert(
            0,
            {
                "date": now,
                "project": self.project_id,
                "focus": delta.task_desc,
                "duration_approx": delta.duration,
                "key_output": delta.last_file,
                "conversation_id": delta.conversation_id,
            },
        )

        system_data["sessions_log"] = sessions[:30]
        if "meta" not in system_data:
            system_data["meta"] = {}
        system_data["meta"]["last_updated"] = now
        system_data["last_updated"] = now
        self._write_json(self.system_file, system_data)
        completed.append(self.system_file)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python3 cortex_persist.py <PROJECT_ID> <CONVERSATION_ID>")
        sys.exit(1)

    pid = sys.argv[1]
    cid = sys.argv[2] if len(sys.argv) > 2 else "CLI-FALLBACK"

    delta = SessionDelta(
        task_desc="Manual CORTEX Persist trigger via CLI",
        last_file="babylon60/core/cortex_persist.py",
        conversation_id=cid,
        changes=["Forced synchronization of BFT state"],
        decisions=["CORTEX memory boundary manual check"],
    )

    ledger = CortexOntologyLedger(pid)
    ledger.crystallize_session(delta)
