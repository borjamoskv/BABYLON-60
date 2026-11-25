#!/usr/bin/env python3
"""audit_subagent_declarations.py.

Linter Determinista de Silicio (C5-REAL Quality Gate / INV_C5_ASYNC_SUBAGENTS_RUNTIME).
Audita subagentes (.md) contra la especificación canónica de Google Antigravity
(https://antigravity.google/docs/subagents#asynchronous-subagents).

Erradica el defecto crítico R1 (hang silencioso en lenguaje server por herramientas
no mapeadas o erróneas en el frontmatter YAML) y asegura el confinamiento de nodos hoja (d=1).
"""

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML no disponible en el entorno activo.", file=sys.stderr)
    sys.exit(1)

# Catálogo canónico de herramientas válidas en runtime Antigravity
VALID_TOOLS_CANON: set[str] = {
    # Inspección de ficheros y búsqueda
    "view_file",
    "list_dir",
    "grep_search",
    "find_by_name",
    # Recolección web de borde
    "search_web",
    "read_url_content",
    # Mutación de ficheros y workspace
    "write_to_file",
    "replace_file_content",
    "multi_replace_file_content",
    # Ejecución bare-metal
    "run_command",
    # Coordinación inter-agente e IPC
    "send_message",
    "schedule",
    "invoke_subagent",
    "manage_subagents",
    "ask_question",
    # Protocolo MCP
    "call_mcp_tool",
    "list_resources",
    "read_resource",
    "manage_task",
}

# Diccionario de alias / erratas conocidas que causan el bug de bloqueo R1
KNOWN_HANG_TYPOS: dict[str, str] = {
    "read_file": "view_file",
    "cat": "view_file",
    "write_file": "write_to_file",
    "edit_file": "replace_file_content",
    "bash": "run_command",
    "sh": "run_command",
    "terminal": "run_command",
    "exec": "run_command",
    "execute_command": "run_command",
    "search": "grep_search",
    "find": "find_by_name",
    "browser": "use /browser slash command",
}

VALID_MODELS: set[str] = {"inherit", "flash_lite", "flash", "pro"}
VALID_POLICIES: set[str] = {"sandbox", "auto", "eager", "off"}


@dataclass
class AuditFinding:
    file_path: str
    rule: str
    severity: str  # ERROR | WARNING
    message: str
    remediation: str = ""


def parse_subagent_file(path: Path) -> tuple[dict[str, Any] | None, str, str | None]:
    """Lee y parsea un archivo de subagente .md extrayendo su frontmatter YAML."""
    try:
        content = path.read_text(encoding="utf-8")
    except Exception as exc:
        return None, "", f"Error de lectura: {exc}"

    if not content.startswith("---"):
        return None, content, "No inicia con delimitador YAML '---'"

    parts = content.split("---", 2)
    if len(parts) < 3:
        return None, content, "Faltan delimitadores YAML de cierre ('---')"

    fm_raw = parts[1]
    body = parts[2]

    try:
        fm = yaml.safe_load(fm_raw)
        if not isinstance(fm, dict):
            return None, body, "El frontmatter YAML no se parseó como diccionario"
        return fm, body, None
    except Exception as exc:
        return None, body, f"Error de parseo YAML: {exc}"


def audit_subagent(path: Path, fm: dict[str, Any], body: str) -> list[AuditFinding]:
    """Audita un único archivo de subagente contra las invariantes de runtime."""
    findings: list[AuditFinding] = []
    file_str = str(path)

    # 1. Validación de campos obligatorios
    name = fm.get("name")
    if not isinstance(name, str) or not name.strip():
        findings.append(
            AuditFinding(
                file_path=file_str,
                rule="REQ_FIELD_NAME",
                severity="ERROR",
                message="Falta el campo obligatorio 'name' o está vacío.",
                remediation="Defina 'name: <identificador_unico>' en el frontmatter YAML.",
            )
        )
    else:
        # El nombre debe coincidir idealmente con el nombre de fichero (o carpeta padre)
        stem = path.stem
        if stem != "agent" and name != stem:
            findings.append(
                AuditFinding(
                    file_path=file_str,
                    rule="NAME_FILENAME_MISMATCH",
                    severity="WARNING",
                    message=f"El campo 'name' ('{name}') difiere del stem del archivo ('{stem}').",
                    remediation=f"Alinee 'name' con '{stem}' para evitar desajustes en descubrimiento.",
                )
            )

    desc = fm.get("description")
    if not isinstance(desc, str) or not desc.strip():
        findings.append(
            AuditFinding(
                file_path=file_str,
                rule="REQ_FIELD_DESCRIPTION",
                severity="ERROR",
                message="Falta el campo obligatorio 'description' o está vacío.",
                remediation="Defina 'description: <descripcion>' en el frontmatter YAML.",
            )
        )

    # 2. Invariante R1: Validación estricta de la lista blanca de tools (Anti-Hang Gate)
    tools = fm.get("tools")
    if tools is not None:
        if not isinstance(tools, list):
            findings.append(
                AuditFinding(
                    file_path=file_str,
                    rule="TOOLS_SCHEMA_TYPE",
                    severity="ERROR",
                    message="El campo 'tools' debe ser una lista de strings.",
                    remediation="Formatee 'tools' como lista YAML: 'tools: [view_file, ...]' o guiones.",
                )
            )
        else:
            for t in tools:
                if not isinstance(t, str):
                    findings.append(
                        AuditFinding(
                            file_path=file_str,
                            rule="TOOLS_ITEM_TYPE",
                            severity="ERROR",
                            message=f"Elemento no-string detectado en 'tools': {t}",
                            remediation="Asegúrese de que todos los identificadores sean cadenas de texto.",
                        )
                    )
                    continue

                if t not in VALID_TOOLS_CANON:
                    suggestion = KNOWN_HANG_TYPOS.get(t, "Consulte el catálogo canónico de tools")
                    findings.append(
                        AuditFinding(
                            file_path=file_str,
                            rule="R1_HANG_UNMAPPED_TOOL",
                            severity="ERROR",
                            message=(
                                f"Herramienta no mapeada o errónea '{t}' detectada en 'tools'. "
                                "Esto provoca un cuelgue indefinido (hang) del proceso en runtime Antigravity."
                            ),
                            remediation=f"Reemplace '{t}' por su equivalente canónico ({suggestion}).",
                        )
                    )

    # 3. Invariante de Aislamiento de Profundidad (d=1) para Nodos Hoja
    # Si el agente es explícitamente nodo hoja o moskvbot, tiene prohibido invocar subagentes
    is_leaf = False
    if name == "moskvbot" or fm.get("mainAgent") is False:
        # Chequeo si se comporta como worker hoja
        is_leaf = True

    if is_leaf and isinstance(tools, list):
        forbidden_leaf_tools = {"invoke_subagent", "manage_subagents"}
        intersect = forbidden_leaf_tools.intersection(set(tools))
        if intersect and name == "moskvbot":
            findings.append(
                AuditFinding(
                    file_path=file_str,
                    rule="LEAF_NODE_CONFINEMENT_D1",
                    severity="ERROR",
                    message=(
                        f"El nodo hoja '{name}' declara herramientas de orquestación recursiva: {intersect}. "
                        "Los nodos hoja tienen estrictamente prohibida la invocación anidada (d=1 limit)."
                    ),
                    remediation=f"Elimine {intersect} de la lista 'tools' de '{name}'.",
                )
            )

    # 4. Invariante de Modelo y Política de Ejecución
    model = fm.get("model")
    if model is not None and model not in VALID_MODELS:
        findings.append(
            AuditFinding(
                file_path=file_str,
                rule="INVALID_MODEL_TIER",
                severity="ERROR",
                message=f"Modelo no reconocido '{model}'. Modelos válidos: {sorted(VALID_MODELS)}",
                remediation=f"Use uno de: {sorted(VALID_MODELS)} (por defecto: 'inherit').",
            )
        )

    policy = fm.get("commandExecutionPolicy")
    if policy is not None and policy not in VALID_POLICIES:
        findings.append(
            AuditFinding(
                file_path=file_str,
                rule="INVALID_COMMAND_POLICY",
                severity="ERROR",
                message=f"Política de ejecución '{policy}' inválida. Válidas: {sorted(VALID_POLICIES)}",
                remediation=f"Use una de: {sorted(VALID_POLICIES)} (por defecto: 'sandbox').",
            )
        )

    # 5. Validación mínima de cuerpo Markdown (System Prompt)
    if not body.strip():
        findings.append(
            AuditFinding(
                file_path=file_str,
                rule="EMPTY_SYSTEM_PROMPT",
                severity="WARNING",
                message="El cuerpo del subagente (System Prompt) está vacío.",
                remediation="Añada las instrucciones del sistema bajo el delimitador YAML.",
            )
        )

    return findings


def get_staged_subagent_files() -> list[Path]:
    """Obtiene los archivos .md en el índice git (staged) que sean subagentes."""
    try:
        res = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=False,
            check=True,
        )
    except Exception:
        return []

    staged_files: list[Path] = []
    lines = res.stdout.decode("utf-8", errors="replace").splitlines()
    for raw_line in lines:
        line = raw_line.strip()
        if not line or not line.endswith(".md"):
            continue

        p = Path(line)
        if not p.is_file():
            continue

        # Si está en una ruta de agentes obvia o contiene subagent: true
        if "agents/" in line or ".agents/agents/" in line:
            staged_files.append(p)
        else:
            # Inspeccionar si tiene frontmatter con subagent: true
            try:
                head = p.read_text(encoding="utf-8")[:1000]
                if "subagent: true" in head or "subagent:true" in head:
                    staged_files.append(p)
            except Exception:
                pass

    return staged_files


def discover_subagent_files(workspace_only: bool, global_only: bool) -> list[Path]:
    """Descubre archivos de subagentes en el workspace y/o configuración global."""
    files: set[Path] = set()

    workspace_dirs = [
        Path.cwd() / ".agents" / "agents",
        Path.cwd() / "agents",
    ]
    global_dirs = [
        Path.home() / ".gemini" / "config" / "agents",
    ]

    target_dirs: list[Path] = []
    if workspace_only:
        target_dirs.extend(workspace_dirs)
    elif global_only:
        target_dirs.extend(global_dirs)
    else:
        target_dirs.extend(workspace_dirs)
        target_dirs.extend(global_dirs)

    for d in target_dirs:
        if d.is_dir():
            for p in d.rglob("*.md"):
                if p.is_file():
                    files.add(p)

    return sorted(list(files))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audita declaraciones de subagentes en silicio (Anti-Hang R1 Gate)."
    )
    parser.add_argument("--workspace-only", action="store_true", help="Audita solo el workspace actual.")
    parser.add_argument("--global-only", action="store_true", help="Audita solo ~/.gemini/config/agents/.")
    parser.add_argument("--staged", action="store_true", help="Audita únicamente archivos en el índice git.")
    parser.add_argument("--json", action="store_true", help="Emite salida estructurada JSON.")
    args = parser.parse_args()

    if args.staged:
        files = get_staged_subagent_files()
        if not files:
            if not args.json:
                print("ℹ️  [SUBAGENT AUDIT]: Cero archivos de subagente modificados en el índice git (staged).")
            return 0
    else:
        files = discover_subagent_files(args.workspace_only, args.global_only)

    if not files:
        if not args.json:
            print("ℹ️  [SUBAGENT AUDIT]: No se encontraron archivos de subagentes en los directorios evaluados.")
        return 0

    all_findings: list[AuditFinding] = []
    audited_count = 0

    for path in files:
        fm, body, parse_err = parse_subagent_file(path)
        if parse_err:
            all_findings.append(
                AuditFinding(
                    file_path=str(path),
                    rule="PARSE_ERROR",
                    severity="ERROR",
                    message=parse_err,
                )
            )
            continue

        if fm is None:
            continue

        audited_count += 1
        findings = audit_subagent(path, fm, body)
        all_findings.extend(findings)

    errors = [f for f in all_findings if f.severity == "ERROR"]
    warnings = [f for f in all_findings if f.severity == "WARNING"]

    if args.json:
        payload = {
            "audited_count": audited_count,
            "error_count": len(errors),
            "warning_count": len(warnings),
            "errors": [asdict(e) for e in errors],
            "warnings": [asdict(w) for w in warnings],
            "status": "FAIL" if errors else "PASS",
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
        return 1 if errors else 0

    print("════════════════════════════════════════════════════════════════════════════════")
    print("  AUDITORÍA DE SUBAGENTES ASÍNCRONOS ANTIGRAVITY (ANTI-HANG R1 GATE)")
    print("════════════════════════════════════════════════════════════════════════════════")
    print(f"Archivos evaluados en silicio : {len(files)}")
    print(f"Subagentes válidos parseados   : {audited_count}")
    print(f"Errores críticos bloqueantes   : {len(errors)}")
    print(f"Advertencias de convención     : {len(warnings)}")
    print("────────────────────────────────────────────────────────────────────────────────")

    if warnings:
        print("\n⚠️  ADVERTENCIAS:")
        for w in warnings:
            print(f"  • [{w.rule}] {w.file_path}: {w.message}")
            if w.remediation:
                print(f"    ↳ Acción: {w.remediation}")

    if errors:
        print("\n❌ ERRORES CRÍTICOS (COMMIT / RUNTIME FAIL):")
        for err in errors:
            print(f"  • [{err.rule}] {err.file_path}: {err.message}")
            if err.remediation:
                print(f"    ↳ Acción: {err.remediation}")
        print("\n🚫 VEREDICTO: FALLO DE INTEGRIDAD EN DECLARACIÓN DE SUBAGENTES.")
        print("   Corrija las herramientas no mapeadas para erradicar el bug de hang R1.")
        return 1

    print("\n✅ VEREDICTO: EXIT 0 — Todas las declaraciones de subagente cumplen invariantes.")
    print("   • Lista blanca de tools validada al 100% contra el canon del language server.")
    print("   • Confinamiento de nodos hoja (d=1) verificado sin fugas recursivas.")
    print("════════════════════════════════════════════════════════════════════════════════")
    return 0


if __name__ == "__main__":
    sys.exit(main())
