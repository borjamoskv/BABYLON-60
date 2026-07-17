"""build_dataset.py — assemble a labeled corpus for weight fitting.

Pages full completed INTERVENTIONAL study records from the v2 API (features come
for free in the page payload), then fetches each protocol's version history in
parallel to derive the ground-truth substantive-amendment count.

Output: dataset.json  (list of {features..., target n_substantive, n_versions}).
Reproducible & resumable: re-running loads dataset.json if already present.
"""
from __future__ import annotations

import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.ctgov import CtGovClient, CtGovError, V2_BASE, classify_history  # noqa: E402
from apex_trials.features import extract_features  # noqa: E402

TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 3000
TIME_CAP_S = float(sys.argv[2]) if len(sys.argv) > 2 else 470.0
OUT = Path("dataset.json")


def page_studies(page_token: str | None) -> tuple[list[dict], str | None]:
    params = {
        "filter.overallStatus": "COMPLETED",
        "filter.advanced": "AREA[StudyType]INTERVENTIONAL",
        "pageSize": "200",
        "countTotal": "false",
    }
    if page_token:
        params["pageToken"] = page_token
    url = f"{V2_BASE}/studies?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "apex-trials/0.1"})
    with urllib.request.urlopen(req, timeout=45) as r:
        data = json.loads(r.read().decode())
    return data.get("studies", []), data.get("nextPageToken")


def fetch_target(nct: str) -> tuple[str, int, int] | None:
    client = CtGovClient(cache=None, timeout=30, retries=2)  # cacheless: no sqlite contention
    try:
        h = classify_history(nct, client.get_history(nct))
    except CtGovError:
        return None
    return nct, h.n_substantive, h.n_versions


def main() -> None:
    if OUT.exists():
        rows = json.loads(OUT.read_text())
        print(f"loaded existing dataset.json: {len(rows)} rows")
        return

    t0 = time.monotonic()
    rows: list[dict] = []
    feat_by_nct: dict[str, dict] = {}
    token: str | None = None
    pages = 0

    with ThreadPoolExecutor(max_workers=12) as pool:
        while len(rows) < TARGET and (time.monotonic() - t0) < TIME_CAP_S:
            studies, token = page_studies(token)
            pages += 1
            if not studies:
                break
            batch: list[str] = []
            for st in studies:
                f = extract_features(st)
                if f.nct_id == "?" or f.nct_id in feat_by_nct:
                    continue
                feat_by_nct[f.nct_id] = f.as_dict()
                batch.append(f.nct_id)

            futures = {pool.submit(fetch_target, nct): nct for nct in batch}
            for fut in as_completed(futures):
                res = fut.result()
                if res is None:
                    continue
                nct, n_sub, n_ver = res
                row = dict(feat_by_nct[nct])
                row["target_substantive"] = n_sub
                row["n_versions"] = n_ver
                rows.append(row)

            if pages % 3 == 0 or len(rows) >= TARGET:
                el = time.monotonic() - t0
                print(f"  pages={pages} rows={len(rows)} elapsed={el:.0f}s", flush=True)
            if token is None:
                break

    OUT.write_text(json.dumps(rows))
    el = time.monotonic() - t0
    n_amended = sum(1 for r in rows if r["target_substantive"] > 0)
    mean_amend = sum(r["target_substantive"] for r in rows) / max(len(rows), 1)
    print(f"\nDONE: {len(rows)} rows in {el:.0f}s across {pages} pages")
    print(f"  with >=1 substantive amendment: {n_amended} ({100*n_amended/max(len(rows),1):.1f}%)")
    print(f"  mean substantive amendments: {mean_amend:.2f}")
    print(f"  saved -> {OUT}")


if __name__ == "__main__":
    main()
