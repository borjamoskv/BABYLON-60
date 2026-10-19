"""
BABYLON-60 Dynamic MCP Code Scaffolder (C5-REAL)
Generador e Implementador de Servidores MCP Efímeros («MCP Bomba») y Persistentes
"""

import ast
import hashlib
import json
import logging
import os
import textwrap
from typing import Optional, Set

from .mcp_deductive_engine import McpCandidateContract

logger = logging.getLogger(__name__)

FORBIDDEN_AST_MODULES: Set[str] = {
    "subprocess",
    "pty",
    "socket",
    "ctypes",
    "urllib",
    "http",
    "ftplib",
    "telnetlib",
    "shutil",
    "webbrowser",
    "multiprocessing",
}

FORBIDDEN_AST_CALLS: Set[str] = {
    "eval",
    "exec",
    "compile",
    "__import__",
    "open",
    "system",
    "popen",
    "spawnl",
    "spawnle",
    "spawnlp",
    "spawnlpe",
    "spawnv",
    "spawnve",
    "spawnvp",
    "spawnvpe",
    "execl",
    "execle",
    "execlp",
    "execlpe",
    "execv",
    "execve",
    "execvp",
    "execvpe",
    "remove",
    "unlink",
    "rmdir",
    "rmtree",
}


def compute_code_hash(code: str) -> str:
    """Calcula el digest canónico BLAKE3 (INV_C5_ONWIRE_CANON) del código sintetizado."""
    raw = code.encode("utf-8")
    try:
        from blake3 import blake3

        return str(blake3(raw).hexdigest())
    except ImportError:
        return hashlib.sha256(raw).hexdigest()


class McpCodeScaffolder:
    """
    Sintetiza el código ejecutable de un servidor MCP a partir de un candidato McpCandidateContract.
    Soporta inyección de lógica real validada por AST y autodestrucción (Burn-After-Use / MCP Bomba).
    """

    def __init__(self, output_dir: Optional[str] = None) -> None:
        if output_dir is None:
            base = os.environ.get(
                "BABYLON_HOME",
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))),
            )
            output_dir = os.path.join(base, "scratch", "dynamic_mcps")
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    @staticmethod
    def validate_implementation_ast(implementation_body: str) -> None:
        """
        Valida sintáctica y semánticamente el cuerpo de la herramienta antes de sintetizar el MCP.
        Bloquea primitivas de escape de sandbox o ejecución arbitraria de subprocesos (AX-0 / FL-008).
        """
        clean_body = textwrap.dedent(implementation_body).strip()
        if not clean_body:
            raise ValueError("[AX-0 AST GATE] El cuerpo de implementación (implementation_body) no puede estar vacío.")

        wrapped_source = "def _sandbox_probe():\n" + textwrap.indent(clean_body, "    ") + "\n"
        try:
            tree = ast.parse(wrapped_source)
        except SyntaxError as exc:
            raise ValueError(f"[AX-0 AST GATE] Error de sintaxis en implementation_body: {exc}") from exc

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root_mod = alias.name.split(".")[0]
                    if root_mod in FORBIDDEN_AST_MODULES or root_mod == "os":
                        raise ValueError(f"[AX-0 AST GATE] Importación prohibida en MCP Bomba: '{alias.name}'")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    root_mod = node.module.split(".")[0]
                    if root_mod in FORBIDDEN_AST_MODULES or root_mod == "os":
                        raise ValueError(f"[AX-0 AST GATE] Importación desde módulo prohibido: '{node.module}'")
            elif isinstance(node, ast.Call):
                func_name = None
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr
                if func_name in FORBIDDEN_AST_CALLS:
                    raise ValueError(f"[AX-0 AST GATE] Llamada a primitiva prohibida en MCP Bomba: '{func_name}()'")
            elif isinstance(node, ast.Attribute):
                if node.attr.startswith("__") and node.attr.endswith("__"):
                    raise ValueError(f"[AX-0 AST GATE] Acceso a atributo dunder prohibido: '{node.attr}'")

    def scaffold_fastmcp_python(self, contract: McpCandidateContract, custom_filename: Optional[str] = None) -> str:
        """
        Genera un archivo de servidor MCP en Python con protocolo stdio JSON-RPC 2.0 y autodestrucción opcional.
        """
        filename = custom_filename or f"mcp_{contract.server_name.lower()}_server.py"
        file_path = os.path.join(self.output_dir, filename)

        # Construir argumentos de la función
        func_params = []
        for param in contract.parameters:
            py_type = "Any"
            if param.param_type == "string":
                py_type = "str"
            elif param.param_type == "integer":
                py_type = "int"
            elif param.param_type == "number":
                py_type = "float"
            elif param.param_type == "boolean":
                py_type = "bool"
            elif param.param_type == "object":
                py_type = "dict"
            func_params.append(f"{param.name}: {py_type} = None")

        params_signature = ", ".join(func_params)
        schema_json_str = json.dumps(contract.to_json_schema())
        received_args_dict = ", ".join([f'"{p.name}": {p.name}' for p in contract.parameters])

        if contract.implementation_body:
            self.validate_implementation_ast(contract.implementation_body)
            dedented_body = textwrap.dedent(contract.implementation_body).strip()
            indented_user_logic = textwrap.indent(dedented_body, "    ")
        else:
            indented_user_logic = '    return "Operación ejecutada con alta exergía"'

        code = f'''"""
Servidor MCP Autónomo Generado por Babylon60 McpCodeScaffolder (C5-REAL)
Servidor: {contract.server_name}
Herramienta: {contract.tool_name}
Max Invocations (Burn-After-Use): {contract.max_invocations}
"""

import json
import logging
import math
import os
import re
import sys
from typing import Any

logging.basicConfig(level=logging.INFO, stream=sys.stderr)

MAX_INVOCATIONS = {int(contract.max_invocations)}
_INVOCATION_COUNT = 0


def _user_impl({params_signature}) -> Any:
{indented_user_logic}


def {contract.tool_name}({params_signature}) -> dict:
    """{contract.description}"""
    logging.info("Ejecutando {contract.tool_name} con parámetros recibidos.")
    computed = _user_impl({", ".join([f"{p.name}={p.name}" for p in contract.parameters])})
    return {{
        "status": "SUCCESS",
        "server": "{contract.server_name}",
        "tool": "{contract.tool_name}",
        "result": computed,
        "received_args": {{{received_args_dict}}},
    }}


def _self_destruct() -> bool:
    """Autodestrucción física del script efímero (Burn-After-Use / Cero Huella)."""
    try:
        script_file = os.path.abspath(__file__)
        if os.path.exists(script_file):
            os.unlink(script_file)
            logging.info(f"[MCP-BOMBA] Autodestrucción completada: {{script_file}}")
            return True
    except Exception as exc:
        logging.warning(f"[MCP-BOMBA] Fallo en autodestrucción: {{exc}}")
    return False


def handle_request(line: str) -> bool:
    """Procesa una línea JSON-RPC 2.0. Devuelve False si el servidor debe autodestruirse y salir."""
    global _INVOCATION_COUNT
    try:
        req = json.loads(line)
        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params") or {{}}

        if method in ("notifications/initialized", "initialized"):
            return True

        if method == "notifications/detonate":
            _self_destruct()
            return False

        if method == "initialize":
            res = {{
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {{
                    "protocolVersion": "2024-11-05",
                    "capabilities": {{"tools": {{}}}},
                    "serverInfo": {{
                        "name": "{contract.server_name}",
                        "version": "1.0.0",
                        "ephemeral_bomb": MAX_INVOCATIONS > 0,
                        "max_invocations": MAX_INVOCATIONS,
                    }},
                }},
            }}
        elif method == "ping":
            res = {{"jsonrpc": "2.0", "id": req_id, "result": {{}}}}
        elif method == "tools/list":
            res = {{
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {{
                    "tools": [
                        {{
                            "name": "{contract.tool_name}",
                            "description": {json.dumps(contract.description)},
                            "inputSchema": {schema_json_str},
                        }}
                    ]
                }},
            }}
        elif method == "tools/call":
            call_args = params.get("arguments") or {{}}
            filtered_kwargs = {{
                k: v for k, v in call_args.items() if k in {json.dumps([p.name for p in contract.parameters])}
            }}
            try:
                payload = {contract.tool_name}(**filtered_kwargs)
                _INVOCATION_COUNT += 1
                should_detonate = MAX_INVOCATIONS > 0 and _INVOCATION_COUNT >= MAX_INVOCATIONS
                payload["invocations_used"] = _INVOCATION_COUNT
                payload["self_destruct_triggered"] = should_detonate
                res = {{
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {{
                        "content": [
                            {{
                                "type": "text",
                                "text": json.dumps(payload, ensure_ascii=False),
                            }}
                        ],
                        "isError": False,
                    }},
                }}
            except Exception as tool_exc:
                _INVOCATION_COUNT += 1
                should_detonate = MAX_INVOCATIONS > 0 and _INVOCATION_COUNT >= MAX_INVOCATIONS
                res = {{
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {{
                        "content": [
                            {{
                                "type": "text",
                                "text": json.dumps(
                                    {{
                                        "status": "ERROR",
                                        "server": "{contract.server_name}",
                                        "tool": "{contract.tool_name}",
                                        "error": str(tool_exc),
                                        "self_destruct_triggered": should_detonate,
                                    }},
                                    ensure_ascii=False,
                                ),
                            }}
                        ],
                        "isError": True,
                    }},
                }}
            sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\\n")
            sys.stdout.flush()
            if should_detonate:
                _self_destruct()
                return False
            return True
        else:
            res = {{
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {{"code": -32601, "message": f"Method not found: {{method}}"}},
            }}

        sys.stdout.write(json.dumps(res, ensure_ascii=False) + "\\n")
        sys.stdout.flush()
        return True
    except Exception as e:
        logging.error(f"Error procesando JSON-RPC: {{e}}")
        return True


if __name__ == "__main__":
    for raw_line in sys.stdin:
        stripped = raw_line.strip()
        if stripped:
            keep_alive = handle_request(stripped)
            if not keep_alive:
                break
'''
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"[McpCodeScaffolder] Código MCP sintetizado exitosamente en '{file_path}'")
        return file_path
