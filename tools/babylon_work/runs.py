"""Durable jobs; model outputs cannot grant execution authority."""

from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone

from tools.babylon_work.workspace import Workspace, WorkspaceError, text

ACTIVE = ("queued", "running", "authorizing")


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Runs:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        with closing(workspace.connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS work_runs (
                    id TEXT PRIMARY KEY, task_id TEXT NOT NULL REFERENCES tasks(id),
                    revision INTEGER NOT NULL, kind TEXT NOT NULL, state TEXT NOT NULL,
                    request TEXT NOT NULL, result TEXT NOT NULL DEFAULT '{}',
                    detail TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS work_one_active_task ON work_runs(task_id)
                    WHERE state IN ('queued', 'running', 'authorizing');
            """)

    def recover(self) -> None:
        with closing(self.workspace.connect()) as db, db:
            db.execute("UPDATE work_runs SET state='interrupted', detail=?, updated_at=? "
                       "WHERE state IN ('queued','running','authorizing','awaiting_approval')",
                       ("Servidor reiniciado: resultado no confirmado; no se ha reintentado el trabajo.", now()))

    @staticmethod
    def decode(row) -> dict:
        result = dict(row)
        result["request"] = json.loads(result["request"])
        result["result"] = json.loads(result["result"])
        return result

    def get(self, run_id: str) -> dict:
        with closing(self.workspace.connect()) as db:
            row = db.execute("SELECT * FROM work_runs WHERE id=?", (run_id,)).fetchone()
            if row is None:
                raise WorkspaceError("No se encuentra el trabajo.", 404)
            return self.decode(row)

    def for_task(self, task_id: str) -> list[dict]:
        with closing(self.workspace.connect()) as db:
            return [self.decode(row) for row in db.execute(
                "SELECT * FROM work_runs WHERE task_id=? ORDER BY created_at DESC LIMIT 30", (task_id,))]

    def create(self, task_id: str, revision: object, kind: str, request: dict) -> dict:
        run_id, timestamp = uuid.uuid4().hex, now()
        try:
            with closing(self.workspace.connect()) as db, db:
                db.execute("BEGIN IMMEDIATE")
                task = db.execute("SELECT revision,status FROM tasks WHERE id=?", (task_id,)).fetchone()
                if task is None:
                    raise WorkspaceError("No se encuentra el encargo.", 404)
                if type(revision) is not int or revision != task["revision"]:
                    raise WorkspaceError("El encargo ha cambiado. Recarga antes de iniciar un trabajo.", 409)
                if task["status"] == "completed":
                    raise WorkspaceError("Reabre el encargo antes de iniciar otro trabajo.", 409)
                if db.execute("SELECT count(*) FROM work_runs").fetchone()[0] >= 500:
                    raise WorkspaceError("Límite de 500 trabajos alcanzado; conserva o archiva este espacio.", 409)
                db.execute("INSERT INTO work_runs(id,task_id,revision,kind,state,request,created_at,updated_at) "
                           "VALUES(?,?,?,?,?,?,?,?)", (run_id, task_id, revision, kind, "queued",
                           json.dumps(request), timestamp, timestamp))
                self.workspace.event(db, task_id, "run_created", "Trabajo creado: " + kind, timestamp)
        except sqlite3.IntegrityError as exc:
            raise WorkspaceError("Este encargo ya tiene un trabajo en curso.", 409) from exc
        return self.get(run_id)

    def move(self, run_id: str, state: str, detail: str, result: dict | None = None,
             *, expected: tuple[str, ...] | None = None) -> dict:
        with closing(self.workspace.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT state,task_id FROM work_runs WHERE id=?", (run_id,)).fetchone()
            if row is None or (expected is not None and row["state"] not in expected):
                raise WorkspaceError("El trabajo ya no admite esta acción.", 409)
            timestamp = now()
            db.execute("UPDATE work_runs SET state=?,detail=?,result=?,updated_at=? WHERE id=?",
                       (state, detail, json.dumps(result or {}), timestamp, run_id))
            self.workspace.event(db, row["task_id"], "run_" + state, detail, timestamp)
        return self.get(run_id)

    def complete_generation(self, run_id: str, document: str, sources: list[dict], metadata: dict) -> None:
        text(document, "document", 100_000)
        with closing(self.workspace.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            run = db.execute("SELECT * FROM work_runs WHERE id=?", (run_id,)).fetchone()
            if run is None or run["state"] != "running":
                raise WorkspaceError("El trabajo ya no está en ejecución.", 409)
            task = db.execute("SELECT revision,status FROM tasks WHERE id=?", (run["task_id"],)).fetchone()
            state = "succeeded"
            detail = "Documento generado por " + metadata["model"] + "; revisión pendiente."
            if not metadata["complete"]:
                state, detail = "incomplete", "El proveedor ha entregado un resultado parcial. El borrador anterior se conserva."
            elif metadata.get("warnings"):
                state, detail = "needs_review", "Hay instrucciones de instalación sin respaldo literal en los extractos. El resultado se conserva para revisión."
            elif task["revision"] != run["revision"] or task["status"] == "completed":
                state, detail = "conflict", "El encargo cambió durante la inferencia. El resultado se conserva sin sobrescribir tu documento."
            else:
                db.execute("UPDATE tasks SET document=?,sources=?,status='review',revision=revision+1,updated_at=? WHERE id=?",
                           (document, json.dumps(sources), now(), run["task_id"]))
            result = {"document": document, "sources": sources, **metadata}
            db.execute("UPDATE work_runs SET state=?,detail=?,result=?,updated_at=? WHERE id=?",
                       (state, detail, json.dumps(result), now(), run_id))
            self.workspace.event(db, run["task_id"], "generation_" + state, detail, now())

    def public(self, run: dict) -> dict:
        # Requests contain only user context, fixed commands and approval envelopes; never credentials.
        result = {key: run[key] for key in ("id", "task_id", "revision", "kind", "state", "detail", "result",
                                           "created_at", "updated_at")}
        if run["kind"] == "checks" and "approval_task" in run["request"]:
            result["approval_task"] = run["request"]["approval_task"]
            result["command"] = run["request"]["arguments"]["argv"]
        elif run["kind"] == "generation":
            result["model"] = run["request"]["model"]
            result["provider"] = run["request"]["provider"]
        return result
