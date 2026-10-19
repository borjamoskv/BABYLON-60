#!/usr/bin/env python3
"""
C5-REAL Canonical 3-Strata Entropy Quality Gate (audit_entropy_3strata.py)
==========================================================================
Executes the three orthogonal entropy audits required by c5-information-thermodynamics:
  - Stratum 1: Physical Silicon TRNG (/dev/urandom 64 KB, H(X) >= 7.9968, 0 parasitic daemons)
  - Stratum 2: Codebase Structural Entropy, Jaccard Clones (J >= 0.75) & Zero-Width Characters
  - Stratum 3: KISH Linguistic Entropy Transducer (Ω₁₇) on Canonical Specifications
"""

from __future__ import annotations

import argparse
import json
import math
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).absolute().parents[2]
_KISH_DIR = str(REPO_ROOT / "01_KISH_ENGINE")
if _KISH_DIR not in sys.path:
    sys.path.insert(0, _KISH_DIR)

from babylon60.transducers.linguistic_entropy import LinguisticEntropyDetector  # noqa: E402


class Stratum1Result(TypedDict):
    sample_bytes: int
    unique_byte_values: int
    shannon_entropy: float
    efficiency_pct: float
    haveged_active: bool
    rng_tools_active: bool
    passed: bool


class Stratum2Result(TypedDict):
    total_files: int
    entropy_by_ext: dict[str, float]
    epistemic_clones_count: int
    malicious_zw_count: int
    passed: bool


class DocEntropySummary(TypedDict):
    word_count: int
    word_entropy: float
    trigram_entropy: float
    mattr: float
    burstiness: float
    slop_density: float
    exergy_pct: float


class Stratum3Result(TypedDict):
    documents: dict[str, DocEntropySummary]
    min_exergy_pct: float
    max_slop_density: float
    passed: bool


class FullAuditReport(TypedDict):
    stratum_1: Stratum1Result
    stratum_2: Stratum2Result
    stratum_3: Stratum3Result
    overall_passed: bool


def audit_stratum_1(sample_size: int = 65536) -> Stratum1Result:
    with open("/dev/urandom", "rb") as f:
        data = f.read(sample_size)

    counts = Counter(data)
    total = len(data)
    h_shannon = 0.0
    for byte_val in range(256):
        c = counts[byte_val]
        if c > 0:
            p = c / total
            h_shannon -= p * math.log2(p)

    efficiency = (h_shannon / 8.0) * 100.0

    # Process diagnostics invariant: NEVER use -c flag with ps aux
    ps_proc = subprocess.run(["ps", "aux"], capture_output=True, text=True, check=True)
    ps_lines = [
        line.lower()
        for line in ps_proc.stdout.splitlines()
        if "audit_entropy_3strata" not in line and "python" not in line.lower()
    ]
    ps_blob = "\n".join(ps_lines)

    haveged = "haveged" in ps_blob
    rng_tools = "rngd" in ps_blob or "rng-tools" in ps_blob
    passed = efficiency >= 99.95 and not haveged and not rng_tools

    return {
        "sample_bytes": sample_size,
        "unique_byte_values": len(counts),
        "shannon_entropy": round(h_shannon, 6),
        "efficiency_pct": round(efficiency, 4),
        "haveged_active": haveged,
        "rng_tools_active": rng_tools,
        "passed": passed,
    }


def audit_stratum_2(root: Path = REPO_ROOT) -> Stratum2Result:
    valid_exts = {".rs", ".py", ".ts", ".astro", ".md", ".json"}
    exclude_dirs = {
        ".git",
        "node_modules",
        "dist",
        "target",
        ".venv",
        "__pycache__",
        "AUDIT_REPORTS_2026",
        "AUDITORIAS_EPISTEMICAS",
        ".lake",
        ".codex",
        "tmp",
        "build",
    }
    malicious_zw = {"\u200b", "\u200c", "\ufeff"}

    by_ext: dict[str, list[float]] = {ext: [] for ext in valid_exts}
    doc_tokens: dict[str, set[str]] = {}
    malicious_zw_count = 0
    total_files = 0

    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith(".")]
        for fname in files:
            path = Path(dirpath) / fname
            ext = path.suffix.lower()
            if ext not in valid_exts:
                continue
            try:
                raw = path.read_bytes()
            except OSError:
                continue
            if not raw:
                continue

            total_files += 1
            counts = Counter(raw)
            n_bytes = len(raw)
            h = -sum((c / n_bytes) * math.log2(c / n_bytes) for c in counts.values())
            by_ext[ext].append(h)

            if ext in {".md", ".rs", ".py", ".ts", ".astro"}:
                try:
                    text = raw.decode("utf-8")
                except UnicodeDecodeError:
                    continue
                for zw in malicious_zw:
                    malicious_zw_count += text.count(zw)
                if ext == ".md" and n_bytes < 200_000:
                    words = {w.lower() for w in text.split() if len(w) > 3}
                    if len(words) > 20:
                        doc_tokens[str(path.relative_to(root))] = words

    doc_keys = list(doc_tokens.keys())
    clones_count = 0
    for i in range(len(doc_keys)):
        t1 = doc_tokens[doc_keys[i]]
        for j in range(i + 1, len(doc_keys)):
            t2 = doc_tokens[doc_keys[j]]
            union = len(t1 | t2)
            if union > 0 and (len(t1 & t2) / union) >= 0.75:
                clones_count += 1

    avg_by_ext = {
        ext: round(sum(vals) / len(vals), 4)
        for ext, vals in sorted(by_ext.items())
        if vals
    }

    return {
        "total_files": total_files,
        "entropy_by_ext": avg_by_ext,
        "epistemic_clones_count": clones_count,
        "malicious_zw_count": malicious_zw_count,
        "passed": clones_count == 0 and malicious_zw_count == 0 and total_files > 0,
    }


def audit_stratum_3(root: Path = REPO_ROOT) -> Stratum3Result:
    detector = LinguisticEntropyDetector()
    targets = (
        "AGENTS.md",
        "docs/01_spec/spec_nemesis.md",
        "docs/01_spec/spec_exergy_ontology.md",
    )
    docs: dict[str, DocEntropySummary] = {}
    min_exergy = 100.0
    max_slop = 0.0

    for rel in targets:
        p = root / rel
        if not p.is_file():
            continue
        rep = detector.analyze(p.read_text(encoding="utf-8"))
        ex_pct = round(rep.exergy_score * 100.0, 2)
        min_exergy = min(min_exergy, ex_pct)
        max_slop = max(max_slop, rep.slop_density)
        docs[rel] = {
            "word_count": rep.word_count,
            "word_entropy": rep.word_entropy,
            "trigram_entropy": rep.trigram_entropy,
            "mattr": rep.mattr,
            "burstiness": rep.burstiness,
            "slop_density": rep.slop_density,
            "exergy_pct": ex_pct,
        }

    passed = bool(docs) and min_exergy >= 90.0 and max_slop == 0.0
    return {
        "documents": docs,
        "min_exergy_pct": min_exergy,
        "max_slop_density": max_slop,
        "passed": passed,
    }


def run_full_audit(root: Path = REPO_ROOT) -> FullAuditReport:
    s1 = audit_stratum_1()
    s2 = audit_stratum_2(root)
    s3 = audit_stratum_3(root)
    return {
        "stratum_1": s1,
        "stratum_2": s2,
        "stratum_3": s3,
        "overall_passed": s1["passed"] and s2["passed"] and s3["passed"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON output")
    args = parser.parse_args()

    report = run_full_audit()
    if args.json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        s1 = report["stratum_1"]
        s2 = report["stratum_2"]
        s3 = report["stratum_3"]
        print(
            f"[S1:TRNG] H(X)={s1['shannon_entropy']} bits/B ({s1['efficiency_pct']}%) | PASS={s1['passed']}"
        )
        print(
            f"[S2:CODE] files={s2['total_files']} | clones={s2['epistemic_clones_count']} | PASS={s2['passed']}"
        )
        print(
            f"[S3:KISH] min_exergy={s3['min_exergy_pct']}% | max_slop={s3['max_slop_density']} | PASS={s3['passed']}"
        )
    return 0 if report["overall_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
