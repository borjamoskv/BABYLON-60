"""Tests para el motor de firma canónica C5-REAL y auditoría agnóstica de selector."""

import json
from pathlib import Path

from scripts.guards.c5_signature_engine import (
    classify_capability_tier,
    detect_active_model_and_mode,
    evaluate_selector_fitness,
    format_pre_invocation_audit_line,
    generate_signature,
)
from scripts.guards.verify_active_topology import validate_text


def test_generate_signature_passes_validator():
    body = "Cuerpo de prueba para validación de firma en silicio con alta exergía C5-REAL."
    sig = generate_signature(body, mutation="Ninguna (test unitario)")
    full_text = f"{body}\n\n{sig}"

    errors = validate_text(full_text, response=True)
    assert errors == [], f"La firma generada no pasó el validador: {errors}"


def test_signature_contains_darwin_thermal_and_exergy():
    body = "Texto de evaluación de prueba con suficiente longitud para medir la exergía."
    sig = generate_signature(body)

    assert "[ LLM ]: " in sig
    assert "[ MODO COGNITIVO ]: " in sig
    assert "[ TOPOLOGÍA ACTIVA ]: MOSKV-1" in sig
    assert "[ RÉGIMEN TÉRMICO ]: Nominal" in sig or "[ RÉGIMEN TÉRMICO ]: Degradado" in sig
    assert "[ EXERGÍA INFORMATIVA ]: " in sig
    assert "/ 21.000 (c5-lexical-v2)" in sig
    assert "[ MUTACIÓN CAUSAL ]: " in sig


def test_agnostic_capability_tier_classification():
    # Estrato 1 — Modelos ligeros/rápidos de cualquier proveedor (sin confundir "gemini" con "mini")
    assert classify_capability_tier("Gemini 3.8 Flash", "High (Fast)")["tier"] == 1
    assert classify_capability_tier("claude-4-haiku", "Standard")["tier"] == 1
    assert classify_capability_tier("gpt-6-mini", "low")["tier"] == 1
    assert classify_capability_tier("Unknown-Model-X", "Fast")["tier"] == 1

    # Estrato 2 — Ejecución acotada (Low y Medium) sin depender de nombres fijos
    t2_low = classify_capability_tier("Gemini 4 Argon (Low)", "Low")
    assert t2_low["tier"] == 2 and t2_low["effort"] == "low"

    t2_sonnet = classify_capability_tier("Claude Sonnet 5.5", "Low")
    assert t2_sonnet["tier"] == 2 and t2_sonnet["effort"] == "low"

    t2_med = classify_capability_tier("Future-Frontier-LLM", "Medium")
    assert t2_med["tier"] == 2 and t2_med["effort"] == "medium"

    # Estrato 3 — Razonamiento profundo / Apex
    t3_argon = classify_capability_tier("Gemini 4 Argon (High)", "High")
    assert t3_argon["tier"] == 3 and t3_argon["effort"] == "high"

    t3_opus = classify_capability_tier("Claude Opus 5.5", "Extended thinking")
    assert t3_opus["tier"] == 3 and t3_opus["effort"] == "high"

    # Estrato 0 — No expuesto
    assert classify_capability_tier("No expuesto", "No expuesto")["tier"] == 0


def test_selector_fitness_optimal_and_mismatched():
    # 1. Consulta corta con modelo pesado en High -> DESAJUSTADO (Óptimo: Estrato 1 Fast)
    res_overkill = evaluate_selector_fitness(
        "Gemini 4 Argon (High)",
        "High",
        "¿Esto solo funciona con el comando?",
    )
    assert res_overkill["status"] == "DESAJUSTADO"
    assert "Estrato 1" in str(res_overkill["llm_field"])
    assert res_overkill["warning"] is not None

    # 2. Contrato cerrado (<=4 archivos) en nivel Low -> ÓPTIMO (Estrato 2 Low)
    contract_prompt = (
        "🎯 [CONTRATO /GOAL BLOQUEADO]\n"
        "🔄 ROTAR SELECTOR A: Cualquier Frontera | NIVEL: Low\n"
        "1. OBJETIVO EXACTO: Implementar broker AF_UNIX.\n"
        "2. ARCHIVOS PERMITIDOS (Write): src/a.rs, src/b.rs\n"
    )
    res_contract_ok = evaluate_selector_fitness("Claude Sonnet 5.5", "Low", contract_prompt)
    assert res_contract_ok["status"] == "ÓPTIMO"
    assert "ÓPTIMO: Estrato 2" in str(res_contract_ok["llm_field"])
    assert res_contract_ok["warning"] is None

    # 3. Verificación formal Ring-0 (Lean 4 / Seqlock) en High -> ÓPTIMO (Estrato 3 High)
    res_ring0_ok = evaluate_selector_fitness(
        "Any-Apex-Model",
        "High",
        "Verificar formalmente en Lean 4 la invariante de concurrencia del Seqlock.",
    )
    assert res_ring0_ok["status"] == "ÓPTIMO"
    assert "Estrato 3" in str(res_ring0_ok["llm_field"])


def test_transcript_and_env_detection(tmp_path: Path) -> None:
    # Detección por variables de entorno agnósticas (ej. Claude Code)
    model, mode, source = detect_active_model_and_mode(
        env={"ANTHROPIC_MODEL": "claude-sonnet-5-5", "CLAUDE_CODE_EFFORT": "low"}
    )
    assert model == "claude-sonnet-5-5"
    assert mode == "low"
    assert source == "env Claude"

    # Detección por hook payload directo
    hp_model, hp_mode, hp_source = detect_active_model_and_mode(
        hook_payload={"model": "Future-LLM-7", "effort": "Medium"}
    )
    assert hp_model == "Future-LLM-7"
    assert hp_mode == "Medium"
    assert hp_source == "hook payload"

    # Detección desde transcript.jsonl con <USER_SETTINGS_CHANGE>
    transcript = tmp_path / "transcript.jsonl"
    step = {
        "step_index": 0,
        "type": "USER_INPUT",
        "content": (
            "<USER_REQUEST>\nimplementa el parche\n</USER_REQUEST>\n"
            "<USER_SETTINGS_CHANGE>\n"
            "The user changed setting `Model Selection` from None to Gemini 4 Argon (Low).\n"
            "</USER_SETTINGS_CHANGE>"
        ),
    }
    transcript.write_text(json.dumps(step) + "\n", encoding="utf-8")

    t_model, t_mode, t_source = detect_active_model_and_mode(transcript_path=transcript)
    assert t_model == "Gemini 4 Argon (Low)"
    assert t_mode == "Low"
    assert t_source == "selector UI"

    body = "Implementación verificada sobre el árbol de trabajo con contrato acotado."
    sig = generate_signature(body, transcript_path=transcript, mutation="Ninguna (test)")
    assert "ÓPTIMO: Estrato 2" in sig
    assert validate_text(f"{body}\n\n{sig}", response=True, require_selector_verdict=True) == []


def test_continuation_and_dialectical_pulse_inheritance(tmp_path: Path) -> None:
    transcript = tmp_path / "pulse_transcript.jsonl"
    steps = [
        {
            "step_index": 0,
            "type": "USER_INPUT",
            "content": "<USER_REQUEST>\n/goal implementar broker\n</USER_REQUEST>",
        },
        {
            "step_index": 1,
            "type": "PLANNER_RESPONSE",
            "content": (
                "🎯 [CONTRATO /GOAL BLOQUEADO]\n"
                "🔄 ROTAR SELECTOR A: Frontera | NIVEL: Low\n"
                "1. OBJETIVO EXACTO: Implementar broker.\n"
            ),
        },
        {
            "step_index": 2,
            "type": "USER_INPUT",
            "content": (
                "<USER_REQUEST>\nok\n</USER_REQUEST>\n"
                "<USER_SETTINGS_CHANGE>\n"
                "The user changed setting `Model Selection` from Flash to Gemini 4 Argon (Low).\n"
                "</USER_SETTINGS_CHANGE>"
            ),
        },
    ]
    transcript.write_text("\n".join(json.dumps(s) for s in steps) + "\n", encoding="utf-8")

    # El pulso "ok" hereda el contrato Low del turno previo -> ÓPTIMO en Argon (Low)
    audit_line = format_pre_invocation_audit_line(transcript)
    assert "VEREDICTO = ÓPTIMO (Estrato 2 (Ejecución Acotada / Low))" in audit_line

    # Si falta el veredicto en una firma con modelo expuesto y se exige require_selector_verdict:
    raw_no_verdict = (
        "Cuerpo.\n\n```text\n"
        "[ LLM ]: Gemini 4 Argon (Low)\n"
        "[ MODO COGNITIVO ]: Low\n"
        "[ TOPOLOGÍA ACTIVA ]: MOSKV-1\n"
        "[ RÉGIMEN TÉRMICO ]: Nominal\n"
        "[ EXERGÍA INFORMATIVA ]: No medida\n"
        "[ MUTACIÓN CAUSAL ]: Ninguna\n```\n"
    )
    errs = validate_text(raw_no_verdict, response=True, require_selector_verdict=True)
    assert len(errs) == 2
