"""demo.py — one-shot C5-REAL demonstration of the APEX-TRIALS pipeline.

    python demo.py

Scores a complex multinational oncology Phase 3 trial, commits the decision to a
fresh hash-chain ledger, prints the ground-truth amendment history it is validated
against, verifies the chain, and writes the Industrial Noir HTML attestation.
"""
from __future__ import annotations

from pathlib import Path

from apex_trials import AmendmentLedger, Copilot, CtGovClient, HttpCache
from apex_trials.backtest import run_backtest
from apex_trials.report import render_report

SHOWCASE = "NCT01245062"  # trametinib vs chemo, metastatic melanoma, 19 countries, PHASE3


def main() -> None:
    client = CtGovClient(cache=HttpCache("ctgov_cache.db"))
    ledger = AmendmentLedger("master_ledger.db")
    result = Copilot(client, ledger).score(SHOWCASE)

    a, e, h = result.assessment, result.ledger_entry, result.history
    print(f"\n[{a.tier}] {a.nct_id}  score={a.score}/100  raw={a.raw_score}/114")
    for r in a.fired_rules:
        if r.points:
            print(f"  +{r.points:>2}/{r.max_points:<2} {r.driver:<26} {r.evidence}")
    print(f"\n  ledger.entry_hash = {e.entry_hash}")
    print(f"  causal_taint      = {e.causal_taint}")
    if h is not None:
        print(f"\n  GROUND-TRUTH: predicted {a.score}/100 ({a.tier}); "
              f"record shows {h.n_substantive} substantive amendments across {h.n_versions} versions")

    print(f"\n  chain: {ledger.verify_chain().as_dict()}")

    bt = run_backtest(client, condition="melanoma", n=30)
    Path(f"{SHOWCASE}_apex.html").write_text(render_report(result, backtest=bt), encoding="utf-8")
    print(f"  wrote {SHOWCASE}_apex.html  (Spearman ρ={bt.spearman:.3f}, n={bt.n})")
    ledger.close()


if __name__ == "__main__":
    main()
