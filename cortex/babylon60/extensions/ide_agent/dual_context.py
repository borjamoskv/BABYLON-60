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

    def __init__(self) -> None:
        self.code_ast: dict[str, Any] | None = None
        self.dom_aom: dict[str, Any] | None = None

        socket_env = os.environ.get("CORTEX_IPC_SOCKET")
        if not socket_env:
            try:
                env_path = os.path.join(os.getcwd(), ".env")
                if os.path.exists(env_path):
                    with open(env_path, "r") as f:
                        for line in f:
                            if line.startswith("CORTEX_IPC_SOCKET="):
                                socket_env = line.split("=")[1].strip()
                                os.environ["CORTEX_IPC_SOCKET"] = socket_env
                                break
            except Exception:
                pass

        if not socket_env:
            socket_env = "/tmp/cortex_ipc.sock"
            os.environ["CORTEX_IPC_SOCKET"] = socket_env
            logging.info(
                f"[C5-REAL] CORTEX_IPC_SOCKET asignado por defecto a {socket_env}"
            )

        self.socket_path: str = socket_env or ""
        logging.basicConfig(level=logging.INFO)

    async def ingest_code_context(
        self, file_path: str, ast_data: dict[str, Any]
    ) -> None:
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

    async def handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Transductor de payload IPC (NDJSON Stream)."""
        try:
            async for line in reader:
                line_str = line.decode("utf-8").strip()
                if not line_str:
                    continue
                try:
                    payload = json.loads(line_str)
                    ptype = payload.get("type")
                    if ptype == "AST":
                        await self.ingest_code_context(
                            payload.get("file", "unknown"), payload.get("data", {})
                        )
                    elif ptype == "AOM":
                        await self.ingest_dom_context(payload.get("data", {}))
                    elif ptype == "HEARTBEAT":
                        pass  # Ω43: Mantiene el liveness del socket
                except json.JSONDecodeError as e:
                    logging.warning(
                        f"[C5-REAL] NDJSON Stream Warning: Chunk ignorado por error de formato: {e}"
                    )
                    continue
        except Exception as e:
            # Fail-Fast C5-REAL logging
            logging.error(f"[C4-SIM] IPC Stream Fatal Error: {e}")
        finally:
            writer.close()
            await writer.wait_closed()

    async def start_ipc_server(self) -> None:
        """Ω9: Ignición determinista síncrona."""
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        server = await asyncio.start_unix_server(
            self.handle_client, path=self.socket_path
        )
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
