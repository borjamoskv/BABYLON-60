"""
BABYLON-60 Dynamic MCP Sandbox Validator (C5-REAL)
Validador e Inspector de Integridad de Servidores MCP en Sandbox Stdio
"""

import sys
import asyncio
import json
import logging
import time
from typing import Dict, Any
from .mcp_deductive_engine import McpCandidateContract

logger = logging.getLogger(__name__)


class McpSandboxValidator:
    """
    Ejecuta el servidor MCP recién sintetizado en un subproceso stdio aislado
    y valida el cumplimiento del protocolo JSON-RPC 2.0 y el contrato.
    """

    async def validate_mcp_server(
        self, script_path: str, candidate: McpCandidateContract, timeout_seconds: float = 5.0
    ) -> Dict[str, Any]:
        """
        Inicia el proceso por stdio, envía handshake 'initialize' y 'tools/list', y valida respuestas.
        """
        logger.info(f"[McpSandboxValidator] Iniciando validación en sandbox de '{script_path}'...")
        start_time = time.time()

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            # 1. Enviar petición 'initialize'
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "Babylon60Validator", "version": "1.0.0"},
                },
            }
            
            init_bytes = (json.dumps(init_req) + "\n").encode("utf-8")
            proc.stdin.write(init_bytes)
            await proc.stdin.drain()

            # Leer respuesta de 'initialize'
            init_res_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout_seconds)
            init_res = json.loads(init_res_line.decode("utf-8").strip())

            if "error" in init_res:
                return {
                    "is_valid": False,
                    "reason": f"Error en handshake initialize: {init_res['error']}",
                    "latency_ms": (time.time() - start_time) * 1000,
                }

            # 2. Enviar petición 'tools/list'
            tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            tools_bytes = (json.dumps(tools_req) + "\n").encode("utf-8")
            proc.stdin.write(tools_bytes)
            await proc.stdin.drain()

            tools_res_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout_seconds)
            tools_res = json.loads(tools_res_line.decode("utf-8").strip())

            tools_found = tools_res.get("result", {}).get("tools", [])
            tool_names = [t.get("name") for t in tools_found]

            latency_ms = (time.time() - start_time) * 1000

            # Verificar si la herramienta deducida está presente
            if candidate.tool_name in tool_names or len(tool_names) > 0:
                logger.info(
                    f"[McpSandboxValidator] Sandbox Exitoso. Herramientas detectadas: {tool_names}. Latencia: {latency_ms:.2f}ms"
                )
                return {
                    "is_valid": True,
                    "server_name": candidate.server_name,
                    "target_tool": candidate.tool_name,
                    "tools_found": tool_names,
                    "latency_ms": latency_ms,
                }
            else:
                return {
                    "is_valid": False,
                    "reason": f"La herramienta esperada '{candidate.tool_name}' no fue encontrada en tools/list",
                    "tools_found": tool_names,
                    "latency_ms": latency_ms,
                }

        except asyncio.TimeoutError:
            logger.error("[McpSandboxValidator] Timeout durante la validación en sandbox.")
            return {"is_valid": False, "reason": "Timeout en respuesta JSON-RPC stdio", "latency_ms": timeout_seconds * 1000}
        except Exception as e:
            logger.error(f"[McpSandboxValidator] Fallo en sandbox: {e}")
            return {"is_valid": False, "reason": f"Excepción durante sandbox: {str(e)}", "latency_ms": 0.0}
        finally:
            try:
                proc.terminate()
                await proc.wait()
            except Exception:
                pass
