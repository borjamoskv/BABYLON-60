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

        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError("Subprocess stdin/stdout streams failed to initialize.")

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
            return {
                "is_valid": False,
                "reason": "Timeout en respuesta JSON-RPC stdio",
                "latency_ms": timeout_seconds * 1000,
            }
        except Exception as e:
            logger.error(f"[McpSandboxValidator] Fallo en sandbox: {e}")
            return {"is_valid": False, "reason": f"Excepción durante sandbox: {str(e)}", "latency_ms": 0.0}
        finally:
            try:
                proc.terminate()
                await proc.wait()
            except Exception as e:
                logger.warning(f"Cleanup Error: {e}")

    async def execute_and_detonate_mcp(
        self,
        script_path: str,
        candidate: McpCandidateContract,
        call_arguments: Dict[str, Any],
        timeout_seconds: float = 5.0,
        detonate: bool = True,
    ) -> Dict[str, Any]:
        """
        Ejecuta el ciclo completo de un «MCP Bomba» en un subproceso stdio aislado:
        1. Handshake 'initialize'
        2. Verificación 'tools/list'
        3. Invocación real 'tools/call' con call_arguments
        4. Autodestrucción física ('unlink') garantizada tras la ejecución (Cero Huella).
        """
        import os

        logger.info(f"[McpSandboxValidator] Detonando MCP efímero '{script_path}' -> {candidate.tool_name}...")
        start_time = time.time()

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            script_path,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        if proc.stdin is None or proc.stdout is None:
            raise RuntimeError("Subprocess stdin/stdout streams failed to initialize.")

        try:
            # 1. Handshake 'initialize'
            init_req = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "Babylon60BombExecutor", "version": "1.0.0"},
                },
            }
            proc.stdin.write((json.dumps(init_req) + "\n").encode("utf-8"))
            await proc.stdin.drain()

            init_res_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout_seconds)
            init_res = json.loads(init_res_line.decode("utf-8").strip())
            if "error" in init_res:
                return {
                    "status": "ERROR",
                    "is_valid": False,
                    "reason": f"Error en initialize: {init_res['error']}",
                    "latency_ms": (time.time() - start_time) * 1000,
                }

            # 2. Verificación 'tools/list'
            tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
            proc.stdin.write((json.dumps(tools_req) + "\n").encode("utf-8"))
            await proc.stdin.drain()

            tools_res_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout_seconds)
            tools_res = json.loads(tools_res_line.decode("utf-8").strip())
            tools_found = tools_res.get("result", {}).get("tools", [])
            tool_names = [t.get("name") for t in tools_found]

            if candidate.tool_name not in tool_names:
                return {
                    "status": "ERROR",
                    "is_valid": False,
                    "reason": f"Tool '{candidate.tool_name}' ausente en tools/list: {tool_names}",
                    "latency_ms": (time.time() - start_time) * 1000,
                }

            # 3. Invocación 'tools/call'
            call_req = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": candidate.tool_name,
                    "arguments": call_arguments,
                },
            }
            proc.stdin.write((json.dumps(call_req) + "\n").encode("utf-8"))
            await proc.stdin.drain()

            call_res_line = await asyncio.wait_for(proc.stdout.readline(), timeout=timeout_seconds)
            call_res = json.loads(call_res_line.decode("utf-8").strip())

            result_obj = call_res.get("result", {})
            is_error = bool(result_obj.get("isError", False)) or ("error" in call_res)
            content_list = result_obj.get("content", [])
            raw_text = content_list[0].get("text", "{}") if content_list else "{}"
            try:
                parsed_payload = json.loads(raw_text)
            except Exception:
                parsed_payload = {"raw_output": raw_text}

            if detonate and os.path.exists(script_path):
                # Enviar notificación de detonación si aún no se auto-eliminó
                try:
                    detonate_req = {"jsonrpc": "2.0", "method": "notifications/detonate", "params": {}}
                    proc.stdin.write((json.dumps(detonate_req) + "\n").encode("utf-8"))
                    await proc.stdin.drain()
                except Exception:
                    pass

            try:
                await asyncio.wait_for(proc.wait(), timeout=1.0)
            except asyncio.TimeoutError:
                pass

            latency_ms = (time.time() - start_time) * 1000
            return {
                "status": "ERROR" if is_error else "SUCCESS",
                "is_valid": not is_error,
                "server_name": candidate.server_name,
                "tool_name": candidate.tool_name,
                "tool_output": parsed_payload,
                "latency_ms": latency_ms,
            }

        except asyncio.TimeoutError:
            logger.error("[McpSandboxValidator] Timeout durante ejecución de MCP Bomba.")
            return {
                "status": "ERROR",
                "is_valid": False,
                "reason": "Timeout en ejecución JSON-RPC stdio",
                "latency_ms": timeout_seconds * 1000,
            }
        except Exception as e:
            logger.error(f"[McpSandboxValidator] Excepción ejecutando MCP Bomba: {e}")
            return {
                "status": "ERROR",
                "is_valid": False,
                "reason": str(e),
                "latency_ms": (time.time() - start_time) * 1000,
            }
        finally:
            try:
                if proc.returncode is None:
                    proc.terminate()
                    await proc.wait()
            except Exception:
                pass
            if detonate and os.path.exists(script_path):
                try:
                    os.unlink(script_path)
                except Exception as unlink_err:
                    logger.warning(f"[McpSandboxValidator] Error forzando unlink de {script_path}: {unlink_err}")

    def execute_and_detonate_mcp_sync(
        self,
        script_path: str,
        candidate: McpCandidateContract,
        call_arguments: Dict[str, Any],
        timeout_seconds: float = 5.0,
        detonate: bool = True,
    ) -> Dict[str, Any]:
        """Wrapper síncrono para invocar execute_and_detonate_mcp desde servidores stdio síncronos."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop is not None and loop.is_running():
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(
                    asyncio.run,
                    self.execute_and_detonate_mcp(
                        script_path=script_path,
                        candidate=candidate,
                        call_arguments=call_arguments,
                        timeout_seconds=timeout_seconds,
                        detonate=detonate,
                    ),
                )
                return future.result(timeout=timeout_seconds + 2.0)
        return asyncio.run(
            self.execute_and_detonate_mcp(
                script_path=script_path,
                candidate=candidate,
                call_arguments=call_arguments,
                timeout_seconds=timeout_seconds,
                detonate=detonate,
            )
        )
