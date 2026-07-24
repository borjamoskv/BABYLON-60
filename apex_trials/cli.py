"""apex_trials.cli — C5-REAL operator surface.

    apex score    NCT01234567            # score + write ledger entry (visible trace)
    apex report   NCT01234567 -o out.html [--calibrate cancer]
    apex backtest --condition cancer -n 40
    apex verify                          # recompute + verify the whole hash-chain
    apex search  "breast cancer" --phase 3

Emoji protocol denotes ledger/hardware state only (per AGENTS.md), never sentiment.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

from typing import Any
import json
from pathlib import Path

import click

from .backtest import run_backtest
from .transducer import Transducer
from .ctgov import CtGovClient, HttpCache
from .ledger import AmendmentLedger
from .report import render_report

DEFAULT_DB = "master_ledger.db"
DEFAULT_CACHE = "ctgov_cache.db"


def _client() -> CtGovClient:
    return CtGovClient(cache=HttpCache(DEFAULT_CACHE))


def _get_ledger(db_path: str) -> Any:
    if db_path == "live-bft" or db_path.startswith("bft:"):
        from .ledger import BabylonBFTLedgerAdapter

        actual_path = db_path.split(":", 1)[1] if ":" in db_path else "cortex.db"
        return BabylonBFTLedgerAdapter(actual_path)
    return AmendmentLedger(db_path)


@click.group()
def cli() -> None:
    """APEX-TRIALS — deterministic, auditable clinical-trial amendment-risk transducer."""


@cli.command()
@click.argument("nct_id")
@click.option("--db", default=DEFAULT_DB, help="Ledger DB path (use 'live-bft' for BFT).")
@click.option("--json", "as_json", is_flag=True, help="Emit machine-readable JSON.")
def score(nct_id: str, db: str, as_json: bool) -> None:
    """Score a protocol and commit the decision to the hash-chain ledger."""
    with _get_ledger(db) as ledger:
        result = Transducer(_client(), ledger).score(nct_id)
    if as_json:
        click.echo(json.dumps(result.as_dict(), indent=2))
        return
    a, e, f = result.assessment, result.ledger_entry, result.features
    click.echo(f"\n🔍 {f.nct_id} — {f.brief_title[:64]}")
    click.echo(f"⚙️  {a.tier}  score={a.score}/100  (raw {a.raw_score}/114)  · {f.phase} · {f.therapeutic_area}")
    if a.expected_amendments is not None:
        click.echo(
            f"🧮 forecast {a.expected_amendments:.1f} substantive amendments  · model {a.mode} ({a.model_version})"
        )
    for r in a.fired_rules:
        if r.points:
            click.echo(f"    +{r.points:>2}/{r.max_points:<2}  {r.driver:<28} [{r.evidence}]")
    click.echo(f"💾 ledger id={e.id}")
    click.echo(f"   hash={e.entry_hash}")
    click.echo(f"   lamport_t={e.lamport_t}  taint={e.causal_taint}")
    if result.history is not None:
        h = result.history
        click.echo(f"🟢 ground-truth: {h.n_substantive} substantive amendments / {h.n_versions} versions on record")


@cli.command()
@click.argument("nct_id")
@click.option("-o", "--out", default=None, help="Output HTML path (default: <NCT>_apex.html).")
@click.option("--db", default=DEFAULT_DB, help="Ledger DB path (use 'live-bft' for BFT).")
@click.option("--calibrate", default=None, help="Condition to run cohort calibration against (optional).")
@click.option("-n", "--cohort", default=30, help="Cohort size for --calibrate.")
def report(nct_id: str, out: str | None, db: str, calibrate: str | None, cohort: int) -> None:
    """Render the Industrial Noir HTML attestation for a protocol."""
    client = _client()
    with _get_ledger(db) as ledger:
        result = Transducer(client, ledger).score(nct_id)
    bt = run_backtest(client, condition=calibrate, n=cohort) if calibrate else None
    target = Path(out) if out else Path(f"{result.features.nct_id}_apex.html")
    target.write_text(render_report(result, backtest=bt), encoding="utf-8")
    click.echo(f"💾 wrote {target}  ({result.assessment.tier} {result.assessment.score}/100)")


@cli.command()
@click.option("--condition", required=True, help="Condition query, e.g. 'cancer'.")
@click.option("-n", "--n", default=30, help="Cohort size.")
@click.option("--status", default="COMPLETED", help="overallStatus filter.")
@click.option("--json", "as_json", is_flag=True, help="Emit JSON.")
def backtest(condition: str, n: int, status: str, as_json: bool) -> None:
    """Calibrate the score against public amendment ground-truth."""
    rep = run_backtest(_client(), condition=condition, n=n, status=status)
    if as_json:
        click.echo(json.dumps(rep.as_dict(), indent=2))
        return
    click.echo(f"\n⚙️  cohort n={rep.n}  condition='{condition}'  Spearman ρ={rep.spearman:.3f}")
    for tier in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        tm = rep.tier_means.get(tier)
        if tm:
            click.echo(
                f"    {tier:<9} n={int(tm['n']):>2}  mean_score={tm['mean_score']:>5}  "
                f"mean_actual_amendments={tm['mean_actual_amendments']}"
            )


@cli.command()
@click.option("--db", default=DEFAULT_DB, help="Ledger DB path.")
def verify(db: str) -> None:
    """Recompute and verify the entire hash-chain."""
    with AmendmentLedger(db) as ledger:
        v = ledger.verify_chain()
    icon = "🟢" if v.valid else "🔴"
    click.echo(f"{icon} chain valid={v.valid}  entries={v.entries}  broken_at={v.broken_at}  {v.reason or ''}")


@cli.command()
@click.argument("query")
@click.option("--phase", default=None, help="Phase filter, e.g. 3.")
@click.option("--status", default=None, help="overallStatus filter.")
@click.option("-n", "--n", default=15, help="Result count.")
def search(query: str, phase: str | None, status: str | None, n: int) -> None:
    """Search ClinicalTrials.gov and list NCT ids."""
    studies = _client().search(condition=query, phase=phase, status=status, page_size=n)
    for st in studies:
        ident = st.get("protocolSection", {}).get("identificationModule", {})
        design = st.get("protocolSection", {}).get("designModule", {})
        phases = ",".join(design.get("phases", []) or ["NA"])
        click.echo(f"  {ident.get('nctId', '?'):<13} [{phases:<12}] {ident.get('briefTitle', '')[:66]}")


def main() -> None:
    cli()


if __name__ == "__main__":
    main()
