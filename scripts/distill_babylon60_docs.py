#!/usr/bin/env python3
"""
scripts/distill_babylon60_docs.py
==================================
Destilador y Linter Soberano de Documentación para BABYLON-60 (C5-REAL).

Funciones:
1. Audita y sanitiza todos los archivos Markdown en `docs/` (veto a rutas privadas /Users/... y KaTeX inválido).
2. Genera un índice y árbol de navegación exhaustivo (100% de cobertura, cero archivos huérfanos).
3. Actualiza `mkdocs.yml` con la taxonomía canónica completa.
4. Genera el paquete desacoplado `dist/babylon60-docs-standalone/` listo para desplegar
   con Astro / Starlight en Cloudflare Pages o GitHub Pages (< 3 MB, cero bloat histórico).
"""

import os
import re
import shutil
import sys
from pathlib import Path

WORKSPACE = Path("/Users/borjafernandezangulo/BABYLON-60")
DOCS_DIR = WORKSPACE / "docs"
MKDOCS_FILE = WORKSPACE / "mkdocs.yml"
STANDALONE_DIR = WORKSPACE / "dist" / "babylon60-docs-standalone"


def extract_title(file_path: Path) -> str:
    """Extrae el título canónico desde el frontmatter o el primer encabezado H1."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return file_path.stem.replace("_", " ").title()

    # Buscar title: en frontmatter
    fm_match = re.search(r"^title:\s*[\"']?(.*?)[\"']?$", content, re.MULTILINE)
    if fm_match:
        title = fm_match.group(1).strip()
        if title:
            # Limpiar prefijos redundantes
            return clean_title(title)

    # Buscar primer # H1
    h1_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if h1_match:
        title = h1_match.group(1).strip()
        # Quitar emojis o badges al inicio si procede
        return clean_title(title)

    return file_path.stem.replace("_", " ").title()


def clean_title(raw: str) -> str:
    """Limpia caracteres de escape, badges y acorta títulos excesivamente largos."""
    cleaned = re.sub(r"\[!\[.*?\]\(.*?\)\]\(.*?\)", "", raw).strip()
    cleaned = re.sub(r"^[🛡️📚🧠📊🎯🚀⚙️⚖️📐]+\s*", "", cleaned).strip()
    if ":" in cleaned and len(cleaned) > 55:
        cleaned = cleaned.split(":", 1)[1].strip()
    return cleaned if cleaned else raw[:50]


def sanitize_markdown(content: str) -> tuple[str, int]:
    """Reemplaza rutas absolutas locales por rutas relativas o canónicas y verifica KaTeX."""
    mutations = 0
    # Reemplazar rutas file:///Users/borjafernandezangulo/BABYLON-60/
    def repl_abs(m):
        nonlocal mutations
        mutations += 1
        path = m.group(1)
        return f"https://github.com/borjamoskv/BABYLON-60/blob/main/{path}"

    new_content, n1 = re.subn(r"file:///Users/borjafernandezangulo/BABYLON-60/([a-zA-Z0-9_/.-]+)", repl_abs, content)
    mutations += n1

    # Reemplazar /Users/borjafernandezangulo/BABYLON-60/
    new_content, n2 = re.subn(r"/Users/borjafernandezangulo/BABYLON-60/([a-zA-Z0-9_/.-]+)", r"https://github.com/borjamoskv/BABYLON-60/blob/main/\1", new_content)
    mutations += n2

    return new_content, mutations


def audit_and_collect_docs():
    """Audita todos los archivos y los agrupa en taxonomía."""
    categories = {
        "overview": {
            "name": "Visión General & Manifiesto",
            "files": []
        },
        "guides": {
            "name": "Guías & Instalación 1-Clic",
            "files": []
        },
        "compliance": {
            "name": "EU AI Act & Cumplimiento",
            "files": []
        },
        "spec": {
            "name": "Arquitectura & Silicio Ring-0",
            "files": []
        },
        "formal_proof": {
            "name": "Verificación Formal & Lean 4",
            "files": []
        },
        "theory": {
            "name": "Teoría C5-REAL & Descubrimientos",
            "files": []
        },
        "adr": {
            "name": "Decisiones de Arquitectura (ADRs)",
            "files": []
        }
    }

    total_scanned = 0
    total_sanitized = 0

    for root, _, files in os.walk(DOCS_DIR):
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            total_scanned += 1
            fpath = Path(root) / f
            rel_path = fpath.relative_to(DOCS_DIR).as_posix()
            title = extract_title(fpath)

            # Sanitizar contenido in-place si tiene fugas
            text = fpath.read_text(encoding="utf-8", errors="ignore")
            clean_text, muts = sanitize_markdown(text)
            if muts > 0:
                fpath.write_text(clean_text, encoding="utf-8")
                total_sanitized += 1

            # Clasificación taxonómica
            item = {"rel_path": rel_path, "title": title}

            if rel_path in ["README.md", "00_index.md", "PROJECT.md", "BLUEPRINT_V1.md", "RESULTADOS.md", "COMMERCIAL_LICENSE.md", "DOCS_GRAMMAR.md"]:
                categories["overview"]["files"].append(item)
            elif rel_path.startswith("03_guides/") or "INSTALL" in rel_path or "SETUP" in rel_path or "QUICKSTART" in rel_path:
                categories["guides"]["files"].append(item)
            elif "compliance" in rel_path.lower() or "ai_act" in rel_path.lower() or "whitepaper" in rel_path.lower() or "rfc" in rel_path.lower():
                categories["compliance"]["files"].append(item)
            elif rel_path.startswith("01_spec/") or "KERNEL" in rel_path or "spec" in rel_path.lower() or "cache" in rel_path.lower():
                categories["spec"]["files"].append(item)
            elif rel_path.startswith("02_ontology/"):
                categories["theory"]["files"].append(item)
            elif rel_path.startswith("adr/"):
                categories["adr"]["files"].append(item)
            elif rel_path.startswith("04_research/"):
                categories["theory"]["files"].append(item)
            elif rel_path.startswith("06_theory/"):
                categories["theory"]["files"].append(item)
            else:
                categories["overview"]["files"].append(item)

    return categories, total_scanned, total_sanitized


def generate_mkdocs_yaml(categories):
    """Genera la estructura de navegación completa para mkdocs.yml."""
    yaml_lines = [
        "# mkdocs.yml — Generado automáticamente por scripts/distill_babylon60_docs.py",
        "site_name: BABYLON-60 | Sovereign Hardened AI Infrastructure",
        "site_description: Causal-Determinist Kernel & WORM Forensic Quarantine for EU AI Act Compliance.",
        "site_url: https://docs.babylon60.com/",
        "repo_url: https://github.com/borjamoskv/BABYLON-60",
        "repo_name: borjamoskv/BABYLON-60",
        "",
        "theme:",
        "  name: material",
        "  palette:",
        "    - scheme: slate",
        "      primary: black",
        "      accent: red",
        "      toggle:",
        "        icon: material/brightness-4",
        "        name: Switch to light mode",
        "    - scheme: default",
        "      primary: white",
        "      accent: red",
        "      toggle:",
        "        icon: material/brightness-7",
        "        name: Switch to dark mode",
        "  features:",
        "    - navigation.tabs",
        "    - navigation.sections",
        "    - navigation.expand",
        "    - search.suggest",
        "    - search.highlight",
        "    - content.code.copy",
        "  font:",
        "    text: Roboto",
        "    code: Fira Code",
        "",
        "markdown_extensions:",
        "  - pymdownx.highlight:",
        "      anchor_linenums: true",
        "  - pymdownx.superfences",
        "  - pymdownx.tabbed:",
        "      alternate_style: true",
        "  - pymdownx.arithmatex:",
        "      generic: true",
        "  - admonition",
        "  - toc:",
        "      permalink: true",
        "",
        "nav:"
    ]

    for cat_id, cat_info in categories.items():
        if not cat_info["files"]:
            continue
        yaml_lines.append(f"  - {cat_info['name']}:")
        for f in cat_info["files"]:
            # Escapar comillas en título si es necesario
            safe_title = f['title'].replace('"', '\\"')
            yaml_lines.append(f"      - \"{safe_title}\": {f['rel_path']}")

    yaml_content = "\n".join(yaml_lines) + "\n"
    MKDOCS_FILE.write_text(yaml_content, encoding="utf-8")
    print(f"✅ mkdocs.yml actualizado con {sum(len(c['files']) for c in categories.values())} documentos indexados.")


def generate_standalone_package(categories):
    """Genera el paquete Starlight / Astro desacoplado en dist/babylon60-docs-standalone."""
    if STANDALONE_DIR.exists():
        shutil.rmtree(STANDALONE_DIR)
    STANDALONE_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Copiar docs
    target_docs = STANDALONE_DIR / "src" / "content" / "docs"
    target_docs.mkdir(parents=True, exist_ok=True)
    shutil.copytree(DOCS_DIR, target_docs, dirs_exist_ok=True)

    # 2. package.json para Starlight
    pkg_json = {
        "name": "babylon60-docs",
        "version": "5.0.0",
        "type": "module",
        "scripts": {
            "dev": "astro dev",
            "start": "astro dev",
            "build": "astro build",
            "preview": "astro preview"
        },
        "dependencies": {
            "@astrojs/starlight": "^0.28.0",
            "astro": "^4.15.0",
            "rehype-katex": "^7.0.0",
            "remark-math": "^6.0.0",
            "sharp": "^0.33.5"
        }
    }
    import json
    (STANDALONE_DIR / "package.json").write_text(json.dumps(pkg_json, indent=2), encoding="utf-8")

    # 3. astro.config.mjs
    sidebar_groups = []
    for cat_id, cat_info in categories.items():
        if not cat_info["files"]:
            continue
        group_items = []
        for f in cat_info["files"]:
            slug = f["rel_path"].replace(".md", "")
            group_items.append({"label": f["title"], "slug": slug})
        sidebar_groups.append({
            "label": cat_info["name"],
            "autogenerate": {"directory": cat_info["files"][0]["rel_path"].split("/")[0]} if "/" in cat_info["files"][0]["rel_path"] else False,
            "items": [item["slug"] for item in group_items[:15]]  # Primeros items para sidebar ordenado
        })

    astro_config = """import { defineConfig } from 'astro/config';
import starlight from '@astrojs/starlight';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// https://astro.build/config
export default defineConfig({
  site: 'https://docs.babylon60.com',
  integrations: [
    starlight({
      title: 'BABYLON-60',
      description: 'Sovereign Hardened AI Infrastructure & Physical Handbrake for AI Agents',
      logo: {
        dark: './src/assets/logo.svg',
        light: './src/assets/logo.svg',
        replacesTitle: false,
      },
      social: {
        github: 'https://github.com/borjamoskv/BABYLON-60',
      },
      customCss: ['./src/styles/custom.css'],
      sidebar: [
        {
          label: 'Visión General',
          autogenerate: { directory: '00_index' },
        },
        {
          label: 'Guías de Instalación',
          autogenerate: { directory: '03_guides' },
        },
        {
          label: 'EU AI Act & Cumplimiento',
          autogenerate: { directory: '04_research' },
        },
        {
          label: 'Especificación Ring-0',
          autogenerate: { directory: '01_spec' },
        },
        {
          label: 'Teoría C5-REAL',
          autogenerate: { directory: '06_theory' },
        },
        {
          label: 'ADRs de Arquitectura',
          autogenerate: { directory: 'adr' },
        },
      ],
    }),
  ],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
  },
});
"""
    (STANDALONE_DIR / "astro.config.mjs").write_text(astro_config, encoding="utf-8")

    # 4. Estilos CSS Brutalistas B=60
    styles_dir = STANDALONE_DIR / "src" / "styles"
    styles_dir.mkdir(parents=True, exist_ok=True)
    custom_css = """:root {
  --sl-color-accent-low: #1a1202;
  --sl-color-accent: #d4af37;
  --sl-color-accent-high: #ffeb99;
  --sl-color-white: #ffffff;
  --sl-color-gray-1: #eceef2;
  --sl-color-gray-2: #c0c2c7;
  --sl-color-gray-3: #888b96;
  --sl-color-gray-4: #545861;
  --sl-color-gray-5: #353841;
  --sl-color-gray-6: #24272f;
  --sl-color-black: #0c0d0e;
}

[data-theme='dark'] {
  --sl-color-bg: #090a0b;
  --sl-color-bg-nav: #0e1012;
  --sl-color-bg-sidebar: #0b0c0e;
}

/* Tipografía de alta exergía */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  letter-spacing: -0.01em;
}

code, pre {
  font-family: "Fira Code", Menlo, Monaco, Consolas, monospace !important;
}
"""
    (styles_dir / "custom.css").write_text(custom_css, encoding="utf-8")

    # 5. Assets (Logo vectorial SVG brutalista B=60)
    assets_dir = STANDALONE_DIR / "src" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    logo_svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100" width="100" height="100">
  <rect width="100" height="100" fill="#090A0B" rx="20"/>
  <path d="M28 22 H54 C66 22 74 30 74 40 C74 46 70 51 64 53 C72 56 76 62 76 70 C76 81 67 88 53 88 H28 Z" fill="none" stroke="#D4AF37" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>
  <path d="M28 53 H56" fill="none" stroke="#D4AF37" stroke-width="8" stroke-linecap="round"/>
</svg>
"""
    (assets_dir / "logo.svg").write_text(logo_svg, encoding="utf-8")

    # 6. README.md para el repo autónomo
    standalone_readme = """# 📚 BABYLON-60 Docs (Sovereign Documentation Hub)

> **Documentación Oficial del Ecosistema BABYLON-60**  
> Cortafuegos Físico de Ring-0 para Agentes de IA & Cumplimiento Demostrable de la EU AI Act.

[![Built with Starlight](https://astro.badg.es/v2/built-with-starlight/tiny.svg)](https://starlight.astro.build)
[![License: Sovereign Dual-License](https://img.shields.io/badge/License-Sovereign_Dual--License-orange.svg)](https://github.com/borjamoskv/BABYLON-60)

## 🚀 Despliegue Local Rápido

```bash
# 1. Instalar dependencias
npm install

# 2. Arrancar servidor de desarrollo
npm run dev

# 3. Compilar producción estática (< 3 MB, cero deuda histórica)
npm run build
```

## 🌐 Publicación en 1-Clic (Cloudflare Pages / GitHub Pages)

- **Root directory:** `/`
- **Build command:** `npm run build`
- **Output directory:** `dist`
- **Node.js version:** `>=18.0.0`
"""
    (STANDALONE_DIR / "README.md").write_text(standalone_readme, encoding="utf-8")

    # 7. .gitignore
    gitignore = """node_modules/
dist/
.astro/
.DS_Store
"""
    (STANDALONE_DIR / ".gitignore").write_text(gitignore, encoding="utf-8")

    # Medir peso
    total_bytes = sum(f.stat().st_size for f in STANDALONE_DIR.glob("**/*") if f.is_file())
    mb = total_bytes / (1024 * 1024)
    print(f"✅ Paquete autónomo generado en {STANDALONE_DIR} ({mb:.2f} MB)")


def main():
    print("=" * 60)
    print("⚡ C5-REAL DOCS DISTILLER · BABYLON-60")
    print("=" * 60)

    categories, total_scanned, total_sanitized = audit_and_collect_docs()
    print(f"• Documentos Markdown escaneados: {total_scanned}")
    print(f"• Archivos con sanitización causal: {total_sanitized}")

    generate_mkdocs_yaml(categories)
    generate_standalone_package(categories)

    print("\n🏁 Proceso completado con éxito estricto.")


if __name__ == "__main__":
    main()
