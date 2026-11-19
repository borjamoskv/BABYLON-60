#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.3 Sovereign Hardened - SOVEREIGN COMPLIANCE ORCHESTRATOR
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | COMPLETE END-TO-END PIPELINE
# ============================================================================
"""
[AX-76] INTEGRATION: Orquestador Soberano Unificado de Cumplimiento EU AI Act.

Conecta en un único bucle determinista:
1. Ring-0: Daemon nativo en Rust (latencia sub-milisegundo).
2. Hardware: Atestación de Secure Enclave (P-256) / TouchID.
3. Ring-1: Certificación formal en Lean 4 (Soundness matemático por reducción al absurdo).
4. Capa Externa: Exporter oficial de BABYLON-60 (Ed25519) + Verificador en 1-Click (Rust).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR / "01_KISH_ENGINE"))

from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter  # noqa: E402

# Ruta donde versiones anteriores dejaban el binario compilado. Ya no se ejecuta: un binario
# previo a C0054 certifica cualquier texto con los marcadores esperados.
LEGACY_VERIFIER_BIN = ROOT_DIR / "scripts" / "c5_demos" / "babylon_verifier_bin"


def run_fresh_verifier(pack_path: Path) -> tuple[int, str]:
    """Compila el verificador desde el código fuente actual en un directorio temporal y lo
    ejecuta (C0054). Nunca reutiliza un binario existente. Devuelve (código, salida)."""
    import tempfile

    with tempfile.TemporaryDirectory(prefix="babylon_verifier_") as build_dir:
        binary = Path(build_dir) / "verifier"
        subprocess.run(
            ["rustc", "-O", str(ROOT_DIR / "scripts" / "c5_demos" / "c5_verifier_cli.rs"), "-o", str(binary)],
            check=True,
            capture_output=True,
        )
        result = subprocess.run([str(binary), "--pack", str(pack_path)], capture_output=True, text=True)
    return result.returncode, result.stdout + result.stderr


def main():
    print("========================================================================")
    print(" █ AUTOCOGNITION-Ω | SOVEREIGN COMPLIANCE ORCHESTRATOR")
    print("   Pila Unificada: Rust Ring-0 + TouchID + Lean 4 + AESIA Exporter")
    print("========================================================================")

    t_start = time.perf_counter()

    # 1. Ejecutar el Daemon de Rust en Ring-0
    print("[1/4] Disparando Sovereign Spark Daemon (Rust Baremetal)...")
    rust_bin = ROOT_DIR / "scripts" / "c5_demos" / "poc_sovereign_spark_daemon_bin"
    if not rust_bin.exists():
        subprocess.run(
            ["rustc", "-O", "-C", "opt-level=3", str(ROOT_DIR / "scripts" / "c5_demos" / "poc_sovereign_spark_daemon.rs"), "-o", str(rust_bin)],
            check=True
        )

    _ = subprocess.run([str(rust_bin)], capture_output=True, text=True, check=True)
    print("      -> Daemon ejecutado con éxito en silicio.")

    # 2. Verificar el Teorema Formal en Lean 4
    print("[2/4] Verificando Teorema Formal en Lean 4 (Curry-Howard / Ring-1)...")
    lean_file = ROOT_DIR / "scripts" / "c5_demos" / "poc_annex_vi_compliance.lean"
    res_lean = subprocess.run(["lean", str(lean_file)], capture_output=True, text=True, check=True)
    print(f"      -> {res_lean.stdout.strip()}")

    # 3. Generar Certificado Oficial de Conformidad Anexo VI (AESIA - España)
    print("[3/4] Generando Certificado Oficial de la UE con Ed25519 (AESIA Locale: 'es')...")
    os.environ.setdefault("BABYLON60_SIGNING_SEED", "60" * 32)

    # Crear un manifest temporal para el exporter de producción
    import shutil

    tmp_bundle = ROOT_DIR / "scripts" / "c5_demos" / "tmp_bundle"
    tmp_bundle.mkdir(parents=True, exist_ok=True)
    try:
        manifest_data = {
            "global_hash": "6060c5c5" + "0" * 56,
            "operator": "Borja (Sovereign Root)",
            "system_id": "BABYLON-60-NODE-01",
            "timestamp": time.time(),
        }
        manifest_path = tmp_bundle / "manifest.json"
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest_data, f)

        exporter = EUAIActComplianceExporter(artifact_bundle_path=str(tmp_bundle))
        cert = exporter.generate_certificate(
            system_id="BABYLON-60-CORE",
            operator_name="Borja (Sovereign Operator)",
            locale="es",
        )
        signed_cert = exporter.sign_certificate(cert)
    finally:
        shutil.rmtree(tmp_bundle, ignore_errors=True)

    cert_path = ROOT_DIR / "scripts" / "c5_demos" / "official_eu_compliance_certificate.json"
    with open(cert_path, "w", encoding="utf-8") as f:
        json.dump(signed_cert, f, indent=2, ensure_ascii=False)
    print(f"      -> Certificado sellado y firmado: {cert_path.name}")
    sig_hex = str(signed_cert.get("signature", ""))
    print(f"      -> Huella Ed25519: {sig_hex[:24]}...")

    # 4. Auditoría Técnica Instantánea mediante el Verificador Autónomo de Rust
    print("[4/4] Ejecutando Verificador Autónomo de Conformidad (compilado desde la fuente actual)...")
    pack_path = ROOT_DIR / "scripts" / "c5_demos" / "eu_ai_act_annex_vi_pack.json"
    verifier_code, verifier_output = run_fresh_verifier(pack_path)
    print("------------------------------------------------------------------------")
    for line in verifier_output.splitlines():
        if "INDICIO" in line or "DICTAMEN" in line or "Motivo" in line:
            print(f"  {line.strip()}")
    print("------------------------------------------------------------------------")

    total_time_ms = (time.perf_counter() - t_start) * 1000
    print(f"[+] PIPELINE SOBERANO COMPLETO EN {total_time_ms:.2f} ms.")
    if verifier_code == 0:
        print("DICTAMEN: el verificador aceptó el expediente.")
    else:
        # C0054: sin firma y ancla verificadas el verificador rechaza; no hay dictamen de conformidad.
        print("DICTAMEN: NO CONFORME. El verificador rechazó el expediente (firma y ancla no verificadas).")
        print("========================================================================")
        sys.exit(1)
    print("========================================================================")


if __name__ == "__main__":
    main()
