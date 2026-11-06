"""Single-owner background runtime; the HTTP surface never receives signing keys."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
import json
from pathlib import Path
from threading import Event
from typing import Any

from tools.babylon_work.effects import ProtectedChecks
from tools.babylon_work.providers import ModelClient
from tools.babylon_work.runs import Runs
from tools.babylon_work.workspace import Workspace, WorkspaceError, text


class Runtime:
    def __init__(self, workspace: Workspace, native_library: Path | None):
        self.workspace = workspace
        self.runs = Runs(workspace)
        self.runs.recover()
        self.models = ModelClient()
        self.worker = ThreadPoolExecutor(max_workers=1, thread_name_prefix="babylon-work")
        self.ready = Event()
        self.effects: ProtectedChecks | None = None
        # JSON status combines command catalog entries and optional diagnostics.
        self.effect_status: dict[str, Any] = {
            "native_available": False,
            "signing_key_configured": False,
            "commands": [],
            "detail": "Biblioteca nativa no configurada. La ejecución se rechaza.",
        }
        self.worker.submit(self.initialize, native_library)

    def initialize(self, native_library: Path | None) -> None:
        try:
            self.models.discover()
            if native_library is not None:
                self.effects = ProtectedChecks(
                    self.workspace.path.parent / "approvals.sqlite", native_library, workspace=self.workspace
                )
                self.effect_status = self.effects.status()
        except (ImportError, OSError, ValueError, PermissionError):
            self.effect_status["detail"] = "La biblioteca del broker no se ha podido cargar. Ejecución denegada."
        finally:
            self.ready.set()

    def status(self) -> dict[str, object]:
        return {"ready": self.ready.is_set(), "providers": self.models.catalog, "effects": self.effect_status}

    def start(self, task_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if set(body) - {"kind", "revision", "provider", "model", "instruction", "command_id"}:
            raise WorkspaceError("La solicitud incluye campos no admitidos.")
        kind = body.get("kind")
        if kind == "generation":
            self.models.validate(body.get("provider"), body.get("model"))
            request = {
                "provider": body["provider"],
                "model": body["model"],
                "instruction": text(body.get("instruction", ""), "instrucción", 4000, required=False),
            }
        elif kind == "checks":
            if not self.effect_status["native_available"]:
                raise WorkspaceError(self.effect_status["detail"], 409)
            command = body.get("command_id")
            if not isinstance(command, str) or command not in {item["id"] for item in self.effect_status["commands"]}:
                raise WorkspaceError("La comprobación no está en el catálogo permitido.")
            request = {"command_id": command}
        else:
            raise WorkspaceError("Tipo de trabajo no disponible.")
        # Capture the task at the same revision that the job creation validates.
        task = self.workspace.get(task_id)
        if task["revision"] != body.get("revision"):
            raise WorkspaceError("El encargo ha cambiado. Recarga antes de continuar.", 409)
        run = self.runs.create(task_id, body.get("revision"), kind, request)
        self.worker.submit(self.perform, run["id"], task)
        return self.runs.public(run)

    def perform(self, run_id: str, snapshot: dict[str, Any]) -> None:
        run = self.runs.move(run_id, "running", "Preparando el trabajo.", expected=("queued",))
        try:
            request = run["request"]
            if run["kind"] == "generation":
                document, sources, metadata = self.models.generate(
                    snapshot, request["provider"], request["model"], request["instruction"]
                )
                self.runs.complete_generation(run_id, document, sources, metadata)
            else:
                assert self.effects is not None
                arguments, approval_task = self.effects.prepare(run_id, snapshot, request["command_id"])
                with closing(self.workspace.connect()) as db, db:
                    db.execute(
                        "UPDATE work_runs SET request=? WHERE id=?",
                        (json.dumps({**request, "arguments": arguments, "approval_task": approval_task}), run_id),
                    )
                self.runs.move(
                    run_id,
                    "awaiting_approval",
                    "Solicitud preparada. Revisa el comando y solicita la firma del operador.",
                )
        except Exception as exc:
            detail = (
                str(exc)
                if isinstance(exc, WorkspaceError)
                else "El trabajo ha fallado. El borrador anterior se conserva."
            )
            self.runs.move(run_id, "failed", detail)

    def authorize(self, run_id: str, body: dict[str, Any]) -> dict[str, Any]:
        if body:
            raise WorkspaceError("No se admiten permisos ni firmas declarados por el cliente.")
        run = self.runs.get(run_id)
        if run["kind"] != "checks":
            raise WorkspaceError("Este trabajo no admite firma de ejecución.")
        self.runs.move(
            run_id, "authorizing", "Solicitando firma para la solicitud completa.", expected=("awaiting_approval",)
        )
        self.worker.submit(self.execute, run_id)
        return self.runs.public(self.runs.get(run_id))

    def execute(self, run_id: str) -> None:
        run = self.runs.get(run_id)
        try:
            task = self.workspace.get(run["task_id"])
            if task["revision"] != run["revision"]:
                raise WorkspaceError("El encargo ha cambiado después de preparar la solicitud.", 409)
            if self.effects is None:
                raise WorkspaceError("Broker no disponible.", 409)
            response = self.effects.execute(run["request"]["arguments"], run["request"]["approval_task"])
            if response.get("isError"):
                output = str(response.get("content", []))
                unknown = "EFFECT_OUTCOME_UNKNOWN" in output
                state = "unknown" if unknown else "denied"
                detail = (
                    "Resultado del efecto no confirmado; no se reintentará."
                    if unknown
                    else "El broker ha denegado la ejecución."
                )
            elif response.get("timed_out"):
                state, detail = (
                    "unknown",
                    "La comprobación agotó su plazo. La autorización queda consumida; sin reintento.",
                )
            else:
                state = "succeeded" if response.get("returncode") == 0 else "failed"
                detail = "Comprobación terminada; salida real disponible."
            self.runs.move(run_id, state, detail, response)
        except WorkspaceError as exc:
            self.runs.move(run_id, "denied", str(exc))
        except Exception:
            self.runs.move(run_id, "unknown", "Resultado no confirmado; ejecución detenida sin reintentos.")

    def close(self) -> None:
        if self.effects is not None:
            self.worker.submit(self.effects.close)
        self.worker.shutdown(wait=True, cancel_futures=False)
