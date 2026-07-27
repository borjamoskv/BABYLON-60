"""
cat_id: generate-ecosystem-map
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P1
"""

import logging


from __future__ import annotations

import ast
import os
import sqlite3
from pathlib import Path

HOME = Path.home()
WORKSPACE = Path(__file__).parent.parent.resolve()
CORTEX_DIR = HOME / ".cortex"
DB_DIR = CORTEX_DIR

# DB paths to map
DB_FILES = {
    "runtime.db": DB_DIR / "runtime.db",
    "nexus.db": DB_DIR / "nexus.db",
    "budget.db": DB_DIR / "budget.db",
    "quota.db": DB_DIR / "quota.db",
    "pulmones.db": DB_DIR / "pulmones.db",
    "vectors.db": DB_DIR / "vectors.db",
}

DEPENDENCIES = [
    "sqlite_vec",
    "aiosqlite",
    "click",
    "rich",
    "pydantic",
    "fastapi",
    "starlette",
    "uvicorn",
    "httpx",
    "mcp",
    "sentence_transformers",
    "onnxruntime",
]


def map_databases() -> str:
    """Connect to SQLite databases and dump schemas, tables, and row counts."""
    md = ["## 🗄️ Database Schemas & Metrics Mapping\n"]

    for db_name, db_path in DB_FILES.items():
        if not db_path.exists():
            md.append(f"### `{db_name}`\n* Status: **Offline (File not found)**\n")
            continue

        md.append(f"### `{db_name}`\n")
        md.append(f"* Path: `{db_path}`")
        md.append(f"* Size: **{db_path.stat().st_size / 1024:.1f} KB**\n")

        try:
            conn = sqlite3.connect(str(db_path))

            # Load sqlite_vec if possible
            try:
                import sqlite_vec

                conn.enable_load_extension(True)
                conn.load_extension(sqlite_vec.loadable_path())
                conn.enable_load_extension(False)
            except Exception as err:  # noqa: BLE001
                logging.getLogger(__name__).info(f"Could not load sqlite-vec extension: {err}")

            cursor = conn.cursor()

            # Get tables
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
            )
            tables = [row[0] for row in cursor.fetchall()]

            if not tables:
                md.append("No active user tables found.\n")
                conn.close()
                continue

            md.append("| Table Name | Columns | Est. Rows |")
            md.append("|:---|:---|:---|")

            table_schemas = []

            for t in sorted(tables):
                try:
                    # Count rows
                    cursor.execute(f'SELECT COUNT(*) FROM "{t}";')
                    row_count = cursor.fetchone()[0]

                    # Columns info
                    cursor.execute(f'PRAGMA table_info("{t}");')
                    cols = cursor.fetchall()
                    col_names = [f"`{c[1]}` ({c[2]})" for c in cols]
                    col_str = ", ".join(col_names[:5])
                    if len(col_names) > 5:
                        col_str += f" (+{len(col_names) - 5} more)"

                    md.append(f"| `{t}` | {col_str} | **{row_count}** |")

                    # Retrieve SQL Schema creation statement
                    cursor.execute(
                        f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{t}';"
                    )
                    sql = cursor.fetchone()
                    if sql and sql[0]:
                        table_schemas.append(f"#### Table `{t}`\n```sql\n{sql[0].strip()}\n```")
                except Exception as table_err:  # noqa: BLE001
                    md.append(f"| `{t}` | *Error mapping table:* `{table_err}` | N/A |")

            md.append("\n" + "\n".join(table_schemas) + "\n")
            conn.close()
        except Exception as e:  # noqa: BLE001
            md.append(f"*Error reading database:* `{e}`\n")

    return "\n".join(md)


def extract_routes(filepath: Path) -> list[dict]:
    routes = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute):
                        if dec.func.attr in (
                            "get",
                            "post",
                            "put",
                            "delete",
                            "patch",
                            "options",
                            "head",
                        ):
                            path = ""
                            if dec.args and isinstance(dec.args[0], ast.Constant):
                                path = dec.args[0].value
                            elif dec.args and isinstance(dec.args[0], ast.Str):
                                path = dec.args[0].s

                            routes.append(
                                {
                                    "file": filepath.name,
                                    "method": dec.func.attr.upper(),
                                    "path": path or "/",
                                    "handler": node.name,
                                    "desc": (ast.get_docstring(node) or "No description.").split(
                                        "\n"
                                    )[0],
                                }
                            )
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"Error parsing routes in {filepath.name}: {e}")
    return routes


def map_routes() -> str:
    """Scan routes folder and map all FastAPI routes."""
    routes_dir = WORKSPACE / "babylon60" / "routes"
    md = ["## 🌐 HTTP / API Routes Mapping\n"]

    if not routes_dir.exists():
        md.append("Routes folder `babylon60/routes` not found.\n")
        return "\n".join(md)

    all_routes = []
    for f in sorted(routes_dir.glob("*.py")):
        if f.name == "__init__.py":
            continue
        all_routes.extend(extract_routes(f))

    if not all_routes:
        md.append("No routes detected.\n")
        return "\n".join(md)

    md.append(f"Scanned **{len(all_routes)}** active endpoints.\n")
    md.append("| Method | Endpoint Path | Handler | File | Description |")
    md.append("|:---|:---|:---|:---|:---|")

    # Sort by path then method
    all_routes.sort(key=lambda x: (x["path"], x["method"]))
    for r in all_routes:
        md.append(
            f"| `{r['method']}` | **`{r['path']}`** | `{r['handler']}` | `{r['file']}` | {r['desc']} |"
        )

    return "\n".join(md) + "\n"


def extract_cli(filepath: Path) -> list[dict]:
    cmds = []
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    name = ""
                    cmd_type = "command"
                    is_click = False

                    if isinstance(dec, ast.Call):
                        func = dec.func
                        if isinstance(func, ast.Attribute):
                            if func.attr in ("command", "group"):
                                is_click = True
                                cmd_type = func.attr
                            elif (
                                isinstance(func.value, ast.Name)
                                and func.value.id == "click"
                                and func.attr in ("command", "group")
                            ):
                                is_click = True
                                cmd_type = func.attr
                        elif isinstance(func, ast.Name):
                            if func.id in ("command", "group"):
                                is_click = True
                                cmd_type = func.id

                        if is_click:
                            if dec.args and isinstance(dec.args[0], ast.Constant):
                                name = dec.args[0].value
                            elif dec.args and isinstance(dec.args[0], ast.Str):
                                name = dec.args[0].s
                            elif dec.keywords:
                                for kw in dec.keywords:
                                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                                        name = kw.value.value
                                    elif kw.arg == "name" and isinstance(kw.value, ast.Str):
                                        name = kw.value.s

                    elif isinstance(dec, ast.Name) and dec.id in ("command", "group"):
                        is_click = True
                        cmd_type = dec.id

                    if is_click:
                        if not name:
                            name = (
                                node.name.replace("_cmd", "").replace("_cmds", "").replace("_", "-")
                            )
                        cmds.append(
                            {
                                "file": filepath.name,
                                "type": cmd_type.upper(),
                                "name": name,
                                "handler": node.name,
                                "desc": (ast.get_docstring(node) or "").split("\n")[0]
                                or "No description.",
                            }
                        )
                        break
    except Exception as e:  # noqa: BLE001
        logging.getLogger(__name__).info(f"Error parsing CLI in {filepath.name}: {e}")
    return cmds


def map_cli() -> str:
    """Scan CLI commands and map them."""
    cli_dir = WORKSPACE / "babylon60" / "cli"
    md = ["## 💻 CLI Commands Mapping\n"]

    if not cli_dir.exists():
        md.append("CLI folder `babylon60/cli` not found.\n")
        return "\n".join(md)

    all_cmds = []
    for f in sorted(cli_dir.glob("*.py")):
        if f.name in ("__init__.py", "common.py", "errors.py"):
            continue
        all_cmds.extend(extract_cli(f))

    if not all_cmds:
        md.append("No CLI commands detected.\n")
        return "\n".join(md)

    md.append(f"Scanned **{len(all_cmds)}** registered CLI entrypoints.\n")
    md.append("| Type | Command | Handler | File | Description |")
    md.append("|:---|:---|:---|:---|:---|")

    all_cmds.sort(key=lambda x: (x["type"], x["name"]))
    for c in all_cmds:
        md.append(
            f"| `{c['type']}` | **`{c['name']}`** | `{c['handler']}` | `{c['file']}` | {c['desc']} |"
        )

    return "\n".join(md) + "\n"


def map_dependencies() -> str:
    """Trace all import frequencies of core third-party dependencies."""
    md = ["## 📦 Package Dependency & Coupling Map\n"]

    mapping = {dep: [] for dep in DEPENDENCIES}
    search_dirs = [WORKSPACE / "babylon60", WORKSPACE / "cortex"]

    py_files_count = 0
    for s_dir in search_dirs:
        if not s_dir.exists():
            continue
        for root, _, files in os.walk(s_dir):
            for file in files:
                if file.endswith(".py"):
                    py_files_count += 1
                    path = Path(root) / file
                    try:
                        content = path.read_text(encoding="utf-8")
                        tree = ast.parse(content, filename=str(path))
                        for node in ast.walk(tree):
                            base = None
                            if isinstance(node, ast.Import):
                                for alias in node.names:
                                    base = alias.name.split(".")[0]
                                    if base in mapping:
                                        mapping[base].append(path.relative_to(WORKSPACE))
                            elif isinstance(node, ast.ImportFrom):
                                if node.module:
                                    base = node.module.split(".")[0]
                                    if base in mapping:
                                        mapping[base].append(path.relative_to(WORKSPACE))
                    except Exception:  # noqa: BLE001
                        continue

    md.append(f"Analyzed **{py_files_count}** Python files in `babylon60/` and `cortex/`.\n")
    md.append("| Package Name | Import Count | Coupling Density |")
    md.append("|:---|:---|:---|")

    for dep in sorted(DEPENDENCIES):
        files = sorted(list(set(mapping[dep])))
        density = (len(files) / py_files_count * 100) if py_files_count > 0 else 0
        md.append(f"| `{dep}` | {len(files)} files | **{density:.1f}%** |")

    md.append("\n### Detailed Package Import Mappings\n")
    for dep in sorted(DEPENDENCIES):
        files = sorted(list(set(mapping[dep])))
        md.append(f"#### `{dep}` imports ({len(files)} files)")
        if not files:
            md.append("- No occurrences found.\n")
        else:
            for f in files[:15]:
                md.append(f"- `{f}`")
            if len(files) > 15:
                md.append(f"- *...and {len(files) - 15} more files*")
            md.append("")

    return "\n".join(md)


def map_swarm() -> str:
    """Parse LEGION-93 mapping data and verify compliance."""
    mapping_file = WORKSPACE / "docs" / "design" / "LEGION_93_MAPPING.md"
    md = ["## 🔱 Swarm Nodes Mapping (LEGION-93)\n"]

    if not mapping_file.exists():
        md.append("Swarm nodes mapping file `docs/design/LEGION_93_MAPPING.md` not found.\n")
        return "\n".join(md)

    try:
        content = mapping_file.read_text(encoding="utf-8")
        rows = []
        for line in content.splitlines():
            if (
                "|" in line
                and not line.strip().startswith("|-")
                and not line.strip().startswith("| #")
                and not line.strip().startswith("| ID")
            ):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if len(parts) >= 6:
                    rows.append(parts)

        md.append(
            f"Scanned **{len(rows)}** defined agent identities matching the LEGION-93 swarm topology.\n"
        )
        md.append("| ID Nodo | Identidad Cognitiva | Exergy | Realidad | Intent | Payload Model |")
        md.append("|:---|:---|:---|:---|:---|:---|")

        for r in rows:
            md.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} | {r[6]} |")
    except Exception as e:  # noqa: BLE001
        md.append(f"*Error parsing LEGION-93 mapping file:* `{e}`\n")

    return "\n".join(md) + "\n"


def main():
    logging.getLogger(__name__).info("Compiling Master Cognitive Ecosystem Map...")

    md_header = [
        "# 🗺️ COGNITIVE ECOSYSTEM MAP — BABYLON-60",
        "",
        '> **"CERO ANERGÍA ES LA MUERTE."** — Cristalizado bajo la soberanía de **Borja Moskv** (Γ1)',
        "",
        "* **Reality Level**: C5-REAL (Full AST Extraction + Dynamic Schema Query)",
        "* **Audit Date**: 2026-07-06",
        "* **Subprocess Kernel**: `tools/generate_ecosystem_map.py` v1.0.0",
        "",
        "---",
        "",
    ]

    sections = [map_databases(), map_routes(), map_cli(), map_swarm(), map_dependencies()]

    full_md = "\n\n".join(md_header + sections)

    # Save to docs/design/COGNITIVE_ECOSYSTEM_MAP.md
    out_docs = WORKSPACE / "docs" / "design" / "COGNITIVE_ECOSYSTEM_MAP.md"
    out_docs.parent.mkdir(parents=True, exist_ok=True)
    out_docs.write_text(full_md, encoding="utf-8")
    logging.getLogger(__name__).info(f"Ecosystem map written to {out_docs}")

    # Save to current conversation artifacts directory
    session_id = "e857993e-3117-4ca9-903f-b14614e44cc9"
    out_session = (
        Path("/Users/borjafernandezangulo/.gemini/antigravity/brain")
        / session_id
        / "ecosystem_mapping.md"
    )
    out_session.parent.mkdir(parents=True, exist_ok=True)
    out_session.write_text(full_md, encoding="utf-8")
    logging.getLogger(__name__).info(f"Ecosystem map written to session artifact: {out_session}")


if __name__ == "__main__":
    main()
