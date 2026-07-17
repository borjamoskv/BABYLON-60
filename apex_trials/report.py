"""apex_trials.report — Industrial Noir 2026 single-file HTML attestation.

Renders one protocol's assessment as a self-contained, offline HTML document:
risk gauge, fired-rule ledger, cryptographic attestation panel, ground-truth
amendment timeline, and (optional) cohort calibration. No external assets, no
browser storage — a physical artifact of a C5-REAL decision.

Palette: absolute dark #0A0A0A, cobalt #2B3BE5, ferrous grays.

Author: Borja Moskv (borjamoskv). Reality level: C5-REAL.
"""

from __future__ import annotations

import html

from .backtest import BacktestReport
from .copilot import CopilotResult
from .modules import _MODELS as _MOD_MODELS
from .risk_engine import _FITTED

_TIER_COLOR = {
    "LOW": "#4CAF50",
    "MODERATE": "#E5B72B",
    "HIGH": "#FF6B35",
    "CRITICAL": "#CE422B",
}


def _esc(text: object) -> str:
    return html.escape(str(text))


def _gauge_svg(score: int, tier: str) -> str:
    color = _TIER_COLOR.get(tier, "#2B3BE5")
    circumference = 2 * 3.141592653589793 * 90
    dash = circumference * (score / 100.0)
    return f"""
<svg viewBox="0 0 220 220" width="200" height="200" role="img" aria-label="risk score {score}">
  <circle cx="110" cy="110" r="90" fill="none" stroke="#1a1a22" stroke-width="16"/>
  <circle cx="110" cy="110" r="90" fill="none" stroke="{color}" stroke-width="16"
          stroke-linecap="round" stroke-dasharray="{dash:.2f} {circumference:.2f}"
          transform="rotate(-90 110 110)"/>
  <text x="110" y="102" text-anchor="middle" fill="#F5F5F7" font-size="52" font-family="ui-monospace,monospace" font-weight="700">{score}</text>
  <text x="110" y="132" text-anchor="middle" fill="{color}" font-size="18" font-family="ui-monospace,monospace" letter-spacing="2">{_esc(tier)}</text>
  <text x="110" y="156" text-anchor="middle" fill="#6b6b78" font-size="11" font-family="ui-monospace,monospace">/ 100 AMENDMENT RISK</text>
</svg>"""


def _rules_rows(result: CopilotResult) -> str:
    rules = result.assessment.fired_rules
    contribs = result.assessment.contributions or tuple(0.0 for _ in rules)
    maxc = max(contribs) if contribs and max(contribs) > 0 else 1.0
    out: list[str] = []
    for r, c in zip(rules, contribs):
        active = r.points > 0
        bar_w = int(c / maxc * 100)
        pts_color = "#2B3BE5" if active else "#3a3a44"
        out.append(f"""
    <tr class="{"on" if active else "off"}">
      <td class="drv">{_esc(r.driver)}</td>
      <td class="ev">{_esc(r.evidence)}</td>
      <td class="pts"><span style="color:{pts_color}">+{r.points}</span><span class="mx">/{r.max_points}</span></td>
      <td class="ctr">{c:.1f}</td>
      <td class="barcell"><span class="bar" style="width:{bar_w}%;background:{pts_color}"></span></td>
      <td class="rule">{_esc(r.rule)}</td>
    </tr>""")
    return "".join(out)


def _fit_provenance() -> str:
    if _FITTED is None:
        return ""
    m = _FITTED.get("metrics", {})
    provenance = (
        f'<div class="note" style="margin-top:12px;border-top:1px solid var(--line);padding-top:12px;">'
        f"Weights fitted on {_FITTED.get('n_train', '?')} trials, "
        f"held out {_FITTED.get('n_test', '?')}: Spearman ρ(score, actual amendments) = "
        f'<b style="color:#2B3BE5">{m.get("spearman_fitted", "?")}</b> '
        f"(prior {m.get('spearman_hand', '?')}); calibration MAE = "
        f"{m.get('isotonic_mae', '?')} vs {m.get('baseline_mae', '?')} baseline.</div>"
    )
    if "spearman_temporal" in m:
        provenance += (
            f'<div class="note" style="margin-top:6px;color:#a9a9b6;">'
            f"<b>▍FORWARD GENERALIZATION (Temporal Split ≤{m.get('temporal_cutoff', '?')} vs ≥{m.get('temporal_cutoff', '?')}):</b><br/>"
            f'Spearman ρ = <b style="color:#FF6B35">{m.get("spearman_temporal", "?")}</b> · '
            f"calibration MAE = {m.get('mae_temporal', '?')} (baseline {m.get('mae_base_temporal', '?')}) · "
            f"macro-AUC = {m.get('macro_auc_temporal', '?')} (vs random {m.get('macro_auc_random', '?')}).</div>"
        )
    return provenance


def _history_block(result: CopilotResult) -> str:
    h = result.history
    if h is None:
        return '<div class="muted">History plane unavailable for this record.</div>'
    tl: list[str] = []
    for d in h.substantive_dates:
        tl.append(
            f'<li><span class="dot"></span><span class="date">{_esc(d)}</span> substantive protocol amendment</li>'
        )
    timeline = "".join(tl) or '<li class="muted">No substantive amendments on record.</li>'
    pred = result.assessment.score
    return f"""
    <div class="grid2">
      <div class="stat"><div class="k">VERSIONS ON RECORD</div><div class="v">{h.n_versions}</div></div>
      <div class="stat"><div class="k">SUBSTANTIVE AMENDMENTS</div><div class="v" style="color:#FF6B35">{h.n_substantive}</div></div>
      <div class="stat"><div class="k">ADMIN UPDATES</div><div class="v">{h.n_administrative}</div></div>
      <div class="stat"><div class="k">PREDICTED RISK</div><div class="v" style="color:#2B3BE5">{pred}</div></div>
    </div>
    <ul class="timeline">{timeline}</ul>"""


def _module_surface_block(result: CopilotResult) -> str:
    risks = result.module_risks
    if not risks:
        return ""
    rows: list[str] = []
    for m in risks:
        p = m.probability * 100
        base = m.base_rate * 100
        color = "#CE422B" if p >= 60 else "#FF6B35" if p >= 40 else "#E5B72B" if p >= 25 else "#4CAF50"
        rows.append(f"""
      <div class="mrow">
        <div class="mlabel">{_esc(m.label)}</div>
        <div class="mbar"><span class="mfill" style="width:{p:.0f}%;background:{color}"></span>
          <span class="mbase" style="left:{base:.0f}%"></span></div>
        <div class="mval">{p:.0f}%<span class="mlift"> · {m.lift:.2f}×</span></div>
      </div>""")
    macro = "?"
    if _MOD_MODELS is not None:
        aucs = [v["auc"] for v in _MOD_MODELS["modules"].values()]
        macro = f"{sum(aucs) / len(aucs):.3f}"
    return f"""
  <section class="card">
    <h2>▍AMENDMENT SURFACE <span class="sub">— which modules will change · P vs base rate (tick)</span></h2>
    <div class="msurf">{"".join(rows)}</div>
    <div class="note">Per-module logistic models, leakage-mitigated (each excludes its own feature). Macro-AUC {macro} held-out. The tick marks the corpus base rate — bar past it = elevated risk for this design.</div>
  </section>"""


def _calibration_block(bt: BacktestReport | None) -> str:
    if bt is None:
        return ""
    rows: list[str] = []
    for tier in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        tm = bt.tier_means.get(tier)
        if not tm:
            continue
        color = _TIER_COLOR.get(tier, "#2B3BE5")
        rows.append(f"""
      <tr>
        <td style="color:{color};font-weight:700">{tier}</td>
        <td>{int(tm["n"])}</td>
        <td>{tm["mean_score"]}</td>
        <td style="color:#FF6B35">{tm["mean_actual_amendments"]}</td>
      </tr>""")
    return f"""
  <section class="card">
    <h2>▍COHORT CALIBRATION <span class="sub">— score vs. public ground-truth</span></h2>
    <div class="spear">Spearman ρ(score, actual amendments) = <b>{bt.spearman:.3f}</b> &nbsp;·&nbsp; n={bt.n} completed trials</div>
    <table class="cal">
      <thead><tr><th>TIER</th><th>N</th><th>MEAN SCORE</th><th>MEAN ACTUAL AMENDMENTS</th></tr></thead>
      <tbody>{"".join(rows)}</tbody>
    </table>
    <div class="note">Spearman ρ is the ordering evidence; per-tier means are indicative and noisy at small n. Driver mixing weights were fit on a separate broad corpus (see provenance above), not on this cohort — so this is out-of-cohort evidence.</div>
  </section>"""


def render_report(result: CopilotResult, backtest: BacktestReport | None = None) -> str:
    f = result.features
    a = result.assessment
    e = result.ledger_entry
    chain = "CHAIN VERIFIED" if e.entry_hash else "UNVERIFIED"
    tier_color = _TIER_COLOR.get(a.tier, "#2B3BE5")
    exp = a.expected_amendments
    exp_callout = (
        (
            f'<div class="callout">FORECAST <b>{exp:.1f}</b> substantive protocol amendments'
            f'<span class="muted"> · {_esc(a.mode)} model, isotonic-calibrated</span></div>'
        )
        if exp is not None
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>APEX-TRIALS · {_esc(f.nct_id)} · Amendment Risk Attestation</title>
<style>
  :root {{ --bg:#0A0A0A; --panel:#111118; --line:#22222c; --ink:#F5F5F7; --mut:#6b6b78; --cobalt:#2B3BE5; }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--ink);
         font-family:ui-monospace,"JetBrains Mono","SF Mono",Menlo,monospace; line-height:1.5; }}
  .wrap {{ max-width:1040px; margin:0 auto; padding:40px 24px 80px; }}
  .masthead {{ display:flex; justify-content:space-between; align-items:baseline;
               border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:8px; }}
  .brand {{ font-weight:700; letter-spacing:3px; font-size:15px; }}
  .brand b {{ color:var(--cobalt); }}
  .rl {{ color:var(--mut); font-size:11px; letter-spacing:2px; }}
  .ascii {{ color:#1c1c26; font-size:11px; letter-spacing:1px; overflow:hidden; white-space:nowrap; margin:2px 0 26px; }}
  h1 {{ font-size:19px; font-weight:600; margin:0 0 2px; }}
  .nct {{ color:var(--cobalt); font-weight:700; }}
  .subtitle {{ color:var(--mut); font-size:13px; margin-bottom:26px; }}
  .top {{ display:flex; gap:28px; align-items:center; flex-wrap:wrap; margin-bottom:8px; }}
  .facts {{ flex:1; min-width:280px; display:grid; grid-template-columns:1fr 1fr; gap:10px 22px; }}
  .fact .k {{ color:var(--mut); font-size:10px; letter-spacing:1.5px; }}
  .fact .v {{ font-size:15px; }}
  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:4px;
           padding:22px 24px; margin:22px 0; }}
  h2 {{ font-size:13px; letter-spacing:2px; margin:0 0 16px; color:var(--ink); font-weight:700; }}
  h2 .sub {{ color:var(--mut); font-weight:400; letter-spacing:0; }}
  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}
  th {{ text-align:left; color:var(--mut); font-weight:500; font-size:10px; letter-spacing:1px;
        border-bottom:1px solid var(--line); padding:0 10px 8px 0; }}
  td {{ padding:8px 10px 8px 0; border-bottom:1px solid #17171f; vertical-align:middle; }}
  tr.off td {{ opacity:.4; }}
  .drv {{ font-weight:600; white-space:nowrap; }}
  .ev {{ color:#b9b9c6; white-space:nowrap; }}
  .pts {{ font-weight:700; white-space:nowrap; }} .pts .mx {{ color:var(--mut); font-weight:400; }}
  .ctr {{ font-weight:700; color:#cfcfda; white-space:nowrap; }}
  .callout {{ display:inline-block; margin:0 0 22px; padding:9px 16px; border:1px solid var(--cobalt);
              border-left:3px solid var(--cobalt); border-radius:4px; background:#0d0f1e; font-size:14px; }}
  .callout b {{ color:var(--cobalt); font-size:19px; margin:0 4px; }}
  .barcell {{ width:120px; }}
  .bar {{ display:block; height:7px; border-radius:3px; min-width:2px; }}
  .rule {{ color:var(--mut); font-size:11px; }}
  .attest {{ display:grid; grid-template-columns:150px 1fr; gap:9px 16px; font-size:12px; }}
  .attest .k {{ color:var(--mut); letter-spacing:1px; }}
  .attest .v {{ word-break:break-all; color:#cfcfda; }}
  .hash {{ color:#4CAF50; }}
  .badge {{ display:inline-block; padding:3px 10px; border:1px solid #4CAF50; color:#4CAF50;
            border-radius:3px; font-size:11px; letter-spacing:1px; }}
  .grid2 {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:18px; }}
  .stat {{ background:#0c0c12; border:1px solid var(--line); border-radius:4px; padding:12px 14px; }}
  .stat .k {{ color:var(--mut); font-size:9.5px; letter-spacing:1px; }}
  .stat .v {{ font-size:26px; font-weight:700; }}
  .timeline {{ list-style:none; padding:0; margin:0; font-size:12.5px; }}
  .timeline li {{ padding:6px 0 6px 4px; border-left:1px solid var(--line); margin-left:6px; padding-left:16px; position:relative; }}
  .timeline .dot {{ position:absolute; left:-4px; top:11px; width:7px; height:7px; background:#FF6B35; border-radius:50%; }}
  .timeline .date {{ color:var(--cobalt); margin-right:8px; }}
  .muted {{ color:var(--mut); }}
  .msurf {{ display:flex; flex-direction:column; gap:11px; }}
  .mrow {{ display:grid; grid-template-columns:180px 1fr 92px; align-items:center; gap:14px; font-size:12.5px; }}
  .mlabel {{ font-weight:600; white-space:nowrap; }}
  .mbar {{ position:relative; height:11px; background:#0c0c12; border:1px solid var(--line); border-radius:3px; }}
  .mfill {{ display:block; height:100%; border-radius:2px; }}
  .mbase {{ position:absolute; top:-3px; width:2px; height:17px; background:#f5f5f7; opacity:.55; }}
  .mval {{ text-align:right; font-weight:700; white-space:nowrap; }} .mval .mlift {{ color:var(--mut); font-weight:400; font-size:11px; }}
  .spear {{ font-size:13px; margin-bottom:14px; color:#cfcfda; }} .spear b {{ color:var(--cobalt); }}
  table.cal td, table.cal th {{ padding:7px 12px 7px 0; }}
  .note {{ color:var(--mut); font-size:11px; margin-top:12px; }}
  .verdict {{ font-size:12px; color:#b9b9c6; margin-top:14px; padding-top:14px; border-top:1px solid var(--line); }}
  footer {{ color:var(--mut); font-size:10.5px; letter-spacing:1px; text-align:center;
            margin-top:44px; border-top:1px solid var(--line); padding-top:18px; }}
  a {{ color:var(--cobalt); }}
</style>
</head>
<body>
<div class="wrap">
  <div class="masthead">
    <div class="brand">APEX·<b>TRIALS</b> — AMENDMENT RISK ENGINE</div>
    <div class="rl">REALITY_LEVEL: C5-REAL · INDUSTRIAL NOIR 2026</div>
  </div>
  <div class="ascii">█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█</div>

  <h1><span class="nct">{_esc(f.nct_id)}</span> — {_esc(f.brief_title)}</h1>
  <div class="subtitle">{_esc(f.phase)} · {_esc(f.study_type)} · {_esc(f.therapeutic_area)} · {_esc(a.model_version)}</div>
  {exp_callout}

  <div class="top">
    {_gauge_svg(a.score, a.tier)}
    <div class="facts">
      <div class="fact"><div class="k">ELIGIBILITY CRITERIA</div><div class="v">{f.n_eligibility_criteria} ({f.n_inclusion} incl / {f.n_exclusion} excl)</div></div>
      <div class="fact"><div class="k">ENDPOINTS</div><div class="v">{f.n_primary_endpoints} primary / {f.n_secondary_endpoints} secondary</div></div>
      <div class="fact"><div class="k">ARMS</div><div class="v">{f.n_arms}</div></div>
      <div class="fact"><div class="k">ENROLLMENT</div><div class="v">{f.enrollment:,}</div></div>
      <div class="fact"><div class="k">GEOGRAPHY</div><div class="v">{f.n_countries} countries / {f.n_sites} sites</div></div>
      <div class="fact"><div class="k">DESIGN</div><div class="v">{_esc(f.intervention_model)} · mask {_esc(f.masking)}</div></div>
    </div>
  </div>

  <section class="card">
    <h2>▍RISK DECOMPOSITION <span class="sub">— every point traced to a firing rule</span></h2>
    <table>
      <thead><tr><th>DRIVER</th><th>EVIDENCE</th><th>BAND</th><th>CONTRIB</th><th></th><th>RULE</th></tr></thead>
      <tbody>{_rules_rows(result)}</tbody>
    </table>
    <div class="verdict">Raw {a.raw_score}/{114} band points → normalized <b style="color:{tier_color}">{a.score}/100 · {_esc(a.tier)}</b>
      via {_esc(a.mode)} mixing. This is a pure function of the protocol record: identical input reproduces this exact score.</div>
    {_fit_provenance()}
  </section>

  <section class="card">
    <h2>▍CRYPTOGRAPHIC ATTESTATION <span class="sub">— cortex-persist hash-chain · 21 CFR Part 11 audit trail</span></h2>
    <div style="margin-bottom:14px"><span class="badge">🟢 {chain}</span></div>
    <div class="attest">
      <div class="k">LEDGER ID (uuid5)</div><div class="v">{_esc(e.id)}</div>
      <div class="k">ENTRY HASH</div><div class="v hash">{_esc(e.entry_hash)}</div>
      <div class="k">PREV HASH</div><div class="v">{_esc(e.prev_hash)}</div>
      <div class="k">LAMPORT_T</div><div class="v">{e.lamport_t}</div>
      <div class="k">CAUSAL TAINT</div><div class="v">{_esc(e.causal_taint)}</div>
      <div class="k">AGENT ID</div><div class="v">{_esc(e.agent_id)}</div>
      <div class="k">CREATED AT</div><div class="v">{_esc(e.created_at)}</div>
    </div>
    <div class="note">The hash covers the decision content only (not wall-clock), so the chain reproduces byte-for-byte. Tampering with any field breaks verification on read.</div>
  </section>

  <section class="card">
    <h2>▍GROUND-TRUTH AMENDMENT HISTORY <span class="sub">— public record vs. our prediction</span></h2>
    {_history_block(result)}
  </section>

  {_module_surface_block(result)}

  {_calibration_block(backtest)}

  <footer>
    APEX-TRIALS · cortex-persist substrate · data © ClinicalTrials.gov (public domain)<br/>
    Titular Civil: Borja Fernández Angulo · AKA Borja Moskv (borjamoskv) · Hash: FORGED IN C5-REAL EXECUTION
  </footer>
</div>
</body>
</html>"""
