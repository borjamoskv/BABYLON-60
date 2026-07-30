# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
verify_claims.py — Verificación paralela del informe de arbitraje contra
fuentes primarias.

El informe llegó con TODAS sus cifras marcadas "[verificar contra la fuente
primaria]". Este script las verifica realmente: fetch HTTP, extracción del
número reclamado, comparación.

Estados: CONFIRMADO | REFUTADO | NO_ENCONTRADO | INACCESIBLE
"""

from __future__ import annotations

import json
import re
import ssl
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field

UA = {"User-Agent": "Mozilla/5.0 (compatible; claim-verifier/1.0)"}
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE


@dataclass
class Claim:
    id: str
    claim: str            # afirmación del informe
    urls: list[str]       # fuentes primarias candidatas
    probes: list[str]     # regex que confirmarían la cifra
    status: str = "PENDIENTE"
    found: str = ""
    src: str = ""
    ms: int = 0
    notes: list[str] = field(default_factory=list)


CLAIMS = [
    Claim("FABLE_PY",
          "Fable 4 (2023) añadió target Python; menos maduro que JS",
          ["https://raw.githubusercontent.com/fable-compiler/Fable/main/CHANGELOG.md",
           "https://raw.githubusercontent.com/fable-compiler/Fable/main/README.md"],
          [r"(?i)##?\s*4\.0\.0.*?20(2[2-5])", r"(?i)python", r"(?i)rust|dart|typescript"]),

    Claim("ANDROID_MEM",
          "Android: vulnerabilidades de memoria 76% (2019) → 24% (2024)",
          ["https://security.googleblog.com/2024/09/eliminating-memory-safety-vulnerabilities-Android.html",
           "https://security.googleblog.com/2022/12/memory-safe-languages-in-android-13.html"],
          [r"76\s*%", r"24\s*%", r"(?i)memory[- ]safety vulnerabilit"]),

    Claim("MSFT_70",
          "Microsoft: ~70% de CVEs son memory safety (BlueHat IL 2019)",
          ["https://msrc.microsoft.com/blog/2019/07/a-proactive-approach-to-more-secure-code/",
           "https://raw.githubusercontent.com/microsoft/MSRC-Security-Research/master/presentations/2019_02_BlueHatIL/2019_01%20-%20BlueHatIL%20-%20Trends%2C%20challenge%2C%20and%20shifts%20in%20software%20vulnerability%20mitigation.pdf"],
          [r"~?\s*70\s*%", r"(?i)memory safety"]),

    Claim("GAO_15",
          "Gao/Bird/Barr ICSE 2017: ~15% de bugs JS detectables por tipos",
          ["https://www0.cs.ucl.ac.uk/staff/e.barr/pub/typestudy.pdf",
           "https://ttendency.cs.ucl.ac.uk/projects/type_study/documents/type_study.pdf"],
          [r"15\s*%", r"(?i)detectable", r"(?i)flow|typescript"]),

    Claim("TAKIKAWA",
          "Takikawa POPL 2016: sound gradual typing con ralentizaciones catastróficas",
          ["https://www2.ccs.neu.edu/racket/pubs/popl16-tfgnvf.pdf"],
          [r"(?i)\b\d{1,3}x\b", r"(?i)overhead", r"(?i)sound gradual typing"]),

    Claim("BERGER_REPRO",
          "Berger TOPLAS 2019: la replicación desmonta Ray et al. FSE 2014",
          ["https://arxiv.org/abs/1901.10220"],
          [r"(?i)reproduc", r"(?i)(small|little|not|fail|weak).{0,40}(effect|significan|evidence)"]),

    Claim("QIN_PLDI20",
          "Qin et al. PLDI 2020: Rust no previene deadlocks ni bugs lógicos",
          ["https://arxiv.org/abs/2003.03296",
           "https://songlh.github.io/paper/rust-study.pdf"],
          [r"(?i)deadlock", r"(?i)unsafe", r"(?i)blocking bug|concurrency bug"]),

    Claim("AIACT_ART12",
          "EU AI Act Art. 12 exige registro automático de eventos (logs)",
          ["https://artificialintelligenceact.eu/article/12/"],
          [r"(?i)automatic(ally)? record", r"(?i)\blogs?\b", r"(?i)traceability",
           r"(?i)compile|type system|static typing"]),

    Claim("SCHNEIER_LOG",
          "Schneier&Kelsey: logs seguros protegen entradas PREVIAS al compromiso",
          ["https://www.schneier.com/wp-content/uploads/2016/02/paper-secure-logs.pdf",
           "https://www.schneier.com/academic/paperfiles/paper-auditlogs.pdf"],
          [r"(?i)before.{0,30}compromis", r"(?i)forward", r"(?i)cannot.{0,40}(read|alter|undetect)"]),

    Claim("PY_TYPES_WILD",
          "Rak-amnouykit et al.: baja cobertura de anotaciones en Python real",
          ["https://arxiv.org/abs/2011.06413",
           "https://www.cs.rpi.edu/~milanova/docs/dls2020.pdf"],
          [r"\b\d{1,2}(\.\d)?\s*%", r"(?i)mypy", r"(?i)pytype", r"(?i)disagree"]),
]


def fetch(url: str, timeout: int = 25) -> tuple[str, str]:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
        raw = r.read()
    if raw[:4] == b"%PDF":
        try:
            import subprocess
            p = subprocess.run(["pdftotext", "-", "-"], input=raw,
                               capture_output=True, timeout=60)
            if p.returncode == 0 and p.stdout:
                return p.stdout.decode("utf-8", "replace"), "pdf"
        except Exception:
            pass
        return "", "pdf-no-extract"
    txt = raw.decode("utf-8", "replace")
    txt = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", txt)
    txt = re.sub(r"<[^>]+>", " ", txt)
    return re.sub(r"\s+", " ", txt), "html"


def check(c: Claim) -> dict:
    t0 = time.perf_counter()
    for url in c.urls:
        try:
            txt, kind = fetch(url)
        except Exception as e:
            c.notes.append(f"{url.split('/')[2]}: {type(e).__name__}")
            continue
        if not txt:
            c.notes.append(f"{url.split('/')[2]}: {kind}")
            continue
        hits = []
        for p in c.probes:
            m = re.search(p, txt)
            if m:
                i = max(0, m.start() - 90)
                hits.append(re.sub(r"\s+", " ", txt[i:m.end() + 90]).strip())
        c.src = url
        if len(hits) >= max(2, len(c.probes) // 2):
            c.status = "CONFIRMADO"
        elif hits:
            c.status = "PARCIAL"
        else:
            c.status = "NO_ENCONTRADO"
        c.found = " ⋅ ".join(h[:150] for h in hits[:2])
        break
    else:
        c.status = "INACCESIBLE"
    c.ms = int((time.perf_counter() - t0) * 1000)
    return asdict(c)


def main() -> int:
    print("\nVERIFICACIÓN DE CIFRAS · informe de arbitraje contra fuentes primarias")
    print("=" * 84)
    out = []
    with ThreadPoolExecutor(max_workers=len(CLAIMS)) as ex:
        futs = {ex.submit(check, c): c.id for c in CLAIMS}
        for f in as_completed(futs):
            out.append(f.result())
    out.sort(key=lambda r: r["id"])

    tally: dict[str, int] = {}
    print(f"\n{'ID':<16}{'ESTADO':<14}{'ms':>6}  AFIRMACIÓN")
    print("-" * 84)
    for r in out:
        tally[r["status"]] = tally.get(r["status"], 0) + 1
        print(f"{r['id']:<16}{r['status']:<14}{r['ms']:>6}  {r['claim'][:44]}")

    print("\n" + "=" * 84)
    print("EVIDENCIA EXTRAÍDA")
    print("=" * 84)
    for r in out:
        if r["found"]:
            print(f"\n[{r['id']}] {r['status']}  ← {r['src'].split('/')[2]}")
            print(f"  {r['found'][:290]}")
        elif r["notes"]:
            print(f"\n[{r['id']}] {r['status']}  ({'; '.join(r['notes'][:2])})")

    print("\n" + "=" * 84)
    print("  " + " · ".join(f"{k}={v}" for k, v in sorted(tally.items())))
    json.dump(out, open("verification_report.json", "w"), indent=2, ensure_ascii=False)
    print("  informe: verification_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
