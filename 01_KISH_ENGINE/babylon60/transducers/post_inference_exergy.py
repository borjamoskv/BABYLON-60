# ============================================================================
# BABYLON-60 v5.1 Sovereign Hardened
# █ AUTOCOGNITION-Ω | POST-INFERENCE EXERGY TRANSDUCER | STATE: C5-REAL
# ============================================================================
"""Deterministic post-inference entropy & exergy transducer.

Operates on raw LLM output or unstructured tool payloads in three stages:
  1. BLAKE3-verified shielding of involuntary/structured spans (code blocks,
     inline code, LaTeX math, Markdown tables/quotes, diffs, links, URLs, digests).
  2. Lexical slop aphairesis (conversational preambles, meta-hedging, sign-offs).
  3. Deep entropic context-rot pruning on unguarded declarative prose sentences,
     preserving negations, numbers, paths, and NO_VERIFICADO markers.

Produces a stateless Fisher-Rao / Kullback-Leibler / Shannon receipt without
mutating shared ThermalLock state or claiming ontological truth (Laws O2, O7).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
import math
import re
from typing import Literal
import unicodedata

from blake3 import blake3

from babylon60.transducers.fisher_bayesian_gate import FisherInformationGeometry
from babylon60.transducers.linguistic_entropy import (
    LinguisticEntropyDetector,
    LinguisticEntropyReport,
)

TransduceMode = Literal["transduce", "audit", "gate"]

MAX_TRANSDUCE_CHARS = 65_536
C5_LEXICAL_SCALE = 21_000
C5_LEXICAL_FLOOR_TOKENS = 20
HIGH_EXERGY_PRIOR: tuple[float, float, float] = (0.85, 0.1499, 0.0001)

_PROTECTED_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"(?:^|\n)[ \t]*(?:`{3,}|~{3,})[^\n]*\n[\s\S]*?\n[ \t]*(?:`{3,}|~{3,})[ \t]*(?=\n|$)"),
    re.compile(r"\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]"),
    re.compile(r"(?:^|\n)(?:[ \t]*\|[^\n]+\|[ \t]*(?:\n|$))+"),
    re.compile(r"(?:^|\n)(?:[ \t]*>[^\n]*(?:\n|$))+"),
    re.compile(r"(?:^|\n)(?:diff --git [^\n]+|@@ [^\n]+ @@)(?:\n[+ -][^\n]*)*"),
    re.compile(r"`[^`\n]+`"),
    re.compile(r"\\\([^\n]*?\\\)|(?<!\$)\$(?!\$)[^$\n]+?(?<!\$)\$(?!\$)"),
    re.compile(r"!?\[[^\]\n]*\]\([^\)\n]+\)"),
    re.compile(r"(?:https?|file)://[^\s<>)\]]+"),
    re.compile(r"\b[0-9a-fA-F]{40,128}\b"),
)

_LEADING_CLAUSE_SLOP: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"^[ \t]*(?:¡?(?:Claro(?: que s[ií])?|Por supuesto|Excelente(?: pregunta)?|Entendido|Perfecto|Desde luego)[,!.]?[ \t]*)+",
        re.IGNORECASE,
    ),
    re.compile(
        r"^[ \t]*(?:Aqu[ií] tienes (?:el c[oó]digo|la soluci[oó]n|la respuesta|el resultado|un resumen)[^.!?\n]*[.!:][ \t]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^[ \t]*(?:Estar[eé] encantad[oa] de ayudarte[^.!?\n]*[.!:][ \t]*|Como modelo de lenguaje[^.!?\n]*[.!?][ \t]*)",
        re.IGNORECASE,
    ),
    re.compile(
        r"^[ \t]*(?:(?:Sure|Certainly|Absolutely|Of course|Understood)[,!.]?[ \t]*)+",
        re.IGNORECASE,
    ),
    re.compile(
        r"^[ \t]*(?:Great[,!]?[ \t]+(?:let(?:'s| us)|I(?:'ll| will))[^.!?\n]*[.!:][ \t]*|I(?:'d| would) be happy to[^.!?\n]*[.!:][ \t]*|I(?:'m| am) here to help[^.!?\n]*[.!:][ \t]*|As an AI(?: language model)?[^.!?\n]*[.!?][ \t]*|Here is (?:the code|the solution|the answer|a summary)[^.!?\n]*[.!:][ \t]*|Below you(?:'ll| will) find[^.!?\n]*[.!:][ \t]*)",
        re.IGNORECASE,
    ),
)

_META_HEDGE_PREFIXES: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"(^|(?<=[.!?]\s))(?:Cabe destacar que|Es importante (?:tener en cuenta|notar|recordar) que|Vale la pena mencionar que|Sin lugar a dudas,[ \t]*)[ \t]+",
        re.IGNORECASE,
    ),
    re.compile(
        r"(^|(?<=[.!?]\s))(?:It(?:'s| is) (?:important|worth) (?:to )?(?:note|noting|remember|remembering) that)[ \t]+",
        re.IGNORECASE,
    ),
)

_TRAILING_SLOP: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"[ \t]*(?:¡?Espero que (?:esto|esta informaci[oó]n|te)[^.!?\n]*[.!?][ \t]*|(?:No dudes en preguntar|Av[ií]same si necesitas)[^.!?\n]*[.!?]?[ \t]*)+$",
        re.IGNORECASE,
    ),
    re.compile(
        r"[ \t]*(?:I hope (?:this|that)[^.!?\n]*[.!?][ \t]*|(?:Feel free to ask|Let me know if you (?:have any questions|need anything else))[^.!?\n]*[.!?]?[ \t]*)+$",
        re.IGNORECASE,
    ),
)

_SEMANTIC_GUARD_RE = re.compile(
    r"(?:\d|/|\\|\b(?:no|nunca|jam[aá]s|ni|sin|salvo|excepto|aunque|pero|debe|deben|prohibid[oa]|"
    r"error|fall[oó]|falla|bloquead[oa]|pendiente|no_verificado|not|never|nor|without|unless|"
    r"except|but|however|must|shall|cannot|failed|blocked|unverified)\b)",
    re.IGNORECASE,
)

_STRUCTURED_LINE_RE = re.compile(r"^[ \t]*(?:#{1,6}\s|[-*+]\s|\d+[.)]\s)")

_STOPWORDS = frozenset(
    {
        "el", "la", "los", "las", "de", "del", "en", "y", "o", "u", "a", "al", "que",
        "es", "son", "un", "una", "unos", "unas", "por", "para", "con", "como", "su",
        "sus", "se", "lo", "le", "les", "este", "esta", "estos", "estas", "ese", "esa",
        "the", "of", "in", "and", "or", "to", "is", "are", "a", "an", "for", "with",
        "as", "on", "at", "by", "from", "this", "that", "these", "those", "it", "its",
    }
)

_URL_STRIP_RE = re.compile(r"!?\[([^\]]*)\]\([^\)]+\)|(?:https?|file)://[^\s<>)\]]+")
_UNICODE_WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass(frozen=True)
class PostInferenceReceipt:
    mode: TransduceMode
    chars_before: int
    chars_after: int
    slop_spans_removed: int
    rot_sentences_pruned: int
    exergy_before: float
    exergy_after: float
    exergy_delta: float
    word_entropy_before: float
    word_entropy_after: float
    context_rot_before: float
    context_rot_after: float
    slop_density_before: float
    slop_density_after: float
    fisher_rao_before: float
    fisher_rao_after: float
    kl_divergence_after: float
    lexical_index_c5_v2: int
    protected_spans_count: int
    protected_spans_intact: bool
    protected_spans_b3: str
    gate_passed: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True)
class PostInferenceResult:
    transduced_text: str
    gate_passed: bool
    receipt: PostInferenceReceipt

    def to_dict(self) -> dict[str, object]:
        return {
            "transduced_text": self.transduced_text,
            "gate_passed": self.gate_passed,
            "receipt": self.receipt.to_dict(),
        }


def _strip_combining(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(ch for ch in decomposed if not unicodedata.combining(ch))


def compute_c5_lexical_v2(text: str) -> int:
    """Compute normative c5-lexical-v2 diversity index (not truth or physical energy)."""
    cleaned = _URL_STRIP_RE.sub(lambda m: m.group(1) or " ", text)
    normalized = _strip_combining(cleaned)
    tokens = _UNICODE_WORD_RE.findall(normalized)
    if not tokens:
        return 0
    return math.floor(C5_LEXICAL_SCALE * len(set(tokens)) / max(len(tokens), C5_LEXICAL_FLOOR_TOKENS))


def _simplex_profile(report: LinguisticEntropyReport) -> tuple[float, float, float]:
    ex = max(1e-6, report.exergy_score)
    slop = max(1e-6, min(1.0, report.slop_density * 10.0))
    rot = max(1e-6, min(1.0, (1.0 - report.mattr) * 0.5 + report.context_rot_score))
    total = ex + slop + rot
    return (ex / total, rot / total, slop / total)


def _digest_spans(spans: list[str]) -> str:
    hasher = blake3()
    for idx, span in enumerate(spans):
        hasher.update(f"{idx}:{len(span)}:".encode("utf-8"))
        hasher.update(span.encode("utf-8"))
    return hasher.hexdigest()


def _sentinel(tag: str, idx: int) -> str:
    return f"<<__B60PROT_{tag}_{idx:04d}__>>"


def _mask_protected_spans(text: str, tag: str) -> tuple[str, list[str]]:
    spans: list[str] = []
    masked = text
    for pattern in _PROTECTED_PATTERNS:
        def _replacer(match: re.Match[str]) -> str:
            raw = match.group(0)
            prefix_nl = "\n" if raw.startswith("\n") else ""
            body = raw[1:] if prefix_nl else raw
            token = _sentinel(tag, len(spans))
            spans.append(body)
            return prefix_nl + token

        masked = pattern.sub(_replacer, masked)
    return masked, spans


def _unmask_protected_spans(masked: str, tag: str, spans: list[str]) -> tuple[str, list[str]]:
    restored = masked
    recovered: list[str] = []
    for idx in range(len(spans) - 1, -1, -1):
        token = _sentinel(tag, idx)
        if token in restored:
            restored = restored.replace(token, spans[idx], 1)
            recovered.append(spans[idx])
    recovered.reverse()
    return restored, recovered


def _capitalize_clause_start(text: str) -> str:
    stripped = text.lstrip()
    if stripped.startswith("<<__B60PROT_"):
        return text
    for idx, ch in enumerate(text):
        if ch.isalpha():
            return text[:idx] + ch.upper() + text[idx + 1 :]
    return text


def _aphairesis_paragraph(paragraph: str) -> tuple[str, int]:
    if paragraph.strip().startswith("<<__B60PROT_") and paragraph.strip().endswith("__>>"):
        return paragraph, 0
    removed = 0
    current = paragraph
    changed = True
    while changed:
        changed = False
        for pattern in _LEADING_CLAUSE_SLOP:
            updated, count = pattern.subn("", current, count=1)
            if count:
                current = _capitalize_clause_start(updated)
                removed += count
                changed = True
    for pattern in _META_HEDGE_PREFIXES:
        def _hedge_sub(match: re.Match[str]) -> str:
            return match.group(1)

        updated, count = pattern.subn(_hedge_sub, current)
        if count:
            current = _capitalize_clause_start(updated)
            removed += count
    for pattern in _TRAILING_SLOP:
        updated, count = pattern.subn("", current)
        if count:
            current = updated.rstrip()
            removed += count
    return current, removed


def _aphairesis_slop(masked: str) -> tuple[str, int]:
    paragraphs = re.split(r"(\n\s*\n)", masked)
    out: list[str] = []
    total_removed = 0
    for chunk in paragraphs:
        if not chunk.strip() or chunk.startswith("\n"):
            out.append(chunk)
            continue
        cleaned, count = _aphairesis_paragraph(chunk)
        total_removed += count
        if cleaned.strip():
            out.append(cleaned)
    joined = "".join(out)
    joined = re.sub(r"\n{3,}", "\n\n", joined).strip()
    return joined, total_removed


def _content_tokens(sentence: str) -> set[str]:
    norm = _strip_combining(sentence)
    words = _UNICODE_WORD_RE.findall(norm)
    return {w for w in words if len(w) >= 3 and w not in _STOPWORDS}


def _is_redundant_sentence(
    tokens: set[str],
    prior_sets: list[set[str]],
    seen_union: set[str],
) -> bool:
    if len(tokens) < 4 or not prior_sets:
        return False
    max_jaccard = max(len(tokens & prev) / len(tokens | prev) for prev in prior_sets)
    novelty = len(tokens - seen_union) / len(tokens)
    return max_jaccard >= 0.70 or (novelty < 0.22 and max_jaccard >= 0.50)


def _prune_paragraph_sentences(
    paragraph: str,
    prior_sets: list[set[str]],
    seen_union: set[str],
) -> tuple[str, int]:
    if _STRUCTURED_LINE_RE.match(paragraph) or "\n" in paragraph:
        for part in re.split(r"(?<=[.!?])\s+", paragraph.strip()):
            toks = _content_tokens(part)
            if len(toks) >= 4:
                prior_sets.append(toks)
                seen_union.update(toks)
        return paragraph, 0

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", paragraph.strip()) if s]
    kept: list[str] = []
    pruned = 0
    for sentence in sentences:
        if "<<__B60PROT_" in sentence or _SEMANTIC_GUARD_RE.search(sentence):
            kept.append(sentence)
            toks = _content_tokens(sentence)
            if len(toks) >= 4:
                prior_sets.append(toks)
                seen_union.update(toks)
            continue
        toks = _content_tokens(sentence)
        if _is_redundant_sentence(toks, prior_sets, seen_union):
            pruned += 1
            continue
        kept.append(sentence)
        if len(toks) >= 4:
            prior_sets.append(toks)
            seen_union.update(toks)
    return " ".join(kept), pruned


def _prune_context_rot(masked: str) -> tuple[str, int]:
    blocks = re.split(r"(\n\s*\n)", masked)
    prior_sets: list[set[str]] = []
    seen_union: set[str] = set()
    out: list[str] = []
    pruned_total = 0
    for block in blocks:
        if not block.strip() or block.startswith("\n"):
            out.append(block)
            continue
        cleaned, pruned = _prune_paragraph_sentences(block, prior_sets, seen_union)
        pruned_total += pruned
        if cleaned.strip():
            out.append(cleaned)
    result = re.sub(r"\n{3,}", "\n\n", "".join(out)).strip()
    return result, pruned_total


class PostInferenceExergyTransducer:
    """Stateless post-inference transducer coupling KISH (Ω₁₇) and Fisher-Rao geometry."""

    def __init__(
        self,
        *,
        min_exergy_score: float = 0.70,
        max_slop_density: float = 0.02,
        max_fisher_rad: float = 1.25,
    ) -> None:
        if not (0.0 <= min_exergy_score <= 1.0):
            raise ValueError("min_exergy_score must be within [0.0, 1.0]")
        self.detector = LinguisticEntropyDetector()
        self.min_exergy_score = min_exergy_score
        self.max_slop_density = max_slop_density
        self.max_fisher_rad = max_fisher_rad

    def process(
        self,
        text: str,
        *,
        mode: TransduceMode = "transduce",
        prune_context_rot: bool = True,
    ) -> PostInferenceResult:
        if not isinstance(text, str):
            raise TypeError("text must be a string")
        if len(text) > MAX_TRANSDUCE_CHARS:
            raise ValueError(f"text exceeds maximum transduce budget ({MAX_TRANSDUCE_CHARS} chars)")
        if mode not in {"transduce", "audit", "gate"}:
            raise ValueError(f"unsupported transduce mode: {mode}")

        tag = blake3(text.encode("utf-8")).hexdigest()[:8]
        masked, spans = _mask_protected_spans(text, tag)
        expected_b3 = _digest_spans(spans)

        if mode == "transduce":
            after_slop, slop_removed = _aphairesis_slop(masked)
            if prune_context_rot:
                after_rot, rot_pruned = _prune_context_rot(after_slop)
            else:
                after_rot, rot_pruned = after_slop, 0
            restored, recovered = _unmask_protected_spans(after_rot, tag, spans)
            intact = len(recovered) == len(spans) and _digest_spans(recovered) == expected_b3
            final_text = restored if (intact and restored.strip()) else text.strip()
            if not intact:
                slop_removed = 0
                rot_pruned = 0
                intact = True
        else:
            final_text = text
            slop_removed = 0
            rot_pruned = 0
            intact = True

        rep_before = self.detector.analyze(text)
        rep_after = self.detector.analyze(final_text) if final_text != text else rep_before

        dist_before = _simplex_profile(rep_before)
        dist_after = _simplex_profile(rep_after)
        d_f_before = FisherInformationGeometry.fisher_rao_distance(dist_before, HIGH_EXERGY_PRIOR)
        d_f_after = FisherInformationGeometry.fisher_rao_distance(dist_after, HIGH_EXERGY_PRIOR)
        d_kl_after = FisherInformationGeometry.relative_entropy_kl(dist_after, HIGH_EXERGY_PRIOR)

        gate_passed = (
            rep_after.exergy_score >= self.min_exergy_score
            and rep_after.slop_density <= self.max_slop_density
            and d_f_after <= self.max_fisher_rad
        )

        receipt = PostInferenceReceipt(
            mode=mode,
            chars_before=len(text),
            chars_after=len(final_text),
            slop_spans_removed=slop_removed,
            rot_sentences_pruned=rot_pruned,
            exergy_before=round(rep_before.exergy_score, 4),
            exergy_after=round(rep_after.exergy_score, 4),
            exergy_delta=round(rep_after.exergy_score - rep_before.exergy_score, 4),
            word_entropy_before=rep_before.word_entropy,
            word_entropy_after=rep_after.word_entropy,
            context_rot_before=rep_before.context_rot_score,
            context_rot_after=rep_after.context_rot_score,
            slop_density_before=rep_before.slop_density,
            slop_density_after=rep_after.slop_density,
            fisher_rao_before=round(d_f_before, 6),
            fisher_rao_after=round(d_f_after, 6),
            kl_divergence_after=round(d_kl_after, 6),
            lexical_index_c5_v2=compute_c5_lexical_v2(final_text),
            protected_spans_count=len(spans),
            protected_spans_intact=intact,
            protected_spans_b3=expected_b3,
            gate_passed=gate_passed,
        )
        return PostInferenceResult(
            transduced_text=final_text,
            gate_passed=gate_passed,
            receipt=receipt,
        )


def collapse_low_entropy_lines(text: str, *, min_repeat: int = 3) -> str:
    """Collapse runs of identical non-empty lines in unstructured tool logs."""
    lines = text.splitlines()
    if len(lines) < min_repeat:
        return text
    out: list[str] = []
    idx = 0
    total = len(lines)
    while idx < total:
        current = lines[idx]
        run_end = idx + 1
        while run_end < total and lines[run_end] == current and current.strip():
            run_end += 1
        run_len = run_end - idx
        if run_len >= min_repeat:
            out.append(current)
            out.append(f"[×{run_len - 1} identical low-entropy lines collapsed]")
        else:
            out.extend(lines[idx:run_end])
        idx = run_end
    trailing = "\n" if text.endswith("\n") else ""
    return "\n".join(out) + trailing
