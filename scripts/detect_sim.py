# C5-REAL EXERGY CERTIFIED
"""Synthetic Artifact & Simulation Detector (detect_sim.py)

Scans plan documents, text payloads, or markdown artifacts for synthetic
hexadecimal signatures, unbacked execution claims, unverifiable commit hashes,
and sourceless metrics (C4-SIM theater).
"""

import argparse
import json
import math
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

HEX_RE = re.compile(r"\b[0-9a-f]{32,64}\b", re.IGNORECASE)
SHORT_COMMIT_RE = re.compile(r"\[(?:master|main)\s+([0-9a-f]{7,40})\]")

CLAIM_PATTERNS = [
    r"\bRan command:",
    r"\bHe (?:ejecutado|actualizado|modificado|creado|escrito)\b",
    r"\bI (?:ran|executed|updated|created|wrote)\b",
    r"\bATP\s+SAVED\b",
    r"\bCommit_Hash:",
]

METRIC_NO_SOURCE_RE = re.compile(
    r"\b(ATP(?:\s+SAVED)?|EXERGY|ANERGIA|COHERENCE)\s*[:=+]\s*[+-]?\d+", re.IGNORECASE
)


def shannon_entropy(s: str) -> float:
    """Calculate character Shannon entropy."""
    if not s:
        return 0.0
    counts = Counter(s)
    n = len(s)
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def byte_pair_monotonic_ratio(h: str) -> float:
    """Ratio of strictly ascending consecutive byte pairs."""
    pairs = [h[i : i + 2] for i in range(0, len(h) - 1, 2)]
    if len(pairs) < 2:
        return 0.0
    vals = [int(p, 16) for p in pairs]
    ascending = sum(1 for a, b in zip(vals, vals[1:]) if b > a)
    return ascending / (len(vals) - 1)


def nibble_run_score(h: str) -> float:
    """Score sequential nibbles (0,1,2,3 / a,b,c,d)."""
    vals = [int(c, 16) for c in h]
    runs = sum(1 for a, b in zip(vals, vals[1:]) if b == (a + 1) % 16)
    return runs / max(len(vals) - 1, 1)


def analyze_hex(h: str) -> dict:
    """Analyze hex string for synthetic generation signatures."""
    h_low = h.lower()
    ent = shannon_entropy(h_low)
    mono = byte_pair_monotonic_ratio(h_low)
    nibble = nibble_run_score(h_low)

    flags = []
    if ent < 3.5:
        flags.append(f"LOW_ENTROPY({ent:.2f})")
    if mono > 0.72:
        flags.append(f"MONOTONIC_BYTES({mono:.2f})")
    if nibble > 0.30:
        flags.append(f"NIBBLE_RUNS({nibble:.2f})")

    return {
        "hex": h,
        "length": len(h),
        "entropy": round(ent, 3),
        "monotonic_ratio": round(mono, 3),
        "nibble_run_score": round(nibble, 3),
        "flags": flags,
        "suspect": len(flags) > 0,
    }


def commit_exists(sha: str) -> bool:
    """Check if a commit hash exists in local git ledger."""
    r = subprocess.run(
        ["git", "cat-file", "-t", sha], capture_output=True, text=True
    )
    return r.returncode == 0 and r.stdout.strip() == "commit"


def scan_text(text: str) -> dict:
    """Scan payload text for all synthetic artifact classes."""
    findings = {
        "synthetic_hashes": [],
        "unverifiable_commits": [],
        "unbacked_claims": [],
        "sourceless_metrics": [],
    }

    for h in set(HEX_RE.findall(text)):
        a = analyze_hex(h)
        if a["suspect"]:
            findings["synthetic_hashes"].append(a)

    for sha in set(SHORT_COMMIT_RE.findall(text)):
        if not commit_exists(sha):
            findings["unverifiable_commits"].append(sha)

    for pat in CLAIM_PATTERNS:
        for m in re.finditer(pat, text, re.IGNORECASE):
            snippet = text[max(0, m.start() - 40) : m.end() + 60].replace(
                "\n", " "
            )
            findings["unbacked_claims"].append(
                {
                    "pattern": pat,
                    "context": snippet.strip(),
                }
            )

    for m in METRIC_NO_SOURCE_RE.finditer(text):
        findings["sourceless_metrics"].append(m.group(0))

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Detect synthetic theater artifacts."
    )
    parser.add_argument("target", help="File path to inspect")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on claims in addition to synthetic hashes",
    )
    args = parser.parse_args()

    p = Path(args.target)
    if not p.exists():
        print(json.dumps({"error": "FILE_NOT_FOUND", "path": str(p)}))
        sys.exit(1)

    text = p.read_text(encoding="utf-8", errors="replace")
    findings = scan_text(text)

    hard_fail = (
        len(findings["synthetic_hashes"]) > 0
        or len(findings["unverifiable_commits"]) > 0
    )
    soft_fail = (
        len(findings["unbacked_claims"]) > 0
        or len(findings["sourceless_metrics"]) > 0
    )

    fail = hard_fail or (args.strict and soft_fail)

    result = {
        "target": str(p),
        "PASS": not fail,
        "hard_violations": {
            "synthetic_hashes": len(findings["synthetic_hashes"]),
            "unverifiable_commits": len(findings["unverifiable_commits"]),
        },
        "soft_violations": {
            "unbacked_claims": len(findings["unbacked_claims"]),
            "sourceless_metrics": len(findings["sourceless_metrics"]),
        },
        "findings": findings,
    }

    print(json.dumps(result, indent=2, ensure_ascii=False))
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
