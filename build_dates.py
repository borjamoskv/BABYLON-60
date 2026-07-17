"""build_dates.py — registration date per trial, for the temporal split.

Fetches studyFirstPostDate for the exact NCTs already in dataset.json using the
v2 filter.ids batch endpoint (200/req). Deterministic, exact coverage.

Output: dates.json  {nct_id: "YYYY-MM-DD"}
"""
from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

V2 = "https://clinicaltrials.gov/api/v2/studies"


def get(url: str) -> dict:
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "apex/0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        return json.loads(r.read().decode())


def main() -> None:
    rows = json.loads(Path("dataset.json").read_text())
    ncts = [r["nct_id"] for r in rows]
    dates: dict[str, str] = {}
    for i in range(0, len(ncts), 200):
        batch = ncts[i:i + 200]
        params = {
            "filter.ids": ",".join(batch),
            "fields": "NCTId,StudyFirstPostDate",
            "pageSize": "200",
        }
        data = get(f"{V2}?{urllib.parse.urlencode(params)}")
        for st in data.get("studies", []):
            ps = st.get("protocolSection", {})
            nct = ps.get("identificationModule", {}).get("nctId")
            date = ps.get("statusModule", {}).get("studyFirstPostDateStruct", {}).get("date")
            if nct and date:
                dates[nct] = date
        if (i // 200) % 10 == 0:
            print(f"  batch {i//200} · {len(dates)} dates", flush=True)

    Path("dates.json").write_text(json.dumps(dates))
    years = Counter(d[:4] for d in dates.values())
    print(f"\nDONE: {len(dates)}/{len(ncts)} dated ({100*len(dates)/len(ncts):.1f}%)")
    print("year histogram (registration / first-post):")
    cum = 0
    total = len(dates)
    for y in sorted(years):
        cum += years[y]
        print(f"  {y}: {years[y]:>4}   cum {100*cum/total:>5.1f}%")


if __name__ == "__main__":
    main()
