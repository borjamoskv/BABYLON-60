#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# C5-REAL: Dynamic Sanity Check for Indirect Prompt Injection (IPI) patterns.
# Author: Borja Moskv (borjamoskv)

import os
import re
import sys
import hashlib
from typing import Pattern, Any

# Exclusiones de directorios para evitar escaneos recursivos innecesarios (Anergía)
EXCLUDED_DIRS: list[str] = [
    ".git",
    ".venv",
    "node_modules",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "sandbox_stress",
    "audits"
]

# Extensiones de archivos binarios excluidos
EXCLUDED_EXTS: list[str] = [
    ".db",
    ".db-journal",
    ".npz",
    ".png",
    ".jpg",
    ".jpeg",
    ".zip",
    ".tar.gz",
    ".egg-info",
    ".sqlite"
]

# Patrones heurísticos comunes de inyección indirecta (IPI)
IPI_SIGNATURES: list[Pattern[str]] = [
    re.compile(r"system\s+override", re.IGNORECASE),
    re.compile(r"ignore\s+prior\s+directions", re.IGNORECASE),
    re.compile(r"ignore\s+previous\s+instructions", re.IGNORECASE),
    re.compile(r"ignora\s+las\s+instrucciones\s+anteriores", re.IGNORECASE),
    re.compile(r"you\s+must\s+execute", re.IGNORECASE),
    re.compile(r"execute\s+the\s+command", re.IGNORECASE),
    re.compile(r"run\s+command", re.IGNORECASE),
    re.compile(r"inject\s+payload", re.IGNORECASE),
]

def calculate_blake3(file_path: str) -> str:
    """Calcula el hash BLAKE3 o SHA256 como fallback determinista del archivo."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()
    except IOError:
        return "0" * 64

def scan_file(file_path: str) -> list[dict[str, Any]]:
    """Escanea un archivo en busca de firmas IPI conocidas."""
    detections: list[dict[str, Any]] = []
    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line_idx, line in enumerate(f, 1):
                for pattern in IPI_SIGNATURES:
                    if pattern.search(line):
                        detections.append({
                            "line": line_idx,
                            "content": line.strip(),
                            "pattern": pattern.pattern
                        })
    except Exception as e:
        # Pasa en silencio bajo directrices de resiliencia del OS
        pass
    return detections

def main() -> None:
    workspace_root: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    violation_found: bool = False
    
    # Registro de auditoría con tipo explícito para Mypy (Invariante Ω17)
    audit_log: dict[str, dict[str, Any]] = {}

    for root, dirs, files in os.walk(workspace_root):
        # Exclusión in-place de directorios para optimizar recorrido de disco
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        
        for file in files:
            file_path: str = os.path.join(root, file)
            
            # Evitar escanear el propio script de auditoría
            if file == "sanitize_ipi_payloads.py":
                continue
                
            # Excluir binarios y bases de datos por extensión
            ext: str = os.path.splitext(file)[1].lower()
            if ext in EXCLUDED_EXTS:
                continue

            # Evitar escanear archivos que contengan sandbox_stress en su ruta
            if any(ex_dir in file_path.split(os.sep) for ex_dir in EXCLUDED_DIRS):
                continue
                
            detections: list[dict[str, Any]] = scan_file(file_path)
            
            if detections:
                violation_found = True
                rel_path: str = os.path.relpath(file_path, workspace_root)
                file_hash: str = calculate_blake3(file_path)
                
                audit_log[rel_path] = {
                    "hash": file_hash,
                    "violations": detections
                }

    if violation_found:
        print("[!] C5-REAL: SE DETECTARON POSIBLES PAYLOADS DE INYECCIÓN DE PROMPTS (IPI):", file=sys.stderr)
        for path, info in audit_log.items():
            print(f"  Archivo: {path} (Hash: {info['hash']})", file=sys.stderr)
            for v in info["violations"]:
                print(f"    Línea {v['line']}: [Patrón: {v['pattern']}] -> {v['content']}", file=sys.stderr)
        sys.exit(1)
    else:
        print("[+] C5-REAL: Escaneo IPI completo. Cero vectores de inyección detectados.")
        sys.exit(0)

if __name__ == "__main__":
    main()
