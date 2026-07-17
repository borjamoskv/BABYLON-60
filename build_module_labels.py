"""build_module_labels.py — attach per-module amendment labels to the corpus.

Reuses the features already in dataset.json (current-record) and re-fetches each
trial's history to derive, per SUBSTANTIVE module, a binary label: was that module
amended in any post-registration version?

Leakage note: features come from the latest record, which for a completed trial is
post-amendment. The fitting step (fit_module_models.py) mitigates this by dropping
each target's SELF-REFERENTIAL feature (e.g. it does not use the final eligibility
count to predict whether eligibility was amended). Cross-feature signal is retained.

Output: dataset_modules.json
"""
from __future__ import annotations

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from apex_trials.ctgov import CtGovClient, CtGovError  # noqa: E402

SUBSTANTIVE = ["Eligibility", "Study Design", "Outcome Measures",
               "Arms and Interventions", "Conditions", "Study Description"]
MODULE_KEY = {
    "Eligibility": "elig", "Study Design": "design", "Outcome Measures": "outcomes",
    "Arms and Interventions": "arms", "Conditions": "conditions", "Study Description": "descr",
}
OUT = Path("dataset_modules.json")
TIME_CAP_S = 460.0


def module_labels(nct: str) -> dict[str, int] | None:
    client = CtGovClient(cache=None, timeout=30, retries=2)
    try:
        h = client.get_history(nct)
    except CtGovError:
        return None
    seen = {m: 0 for m in SUBSTANTIVE}
    for change in h.get("changes", []):
        if change.get("version", 0) == 0:
            continue
        for label in change.get("moduleLabels") or []:
            if label in seen:
                seen[label] = 1
    return {MODULE_KEY[m]: seen[m] for m in SUBSTANTIVE}


def main() -> None:
    rows = json.loads(Path("dataset.json").read_text())
    ncts = [r["nct_id"] for r in rows]
    by_nct = {r["nct_id"]: r for r in rows}
    out_rows: list[dict] = []
    t0 = time.monotonic()

    with ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(module_labels, nct): nct for nct in ncts}
        done = 0
        for fut in as_completed(futures):
            nct = futures[fut]
            done += 1
            labels = fut.result()
            if labels is None:
                continue
            row = dict(by_nct[nct])
            row.update({f"amended_{k}": v for k, v in labels.items()})
            out_rows.append(row)
            if done % 1500 == 0:
                print(f"  {done}/{len(ncts)} elapsed={time.monotonic()-t0:.0f}s", flush=True)
            if time.monotonic() - t0 > TIME_CAP_S:
                print("  time cap reached", flush=True)
                break

    OUT.write_text(json.dumps(out_rows))
    n = len(out_rows)
    print(f"\nDONE: {n} rows in {time.monotonic()-t0:.0f}s")
    print("base rates (P(module amended)):")
    for m in SUBSTANTIVE:
        k = MODULE_KEY[m]
        rate = sum(r[f"amended_{k}"] for r in out_rows) / max(n, 1)
        print(f"  {m:<26} {rate:.3f}")
    print(f"saved -> {OUT}")


if __name__ == "__main__":
    main()
