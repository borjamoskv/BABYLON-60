# C5-REAL EXERGY CERTIFIED
import os
import json
import shutil
from pathlib import Path

# CORTEX Nexus Ingestion Protocol
# Compresses semantic trees from legacy submodules into a unified graph.

ROOT = Path(__file__).parent.parent
DOCS_DIR = ROOT / "docs"
PUBLIC_DOCS = ROOT / "public" / "docs_nexus"
INDEX_FILE = ROOT / "public" / "docs_nexus" / "nexus_index.json"

def clean_and_prepare():
    if PUBLIC_DOCS.exists():
        shutil.rmtree(PUBLIC_DOCS)
    PUBLIC_DOCS.mkdir(parents=True)

def ingest_submodules():
    index = []

    for submodule in ["legacy-wiki", "legacy-cortex-docs"]:
        submodule_path = DOCS_DIR / submodule
        if not submodule_path.exists():
            continue

        for ext in ["*.md", "*.mdx"]:
            for file_path in submodule_path.rglob(ext):
                # Ignore hidden files, node_modules, etc.
                if ".git" in file_path.parts or "node_modules" in file_path.parts:
                    continue

                rel_path = file_path.relative_to(submodule_path)
                dest_path = PUBLIC_DOCS / submodule / rel_path

                # Copy file
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)

                # Add to index
                index.append({
                    "id": f"{submodule}/{rel_path.with_suffix('')}",
                    "source": submodule,
                    "path": f"/docs_nexus/{submodule}/{rel_path}",
                    "name": file_path.stem
                })

    with open(INDEX_FILE, "w") as f:
        json.dump(index, f, indent=2)

    print(f"[C5-REAL] Ingested {len(index)} nodes into Nexus Graph.")

if __name__ == "__main__":
    clean_and_prepare()
    ingest_submodules()
