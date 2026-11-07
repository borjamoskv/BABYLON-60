"""Trusted fixed-command host, mediated by Babylon's existing Rust broker and gate.

The host and repository code are trusted. This is authorization mediation, not
an operating-system sandbox for arbitrary model-generated code.
"""

from __future__ import annotations

import os
from contextlib import closing
from pathlib import Path
import shutil
import signal
import subprocess
from threading import Thread
from typing import Any, TypedDict

from blake3 import blake3

from babylon60.mcp.effect_dispatch import EffectDispatcher, MediatedHandlers, canonical
from babylon60.verification.verification_gate import VerificationGate
from tools.babylon_work.workspace import ROOT, Workspace, WorkspaceError

CHECKS = {
    "workspace_tests": (
        "Pruebas de Babylon Work",
        ["uv", "run", "--locked", "pytest", "tests/test_babylon_work.py", "-q"],
    ),
    "javascript": ("Sintaxis de la interfaz", ["node", "--check", "tools/babylon_work/work.js"]),
}
BOUND_FILES = [
    "uv.lock",
    "pyproject.toml",
    "tests/test_babylon_work.py",
    "01_KISH_ENGINE/babylon60/mcp/effect_dispatch.py",
    "01_KISH_ENGINE/babylon60/verification/verification_gate.py",
    "01_KISH_ENGINE/babylon60/verification/hardware_attestation.py",
]


class CheckCommand(TypedDict):
    """Trusted command catalog entry, separate from dynamic approval payloads."""

    label: str
    argv: list[str]


def workload_digest() -> str:
    files = BOUND_FILES + [
        str(path.relative_to(ROOT))
        for path in sorted((ROOT / "tools/babylon_work").glob("*"))
        if path.suffix in {".py", ".js", ".css", ".html"}
    ]
    manifest = []
    for name in files:
        fd = os.open(ROOT / name, os.O_RDONLY | os.O_NOFOLLOW)
        with os.fdopen(fd, "rb") as source:
            manifest.append([name, blake3(source.read()).hexdigest()])
    return blake3(canonical(manifest)).hexdigest()


class ProtectedChecks(MediatedHandlers):
    EFFECT_HANDLERS = {"run_checks": "work_run_checks", "_spawn_check": "work_run_checks"}

    def __init__(self, gate_path: Path, native_library: Path, *, workspace: Workspace):
        self.workspace = workspace
        self.gate = VerificationGate(str(gate_path))
        self.effect_dispatcher = EffectDispatcher(self.gate, native_library)
        self.effect_dispatcher.update_external_policy("Enabled", "Enabled")
        self.commands: dict[str, CheckCommand] = {}
        for key, (label, argv) in CHECKS.items():
            binary = shutil.which(argv[0])
            if binary:
                self.commands[key] = {"label": label, "argv": [binary, *argv[1:]]}

    def status(self) -> dict[str, object]:
        return {
            "native_available": True,
            "signing_key_configured": self.gate._trusted_key is not None,
            "commands": [{"id": key, **item} for key, item in self.commands.items()],
            "detail": "Firma por solicitud y consumo de un solo uso. No es aislamiento del sistema operativo.",
        }

    def prepare(
        self, execution_id: str, task: dict[str, Any], command_id: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        # Task and approval objects retain their validated JSON envelope fields.
        if command_id not in self.commands:
            raise WorkspaceError("Comprobación fuera del catálogo autorizado.")
        arguments = {
            "command_id": command_id,
            "argv": self.commands[command_id]["argv"],
            "cwd": str(ROOT),
            "source_digest": workload_digest(),
            "binary_digest": blake3(Path(self.commands[command_id]["argv"][0]).read_bytes()).hexdigest(),
            "task_id": task["id"],
            "task_revision": task["revision"],
            "document_digest": blake3(task["document"].encode()).hexdigest(),
        }
        prepared = self.effect_dispatcher.dispatch(
            "work_run_checks", arguments, {"execution_id": execution_id, "mode": "prepare"}, self.run_checks
        )
        if prepared.get("isError") or not isinstance(prepared.get("approval_task"), dict):
            raise WorkspaceError("El broker no puede preparar esta comprobación.", 409)
        approval = prepared["approval_task"]
        assert isinstance(approval, dict)
        return arguments, approval

    def execute(
        self, arguments: dict[str, Any], approval_task: dict[str, Any], *, request_signature: bool = True
    ) -> dict[str, object]:
        execution_id = approval_task["execution_id"]
        refreshed = self.effect_dispatcher.dispatch(
            "work_run_checks", arguments, {"execution_id": execution_id, "mode": "prepare"}, self.run_checks
        )
        if refreshed.get("isError") or canonical(refreshed.get("approval_task")) != canonical(approval_task):
            raise WorkspaceError("El código o la política ha cambiado. Esta solicitud ya no es válida.", 409)
        if arguments.get("source_digest") != workload_digest():
            raise WorkspaceError("Las fuentes han cambiado después de preparar la solicitud.", 409)
        if request_signature:
            if self.gate._trusted_key is None:
                raise WorkspaceError(
                    "Falta BABYLON_ENCLAVE_PINNED_PUBKEY: configura la clave P-256 de confianza del operador.", 409
                )
            scope = "Babylon Work: " + self.commands[arguments["command_id"]]["label"]
            if not self.gate.enforce_biometric_sign_off(
                execution_id, approval_task["action"], scope, task_payload=approval_task
            ):
                raise WorkspaceError(
                    "La firma no se ha obtenido o no es válida. No se ha reintentado la biometría.", 403
                )
        return self.effect_dispatcher.dispatch(
            "work_run_checks", arguments, {"execution_id": execution_id}, self.run_checks
        )

    def run_checks(self, arguments: dict[str, object]) -> dict[str, object]:
        # Revalidate after biometrics, and serialize normal workspace writers with
        # the effect. The approval database alone cannot lock the task database.
        with closing(self.workspace.connect()) as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT revision,document FROM tasks WHERE id=?", (arguments.get("task_id"),)
                ).fetchone()
                if (
                    row is None
                    or row["revision"] != arguments.get("task_revision")
                    or blake3(row["document"].encode()).hexdigest() != arguments.get("document_digest")
                ):
                    raise PermissionError("Task changed before protected execution")
                return self._spawn_check(arguments)
            finally:
                db.rollback()

    def _spawn_check(self, arguments: dict[str, object]) -> dict[str, object]:
        command = self.commands.get(str(arguments.get("command_id")))
        if command is None or arguments.get("argv") != command["argv"] or arguments.get("cwd") != str(ROOT):
            raise PermissionError("Command differs from the reviewed catalog")
        if arguments.get("source_digest") != workload_digest():
            raise PermissionError("Source differs from the approved snapshot")
        if arguments.get("binary_digest") != blake3(Path(command["argv"][0]).read_bytes()).hexdigest():
            raise PermissionError("Executable differs from the approved snapshot")
        captured = bytearray()
        with subprocess.Popen(
            command["argv"],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        ) as process:

            def drain() -> None:
                assert process.stdout is not None
                while block := process.stdout.read(4096):
                    if len(captured) < 32_768:
                        captured.extend(block[: 32_768 - len(captured)])

            reader = Thread(target=drain, daemon=True)
            reader.start()
            timed_out = False
            try:
                returncode = process.wait(timeout=90)
            except subprocess.TimeoutExpired:
                timed_out = True
                os.killpg(process.pid, signal.SIGKILL)
                returncode = process.wait(timeout=5)
            reader.join(timeout=5)
            if reader.is_alive():
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                reader.join(timeout=5)
                raise RuntimeError("A child still holds the output pipe; effect outcome unknown")
        return {
            "isError": False,
            "returncode": returncode,
            "timed_out": timed_out,
            "output": captured.decode("utf-8", errors="replace"),
            "argv": command["argv"],
            "source_digest": arguments["source_digest"],
            "pid": process.pid,
        }

    def close(self) -> None:
        self.gate._conn.close()
