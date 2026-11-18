#!/usr/bin/env python3
"""Tests de verificación para C5-UNIVERSAL-AUTOROUTE v3.0.

Valida los 6 ejes de universalidad sin modificar la carpeta congelada tests/*:
1. Agnosticismo ante modelos futuros o desconocidos y separación Modelo != Esfuerzo.
2. Detección exacta de 'Gemini 4 Hydrogen Extra' (sobre-esfuerzo en pesos ligeros).
3. Gravedad e histéresis de KV-Cache (preservación de familia con contexto acumulado > 32K).
4. Bloqueo de soberanía S0_LOCAL_AIRGAP (secretos crudos nunca van a GPT-OSS 120B remoto).
5. Herencia de '/plan' aprobado ('Comments on artifact URI:') y deduplicación anti-spam.
6. Portabilidad multiplataforma (cero rutas temporales o de usuario fijas) y latencia O(1) < 100 us.
"""

from __future__ import annotations

import json
from pathlib import Path
import sys
import time

repo_root = Path(__file__).absolute().parents[2]
kish_root = repo_root / "01_KISH_ENGINE"
for candidate in (repo_root, kish_root):
    if str(candidate) not in sys.path and candidate.is_dir():
        sys.path.insert(0, str(candidate))

from babylon60.cognitive_pilot.universal_autoroute import (  # noqa: E402
    classify_universal_capability,
    evaluate_universal_route,
    extract_latest_task_context,
    parse_universal_selector,
)
from scripts.guards.c5_signature_engine import (  # noqa: E402
    classify_capability_tier,
    evaluate_selector_fitness,
    format_pre_invocation_audit_line,
    parse_selector_string,
)


def test_hydrogen_extra_space_and_paren_parsing_and_overburn() -> None:
    # Etiqueta literal de la UI de Antigravity (sin paréntesis)
    m_ui, mode_ui = parse_selector_string("Gemini 4 Hydrogen Extra")
    assert m_ui == "Gemini 4 Hydrogen"
    assert mode_ui == "Extra"

    #Conserva tier == 1 para compatibilidad con test_c5_signature_engine, pero marca effort_overburn
    cap = classify_capability_tier(m_ui, mode_ui)
    assert cap["tier"] == 1
    assert cap["reasoning_effort"] == "extra"
    assert cap["effort_overburn"] is True

    # En consulta trivial, recomienda bajar razonamiento sin exigir cambiar de familia
    verdict = evaluate_universal_route(
        m_ui,
        mode_ui,
        "¿Qué hora es?",
        host="antigravity_ui",
        session_id=f"test-h-extra-{time.time_ns()}",
    )
    assert verdict.recommended_action == "lower_effort"
    assert verdict.constitutional_notice is not None
    assert "bajar razonamiento" in verdict.constitutional_notice


def test_architecture_design_and_multimodal_not_misclassified_as_tier1() -> None:
    # El caso real del turno inicial: "DISEÑA UN AUTOROUTE" en Carbon (High) u Orchestrator (Argon)
    res_carbon = evaluate_selector_fitness(
        "Gemini 4 Carbon (High)",
        "High",
        "DISEÑA UN AUTOROUTE [MEDIA_UPLOADED]",
    )
    assert res_carbon["status"] == "ÓPTIMO"

    res_orch = evaluate_selector_fitness(
        "Orchestrator (Argon)",
        "Orchestrator",
        "DISEÑA UN AUTOROUTE",
    )
    assert res_orch["status"] == "ÓPTIMO"


def test_future_unknown_models_and_generic_host_fallback() -> None:
    # Modelo futuro desconocido en un host genérico sin perfil prefijado
    m_fut, mode_fut = parse_universal_selector("VendorX-Quantum-7 (Low)")
    cap = classify_universal_capability(m_fut, mode_fut)
    assert cap["tier"] == 2
    assert cap["reasoning_effort"] == "low"

    verdict = evaluate_universal_route(
        "VendorX-Quantum-7 (Low)",
        "Low",
        "Verificar formalmente en Lean 4 la invariante del Seqlock.",
        host="unknown_future_ide",
    )
    assert verdict.status == "DESAJUSTADO"
    assert verdict.concrete_option is None
    assert "Estrato 3" in verdict.capability_description
    assert verdict.constitutional_notice is not None
    assert "VendorX" in verdict.constitutional_notice or "Estrato 3" in verdict.constitutional_notice


def test_airgap_secrets_never_route_to_remote_gpt_oss() -> None:
    secret_prompt = (
        "Analiza esta clave privada:\n"
        "-----BEGIN OPENSSH PRIVATE KEY-----\n"
        "b3BlbnNzaC1rZXktdjEAAAAABG5vbmU=\n"
    )
    # Incluso si el usuario está en GPT-OSS 120B (Medium), se detecta que es remoto y exige loopback
    verdict = evaluate_universal_route(
        "GPT-OSS 120B (Medium)",
        "Medium",
        secret_prompt,
        host="antigravity_ui",
    )
    assert verdict.status == "DESAJUSTADO"
    assert verdict.recommended_action == "route_local_airgap"
    assert verdict.sdk_guardrails["require_loopback"] is True
    assert verdict.concrete_option is not None
    assert "127.0.0.1" in verdict.concrete_option or "litert://" in verdict.concrete_option

    # Si ya corre en un modelo loopback local (LiteRT / Ollama), es ÓPTIMO
    verdict_local = evaluate_universal_route(
        "litert://gemma4-26b",
        "Standard",
        secret_prompt,
        host="local_loopback",
    )
    assert verdict_local.status == "ÓPTIMO"
    assert verdict_local.recommended_action == "keep"


def test_kv_cache_hysteresis_prefers_same_family_on_large_context() -> None:
    # Con >32K tokens acumulados en familia claude-5.5, para una tarea Estrato 2 sugiere
    # mantener la familia claude-5.5 (Claude Sonnet 5.5) incluso en antigravity_ui
    verdict = evaluate_universal_route(
        "Claude Opus 5.5",
        "High",
        "Implementa la función de validación en auth.py",
        host="antigravity_ui",
        context_tokens=64_000,
    )
    assert verdict.recommended_action == "lower_effort"
    assert verdict.concrete_option is not None
    assert "Claude Sonnet 5.5" in verdict.concrete_option


def test_plan_artifact_approval_inheritance_and_anti_nagging_suppression(tmp_path: Path) -> None:
    artifact = tmp_path / "implementation_plan.md"
    artifact.write_text(
        "# Plan de Implementación en ~/10_PROJECTS/BABYLON-60\n"
        "Implementa universal_autoroute.py y c5_signature_engine.py.\n",
        encoding="utf-8",
    )
    transcript = tmp_path / "transcript.jsonl"
    step = {
        "step_index": 0,
        "type": "USER_INPUT",
        "content": (
            f"Comments on artifact URI: {artifact.as_uri()}\n\n"
            "The user has approved this document.\n\n"
            "<USER_REQUEST>\n\n</USER_REQUEST>\n"
            "<USER_SETTINGS_CHANGE>\n"
            "The user changed setting `Model Selection` from Carbon to Orchestrator (Argon).\n"
            "</USER_SETTINGS_CHANGE>"
        ),
    }
    transcript.write_text(json.dumps(step) + "\n", encoding="utf-8")

    task_text, _, _, _ = extract_latest_task_context(transcript)
    assert "ejecuta el plan aprobado" in task_text
    assert "universal_autoroute.py" in task_text

    audit_line = format_pre_invocation_audit_line(
        transcript, hook_payload={"conversationId": "conv-plan-approve-1"}
    )
    assert "VEREDICTO = ÓPTIMO" in audit_line

    # Prueba de deduplicación anti-spam (presentation.md L114):
    # El primer aviso se emite; el segundo idéntico en la misma sesión se suprime.
    sess_id = f"dedup-sess-{time.time_ns()}"
    v1 = evaluate_universal_route(
        "Gemini 4 Carbon (High)",
        "High",
        "¿Qué hora es?",
        session_id=sess_id,
    )
    v2 = evaluate_universal_route(
        "Gemini 4 Carbon (High)",
        "High",
        "¿Qué día es?",
        session_id=sess_id,
    )
    assert v1.notice_suppressed is False
    assert v1.constitutional_notice is not None
    assert v2.notice_suppressed is True
    assert v2.constitutional_notice is None


def test_cross_platform_hygiene_and_sub_100us_latency() -> None:
    src_path = kish_root / "babylon60" / "cognitive_pilot" / "universal_autoroute.py"
    source_code = src_path.read_text(encoding="utf-8")
    assert '"/tmp/' not in source_code and "'/tmp/" not in source_code
    assert "/Users/" not in source_code
    assert "tempfile.gettempdir()" in source_code

    t0 = time.perf_counter_ns()
    iterations = 500
    for i in range(iterations):
        evaluate_universal_route(
            "Orchestrator (Argon)",
            "Orchestrator",
            f"Implementa ajuste en archivo_{i % 3}.py",
        )
    avg_us = ((time.perf_counter_ns() - t0) / 1_000.0) / iterations
    assert avg_us < 100.0, f"Latencia media excesiva: {avg_us:.2f} us (límite 100 us)"


def test_mcp_babylon_autoroute_evaluate_tool(tmp_path: Path) -> None:
    from babylon60.mcp.cortex_mcp_server import CortexMCPServer

    server = CortexMCPServer(
        ledger_path=tmp_path / "ledger.db",
        mail_ledger_path=tmp_path / "mail.db",
        causal_gate_path=tmp_path / "causal.db",
    )
    list_res = server.process_request({"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}})
    assert list_res is not None
    tools = list_res["result"]["tools"]
    autoroute_tools = [t for t in tools if t["name"] == "babylon_autoroute_evaluate"]
    assert len(autoroute_tools) == 1
    # Al ser read-only, no debe exigir babylon60/authorization
    assert "_meta" not in autoroute_tools[0]

    call_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "babylon_autoroute_evaluate",
                "arguments": {
                    "prompt": "Verificar formalmente en Lean 4 la invariante del Seqlock.",
                    "model": "Orchestrator (Carbon)",
                    "host": "antigravity_ui",
                },
            },
        }
    )
    assert call_res is not None
    result = call_res["result"]
    assert result["isError"] is False
    structured = result["structuredContent"]
    assert structured["status"] == "ÓPTIMO"
    assert structured["optimal"]["tier"] == 3

    # También debe responder por su alias canónico cortex_autoroute_evaluate
    alias_res = server.process_request(
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "cortex_autoroute_evaluate",
                "arguments": {
                    "prompt": "¿Qué hora es?",
                    "model": "Gemini 4 Hydrogen Extra",
                    "host": "antigravity_ui",
                },
            },
        }
    )
    assert alias_res is not None
    alias_structured = alias_res["result"]["structuredContent"]
    assert alias_structured["recommended_action"] == "lower_effort"

