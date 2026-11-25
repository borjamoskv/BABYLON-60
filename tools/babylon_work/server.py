"""Authenticated Babylon Work app-server with bounded AI jobs and signed checks."""

from __future__ import annotations

import argparse
import hmac
import json
import secrets
import sqlite3
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

from tools.babylon_work.workspace import ROOT, Workspace, WorkspaceError, read_source, source_catalog
from tools.babylon_work.runtime import Runtime

ASSETS = {"/": ("index.html", "text/html"), "/work.css": ("work.css", "text/css"),
          "/work.js": ("work.js", "text/javascript"), "/runtime-ui.js": ("runtime-ui.js", "text/javascript")}
MAX_BODY = 450_000


class WorkServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, port: int, workspace: Workspace, *, native_library: Path | None = None):
        self.workspace = workspace
        self.token = secrets.token_urlsafe(32)
        super().__init__(("127.0.0.1", port), WorkHandler)
        self.origin = f"http://127.0.0.1:{self.server_port}"
        self.runtime = Runtime(workspace, native_library)

    def server_close(self) -> None:
        if hasattr(self, "runtime"):
            self.runtime.close()
        super().server_close()


class WorkHandler(BaseHTTPRequestHandler):
    server: WorkServer

    def log_message(self, *_args: object) -> None:
        pass  # Do not log authorization material or draft contents.

    def send(self, status: int, data: bytes, content_type: str = "application/json") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Content-Security-Policy", "default-src 'none'; script-src 'self'; "
                         "style-src 'self'; connect-src 'self'; img-src 'self' data:; "
                         "base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
        self.end_headers()
        self.wfile.write(data)

    def json(self, status: int, body: object) -> None:
        self.send(status, json.dumps(body, ensure_ascii=False).encode())

    def authorize(self) -> bool:
        expected_host = f"127.0.0.1:{self.server.server_port}"
        if self.headers.get("Host") != expected_host:
            self.json(403, {"error": "Anfitrión no autorizado."})
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin != self.server.origin:
            self.json(403, {"error": "Origen no autorizado."})
            return False
        provided = self.headers.get("Authorization", "")
        if not hmac.compare_digest(provided.encode(), ("Bearer " + self.server.token).encode()):
            self.json(401, {"error": "Introduce la clave de acceso local que aparece al iniciar el servidor."})
            return False
        return True

    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path in ASSETS:
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                self.json(403, {"error": "Anfitrión no autorizado."})
                return
            name, content_type = ASSETS[path]
            self.send(200, (Path(__file__).parent / name).read_bytes(), content_type)
            return
        if not self.authorize():
            return
        try:
            if path == "/api/workspace":
                self.json(200, {"tasks": self.server.workspace.list(), "sources": source_catalog(),
                                "project": ROOT.name, "mode": "ai-and-signed-checks"})
            elif path == "/api/runtime":
                self.json(200, self.server.runtime.status())
            elif path.startswith("/api/runs/"):
                self.json(200, self.server.runtime.runs.public(
                    self.server.runtime.runs.get(path.removeprefix("/api/runs/"))))
            elif path.startswith("/api/tasks/") and path.endswith("/runs"):
                task_id = path.removeprefix("/api/tasks/").removesuffix("/runs")
                self.server.workspace.get(task_id)
                self.json(200, [self.server.runtime.runs.public(run) for run in self.server.runtime.runs.for_task(task_id)])
            elif path.startswith("/api/sources/"):
                self.json(200, read_source(path.removeprefix("/api/sources/")))
            elif path.startswith("/api/tasks/"):
                self.json(200, self.server.workspace.get(path.removeprefix("/api/tasks/")))
            else:
                self.json(404, {"error": "Ruta no disponible."})
        except WorkspaceError as exc:
            self.json(exc.status, {"error": str(exc)})
        except (OSError, UnicodeError, sqlite3.Error):
            self.json(500, {"error": "No se ha podido leer el espacio local."})

    def do_POST(self) -> None:
        if not self.authorize():
            return
        try:
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                raise WorkspaceError("Se requiere contenido JSON.", 415)
            raw_length = self.headers.get("Content-Length", "")
            if not raw_length.isdecimal() or not 0 < int(raw_length) <= MAX_BODY:
                raise WorkspaceError("Tamaño de solicitud no permitido.", 413)
            self.connection.settimeout(10)
            body = json.loads(self.rfile.read(int(raw_length)))
            if not isinstance(body, dict):
                raise WorkspaceError("La solicitud debe ser un objeto JSON.")
            path = urlsplit(self.path).path
            if path == "/api/tasks":
                self.json(201, self.server.workspace.create(body))
            elif path.startswith("/api/tasks/") and path.endswith("/runs"):
                task_id = path.removeprefix("/api/tasks/").removesuffix("/runs")
                self.json(202, self.server.runtime.start(task_id, body))
            elif path.startswith("/api/runs/") and path.endswith("/authorize"):
                run_id = path.removeprefix("/api/runs/").removesuffix("/authorize")
                self.json(202, self.server.runtime.authorize(run_id, body))
            elif path.startswith("/api/tasks/"):
                self.json(200, self.server.workspace.update(path.removeprefix("/api/tasks/"), body))
            else:
                raise WorkspaceError("Ruta no disponible.", 404)
        except WorkspaceError as exc:
            self.json(exc.status, {"error": str(exc)})
        except (ValueError, UnicodeError):
            self.json(400, {"error": "JSON no válido."})
        except (OSError, TimeoutError, sqlite3.Error):
            self.json(500, {"error": "No se ha podido guardar. Conserva tu borrador y vuelve a intentarlo."})


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8788)
    parser.add_argument("--state", type=Path, default=ROOT / "target" / "babylon-work" / "workspace.sqlite")
    parser.add_argument("--capability-library", type=Path,
                        default=ROOT / "target" / "debug" / "libbabylon60.dylib",
                        help="Biblioteca del broker, seleccionada por el operador; nunca desde la API")
    args = parser.parse_args()
    library = args.capability_library.absolute()
    server = WorkServer(args.port, Workspace(args.state), native_library=library if library.is_file() else None)
    print(f"Babylon Work · prototipo local\n{server.origin}\nClave local: {server.token}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
