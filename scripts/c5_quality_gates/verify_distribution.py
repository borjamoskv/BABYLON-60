#!/usr/bin/env python3
"""
C5-REAL Distribution Quality Gate: verify_distribution.py
Audita la preparación del paquete babylon60 para distribución en PyPI, Crates.io y GHCR.
Soporta emisión de telemetría nativa M2M via --json.
"""

import sys
import json
import argparse
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent

def check_python_distribution() -> dict:
    result = {"status": "PASS", "details": [], "artifacts": []}
    try:
        subprocess.run(["uv", "build"], cwd=ROOT_DIR, capture_output=True, text=True, check=True)
        dist_dir = ROOT_DIR / "dist"
        if not dist_dir.exists():
            result["status"] = "FAIL"
            result["details"].append("Directorio dist/ no fue generado")
            return result
        
        artifacts = [f.name for f in dist_dir.glob("*")]
        result["artifacts"] = artifacts
        whl = [f for f in artifacts if f.endswith(".whl")]
        sdist = [f for f in artifacts if f.endswith(".tar.gz")]
        
        if not whl or not sdist:
            result["status"] = "FAIL"
            result["details"].append(f"Faltan artefactos obligatorios. Encontrados: {artifacts}")
        else:
            result["details"].append(f"Empaquetado Python OK: {whl[0]}, {sdist[0]}")
    except Exception as e:
        result["status"] = "FAIL"
        result["details"].append(f"Error en uv build: {str(e)}")
    
    return result

def check_rust_distribution() -> dict:
    result = {"status": "PASS", "details": []}
    try:
        res = subprocess.run(
            ["cargo", "check", "--workspace"],
            cwd=ROOT_DIR,
            capture_output=True,
            text=True
        )
        if res.returncode != 0:
            result["status"] = "FAIL"
            result["details"].append(f"cargo check fallo: {res.stderr[:300]}")
        else:
            result["details"].append("Workspace de Rust compila limpiamente")
    except Exception as e:
        result["status"] = "FAIL"
        result["details"].append(f"Error ejecutando cargo check: {str(e)}")
    
    return result

def check_dockerfile() -> dict:
    result = {"status": "PASS", "details": []}
    dockerfile_path = ROOT_DIR / "Dockerfile"
    if not dockerfile_path.exists():
        result["status"] = "FAIL"
        result["details"].append("Dockerfile ausente")
        return result
    
    content = dockerfile_path.read_text(encoding="utf-8")
    checks = {
        "non_root_user": "USER appuser" in content,
        "healthcheck": "HEALTHCHECK" in content,
        "oci_labels": "org.opencontainers.image" in content,
        "slim_base": "python:3.12-slim" in content,
    }
    
    for check_name, passed in checks.items():
        if passed:
            result["details"].append(f"Dockerfile {check_name}: OK")
        else:
            result["status"] = "FAIL"
            result["details"].append(f"Dockerfile falta {check_name}")
            
    return result

def check_workflows() -> dict:
    result = {"status": "PASS", "details": []}
    wf_dir = ROOT_DIR / ".github" / "workflows"
    required_workflows = ["pypi-publish.yml", "crates-publish.yml", "docker-ghcr.yml"]
    
    for wf in required_workflows:
        path = wf_dir / wf
        if path.exists():
            result["details"].append(f"Workflow {wf}: OK")
        else:
            result["status"] = "FAIL"
            result["details"].append(f"Workflow ausente: {wf}")
            
    return result

def main() -> None:
    parser = argparse.ArgumentParser(description="C5-REAL Distribution Audit Gate")
    parser.add_argument("--json", action="store_true", help="Emitir resultados en formato JSON M2M")
    args = parser.parse_args()
    
    python_res = check_python_distribution()
    rust_res = check_rust_distribution()
    docker_res = check_dockerfile()
    wf_res = check_workflows()
    
    all_passed = all(
        res["status"] == "PASS" 
        for res in [python_res, rust_res, docker_res, wf_res]
    )
    
    report = {
        "quality_gate": "verify_distribution",
        "overall_status": "PASS" if all_passed else "FAIL",
        "python": python_res,
        "rust": rust_res,
        "docker": docker_res,
        "workflows": wf_res
    }
    
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("==================================================")
        print(f"C5-REAL DISTRIBUTION AUDIT GATE: {report['overall_status']}")
        print("==================================================")
        print(f"[Python]   Status: {python_res['status']} -> {', '.join(python_res['details'])}")
        print(f"[Rust]     Status: {rust_res['status']} -> {', '.join(rust_res['details'])}")
        print(f"[Docker]   Status: {docker_res['status']} -> {', '.join(docker_res['details'])}")
        print(f"[Workflows] Status: {wf_res['status']} -> {', '.join(wf_res['details'])}")
        print("==================================================")
        
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
