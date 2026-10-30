#!/usr/bin/env python3
"""Generate or check deterministic Markdown navigation from the saved docs tree."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

REPO_ROOT = Path(__file__).absolute().parents[2]
SECTION_NAMES = {
    "root": "Core reference",
    "01_spec": "Specifications",
    "02_ontology": "Ontology and threat models",
    "03_guides": "Operational guides",
    "04_research": "Research",
    "06_theory": "Theory",
    "security": "Security contracts and audit reports",
    "adr": "Architecture decisions",
    "papers": "Papers and experiments",
}


def extract_title(path: Path) -> str:
    """Read the first H1 outside code fences, falling back to the filename."""
    fence = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\s{0,3}(?:`{3,}|~{3,})", line):
            fence = not fence
        elif not fence and line.startswith("# "):
            return line[2:].strip().replace("|", "\\|")
    return path.stem.replace("_", " ")


def document_graph(docs_dir: Path) -> dict[str, object]:
    """Count content documents separately from generated navigation pages."""
    files = sorted(p for p in docs_dir.rglob("*.md") if ".lake" not in p.parts)
    topology: dict[str, list[dict[str, str]]] = {}
    content = [p for p in files if p.name != "00_index.md"]
    for path in content:
        relative = path.relative_to(docs_dir)
        section = relative.parts[0] if len(relative.parts) > 1 else "root"
        name = SECTION_NAMES.get(section, section.replace("_", " ").title())
        topology.setdefault(name, []).append(
            {
                "path": relative.as_posix(),
                "title": extract_title(path),
                "filename": path.name,
            }
        )
    return {"schema_version": "1.1", "type": "C5_DOCUMENT_GRAPH", "total_documents": len(content), "topology": topology}


def render_index(directory: Path, paths: list[Path], title: str) -> str:
    lines = [
        f"# {title}",
        "",
        "Índice de navegación generado a partir de los archivos Markdown guardados.",
        "La inclusión de un documento no certifica sus afirmaciones ni su implementación.",
        "",
        f"**Entradas indexadas:** {len(paths)} (se excluye únicamente este índice).",
        "",
        "| Documento | Título |",
        "| :--- | :--- |",
    ]
    for path in paths:
        relative = path.relative_to(directory).as_posix()
        lines.append(f"| [`{relative}`]({relative}) | {extract_title(path)} |")
    lines.extend(
        [
            "",
            "Regeneración desde la raíz del repositorio:",
            "",
            "```sh",
            "python3 scripts/c5_quality_gates/sync_docs_index.py",
            "```",
            "",
            "Comprueba el contenido generado con el mismo comando y `--check`.",
            "",
        ]
    )
    return "\n".join(lines)


def expected_indexes(docs_dir: Path) -> dict[Path, str]:
    sections = [(docs_dir / "03_guides", "Guías operativas"), (docs_dir / "06_theory", "Fundamentos teóricos")]
    result = {}
    for directory, title in sections:
        if directory.is_dir():
            index = directory / "00_index.md"
            paths = sorted(p for p in directory.rglob("*.md") if p != index)
            result[index] = render_index(directory, paths, title)
    index = docs_dir / "00_index.md"
    paths = set(p for p in docs_dir.rglob("*.md") if p != index)
    paths.update(result)
    # Section indexes appear in the master inventory on the first generation too.
    titles = {path: content.splitlines()[0][2:] for path, content in result.items()}
    lines = [
        "# BABYLON-60 — Documentation index",
        "",
        "Navegación generada desde los archivos Markdown guardados.",
        "La inclusión de un documento no acredita verificación formal, ejecución ni cumplimiento regulatorio.",
        "",
        f"**Entradas indexadas:** {len(paths)} (se excluye únicamente este índice).",
        "",
        "| Documento | Título |",
        "| :--- | :--- |",
    ]
    for path in sorted(paths):
        relative = path.relative_to(docs_dir).as_posix()
        title = titles[path] if path in titles else extract_title(path)
        lines.append(f"| [`{relative}`]({relative}) | {title} |")
    lines.extend(
        [
            "",
            "```sh",
            "python3 scripts/c5_quality_gates/sync_docs_index.py --check",
            "```",
            "",
            "Omite `--check` para regenerar los índices maestro, de guías y de teoría.",
            "",
        ]
    )
    result[index] = "\n".join(lines)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs-dir", type=Path, default=REPO_ROOT / "docs")
    parser.add_argument("--check", action="store_true", help="Report stale indexes without changing files")
    parser.add_argument("--json", action="store_true", help="Emit content-document inventory without changing files")
    args = parser.parse_args()
    if not args.docs_dir.is_dir():
        parser.error(f"Documentation directory does not exist: {args.docs_dir}")
    if args.json:
        print(json.dumps(document_graph(args.docs_dir), indent=2, ensure_ascii=False))
        return 0
    stale = []
    for path, content in expected_indexes(args.docs_dir).items():
        if args.check:
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                stale.append(path)
        else:
            path.write_text(content, encoding="utf-8")
            print(f"Generated {path}")
    if stale:
        for path in stale:
            print(f"STALE: {path}")
        return 1
    if args.check:
        print("PASS: generated documentation indexes match the saved Markdown inventory")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
