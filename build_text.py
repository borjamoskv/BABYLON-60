"""build_text.py — protocol free-text per trial, for TF-IDF features.

Fetches EligibilityCriteria + BriefSummary for the exact NCTs in dataset.json via
the v2 filter.ids batch endpoint. Deterministic, exact coverage.

Output: texts.json  {nct_id: {"elig": "...", "brief": "..."}}
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

V2 = "https://clinicaltrials.gov/api/v2/studies"


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "apex/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode())


def main() -> None:
    rows = json.loads(Path("dataset.json").read_text())
    ncts = [r["nct_id"] for r in rows]
    texts: dict[str, dict[str, str]] = {}
    for i in range(0, len(ncts), 200):
        batch = ncts[i:i + 200]
        params = {
            "filter.ids": ",".join(batch),
            "fields": "NCTId,EligibilityCriteria,BriefSummary",
            "pageSize": "200",
        }
        data = get(f"{V2}?{urllib.parse.urlencode(params)}")
        for st in data.get("studies", []):
            ps = st.get("protocolSection", {})
            nct = ps.get("identificationModule", {}).get("nctId")
            if not nct:
                continue
            elig = ps.get("eligibilityModule", {}).get("eligibilityCriteria", "") or ""
            brief = ps.get("descriptionModule", {}).get("briefSummary", "") or ""
            texts[nct] = {"elig": elig, "brief": brief}
        if (i // 200) % 10 == 0:
            print(f"  batch {i//200} · {len(texts)} texts", flush=True)

    Path("texts.json").write_text(json.dumps(texts))
    lens = [len(v["elig"]) + len(v["brief"]) for v in texts.values()]
    empty = sum(1 for v in texts.values() if not (v["elig"] + v["brief"]).strip())
    print(f"\nDONE: {len(texts)}/{len(ncts)} texts")
    print(f"  mean chars: {sum(lens)/max(len(lens),1):.0f}  ·  empty: {empty}")
    print("saved -> texts.json")


if __name__ == "__main__":
    main()
