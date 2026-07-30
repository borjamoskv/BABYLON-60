# C5-REAL EXERGY CERTIFIED
import os
import sys
import json
import signal
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

# -----------------------------------------------------------------------------
# CORTEX PERSIST OMEGA (C5-REAL)
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


class CortexOntologyLedger:
    """Motor estricto para el volcado de memoria de MOSKV-1 hacia la ontología global."""

    def __init__(self, project_id: str) -> None:
        self.project_id = project_id

        # Rutas físicas inmutables
        self.base_dir = str(Path.home() / ".agent/memory")
        self.projects_dir = os.path.join(self.base_dir, "projects")
        self.ghosts_file = os.path.join(self.base_dir, "ghosts.json")
        self.system_file = os.path.join(self.base_dir, "system.json")
        self.snapshots_dir = os.path.join(self.base_dir, "snapshots")

        self._verify_topology()

    def _verify_topology(self) -> None:
        """Falsación de existencia de rutas (Regla Ω22)."""
        paths = [self.projects_dir, self.snapshots_dir, self.ghosts_file, self.system_file]
        for p in paths:
            if not os.path.exists(p):
                print(f"[-] FATAL: Ontological path missing: {p}")
                os.kill(os.getpid(), signal.SIGKILL)
                raise RuntimeError("FAIL-FAST: Topología de memoria CORTEX ausente.")

    def _get_iso_now(self) -> str:
        # Formato ISO con timezone de Madrid/Bilbao (+02:00 por simplicidad estival)
        # Nota: La manipulación de timezones aquí asume el entorno CORTEX estándar.
        dt = datetime.now(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S+02:00")

    def _read_json(self, path: str) -> Dict[str, Any]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return dict(json.load(f))
        except (json.JSONDecodeError, OSError):
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError(f"FAIL-FAST: Corrupción en vector de memoria {path}")

    def _write_json(self, path: str, data: Dict[str, Any]) -> None:
        try:
            payload = json.dumps(data, indent=2, ensure_ascii=False)
            # Doble validación antes de mutar el disco
            json.loads(payload)
            with open(path, "w", encoding="utf-8") as f:
                f.write(payload)
        except (json.JSONDecodeError, OSError):
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError(f"FAIL-FAST: Fallo de cristalización en {path}")

    def crystallize_session(self, delta: SessionDelta) -> None:
        """Acopla la sesión actual a los tres pilares de memoria: Project, Ghost, System."""
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
                "mood": f"C5-REAL Automatic Snapshot | {delta.task_desc[:30]}...",
            }
        )
        self._write_json(self.ghosts_file, ghosts_data)

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

        print(f"[+] CORTEX PERSIST: Ontología cristalizada con éxito para {self.project_id}")


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
