"""End-to-end against the live ClinicalTrials.gov API. Network-dependent.

Skips cleanly when offline so the unit suite stays green in isolated CI.
"""

from __future__ import annotations

import urllib.error
import urllib.request

import pytest

from apex_trials import AmendmentLedger, Copilot, CtGovClient, HttpCache
from apex_trials.report import render_report


def _online() -> bool:
    try:
        urllib.request.urlopen("https://clinicaltrials.gov/api/v2/version", timeout=10)
        return True
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


pytestmark = pytest.mark.skipif(not _online(), reason="ClinicalTrials.gov unreachable")


def test_end_to_end_score_and_ledger(tmp_path) -> None:  # type: ignore
    client = CtGovClient(cache=HttpCache(str(tmp_path / "c.db")))
    with AmendmentLedger(tmp_path / "l.db") as ledger:
        result = Copilot(client, ledger).score("NCT00593697")
        assert result.features.nct_id == "NCT00593697"
        assert 0 <= result.assessment.score <= 100
        assert result.assessment.tier in ("LOW", "MODERATE", "HIGH", "CRITICAL")
        assert result.ledger_entry.entry_hash
        assert ledger.verify_chain().valid
        assert result.history is not None and result.history.n_versions >= 1
        html = render_report(result)
        assert html.startswith("<!DOCTYPE html>") and "APEX" in html and "localStorage" not in html


def test_search_returns_ncts(tmp_path) -> None:  # type: ignore
    client = CtGovClient(cache=HttpCache(str(tmp_path / "c.db")))
    studies = client.search(condition="breast cancer", status="COMPLETED", page_size=5)
    assert studies
    for st in studies:
        assert st["protocolSection"]["identificationModule"]["nctId"].startswith("NCT")
