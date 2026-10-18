#!/usr/bin/env python3
"""
prompt_exergy_oracle.py
=============================================================================
BABYLON-60 / C5-REAL — Lexical index and reported work evidence
The v2 index measures token diversity with a normative 20-token sample floor.
It does not assess correctness, usefulness, physical energy or authorization.
Supply the response body before adding its attestation footer.

Examples:
  python prompt_exergy_oracle.py "texto a evaluar"
  python prompt_exergy_oracle.py --stdin --json --criteria criteria.json
  python prompt_exergy_oracle.py --test

Criteria JSON is an array of objects with id, description, status
(passed/failed/pending) and evidence (an array of nonblank references).
Summaries count reported evidence; they do not verify referenced claims.
=============================================================================
"""

import argparse
from dataclasses import asdict, dataclass
import json
import math
from pathlib import Path
import re
import sys
from typing import Dict, Literal, Tuple, cast
import unicodedata

C5_SCALE = 21_000
MIN_SAMPLE_TOKENS = 20
LEXICAL_METHOD = "c5-lexical-v2"
CriterionStatus = Literal["passed", "failed", "pending"]


@dataclass
class ExergyScore:
    raw_score: float
    c5_score: int  # Scale 0 - 21000
    classification: str
    shannon_entropy: float
    cushion_ratio: float
    silicon_pointer_density: float
    kinetic_vector: bool
    diagnostic: str
    method: str = LEXICAL_METHOD
    token_count: int = 0
    unique_token_count: int = 0


@dataclass(frozen=True)
class WorkCriterion:
    """A declared task criterion and references to its reported evidence."""

    id: str
    description: str
    status: CriterionStatus
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True)
class WorkSummary:
    """Counts of declared criteria, independent from the lexical score."""

    passed: int
    failed: int
    pending: int
    total: int
    criteria: tuple[WorkCriterion, ...]
    summary: str


def strip_accents(s: str) -> str:
    accents = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "Á": "a",
        "É": "e",
        "Í": "i",
        "Ó": "o",
        "Ú": "u",
        "ñ": "n",
        "Ñ": "n",
    }
    return "".join(accents.get(c, c) for c in s)


# Legacy lexical descriptors. None of these lists contributes to the v2 score.
FILLER_TOKENS = frozenset(
    {
        "muy",
        "bastante",
        "quizas",
        "talvez",
        "posiblemente",
        "increible",
        "maravilloso",
        "revolucionario",
        "magico",
        "espectacular",
        "bueno",
        "bonita",
        "bonito",
        "hermoso",
        "genial",
        "super",
        "interesante",
        "obviamente",
        "basicamente",
        "realmente",
        "claramente",
        "very",
        "quite",
        "maybe",
        "perhaps",
        "revolutionary",
        "incredible",
        "amazing",
        "obviously",
        "basically",
        "really",
        "literally",
        "awesome",
    }
)

# Canonical kinetic operators (Ring -1 / Ring-0 transduction)
KINETIC_OPERATORS = frozenset(
    {
        "itera",
        "sigue",
        "mas",
        "mejoralo",
        "deploy",
        "falsabilia",
        "falsabilialo",
        "purga anergia",
        "prueba de estres",
        "fuera de aqui todo esto",
        "fuera de aqui todo eto",
        "autodidact",
        "wait-what",
    }
)

# Legacy technical-word descriptor, not evidence of physical grounding.
SILICON_PATTERNS = [
    re.compile(r"0x[0-9a-fA-F]+"),  # Hex addresses
    re.compile(
        r"\b(openat|unlinkat|fsync|stat|pread|mmap|seqlock|2pc|sigkill|touch id|secure enclave|face id)\b", re.I
    ),
    re.compile(r"(/[\w\.\-]+)+"),  # Unix paths
    re.compile(r"\b[0-9a-f]{40,64}\b"),  # Hashes (SHA-1, SHA-256)
    re.compile(r"\b(m3 pro|apple silicon|arm64|musl|c-abi|posix|l1|cache line|fs)\b", re.I),
    re.compile(r"\b(st_dev|st_ino|f_bavail|dfd|reap_jail)\b", re.I),
    re.compile(r"\b(trama|imposibilidad|averia|recibo falsificado|captor|rehen|markov|aplauso|grena)\b", re.I),
]


def compute_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    freqs: Dict[str, int] = {}
    for ch in text:
        freqs[ch] = freqs.get(ch, 0) + 1
    length = len(text)
    ent = 0.0
    for count in freqs.values():
        p = count / length
        ent -= p * math.log2(p)
    return ent


def compute_cushion_ratio(text: str) -> Tuple[float, int, int]:
    """
    Legacy list-based repetition and filler descriptor, not semantic quality.
    """
    words = re.findall(r"\b[\w\-]+\b", strip_accents(text.lower()))
    if not words:
        return 0.0, 0, 0

    filler_count = sum(1 for w in words if w in FILLER_TOKENS)
    substantive_count = max(0, len(words) - filler_count)

    # Word repetition penalty (Jakobovits semantic satiation)
    word_freqs: Dict[str, int] = {}
    for w in words:
        word_freqs[w] = word_freqs.get(w, 0) + 1
    max_rep = max(word_freqs.values()) if word_freqs else 1
    rep_penalty = 1.0 if max_rep <= 2 else (1.0 / (max_rep - 1))

    # Strict penalty if filler words exist
    ratio = (substantive_count / (1.0 + (filler_count * 3.0))) * rep_penalty
    return ratio, substantive_count, filler_count


def compute_silicon_grounding(text: str) -> float:
    matches = 0
    norm_text = strip_accents(text)
    for pattern in SILICON_PATTERNS:
        matches += len(pattern.findall(norm_text))
    words = max(1, len(re.findall(r"\b[\w\-]+\b", text)))
    density = min(1.0, (matches * 2.5) / words)
    return density


def _destination_end(text: str, opening: int) -> int | None:
    """Find the balanced end of a common Markdown inline destination."""
    depth = 1
    quote: str | None = None
    in_angle = False
    index = opening + 1
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if quote is not None:
            if char == quote:
                quote = None
        elif char == "<":
            in_angle = True
        elif char == ">":
            in_angle = False
        elif not in_angle:
            if char in ("'", '"') and text[index - 1].isspace():
                quote = char
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return index
        index += 1
    return None


def _text_without_link_metadata(text: str) -> str:
    """Keep labels, dropping common inline/reference destinations and URLs.

    This is lexical preprocessing, not a complete Markdown renderer. Bare URLs
    extend to whitespace or angle brackets. Balanced inline destinations may
    contain escaped parentheses and quoted titles.
    """
    reference_definition = (
        r"(?m)^[ \t]{0,3}\[[^\]\n]+\]:[ \t]*(?:\n[ \t]*)?"
        r"(?:<[^<>\n]*>|(?:\\.|[^\s\\])+)"
        r"(?:[ \t]+(?:\n[ \t]*)?|\n[ \t]*)?"
        r"(?:\"[^\"\n]*\"|'[^'\n]*'|\([^\n]*\))?[ \t]*$"
    )
    text = re.sub(reference_definition, " ", text)
    parts: list[str] = []
    start = scan = 0
    while scan < len(text):
        close_label = text.find("](", scan)
        if close_label < 0:
            break
        if text.rfind("[", start, close_label) < 0:
            scan = close_label + 2
            continue
        end = _destination_end(text, close_label + 1)
        if end is None:
            scan = close_label + 2
            continue
        parts.append(text[start : close_label + 1])
        parts.append(" ")
        start = scan = end + 1
    parts.append(text[start:])
    text = "".join(parts)
    text = re.sub(r"(\[[^\]\n]+\])\[[^\]\n]*\]", r"\1 ", text)
    return re.sub(r"(?:[a-z][a-z0-9+.-]*://|mailto:|tel:)[^\s<>]+", " ", text, flags=re.IGNORECASE)


def _normalize_lexical_text(text: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFKD", text.casefold()) if unicodedata.category(char) != "Mn"
    )


def evaluate_prompt_exergy(prompt: str) -> ExergyScore:
    """Evaluate supplied text using the reproducible lexical v2 formula.

    Tokens include Unicode letters and digits; underscores and hyphens split
    tokens. Compatibility folding merges case and diacritics (including ñ/n).
    A score of 21,000 can describe a list of distinct words, not its meaning.
    """
    raw = _text_without_link_metadata(prompt.strip())
    normalized = _normalize_lexical_text(raw)
    tokens = re.findall(r"[^\W_]+", normalized)
    count = len(tokens)
    unique = len(set(tokens))
    c5_score = C5_SCALE * unique // max(count, MIN_SAMPLE_TOKENS)
    is_kinetic = any(normalized == op or normalized.startswith(op + " ") for op in KINETIC_OPERATORS)
    cushion_ratio, _, _ = compute_cushion_ratio(raw)
    if count == 0:
        classification = "SIN_TEXTO_EVALUABLE"
        diagnostic = "Sin tokens evaluables; índice léxico 0."
    elif count < MIN_SAMPLE_TOKENS:
        classification = "MUESTRA_BREVE"
        diagnostic = "Muestra de menos de 20 tokens; umbral normativo, sin valoración semántica."
    else:
        classification = "INDICE_LEXICO"
        diagnostic = "Diversidad léxica; no evalúa corrección, utilidad, energía física ni permisos."
    return ExergyScore(
        raw_score=c5_score / C5_SCALE,
        c5_score=c5_score,
        classification=classification,
        shannon_entropy=round(compute_shannon_entropy(raw), 3),
        cushion_ratio=round(cushion_ratio, 3),
        silicon_pointer_density=round(compute_silicon_grounding(raw), 3),
        kinetic_vector=is_kinetic,
        diagnostic=diagnostic,
        token_count=count,
        unique_token_count=unique,
    )


def _nonblank_string(value: object, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} debe ser una cadena no vacía")
    return value


def _validate_criterion(criterion: WorkCriterion) -> None:
    _nonblank_string(criterion.id, "id")
    _nonblank_string(criterion.description, "description")
    if criterion.status not in ("passed", "failed", "pending"):
        raise ValueError("status debe ser passed, failed o pending")
    if not isinstance(criterion.evidence, tuple):
        raise ValueError("evidence debe ser una tupla de referencias")
    for reference in criterion.evidence:
        _nonblank_string(reference, "evidence")
    if criterion.status == "passed" and not criterion.evidence:
        raise ValueError(f"El criterio {criterion.id!r} está cumplido sin evidencia")


def summarize_work(criteria: list[WorkCriterion]) -> WorkSummary:
    """Count criteria without granting authority or verifying their references."""
    seen: set[str] = set()
    for criterion in criteria:
        _validate_criterion(criterion)
        identifier = criterion.id.strip()
        if identifier in seen:
            raise ValueError(f"Identificador de criterio duplicado: {identifier}")
        seen.add(identifier)
    passed = sum(item.status == "passed" for item in criteria)
    failed = sum(item.status == "failed" for item in criteria)
    pending = sum(item.status == "pending" for item in criteria)
    total = len(criteria)
    summary = (
        f"{passed}/{total} criterios cumplidos; fallidos: {failed}; pendientes: {pending}"
        if total
        else "Sin criterios definidos"
    )
    return WorkSummary(passed, failed, pending, total, tuple(criteria), summary)


def _parse_criterion(value: object) -> WorkCriterion:
    if not isinstance(value, dict):
        raise ValueError("Cada criterio debe ser un objeto JSON")
    fields: dict[str, object] = {}
    for key, item in value.items():
        if not isinstance(key, str):
            raise ValueError("Los campos del criterio deben ser cadenas")
        fields[key] = item
    if set(fields) != {"id", "description", "status", "evidence"}:
        raise ValueError("Cada criterio requiere solo id, description, status y evidence")
    status = fields["status"]
    if not isinstance(status, str) or status not in ("passed", "failed", "pending"):
        raise ValueError("status debe ser passed, failed o pending")
    references = fields["evidence"]
    if not isinstance(references, list):
        raise ValueError("evidence debe ser una lista de referencias")
    criterion = WorkCriterion(
        id=_nonblank_string(fields["id"], "id"),
        description=_nonblank_string(fields["description"], "description"),
        status=cast(CriterionStatus, status),
        evidence=tuple(_nonblank_string(reference, "evidence") for reference in references),
    )
    _validate_criterion(criterion)
    return criterion


def load_work_criteria(path: Path) -> list[WorkCriterion]:
    """Read a strict UTF-8 JSON array of criteria, with no persistence writes."""
    decoded: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(decoded, list):
        raise ValueError("El informe de criterios debe ser una lista JSON")
    criteria = [_parse_criterion(item) for item in decoded]
    summarize_work(criteria)
    return criteria


def run_benchmark() -> int:
    """Run lexical regressions; success is not semantic or hardware attestation."""
    cases = [
        ("vacío", "", 0),
        ("puntuación", "!!!", 0),
        ("operador", "itera", 1050),
        ("vocabulario técnico", "seqlock mmap fsync arm64 musl posix", 6300),
        ("vocabulario común", "casa mesa silla puerta vaso libro", 6300),
        ("repetición", "uno " * 100, 210),
    ]
    print("BABYLON-60 — Regresiones del índice léxico v2")
    all_passed = True
    for label, text, expected in cases:
        actual = evaluate_prompt_exergy(text).c5_score
        passed = actual == expected
        all_passed = all_passed and passed
        print(f"{'PASS' if passed else 'FAIL'}: {label}: {actual}/{C5_SCALE}, esperado {expected}")
    print("Regresiones léxicas superadas." if all_passed else "Fallo en las regresiones léxicas.")
    return 0 if all_passed else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Índice léxico C5 y criterios de trabajo con evidencia reportada")
    parser.add_argument("text", nargs="*", help="Texto a evaluar (sin atestación)")
    parser.add_argument("--stdin", action="store_true", help="Leer el cuerpo completo desde la entrada estándar")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Emitir text y work como JSON")
    parser.add_argument("--criteria", type=Path, help="Informe externo: lista JSON de criterios")
    parser.add_argument("--test", action="store_true", help="Ejecutar regresiones léxicas")
    args = parser.parse_args(argv)
    words: list[str] = args.text
    use_stdin: bool = args.stdin
    json_output: bool = args.json_output
    criteria_path: Path | None = args.criteria
    run_tests: bool = args.test
    if use_stdin and words:
        parser.error("--stdin no se puede combinar con texto posicional")
    if run_tests and (words or use_stdin or json_output or criteria_path is not None):
        parser.error("--test se usa sin texto ni otros modos")
    if run_tests or (not words and not use_stdin and not json_output and criteria_path is None):
        return run_benchmark()
    try:
        body = sys.stdin.read() if use_stdin else " ".join(words)
        criteria = load_work_criteria(criteria_path) if criteria_path is not None else []
        result = evaluate_prompt_exergy(body)
        work = summarize_work(criteria)
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    if json_output:
        print(json.dumps({"text": asdict(result), "work": asdict(work)}, ensure_ascii=False))
    else:
        print(f"Puntuación: {result.c5_score} / {C5_SCALE} | {result.classification} | {result.diagnostic}")
        print(f"Método: {result.method}; tokens: {result.token_count}; distintos: {result.unique_token_count}")
        print(f"Trabajo verificado (recuento de criterios reportados): {work.summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
