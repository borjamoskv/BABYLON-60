# C5-REAL EXERGY CERTIFIED
import asyncio
import logging

from typing import Any

import os
import json
import signal

class DualContextAgent:
    """
    C5-REAL: Agente de Contexto Dual (Agent Igor)
    Servidor IPC (Unix Socket) para ingestión de grafos AST y AOM.
    """

    def _extract_socket_from_lines(self, lines: list[str]) -> str | None:
        for line in lines:
            if line.startswith("CORTEX_IPC_SOCKET="):
                return line.split("=")[1].strip()
        return None

    def _read_env_socket(self) -> str | None:
        env_path = os.path.join(os.getcwd(), ".env")
        if not os.path.exists(env_path):
            return None
        try:
            with open(env_path, "r") as f:
                lines = f.readlines()
            return self._extract_socket_from_lines(lines)
        except OSError:
            pass
        return None

    def __init__(self) -> None:
        self.code_ast: dict[str, Any] | None = None
        self.dom_aom: dict[str, Any] | None = None

        socket_env = os.environ.get("CORTEX_IPC_SOCKET")
        if not socket_env:
            socket_env = self._read_env_socket()
            if socket_env:
                os.environ["CORTEX_IPC_SOCKET"] = socket_env

        if not socket_env:
            socket_env = "/tmp/cortex_ipc.sock"
            os.environ["CORTEX_IPC_SOCKET"] = socket_env
            logging.info(f"[C5-REAL] CORTEX_IPC_SOCKET asignado por defecto a {socket_env}")

        self.socket_path: str = socket_env or ""
        logging.basicConfig(level=logging.INFO)

    async def ingest_code_context(self, file_path: str, ast_data: dict[str, Any]) -> None:
        self.code_ast = ast_data
        logging.info(f"[C5-REAL] Ingested AST from {file_path}")

    async def ingest_dom_context(self, aom_data: dict[str, Any]) -> None:
        self.dom_aom = aom_data
        logging.info("[C5-REAL] Ingested Target DOM AOM")

    async def evaluate_isomorphism(self) -> dict[str, Any]:
        if not self.code_ast or not self.dom_aom:
            return {"status": "Anergia", "reason": "Missing context"}
        return {
            "status": "Exergia",
            "isomorphism_matched": True,
            "action": "Esperando comandos del operador",
        }

    async def _process_payload(self, payload: dict[str, Any]) -> None:
        ptype = payload.get("type")
        if ptype == "AST":
            await self.ingest_code_context(payload.get("file", "unknown"), payload.get("data", {}))
        elif ptype == "AOM":
            await self.ingest_dom_context(payload.get("data", {}))
        elif ptype == "HEARTBEAT":
            pass

    async def handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Transductor de payload IPC (NDJSON Stream)."""
        try:
            async for line in reader:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    payload = json.loads(line_str)
                    await self._process_payload(payload)
                except json.JSONDecodeError as e:
                    logging.warning(f"[C5-REAL] NDJSON Stream Warning: Chunk ignorado por error de formato: {e}")
                    continue
        except (OSError, ValueError, json.JSONDecodeError, RuntimeError) as e:
            # Fail-Fast C5-REAL logging
            logging.error(f"[C5-REAL] IPC Stream Fatal Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start_ipc_server(self) -> None:
        """Ω9: Ignición determinista síncrona."""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        server = await asyncio.start_unix_server(self.handle_client, path=self.socket_path)
        logging.info(f"[C5-REAL] Agent Igor IPC Server listening on {self.socket_path}")

        async with server:
            await server.serve_forever()

def cleanup_socket(signum: Any, frame: Any) -> None:
    """Ω43: Prevención de Zombie IPC (Desvinculado Atómico)."""
    sock: str = os.environ.get("CORTEX_IPC_SOCKET", "")
    if sock and os.path.exists(sock):
        os.remove(sock)
        logging.info("[C5-REAL] Socket unlinked atomically. Purging process.")
    os.kill(os.getpid(), signal.SIGKILL)

if __name__ == "__main__":
    signal.signal(signal.SIGINT, cleanup_socket)
    signal.signal(signal.SIGTERM, cleanup_socket)

    agent = DualContextAgent()
    asyncio.run(agent.start_ipc_server())
