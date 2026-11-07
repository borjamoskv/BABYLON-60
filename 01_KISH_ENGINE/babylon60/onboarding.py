"""Opt-in Codex integration, ownership-aware removal and isolated MCP diagnosis.

Instruction files are read through no-follow descriptors. Replacements check both
identity and bytes immediately before replacing; this detects ordinary concurrent
edits, but is not a filesystem compare-and-swap primitive.
"""

from __future__ import annotations

import json
import os
import queue
import shutil
import stat
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from blake3 import blake3

from babylon60.experience import (
    load_mcp_instructions,
    load_presentation_guide,
    load_session_profile,
)

_NAME = "babylon60"
_MODULE = "babylon60.mcp.cortex_mcp_server"
_START = b"<!-- babylon60:codex:start -->"
_END = b"<!-- babylon60:codex:end -->"
_NEXT = "Abre una conversación nueva de Codex para cargar las preferencias y el MCP."
_REPAIR = "Revisa el conflicto indicado y vuelve a ejecutar babylon60 setup --client codex."


class _IntegrationError(Exception):
    """An actionable, expected integration failure."""


@dataclass(frozen=True)
class _File:
    path: Path
    data: bytes | None
    identity: tuple[int, int, int, int, int] | None
    mode: int = 0o600


def _absolute(path: str | Path) -> Path:
    return Path(path).expanduser().absolute()


def _locations() -> tuple[Path, Path, Path]:
    codex_home = _absolute(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    data_home = _absolute(os.environ.get("BABYLON_HOME", str(Path.home() / ".babylon60")))
    return codex_home, data_home, data_home / "integrations" / "codex.json"


def _check_directory(path: Path) -> None:
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return
    if not stat.S_ISDIR(mode):
        raise _IntegrationError(f"La ruta debe ser un directorio real, sin symlinks: {path}")


def _parents(path: Path) -> None:
    """Create only real directories, rejecting symlinks at the managed boundary."""
    missing: list[Path] = []
    cursor = path
    while not cursor.exists() and not cursor.is_symlink():
        missing.append(cursor)
        cursor = cursor.parent
    _check_directory(cursor)
    for directory in reversed(missing):
        directory.mkdir(mode=0o700, exist_ok=True)
        _check_directory(directory)


def _read(path: Path) -> _File:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0)
    try:
        fd = os.open(path, flags)
    except FileNotFoundError:
        if path.is_symlink():
            raise _IntegrationError(f"Se rechaza el symlink: {path}") from None
        return _File(path, None, None)
    except OSError as exc:
        raise _IntegrationError(f"No se puede leer con seguridad {path}: {exc}") from exc
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
            raise _IntegrationError(f"Se requiere un archivo regular sin enlaces adicionales: {path}")
        # Windows has no O_NOFOLLOW; the post-open lstat also rejects links there.
        link_info = path.lstat()
        if stat.S_ISLNK(link_info.st_mode) or (info.st_dev, info.st_ino) != (link_info.st_dev, link_info.st_ino):
            raise _IntegrationError(f"La ruta cambió o es un symlink: {path}")
        data = stream.read()
    identity = (info.st_dev, info.st_ino, info.st_mtime_ns, info.st_size, info.st_mode)
    return _File(path, data, identity, stat.S_IMODE(info.st_mode))


def _unchanged(file: _File) -> bool:
    current = _read(file.path)
    return current.identity == file.identity and current.data == file.data


def _fingerprint(file: _File) -> dict[str, object]:
    """Keep ownership evidence without retaining configuration or credentials."""
    return {
        "exists": file.data is not None,
        "blake3": blake3(file.data or b"").hexdigest(),
        "identity": list(file.identity) if file.identity is not None else None,
    }


def _replace(before: _File, data: bytes | None) -> _File:
    if not _unchanged(before):
        raise _IntegrationError(f"Cambio concurrente detectado; se conserva {before.path}")
    if data is None:
        before.path.unlink(missing_ok=True)
        return _read(before.path)
    _parents(before.path.parent)
    temporary: str | None = None
    try:
        with tempfile.NamedTemporaryFile(dir=before.path.parent, prefix=".babylon60-", delete=False) as stream:
            temporary = stream.name
            if hasattr(os, "fchmod"):
                os.fchmod(stream.fileno(), before.mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        if not _unchanged(before):
            raise _IntegrationError(f"Cambio concurrente detectado; se conserva {before.path}")
        os.replace(temporary, before.path)
        temporary = None
        return _read(before.path)
    finally:
        if temporary is not None:
            Path(temporary).unlink(missing_ok=True)


def _state(file: _File) -> dict[str, object]:
    if file.data is None:
        return {"version": 1, "clients": {}}
    try:
        value = json.loads(file.data)
    except (ValueError, UnicodeDecodeError) as exc:
        raise _IntegrationError(f"Estado de instalación dañado; conserva y revisa {file.path}") from exc
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("clients"), dict):
        raise _IntegrationError(f"Formato de estado no reconocido; revisa {file.path}")
    return cast(dict[str, object], value)


def _record(state: dict[str, object], home: Path) -> dict[str, object] | None:
    clients = cast(dict[str, object], state["clients"])
    record = clients.get(str(home))
    if record is None:
        return None
    if not isinstance(record, dict):
        raise _IntegrationError("El registro de propiedad de Codex está dañado.")
    if (
        record.get("profile_path") not in {str(home / "AGENTS.md"), str(home / "AGENTS.override.md")}
        or not isinstance(record.get("segment"), str)
        or not isinstance(record.get("transport"), dict)
        or not isinstance(record.get("managed_mcp"), bool)
    ):
        raise _IntegrationError("El registro de propiedad de Codex está incompleto o fuera de su directorio.")
    return cast(dict[str, object], record)


def _effective(home: Path) -> _File:
    _check_directory(home)
    override = _read(home / "AGENTS.override.md")
    if override.data and override.data.strip():
        return override
    return _read(home / "AGENTS.md")


def _codex() -> str:
    executable = shutil.which("codex") or shutil.which("codex.cmd")
    if not executable:
        raise _IntegrationError(
            "No se encuentra Codex CLI en PATH. Instálalo y ejecuta babylon60 setup --client codex."
        )
    return str(_absolute(executable))


def _codex_prefix(executable: str) -> list[str]:
    if sys.platform != "win32" or Path(executable).suffix.lower() not in {".cmd", ".bat"}:
        return [executable]
    # Do not pass user paths through cmd.exe. The official npm shim has a stable
    # JavaScript entry point, which can be called directly with Node and argv.
    base = Path(executable).parent
    script = base / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
    local_node = base / "node.exe"
    node = str(local_node) if local_node.is_file() else shutil.which("node.exe") or shutil.which("node")
    if not script.is_file() or not node:
        raise _IntegrationError(
            "No se puede usar este launcher .cmd de Codex sin un shell. "
            "Instala la CLI oficial con Node.js o coloca codex.exe en PATH y repite setup."
        )
    return [str(_absolute(node)), str(script)]


def _run(executable: str, home: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    env = dict(os.environ, CODEX_HOME=str(home))
    directory = home
    while not directory.is_dir():
        directory = directory.parent
    # A list of arguments avoids shell expansion, including paths with Unicode.
    return subprocess.run(
        [*_codex_prefix(executable), "mcp", *arguments],
        env=env,
        cwd=directory,
        capture_output=True,
        timeout=30,
        check=False,
    )


def _get(executable: str, home: Path) -> dict[str, object] | None:
    if not home.exists():
        # An uninitialized Codex home cannot contain a registration. Some CLI
        # versions reject a nonexistent CODEX_HOME even for read-only queries.
        return None
    result = _run(executable, home, ["get", _NAME, "--json"])
    if result.returncode:
        error = result.stderr.decode("utf-8", errors="replace")
        if f"No MCP server named '{_NAME}' found" in error:
            return None
        # Do not print CLI output: configuration errors may include credentials.
        raise _IntegrationError(
            "Codex no puede leer su configuración. Ejecuta codex mcp get babylon60 --json "
            "con el mismo CODEX_HOME y corrige el error antes de repetir setup."
        )
    try:
        value = json.loads(result.stdout)
    except (ValueError, UnicodeDecodeError) as exc:
        raise _IntegrationError("Codex devolvió una configuración no válida; actualiza o revisa su CLI.") from exc
    if not isinstance(value, dict) or not isinstance(value.get("transport"), dict):
        raise _IntegrationError("Codex devolvió un formato MCP no reconocido; revisa su versión.")
    transport = cast(dict[str, object], value["transport"])
    normalized: dict[str, object] = dict(transport)
    normalized["enabled"] = value.get("enabled", True)
    normalized["env"] = transport.get("env") or {}
    settings = {
        key: setting
        for key, setting in value.items()
        if key not in {"name", "transport", "enabled"} and setting is not None
    }
    if settings:
        normalized["settings"] = settings
    for key in ("env_vars", "cwd"):
        if not normalized.get(key):
            normalized.pop(key, None)
    return normalized


def _transport(data_home: Path) -> dict[str, object]:
    return {
        "type": "stdio",
        "enabled": True,
        "command": str(_absolute(sys.executable)),
        "args": ["-m", _MODULE, "--ledger", str(data_home / "mcp_ledger.db")],
        "env": {
            "BABYLON_HOME": str(data_home),
            "BABYLON_CAUSAL_GATE_DB": str(data_home / "causal_gate.db"),
        },
    }


def _add(executable: str, home: Path, transport: dict[str, object]) -> None:
    arguments = ["add", _NAME]
    environment = cast(dict[str, str], transport["env"])
    for key, value in sorted(environment.items()):
        arguments.extend(["--env", f"{key}={value}"])
    arguments.extend(["--", cast(str, transport["command"]), *cast(list[str], transport["args"])])
    if _run(executable, home, arguments).returncode:
        raise _IntegrationError("Codex no pudo registrar el MCP. Revisa permisos y configuración y repite setup.")


def _remove_mcp(executable: str, home: Path) -> None:
    if _run(executable, home, ["remove", _NAME]).returncode:
        raise _IntegrationError(
            "Codex no pudo retirar el MCP. Revisa su configuración antes de repetir setup --remove."
        )


def _strip(file: _File, record: dict[str, object]) -> bytes:
    data = file.data or b""
    segment = cast(str, record["segment"]).encode("utf-8")
    if not segment or data.count(segment) != 1:
        raise _IntegrationError(
            f"El bloque gestionado cambió o falta; se conserva {file.path}. Revisa sus marcadores Babylon."
        )
    return data.replace(segment, b"", 1)


def _segment(data: bytes, profile: str) -> bytes:
    if _START in data or _END in data:
        raise _IntegrationError("Hay marcadores Babylon sin propiedad confirmada; revisa el bloque antes de instalar.")
    separator = b"" if not data or data.endswith(b"\n\n") else b"\n" if data.endswith(b"\n") else b"\n\n"
    segment = separator + _START + b"\n" + profile.rstrip().encode("utf-8") + b"\n" + _END + b"\n"
    if len(segment) > 2000:
        raise _IntegrationError("El bloque global de Babylon supera el límite de 2000 bytes.")
    return segment


def _result(ok: bool, status: str, message: str, next_step: str, **extra: object) -> dict[str, object]:
    return {"ok": ok, "status": status, "message": message, "next_step": next_step, **extra}


def setup_codex(*, dry_run: bool = False, remove: bool = False) -> dict[str, object]:
    """Connect the installed package to Codex, without changing unrelated settings."""
    changed: list[tuple[_File, _File]] = []
    executable: str | None = None
    home: Path | None = None
    previous: dict[str, object] | None = None
    expected: dict[str, object] | None = None
    record: dict[str, object] | None = None
    mcp_touched = False
    config_after: _File | None = None
    try:
        home, data_home, state_path = _locations()
        _check_directory(home)
        _check_directory(data_home)
        _check_directory(state_path.parent)
        state_file = _read(state_path)
        state = _state(state_file)
        record = _record(state, home)
        if remove and record is None:
            return _result(
                True,
                "not_configured",
                "Babylon no tiene una instalación propia que retirar en este CODEX_HOME.",
                "No se ha modificado la configuración.",
            )
        executable = _codex()
        config_before = _read(home / "config.toml")
        previous = _get(executable, home)
        expected = _transport(data_home)
        owned_transport = record.get("transport") if record else None
        owned = bool(record and record["managed_mcp"])
        if previous is not None and previous != expected and (not owned or previous != owned_transport):
            raise _IntegrationError(
                "El nombre MCP babylon60 ya pertenece a otra configuración o fue modificado. Se conserva; renómbralo en Codex o revisa su propietario."
            )
        if remove and owned and previous is not None and previous != owned_transport:
            raise _IntegrationError(
                "El MCP gestionado fue modificado externamente; se conserva. Revisa la configuración antes de retirarlo."
            )
        destructive = owned and previous is not None and (remove or previous != expected)
        if destructive and record and record.get("config_guard") != _fingerprint(config_before):
            raise _IntegrationError(
                "config.toml cambió desde la instalación; Codex no expone todas sus opciones MCP. "
                "Se conserva la configuración completa. Revisa sus cambios y retira el registro "
                "manualmente con codex mcp remove babylon60 antes de repetir setup."
            )

        target = _effective(home)
        edits: list[tuple[_File, bytes]] = []
        old: _File | None = None
        stripped: bytes | None = None
        if record:
            old = _read(Path(cast(str, record["profile_path"])))
            stripped = _strip(old, record)
        if remove:
            assert old is not None and stripped is not None and record is not None
            edits.append((old, stripped))
            steps = [f"Retirar únicamente el bloque Babylon de {old.path}"]
            if owned and previous is not None:
                steps.append("codex mcp remove babylon60 (solo registro propio)")
            cast(dict[str, object], state["clients"]).pop(str(home))
        else:
            profile = load_session_profile()
            if old and old.path != target.path:
                assert stripped is not None
                edits.append((old, stripped))
            base = stripped if old and old.path == target.path else (target.data or b"")
            assert base is not None
            segment = _segment(base, profile)
            edits.append((target, base + segment))
            managed = owned or previous is None
            cast(dict[str, object], state["clients"])[str(home)] = {
                "profile_path": str(target.path),
                "segment": segment.decode("utf-8"),
                "transport": expected,
                "managed_mcp": managed,
                "config_guard": record.get("config_guard") if record else _fingerprint(config_before),
            }
            steps = [f"Instalar el bloque Babylon ({len(segment)} bytes) en {target.path}"]
            if old and old.path != target.path:
                steps.insert(0, f"Migrar únicamente el bloque propio de {old.path}")
            if previous != expected:
                steps.extend(
                    [
                        f"Entorno MCP: BABYLON_HOME={data_home}",
                        f"Entorno MCP: BABYLON_CAUSAL_GATE_DB={data_home / 'causal_gate.db'}",
                        f"Registrar codex mcp add babylon60 --env BABYLON_HOME={data_home} --env BABYLON_CAUSAL_GATE_DB={data_home / 'causal_gate.db'} -- {expected['command']} -m {_MODULE} --ledger {data_home / 'mcp_ledger.db'}",
                    ]
                )
        steps.append(f"Guardar propiedad de la integración en {state_path}; conservar el ledger")
        if dry_run:
            return _result(
                True,
                "dry_run",
                "Vista previa; no se ha escrito ningún archivo ni modificado el MCP.",
                "Ejecuta el mismo comando sin --dry-run para aplicar estos cambios.",
                steps=steps,
            )

        if not remove and _effective(home).path != target.path:
            raise _IntegrationError("El archivo global efectivo cambió durante la operación; repite setup.")
        for before, content in edits:
            if before.data != content:
                changed.append((before, _replace(before, content)))
        if remove and owned and previous is not None:
            if _get(executable, home) != previous or not _unchanged(config_before):
                raise _IntegrationError("El MCP cambió durante la operación; se conserva la configuración externa.")
            mcp_touched = True
            try:
                _remove_mcp(executable, home)
            finally:
                config_after = _read(home / "config.toml")
            if _get(executable, home) is not None:
                raise _IntegrationError("Codex sigue exponiendo el registro MCP después de retirarlo.")
        elif not remove and previous != expected:
            if _get(executable, home) != previous or not _unchanged(config_before):
                raise _IntegrationError("El MCP cambió durante la operación; se conserva la configuración externa.")
            mcp_touched = True
            try:
                if previous is not None:
                    _remove_mcp(executable, home)
                _add(executable, home, expected)
            finally:
                config_after = _read(home / "config.toml")
            if _get(executable, home) != expected:
                raise _IntegrationError("El registro MCP no coincide con lo solicitado; revisa la versión de Codex.")
            installed_record = cast(dict[str, object], cast(dict[str, object], state["clients"])[str(home)])
            installed_record["config_guard"] = _fingerprint(config_after)
        if not remove and _effective(home).path != target.path:
            raise _IntegrationError("El archivo global efectivo cambió durante la operación; repite setup.")
        for _, after in changed:
            if not _unchanged(after):
                raise _IntegrationError(f"Cambio concurrente detectado; se conserva {after.path}")
        encoded = (json.dumps(state, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        if state_file.data != encoded:
            changed.append((state_file, _replace(state_file, encoded)))
        return _result(
            True,
            "removed" if remove else "configured",
            "Integración propia de Babylon retirada; el ledger se conserva."
            if remove
            else "Babylon conectado a Codex con preferencias globales y MCP del paquete instalado.",
            "Abre una conversación nueva de Codex para cargar la configuración actualizada." if remove else _NEXT,
            steps=steps,
        )
    except (OSError, ValueError, subprocess.SubprocessError, _IntegrationError) as exc:
        rollback_errors: list[str] = []
        if mcp_touched and executable and home:
            try:
                if config_after is None or not _unchanged(config_after):
                    raise _IntegrationError("La configuración cambió externamente durante el rollback.")
                current = _get(executable, home)
                if current == expected and current != previous:
                    _remove_mcp(executable, home)
                    current = None
                if current is None and previous is not None:
                    _add(executable, home, previous)
                elif current != previous:
                    rollback_errors.append("El MCP cambió externamente y se conserva.")
            except (OSError, ValueError, subprocess.SubprocessError, _IntegrationError):
                rollback_errors.append(
                    "No se pudo restaurar el MCP automáticamente; revisa codex mcp get babylon60 --json."
                )
        for before, after in reversed(changed):
            try:
                _replace(after, before.data)
            except (OSError, _IntegrationError):
                rollback_errors.append(f"Se conserva el cambio externo en {before.path}.")
        if mcp_touched and previous is not None and home and record and record.get("managed_mcp"):
            try:
                if record.get("config_guard") != _fingerprint(_read(home / "config.toml")):
                    rollback_errors.append(
                        "La restauración no recuperó el guard previo de config.toml; revisa "
                        "codex mcp get babylon60 --json antes de retirar la integración."
                    )
            except (OSError, _IntegrationError):
                rollback_errors.append("No se pudo comprobar el guard de config.toml después de la reversión.")
        return _result(
            False,
            "rollback_incomplete" if rollback_errors else "error",
            str(exc),
            _REPAIR
            if not rollback_errors
            else "Revisa los cambios conservados y el registro codex mcp get babylon60 --json antes de repetir setup o retirarlo manualmente.",
            rollback=rollback_errors,
        )


def _probe(transport: dict[str, object]) -> dict[str, object]:
    """Speak MCP to the installed executable with all writable paths temporary."""
    with tempfile.TemporaryDirectory(prefix="babylon60-doctor-") as directory:
        temporary = Path(directory)
        env = dict(os.environ)
        env.pop("PYTHONPATH", None)
        env.pop("PYTHONHOME", None)
        env.update(
            {
                "BABYLON_HOME": str(temporary / "data"),
                "BABYLON_CAUSAL_GATE_DB": str(temporary / "gate.db"),
                "PYTHONIOENCODING": "utf-8",
            }
        )
        command = [cast(str, transport["command"]), "-m", _MODULE, "--ledger", str(temporary / "ledger.db")]
        messages: queue.Queue[bytes | None] = queue.Queue(maxsize=128)
        with tempfile.TemporaryFile() as errors:
            process = subprocess.Popen(
                command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=errors, cwd=temporary, env=env
            )
            assert process.stdin is not None and process.stdout is not None
            output = process.stdout
            deadline = time.monotonic() + 20

            def collect() -> None:
                for _ in range(messages.maxsize):
                    if time.monotonic() >= deadline:
                        return
                    line = output.readline(1_048_577)
                    try:
                        messages.put_nowait(line or None)
                    except queue.Full:
                        return
                    if not line:
                        return

            reader = threading.Thread(target=collect, daemon=True)
            reader.start()

            def send(message: dict[str, object]) -> None:
                assert process.stdin is not None
                process.stdin.write((json.dumps(message, ensure_ascii=False) + "\n").encode("utf-8"))
                process.stdin.flush()

            def request(identifier: int, method: str, params: dict[str, object]) -> dict[str, object]:
                send({"jsonrpc": "2.0", "id": identifier, "method": method, "params": params})
                for _ in range(64):
                    try:
                        raw = messages.get(timeout=max(0.001, deadline - time.monotonic()))
                    except queue.Empty as exc:
                        raise _IntegrationError("El MCP no respondió a tiempo en la sonda temporal.") from exc
                    if raw is None:
                        raise _IntegrationError(
                            "El ejecutable no pudo iniciar el MCP fuera del checkout; reinstala el paquete con sus dependencias."
                        )
                    if len(raw) > 1_048_576:
                        raise _IntegrationError("El MCP produjo una respuesta fuera del límite de diagnóstico.")
                    value = json.loads(raw)
                    if not isinstance(value, dict) or value.get("jsonrpc") != "2.0":
                        raise _IntegrationError("La respuesta del MCP no respeta JSON-RPC 2.0.")
                    if value.get("id") != identifier:
                        continue
                    if "error" in value or not isinstance(value.get("result"), dict):
                        raise _IntegrationError(f"El MCP rechazó {method}; revisa la instalación del paquete.")
                    return cast(dict[str, object], value["result"])
                raise _IntegrationError("El MCP no devolvió la respuesta esperada.")

            try:
                initialized = request(
                    1,
                    "initialize",
                    {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {},
                        "clientInfo": {"name": "babylon60-doctor", "version": "1"},
                    },
                )
                if initialized.get("instructions") != load_mcp_instructions():
                    raise _IntegrationError("Las instrucciones MCP no coinciden con el contrato del paquete instalado.")
                send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
                tools = request(2, "tools/list", {})
                advertised_tools = tools.get("tools")
                if not isinstance(advertised_tools, list) or not advertised_tools:
                    raise _IntegrationError("El MCP no anuncia sus herramientas.")
                guide = request(3, "resources/read", {"uri": "babylon://presentation/guide"})
                contents = guide.get("contents")
                if not isinstance(contents, list) or not any(
                    isinstance(item, dict)
                    and item.get("uri") == "babylon://presentation/guide"
                    and item.get("text") == load_presentation_guide()
                    for item in contents
                ):
                    raise _IntegrationError("La guía portable no coincide con el recurso distribuido.")
                return {
                    "server": initialized.get("serverInfo"),
                    "protocol": initialized.get("protocolVersion"),
                    "tools": len(advertised_tools),
                    "isolated": True,
                }
            finally:
                process.stdin.close()
                if process.poll() is None:
                    process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=3)
                reader.join(timeout=1)
                output.close()


def doctor_codex() -> dict[str, object]:
    """Diagnose connection and contract delivery, never infer model behavior."""
    checks: dict[str, str] = {
        "configuration": "PENDIENTE",
        "executable": "PENDIENTE",
        "mcp": "PENDIENTE",
        "contract": "PENDIENTE",
        "behavior": "NO_VERIFICADO",
    }
    stage = "configuration"
    try:
        home, data_home, state_path = _locations()
        _check_directory(home)
        _check_directory(data_home)
        _check_directory(state_path.parent)
        executable = _codex()
        configured = _get(executable, home)
        expected = _transport(data_home)
        if configured != expected:
            raise _IntegrationError(
                "Falta el registro MCP esperado o su configuración ha cambiado. Ejecuta babylon60 setup --client codex."
            )
        state = _state(_read(state_path))
        record = _record(state, home)
        target = _effective(home)
        if not record or record["profile_path"] != str(target.path):
            raise _IntegrationError(
                "El perfil global no está en el archivo efectivo. Ejecuta babylon60 setup --client codex para instalarlo o migrarlo."
            )
        stripped = _strip(target, record)
        if target.data != stripped + _segment(stripped, load_session_profile()):
            raise _IntegrationError(
                "El perfil global no coincide con la versión instalada. Ejecuta babylon60 setup --client codex."
            )
        checks[stage] = "OK"
        stage = "executable"
        python = Path(cast(str, configured["command"]))
        if not python.is_file() or (os.name != "nt" and not os.access(python, os.X_OK)):
            raise _IntegrationError(
                "No existe un ejecutable Python accesible para el paquete; reinstala Babylon y repite setup."
            )
        checks[stage] = "OK"
        stage = "mcp"
        details = _probe(configured)
        checks[stage] = "OK"
        checks["contract"] = "OK"
        return _result(
            True,
            "connected",
            "Configuración, conexión MCP y entrega del contrato verificadas con datos temporales. La mejora de las respuestas sigue NO_VERIFICADO.",
            _NEXT,
            checks=checks,
            probe=details,
        )
    except (OSError, ValueError, subprocess.SubprocessError, _IntegrationError) as exc:
        checks[stage] = "ERROR"
        return _result(
            False,
            "error",
            str(exc),
            "Ejecuta babylon60 setup --client codex y repite babylon60 doctor --client codex --json.",
            checks=checks,
        )
