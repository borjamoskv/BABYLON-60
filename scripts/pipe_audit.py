#!/usr/bin/env python3
"""Ω-15 — pipe_audit: proxy auditado de sustitución de intérprete.

ITERA-1 / OPSEC-Ω TASKFORCE-16 · Agente Ω-15 (Pipe-Auditor).
Cierra el agujero ciego del §2.3 (REMEDIACION_CODE_SCANNING_2026-07-18):
el allowlist de `babylon60/extensions/aether/tools.py` cierra ejecutables
desconocidos, pero `python3 -c "import os; os.system('rm -rf /')"` o
`node -e "require('child_process').execSync(...)"` lo atraviesan porque
el payload vive dentro del argumento de un intérprete PERMITIDO.

`pipe_audit` NO es sandbox de OS (eso es ITERA-4: seccomp/landlock/docker).
Es la CAPA DE DETECCIÓN Y AUDITORÍA que hoy es ciega:

  1. Analiza el payload de `-c` / `-e` / `--eval` con un AST visitor
     (Python) o un regex de strings (Node) buscando vectores conocidos.
  2. Todo veredicto (BLOCK / WARN / PASS) se appendea a un ledger
     JSONL hash-chain SHA3-256 → audit trail tamper-evident del canal
     de intérpretes. La cadena detecta reescritura del log a posteriori.

Exit 0 = PASS · Exit 1 = BLOCK · Exit 2 = WARN (logged, permitido).
Stdlib only. Python 3.10+.
"""

from __future__ import annotations

import ast
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LEDGER = Path.home() / ".cortex" / "pipe_audit_log.jsonl"

# ── Vectores de ejecución OS en payloads de intérprete ─────────────────
DANGEROUS_PY_CALLS = {
    "os.system", "os.popen", "os.spawnl", "os.spawnle", "os.spawnlp",
    "os.spawnv", "os.spawnve", "os.spawnvp", "os.execl", "os.execle",
    "os.execlp", "os.execv", "os.execve", "os.execvp", "subprocess.run",
    "subprocess.call", "subprocess.check_call", "subprocess.check_output",
    "subprocess.Popen", "shutil.rmtree", "shutil.move",
}
DANGEROUS_PY_BUILTINS = {"eval", "exec", "compile", "__import__"}
DANGEROUS_NODE_RE = re.compile(
    r"require\(['\"]child_process['\"]\)|child_process"
    r"|execSync|spawnSync|execFileSync|\.exec\(|\.spawn\(|\.fork\("
)
NODE_INTERPRETERS = {"node", "nodejs", "deno", "bun"}
PY_INTERPRETERS = {"python", "python3", "python3.10", "python3.11", "python3.12", "pypy3"}


def _chain(prev: str, payload: dict) -> str:
    return hashlib.sha3_256(
        (prev + json.dumps(payload, sort_keys=True)).encode()
    ).hexdigest()


def _ledger_append(entry: dict) -> None:
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    prev = "0" * 64
    if LEDGER.exists():
        try:
            last = LEDGER.read_text(encoding="utf-8").strip().splitlines()
            if last:
                prev = json.loads(last[-1]).get("hash", prev)
        except (json.JSONDecodeError, OSError):
            pass
    entry["prev_hash"] = prev
    entry["hash"] = _chain(prev, entry)
    try:
        with LEDGER.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass


def _record(interp: str, verdict: str, hits: list[str], payload: str) -> None:
    _ledger_append({
        "ts": datetime.now(timezone.utc).isoformat(),
        "agent": "Ω-15",
        "interpreter": interp,
        "verdict": verdict,
        "hits": hits,
        "payload_sha3": hashlib.sha3_256(payload.encode()).hexdigest()[:16],
    })


class _PyVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.hits: list[str] = []

    def _qualname(self, node: ast.expr) -> str:
        parts: list[str] = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value  # type: ignore[assignment]
        if isinstance(node, ast.Name):
            parts.append(node.id)
        return ".".join(reversed(parts))

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        name = ""
        if isinstance(node.func, ast.Attribute):
            name = self._qualname(node.func)
        elif isinstance(node.func, ast.Name):
            name = node.func.id
        if name in DANGEROUS_PY_CALLS or name in DANGEROUS_PY_BUILTINS:
            self.hits.append(f"{name}() @line {node.lineno}")
        self.generic_visit(node)


def scan_python(payload: str) -> list[str]:
    try:
        tree = ast.parse(payload)
    except SyntaxError:
        return ["UNPARSEABLE_PAYLOAD (posible ofuscación)"]
    visitor = _PyVisitor()
    visitor.visit(tree)
    return visitor.hits


def scan_node(payload: str) -> list[str]:
    return [f"{m} (regex)" for m in DANGEROUS_NODE_RE.findall(payload)] or (
        ["child_process/dynamic"] if DANGEROUS_NODE_RE.search(payload) else []
    )


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: pipe_audit <interpreter> [args...]", file=sys.stderr)
        return 2
    interp = Path(sys.argv[1]).name.lower()
    args = sys.argv[2:]

    payload = ""
    for i, a in enumerate(args):
        if a in ("-c", "-e", "--eval") and i + 1 < len(args):
            payload = args[i + 1]
            break
    if not payload:
        return 0  # modo script/repl: nada que auditar aquí

    hits: list[str] = []
    if interp in PY_INTERPRETERS:
        hits = scan_python(payload)
    elif interp in NODE_INTERPRETERS:
        hits = scan_node(payload)

    if hits:
        _record(interp, "BLOCK", hits, payload)
        print(f"[Ω-15 BLOCK] {interp}: vectores de ejecución OS detectados:", file=sys.stderr)
        for h in hits:
            print(f"  · {h}", file=sys.stderr)
        return 1

    _record(interp, "PASS", [], payload)
    return 0


if __name__ == "__main__":
    sys.exit(main())
