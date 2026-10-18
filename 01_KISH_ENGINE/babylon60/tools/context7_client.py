#!/usr/bin/env python3
"""
Cliente Soberano Zero-Dependency para Context7 MCP (Upstash).
Comunica vía JSON-RPC sobre stdio contra el paquete local en /opt/homebrew.
Permite resolución de bibliotecas y consulta de documentación oficial sin arrastre de contexto.
"""

import sys
import json
import subprocess
import argparse
from typing import Dict, Any

MCP_ENTRYPOINT = "/opt/homebrew/lib/node_modules/@upstash/context7-mcp/dist/index.js"


class Context7Client:
    def __init__(self, entrypoint: str = MCP_ENTRYPOINT) -> None:
        self.entrypoint = entrypoint

    def _call_tool(self, name: str, arguments: Dict[str, Any], timeout: int = 15) -> Dict[str, Any]:
        proc = subprocess.Popen(
            ["node", self.entrypoint],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        try:
            if proc.stdin is None or proc.stdout is None or proc.stderr is None:
                raise RuntimeError("Context7 MCP pipes were not initialized")
            init_req = (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "initialize",
                        "params": {
                            "protocolVersion": "2024-11-05",
                            "capabilities": {},
                            "clientInfo": {"name": "c5-context7-client", "version": "1.0.0"},
                        },
                    }
                )
                + "\n"
            )
            proc.stdin.write(init_req)
            proc.stdin.flush()

            # Leer respuesta de initialize
            resp_init_line = proc.stdout.readline()
            if not resp_init_line:
                err = proc.stderr.read()
                raise RuntimeError(f"Context7 MCP falló en inicialización: {err}")

            # Notificar initialized
            notif_init = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized"}) + "\n"
            proc.stdin.write(notif_init)

            # Llamar tool
            call_req = (
                json.dumps(
                    {
                        "jsonrpc": "2.0",
                        "id": 2,
                        "method": "tools/call",
                        "params": {"name": name, "arguments": arguments},
                    }
                )
                + "\n"
            )
            proc.stdin.write(call_req)
            proc.stdin.flush()

            # Leer respuesta de tools/call
            resp_line = proc.stdout.readline()
            if not resp_line:
                err = proc.stderr.read()
                raise RuntimeError(f"Context7 MCP no devolvió respuesta: {err}")

            data = json.loads(resp_line)
            if "error" in data:
                raise RuntimeError(f"Context7 Error: {data['error']}")
            if not isinstance(data, dict):
                raise RuntimeError("Context7 MCP response must be an object")
            result = data.get("result", {})
            if not isinstance(result, dict):
                raise RuntimeError("Context7 MCP result must be an object")
            return result
        finally:
            try:
                proc.kill()
            except Exception:
                pass

    def resolve_library(self, library_name: str, query: str = "") -> Dict[str, Any]:
        """Resuelve el ID canónico de Context7 para una biblioteca dada."""
        q = query or f"Documentación y especificaciones de {library_name}"
        return self._call_tool("resolve-library-id", {"libraryName": library_name, "query": q})

    def query_docs(self, library_id: str, query: str) -> Dict[str, Any]:
        """Consulta fragmentos de documentación oficial versionada."""
        return self._call_tool("query-docs", {"libraryId": library_id, "query": query})


def main() -> None:
    parser = argparse.ArgumentParser(description="Context7 Sovereign MCP CLI")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # resolve
    p_res = subparsers.add_parser("resolve", help="Resolver ID canónico de biblioteca")
    p_res.add_argument("library", help="Nombre de la biblioteca (ej: Next.js, PyTorch, React)")
    p_res.add_argument("--query", "-q", default="", help="Contexto o consulta para afinar ranking")

    # query
    p_query = subparsers.add_parser("docs", help="Consultar documentación oficial")
    p_query.add_argument("library_id", help="ID canónico (ej: /vercel/next.js o /facebook/react)")
    p_query.add_argument("query", help="Pregunta o concepto específico a documentar")

    args = parser.parse_args()
    client = Context7Client()

    try:
        if args.subcommand == "resolve":
            res = client.resolve_library(args.library, args.query)
            print(json.dumps(res, indent=2, ensure_ascii=False))
        elif args.subcommand == "docs":
            res = client.query_docs(args.library_id, args.query)
            # Imprimir contenido limpio
            content_items = res.get("content", [])
            for item in content_items:
                if item.get("type") == "text":
                    print(item.get("text", ""))
                else:
                    print(json.dumps(item, indent=2, ensure_ascii=False))
    except Exception as e:
        sys.stderr.write(f"Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
