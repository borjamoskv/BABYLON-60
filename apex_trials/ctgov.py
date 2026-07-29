"""apex_trials.ctgov — ClinicalTrials.gov API v2 client (+ internal history API).

Two data planes, both public:
  - v2 study records : GET /api/v2/studies            (search)
                       GET /api/v2/studies/{nct}       (single record)
  - version history  : GET /api/int/studies/{nct}/history
                       (the feed behind the site's "History of Changes" tab)

The history plane is the differentiating signal: it exposes, per protocol
version, WHICH modules changed (`moduleLabels`), so a *substantive* protocol
amendment (Eligibility / Study Design / Arms / Outcomes) can be told apart
from an administrative update (Study Status / Contacts). This is the public
ground-truth Biorce's black box does not surface.

Responses are cached to a local SQLite blob store so a scored protocol is
reproducible offline and API load stays polite. No third-party deps.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

import json
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

V2_BASE = "https://clinicaltrials.gov/api/v2"
INT_BASE = "https://clinicaltrials.gov/api/int"
USER_AGENT = "apex-trials/0.1 (+moskv://cortex-persist)"

# moduleLabels emitted by the history API, partitioned by regulatory weight.
# Vocabulary verified empirically against a 48-study sample (see labels probe).
SUBSTANTIVE_MODULES: frozenset[str] = frozenset(
    {
        "Study Design",
        "Outcome Measures",
        "Arms and Interventions",
        "Eligibility",
        "Conditions",
        "Study Description",
    }
)
ADMINISTRATIVE_MODULES: frozenset[str] = frozenset(
    {
        "Study Status",
        "Contacts/Locations",
        "Study Identification",
        "Sponsor/Collaborators",
        "More Information",
        "References",
        "Document Section",
        "Oversight",
        "Study Documents",
        "Recruitment Status",
    }
)
# Results-reporting sections: posted AFTER completion, not protocol amendments.
# Excluded from both amendment and admin counts.
RESULTS_MODULES: frozenset[str] = frozenset(
    {
        "Baseline Characteristics",
        "Outcome Measures (Results)",
        "Participant Flow",
        "Adverse Events",
        "Limitations and Caveats",
    }
)


class CtGovError(RuntimeError):
    """Raised on non-recoverable API failures (kept narrow; no bare except)."""


@dataclass(frozen=True)
class HttpCache:
    """Content-addressed HTTP cache so a run reproduces byte-for-byte offline."""

    db_path: str = "ctgov_cache.db"

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=5.0)
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute(
            "CREATE TABLE IF NOT EXISTS http_cache (url TEXT PRIMARY KEY, body TEXT NOT NULL, ts REAL NOT NULL);"
        )
        return conn

    def get(self, url: str) -> str | None:
        conn = self._conn()
        try:
            cur = conn.execute("SELECT body FROM http_cache WHERE url = ?;", (url,))
            row = cur.fetchone()
            return str(row[0]) if row is not None else None
        finally:
            conn.close()

    def put(self, url: str, body: str) -> None:
        conn = self._conn()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO http_cache (url, body, ts) VALUES (?,?,?);",
                (url, body, time.time()),
            )
            conn.commit()
        finally:
            conn.close()


class CtGovClient:
    def __init__(self, cache: HttpCache | None = None, timeout: float = 30.0, retries: int = 3) -> None:
        self.cache = cache
        self.timeout = timeout
        self.retries = retries

    def _fetch(self, url: str) -> dict[str, Any]:
        if self.cache is not None:
            cached = self.cache.get(url)
            if cached is not None:
                val = json.loads(cached)
                if isinstance(val, dict):
                    return val

        req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": USER_AGENT})
        last_err: Exception | None = None
        for attempt in range(1, self.retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read().decode("utf-8")
                if self.cache is not None:
                    self.cache.put(url, body)
                val = json.loads(body)
                if isinstance(val, dict):
                    return val
                raise CtGovError(f"Unexpected non-dict JSON response from {url}")
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise CtGovError(f"404 Not Found: {url}") from exc
                last_err = exc
            except (urllib.error.URLError, TimeoutError) as exc:
                last_err = exc
            except json.JSONDecodeError as exc:
                raise CtGovError(f"Invalid JSON from {url}") from exc
            time.sleep(0.4 * (2 ** (attempt - 1)))
        raise CtGovError(f"Failed after {self.retries} attempts: {url} ({last_err})")

    # -- v2 study records --------------------------------------------------------
    def get_study(self, nct_id: str) -> dict[str, Any]:
        nct = nct_id.strip().upper()
        return self._fetch(f"{V2_BASE}/studies/{urllib.parse.quote(nct)}")

    def search(
        self,
        condition: str | None = None,
        term: str | None = None,
        phase: str | None = None,
        status: str | None = None,
        page_size: int = 20,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {"pageSize": str(min(page_size, 1000))}
        if condition:
            params["query.cond"] = condition
        if term:
            params["query.term"] = term
        filters: list[str] = []
        if status:
            params["filter.overallStatus"] = status.upper()
        if phase:
            filters.append(f"AREA[Phase]{_normalize_phase(phase)}")
        if filters:
            params["filter.advanced"] = " AND ".join(filters)
        url = f"{V2_BASE}/studies?{urllib.parse.urlencode(params)}"
        data = self._fetch(url)
        return list(data.get("studies", []))

    # -- internal history plane --------------------------------------------------
    def get_history(self, nct_id: str) -> dict[str, Any]:
        nct = nct_id.strip().upper()
        return self._fetch(f"{INT_BASE}/studies/{urllib.parse.quote(nct)}/history")


@dataclass(frozen=True)
class AmendmentHistory:
    nct_id: str
    n_versions: int
    n_substantive: int
    n_administrative: int
    first_date: str | None
    last_date: str | None
    substantive_dates: tuple[str, ...]
    unknown_labels: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "nct_id": self.nct_id,
            "n_versions": self.n_versions,
            "n_substantive_amendments": self.n_substantive,
            "n_administrative_updates": self.n_administrative,
            "first_date": self.first_date,
            "last_date": self.last_date,
            "substantive_dates": list(self.substantive_dates),
            "unknown_labels": list(self.unknown_labels),
        }


def classify_history(nct_id: str, history: dict[str, Any]) -> AmendmentHistory:
    """Ground-truth: count substantive protocol amendments from version moduleLabels.

    Version 0 is the initial registration, not an amendment. A version counts as a
    substantive amendment iff any of its changed modules is in SUBSTANTIVE_MODULES.
    """
    changes = history.get("changes", [])
    n_versions = len(changes)
    n_substantive = 0
    n_administrative = 0
    substantive_dates: list[str] = []
    unknown: set[str] = set()
    dates: list[str] = []

    for change in changes:
        version = change.get("version", 0)
        date = change.get("date")
        if date:
            dates.append(date)
        labels = change.get("moduleLabels") or []
        if version == 0:
            continue  # initial registration
        is_substantive = False
        is_administrative = False
        for label in labels:
            if label in SUBSTANTIVE_MODULES:
                is_substantive = True
            elif label in ADMINISTRATIVE_MODULES:
                is_administrative = True
            elif label not in RESULTS_MODULES:
                unknown.add(label)
        if is_substantive:
            n_substantive += 1
            if date:
                substantive_dates.append(date)
        elif is_administrative:
            n_administrative += 1
        # else: results-only version -> not counted as a protocol amendment

    return AmendmentHistory(
        nct_id=nct_id,
        n_versions=n_versions,
        n_substantive=n_substantive,
        n_administrative=n_administrative,
        first_date=min(dates) if dates else None,
        last_date=max(dates) if dates else None,
        substantive_dates=tuple(substantive_dates),
        unknown_labels=tuple(sorted(unknown)),
    )


def _normalize_phase(phase: str) -> str:
    p = phase.strip().upper().replace(" ", "")
    mapping = {
        "1": "PHASE1",
        "2": "PHASE2",
        "3": "PHASE3",
        "4": "PHASE4",
        "PHASE1": "PHASE1",
        "PHASE2": "PHASE2",
        "PHASE3": "PHASE3",
        "PHASE4": "PHASE4",
        "I": "PHASE1",
        "II": "PHASE2",
        "III": "PHASE3",
        "IV": "PHASE4",
    }
    return mapping.get(p, p)
