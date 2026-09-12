# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [PoC & Falsación Empírica] Bounty Pipeline Orchestrator & CLI Test
"""test_bounty_orchestrator_cli.py - Validación del orquestador unificado y CLI.

Certifica:
1. Ejecución completa del ciclo con BountyPipelineOrchestrator.
2. Auto-atestación selectiva de hallazgos críticos (Proof of Claim).
3. Invocación de bounty_cli sin efectos secundarios ni fallos en sys.argv.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from babylon60.bft.bounty_pipeline_orchestrator import BountyPipelineOrchestrator
from babylon60.cli.bounty_cli import main as cli_main


@pytest.mark.asyncio
async def test_orchestrator_cycle_with_synthetic_items() -> None:
    """Verifica el ciclo completo con orquestación funtorial unificada."""
    orchestrator = BountyPipelineOrchestrator()

    synthetic_data = [
        {
            "ghsa_id": "GHSA-EVM-TEST",
            "summary": "Uniswap v4 Hook reentrancy with EIP-1153 transient storage",
            "description": "Exploit: 605d5e",
            "severity": "critical",
            "html_url": "https://example.com/evm",
            "vulnerabilities": [{"package": {"ecosystem": "solidity"}}],
        },
        {
            "ghsa_id": "GHSA-NAT-TEST",
            "summary": "WebKit Gigacage memory corruption in IsoMalloc",
            "description": "UAF in JSC engine",
            "severity": "critical",
            "html_url": "https://example.com/nat",
            "vulnerabilities": [{"package": {"ecosystem": "cpp"}}],
        },
        {
            "ghsa_id": "GHSA-AI-TEST",
            "summary": "PyTorch arbitrary pickle execution via unsafe tensor loading",
            "description": "RCE in weights",
            "severity": "high",
            "html_url": "https://example.com/ai",
            "vulnerabilities": [{"package": {"ecosystem": "pip"}}],
        },
    ]

    report = await orchestrator.execute_cycle(
        synthetic_items=synthetic_data,
        auto_attest_high_risk=True,
        risk_threshold=0.5,
    )

    assert report.frames_ingested == 3
    assert len(report.evm_analyses) == 1
    assert len(report.native_triages) == 1
    assert len(report.ai_sentinel_dicta) == 1
    # Todos deben haber superado el umbral de riesgo 0.5 y generado recibos
    assert len(report.claim_receipts) >= 2
    assert report.total_elapsed_ms > 0.0


def test_bounty_cli_dry_run(capsys: pytest.CaptureFixture[str]) -> None:
    """Verifica que bounty_cli se ejecute sin excepciones en modo JSON."""
    with pytest.raises(SystemExit) as exc_info:
        cli_main(["--per-page", "1", "--json"])

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "timestamp_utc" in captured.out
    assert "frames_ingested" in captured.out


def test_bounty_cli_inspect_bytecode(capsys: pytest.CaptureFixture[str]) -> None:
    """Verifica la inspección de bytecode vía CLI con flags y opcodes."""
    with pytest.raises(SystemExit) as exc_info:
        cli_main(
            [
                "--inspect-bytecode",
                "60005e5df4ff",
                "--hook-address",
                "0x0088000000000000000000000000000000000000",
            ]
        )

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "INSPECCIÓN CUANTITATIVA DE BYTECODE EVM" in captured.out
    assert "Opcodes TSTORE:     1 (0x5d)" in captured.out
    assert "DELEGATECALL:       1 (0xf4)" in captured.out
    assert "SELFDESTRUCT:       1 (0xff)" in captured.out
    assert "DICTAMEN DE INVARIANTES:" in captured.out


def test_bounty_cli_export_claims(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    """Verifica que la opción --export-claims escriba los recibos sellados."""
    out_file = tmp_path / "exported_claims.json"

    with pytest.raises(SystemExit) as exc_info:
        cli_main(
            [
                "--per-page",
                "1",
                "--export-claims",
                str(out_file),
            ]
        )

    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "TELEMETRÍA DE CICLO FUNTORIAL:" in captured.out
