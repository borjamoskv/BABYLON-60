#!/usr/bin/env python3
"""Motor canónico de cálculo de firma C5-REAL y auditoría universal de selector (MOSKV-1).

Calcula y genera la firma de salida de 6 campos integrando:
1. Detección dinámica agnóstica de plataforma (Antigravity, Claude Code, Codex, Cursor, CLI).
2. Clasificación universal en el Álgebra de Capacidades (Soberanía x Estrato x Esfuerzo x Topología)
   delegada a babylon60.cognitive_pilot.universal_autoroute (sin modelos prefijados en lógica).
3. Herencia causal multi-turno para pulsos somáticos, menciones @[...], aprobaciones /plan
   ("Comments on artifact URI:") y contratos /goal.
4. Telemetría de silicio en tiempo real (Apple Silicon M3 Pro / Darwin) e índice léxico (c5-lexical-v2).
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import asdict
import json
import os
from pathlib import Path
import re
import subprocess
import sys

repo_root = Path(__file__).absolute().parents[2]
kish_root = repo_root / "01_KISH_ENGINE"
for candidate in (repo_root, kish_root):
    if str(candidate) not in sys.path and candidate.is_dir():
        sys.path.insert(0, str(candidate))

from babylon60.cognitive_pilot.universal_autoroute import (  # noqa: E402
    CONTINUATION_PULSES,
    DIALECTICAL_PULSES,
    SETTINGS_CHANGE_RE,
    classify_universal_capability,
    evaluate_universal_route,
    extract_latest_task_context,
    extract_turn_request_with_metadata,
    infer_universal_target,
    parse_universal_selector,
)


def parse_selector_string(selection: str, explicit_mode: str = "") -> tuple[str, str]:
    """Extrae (model_display, mode_display) de cualquier cadena de selector o entorno."""
    return parse_universal_selector(selection, explicit_mode)


def detect_active_model_and_mode(
    transcript_path: Path | None = None,
    env: Mapping[str, str] | None = None,
    hook_payload: Mapping[str, object] | None = None,
) -> tuple[str, str, str]:
    """Detecta (modelo, modo, fuente) de forma agnóstica a la plataforma.

    Orden de prioridad:
    1. Payload directo de hook (ej. Claude Code / Cursor / SDK).
    2. Variables explícitas C5_ACTIVE_MODEL / C5_ACTIVE_MODE.
    3. Variables de entorno del proveedor (Claude Code, Codex/OpenAI, Gemini CLI).
    4. Transcript JSONL de sesión (Antigravity <USER_SETTINGS_CHANGE> o Claude Code message.model).
    5. Fallback canónico: ("No expuesto", "No expuesto", "sin metadatos").
    """
    env_map = os.environ if env is None else env

    if hook_payload:
        hp_model = str(hook_payload.get("model") or "").strip()
        hp_mode = str(
            hook_payload.get("thinking_level")
            or hook_payload.get("effort")
            or hook_payload.get("cognitive_mode")
            or ""
        ).strip()
        if hp_model:
            model, mode = parse_selector_string(hp_model, hp_mode)
            return model, mode, "hook payload"

    c5_model = env_map.get("C5_ACTIVE_MODEL", "").strip()
    c5_mode = env_map.get("C5_ACTIVE_MODE", "").strip()
    if c5_model:
        model, mode = parse_selector_string(c5_model, c5_mode)
        return model, mode, "env C5"

    for model_var, mode_var, provider in (
        ("ANTHROPIC_MODEL", "CLAUDE_CODE_EFFORT", "env Claude"),
        ("CLAUDE_MODEL", "CLAUDE_CODE_EFFORT", "env Claude"),
        ("OPENAI_MODEL", "OPENAI_REASONING_EFFORT", "env OpenAI"),
        ("CODEX_MODEL", "OPENAI_REASONING_EFFORT", "env Codex"),
        ("GEMINI_MODEL", "GEMINI_THINKING_LEVEL", "env Gemini"),
    ):
        val = env_map.get(model_var, "").strip()
        if val:
            model, mode = parse_selector_string(val, env_map.get(mode_var, ""))
            return model, mode, provider

    if transcript_path is not None and transcript_path.is_file():
        try:
            lines = transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines()
            for raw_line in reversed(lines):
                if not raw_line.strip():
                    continue
                record = json.loads(raw_line)
                if record.get("type") == "USER_INPUT":
                    content = str(record.get("content", ""))
                    matches = list(SETTINGS_CHANGE_RE.finditer(content))
                    if matches:
                        selection = matches[-1].group(1).rstrip(".").strip()
                        model, mode = parse_selector_string(selection)
                        return model, mode, "selector UI"
                msg_obj = record.get("message")
                if isinstance(msg_obj, dict) and msg_obj.get("model"):
                    c_model = str(msg_obj["model"]).strip()
                    c_effort = env_map.get("CLAUDE_CODE_EFFORT", "")
                    model, mode = parse_selector_string(c_model, c_effort)
                    return model, mode, "transcript Claude"
        except Exception:
            pass

    return "No expuesto", "No expuesto", "sin metadatos"


def _extract_turn_request_text(content: str) -> str:
    """Extrae el texto del turno expandiendo @[...] y herencias de artefactos aprobados."""
    return extract_turn_request_with_metadata(content)


def extract_latest_user_request(transcript_path: Path | None) -> str:
    """Extrae el contexto de tarea del último turno (con herencia causal para pulsos y /plan)."""
    task_text, _, _, _ = extract_latest_task_context(transcript_path)
    return task_text


def classify_capability_tier(model: str, mode: str) -> dict[str, object]:
    """Clasifica cualquier combinación (LLM, Modo) en los Estratos Universales C5."""
    return classify_universal_capability(model, mode)


def infer_optimal_tier(
    task_text: str = "",
    *,
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
) -> dict[str, object]:
    """Determina el Estrato, Esfuerzo y Topología óptimos requeridos por la tarea activa."""
    target = infer_universal_target(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        task_tier=task_tier,
    )
    return {
        "tier": target.tier,
        "effort": target.effort,
        "reasoning_effort": target.reasoning_effort,
        "topology": target.topology,
        "label": target.label,
        "sovereignty": target.sovereignty,
    }


def _infer_host_from_source(source: str) -> str:
    src_low = source.casefold()
    if "claude" in src_low:
        return "claude_code"
    if "codex" in src_low or "openai" in src_low:
        return "codex_cli"
    if "gemini" in src_low:
        return "gemini_cli"
    if "selector ui" in src_low:
        return "antigravity_ui"
    return "generic"


def evaluate_selector_fitness(
    model: str,
    mode: str,
    task_text: str = "",
    *,
    source: str = "selector UI",
    host: str | None = None,
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
    context_tokens: int = 0,
    rework_failures: int = 0,
    infra_blocked: bool = False,
    contains_unredacted_secrets: bool = False,
    session_id: str | None = None,
) -> dict[str, object]:
    """Evalúa si el LLM y Modo activos son coherentes con el Álgebra Universal e Histéresis."""
    effective_host = host or _infer_host_from_source(source)
    verdict = evaluate_universal_route(
        model,
        mode,
        task_text,
        source=source,
        host=effective_host,
        files_count=files_count,
        has_contract=has_contract,
        task_tier=task_tier,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
        session_id=session_id,
    )
    return asdict(verdict)


def format_pre_invocation_audit_line(
    transcript_path: str | Path | None = None,
    *,
    env: Mapping[str, str] | None = None,
    hook_payload: Mapping[str, object] | None = None,
) -> str:
    """Genera la línea canónica de auditoría de selector para hooks PreInvocation."""
    t_path = Path(transcript_path) if transcript_path else None
    model, mode, source = detect_active_model_and_mode(
        transcript_path=t_path,
        env=env,
        hook_payload=hook_payload,
    )
    task_text, context_tokens, rework_failures, infra_blocked = extract_latest_task_context(t_path)
    if not task_text and hook_payload and hook_payload.get("prompt"):
        task_text = str(hook_payload["prompt"])

    session_id = str(hook_payload.get("conversationId") or "") if hook_payload else None
    fitness = evaluate_selector_fitness(
        model,
        mode,
        task_text,
        source=source,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        session_id=session_id,
    )
    raw_active = fitness.get("active")
    active: dict[str, object] = raw_active if isinstance(raw_active, dict) else {}
    raw_optimal = fitness.get("optimal")
    optimal: dict[str, object] = raw_optimal if isinstance(raw_optimal, dict) else {}

    if fitness["status"] == "NO_EXPUESTO":
        return f"🧠 [AUDITORÍA DE SELECTOR · RING-4]: ACTIVO = No expuesto | TAREA ESTIMADA = {optimal.get('label', 'No expuesto')}"

    if fitness["status"] == "ÓPTIMO":
        verdict = f"ÓPTIMO ({active.get('label', '')})"
        if fitness.get("recommended_action") == "lower_effort" and not fitness.get("notice_suppressed"):
            verdict += " | AVISO = Esfuerzo Extra activo en tarea de triaje (bajar a Low/Medium ahorra cuota)"
    else:
        opt_target = fitness.get("concrete_option") or optimal.get("label", "")
        verdict = f"⚠️ DESAJUSTADO -> Óptimo: {optimal.get('label', '')}"
        if opt_target and str(opt_target) not in str(optimal.get("label", "")) and not fitness.get("notice_suppressed"):
            verdict += f" [Sugerido: {opt_target}]"

    return (
        f"🧠 [AUDITORÍA DE SELECTOR · RING-4]: "
        f"ACTIVO = {model} | Modo: {mode} ({source}) [{active.get('label', '')}] | "
        f"VEREDICTO = {verdict}"
    )


def compute_thermal_regime() -> str:
    from scripts.c5_thermo.silicon_thermal_telemetry import get_thermal_telemetry

    return get_thermal_telemetry()["summary"]


def compute_exergy(body: str, repo_root: Path) -> str:
    oracle_path = repo_root / "scripts/c5_quality_gates/prompt_exergy_oracle.py"
    if not oracle_path.exists():
        return "No medida"
    try:
        res = subprocess.run(
            [sys.executable, str(oracle_path), "--stdin", "--json"],
            input=body,
            capture_output=True,
            text=True,
            check=True,
        )
        data = json.loads(res.stdout)
        score = data.get("text", {}).get("c5_score", 0)
        method = data.get("text", {}).get("method", "c5-lexical-v2")
        return f"{score:,} / 21.000 ({method})".replace(",", ".")
    except Exception:
        return "No medida"


def generate_signature(
    body: str,
    *,
    model: str | None = None,
    mode: str | None = None,
    mutation: str = "Ninguna",
    repo_root: Path | None = None,
    transcript_path: Path | None = None,
    task_text: str = "",
    task_tier: str | None = None,
    audit_selector: bool = True,
) -> str:
    if repo_root is None:
        repo_root = Path(__file__).absolute().parents[2]

    detected_model, detected_mode, source = detect_active_model_and_mode(transcript_path=transcript_path)
    final_model = model if (model is not None and model.strip()) else detected_model
    final_mode = mode if (mode is not None and mode.strip()) else detected_mode

    if audit_selector and final_model != "No expuesto":
        effective_task = task_text or extract_latest_user_request(transcript_path)
        if "ÓPTIMO" not in final_model and "DESAJUSTADO" not in final_model:
            fitness = evaluate_selector_fitness(
                final_model,
                final_mode,
                effective_task,
                source=source,
                task_tier=task_tier,
            )
            final_model = str(fitness["llm_field"])
            final_mode = str(fitness["mode_field"])

    thermal = compute_thermal_regime()
    exergy = compute_exergy(body, repo_root)

    lines = [
        f"[ LLM ]: {final_model}  ",
        f"[ MODO COGNITIVO ]: {final_mode}  ",
        "[ TOPOLOGÍA ACTIVA ]: MOSKV-1  ",
        f"[ RÉGIMEN TÉRMICO ]: {thermal}  ",
        f"[ EXERGÍA INFORMATIVA ]: {exergy}  ",
        f"[ MUTACIÓN CAUSAL ]: {mutation}  ",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--body", type=Path, help="Ruta al archivo con el cuerpo del mensaje")
    parser.add_argument("--model", default=None, help="Modelo activo (si se omite, se auto-detecta)")
    parser.add_argument("--mode", default=None, help="Modo cognitivo activo (si se omite, se auto-detecta)")
    parser.add_argument("--host", default=None, help="Perfil de host opcional (antigravity_ui, claude_code, codex_cli, etc.)")
    parser.add_argument("--transcript", type=Path, default=None, help="Ruta opcional a transcript.jsonl")
    parser.add_argument("--task-text", default="", help="Texto de la tarea o prompt para evaluar adecuación")
    parser.add_argument(
        "--task-tier",
        choices=["fast", "low", "medium", "high", "xhigh", "extra"],
        default=None,
        help="Estrato óptimo explícito de la tarea",
    )
    parser.add_argument("--mutation", default="Ninguna")
    parser.add_argument("--append", action="store_true", help="Adjuntar la firma al archivo de cuerpo")
    parser.add_argument(
        "--check-selector",
        action="store_true",
        help="Imprimir únicamente el diagnóstico JSON de adecuación del selector",
    )
    args = parser.parse_args()

    if args.check_selector:
        det_model, det_mode, source = detect_active_model_and_mode(transcript_path=args.transcript)
        use_model = args.model or det_model
        use_mode = args.mode or det_mode
        task, ctx_tokens, rework_failures, infra_blocked = extract_latest_task_context(args.transcript)
        effective_task = args.task_text or task
        report = evaluate_selector_fitness(
            use_model,
            use_mode,
            effective_task,
            source=source,
            host=args.host,
            task_tier=args.task_tier,
            context_tokens=ctx_tokens,
            rework_failures=rework_failures,
            infra_blocked=infra_blocked,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    repo_root = Path(__file__).absolute().parents[2]
    body_text = args.body.read_text(encoding="utf-8") if args.body else sys.stdin.read()

    sig = generate_signature(
        body_text,
        model=args.model,
        mode=args.mode,
        mutation=args.mutation,
        repo_root=repo_root,
        transcript_path=args.transcript,
        task_text=args.task_text,
        task_tier=args.task_tier,
    )

    if args.append and args.body:
        with args.body.open("a", encoding="utf-8") as f:
            f.write("\n\n" + sig + "\n")
        print(f"Firma adjuntada a {args.body}")
    else:
        print(sig)
    return 0


if __name__ == "__main__":
    sys.exit(main())
