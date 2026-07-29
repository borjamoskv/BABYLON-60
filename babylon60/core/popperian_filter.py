"""
[C5-REAL] Popperian Falsification Filter.

Empirically calibrated via scripts/calibrate_popperian_entropy.py (INV_INGESTA_08).
Statistical basis: Technical Corpus Mean = 4.8326, StdDev = 0.3479.
Optimal Bounds: [3.79, 5.88] bits/char.

Author: Telmo Dinámico de Moskv (borjamoskv)
"""

import sys
import math
import re
import argparse
import unicodedata
from dataclasses import dataclass, field

# --- Constants ---

# Thermodynamic Valve: max payload size to prevent OOM (INV_C5_THERMO_VALVE)
MAX_PAYLOAD_BYTES: int = 1_048_576  # 1 MiB

# Empirically Calibrated Thresholds (C5-REAL - INV_INGESTA_08)
MIN_ENTROPY: float = 3.79
MAX_ENTROPY: float = 5.88

# C4-SIM Corporate Buzzwords (Syntactic Holograms)
# NOTE: This is a linear regex filter, NOT a Weisfeiler-Lehman graph hash.
# It is trivially bypassable by synonyms and homoglyphs. Treat as a first-pass sieve only.
HYPE_PATTERNS: list[str] = [
    r"game(\s|-)changer",
    r"100x",
    r"10x",
    r"passive income",
    r"synergy",
    r"disrupt(ive|ing)?",
    r"revolutionary",
    r"next(-|\s)?generation",
    r"paradigm shift",
    r"unpacking",
    r"delve",
    r"moonshot",
    r"silver bullet",
    r"no[- ]brainer",
    r"unlock(ing)?\s+(your|the|massive)",
    r"6[- ]figure",
    r"7[- ]figure",
    r"scale\s+to\s+(the\s+)?moon",
]

HYPE_REGEX = re.compile(r'\b(' + '|'.join(HYPE_PATTERNS) + r')\b', re.IGNORECASE)

# Physical Anchors (URL, SHA256 hex, Ethereum address)
ANCHOR_REGEX = re.compile(r'(https?://[^\s]+|[a-f0-9]{64}|0x[a-f0-9]{40})', re.IGNORECASE)

# --- Data Structures ---

@dataclass(frozen=True)
class FilterResult:
    """Structured result from the Popperian Filter for BFT DDB routing."""
    passed: bool
    reason: str
    entropy: float
    hype_matches: list[str] = field(default_factory=list)
    truncated: bool = False


# --- Core Functions ---

def normalize_unicode(text: str) -> str:
    """
    Apply NFKD Unicode normalization to collapse homoglyphs.
    This mitigates trivial Cyrillic/Greek substitution attacks (e.g., 'а' -> 'a').
    """
    return unicodedata.normalize("NFKD", text)


def shannon_entropy(data: str) -> float:
    """Calculate the Shannon entropy (bits/char) of a string."""
    if not data:
        return 0.0

    length = len(data)
    frequencies: dict[str, int] = {}
    for char in data:
        frequencies[char] = frequencies.get(char, 0) + 1

    entropy = 0.0
    for count in frequencies.values():
        prob = count / length
        entropy -= prob * math.log2(prob)

    return entropy


def evaluate_payload(text: str) -> FilterResult:
    """
    Evaluates text against the Popperian Thermodynamic Filter.

    Returns a structured FilterResult with reason codes suitable for
    Dependency-Directed Backtracking (DDB) in the BFT engine.
    """
    truncated = False

    # 0. Thermodynamic Valve: truncate oversized payloads (INV_C5_THERMO_VALVE)
    if len(text.encode("utf-8", errors="replace")) > MAX_PAYLOAD_BYTES:
        text = text[:MAX_PAYLOAD_BYTES]
        truncated = True

    # 0.1 Unicode normalization (anti-homoglyph)
    normalized = normalize_unicode(text)

    # 1. Shannon Entropy Check (UNBACKED thresholds)
    entropy = shannon_entropy(normalized)
    if entropy < MIN_ENTROPY:
        return FilterResult(
            passed=False,
            reason=f"ENTROPY_TOO_LOW ({entropy:.2f} < {MIN_ENTROPY})",
            entropy=entropy,
            truncated=truncated,
        )
    if entropy > MAX_ENTROPY:
        return FilterResult(
            passed=False,
            reason=f"ENTROPY_TOO_HIGH ({entropy:.2f} > {MAX_ENTROPY})",
            entropy=entropy,
            truncated=truncated,
        )

    # 2. Hype Pattern Masking (linear regex — NOT 1-WL)
    hype_matches_raw = HYPE_REGEX.findall(normalized)
    hype_matches = [m[0] if isinstance(m, tuple) else m for m in hype_matches_raw]
    if hype_matches:
        return FilterResult(
            passed=False,
            reason="HYPE_PATTERN_DETECTED",
            entropy=entropy,
            hype_matches=hype_matches,
            truncated=truncated,
        )

    # 3. Physical Anchor Requirement (for long-form claims only)
    if len(normalized) > 120:
        if not ANCHOR_REGEX.search(normalized):
            return FilterResult(
                passed=False,
                reason="MISSING_PHYSICAL_ANCHOR",
                entropy=entropy,
                truncated=truncated,
            )

    return FilterResult(
        passed=True,
        reason="PASSED",
        entropy=entropy,
        truncated=truncated,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Popperian Falsification Filter (C5-REAL). "
                    "Exit 0 = passed, Exit 2 = rejected."
    )
    parser.add_argument(
        "file", nargs="?",
        help="File to evaluate (reads from stdin if not provided)"
    )
    args = parser.parse_args()

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read(MAX_PAYLOAD_BYTES)
        except (OSError, UnicodeDecodeError) as e:
            print(f"[ERROR] Could not read file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        content = sys.stdin.read(MAX_PAYLOAD_BYTES)

    if not content.strip():
        print("[ERROR] Empty payload.", file=sys.stderr)
        sys.exit(1)

    result = evaluate_payload(content)

    # Structured diagnostic output to stderr
    if result.passed:
        print(
            f"[PASSED] Entropy: {result.entropy:.2f}. "
            f"No hype detected. Anchors validated."
            f"{' (TRUNCATED)' if result.truncated else ''}",
            file=sys.stderr,
        )
        print(content)
        sys.exit(0)
    else:
        detail = f"Reason: {result.reason}"
        if result.hype_matches:
            detail += f" | Matches: {result.hype_matches}"
        if result.truncated:
            detail += " | (TRUNCATED)"
        print(f"[REJECTED] {detail}", file=sys.stderr)
        sys.exit(2)  # Epistemological failure


if __name__ == "__main__":
    main()
