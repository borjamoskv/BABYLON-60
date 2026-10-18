#!/usr/bin/env python3
"""Motor canónico de cálculo de firma C5-REAL y auditoría agnóstica de selector (MOSKV-1).

Calcula y genera la firma de salida de 6 campos integrando:
1. Detección dinámica agnóstica de plataforma (Antigravity, Claude Code, Codex, Cursor, CLI).
2. Clasificación universal en 3 Estratos de Capacidad/Esfuerzo (sin modelos prefijados).
3. Herencia causal multi-turno para pulsos somáticos ("ok", "sigue", "itera", "ejecuta") y contratos /goal.
4. Telemetría de silicio en tiempo real (Apple Silicon M3 Pro / Darwin) y exergía léxica (c5-lexical-v2).
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import os
from pathlib import Path
import re
import subprocess
import sys


repo_root = Path(__file__).resolve().parents[2]
if str(repo_root) not in sys.path:
    sys.path.insert(0, str(repo_root))

SETTINGS_CHANGE_RE = re.compile(
    r"setting `Model Selection` from .*? to (.*?)(?:\.\s*No need|\.\s*$|\n|$)",
    re.IGNORECASE,
)
USER_REQUEST_RE = re.compile(
    r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>",
    re.DOTALL,
)
CONTRACT_LEVEL_RE = re.compile(
    r"ROTAR SELECTOR A:.*?\|\s*NIVEL:\s*([A-Za-zÁÉÍÓÚáéíóú0-9_() -]+)",
    re.IGNORECASE,
)
CONTINUATION_PULSES = frozenset(
    {
        "ok",
        "dale",
        "sigue",
        "procede",
        "adelante",
        "ejecuta",
        "ejecútalo",
        "ejecutalo",
        "hazlo",
        "si",
        "sí",
        "go",
        "continue",
    }
)
DIALECTICAL_PULSES = frozenset(
    {
        "itera",
        "itrera",
        "itra",
        "iteraa",
        "iytera",
        "falsabiliza",
        "falsabilia",
        "falsabliza",
        "falsa",
        "apex",
        "salto topológico",
        "salto topologico",
    }
)


def parse_selector_string(selection: str, explicit_mode: str = "") -> tuple[str, str]:
    """Extrae (model_display, mode_display) de cualquier cadena de selector o entorno."""
    raw = selection.strip()
    if not raw or raw.casefold() in {"none", "unknown", "no expuesto", "n/a"}:
        return "No expuesto", "No expuesto"

    if explicit_mode and explicit_mode.strip():
        return raw, explicit_mode.strip()

    # Caso: "Gemini 3.8 Flash High (Fast)"
    m_flash_fast = re.match(r"^(.*?)\s+(High\s*\(Fast\)|Fast|Low|Medium|High)$", raw, re.IGNORECASE)
    if m_flash_fast:
        return m_flash_fast.group(1).strip(), m_flash_fast.group(2).strip()

    # Caso: "Gemini 4 Argon (High)" o "GPT-OSS 120B (Medium)"
    m_paren = re.search(r"\(([^()]+)\)\s*$", raw)
    if m_paren:
        inner = m_paren.group(1).strip()
        if inner.casefold() in {
            "low",
            "medium",
            "high",
            "fast",
            "high (fast)",
            "max",
            "máx",
            "máximo",
            "extended",
        }:
            return raw, inner

    # Inferencia limpia de modo por nombre si el host solo expone el ID del modelo
    low_raw = raw.casefold()
    if re.search(r"\b(flash|haiku|mini|nano|lite|instant)\b", low_raw):
        return raw, "Fast"
    if re.search(r"\b(opus|o1|o3|ultra|deep)\b", low_raw):
        return raw, "High"
    return raw, "Standard"


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
            hook_payload.get("thinking_level") or hook_payload.get("effort") or hook_payload.get("cognitive_mode") or ""
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
                # Formato Antigravity: <USER_SETTINGS_CHANGE> en USER_INPUT
                if record.get("type") == "USER_INPUT":
                    content = str(record.get("content", ""))
                    matches = list(SETTINGS_CHANGE_RE.finditer(content))
                    if matches:
                        selection = matches[-1].group(1).rstrip(".").strip()
                        model, mode = parse_selector_string(selection)
                        return model, mode, "selector UI"
                # Formato Claude Code JSONL: {"type": "assistant", "message": {"model": "..."}}
                msg_obj = record.get("message")
                if isinstance(msg_obj, dict) and msg_obj.get("model"):
                    c_model = str(msg_obj["model"]).strip()
                    c_effort = env_map.get("CLAUDE_CODE_EFFORT", "")
                    model, mode = parse_selector_string(c_model, c_effort)
                    return model, mode, "transcript Claude"
        except Exception:
            pass

    return "No expuesto", "No expuesto", "sin metadatos"


def extract_latest_user_request(transcript_path: Path | None) -> str:
    """Extrae el contexto de tarea del último turno (con herencia causal para pulsos breves)."""
    if transcript_path is None or not transcript_path.is_file():
        return ""
    try:
        lines = transcript_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        user_requests: list[str] = []
        recent_contracts: list[str] = []

        for raw_line in reversed(lines):
            if not raw_line.strip():
                continue
            record = json.loads(raw_line)
            rtype = record.get("type")
            content = str(record.get("content", ""))
            if rtype == "USER_INPUT":
                m = USER_REQUEST_RE.search(content)
                req = m.group(1).strip() if m else content.strip()
                if req:
                    user_requests.append(req)
            elif rtype == "PLANNER_RESPONSE" and (
                "CONTRATO /GOAL BLOQUEADO" in content or "ROTAR SELECTOR A:" in content
            ):
                recent_contracts.append(content)
            if len(user_requests) >= 3 and recent_contracts:
                break

        if not user_requests:
            return ""

        latest = user_requests[0]
        latest_norm = re.sub(r"[/!?.]+", "", latest.casefold()).strip()

        # Si es un pulso de continuación ("ok", "dale", "sigue", "ejecuta"):
        # hereda el contrato /goal emitido por el agente o las peticiones previas del operador.
        if latest_norm in CONTINUATION_PULSES:
            prev_context = " | ".join(user_requests[1:4]) if len(user_requests) > 1 else ""
            if recent_contracts:
                return f"{recent_contracts[0]} [CONTEXTO HILO: {prev_context}]"
            if prev_context:
                return f"{latest} [CONTEXTO PREVIO: {prev_context}]"

        # Si es un pulso dialéctico ("itera", "falsabiliza", "apex"):
        # conserva la marca de iteración más el contexto previo para no degradar a Estrato 1.
        if latest_norm in DIALECTICAL_PULSES:
            prev = " ".join(user_requests[1:3]) if len(user_requests) > 1 else ""
            return f"implementa iteración dialéctica ({latest_norm}) {prev}".strip()

        # Herencia de dominio conversacional: si el turno actual es breve (<120 chars),
        # adjunta el contexto de los últimos 2 turnos del operador para no perder invariantes
        # de dominio (ej. LegalTech, Ring-0) ante pulsos cortos o citas de bloques.
        if len(latest) < 120 and len(user_requests) > 1:
            prev_context = " | ".join(user_requests[1:4])
            return f"{latest} [CONTEXTO HILO: {prev_context}]"

        return latest
    except Exception:
        return ""


def classify_capability_tier(model: str, mode: str) -> dict[str, object]:
    """Clasifica cualquier combinación (LLM, Modo) en los 3 Estratos Universales C5."""
    m_low = model.casefold().strip()
    mode_low = mode.casefold().strip()

    if not m_low or m_low.startswith("no expuesto") or m_low in {"none", "unknown", "n/a"}:
        return {
            "tier": 0,
            "effort": "no_expuesto",
            "label": "No expuesto",
        }

    # Estrato 1 — Triaje / Fast (modelos ligeros/rápidos o esfuerzo mínimo/fast)
    if re.search(r"\b(flash|haiku|mini|nano|lite|instant)\b", m_low) or re.search(
        r"\b(fast|minimal|instant)\b", mode_low
    ):
        return {
            "tier": 1,
            "effort": "fast",
            "label": "Estrato 1 (Triaje / Fast)",
        }

    # Estrato 3 — Razonamiento Profundo / Apex (modelos pesados o esfuerzo High/Max/Extended)
    is_explicit_low_or_med = bool(re.search(r"\b(low|bajo|medium|medio|standard)\b", mode_low))
    is_high_mode = bool(
        re.search(r"\b(high|alto|max|máx|máximo|extended|ultrathink|deep)\b", mode_low)
        or re.search(r"\b(high|max|máx)\b", m_low)
    )
    is_apex_model = bool(re.search(r"\b(opus|o1|o3|ultra)\b", m_low) or "deep-research" in m_low)

    if is_high_mode or (is_apex_model and not is_explicit_low_or_med):
        return {
            "tier": 3,
            "effort": "high",
            "label": "Estrato 3 (Razonamiento Profundo / High)",
        }

    # Estrato 2 — Ejecución Acotada (Low vs Medium)
    if any(k in mode_low for k in ("low", "bajo")) or "(low)" in m_low or "-low" in m_low:
        return {
            "tier": 2,
            "effort": "low",
            "label": "Estrato 2 (Ejecución Acotada / Low)",
        }

    return {
        "tier": 2,
        "effort": "medium",
        "label": "Estrato 2 (Ejecución Acotada / Medium)",
    }


def infer_optimal_tier(
    task_text: str = "",
    *,
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
) -> dict[str, object]:
    """Determina el Estrato y Nivel óptimos requeridos por la tarea activa."""
    if task_tier:
        t_norm = task_tier.casefold().strip()
        if t_norm in {"1", "fast", "triage", "triaje"}:
            return {"tier": 1, "effort": "fast", "label": "Estrato 1 (Triaje / Fast)"}
        if t_norm in {"2", "2-low", "low", "bajo"}:
            return {"tier": 2, "effort": "low", "label": "Estrato 2 (Ejecución Acotada / Low)"}
        if t_norm in {"2-medium", "medium", "medio"}:
            return {"tier": 2, "effort": "medium", "label": "Estrato 2 (Ejecución Acotada / Medium)"}
        if t_norm in {"3", "high", "alto", "max", "apex"}:
            return {"tier": 3, "effort": "high", "label": "Estrato 3 (Razonamiento Profundo / High)"}

    text_low = task_text.casefold()
    norm_pulse = re.sub(r"[/!?.]+", "", text_low).strip()

    # 1. Detección de Contrato /goal explícito en el texto
    m_contract = CONTRACT_LEVEL_RE.search(task_text)
    if m_contract:
        prescribed = m_contract.group(1).casefold()
        if "fast" in prescribed:
            return {"tier": 1, "effort": "fast", "label": "Estrato 1 (Triaje / Fast)"}
        if "high" in prescribed or "max" in prescribed:
            return {"tier": 3, "effort": "high", "label": "Estrato 3 (Razonamiento Profundo / High)"}
        if "medium" in prescribed:
            return {"tier": 2, "effort": "medium", "label": "Estrato 2 (Ejecución Acotada / Medium)"}
        return {"tier": 2, "effort": "low", "label": "Estrato 2 (Ejecución Acotada / Low)"}

    detected_contract = (
        has_contract
        if has_contract is not None
        else ("1. objetivo exacto:" in text_low or "archivos permitidos" in text_low)
    )
    if detected_contract:
        if files_count > 4:
            return {"tier": 2, "effort": "medium", "label": "Estrato 2 (Ejecución Acotada / Medium)"}
        return {"tier": 2, "effort": "low", "label": "Estrato 2 (Ejecución Acotada / Low)"}

    # 2. Veto Fail-Closed a Estrato 1 (Flash/Fast) en Dominio LegalTech y Deliberación del Sanedrín
    legaltech_and_sanedrin_keywords = (
        "legaltech",
        "eu ai act",
        "auditoría legal",
        "dictamen jurídico",
        "contrato mercantil",
        "jurisprudencia",
        "sanedrín",
        "sanedrin",
    )
    if any(kw in text_low for kw in legaltech_and_sanedrin_keywords):
        return {"tier": 2, "effort": "medium", "label": "Estrato 2 (Ejecución Acotada / Medium)"}

    # 2b. Detección de Estrato 3 (Arquitectura Crítica Ring-0 / Verificación Formal / Concurrencia)
    ring0_keywords = (
        "lean 4",
        "lean4",
        "lake build",
        "z3",
        "seqlock",
        "sharedmanifest",
        "spsc",
        "concurrencia",
        "arquitectura crítica",
        "debugging raíz",
        "thermos audit",
        "auditoría termonuclear",
        "salto topológico",
        "salto topologico",
    )
    if any(kw in text_low for kw in ring0_keywords):
        return {"tier": 3, "effort": "high", "label": "Estrato 3 (Razonamiento Profundo / High)"}

    # 3. Detección de Estrato 2 (Ejecución Acotada: Medium para >4 archivos, Low para implementación/iteración <=4)
    if files_count > 4 or "refactor multifichero" in text_low:
        return {"tier": 2, "effort": "medium", "label": "Estrato 2 (Ejecución Acotada / Medium)"}

    impl_keywords = (
        "implementa",
        "impleentalo",
        "impleméntalo",
        "codifica",
        "parchea",
        "refactoriza",
        "añade",
        "edita",
        "corrige el bug",
        "ejecuta el contrato",
        "iteración dialéctica",
    )
    if norm_pulse in DIALECTICAL_PULSES or any(kw in text_low for kw in impl_keywords) or (1 <= files_count <= 4):
        return {"tier": 2, "effort": "low", "label": "Estrato 2 (Ejecución Acotada / Low)"}

    # 4. Por defecto: Estrato 1 (Consultas, triaje, bash rápido o destilación Fase 1)
    return {"tier": 1, "effort": "fast", "label": "Estrato 1 (Triaje / Fast)"}


def evaluate_selector_fitness(
    model: str,
    mode: str,
    task_text: str = "",
    *,
    source: str = "selector UI",
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
) -> dict[str, object]:
    """Evalúa si el LLM y Modo activos coinciden con el Estrato óptimo de la tarea."""
    active = classify_capability_tier(model, mode)
    optimal = infer_optimal_tier(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        task_tier=task_tier,
    )

    if active["tier"] == 0:
        return {
            "status": "NO_EXPUESTO",
            "active": active,
            "optimal": optimal,
            "llm_field": "No expuesto",
            "mode_field": "No expuesto",
            "warning": None,
        }

    is_optimal = (active["tier"] == optimal["tier"]) and (active["effort"] == optimal["effort"])
    opt_effort_display = str(optimal["effort"]).capitalize()

    if is_optimal:
        return {
            "status": "ÓPTIMO",
            "active": active,
            "optimal": optimal,
            "llm_field": f"{model} ({source} — ÓPTIMO: {active['label']})",
            "mode_field": f"{mode} ({source} — ÓPTIMO)",
            "warning": None,
        }

    warning = f"⚠️ DESAJUSTE DE SELECTOR: Activo = {model} | {mode} [{active['label']}] | Óptimo = {optimal['label']}"
    return {
        "status": "DESAJUSTADO",
        "active": active,
        "optimal": optimal,
        "llm_field": f"{model} ({source} — DESAJUSTADO -> Óptimo: {optimal['label']})",
        "mode_field": f"{mode} ({source} — DESAJUSTADO -> Óptimo: {opt_effort_display})",
        "warning": warning,
    }


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
    task_text = extract_latest_user_request(t_path)
    if not task_text and hook_payload and hook_payload.get("prompt"):
        task_text = str(hook_payload["prompt"])

    fitness = evaluate_selector_fitness(model, mode, task_text, source=source)
    raw_active = fitness.get("active")
    active: dict[str, object] = raw_active if isinstance(raw_active, dict) else {}
    raw_optimal = fitness.get("optimal")
    optimal: dict[str, object] = raw_optimal if isinstance(raw_optimal, dict) else {}

    if fitness["status"] == "NO_EXPUESTO":
        return f"🧠 [AUDITORÍA DE SELECTOR · RING-4]: ACTIVO = No expuesto | TAREA ESTIMADA = {optimal['label']}"

    if fitness["status"] == "ÓPTIMO":
        verdict = f"ÓPTIMO ({active['label']})"
    else:
        verdict = f"⚠️ DESAJUSTADO -> Óptimo: {optimal['label']}"

    return (
        f"🧠 [AUDITORÍA DE SELECTOR · RING-4]: "
        f"ACTIVO = {model} | Modo: {mode} ({source}) [{active['label']}] | "
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
        repo_root = Path(__file__).resolve().parents[2]

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
    parser.add_argument("--transcript", type=Path, default=None, help="Ruta opcional a transcript.jsonl")
    parser.add_argument("--task-text", default="", help="Texto de la tarea o prompt para evaluar adecuación")
    parser.add_argument(
        "--task-tier",
        choices=["fast", "low", "medium", "high"],
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
        task = args.task_text or extract_latest_user_request(args.transcript)
        report = evaluate_selector_fitness(
            use_model,
            use_mode,
            task,
            source=source,
            task_tier=args.task_tier,
        )
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    repo_root = Path(__file__).resolve().parents[2]
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
