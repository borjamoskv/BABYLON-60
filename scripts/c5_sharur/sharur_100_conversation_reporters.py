#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | SHARUR-3600 CONVERSATION REPORTERS
# ============================================================================
"""
sharur_100_conversation_reporters.py — Data Structures, Cohorts 4-5 & Report Renderers
for the 100-Agent Parallel Swarm for Historic Conversations & Brain Forensics.
Provides Markdown, HTML, and JSON Sitrep generation and rendering utilities.
"""

from __future__ import annotations

import asyncio
import datetime
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AgentResult:
    agent_id: int
    cohort_id: int
    cohort_name: str
    target: str
    verdict: str  # PASS/WARN/FAIL apply only to a stated check; OBSERVED/NOT_EXECUTED otherwise
    exergy_ms: float
    entropy_bits: float | None
    details: str
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class SwarmSitrep:
    timestamp: str
    total_agents: int = 100
    cohorts_executed: int = 5
    passed_agents: int = 0
    warned_agents: int = 0
    failed_agents: int = 0
    info_agents: int = 0
    observed_agents: int = 0
    not_executed_agents: int = 0
    unknown_agents: int = 0
    certification: str = "NOT_ATTESTED"
    evidence_scope: str = "SUPPLIED_CORPUS_AND_REPORTED_RESULTS_ONLY"
    wall_clock_seconds: float = 0.0
    total_conversations_scanned: int = 0
    total_transcripts_parsed: int = 0
    total_transcript_lines: int = 0
    total_user_messages: int = 0
    total_planner_messages: int = 0
    total_tool_calls: int = 0
    total_artifacts_scanned: int = 0
    total_brain_bytes: int = 0
    average_shannon_entropy: float | None = None
    exergy_score: float | None = None
    results: list[AgentResult] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Cohorte 4: Topología MASS, Deskimming & Artefactos (Agentes 060-079)
# ---------------------------------------------------------------------------
async def run_cohort_4(agent_id: int, corpus: Any, sem: asyncio.Semaphore) -> AgentResult:
    """Report supplied corpus observations; unimplemented controls remain unexecuted."""
    async with sem:
        t0 = time.perf_counter()
        target = f"Topology control {agent_id:03d}"
        verdict = "NOT_EXECUTED"
        details = "Control no ejecutado: no existe un comprobador en este reporter."
        metrics: dict[str, Any] = {"check_status": "NOT_EXECUTED"}
        if agent_id == 60:
            target = "Corpus artifact census"
            metrics = {"total_artifacts": len(corpus.artifacts)}
        elif agent_id == 61:
            target = "Corpus artifact extensions"
            metrics = {"extensions": corpus.artifacts_by_ext}
        elif agent_id == 62:
            target = "Scripts recorded in corpus"
            metrics = {"orphan_scripts": corpus.scripts_in_brain}
            verdict = "PASS" if len(corpus.scripts_in_brain) <= 5 else "WARN"
            details = "Umbral local: hasta cinco scripts registrados; no comprueba reubicación ni seguridad."
        elif agent_id == 63:
            target = "Markdown artifact census"
            metrics = {"markdown_crystals": corpus.artifacts_by_ext.get(".md", 0)}
        elif agent_id == 66:
            target = "Mutations recorded in supplied corpus"
            metrics = {
                "total_mutations": sum(corpus.target_files_mutated.values()),
                "hotspots": sorted(corpus.target_files_mutated.items(), key=lambda x: x[1], reverse=True)[:5],
            }
        elif agent_id == 71:
            target = "Large files recorded in corpus"
            size_mb = sum(f["size"] for f in corpus.large_files) / (1024 * 1024)
            metrics = {"large_files_count": len(corpus.large_files), "large_files_mb": size_mb}
            verdict = "PASS" if size_mb < 1500 else "WARN"
            details = "Umbral local de tamaño registrado: menos de 1500 MiB; no certifica capacidad física."
        elif agent_id == 75:
            target = "Empty supplied session directories"
            empty = sum(not any(c.iterdir()) for c in corpus.conv_dirs)
            metrics = {"empty_sessions": empty}
            verdict = "PASS" if empty < 30 else "WARN"
            details = "Umbral local: menos de treinta directorios suministrados vacíos."
        if "check_status" not in metrics:
            if verdict == "NOT_EXECUTED":
                verdict = "OBSERVED"
                details = "Conteo del corpus suministrado; sin verificación independiente de sus afirmaciones."
            metrics["check_status"] = "OBSERVED" if verdict == "OBSERVED" else "EXECUTED"
            metrics["scope"] = "SUPPLIED_CORPUS_ONLY"
        return AgentResult(
            agent_id,
            4,
            "COHORT-4-MASS-TOPOLOGY-DESKIMMING",
            target,
            verdict,
            (time.perf_counter() - t0) * 1000,
            None,
            details,
            metrics,
        )


# ---------------------------------------------------------------------------
# Cohorte 5: Perímetros, OPSEC & Memoria Continua (Agentes 080-099)
# ---------------------------------------------------------------------------
async def run_cohort_5(agent_id: int, corpus: Any, sem: asyncio.Semaphore) -> AgentResult:
    """Count supplied observations without certifying hardware, privacy or overall health."""
    async with sem:
        t0 = time.perf_counter()
        target = f"Security control {agent_id:03d}"
        verdict = "NOT_EXECUTED"
        details = "Control no ejecutado: sin comprobación de seguridad, privacidad ni atestación."
        metrics: dict[str, Any] = {"check_status": "NOT_EXECUTED"}
        if agent_id == 80:
            target = "Secret pattern matches supplied by corpus scanner"
            metrics = {"secret_matches": corpus.secret_matches}
            verdict = "WARN" if sum(corpus.secret_matches.values()) > 0 else "PASS"
        elif agent_id == 81:
            target = "GitHub token pattern matches supplied by corpus scanner"
            count = corpus.secret_matches.get("github", 0)
            metrics = {"github_tokens": count}
            verdict = "WARN" if count else "PASS"
        elif agent_id == 82:
            target = "Private-key pattern matches supplied by corpus scanner"
            count = corpus.secret_matches.get("ssh", 0)
            metrics = {"ssh_keys": count}
            verdict = "FAIL" if count else "PASS"
        elif agent_id == 87:
            target = "Biometric command mentions in supplied logs"
            metrics = {"touch_id_invocations": corpus.touch_id_invocations, "hardware_verified": False}
        elif agent_id == 92:
            target = "Preferences recorded in supplied corpus"
            metrics = {"mined_preferences_count": len(corpus.learned_preferences)}
        elif agent_id == 93:
            target = "Workspace facts recorded in supplied corpus"
            metrics = {"mined_facts_count": len(corpus.learned_workspace_facts)}
        if "check_status" not in metrics:
            if verdict == "NOT_EXECUTED":
                verdict = "OBSERVED"
            details = "Conteo de datos suministrados; no autentica credenciales, hardware ni hechos narrados."
            metrics["check_status"] = "OBSERVED" if verdict == "OBSERVED" else "EXECUTED"
            metrics["scope"] = "SUPPLIED_CORPUS_ONLY"
        if agent_id == 99:
            metrics.update(certification="NOT_ATTESTED", health_index=None)
        return AgentResult(
            agent_id,
            5,
            "COHORT-5-PERIMETERS-OPSEC-CONTINUAL-MEMORY",
            target,
            verdict,
            (time.perf_counter() - t0) * 1000,
            None,
            details,
            metrics,
        )


# ---------------------------------------------------------------------------
# Report Renderers (Markdown, HTML, JSON)
# ---------------------------------------------------------------------------
def compile_swarm_sitrep(corpus: Any, results: list[AgentResult], wall_clock: float) -> SwarmSitrep:
    passed = sum(1 for r in results if r.verdict == "PASS")
    return SwarmSitrep(
        timestamp=datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z"),
        total_agents=len(results),
        cohorts_executed=len({r.cohort_id for r in results}),
        passed_agents=passed,
        warned_agents=sum(1 for r in results if r.verdict == "WARN"),
        failed_agents=sum(1 for r in results if r.verdict == "FAIL"),
        info_agents=sum(1 for r in results if r.verdict == "INFO"),
        observed_agents=sum(1 for r in results if r.verdict == "OBSERVED"),
        not_executed_agents=sum(1 for r in results if r.verdict == "NOT_EXECUTED"),
        unknown_agents=sum(
            1 for r in results if r.verdict not in {"PASS", "WARN", "FAIL", "INFO", "OBSERVED", "NOT_EXECUTED"}
        ),
        wall_clock_seconds=round(wall_clock, 4),
        total_conversations_scanned=len(corpus.conv_dirs),
        total_transcripts_parsed=len(corpus.transcripts),
        total_transcript_lines=corpus.total_lines,
        total_user_messages=len(corpus.user_messages),
        total_planner_messages=len(corpus.planner_messages),
        total_tool_calls=sum(corpus.tool_calls_counter.values()),
        total_artifacts_scanned=len(corpus.artifacts),
        total_brain_bytes=corpus.total_brain_bytes,
        average_shannon_entropy=round(sum(corpus.entropy_samples) / len(corpus.entropy_samples), 3)
        if corpus.entropy_samples
        else None,
        exergy_score=None,
        results=results,
    )


def render_markdown_report(sitrep: SwarmSitrep) -> str:
    lines = [
        "# SHARUR-3600 :: 100-Agent Conversation Forensic Sitrep",
        f"- **Timestamp:** `{sitrep.timestamp}`",
        f"- **Conversations Scanned:** `{sitrep.total_conversations_scanned}`",
        f"- **Transcripts Parsed:** `{sitrep.total_transcripts_parsed}` ({sitrep.total_transcript_lines:,} lines)",
        f"- **Verdicts:** PASS={sitrep.passed_agents} | WARN={sitrep.warned_agents} | FAIL={sitrep.failed_agents} | INFO={sitrep.info_agents} | OBSERVED={sitrep.observed_agents} | NOT_EXECUTED={sitrep.not_executed_agents} | UNKNOWN={sitrep.unknown_agents}",
        "- **Exergy Score:** `NOT_MEASURED`",
        f"- **Certification:** `{sitrep.certification}`",
        "",
        "| Agent | Cohort | Target | Verdict | Details |",
        "| :--- | :--- | :--- | :---: | :--- |",
    ]
    for r in sitrep.results:
        lines.append(f"| `{r.agent_id:03d}` | `{r.cohort_name}` | {r.target} | **{r.verdict}** | {r.details} |")
    return "\n".join(lines) + "\n"


def render_html_report(sitrep: SwarmSitrep) -> str:
    rows = "\n".join(
        f"<tr><td>{r.agent_id:03d}</td><td>{r.cohort_name}</td><td>{r.target}</td>"
        f"<td><strong>{r.verdict}</strong></td><td>{r.details}</td></tr>"
        for r in sitrep.results
    )
    return (
        "<!DOCTYPE html><html lang='es'><head><meta charset='utf-8'>"
        "<title>SHARUR-3600 Sitrep</title></head><body>"
        f"<h1>SHARUR-3600 Conversation Forensic Sitrep ({sitrep.timestamp})</h1>"
        f"<p>PASS: {sitrep.passed_agents} | WARN: {sitrep.warned_agents} | FAIL: {sitrep.failed_agents} | OBSERVED: {sitrep.observed_agents} | NOT_EXECUTED: {sitrep.not_executed_agents} | {sitrep.certification} | Exergy: NOT_MEASURED</p>"
        f"<table><thead><tr><th>ID</th><th>Cohort</th><th>Target</th><th>Verdict</th><th>Details</th></tr></thead><tbody>{rows}</tbody></table>"
        "</body></html>\n"
    )


def emit_sitrep_reports(sitrep: SwarmSitrep, scripts_dir: Path, audit_dir: Path) -> None:
    sitrep_dict = asdict(sitrep)
    out_json = scripts_dir / "sharur_100_conversations_sitrep.json"
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(sitrep_dict, f, indent=2, ensure_ascii=False)

    out_audit = audit_dir / "sharur_100_conversations_sitrep.json"
    with open(out_audit, "w", encoding="utf-8") as f:
        json.dump(sitrep_dict, f, indent=2, ensure_ascii=False)

    print(f"\n[✓] Sitrep JSON guardado en: {out_json}")
    print(f"[✓] Sitrep JSON respaldado en: {out_audit}")
