"""Durable draft workspace; never dispatches agent or operating-system effects."""

from __future__ import annotations

import json
import os
import re
import sqlite3
import stat
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

from blake3 import blake3

from babylon60.database.core import connect_sync

ROOT = Path(__file__).absolute().parents[2]
SOURCES = {
    "overview": ("Presentación de Babylon", "README.md"),
    "architecture": ("Arquitectura y límites", "docs/01_spec/spec_architecture.md"),
    "security": ("Modelo de seguridad", "docs/01_spec/spec_security_model.md"),
    "workflow": ("Trabajo con agentes", "docs/03_guides/guide_agent_workflow.md"),
}
KINDS = {"document": "Documentación", "review": "Revisión técnica", "research": "Investigación"}
STATUS = {"draft", "active", "paused", "review", "completed"}
MAX_DOCUMENT = 100_000


class WorkspaceError(ValueError):
    """An actionable validation, conflict, or scope error."""

    def __init__(self, message: str, status: int = 400):
        super().__init__(message)
        self.status = status


def text(value: object, field: str, limit: int, *, required: bool = True) -> str:
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise WorkspaceError(f"Revisa {field}: texto {'obligatorio, ' if required else ''}máximo {limit} caracteres.")
    return value.strip() if field != "document" else value


def read_source(source_id: str) -> dict:
    if source_id not in SOURCES:
        raise WorkspaceError("Fuente fuera del catálogo autorizado.", 404)
    label, relative = SOURCES[source_id]
    # Resolve every component through descriptors; reject symlinks at every level.
    directory = os.open(ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        components = Path(relative).parts
        for component in components[:-1]:
            next_directory = os.open(
                component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory
            )
            os.close(directory)
            directory = next_directory
        fd = os.open(components[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
        with os.fdopen(fd, "rb") as source:
            if not stat.S_ISREG(os.fstat(source.fileno()).st_mode):
                raise WorkspaceError("La fuente no es un archivo regular.")
            data = source.read(262_145)
            if len(data) > 262_144:
                raise WorkspaceError("La fuente supera el límite de lectura.")
    except OSError as exc:
        raise WorkspaceError("No se puede leer esta fuente con el alcance actual.", 409) from exc
    finally:
        os.close(directory)
    return {"id": source_id, "label": label, "path": relative, "digest": blake3(data).hexdigest(),
            "content": data.decode("utf-8"), "bytes": len(data)}


def source_catalog() -> list[dict]:
    return [{"id": key, "label": label, "path": path} for key, (label, path) in SOURCES.items()]


def prepare_document(task: dict) -> tuple[str, list[dict]]:
    """Assemble a source-backed brief without pretending to run an LLM or tests."""
    selected = {"document": ["overview", "workflow"], "review": ["security", "architecture"],
                "research": ["architecture", "overview"]}[task["kind"]]
    sources = [read_source(key) for key in selected]
    lines = [f"# {task['title']}", "", "## Objetivo", "", task["prompt"], "",
             "## Punto de partida", "",
             "Borrador preparado localmente a partir de archivos de BABYLON-60. "
             "La selección de extractos es determinista; no se ha invocado un modelo de IA.", ""]
    for source in sources:
        lines += [f"## {source['label']}", "", f"Fuente: {source['path']}", ""]
        paragraphs = source["content"].split("\n\n")
        excerpts = [re.sub(r"(?m)^> ?", "", p.strip()) for p in paragraphs if len(p.strip()) > 100
                    and not p.lstrip().startswith(("```", "[", "![", "<", "|", "$$", "---", "#"))]
        for excerpt in excerpts[:2]:
            lines += ["\n".join("> " + row for row in excerpt[:1200].splitlines()), ""]
    lines += ["## Decisiones del proyecto", ""]
    lines += [f"- {item}" for item in task["decisions"]] or ["- Pendiente de revisión humana."]
    lines += ["", "## Comprobaciones pendientes", "",
              "- Contrastar los extractos con el objetivo del encargo.",
              "- Completar y revisar el documento antes de marcarlo como terminado.",
              "- Las pruebas del runtime, la inferencia y la ejecución protegida no se han ejecutado.",
              "", "## Fuentes del borrador", ""]
    lines += [f"- {s['path']} · BLAKE3 {s['digest']}" for s in sources]
    return "\n".join(lines) + "\n", [{k: s[k] for k in ("id", "label", "path", "digest")} for s in sources]


class Workspace:
    def __init__(self, path: Path):
        self.path = path.absolute()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, prompt TEXT NOT NULL,
                    kind TEXT NOT NULL, status TEXT NOT NULL, document TEXT NOT NULL DEFAULT '',
                    decisions TEXT NOT NULL DEFAULT '[]', sources TEXT NOT NULL DEFAULT '[]',
                    revision INTEGER NOT NULL DEFAULT 1, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS events (
                    seq INTEGER PRIMARY KEY AUTOINCREMENT, task_id TEXT NOT NULL REFERENCES tasks(id),
                    action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def connect(self) -> sqlite3.Connection:
        db = connect_sync(self.path, synchronous="FULL")
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def decode(row: sqlite3.Row) -> dict:
        task = dict(row)
        for key in ("decisions", "sources"):
            task[key] = json.loads(task[key])
        return task

    def list(self) -> list[dict]:
        with closing(self.connect()) as db:
            return [self.decode(row) for row in db.execute("SELECT * FROM tasks ORDER BY updated_at DESC, id")]

    def get(self, task_id: str) -> dict:
        with closing(self.connect()) as db:
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                raise WorkspaceError("No se encuentra el encargo.", 404)
            task = self.decode(row)
            task["events"] = [dict(event) for event in db.execute(
                "SELECT seq, action, detail, created_at FROM events WHERE task_id=? ORDER BY seq DESC LIMIT 100",
                (task_id,))]
            return task

    @staticmethod
    def event(db: sqlite3.Connection, task_id: str, action: str, detail: str, now: str) -> None:
        db.execute("INSERT INTO events(task_id,action,detail,created_at) VALUES(?,?,?,?)",
                   (task_id, action, detail, now))

    def create(self, body: dict) -> dict:
        title = text(body.get("title"), "título", 160)
        prompt = text(body.get("prompt"), "objetivo", 6000)
        kind = body.get("kind", "document")
        if not isinstance(kind, str) or kind not in KINDS:
            raise WorkspaceError("Tipo de encargo desconocido.")
        task_id, now = uuid.uuid4().hex, datetime.now(timezone.utc).isoformat()
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT INTO tasks(id,title,prompt,kind,status,updated_at) VALUES(?,?,?,?,?,?)",
                       (task_id, title, prompt, kind, "draft", now))
            self.event(db, task_id, "created", "Encargo creado; pendiente de preparar.", now)
        return self.get(task_id)

    def update(self, task_id: str, body: dict) -> dict:
        action = body.get("action")
        if action not in ("prepare", "save", "pause", "resume", "complete", "decision", "reopen"):
            raise WorkspaceError("Acción no disponible en este prototipo.")
        with closing(self.connect()) as db, db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if row is None:
                raise WorkspaceError("No se encuentra el encargo.", 404)
            task = self.decode(row)
            if type(body.get("revision")) is not int or body["revision"] != task["revision"]:
                raise WorkspaceError("El encargo ha cambiado en otra ventana. Recarga antes de guardar.", 409)
            status = task["status"]
            if status == "completed" and action != "reopen":
                raise WorkspaceError("Reabre el encargo antes de modificarlo.", 409)
            if action == "prepare":
                if task["document"].strip():
                    raise WorkspaceError("Ya existe un borrador. Puedes editarlo sin sobrescribirlo.", 409)
                task["document"], task["sources"] = prepare_document(task)
                task["status"] = "review"
                detail = "Borrador compuesto con fuentes locales. Revisión humana pendiente; sin inferencia."
            elif action == "save":
                task["document"] = text(body.get("document"), "document", MAX_DOCUMENT, required=False)
                task["status"] = "review" if task["document"].strip() else "draft"
                detail = "Documento guardado en el espacio local."
            elif action == "decision":
                if len(task["decisions"]) >= 100:
                    raise WorkspaceError("Este encargo admite hasta 100 decisiones.")
                task["decisions"].append(text(body.get("decision"), "decisión", 2000))
                detail = "Decisión añadida al contexto del encargo."
            elif action == "complete":
                if not task["document"].strip() or body.get("reviewed") is not True:
                    raise WorkspaceError("Guarda un documento y confirma su revisión antes de terminar.")
                task["status"] = "completed"
                detail = "Revisión humana confirmada; encargo terminado. No certifica el runtime."
            else:
                transitions = {"pause": ("paused", {"draft", "active", "review"}),
                               "resume": ("active", {"paused", "draft"}),
                               "reopen": ("review", {"completed"})}
                destination, allowed = transitions[action]
                if status not in allowed:
                    raise WorkspaceError("La transición no corresponde al estado del encargo.", 409)
                task["status"] = destination
                detail = {"pause": "Encargo pausado; contexto y borrador conservados.",
                          "resume": "Encargo retomado desde el estado guardado.",
                          "reopen": "Encargo reabierto para revisión."}[action]
            now = datetime.now(timezone.utc).isoformat()
            db.execute("UPDATE tasks SET document=?, decisions=?, sources=?, status=?, revision=revision+1, "
                       "updated_at=? WHERE id=?", (task["document"], json.dumps(task["decisions"]),
                       json.dumps(task["sources"]), task["status"], now, task_id))
            self.event(db, task_id, action, detail, now)
        return self.get(task_id)
