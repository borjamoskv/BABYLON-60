#!/usr/bin/env python3
"""
aphorism5_cost_linter.py — Linter Determinista de Asimetría de Coste de Falsificación (Aforismo 5)
Mide la densidad de señales voluntarias (Cheap Talk / retórica adjetival / anergía DDD)
frente a señales involuntarias de alto coste (hashes, métricas SI, firmas, referencias físicas).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List

VOLUNTARY_CHEAP_TALK_PATTERNS = [
    r"\b(increíblemente|altamente|extremadamente|revolucionario|mágico|perfecto|inmejorable)\b",
    r"\b(very|extremely|revolutionary|seamless|cutting-edge|world-class|game-changing|magic)\b",
    r"\b(ThreadManager|DataManager|HelperClass|BaseUtil|ServiceWrapper|AbstractHelper)\b",
    r"//\s*TODO:\s*fix\s*later",
]

INVOLUNTARY_HIGH_COST_PATTERNS = [
    r"\b[a-f0-9]{64}\b",  # SHA-256 / SHA3-256
    r"\b\d+(?:\.\d+)?\s*(?:ms|µs|ns|MB/s|GB/s|Hz|dB|LUFS|bits/byte)\b",  # Métricas instrumentales
    r"(?:O\(1\)|O\(\\log\s*N\)|O\(N\)|RFO=0|MAP_SHARED|COSE_Sign1|ΔS\s*<\s*0|C_\\text\{falsify\})",  # Invariantes de sustrato
]


def audit_file(path: Path) -> Dict[str, object]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    # Cortafuegos 11 (Aforismo 2): El detector (ejemplos entrecomillados/backticks) no es la fuga
    prose_text = re.sub(r"`[^`]+`|\"[^\"]+\"", "", raw_text)

    voluntary_hits: List[str] = []
    for pat in VOLUNTARY_CHEAP_TALK_PATTERNS:
        voluntary_hits.extend(re.findall(pat, prose_text, flags=re.IGNORECASE))

    involuntary_hits: List[str] = []
    for pat in INVOLUNTARY_HIGH_COST_PATTERNS:
        involuntary_hits.extend(re.findall(pat, raw_text))

    v_count = len(voluntary_hits)
    i_count = len(involuntary_hits)
    exergy_ratio = round((i_count + 1) / (v_count + 1), 4)

    return {
        "file": str(path),
        "voluntary_cheap_talk_count": v_count,
        "involuntary_substrate_signals": i_count,
        "exergy_signal_ratio": exergy_ratio,
        "status": "PASS" if v_count == 0 or exergy_ratio >= 1.0 else "WARN_CHEAP_TALK",
        "samples_flagged": voluntary_hits[:10],
    }


def main() -> int:
    targets = [Path(arg) for arg in sys.argv[1:]]
    if not targets:
        print("Usage: aphorism5_cost_linter.py <file_or_dir>...", file=sys.stderr)
        return 1

    results = []
    for t in targets:
        if t.is_file():
            results.append(audit_file(t))
        elif t.is_dir():
            for sub in sorted(t.rglob("*.md")):
                results.append(audit_file(sub))

    print(json.dumps(results, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
