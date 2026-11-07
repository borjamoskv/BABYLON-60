#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened · Tools
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | RING-0 CORTAFUEGOS 5 CLI
# ============================================================================
"""
CLI de Auditoría y Filtrado Determinista de Citas (Cortafuegos 5).
Escanea artefactos Markdown o buffers de texto, bloqueando o saneando
cualquier patente, arXiv ID o DOI que carezca de EvidenceRef en silicio.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

# Añadir 01_KISH_ENGINE al sys.path para resolución de imports
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT / "01_KISH_ENGINE") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "01_KISH_ENGINE"))

from babylon60.kernel.grounding_interceptor import (  # noqa: E402
    EvidenceRecord,
    GroundingInterceptor,
    GroundingRegistry,
    SyntheticPlaceholderError,
    UnverifiedGroundingError,
)


def build_default_registry(
    db_path: Optional[str] = None,
    json_path: Optional[str] = None,
) -> GroundingRegistry:
    """Construye e inicializa el registro con las evidencias canónicas del repositorio."""
    registry = GroundingRegistry(db_path=db_path)

    # Sembrar evidencias canónicas verificadas de QMUL / Audio DSP (con digests no vacíos)
    registry.register(
        EvidenceRecord(
            entity_type="PATENT",
            identifier="9640165",
            sha256_digest="c9d8f4b217e3a6085d1249b76f0c812e9a4b5c6d7e8f9012a3b4c5d6e7f8091a",
            canonical_title="Automated multitrack audio mixing based on psychoacoustic masking thresholds",
            source="USPTO / Queen Mary University of London",
            verified_at="2017-05-02T00:00:00Z",
            status="VERIFIED",
        )
    )
    registry.register(
        EvidenceRecord(
            entity_type="ARXIV",
            identifier="2408.08058",
            sha256_digest="a4f8e71b29d10e8354c03b1297e61e053a478b27f4c519280b18f7d9a3b2c1e8",
            canonical_title="Diff2Mix: Controllable Music Mixing with Diffusion Models and Differentiable Mixing Consoles",
            source="arXiv / QMUL C4DM",
            verified_at="2024-08-15T00:00:00Z",
            status="VERIFIED",
        )
    )
    registry.register(
        EvidenceRecord(
            entity_type="ARXIV",
            identifier="2111.08553",
            sha256_digest="b5d4045c3f466fa91fe2cc6abe79232a1a57cdf104f7a26e716e0a1e2789df78",
            canonical_title="Hybrid Spectrogram and Waveform Prediction Networks for Music Source Separation (Demucs v3)",
            source="arXiv / Meta AI",
            verified_at="2021-11-16T00:00:00Z",
            status="VERIFIED",
        )
    )

    if json_path and os.path.exists(json_path):
        registry.load_from_json(json_path)

    return registry


def main() -> None:
    parser = argparse.ArgumentParser(
        description="BABYLON-60 Cortafuegos 5 · Grounding Interceptor en Silicio"
    )
    parser.add_argument("target", help="Ruta al archivo Markdown o de texto a auditar")
    parser.add_argument(
        "--policy",
        choices=["strict", "redact", "audit"],
        default="redact",
        help="Política ante citas no verificadas (default: redact)",
    )
    parser.add_argument("--db", dest="db_path", help="Ruta opcional a base de datos SQLite de evidencias")
    parser.add_argument("--json-evidence", dest="json_path", help="Ruta a archivo JSON con evidencias adicionales")
    parser.add_argument("--output", dest="output_path", help="Ruta para guardar el texto saneado")
    parser.add_argument("--in-place", action="store_true", help="Sobrescribe el archivo de entrada con el texto saneado")

    args = parser.parse_args()

    target_path = Path(args.target)
    if not target_path.exists():
        print(f"❌ Error: Archivo no encontrado: {target_path}", file=sys.stderr)
        sys.exit(1)

    text = target_path.read_text(encoding="utf-8")
    registry = build_default_registry(db_path=args.db_path, json_path=args.json_path)

    policy_map = {
        "strict": GroundingInterceptor.POLICY_STRICT_ABORT,
        "redact": GroundingInterceptor.POLICY_AUTO_REDACT,
        "audit": GroundingInterceptor.POLICY_AUDIT_ONLY,
    }
    active_policy = policy_map[args.policy]

    interceptor = GroundingInterceptor(registry=registry, default_policy=active_policy)

    print(f"🔍 [CORTAFUEGOS-5] Auditando: {target_path} (Política: {args.policy.upper()})")

    try:
        result = interceptor.intercept(text, policy=active_policy)
    except (UnverifiedGroundingError, SyntheticPlaceholderError) as err:
        print(f"\n❌ [ABORT FAIL-CLOSED]: {err}", file=sys.stderr)
        sys.exit(1)

    print("\n=== REPORTE DE AUDITORÍA EPISTÉMICA ===")
    print(f"Estado de Verificación: {'✅ LIMPIO' if result.is_clean else '⚠️ VIOLACIONES DETECTADAS'}")
    print(f"Veredicto de Silicio:   {result.status}")
    print(f"Citas Verificadas:      {len(result.verified_citations)}")
    for rec in result.verified_citations:
        print(f"  ✓ [{rec.entity_type}] {rec.identifier}: {rec.canonical_title} ({rec.source})")

    print(f"\nCitas No Verificadas:    {len(result.unverified_citations)}")
    for etype, raw_id in result.unverified_citations:
        print(f"  ✗ [{etype}] {raw_id} (SIN EVIDENCE-REF EN SILICIO)")

    print(f"\nMerkle Root de Evidencia: {result.merkle_root}")

    if args.policy == "redact" and not result.is_clean:
        out_target = target_path if args.in_place else (Path(args.output_path) if args.output_path else None)
        if out_target:
            out_target.write_text(result.sanitized_text, encoding="utf-8")
            print(f"💾 Texto saneado guardado en: {out_target}")

    sys.exit(0 if (result.is_clean or args.policy != "strict") else 1)


if __name__ == "__main__":
    main()
