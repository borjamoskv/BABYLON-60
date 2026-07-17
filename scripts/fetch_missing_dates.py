#!/usr/bin/env python3
"""fetch_missing_dates.py — batch update dataset.json with enrollment_velocity.

Queries ClinicalTrials.gov API v2 in batches of 200 to fetch dates and computes
the enrollment velocity for each of the 8,000 trials in dataset.json.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

V2 = "https://clinicaltrials.gov/api/v2/studies"
USER_AGENT = "apex/0.1 (+moskv://cortex-persist)"


def _parse_date_to_months(date_str: str | None) -> float | None:
    if not date_str:
        return None
    parts = date_str.split("-")
    try:
        year = int(parts[0])
        month = int(parts[1]) if len(parts) > 1 else 1
        return year * 12.0 + month
    except (ValueError, IndexError):
        return None


def _calculate_duration_months(start_str: str | None, completion_str: str | None) -> float | None:
    start_m = _parse_date_to_months(start_str)
    comp_m = _parse_date_to_months(completion_str)
    if start_m is not None and comp_m is not None:
        diff = comp_m - start_m
        return max(1.0, diff)
    return None


def _get_api(url: str) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={"Accept": "application/json", "User-Agent": USER_AGENT}
    )
    last_err: Exception | None = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_err = exc
            time.sleep(1.0 * (2 ** attempt))
    raise RuntimeError(f"Failed to fetch {url}: {last_err}")


def main() -> None:
    dataset_path = Path("dataset.json")
    if not dataset_path.exists():
        print("ERROR: dataset.json not found.", flush=True)
        return

    rows = json.loads(dataset_path.read_text(encoding="utf-8"))
    ncts = [r["nct_id"] for r in rows]
    print(f"Loaded {len(rows)} trials from dataset.json", flush=True)

    study_dates: dict[str, dict[str, str | None]] = {}

    # Query in batches of 200
    for i in range(0, len(ncts), 200):
        batch = ncts[i:i + 200]
        params = {
            "filter.ids": ",".join(batch),
            "fields": "NCTId,StartDateStruct,CompletionDateStruct,PrimaryCompletionDateStruct",
            "pageSize": "200",
        }
        url = f"{V2}?{urllib.parse.urlencode(params)}"
        print(f"Fetching batch {i//200 + 1}/{len(ncts)//200 + 1}...", flush=True)
        try:
            data = _get_api(url)
            for st in data.get("studies", []):
                ps = st.get("protocolSection", {})
                nct = ps.get("identificationModule", {}).get("nctId")
                status = ps.get("statusModule", {})
                start = status.get("startDateStruct", {}).get("date")
                comp = status.get("completionDateStruct", {}).get("date")
                if not comp:
                    comp = status.get("primaryCompletionDateStruct", {}).get("date")
                if nct:
                    study_dates[nct] = {"start": start, "completion": comp}
        except Exception as e:
            print(f"Warning: batch failed: {e}", flush=True)
        time.sleep(0.5)

    print(f"Fetched dates for {len(study_dates)} studies.", flush=True)

    # Calculate enrollment velocity and update rows
    updated_count = 0
    for row in rows:
        nct = row["nct_id"]
        dates = study_dates.get(nct, {"start": None, "completion": None})
        duration = _calculate_duration_months(dates["start"], dates["completion"]) or 24.0

        enrollment = int(row.get("enrollment", 0) or 0)
        n_sites = int(row.get("n_sites", 0) or 0)
        sites = max(1, n_sites)

        velocity = enrollment / (sites * duration) if enrollment > 0 else 0.0
        row["enrollment_velocity"] = round(velocity, 6)
        updated_count += 1

    dataset_path.write_text(json.dumps(rows), encoding="utf-8")
    print(f"Successfully updated dataset.json: {updated_count} rows updated.", flush=True)


if __name__ == "__main__":
    main()
