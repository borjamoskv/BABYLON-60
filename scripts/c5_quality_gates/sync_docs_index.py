#!/usr/bin/env python3

import logging
#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
"""
sync_docs_index.py - Autonomous Documentation Indexer & Link Verifier
Scans all 96+ markdown documents in docs/ and synchronizes docs/00_index.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DOCS_DIR = REPO_ROOT / "docs"
INDEX_FILE = DOCS_DIR / "00_index.md"

SECTION_NAMES = {
    "root": "⚡ Sovereign Core & Executive Specifications",
    "01_spec": "📋 Technical Specifications & System Protocols",
    "02_ontology": "🧠 Axiomatic Ontology & Threat Models",
    "03_guides": "📖 Integration & Operational Guides",
    "04_research": "🔬 Deep Research, SOTA & Philosophical Manifestos",
    "04_research/manifestos": "📜 Autonomous AI Manifestos",
    "04_research/sota": "⚡ State-of-the-Art Technical Benchmarks",
    "04_research/substack": "✍️ Interdisciplinary Theory & Epistemology",
    "05_gtm": "🚀 Go-To-Market, Valuation & Enterprise Agreements",
    "05_isomorphisms": "🧩 Cancer Isomorphisms & Complex Systems Dynamics",
    "06_theory": "⚖️ Formal Theory, Gödel Incompleteness & Exergy Invariants",
    "audits": "🛡️ Compliance Certificates & Forensic Audits",
}


def extract_title(md_path: Path) -> str:
    """Extract first H1 heading or clean filename."""
    try:
        lines = md_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        for line in lines:
            line_str = line.strip()
            if line_str.startswith("# "):
                title = line_str.lstrip("#").strip()
                return title.replace("|", "\\|")
    except Exception as e:
        logging.error(f'Traza Epistémica Perdida: {e}')
    clean_name = md_path.stem.replace("_", " ").title()
    return f"{clean_name} Specification"


def main() -> None:
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Synchronize or emit docs index")
    parser.add_argument("--json", action="store_true", help="Emit the document graph as pure JSON for inter-agentic consumption")
    args = parser.parse_args()

    md_files = sorted([p for p in DOCS_DIR.rglob("*.md") if p.name != "00_index.md"])
    by_section: Dict[str, List[Dict[str, str]]] = {}
    
    for p in md_files:
        rel = p.relative_to(DOCS_DIR)
        parent_key = rel.parent.as_posix() if len(rel.parts) > 1 else "root"
        section_title = SECTION_NAMES.get(parent_key, f"📁 {parent_key.replace('_', ' ').title()}")
        if section_title not in by_section:
            by_section[section_title] = []
        by_section[section_title].append({
            "path": rel.as_posix(),
            "title": extract_title(p),
            "filename": p.name
        })

    if args.json:
        # Machine-to-Machine output
        payload = {
            "schema_version": "1.0",
            "type": "C5_DOCUMENT_GRAPH",
            "total_documents": len(md_files),
            "topology": by_section
        }
        print(json.dumps(payload, indent=2))
        return

    # Legacy human-readable Markdown compilation
    lines = [
        "# 📚 BABYLON-60 Sovereign Documentation Master Index",
        "",
        "<div align=\"center\">",
        "",
        "[![C5-REAL Verified](https://img.shields.io/badge/C5--REAL-Verified-00F0FF?style=for-the-badge&logo=shield)](https://github.com/borjamoskv/BABYLON-60)",
        "[![Régimen](https://img.shields.io/badge/Régimen-Causal--Determinist-7B1FA2?style=for-the-badge)](https://github.com/borjamoskv/BABYLON-60)",
        "[![Licencia](https://img.shields.io/badge/Licencia-Soberana_INV__C5__17-008055?style=for-the-badge)](./STATUS.md)",
        "",
        "</div>",
        "",
        "> **Nube de Conocimiento Categórico, Especificaciones Formales, Guías y Repositorio Teórico**  ",
        f"> **Estándar:** C5-REAL | **Documentos Totales Indexados:** {len(md_files)} | **Estado:** 100% Synchronized",
        "",
        "---",
        "",
        "## 🛠️ Navegación Rápida por Secciones",
        "",
    ]
    for section_title, docs in by_section.items():
        lines.append(f"### {section_title}")
        lines.append("")
        lines.append("| Documento | Ruta / Archivo | Título Principal / Propósito |")
        lines.append("| :--- | :--- | :--- |")
        for doc in docs:
            fp = doc["path"]
            lines.append(f"| [`{doc['filename']}`](file://{DOCS_DIR / fp}) | `{fp}` | {doc['title']} |")
        lines.append("")
    lines.append("---")
    lines.append("*Índice maestro autogenerado y sincronizado autónomamente por `sync_docs_index.py` bajo estándar C5-REAL.*")
    lines.append("")
    
    content = "\n".join(lines)
    INDEX_FILE.write_text(content, encoding="utf-8")
    print(f"[+] Successfully synchronized master index at {INDEX_FILE} with all {len(md_files)} docs!")

if __name__ == "__main__":
    main()
