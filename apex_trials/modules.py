from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .features import StudyFeatures

_MODELS_PATH = Path(__file__).with_name("module_models.json")


def _load() -> dict[str, Any] | None:
    if _MODELS_PATH.exists():
        from typing import cast

        return cast(dict[str, Any], json.loads(_MODELS_PATH.read_text(encoding="utf-8")))
    return None


_MODELS: dict[str, Any] | None = _load()
_ENGLISH_STOP_WORDS = frozenset(
    [
        "a",
        "about",
        "above",
        "across",
        "after",
        "afterwards",
        "again",
        "against",
        "all",
        "almost",
        "alone",
        "along",
        "already",
        "also",
        "although",
        "always",
        "am",
        "among",
        "amongst",
        "amoungst",
        "amount",
        "an",
        "and",
        "another",
        "any",
        "anyhow",
        "anyone",
        "anything",
        "anyway",
        "anywhere",
        "are",
        "around",
        "as",
        "at",
        "back",
        "be",
        "became",
        "because",
        "become",
        "becomes",
        "becoming",
        "been",
        "before",
        "beforehand",
        "behind",
        "being",
        "below",
        "beside",
        "besides",
        "between",
        "beyond",
        "bill",
        "both",
        "bottom",
        "but",
        "by",
        "call",
        "can",
        "cannot",
        "cant",
        "co",
        "con",
        "could",
        "couldnt",
        "cry",
        "de",
        "describe",
        "detail",
        "do",
        "done",
        "down",
        "due",
        "during",
        "each",
        "eg",
        "eight",
        "either",
        "eleven",
        "else",
        "elsewhere",
        "empty",
        "enough",
        "etc",
        "even",
        "ever",
        "every",
        "everyone",
        "everything",
        "everywhere",
        "except",
        "few",
        "fifteen",
        "fifty",
        "fill",
        "find",
        "fire",
        "first",
        "five",
        "for",
        "former",
        "formerly",
        "forty",
        "found",
        "four",
        "from",
        "front",
        "full",
        "further",
        "get",
        "give",
        "go",
        "had",
        "has",
        "hasnt",
        "have",
        "he",
        "hence",
        "her",
        "here",
        "hereafter",
        "hereby",
        "herein",
        "hereupon",
        "hers",
        "herself",
        "him",
        "himself",
        "his",
        "how",
        "however",
        "hundred",
        "i",
        "ie",
        "if",
        "in",
        "inc",
        "indeed",
        "interest",
        "into",
        "is",
        "it",
        "its",
        "itself",
        "keep",
        "last",
        "latter",
        "latterly",
        "least",
        "less",
        "ltd",
        "made",
        "many",
        "may",
        "me",
        "meanwhile",
        "might",
        "mill",
        "mine",
        "more",
        "moreover",
        "most",
        "mostly",
        "move",
        "much",
        "must",
        "my",
        "myself",
        "name",
        "namely",
        "neither",
        "never",
        "nevertheless",
        "next",
        "nine",
        "no",
        "nobody",
        "none",
        "noone",
        "nor",
        "not",
        "nothing",
        "now",
        "nowhere",
        "of",
        "off",
        "often",
        "on",
        "once",
        "one",
        "only",
        "onto",
        "or",
        "other",
        "others",
        "otherwise",
        "our",
        "ours",
        "ourselves",
        "out",
        "over",
        "own",
        "part",
        "per",
        "perhaps",
        "please",
        "put",
        "rather",
        "re",
        "same",
        "see",
        "seem",
        "seemed",
        "seeming",
        "seems",
        "serious",
        "several",
        "she",
        "should",
        "show",
        "side",
        "since",
        "sincere",
        "six",
        "sixty",
        "so",
        "some",
        "somehow",
        "someone",
        "something",
        "sometime",
        "sometimes",
        "somewhere",
        "still",
        "such",
        "system",
        "take",
        "ten",
        "than",
        "that",
        "the",
        "their",
        "them",
        "themselves",
        "then",
        "thence",
        "there",
        "thereafter",
        "thereby",
        "therefore",
        "therein",
        "thereupon",
        "these",
        "they",
        "thick",
        "thin",
        "third",
        "this",
        "those",
        "though",
        "three",
        "through",
        "throughout",
        "thru",
        "thus",
        "to",
        "together",
        "too",
        "top",
        "toward",
        "towards",
        "twelve",
        "twenty",
        "two",
        "un",
        "under",
        "until",
        "up",
        "upon",
        "us",
        "very",
        "via",
        "was",
        "we",
        "well",
        "were",
        "what",
        "whatever",
        "when",
        "whence",
        "whenever",
        "where",
        "whereafter",
        "whereas",
        "whereby",
        "wherein",
        "whereupon",
        "wherever",
        "whether",
        "which",
        "while",
        "whither",
        "who",
        "whoever",
        "whole",
        "whom",
        "whose",
        "why",
        "will",
        "with",
        "within",
        "without",
        "would",
        "yet",
        "you",
        "your",
        "yours",
        "yourself",
        "yourselves",
    ]
)
_TOKEN_RE = re.compile("(?u)\\b\\w\\w+\\b")


def _tokenize_pure(text: str) -> list[str]:
    return [t for t in _TOKEN_RE.findall(text.lower()) if t not in _ENGLISH_STOP_WORDS]


def _get_ngrams(tokens: list[str]) -> list[str]:
    ngrams = []
    ngrams.extend(tokens)
    for i in range(len(tokens) - 1):
        ngrams.append(f"{tokens[i]} {tokens[i + 1]}")
    return ngrams


def _transform_pure(text: str, vocab: dict[str, int], idf: list[float]) -> list[float]:
    tokens = _tokenize_pure(text)
    ngrams = _get_ngrams(tokens)
    counts: dict[str, int] = {}
    for ngram in ngrams:
        if ngram in vocab:
            counts[ngram] = counts.get(ngram, 0) + 1
    V = len(vocab)
    vector = [0.0] * V
    for term, count in counts.items():
        idx = vocab[term]
        tf = 1.0 + math.log(count)
        vector[idx] = tf * idf[idx]
    sq_sum = sum(val**2 for val in vector)
    if sq_sum > 0:
        norm = math.sqrt(sq_sum)
        vector = [val / norm for val in vector]
    return vector


@dataclass(frozen=True)
class ModuleRisk:
    module: str
    label: str
    probability: float
    base_rate: float
    lift: float

    def as_dict(self) -> dict[str, Any]:
        return {
            "module": self.module,
            "label": self.label,
            "probability": self.probability,
            "base_rate": self.base_rate,
            "lift": self.lift,
        }


def _feature_map(f: StudyFeatures) -> dict[str, float]:
    phase_ord = {"EARLY_PHASE1": 1, "PHASE1": 1, "PHASE2": 2, "PHASE3": 3, "PHASE4": 1.5}.get(f.phase, 0)
    return {
        "n_eligibility_criteria": float(f.n_eligibility_criteria),
        "n_endpoints": float(f.n_primary_endpoints + f.n_secondary_endpoints),
        "n_arms": float(f.n_arms),
        "log_enrollment": math.log1p(f.enrollment),
        "n_countries": float(f.n_countries),
        "phase_ord": float(phase_ord),
        "is_crossover": 1.0 if "CROSSOVER" in f.intervention_model.upper() else 0.0,
        "is_factorial": 1.0 if "FACTORIAL" in f.intervention_model.upper() else 0.0,
        "high_masking": 1.0 if f.masking.upper() in ("TRIPLE", "QUADRUPLE") else 0.0,
        "is_oncology": 1.0 if f.is_oncology else 0.0,
        "is_rare": 1.0 if f.is_rare_disease else 0.0,
        "has_dmc": 1.0 if f.has_dmc else 0.0,
        "is_fda_regulated": 1.0 if f.is_fda_regulated else 0.0,
        "log_summary_words": math.log1p(f.brief_summary_words),
        "n_conditions": float(f.n_conditions),
        "n_interventions": float(f.n_interventions),
    }


def available() -> bool:
    return _MODELS is not None


def model_version() -> str | None:
    return _MODELS["model_version"] if _MODELS is not None else None


def predict_module_risks(
    features: StudyFeatures, eligibility_text: str = "", brief_summary_text: str = ""
) -> tuple[ModuleRisk, ...]:
    if _MODELS is None:
        return ()
    fmap = _feature_map(features)
    text_content = (eligibility_text + " " + brief_summary_text).strip()
    risks: list[ModuleRisk] = []
    for key, m in _MODELS["modules"].items():
        used = m["used_features"]
        mean, std, coef = (m["mean"], m["std"], m["coef"])
        logit = float(m["intercept"])
        for i, feat in enumerate(used):
            z = (fmap[feat] - mean[i]) / (std[i] if std[i] else 1.0)
            logit += coef[i] * z
        if "tfidf_vocab" in m and "tfidf_idf" in m and ("text_coef" in m) and text_content:
            vocab = m["tfidf_vocab"]
            idf = m["tfidf_idf"]
            text_coef = m["text_coef"]
            vec = _transform_pure(text_content, vocab, idf)
            for i, val in enumerate(vec):
                logit += text_coef[i] * val
        p = 1.0 / (1.0 + math.exp(-logit))
        base = float(m["base_rate"])
        risks.append(
            ModuleRisk(
                module=key,
                label=m["label"],
                probability=round(p, 4),
                base_rate=round(base, 4),
                lift=round(p / base, 3) if base > 0 else 0.0,
            )
        )
    risks.sort(key=lambda r: r.probability, reverse=True)
    return tuple(risks)
