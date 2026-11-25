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

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from functools import cache, lru_cache
import hashlib
import hmac
from ipaddress import ip_address
import json
import os
from pathlib import Path
import re
import tempfile
import time
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

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
    alias: str = ""
    explicit_role: bool = False
    explicit_effort: bool = False

    @property
    def canonical_uri(self) -> str:
        return format_canonical_uri(self)


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
_BUNDLED_PROFILES_PATH = Path(__file__).resolve().with_name("fleet_profiles.json")


@cache
def _bundled_fleet_profiles() -> dict[str, object]:
    try:
        data = json.loads(_BUNDLED_PROFILES_PATH.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


@cache
def _selector_compatibility() -> dict[str, Any]:
    """El catálogo distribuido reconoce selectores incluso con perfiles de host v1.0."""
    rules = _bundled_fleet_profiles().get("selector_compatibility")
    return rules if isinstance(rules, dict) else {}


@cache
def _compiled_model_patterns() -> dict[str, re.Pattern[str]]:
    raw = _selector_compatibility().get("model_patterns", {})
    if not isinstance(raw, Mapping):
        return {}
    return {str(k): re.compile(str(v)) for k, v in raw.items() if v}


@cache
def _compiled_family_rules() -> tuple[tuple[re.Pattern[str], str, str, float], ...]:
    rules = _selector_compatibility().get("families", ())
    compiled: list[tuple[re.Pattern[str], str, str, float]] = []
    for rule in rules:
        if isinstance(rule, Mapping) and rule.get("pattern"):
            compiled.append(
                (
                    re.compile(str(rule["pattern"])),
                    str(rule["family"]),
                    str(rule["locality"]),
                    float(rule["cache_discount"]),
                )
            )
    return tuple(compiled)


def _matches_selector(model_low: str, rule: str) -> bool:
    compiled = _compiled_model_patterns().get(rule)
    return bool(compiled and compiled.search(model_low))


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
    candidates.append(_BUNDLED_PROFILES_PATH)

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

    # Caso 1: El selector de un orquestador incluye su variante entre paréntesis.
    m_orch = re.match(r"^Orchestrator\s*\(([^()]+)\)\s*$", raw, re.IGNORECASE)
    if m_orch:
        return raw, "Orchestrator"

    # Caso 2: Sufijo de nivel separado por espacio sin paréntesis alrededor del nivel
    m_space_level = re.match(
        r"^(.*?)\s+((?:Extra|XHigh|X-High|High|Medium|Low)\s*\(Fast\)|Fast|Minimal|Low|Medium|High|XHigh|X-High|Extra)$",
        raw,
        re.IGNORECASE,
    )
    if m_space_level:
        return m_space_level.group(1).strip(), m_space_level.group(2).strip()

    # Caso 3: Nivel entre paréntesis al final (conserva raw completo en model_display por retrocompatibilidad)
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
    if _matches_selector(low_raw, "kinetic_weights"):
        return raw, "Fast"
    if _matches_selector(low_raw, "high_default_mode"):
        return raw, "High"
    return raw, "Standard"


def _http_loopback(selector: str) -> bool | None:
    if not selector.casefold().startswith(("http://", "https://")):
        return None
    try:
        host = urlparse(selector).hostname or ""
        return host.rstrip(".") == "localhost" or ip_address(host).is_loopback
    except ValueError:
        return False


def _infer_family_and_locality(model_low: str) -> tuple[str, str, float]:
    """Determina (familia, localidad, descuento_cache) de forma estructural."""
    http_local = _http_loopback(model_low)
    if http_local:
        return "local-loopback", "loopback", 1.0
    for compiled_re, family, locality, cache_discount in _compiled_family_rules():
        if http_local is False and locality == "loopback":
            continue
        if compiled_re.search(model_low):
            return family, locality, cache_discount
    return "generic", "remote", 0.0


def classify_universal_capability(model: str, mode: str) -> dict[str, object]:
    """Clasifica cualquier par (LLM, Modo) separando Estrato de Pesos y Nivel de Razonamiento."""
    # Each verdict owns its dictionary. Only bounded selector metadata is reused.
    if len(model) + len(mode) > 256:
        return _classify_selector(model, mode)
    return _cached_selector(model, mode).copy()


@lru_cache(maxsize=128)
def _cached_selector(model: str, mode: str) -> dict[str, object]:
    return _classify_selector(model, mode)


def _classify_selector(model: str, mode: str) -> dict[str, object]:
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

    # 1. Orquestadores adaptativos de estratos 2 y 3.
    if re.search(r"\borchestrator\b", m_low) or mode_low == "orchestrator":
        if _matches_selector(m_low, "apex_orchestrator"):
            return {
                "tier": 3,
                "effort": "high",
                "reasoning_effort": "adaptive",
                "effort_overburn": False,
                "family": family,
                "locality": locality,
                "cache_discount": cache_discount,
                "label": "S3.APEX — Estrato 3 (Orquestador Apex)",
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
            "label": "S2.PILOT — Estrato 2 (Orquestador Adaptativo)",
            "is_orchestrator": True,
            "adaptive_tiers": (1, 2),
        }

    # 2. Los modelos ligeros conservan su estrato incluso con esfuerzo extendido.
    if _matches_selector(m_low, "kinetic_weights") or (
        is_fast_effort and not _matches_selector(m_low, "non_kinetic_weights")
    ):
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
    is_apex_model = _matches_selector(m_low, "apex_weights")

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


# Un rol expresa la intención. El estrato numérico y las etiquetas se conservan
# para clientes anteriores al catálogo de alias.
_VAULT = CapabilityTarget(
    2,
    "medium",
    "standard",
    "local_loopback",
    "Estrato 2 (Aislamiento Local Air-Gap 127.0.0.1)",
    sovereignty="local_airgap",
    acceptable_tiers=(2,),
    alias="S0.VAULT",
)
_PULSE = CapabilityTarget(
    1,
    "fast",
    "fast",
    "direct",
    "Estrato 1 (Triaje / Fast)",
    acceptable_tiers=(1,),
    alias="S1.PULSE",
)
_PILOT = CapabilityTarget(
    2,
    "medium",
    "adaptive",
    "native_orchestrator",
    "Estrato 2 (Ejecución Acotada / Medium)",
    acceptable_tiers=(2, 3),
    alias="S2.PILOT",
)
_PILOT_MEDIUM = replace(_PILOT, reasoning_effort="medium")
_FORGE = CapabilityTarget(
    2,
    "low",
    "low",
    "two_phase_contract",
    "Estrato 2 (Ejecución Acotada / Low)",
    acceptable_tiers=(2,),
    alias="S2.FORGE",
)
_ARCHIVE = CapabilityTarget(
    2,
    "medium",
    "medium",
    "direct",
    "Estrato 2 (Contexto masivo / Medium)",
    acceptable_tiers=(2,),
    alias="S2.ARCHIVE",
)
_APEX = CapabilityTarget(
    3,
    "high",
    "high",
    "direct",
    "Estrato 3 (Razonamiento Profundo / High)",
    acceptable_tiers=(3,),
    alias="S3.APEX",
)
_ROLE_TARGETS = {target.alias: target for target in (_VAULT, _PULSE, _PILOT, _FORGE, _ARCHIVE, _APEX)}
_CANONICAL_URI_BASES: dict[str, tuple[str, str]] = {
    "S0.VAULT": ("loopback", "vault"),
    "S1.PULSE": ("kinetic", "pulse"),
    "S2.PILOT": ("adaptive", "pilot"),
    "S2.FORGE": ("bounded", "forge"),
    "S2.ARCHIVE": ("context", "archive"),
    "S3.APEX": ("deep", "apex"),
}
_URI_PAIR_TO_ALIAS: dict[tuple[str, str], str] = {pair: alias for alias, pair in _CANONICAL_URI_BASES.items()}
_VALID_TOPOLOGIES = frozenset(
    {"direct", "two_phase_contract", "native_orchestrator", "leaf_subagent", "local_loopback"}
)
_LEGACY_TIERS = {
    **dict.fromkeys(("1", "fast", "triage", "triaje"), _PULSE),
    **dict.fromkeys(("2", "2-low", "low", "bajo"), _FORGE),
    **dict.fromkeys(("2-medium", "medium", "medio"), _PILOT_MEDIUM),
    **dict.fromkeys(("3", "high", "xhigh", "x-high", "extra", "alto", "max", "apex"), _APEX),
}


def format_canonical_uri(target: CapabilityTarget) -> str:
    """Formatea la URI canónica moskv://<soberanía>/<slug>?effort=<e>&topology=<tau>."""
    ns, slug = _CANONICAL_URI_BASES.get(
        target.alias,
        ("loopback" if target.sovereignty == "local_airgap" else "bounded", "forge"),
    )
    return f"moskv://{ns}/{slug}?effort={target.reasoning_effort}&topology={target.topology}"


def parse_canonical_role(spec: str, level: str = "") -> CapabilityTarget | None:
    """Resuelve un token corto (S0.VAULT..S3.APEX[:effort]) o URI moskv://... hacia CapabilityTarget."""
    raw = spec.strip()
    if not raw:
        return None

    topology_override: str | None = None
    if raw.casefold().startswith("moskv://"):
        parsed = urlparse(raw)
        if parsed.scheme.casefold() != "moskv":
            return None
        ns = (parsed.netloc or "").strip().casefold()
        slug = parsed.path.strip("/").casefold()
        alias = _URI_PAIR_TO_ALIAS.get((ns, slug))
        if alias is None:
            return None
        qs = parse_qs(parsed.query, keep_blank_values=False)
        uri_efforts = qs.get("effort", [])
        uri_topos = qs.get("topology", [])
        modifier = uri_efforts[0] if uri_efforts else ""
        if uri_topos:
            topo_candidate = uri_topos[0].strip().casefold()
            if topo_candidate not in _VALID_TOPOLOGIES:
                return None
            if alias == "S0.VAULT" and topo_candidate != "local_loopback":
                return None
            topology_override = topo_candidate
        target = _ROLE_TARGETS[alias]
    else:
        alias, _, modifier = raw.upper().partition(":")
        candidate = _ROLE_TARGETS.get(alias)
        if candidate is None:
            return None
        target = candidate

    effort = (modifier or level).strip().casefold()
    if effort in {"xhigh", "x-high"}:
        effort = "extra"
    if not effort:
        resolved = replace(target, explicit_role=True)
        return replace(resolved, topology=topology_override) if topology_override else resolved
    if effort not in {"fast", "low", "medium", "high", "extra", "adaptive", "standard"}:
        return None
    # effort es la clase histórica de comparación, reasoning_effort el presupuesto solicitado.
    comparable = {"extra": "high", "standard": "medium", "adaptive": "medium"}.get(effort, effort)
    resolved = replace(
        target,
        effort=comparable,
        reasoning_effort=effort,
        topology=topology_override or target.topology,
        label=target.label if alias == "S0.VAULT" else f"Estrato {target.tier} ({effort})",
        explicit_role=True,
        explicit_effort=True,
    )
    return resolved


def _requested_role(name: str, level: str = "") -> CapabilityTarget | None:
    return parse_canonical_role(name, level)


def _target_from_signals(
    signals: StructuralSignals,
    task_tier: str | None,
    resting_alias: str = "S2.PILOT",
) -> CapabilityTarget:
    if signals.sovereignty == "local_airgap":
        return _VAULT

    if task_tier:
        requested = _requested_role(task_tier) or _LEGACY_TIERS.get(task_tier.casefold().strip())
        if requested is not None:
            return requested

    if signals.prescribed_model:
        requested = _requested_role(signals.prescribed_model, signals.prescribed_level or "")
        if requested is not None:
            return requested
    elif re.fullmatch(
        r"(?:S[0-3]\.[A-Z]+(?::[A-Z-]+)?|moskv://[a-z0-9_.-]+/[a-z0-9_.-]+(?:\?[a-z0-9_=&.-]+)?)",
        signals.task_text.strip(),
        re.IGNORECASE,
    ):
        requested = _requested_role(signals.task_text)
        if requested is not None:
            return requested

    if signals.prescribed_level:
        level = signals.prescribed_level.casefold()
        if "fast" in level:
            return _PULSE
        if any(token in level for token in ("high", "max", "extra")):
            return _APEX
        if "medium" in level:
            return replace(_FORGE, effort="medium", reasoning_effort="medium", label=_PILOT.label)
        return _FORGE

    if signals.has_contract:
        if signals.files_count > 4:
            return replace(_FORGE, effort="medium", reasoning_effort="medium", label=_PILOT.label)
        return _FORGE

    if signals.domain == "formal_ring0" or (signals.rework_failures >= 2 and not signals.infra_blocked):
        return _APEX
    if signals.context_tokens >= 256_000:
        return _ARCHIVE
    if signals.domain == "architecture_design":
        return _PILOT_MEDIUM
    if signals.domain == "legal_sanedrin":
        return replace(_PILOT_MEDIUM, acceptable_tiers=(2,))
    if signals.domain == "multifile_refactor":
        return replace(_FORGE, effort="medium", reasoning_effort="medium", topology=_PILOT.topology, label=_PILOT.label)
    if signals.domain in {"scoped_implementation", "multimodal_analysis"}:
        return replace(_FORGE, topology="leaf_subagent" if signals.is_leaf_scavenging else "native_orchestrator")
    if not signals.task_text.strip() and signals.context_tokens == 0:
        return _ROLE_TARGETS.get(resting_alias, _PULSE)
    return replace(_PULSE, topology="leaf_subagent") if signals.is_leaf_scavenging else _PULSE


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
    """Proyecta la tarea o su alias explícito sobre el Álgebra Universal de Capacidades."""
    signals = extract_structural_signals(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
    )
    return _target_from_signals(signals, task_tier)


_EFFORT_ORDER = {"fast": 0, "low": 1, "medium": 2, "high": 3, "extra": 4}


def _option_display(option: Mapping[str, object], effort: str) -> str:
    label = str(option["label"])
    if option.get("effort") == "adaptive" or option.get("locality") == "loopback":
        return label
    levels = option.get("efforts")
    if isinstance(levels, list) and levels:
        supported = {str(level).casefold(): str(level) for level in levels}
        requested = effort.casefold()
        ranked = supported.keys() & _EFFORT_ORDER.keys()
        if requested not in supported and requested in _EFFORT_ORDER and ranked:
            rank = _EFFORT_ORDER[requested]
            requested = min(ranked, key=lambda e: (abs(_EFFORT_ORDER[e] - rank), _EFFORT_ORDER[e]))
        effort = supported.get(requested, str(levels[0]))
    if not effort or effort == "adaptive" or label.casefold().endswith(f"({effort.casefold()})"):
        return label
    return f"{label} {effort}" if "(" in effort else f"{label} ({effort})"


def _observed_role_fit(
    model: str,
    mode: str,
    target: CapabilityTarget,
    host: str,
    profiles_data: Mapping[str, object],
    domain: str,
    concrete_option: str | None,
) -> tuple[bool | None, bool | None]:
    """Comprueba la capacidad y el esfuerzo cuando el inventario identifica el selector."""
    profiles = profiles_data.get("profiles")
    profile = profiles.get(host) if isinstance(profiles, Mapping) else None
    if not isinstance(profile, Mapping):
        return None, None
    bindings = profile.get("role_bindings")
    inventory = profile.get("options")
    if not isinstance(bindings, Mapping) or not isinstance(inventory, list):
        return None, None
    binding = bindings.get(target.alias)
    bound_label = binding.get("target_label") if isinstance(binding, Mapping) else None
    overrides = binding.get("domain_overrides") if isinstance(binding, Mapping) else None
    override = overrides.get(domain) if isinstance(overrides, Mapping) else None
    observed = model.strip().casefold()
    observed_mode = mode.strip().casefold()
    for opt in inventory:
        if not isinstance(opt, Mapping) or not isinstance(opt.get("label"), str):
            continue
        label = opt["label"].casefold()
        if observed not in {label, f"{label} ({observed_mode})", f"{label} {observed_mode}"}:
            continue
        aliases = opt.get("aliases")
        if opt["label"] not in (bound_label, override) and isinstance(aliases, list) and target.alias not in aliases:
            return False, None
        if target.explicit_effort and opt.get("efforts"):
            requested = _option_display(opt, target.reasoning_effort).casefold()
            return True, requested in {observed, f"{label} ({observed_mode})", f"{label} {observed_mode}"}
        if target.explicit_effort and opt.get("effort") == "adaptive" and target.reasoning_effort != "adaptive":
            return (True, True) if concrete_option == opt["label"] else (False, None)
        return None, None
    return None, None


def _resolve_legacy_host_option(
    target: CapabilityTarget,
    signals: StructuralSignals,
    active_family: str,
    host: str,
    profile: Mapping[str, object],
    options: list[Mapping[str, object]],
) -> str | None:
    """Conserva el orden de selección y los literales de esfuerzo de los perfiles v1.0."""
    if signals.context_tokens > 32_000 and active_family:
        for option in options:
            family = str(option.get("family") or "")
            if not (family.startswith(active_family) or active_family.startswith(family)):
                continue
            adaptive = option.get("adaptive_strata")
            if isinstance(adaptive, list) and target.tier in adaptive:
                return str(option["label"])
            if option.get("stratum") == target.tier:
                return f"{option['label']} ({target.effort.capitalize()})"

    policy = _selector_compatibility().get("legacy_recommendations", {}).get(host)
    if policy and options:
        route = ""
        if target.tier in (1, 2) and signals.domain != "formal_ring0":
            if target.tier == 1 and signals.context_tokens == 0 and not signals.has_contract:
                route = "triage"
            elif profile.get("resting_default"):
                return str(profile["resting_default"])
            else:
                route = "resting"
        elif target.tier == 3:
            route = "formal_ring0" if signals.domain == "formal_ring0" else "apex"
        available = {str(option["label"]): option for option in options}
        choices = []
        for choice in policy.get(route, ()):
            label = choice["label"]
            if label not in available:
                continue
            effort = choice.get("effort")
            levels = available[label].get("efforts")
            if (
                effort
                and isinstance(levels, list)
                and effort.split()[0].casefold() not in (str(x).casefold() for x in levels)
            ):
                continue
            choices.append(f"{label} ({effort})" if effort else label)
        if choices:
            return " o ".join(choices)

    for option in options:
        if option.get("stratum") != target.tier:
            continue
        levels = option.get("efforts")
        if isinstance(levels, list) and levels:
            effort = target.effort if target.effort in (str(x).casefold() for x in levels) else str(levels[0])
            return f"{option['label']} ({effort})"
        return str(option["label"])
    return None


def _resolve_host_option(
    target: CapabilityTarget,
    signals: StructuralSignals,
    active: Mapping[str, object],
    host: str,
    profiles_data: Mapping[str, object],
) -> tuple[str | None, str, str | None]:
    """Resuelve el rol en el catálogo del anfitrión, con fallback por estrato para perfiles v1.0."""
    local_only = target.sovereignty == "local_airgap"
    cap_desc = (
        "runtime local en loopback 127.0.0.1 sin egreso de red (S0 Air-Gap)"
        if local_only
        else f"{target.alias} — {target.label}"
    )
    profiles = profiles_data.get("profiles")
    if not isinstance(profiles, Mapping):
        return None, cap_desc, None

    profile_key = host
    visited: set[str] = set()
    while profile_key not in visited:
        visited.add(profile_key)
        profile = profiles.get(profile_key)
        bindings = profile.get("role_bindings") if isinstance(profile, Mapping) else None
        binding = bindings.get(target.alias) if isinstance(bindings, Mapping) else None
        delegate = binding.get("delegate_profile") if isinstance(binding, Mapping) else None
        if isinstance(delegate, str):
            profile_key = delegate
        elif local_only and binding is None and profile_key == host and host != "local_loopback":
            profile_key = "local_loopback"
        else:
            break
    else:
        return None, cap_desc, None

    if not isinstance(profile, Mapping):
        return None, cap_desc, None
    how_to_apply = str(profile.get("how_to_apply") or "") or None
    inventory = profile.get("options")
    options = (
        [opt for opt in inventory if isinstance(opt, Mapping) and isinstance(opt.get("label"), str)]
        if isinstance(inventory, list)
        else []
    )
    bound_label = binding.get("target_label") if isinstance(binding, Mapping) else None
    if local_only:
        for opt in options:
            if (
                opt.get("locality") == "loopback"
                and _http_loopback(opt["label"]) is not False
                and (not bound_label or opt["label"] == bound_label)
            ):
                return str(opt["label"]), cap_desc, how_to_apply
        return None, cap_desc, how_to_apply

    active_family = str(active.get("family") or "")
    if not isinstance(bindings, Mapping):
        option = _resolve_legacy_host_option(target, signals, active_family, profile_key, profile, options)
        return option, cap_desc, how_to_apply
    if not isinstance(binding, Mapping) or not isinstance(bound_label, str):
        return None, cap_desc, how_to_apply

    effort = target.reasoning_effort
    overrides = binding.get("domain_overrides")
    override = overrides.get(signals.domain) if isinstance(overrides, Mapping) else None
    if isinstance(override, str):
        bound_label = override
    elif not target.explicit_effort and effort == _ROLE_TARGETS[target.alias].reasoning_effort:
        effort = str(binding.get("default_effort") or effort)

    # Entre alternativas del mismo rol, respetar primero el esfuerzo explícito,
    # después la caché de la sesión y por último la preferencia del anfitrión.
    candidates = []
    for opt in options:
        preferred = opt["label"] == bound_label
        if not preferred and (override or target.alias not in (opt.get("aliases") or ())):
            continue
        family = str(opt.get("family") or "")
        same_family = bool(
            signals.context_tokens > 32_000
            and active_family
            and family
            and (family.startswith(active_family) or active_family.startswith(family))
        )
        levels = opt.get("efforts") or ()
        exact_effort = target.explicit_effort and (
            effort == opt.get("effort") or any(str(level).casefold() == effort for level in levels)
        )
        if preferred or same_family or exact_effort:
            candidates.append(((exact_effort, same_family, preferred), opt))
    if candidates:
        _, chosen = max(candidates, key=lambda candidate: candidate[0])
        display_effort = effort if chosen["label"] == bound_label else target.reasoning_effort
        return _option_display(chosen, display_effort), cap_desc, how_to_apply
    # Los perfiles declarativos también admiten un literal de selector completo sin inventario.
    return _option_display({"label": bound_label}, effort if not override else ""), cap_desc, how_to_apply


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
    active["model"] = model
    active["mode"] = mode
    signals = extract_structural_signals(
        task_text,
        files_count=files_count,
        has_contract=has_contract,
        context_tokens=context_tokens,
        rework_failures=rework_failures,
        infra_blocked=infra_blocked,
        contains_unredacted_secrets=contains_unredacted_secrets,
    )
    profiles_data = load_fleet_profiles(profiles_path)
    profiles = profiles_data.get("profiles")
    profile = profiles.get(host) if isinstance(profiles, Mapping) else None
    resting_alias = str(profile.get("resting_alias") or "") if isinstance(profile, Mapping) else ""
    target = _target_from_signals(signals, task_tier, resting_alias)
    optimal_dict = {
        "alias": target.alias,
        "canonical_uri": target.canonical_uri,
        "tier": target.tier,
        "effort": target.effort,
        "reasoning_effort": target.reasoning_effort,
        "topology": target.topology,
        "label": target.label,
        "sovereignty": target.sovereignty,
    }
    concrete_opt, cap_desc, how_to_apply = _resolve_host_option(target, signals, active, host, profiles_data)

    # Guardrails SDK universales (ej. Regla de la Guillotina >= 32768 en modelos con thinking dinámico)
    dynamic_families = _selector_compatibility().get("dynamic_thinking_families", ())
    is_dynamic_thinking_family = active.get("family") in dynamic_families or (
        concrete_opt is not None and _matches_selector(concrete_opt.casefold(), "dynamic_thinking_option")
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
            signals=vars(signals).copy(),
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
            signals=vars(signals).copy(),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — DESAJUSTADO -> Óptimo: {target.label} | rol: {target.alias})",
            mode_field=f"{mode} ({source} — DESAJUSTADO -> Óptimo: Local)",
            warning=f"🛑 BLOQUEO AIR-GAP: Activo = {model} (remoto) | Requerido = {target.label}",
        )

    # Evaluación de compatibilidad de estrato y esfuerzo
    adaptive_tiers = active.get("adaptive_tiers")
    raw_tier = active.get("tier")
    active_tier = raw_tier if isinstance(raw_tier, int) else 0
    active_effort = str(active.get("effort") or "")
    effort_overburn = bool(active.get("effort_overburn")) and target.reasoning_effort != "extra"

    if active.get("is_orchestrator") and isinstance(adaptive_tiers, (tuple, list, set)):
        is_tier_match = target.tier in adaptive_tiers or any(t in adaptive_tiers for t in target.acceptable_tiers)
    elif target.acceptable_tiers and active_tier in target.acceptable_tiers and signals.domain == "architecture_design":
        is_tier_match = True
    else:
        is_tier_match = (active_tier == target.tier) and (active_effort == target.effort)

    role_fit, effort_fit = None, None
    if not sdk_guardrails["require_loopback"] and (target.explicit_role or target.alias == "S2.ARCHIVE"):
        role_fit, effort_fit = _observed_role_fit(
            model, mode, target, host, profiles_data, signals.domain, concrete_opt
        )
        if role_fit is False:
            is_tier_match = False
        elif effort_fit is not None:
            is_tier_match = effort_fit

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
            signals=vars(signals).copy(),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — ÓPTIMO: {active['label']} | rol: {target.alias})",
            mode_field=f"{mode} ({source} — ÓPTIMO)",
            warning=None,
        )

    # Caso 2: Modelo ligero corriendo en Extra/XHigh sobre tarea de Estrato 1
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
            signals=vars(signals).copy(),
            receipt_hmac=receipt,
            latency_ns=t1 - t0,
            llm_field=f"{model} ({source} — ÓPTIMO: {active['label']} | rol: {target.alias})",
            mode_field=f"{mode} ({source} — ÓPTIMO)",
            warning=None if suppressed else f"💡 AVISO DE ESFUERZO: {notice}",
        )

    # Caso 3: Desajuste real de estrato o esfuerzo (sobre-asignado vs sub-asignado)
    if role_fit is False:
        action = "switch_model"
        reason = f"El catálogo del anfitrión requiere otro selector para {target.alias}."
        benefit = "Usar la capacidad declarada para la tarea."
    elif active_tier > target.tier or (
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
        signals=vars(signals).copy(),
        receipt_hmac=receipt,
        latency_ns=t1 - t0,
        llm_field=f"{model} ({source} — DESAJUSTADO -> Óptimo: {target.label} | rol: {target.alias})",
        mode_field=f"{mode} ({source} — DESAJUSTADO -> Óptimo: {opt_effort_display})",
        warning=warning,
    )
