#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
Archive.org Corpus Ingestion & Metadata Resolution CLI Tool
Descarga determinista de manifiestos, texto DjVuTXT y formatos derivados desde Archive.org.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from typing import Dict, Any, Optional

METADATA_API_URL = "https://archive.org/metadata/{identifier}"
DOWNLOAD_BASE_URL = "https://archive.org/download/{identifier}/{filename}"

class ArchiveOrgIngester:
    """
    Gestor de ingesta y resolución de manifiestos de Internet Archive.
    """

    def fetch_manifest(self, identifier: str) -> Dict[str, Any]:
        url = METADATA_API_URL.format(identifier=identifier)
        req = urllib.request.Request(url, headers={"User-Agent": "C5-REAL-Agent/1.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
        return data

    def select_best_text_file(self, manifest: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        files = manifest.get("files", [])

        # 1. Prioridad: DjVuTXT (_djvu.txt)
        for f in files:
            name = f.get("name", "")
            if name.endswith("_djvu.txt") or f.get("format") == "DjVuTXT":
                return f

        # 2. Prioridad: Text PDF
        for f in files:
            name = f.get("name", "")
            if name.endswith(".pdf") and f.get("format") in ["Text PDF", "Additional Text PDF"]:
                return f

        # 3. Prioridad: EPUB
        for f in files:
            if f.get("name", "").endswith(".epub"):
                return f

        # 4. Cualquier archivo .txt
        for f in files:
            if f.get("name", "").endswith(".txt"):
                return f

        return None

    def download_file(self, identifier: str, filename: str, output_dir: str) -> str:
        os.makedirs(output_dir, exist_ok=True)
        encoded_filename = urllib.parse.quote(filename)
        url = f"https://archive.org/download/{identifier}/{encoded_filename}"

        target_path = os.path.join(output_dir, filename.split("/")[-1])
        print(f"[ArchiveOrgIngester] Descargando {filename} desde {url}...")

        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (C5-REAL Engine)"})
            with urllib.request.urlopen(req) as response, open(target_path, "wb") as out_file:
                out_file.write(response.read())
        except Exception as e:
            print(f"[!] Warning con urllib ({e}). Reintentando con subprocess curl...")
            import subprocess
            res = subprocess.run(["curl", "-L", "-s", "-o", target_path, url])
            if res.returncode != 0 or os.path.getsize(target_path) == 0:
                raise RuntimeError(f"Error al descargar {filename} mediante curl: {res.returncode}")

        print(f"[✓] Descargado exitosamente en: {target_path} ({os.path.getsize(target_path)} bytes)")
        return target_path

def main():
    parser = argparse.ArgumentParser(description="Archive.org Corpus Ingestor (C5-REAL Engine)")
    parser.add_argument("identifier", help="Identificador del ítem en Internet Archive")
    parser.add_argument("--info-only", action="store_true", help="Mostrar únicamente manifiesto de metadatos")
    parser.add_argument("--format", help="Formato específico a descargar (ej. _djvu.txt, .pdf, .epub)")
    parser.add_argument("--output-dir", default="scratch/corpus", help="Directorio de destino (default: scratch/corpus)")

    args = parser.parse_args()
    ingester = ArchiveOrgIngester()

    try:
        manifest = ingester.fetch_manifest(args.identifier)
    except Exception as e:
        print(f"Error al consultar manifiesto de Archive.org ({args.identifier}): {e}", file=sys.stderr)
        sys.exit(1)

    metadata = manifest.get("metadata", {})
    files = manifest.get("files", [])

    print(f"=== MANIFIESTO DE ARCHIVE.ORG: {args.identifier} ===")
    print(f"  Título:     {metadata.get('title', 'N/A')}")
    print(f"  Creador:    {metadata.get('creator', 'N/A')}")
    print(f"  Año:        {metadata.get('date', metadata.get('year', 'N/A'))}")
    print(f"  Idioma:     {metadata.get('language', 'N/A')}")
    print(f"  Archivos:   {len(files)} archivos en el repositorio")

    if args.info_only:
        print("\n[Archivos disponibles]:")
        for f in files[:20]:
            print(f"  • {f.get('name')} | Format: {f.get('format')} | Size: {f.get('size')} B")
        sys.exit(0)

    # Seleccionar archivo a descargar
    target_file = None
    if args.format:
        for f in files:
            if args.format in f.get("name", "") or args.format.lower() in f.get("format", "").lower():
                target_file = f
                break

    if not target_file:
        target_file = ingester.select_best_text_file(manifest)

    if not target_file:
        print(f"Error: No se encontró un archivo adecuado para descargar en {args.identifier}", file=sys.stderr)
        sys.exit(1)

    filename = target_file.get("name")
    dest_dir = os.path.join(args.output_dir, args.identifier)
    downloaded_path = ingester.download_file(args.identifier, filename, dest_dir)
    print(f"Ingesta completada. Archivo listo para análisis: {downloaded_path}")

if __name__ == "__main__":
    main()
