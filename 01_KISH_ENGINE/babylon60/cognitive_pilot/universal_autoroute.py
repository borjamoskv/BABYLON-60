#!/usr/bin/env python3
"""C5-UNIVERSAL-AUTOROUTE v3.0 — Motor Agnóstico de Enrutamiento y Esfuerzo (Ring-4).

Desacopla por completo la decisión de capacidad respecto a nombres fijos de modelos,
proveedores, idiomas humanos o clientes IDE concretos, cumpliendo:
1. Álgebra Universal de Capacidades: (Soberanía V, Estrato S, Esfuerzo E, Topología tau).
2. Separación estricta Modelo != Nivel de Razonamiento (.babylon60rules / presentation.md).
3. Gravedad e Histéresis de KV-Cache (descuento del 95% de prefijo en misma familia).
4. Extractor Estructural O(1) en 5 canales (< 100 us, cero llamadas de red).
5. Portabilidad multiplataforma estricta (tempfile.gettempdir(), cero rutas absolutas de usuario o temporales POSIX fijos).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import tempfile
import time
from urllib.parse import unquote, urlparse

SCHEMA_VERSION = "3.0.0"
DEFAULT_HMAC_KEY = b"BABYLON60_UNIVERSAL_AUTOROUTE_V3_KEY"

SETTINGS_CHANGE_RE = re.compile(
    r"setting `Model Selection` from .*? to (.*?)(?:\.\s*No need|\.\s*$|\n|$)",
    re.IGNORECASE,
)
USER_REQUEST_RE = re.compile(
    r"<USER_REQUEST>\s*(.*?)\s*</USER_REQUEST>",
    re.DOTALL,
)
ADDITIONAL_METADATA_RE = re.compile(
    r"<ADDITIONAL_METADATA>\s*(.*?)\s*</ADDITIONAL_METADATA>",
    re.DOTALL,
)
MENTIONED_TEXT_BLOCK_RE = re.compile(
    r"(@\[[^\[\]\r\n]+\])\s+is a \[Text Block\]:\r?\n(.*?)(?=\r?\n@\[[^\[\]\r\n]+\]\s+is a \[|\Z)",
    re.DOTALL,
)
MENTION_TOKEN_RE = re.compile(r"@\[[^\[\]\r\n]+\]")
ARTIFACT_URI_COMMENT_RE = re.compile(
    r"Comments on artifact URI:\s*(file://[^\s\r\n]+)",
    re.IGNORECASE,
)
UPLOADED_MEDIA_RE = re.compile(
    r"(?:The user has uploaded \d+ image|/\.(?:user_uploaded|generated)/|\.(?:png|jpg|jpeg|webp|gif|pdf|mp4|mov|wav|flac)\b)",
    re.IGNORECASE,
)
CONTRACT_LEVEL_RE = re.compile(
    r"ROTAR SELECTOR A:\s*([^\r\n|]+?)\s*\|\s*NIVEL:\s*([A-Za-zÁÉÍÓÚáéíóú0-9_() -]+)",
    re.IGNORECASE,
)
CONTRACT_LEVEL_ONLY_RE = re.compile(
    r"ROTAR SELECTOR A:.*?\|\s*NIVEL:\s*([A-Za-zÁÉÍÓÚáéíóú0-9_() -]+)",
    re.IGNORECASE,
)
FILE_PATH_TOKEN_RE = re.compile(
    r"(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_.-]+\.(?:py|rs|lean|ts|tsx|js|json|yaml|yml|toml|md|sh|sql|dart|c|h|cpp|go)\b"
    r"|\b[A-Za-z0-9_.-]+\.(?:py|rs|lean|ts|tsx|toml|smt2|rules)\b"
)

# Patrones de secretos criptográficos en crudo (V_LOCAL_LOOPBACK / INV_SOVEREIGN_AIRGAP)
RAW_SECRET_RE = re.compile(
    r"(?:-----BEGIN (?:RSA |EC |OPENSSH |PGP )?PRIVATE KEY-----"
    r"|\b(?:AIzaSy[0-9A-Za-z_-]{33}|sk-ant-api[0-9A-Za-z_-]{20,}|ghp_[0-9A-Za-z]{30,}|xox[baprs]-[0-9A-Za-z-]{20,})\b"
    r"|\b(?:AWS_SECRET_ACCESS_KEY|PRIVATE_KEY_HEX|MNEMONIC_SEED)\s*=\s*['\"]?[A-Za-z0-9/+_= -]{24,})",
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
        "proceed",
        "yes",
        "aurrera",
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

# Marcadores estructurales y multilingües por estrato/dominio
FORMAL_RING0_MARKERS = (
    "lean 4",
    "lean4",
    "lake build",
    "lakefile",
    "z3",
    ".smt2",
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
    "epistemic halt",
    "#[repr(c",
    "atomicu64",
    "kudurru",
    "bft consensus",
)
LEGAL_AND_SANEDRIN_MARKERS = (
    "legaltech",
    "eu ai act",
    "auditoría legal",
    "dictamen jurídico",
    "contrato mercantil",
    "jurisprudencia",
    "sanedrín",
    "sanedrin",
)
ARCHITECTURE_DESIGN_MARKERS = (
    "diseña",
    "diseñar",
    "design an ",
    "design a ",
    "arquitectura",
    "autoroute",
    "auto-route",
    "implementation_plan",
    "plan de implementación",
    "grafo dag",
    "especificación técnica",
    "/plan",
)
SYSTEMS_IMPLEMENTATION_MARKERS = (
    "implementa",
    "impleentalo",
    "impleméntalo",
    "implement",
    "codifica",
    "parchea",
    "refactoriza",
    "refactor",
    "añade",
    "edita",
    "corrige",
    "actualiza",
    "ejecuta el contrato",
    "ejecuta el vector",
    "ejecuta el plan",
    "iteración dialéctica",
)
LEAF_SCAVENGING_MARKERS = (
    "scrape",
    "scraping",
    "extrae todas las urls",
    "busca en la web masivamente",
    "escanea 100",
    "moskvbot",
)
INFRA_ENV_ERROR_MARKERS = (
    "401 unauthorized",
    "403 forbidden",
    "permissionerror",
    "operation not permitted",
    "no such file or directory",
    "local_lockfile_missing",
)
REASONING_FAILURE_MARKERS = (
    "assertionerror",
    "failed ",
    "error[e",
    "typeerror:",
    "valueerror:",
    "syntaxerror:",
    "panicked at",
    "test result: failed",
)


@dataclass(frozen=True)
class StructuralSignals:
    """Vector estructural O(1) extraído en < 100 us sin llamadas de red."""

    task_text: str
    domain: str
    sovereignty: str
    files_count: int
    context_tokens: int
    has_contract: bool
    prescribed_level: str | None
    prescribed_model: str | None
    is_multimodal: bool
    is_leaf_scavenging: bool
    rework_failures: int
    infra_blocked: bool
    inherited_from_artifact: str | None = None


@dataclass(frozen=True)
class CapabilityTarget:
    """Descriptor universal de capacidad (agnóstico a proveedor y modelo)."""

    tier: int
    effort: str
    reasoning_effort: str
    topology: str
    label: str
    sovereignty: str = "remote_allowed"
    acceptable_tiers: tuple[int, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class UniversalRouteVerdict:
    """Resultado completo de evaluación universal con recibo criptográfico."""

    status: str
    recommended_action: str
    active: dict[str, object]
    optimal: dict[str, object]
    concrete_option: str | None
    capability_description: str
    reason: str
    expected_benefit: str
    how_to_apply: str | None
    constitutional_notice: str | None
    notice_suppressed: bool
    cache_preserved: bool
    sdk_guardrails: dict[str, object]
    signals: dict[str, object]
    receipt_hmac: str
    latency_ns: int
    llm_field: str
    mode_field: str
    warning: str | None


_DEFAULT_PROFILES_CACHE: dict[str, object] | None = None


def load_fleet_profiles(custom_path: Path | None = None) -> dict[str, object]:
    """Carga el catálogo declarativo de perfiles sin acoplar nombres en código."""
    global _DEFAULT_PROFILES_CACHE
    if custom_path is None and _DEFAULT_PROFILES_CACHE is not None:
        return _DEFAULT_PROFILES_CACHE

    candidates: list[Path] = []
    if custom_path is not None:
        candidates.append(custom_path)
    babylon_home = os.environ.get("BABYLON_HOME")
    if babylon_home:
        candidates.append(Path(babylon_home).expanduser() / "fleet_profiles.json")
    candidates.append(Path.home() / ".babylon60" / "fleet_profiles.json")
    candidates.append(Path(__file__).resolve().with_name("fleet_profiles.json"))

    for path in candidates:
        if not path.is_file():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, dict) and isinstance(data.get("profiles"), dict):
            if custom_path is None:
                _DEFAULT_PROFILES_CACHE = data
            return data
    return {"schema_version": SCHEMA_VERSION, "profiles": {}}


def parse_universal_selector(selection: str, explicit_mode: str = "") -> tuple[str, str]:
    """Extrae (model_display, mode_display) de cualquier cadena de selector o entorno."""
    raw = selection.strip()
    if not raw or raw.casefold() in {"none", "unknown", "no expuesto", "n/a"}:
        return "No expuesto", "No expuesto"

    if explicit_mode and explicit_mode.strip():
        return raw, explicit_mode.strip()

    # Caso 1: Meta-orquestadores nativos ("Orchestrator (Carbon)" / "Orchestrator (Argon)")
    m_orch = re.match(r"^Orchestrator\s*\(([^()]+)\)\s*$", raw, re.IGNORECASE)
    if m_orch:
        return raw, "Orchestrator"

    # Caso 2: Sufijo de nivel separado por espacio sin paréntesis alrededor del nivel
    # Ej.: "Gemini 3.8 Flash High (Fast)", "Gemini 4 Hydrogen Extra", "Gemini 4 Carbon Medium"
    m_space_level = re.match(
        r"^(.*?)\s+((?:Extra|XHigh|X-High|High|Medium|Low)\s*\(Fast\)|Fast|Minimal|Low|Medium|High|XHigh|X-High|Extra)$",
        raw,
        re.IGNORECASE,
    )
    if m_space_level:
        return m_space_level.group(1).strip(), m_space_level.group(2).strip()

    # Caso 3: Nivel entre paréntesis al final (conserva raw completo en model_display por retrocompatibilidad)
    # Ej.: "Gemini 4 Argon (High)", "Gemini 4 Hydrogen (XHigh)", "GPT-OSS 120B (Medium)"
    m_paren = re.search(r"\(([^()]+)\)\s*$", raw)
    if m_paren:
        inner = m_paren.group(1).strip()
        if inner.casefold() in {
            "minimal",
            "low",
            "medium",
            "high",
            "xhigh",
            "x-high",
            "extra",
            "fast",
            "xhigh (fast)",
            "high (fast)",
            "medium (fast)",
            "low (fast)",
            "max",
            "máx",
            "máximo",
            "extended",
            "thinking",
        }:
            return raw, inner

    # Caso 4: Inferencia morfológica limpia cuando solo se expone el ID del modelo
    low_raw = raw.casefold()
    if re.search(r"\b(flash|haiku|mini|nano|lite|instant|hydrogen)\b", low_raw):
        return raw, "Fast"
    if re.search(r"\b(opus|o1|o3|ultra|deep|carbon)\b", low_raw):
        return raw, "High"
    return raw, "Standard"


def _infer_family_and_locality(model_low: str) -> tuple[str, str, float]:
    """Determina (familia, localidad, descuento_cache) de forma estructural."""
    if any(tok in model_low for tok in ("127.0.0.1", "localhost", "litert", "ollama", "vllm", "llama.cpp", "local://")):
        return "local-loopback", "loopback", 1.0
    if "gpt-oss" in model_low:
        # En IDEs gestionados (ej. Antigravity [Notice]), GPT-OSS 120B corre en servidor remoto
        return "gpt-oss", "remote", 0.0
    if any(tok in model_low for tok in ("carbon", "argon", "hydrogen", "gemini-4", "gemini 4")):
        return "gemini-4", "remote", 0.95
    if "orchestrator" in model_low:
        return "gemini-4", "remote", 0.95
    if "gemini" in model_low:
        return "gemini-3.8", "remote", 0.75
    if any(tok in model_low for tok in ("claude", "opus", "sonnet", "haiku")):
        return "claude", "remote", 0.95
    if any(tok in model_low for tok in ("gpt-", "o1", "o3", "codex")):
        return "openai", "remote", 0.75
    return "generic", "remote", 0.0


def classify_universal_capability(model: str, mode: str) -> dict[str, object]:
    """Clasifica cualquier par (LLM, Modo) separando Estrato de Pesos y Nivel de Razonamiento."""
    m_low = model.casefold().strip()
    mode_low = mode.casefold().strip()

    if not m_low or m_low.startswith("no expuesto") or m_low in {"none", "unknown", "n/a"}:
        return {
            "tier": 0,
            "effort": "no_expuesto",
            "reasoning_effort": "unexposed",
            "effort_overburn": False,
            "family": "unexposed",
            "locality": "unknown",
            "cache_discount": 0.0,
            "label": "No expuesto",
        }

    family, locality, cache_discount = _infer_family_and_locality(m_low)

    # Normalización ortogonal del nivel de razonamiento (separado de la clase de pesos)
    is_extra_effort = bool(
        re.search(r"\b(extra|xhigh|x-high|max|máx|máximo|ultrathink)\b", mode_low)
        or re.search(r"\b(extra|xhigh|x-high)\b", m_low)
    )
    is_high_effort = is_extra_effort or bool(
        re.search(r"\b(high|alto|extended|deep|thinking)\b", mode_low) and "(fast)" not in mode_low
    )
    is_low_effort = bool(re.search(r"\b(low|bajo|minimal)\b", mode_low) or "(low)" in m_low or "-low" in m_low)
    is_fast_effort = bool(re.search(r"\b(fast|instant|minimal)\b", mode_low))

    if is_extra_effort:
        norm_reasoning = "extra"
    elif is_high_effort:
        norm_reasoning = "high"
    elif is_low_effort:
        norm_reasoning = "low"
    elif is_fast_effort:
        norm_reasoning = "fast"
    else:
        norm_reasoning = "medium"

    # 1. Meta-Orquestadores dinámicos ("Orchestrator (Carbon)" / "Orchestrator (Argon)")
    if re.search(r"\borchestrator\b", m_low) or mode_low == "orchestrator":
        if "carbon" in m_low:
            return {
                "tier": 3,
                "effort": "high",
                "reasoning_effort": "adaptive",
                "effort_overburn": False,
                "family": family,
                "locality": locality,
                "cache_discount": cache_discount,
                "label": "Estrato 3 (Orquestador Apex / Carbon)",
                "is_orchestrator": True,
                "adaptive_tiers": (2, 3),
            }
        return {
            "tier": 2,
            "effort": "medium",
            "reasoning_effort": "adaptive",
            "effort_overburn": False,
            "family": family,
            "locality": locality,
            "cache_discount": cache_discount,
            "label": "Estrato 2 (Orquestador Adaptativo / Argon)",
            "is_orchestrator": True,
            "adaptive_tiers": (1, 2),
        }

    # 2. Estrato 1 — Modelos cinéticos ligeros (Flash, Haiku, Mini, Nano, Lite, Hydrogen)
    # Nota constitucional: el estrato de pesos de Hydrogen es 1 (retrocompatible con test_c5_signature_engine),
    # pero si su esfuerzo es Extra/XHigh se marca effort_overburn=True para alertar del consumo de salida.
    is_kinetic_weights = bool(re.search(r"\b(flash|haiku|mini|nano|lite|instant|hydrogen)\b", m_low))
    if is_kinetic_weights or (is_fast_effort and not re.search(r"\b(opus|carbon|argon|sonnet|o1|o3)\b", m_low)):
        return {
            "tier": 1,
            "effort": "fast",
            "reasoning_effort": norm_reasoning if is_extra_effort else "fast",
            "effort_overburn": is_extra_effort,
            "family": family,
            "locality": locality,
            "cache_discount": cache_discount,
            "label": "Estrato 1 (Triaje / Fast)",
        }

    # 3. Estrato 3 — Razonamiento Profundo / Apex
    is_explicit_low_or_med = bool(re.search(r"\b(low|bajo|medium|medio|standard)\b", mode_low))
    is_high_mode = bool(
        re.search(r"\b(extra|xhigh|x-high|high|alto|max|máx|máximo|extended|ultrathink|deep|thinking)\b", mode_low)
        or re.search(r"\b(extra|xhigh|x-high|high|max|máx)\b", m_low)
    )
    is_apex_model = bool(re.search(r"\b(opus|o1|o3|ultra|carbon)\b", m_low) or "deep-research" in m_low)

    if is_high_mode or (is_apex_model and not is_explicit_low_or_med):
        return {
            "tier": 3,
            "effort": "high",
            "reasoning_effort": norm_reasoning,
            "effort_overburn": is_extra_effort,
            "family": family,
            "locality": locality,
            "cache_discount": cache_discount,
            "label": "Estrato 3 (Razonamiento Profundo / High)",
        }

    # 4. Estrato 2 — Ejecución Acotada (Low vs Medium)
    if is_low_effort:
        return {
            "tier": 2,
            "effort": "low",
            "reasoning_effort": "low",
            "effort_overburn": False,
            "family": family,
            "locality": locality,
            "cache_discount": cache_discount,
            "label": "Estrato 2 (Ejecución Acotada / Low)",
        }

    return {
        "tier": 2,
        "effort": "medium",
        "reasoning_effort": "medium",
        "effort_overburn": False,
        "family": family,
        "locality": locality,
        "cache_discount": cache_discount,
        "label": "Estrato 2 (Ejecución Acotada / Medium)",
    }


def _read_approved_artifact_snippet(content: str) -> tuple[str, str | None]:
    """Lee de forma segura la cabecera de un artefacto aprobado si <USER_REQUEST> está vacío."""
    m_uri = ARTIFACT_URI_COMMENT_RE.search(content)
    if not m_uri:
        return "", None
    raw_uri = m_uri.group(1).strip()
    try:
        parsed = urlparse(raw_uri)
        if parsed.scheme != "file":
            return "", None
        artifact_path = Path(unquote(parsed.path)).expanduser()
        if not artifact_path.is_file():
            return "", None
        snippet = artifact_path.read_text(encoding="utf-8", errors="ignore")[:4096]
        return snippet, str(artifact_path)
    except Exception:
        return "", None


def extract_turn_request_with_metadata(content: str) -> str:
    """Extrae el texto del turno expandiendo @[...] y herencias de artefactos aprobados."""
    m_req = USER_REQUEST_RE.search(content)
    req = m_req.group(1).strip() if m_req else content.strip()

    # Si el operador aprobó un artefacto (/plan Proceed) y <USER_REQUEST> viene vacío,
    # hereda la cabecera del artefacto aprobado para conservar proyecto y estrato.
    if not req and "Comments on artifact URI:" in content:
        snippet, artifact_path = _read_approved_artifact_snippet(content)
        if snippet:
            return f"ejecuta el plan aprobado en {artifact_path}: {snippet[:600]}"

    if not req or "@[" not in req:
        # Adjuntar marca de imagen subida si consta en <ADDITIONAL_METADATA>
        m_meta_img = ADDITIONAL_METADATA_RE.search(content)
        if m_meta_img and UPLOADED_MEDIA_RE.search(m_meta_img.group(1)):
            return f"{req} [MEDIA_UPLOADED]".strip()
        return req

    m_meta = ADDITIONAL_METADATA_RE.search(content)
    if not m_meta:
        return req

    meta_text = m_meta.group(1)
    blocks_by_token: dict[str, list[str]] = {}
    for match in MENTIONED_TEXT_BLOCK_RE.finditer(meta_text):
        token = match.group(1)
        block_text = match.group(2).strip()
        if block_text:
            blocks_by_token.setdefault(token, []).append(block_text)

    expanded = req
    if blocks_by_token:
        offsets: dict[str, int] = {}

        def _replace_mention(match_tok: re.Match[str]) -> str:
            tok = match_tok.group(0)
            candidates = blocks_by_token.get(tok)
            if not candidates:
                return tok
            idx = offsets.get(tok, 0)
            if idx < len(candidates):
                offsets[tok] = idx + 1
                return candidates[idx]
            return candidates[-1]

        expanded = MENTION_TOKEN_RE.sub(_replace_mention, req).strip()

    if UPLOADED_MEDIA_RE.search(meta_text):
        expanded = f"{expanded} [MEDIA_UPLOADED]".strip()
    return expanded


def extract_latest_task_context(transcript_path: Path | None) -> tuple[str, int, int, bool]:
    """Extrae (task_text, context_tokens, rework_failures, infra_blocked) del transcript."""
    if transcript_path is None or not transcript_path.is_file():
        return "", 0, 0, False
    try:
        raw_text = transcript_path.read_text(encoding="utf-8", errors="ignore")
        context_tokens = max(0, len(raw_text.encode("utf-8", errors="ignore")) // 4)
        lines = raw_text.splitlines()
        user_requests: list[str] = []
        recent_contracts: list[str] = []
        rework_failures = 0
        infra_blocked = False

        # Analizar cola reciente para telemetría de retrabajo y contexto del operador
        for raw_line in reversed(lines[-40:]):
            if not raw_line.strip():
                continue
            try:
                record = json.loads(raw_line)
            except Exception:
                continue
            rtype = str(record.get("type") or "")
            content = str(record.get("content") or "")
            low_content = content.casefold()

            if rtype in {"TOOL_RESULT", "COMMAND_OUTPUT", "OBSERVATION"}:
                if any(m in low_content for m in INFRA_ENV_ERROR_MARKERS):
                    infra_blocked = True
                elif any(m in low_content for m in REASONING_FAILURE_MARKERS):
                    rework_failures += 1

        for raw_line in reversed(lines):
            if not raw_line.strip():
                continue
            record = json.loads(raw_line)
            rtype = record.get("type")
            content = str(record.get("content", ""))
            if rtype == "USER_INPUT":
                req = extract_turn_request_with_metadata(content)
                if req:
                    user_requests.append(req)
            elif rtype == "PLANNER_RESPONSE" and (
                "CONTRATO /GOAL BLOQUEADO" in content or "ROTAR SELECTOR A:" in content
            ):
                recent_contracts.append(content)
            if len(user_requests) >= 3 and recent_contracts:
                break

        if not user_requests:
            return "", context_tokens, rework_failures, infra_blocked

        latest = user_requests[0]
        latest_clean = latest.replace("[MEDIA_UPLOADED]", "").strip()
        latest_norm = re.sub(r"[/!?.]+", "", latest_clean.casefold()).strip()

        if latest_norm in CONTINUATION_PULSES:
            prev_context = " | ".join(user_requests[1:4]) if len(user_requests) > 1 else ""
            if recent_contracts:
                return (
                    f"{recent_contracts[0]} [CONTEXTO HILO: {prev_context}]",
                    context_tokens,
                    rework_failures,
                    infra_blocked,
                )
            if prev_context:
                return (
                    f"{latest} [CONTEXTO PREVIO: {prev_context}]",
                    context_tokens,
                    rework_failures,
                    infra_blocked,
                )

        if latest_norm in DIALECTICAL_PULSES:
            prev = " ".join(user_requests[1:3]) if len(user_requests) > 1 else ""
            return (
                f"implementa iteración dialéctica ({latest_norm}) {prev}".strip(),
                context_tokens,
                rework_failures,
                infra_blocked,
            )

        if len(latest_clean) < 120 and len(user_requests) > 1:
            prev_context = " | ".join(user_requests[1:4])
            return (
                f"{latest} [CONTEXTO HILO: {prev_context}]",
                context_tokens,
                rework_failures,
                infra_blocked,
            )

        return latest, context_tokens, rework_failures, infra_blocked
    except Exception:
        return "", 0, 0, False


def extract_structural_signals(
    task_text: str = "",
    *,
    files_count: int = 0,
    has_contract: bool | None = None,
    context_tokens: int = 0,
    rework_failures: int = 0,
    infra_blocked: bool = False,
    contains_unredacted_secrets: bool = False,
    is_multimodal: bool | None = None,
) -> StructuralSignals:
    """Extrae el vector estructural de 5 canales en O(1)."""
    text_low = task_text.casefold()

    # 1. Conteo estructural de archivos mencionados si no se forzó explícitamente
    effective_files = files_count
    if effective_files == 0 and task_text:
        matched_files = {m.group(0).casefold() for m in FILE_PATH_TOKEN_RE.finditer(task_text)}
        effective_files = len(matched_files)

    # 2. Detección de secretos criptográficos en crudo (V_LOCAL_LOOPBACK)
    has_secrets = contains_unredacted_secrets or bool(RAW_SECRET_RE.search(task_text))
    sovereignty = "local_airgap" if has_secrets else "remote_allowed"

    # 3. Detección de Contrato /goal explícito
    prescribed_model: str | None = None
    prescribed_level: str | None = None
    m_full_contract = CONTRACT_LEVEL_RE.search(task_text)
    if m_full_contract:
        prescribed_model = m_full_contract.group(1).strip()
        prescribed_level = m_full_contract.group(2).strip()
    else:
        m_lvl = CONTRACT_LEVEL_ONLY_RE.search(task_text)
        if m_lvl:
            prescribed_level = m_lvl.group(1).strip()

    detected_contract = (
        has_contract
        if has_contract is not None
        else (prescribed_level is not None or "1. objetivo exacto:" in text_low or "archivos permitidos" in text_low)
    )

    # 4. Detección de multimodalidad y scavenging en subagente hoja
    detected_multimodal = (
        is_multimodal
        if is_multimodal is not None
        else ("[media_uploaded]" in text_low or bool(UPLOADED_MEDIA_RE.search(task_text)))
    )
    is_leaf = any(m in text_low for m in LEAF_SCAVENGING_MARKERS)

    # 5. Clasificación estructural de dominio
    norm_pulse = re.sub(r"[/!?.]+", "", text_low.replace("[media_uploaded]", "")).strip()
    if any(m in text_low for m in FORMAL_RING0_MARKERS):
        domain = "formal_ring0"
    elif any(m in text_low for m in LEGAL_AND_SANEDRIN_MARKERS):
        domain = "legal_sanedrin"
    elif any(m in text_low for m in ARCHITECTURE_DESIGN_MARKERS):
        domain = "architecture_design"
    elif effective_files > 4 or "refactor multifichero" in text_low:
        domain = "multifile_refactor"
    elif (
        norm_pulse in DIALECTICAL_PULSES
        or any(m in text_low for m in SYSTEMS_IMPLEMENTATION_MARKERS)
        or (1 <= effective_files <= 4)
    ):
        domain = "scoped_implementation"
    elif detected_multimodal:
        domain = "multimodal_analysis"
    else:
        domain = "kinetic_triage"

    return StructuralSignals(
        task_text=task_text,
        domain=domain,
        sovereignty=sovereignty,
        files_count=effective_files,
        context_tokens=context_tokens,
        has_contract=detected_contract,
        prescribed_level=prescribed_level,
        prescribed_model=prescribed_model,
        is_multimodal=detected_multimodal,
        is_leaf_scavenging=is_leaf,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
    )


def infer_universal_target(
    task_text: str = "",
    *,
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
    context_tokens: int = 0,
    rework_failures: int = 0,
    infra_blocked: bool = False,
    contains_unredacted_secrets: bool = False,
) -> CapabilityTarget:
    """Proyecta la tarea sobre el Álgebra Universal de Capacidades."""
    if task_tier:
        t_norm = task_tier.casefold().strip()
        if t_norm in {"1", "fast", "triage", "triaje"}:
            return CapabilityTarget(
                tier=1,
                effort="fast",
                reasoning_effort="fast",
                topology="direct",
                label="Estrato 1 (Triaje / Fast)",
                acceptable_tiers=(1,),
            )
        if t_norm in {"2", "2-low", "low", "bajo"}:
            return CapabilityTarget(
                tier=2,
                effort="low",
                reasoning_effort="low",
                topology="two_phase_contract",
                label="Estrato 2 (Ejecución Acotada / Low)",
                acceptable_tiers=(2,),
            )
        if t_norm in {"2-medium", "medium", "medio"}:
            return CapabilityTarget(
                tier=2,
                effort="medium",
                reasoning_effort="medium",
                topology="native_orchestrator",
                label="Estrato 2 (Ejecución Acotada / Medium)",
                acceptable_tiers=(2, 3),
            )
        if t_norm in {"3", "high", "xhigh", "x-high", "extra", "alto", "max", "apex"}:
            return CapabilityTarget(
                tier=3,
                effort="high",
                reasoning_effort="high",
                topology="direct",
                label="Estrato 3 (Razonamiento Profundo / High)",
                acceptable_tiers=(3,),
            )

    signals = extract_structural_signals(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
    )

    # 0. Invariante de Soberanía Local (S0_LOCAL_AIRGAP)
    if signals.sovereignty == "local_airgap":
        return CapabilityTarget(
            tier=2,
            effort="medium",
            reasoning_effort="medium",
            topology="local_loopback",
            label="Estrato 2 (Aislamiento Local Air-Gap 127.0.0.1)",
            sovereignty="local_airgap",
            acceptable_tiers=(2,),
        )

    # 1. Contrato /goal explícito en el texto
    if signals.prescribed_level:
        prescribed = signals.prescribed_level.casefold()
        if "fast" in prescribed:
            return CapabilityTarget(
                tier=1,
                effort="fast",
                reasoning_effort="fast",
                topology="direct",
                label="Estrato 1 (Triaje / Fast)",
                acceptable_tiers=(1,),
            )
        if "high" in prescribed or "max" in prescribed or "extra" in prescribed:
            return CapabilityTarget(
                tier=3,
                effort="high",
                reasoning_effort="high",
                topology="direct",
                label="Estrato 3 (Razonamiento Profundo / High)",
                acceptable_tiers=(3,),
            )
        if "medium" in prescribed:
            return CapabilityTarget(
                tier=2,
                effort="medium",
                reasoning_effort="medium",
                topology="two_phase_contract",
                label="Estrato 2 (Ejecución Acotada / Medium)",
                acceptable_tiers=(2,),
            )
        return CapabilityTarget(
            tier=2,
            effort="low",
            reasoning_effort="low",
            topology="two_phase_contract",
            label="Estrato 2 (Ejecución Acotada / Low)",
            acceptable_tiers=(2,),
        )

    if signals.has_contract:
        if signals.files_count > 4:
            return CapabilityTarget(
                tier=2,
                effort="medium",
                reasoning_effort="medium",
                topology="two_phase_contract",
                label="Estrato 2 (Ejecución Acotada / Medium)",
                acceptable_tiers=(2,),
            )
        return CapabilityTarget(
            tier=2,
            effort="low",
            reasoning_effort="low",
            topology="two_phase_contract",
            label="Estrato 2 (Ejecución Acotada / Low)",
            acceptable_tiers=(2,),
        )

    # 2. Escalamiento por retrabajo empírico verificado (>= 2 fallos lógicos sin bloqueo de infra)
    if signals.rework_failures >= 2 and not signals.infra_blocked:
        return CapabilityTarget(
            tier=3,
            effort="high",
            reasoning_effort="high",
            topology="direct",
            label="Estrato 3 (Razonamiento Profundo / High)",
            acceptable_tiers=(3,),
        )

    # 3. Dominio Formal / Ring-0 / Concurrencia Crítica -> Estrato 3
    if signals.domain == "formal_ring0":
        return CapabilityTarget(
            tier=3,
            effort="high",
            reasoning_effort="high",
            topology="direct",
            label="Estrato 3 (Razonamiento Profundo / High)",
            acceptable_tiers=(3,),
        )

    # 4. Diseño Arquitectónico (/plan, DISEÑA UN AUTOROUTE) o LegalTech/Sanedrín o Refactor > 4 archivos
    # Nota: En diseño arquitectónico son óptimos tanto Estrato 2 (Medium / Orchestrator Argon)
    # como Estrato 3 (High / Carbon / Opus), evitando falsos positivos de desajuste cuando el
    # arquitecto usa un modelo de frontera para diseñar un sistema.
    if signals.domain == "architecture_design":
        return CapabilityTarget(
            tier=2,
            effort="medium",
            reasoning_effort="medium",
            topology="native_orchestrator",
            label="Estrato 2 (Ejecución Acotada / Medium)",
            acceptable_tiers=(2, 3),
        )

    if signals.domain in {"legal_sanedrin", "multifile_refactor"}:
        return CapabilityTarget(
            tier=2,
            effort="medium",
            reasoning_effort="medium",
            topology="native_orchestrator",
            label="Estrato 2 (Ejecución Acotada / Medium)",
            acceptable_tiers=(2,),
        )

    # 5. Implementación acotada (<= 4 archivos) o análisis multimodal técnico
    if signals.domain in {"scoped_implementation", "multimodal_analysis"}:
        return CapabilityTarget(
            tier=2,
            effort="low",
            reasoning_effort="low",
            topology="leaf_subagent" if signals.is_leaf_scavenging else "native_orchestrator",
            label="Estrato 2 (Ejecución Acotada / Low)",
            acceptable_tiers=(2,),
        )

    # 6. Por defecto: Estrato 1 (Consultas directas, bash rápido, triaje o Fase 1 /goal)
    return CapabilityTarget(
        tier=1,
        effort="fast",
        reasoning_effort="fast",
        topology="leaf_subagent" if signals.is_leaf_scavenging else "direct",
        label="Estrato 1 (Triaje / Fast)",
        acceptable_tiers=(1,),
    )


def _resolve_host_option(
    target: CapabilityTarget,
    signals: StructuralSignals,
    active: Mapping[str, object],
    host: str,
    profiles_data: Mapping[str, object],
) -> tuple[str | None, str, str | None]:
    """Resuelve (concrete_option, capability_description, how_to_apply) según el perfil declarativo."""
    if target.sovereignty == "local_airgap":
        cap_desc = "runtime local en loopback 127.0.0.1 sin egreso de red (S0 Air-Gap)"
    elif target.tier == 3:
        cap_desc = "modelo de razonamiento profundo (Estrato 3) con esfuerzo alto"
    elif target.tier == 2 and target.effort == "medium":
        cap_desc = "orquestador adaptativo o modelo de frontera en esfuerzo medio (Estrato 2)"
    elif target.tier == 2:
        cap_desc = "orquestador adaptativo o modelo de ejecución acotada en esfuerzo bajo (Estrato 2)"
    else:
        cap_desc = "modelo rápido de triaje o esfuerzo bajo/fast (Estrato 1)"

    profiles = profiles_data.get("profiles")
    if not isinstance(profiles, Mapping):
        return None, cap_desc, None

    profile_key = "local_loopback" if target.sovereignty == "local_airgap" else host
    host_profile = profiles.get(profile_key)
    if not isinstance(host_profile, Mapping):
        return None, cap_desc, None

    how_to_apply = str(host_profile.get("how_to_apply") or "") or None
    options = host_profile.get("options")
    if not isinstance(options, Sequence):
        return None, cap_desc, how_to_apply

    if target.sovereignty == "local_airgap":
        for opt in options:
            if isinstance(opt, Mapping) and opt.get("locality") == "loopback":
                return str(opt.get("label")), cap_desc, how_to_apply
        return None, cap_desc, how_to_apply

    active_family = str(active.get("family") or "")

    # Si hay contexto acumulado (> 32K tokens) y la familia activa tiene una opción del estrato
    # buscado, priorizar la misma familia para preservar el 95% de caché implícito de prefijo.
    if signals.context_tokens > 32_000 and active_family:
        for opt in options:
            if not isinstance(opt, Mapping):
                continue
            opt_family = str(opt.get("family") or "")
            if not (
                opt_family == active_family
                or opt_family.startswith(active_family)
                or active_family.startswith(opt_family)
            ):
                continue
            adaptive = opt.get("adaptive_strata")
            if isinstance(adaptive, list) and target.tier in adaptive:
                return str(opt["label"]), cap_desc, how_to_apply
            if opt.get("stratum") == target.tier:
                eff_display = target.effort.capitalize()
                return f"{opt['label']} ({eff_display})", cap_desc, how_to_apply

    # Selección estándar en el perfil del host
    if host == "antigravity_ui":
        if target.tier in (1, 2) and signals.domain != "formal_ring0":
            if target.tier == 1 and signals.context_tokens == 0 and not signals.has_contract:
                return "Gemini 3.8 Flash (High (Fast)) o Orchestrator (Argon)", cap_desc, how_to_apply
            return str(host_profile.get("resting_default") or "Orchestrator (Argon)"), cap_desc, how_to_apply
        if target.tier == 3:
            if signals.domain == "formal_ring0":
                return "Claude Opus 5.5 (High) o Orchestrator (Carbon)", cap_desc, how_to_apply
            return "Orchestrator (Carbon)", cap_desc, how_to_apply

    for opt in options:
        if not isinstance(opt, Mapping):
            continue
        if opt.get("stratum") == target.tier:
            effs = opt.get("efforts")
            if isinstance(effs, list) and effs:
                chosen_eff = target.effort if target.effort in [str(x).casefold() for x in effs] else str(effs[0])
                return f"{opt['label']} ({chosen_eff})", cap_desc, how_to_apply
            return str(opt.get("label")), cap_desc, how_to_apply

    return None, cap_desc, how_to_apply


def _state_dir() -> Path:
    """Directorio efímero multiplataforma (INV_C5_CROSS_PLATFORM_FS)."""
    base = Path(os.path.join(tempfile.gettempdir(), "c5_autoroute_state"))
    base.mkdir(mode=0o700, parents=True, exist_ok=True)
    return base


def _check_and_record_session_notice(
    session_id: str | None,
    recommended_action: str,
    active_label: str,
    optimal_label: str,
    rework_failures: int,
) -> bool:
    """Devuelve True si el aviso debe suprimirse por haber sido emitido ya sin evidencia nueva."""
    if not session_id or recommended_action == "keep":
        return False
    safe_id = re.sub(r"[^A-Za-z0-9_.-]", "_", session_id)[:96]
    state_file = _state_dir() / f"session_{safe_id}.json"
    signature = f"{recommended_action}|{active_label}|{optimal_label}"
    try:
        if state_file.is_file():
            prev = json.loads(state_file.read_text(encoding="utf-8"))
            if (
                isinstance(prev, dict)
                and prev.get("signature") == signature
                and int(prev.get("rework_failures", 0)) >= rework_failures
            ):
                return True
        payload = {
            "signature": signature,
            "rework_failures": rework_failures,
            "updated_at": time.time(),
        }
        state_file.write_text(json.dumps(payload), encoding="utf-8")
        try:
            os.chmod(state_file, 0o600)
        except OSError:
            pass
    except Exception:
        return False
    return False


def _sign_verdict(
    task_text: str,
    active_model: str,
    active_mode: str,
    recommended_action: str,
    hmac_key: bytes = DEFAULT_HMAC_KEY,
) -> str:
    payload = f"{active_model}:{active_mode}:{recommended_action}:{task_text[:256]}".encode("utf-8")
    digest = hashlib.sha3_256(payload).digest()
    return hmac.new(hmac_key, digest, hashlib.sha256).hexdigest()[:16]


def evaluate_universal_route(
    model: str,
    mode: str,
    task_text: str = "",
    *,
    source: str = "selector UI",
    host: str = "antigravity_ui",
    files_count: int = 0,
    has_contract: bool | None = None,
    task_tier: str | None = None,
    context_tokens: int = 0,
    rework_failures: int = 0,
    infra_blocked: bool = False,
    contains_unredacted_secrets: bool = False,
    session_id: str | None = None,
    profiles_path: Path | None = None,
) -> UniversalRouteVerdict:
    """Evalúa el estado activo frente al Álgebra Universal con histéresis de KV-Cache."""
    t0 = time.perf_counter_ns()
    active = classify_universal_capability(model, mode)
    signals = extract_structural_signals(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
    )
    target = infer_universal_target(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        task_tier=task_tier,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
    )
    optimal_dict = {
        "tier": target.tier,
        "effort": target.effort,
        "reasoning_effort": target.reasoning_effort,
        "topology": target.topology,
        "label": target.label,
        "sovereignty": target.sovereignty,
    }
    profiles_data = load_fleet_profiles(profiles_path)
    concrete_opt, cap_desc, how_to_apply = _resolve_host_option(target, signals, active, host, profiles_data)

    # Guardrails SDK universales (ej. Regla de la Guillotina >= 32768 en modelos con thinking dinámico)
    is_dynamic_thinking_family = str(active.get("family")) == "gemini-4" or (
        concrete_opt is not None and any(k in concrete_opt.casefold() for k in ("argon", "carbon"))
    )
    sdk_guardrails: dict[str, object] = {
        "min_max_output_tokens": 32768 if is_dynamic_thinking_family else 8192,
        "automatic_continuation": False,
        "background": False,
        "require_loopback": target.sovereignty == "local_airgap",
        "delegate_leaf_subagent": signals.is_leaf_scavenging,
    }

    # Caso 0: Metadatos de modelo no expuestos -> No declarar ÓPTIMO ni bloquear (.babylon60rules L27)
    if active["tier"] == 0:
        t1 = time.perf_counter_ns()
        receipt = _sign_verdict(task_text, model, mode, "keep")
        return UniversalRouteVerdict(
            status="NO_EXPUESTO",
            recommended_action="keep",
            active=active,
            optimal=optimal_dict,
            concrete_option=concrete_opt,
            capability_description=cap_desc,
            reason="El entorno activo no expone metadatos del modelo o esfuerzo.",
            expected_benefit="Continuar sin conmutación especulativa.",
            how_to_apply=how_to_apply,
            constitutional_notice=None,
            notice_suppressed=False,
            cache_preserved=True,
            sdk_guardrails=sdk_guardrails,
            signals=asdict(signals),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field="No expuesto",
            mode_field="No expuesto",
            warning=None,
        )

    # Caso 1: Violación de soberanía local Air-Gap (secreto crudo hacia modelo remoto)
    if target.sovereignty == "local_airgap" and active.get("locality") != "loopback":
        t1 = time.perf_counter_ns()
        receipt = _sign_verdict(task_text, model, mode, "route_local_airgap")
        target_str = concrete_opt or cap_desc
        notice = (
            f"Recomiendo cambiar modelo a {target_str}. "
            f"Motivo: detección de material criptográfico o secreto sin redactar en el turno ({source}). "
            f"Beneficio esperado: evitar egreso de secretos a endpoints remotos (INV_SOVEREIGN_AIRGAP). "
            f"Aplicación: {how_to_apply or 'enrutar a 127.0.0.1 o redactar el secreto antes de enviar'}."
        )
        return UniversalRouteVerdict(
            status="DESAJUSTADO",
            recommended_action="route_local_airgap",
            active=active,
            optimal=optimal_dict,
            concrete_option=concrete_opt,
            capability_description=cap_desc,
            reason="Detección de secreto criptográfico con selector remoto activo.",
            expected_benefit="Aislamiento físico en loopback local (127.0.0.1).",
            how_to_apply=how_to_apply,
            constitutional_notice=notice,
            notice_suppressed=False,
            cache_preserved=False,
            sdk_guardrails=sdk_guardrails,
            signals=asdict(signals),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — DESAJUSTADO -> Óptimo: {target.label})",
            mode_field=f"{mode} ({source} — DESAJUSTADO -> Óptimo: Local)",
            warning=f"🛑 BLOQUEO AIR-GAP: Activo = {model} (remoto) | Requerido = {target.label}",
        )

    # Evaluación de compatibilidad de estrato y esfuerzo
    adaptive_tiers = active.get("adaptive_tiers")
    raw_tier = active.get("tier")
    active_tier = raw_tier if isinstance(raw_tier, int) else 0
    active_effort = str(active.get("effort") or "")
    effort_overburn = bool(active.get("effort_overburn"))

    if active.get("is_orchestrator") and isinstance(adaptive_tiers, (tuple, list, set)):
        is_tier_match = target.tier in adaptive_tiers or any(t in adaptive_tiers for t in target.acceptable_tiers)
    elif target.acceptable_tiers and active_tier in target.acceptable_tiers and signals.domain == "architecture_design":
        is_tier_match = True
    else:
        is_tier_match = (active_tier == target.tier) and (active_effort == target.effort)

    # Histéresis de KV-Cache: si la sesión ya acumula > 32K tokens y el modelo activo es de
    # estrato superior dentro de la misma familia con 95% de descuento, preferimos bajar
    # esfuerzo antes que saltar de proveedor.
    cache_preserved = True
    if is_tier_match and not effort_overburn:
        t1 = time.perf_counter_ns()
        receipt = _sign_verdict(task_text, model, mode, "keep")
        return UniversalRouteVerdict(
            status="ÓPTIMO",
            recommended_action="delegate_leaf_subagent" if signals.is_leaf_scavenging else "keep",
            active=active,
            optimal=optimal_dict,
            concrete_option=concrete_opt,
            capability_description=cap_desc,
            reason="El modelo y nivel de esfuerzo activos son coherentes con la complejidad de la tarea.",
            expected_benefit="Preservación del prefijo de caché sin fricción de cambio.",
            how_to_apply=how_to_apply,
            constitutional_notice=None,
            notice_suppressed=False,
            cache_preserved=True,
            sdk_guardrails=sdk_guardrails,
            signals=asdict(signals),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — ÓPTIMO: {active['label']})",
            mode_field=f"{mode} ({source} — ÓPTIMO)",
            warning=None,
        )

    # Caso 2: Modelo ligero (ej. Hydrogen) corriendo en Extra/XHigh sobre tarea de Estrato 1
    if is_tier_match and effort_overburn:
        action = "lower_effort"
        reason = f"El modelo {model} opera con esfuerzo extendido ({mode}) en una tarea de triaje."
        benefit = "Reducir el desgaste de cuota de tokens de salida sin cambiar de familia de modelo."
        target_display = concrete_opt or cap_desc
        notice = (
            f"Recomiendo bajar razonamiento a Low/Medium (o {target_display}). "
            f"Motivo: {reason} ({source}). "
            f"Beneficio esperado: {benefit}"
        )
        suppressed = _check_and_record_session_notice(
            session_id, action, f"{model}:{mode}", target.label, signals.rework_failures
        )
        t1 = time.perf_counter_ns()
        receipt = _sign_verdict(task_text, model, mode, action)
        return UniversalRouteVerdict(
            status="ÓPTIMO",
            recommended_action=action,
            active=active,
            optimal=optimal_dict,
            concrete_option=concrete_opt,
            capability_description=cap_desc,
            reason=reason,
            expected_benefit=benefit,
            how_to_apply=how_to_apply,
            constitutional_notice=None if suppressed else notice,
            notice_suppressed=suppressed,
            cache_preserved=True,
            sdk_guardrails=sdk_guardrails,
            signals=asdict(signals),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — ÓPTIMO: {active['label']})",
            mode_field=f"{mode} ({source} — ÓPTIMO)",
            warning=None if suppressed else f"💡 AVISO DE ESFUERZO: {notice}",
        )

    # Caso 3: Desajuste real de estrato o esfuerzo (sobre-asignado vs sub-asignado)
    if active_tier > target.tier or (
        active_tier == target.tier and active_effort == "high" and target.effort != "high"
    ):
        action = "lower_effort"
        reason = f"Esfuerzo activo ({model} | {mode}) superior al requerido por la petición ({target.label})."
        benefit = "Menor latencia y menor consumo de tokens de pensamiento."
    elif signals.rework_failures >= 2 and not signals.infra_blocked:
        action = "raise_effort" if active_tier >= 2 else "switch_model"
        reason = f"Se observaron {signals.rework_failures} fallos consecutivos de verificación en la sesión."
        benefit = "Reducir retrabajo mediante mayor profundidad deductiva."
    else:
        action = " raise_effort".strip() if active_tier == target.tier else "switch_model"
        reason = f"La tarea ({signals.domain}) requiere {target.label}, mientras que el activo es {active['label']}."
        benefit = "Evitar truncamiento deductivo o iteraciones fallidas sobre el árbol de trabajo."

    action_es = {
        "lower_effort": "bajar razonamiento",
        "raise_effort": "subir razonamiento",
        "switch_model": "cambiar modelo",
    }.get(action, "ajustar selector")
    target_option_text = concrete_opt or cap_desc
    apply_suffix = f" Aplicación: {how_to_apply}." if how_to_apply else ""
    notice = (
        f"Recomiendo {action_es} a {target_option_text}. "
        f"Motivo: {reason} (fuente: {source}). "
        f"Beneficio esperado: {benefit}{apply_suffix}"
    )
    suppressed = _check_and_record_session_notice(
        session_id, action, f"{model}:{mode}", target.label, signals.rework_failures
    )
    opt_effort_display = str(target.effort).capitalize()
    warning = f"⚠️ DESAJUSTE DE SELECTOR: Activo = {model} | {mode} [{active['label']}] | Óptimo = {target.label}"
    t1 = time.perf_counter_ns()
    receipt = _sign_verdict(task_text, model, mode, action)

    return UniversalRouteVerdict(
        status="DESAJUSTADO",
        recommended_action=action,
        active=active,
        optimal=optimal_dict,
        concrete_option=concrete_opt,
        capability_description=cap_desc,
        reason=reason,
        expected_benefit=benefit,
        how_to_apply=how_to_apply,
        constitutional_notice=None if suppressed else notice,
        notice_suppressed=suppressed,
        cache_preserved=cache_preserved,
        sdk_guardrails=sdk_guardrails,
        signals=asdict(signals),
        receipt_hmac=receipt,
        latency_ns=t1 - t0,
        llm_field=f"{model} ({source} — DESAJUSTADO -> Óptimo: {target.label})",
        mode_field=f"{mode} ({source} — DESAJUSTADO -> Óptimo: {opt_effort_display})",
        warning=warning,
    )
