#!/usr/bin/env python3
"""Generate portable skill distributions from tools/skill_library; no procedures executed."""

from pathlib import Path
import argparse
import json
import os
import re
import shutil
import yaml
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools.skill_library.router import RouteIntent, RouteRecord

ROOT = Path(__file__).absolute().parents[2]
SOURCE = ROOT / "tools/skill_library"
EXCLUDE = shutil.ignore_patterns("__pycache__", "_archive", "archive", ".git", "node_modules")
LAUNCHER = """#!/usr/bin/env python3
# Generated from tools/skill_library/router.py; edit the canonical source.
import runpy
from pathlib import Path
import sys
hub = Path(__file__).absolute().parent.parent
sys.argv.extend(['--hub-root', str(hub)])
runpy.run_path(str(hub.parent / '_skill_router.py'), run_name='__main__')
"""


def build(destination: Path, environment: str) -> None:
    destination.mkdir(parents=True, exist_ok=False)
    catalog = json.loads((SOURCE / "catalog.json").read_text())
    scopes = ["workspace"] if environment == "workspace" else ["global"]
    if environment == "codex":
        scopes.append("codex_overrides")
    if catalog["version"] != 2:
        raise ValueError("Unsupported canonical catalog version")
    generic = set(catalog["policy"]["generic"])
    if catalog["policy"].get("automatic_execution") is not False:
        raise ValueError("Automatic procedure execution is not supported")
    metadata = {}
    capabilities = {}
    for scope in scopes:
        shutil.copytree(SOURCE / scope, destination, dirs_exist_ok=True, ignore=EXCLUDE)
        metadata.update(catalog["scopes"][scope])
        capabilities.update(catalog["capabilities"][scope])
    shutil.copy2(SOURCE / "router.py", destination / "_skill_router.py")
    shutil.copytree(SOURCE / "checks", destination / "_skill_checks")
    aliases = {}
    hubs: dict[Path, list[RouteRecord]] = {}
    for name, capability in sorted(capabilities.items()):
        if "module" not in capability:
            continue
        route = capability["module"]
        hub = destination / route["hub"]
        intent: RouteIntent = capability["intent"].copy()
        intent.setdefault("actions", catalog["policy"]["default_actions"])
        module: RouteRecord = {
            "name": name,
            "aliases": capability["aliases"],
            "module": route["path"],
            "intent": intent,
        }
        relative = Path(route["path"])
        if relative.is_absolute() or ".." in relative.parts or not (hub / relative).is_file():
            raise ValueError(f"Missing or unconfined procedure: {relative}")
        aliases[name] = (hub, module)
        hubs.setdefault(hub, []).append(module)
    for hub, modules in hubs.items():
        table = hub / "references/aliases.json"
        table.parent.mkdir(parents=True, exist_ok=True)
        table.write_text(json.dumps({"version": 2, "modules": modules}, ensure_ascii=False, indent=2) + "\n")
        (hub / "scripts").mkdir(exist_ok=True)
        (hub / "scripts/route.py").write_text(LAUNCHER)
        (hub / "scripts/route.py").chmod(0o755)
    for name, fm in metadata.items():
        entry = destination / name / "SKILL.md"
        text = entry.read_text()
        body = text.split("---", 2)[2]
        description = fm["description"]
        for trigger in sorted(generic):
            description = re.sub(r'["\']' + re.escape(trigger) + r'["\'],?\s*', "", description, flags=re.I)
        fm = dict(fm, description=description)
        metadata[name] = fm
        if name in aliases:
            hub, module = aliases[name]
            target = os.path.relpath(hub / module["module"], entry.parent)
            body = (
                "\n\n# "
                + name
                + "\n\n> **Directiva Declarativa:** Alias generado; conserva rol y alcance del módulo.\n\nLee [el procedimiento especializado]("
                + target
                + ") solo cuando la petición requiera este dominio. Una coincidencia genérica como «itera», «sigue» o «auditoría» no activa el módulo. La carga no autoriza efectos externos.\n"
            )
        hub_modules = hubs.get(entry.parent)
        if hub_modules:
            rows = ["## Módulos disponibles", "", "| Procedimiento | Intención contextual |", "| --- | --- |"]
            for module in hub_modules:
                purpose = metadata[module["name"]]["description"].replace("|", "\\|")
                rows.append(f"| [{module['name']}]({module['module']}) | {purpose} |")
            rendered = "\n".join(rows) + "\n"
            body = body.replace("<!-- skill-library:module-table -->", rendered)
        entry.write_text(
            "---\n" + yaml.safe_dump(fm, allow_unicode=True, sort_keys=False) + "---" + body.rstrip() + "\n"
        )
    # Resolve package resources relative to each document; retain historical data locations.
    for doc in destination.rglob("*.md"):
        text = doc.read_text()
        pattern = r"(?:file:///(?:Users|home)/[^/]+/\.gemini/config/skills/|~/.gemini/config/skills/)([\w./-]*)"
        changed = re.sub(pattern, lambda m: os.path.relpath(destination / m.group(1), doc.parent), text)
        if changed != text:
            changed += "\n\nLas rutas de recursos del paquete son relativas a la carpeta de este documento; ejecutar los ejemplos desde esa carpeta. Las rutas históricas de datos no cambian por instalar el skill.\n"
            doc.write_text(changed)
    registry_path = SOURCE / "global/skills.json"
    registry = json.loads(registry_path.read_text())
    previous = {e["name"]: e for e in registry["entries"]}
    generated = []
    for name, fm in sorted(metadata.items()):
        entry = dict(previous.get(name, {}))
        entry.update(name=name, description=fm["description"], role=fm.get("role"), path=name + "/SKILL.md")
        candidates = capabilities[name]["aliases"]
        entry["triggers"] = sorted({name, "/" + name, *[a for a in candidates if a.lower() not in generic]})
        generated.append(entry)
    registry["entries"] = generated
    registry["total_skills"] = len(generated)
    registry["adjacency"] = [
        edge for edge in registry["adjacency"] if edge["source"] in metadata and edge["target"] in metadata
    ]
    (destination / "skills.json").write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n")
    (destination / "skill_catalog.generated.json").write_text(
        json.dumps(
            {"version": 2, "skills": metadata, "capabilities": capabilities, "policy": catalog["policy"]},
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--environment", choices=["antigravity", "codex", "workspace"], required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build(args.output, args.environment)
