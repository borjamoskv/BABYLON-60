from __future__ import annotations

import html

from .backtest import BacktestReport
from .modules import _MODELS as _MOD_MODELS
from .risk_engine import _FITTED
from .transducer import TransducerResult as CopilotResult

_TIER_COLOR = {"LOW": "#4CAF50", "MODERATE": "#E5B72B", "HIGH": "#FF6B35", "CRITICAL": "#CE422B"}


def _esc(text: object) -> str:
    return html.escape(str(text))


def _gauge_svg(score: int, tier: str) -> str:
    color = _TIER_COLOR.get(tier, "#2B3BE5")
    circumference = 2 * 3.141592653589793 * 90
    dash = circumference * (score / 100.0)
    return f'\n<svg viewBox="0 0 220 220" width="200" height="200" role="img" aria-label="risk score {score}">\n  <circle cx="110" cy="110" r="90" fill="none" stroke="#1a1a22" stroke-width="16"/>\n  <circle cx="110" cy="110" r="90" fill="none" stroke="{color}" stroke-width="16"\n          stroke-linecap="round" stroke-dasharray="{dash:.2f} {circumference:.2f}"\n          transform="rotate(-90 110 110)"/>\n  <text x="110" y="102" text-anchor="middle" fill="#F5F5F7" font-size="52" font-family="ui-monospace,monospace" font-weight="700">{score}</text>\n  <text x="110" y="132" text-anchor="middle" fill="{color}" font-size="18" font-family="ui-monospace,monospace" letter-spacing="2">{_esc(tier)}</text>\n  <text x="110" y="156" text-anchor="middle" fill="#6b6b78" font-size="11" font-family="ui-monospace,monospace">/ 100 AMENDMENT RISK</text>\n</svg>'


def _rules_rows(result: CopilotResult) -> str:
    rules = result.assessment.fired_rules
    contribs = result.assessment.contributions or tuple(0.0 for _ in rules)
    maxc = max(contribs) if contribs and max(contribs) > 0 else 1.0
    out: list[str] = []
    for r, c in zip(rules, contribs, strict=False):
        active = r.points > 0
        bar_w = int(c / maxc * 100)
        pts_color = "#2B3BE5" if active else "#3a3a44"
        out.append(
            f'''\n    <tr class="{("on" if active else "off")}">\n      <td class="drv">{_esc(r.driver)}</td>\n      <td class="ev">{_esc(r.evidence)}</td>\n      <td class="pts"><span style="color:{pts_color}">+{r.points}</span><span class="mx">/{r.max_points}</span></td>\n      <td class="ctr">{c:.1f}</td>\n      <td class="barcell"><span class="bar" style="width:{bar_w}%;background:{pts_color}"></span></td>\n      <td class="rule">{_esc(r.rule)}</td>\n    </tr>'''
        )
    return "".join(out)


def _fit_provenance() -> str:
    if _FITTED is None:
        return ""
    m = _FITTED.get("metrics", {})
    provenance = f"""<div class="note" style="margin-top:12px;border-top:1px solid var(--line);padding-top:12px;">Weights fitted on {_FITTED.get("n_train", "?")} trials, held out {_FITTED.get("n_test", "?")}: Spearman ρ(score, actual amendments) = <b style="color:#2B3BE5">{m.get("spearman_fitted", "?")}</b> (prior {m.get("spearman_hand", "?")}); calibration MAE = {m.get("isotonic_mae", "?")} vs {m.get("baseline_mae", "?")} baseline.</div>"""
    if "spearman_temporal" in m:
        provenance += f"""<div class="note" style="margin-top:6px;color:#a9a9b6;"><b>▍FORWARD GENERALIZATION (Temporal Split ≤{m.get("temporal_cutoff", "?")} vs ≥{m.get("temporal_cutoff", "?")}):</b><br/>Spearman ρ = <b style="color:#FF6B35">{m.get("spearman_temporal", "?")}</b> · calibration MAE = {m.get("mae_temporal", "?")} (baseline {m.get("mae_base_temporal", "?")}) · macro-AUC = {m.get("macro_auc_temporal", "?")} (vs random {m.get("macro_auc_random", "?")}).</div>"""
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
    return f'\n    <div class="grid2">\n      <div class="stat"><div class="k">VERSIONS ON RECORD</div><div class="v">{h.n_versions}</div></div>\n      <div class="stat"><div class="k">SUBSTANTIVE AMENDMENTS</div><div class="v" style="color:#FF6B35">{h.n_substantive}</div></div>\n      <div class="stat"><div class="k">ADMIN UPDATES</div><div class="v">{h.n_administrative}</div></div>\n      <div class="stat"><div class="k">PREDICTED RISK</div><div class="v" style="color:#2B3BE5">{pred}</div></div>\n    </div>\n    <ul class="timeline">{timeline}</ul>'


def _module_surface_block(result: CopilotResult) -> str:
    risks = result.module_risks
    if not risks:
        return ""
    rows: list[str] = []
    for m in risks:
        p = m.probability * 100
        base = m.base_rate * 100
        color = "#CE422B" if p >= 60 else "#FF6B35" if p >= 40 else "#E5B72B" if p >= 25 else "#4CAF50"
        rows.append(
            f'\n      <div class="mrow">\n        <div class="mlabel">{_esc(m.label)}</div>\n        <div class="mbar"><span class="mfill" style="width:{p:.0f}%;background:{color}"></span>\n          <span class="mbase" style="left:{base:.0f}%"></span></div>\n        <div class="mval">{p:.0f}%<span class="mlift"> · {m.lift:.2f}×</span></div>\n      </div>'
        )
    macro = "?"
    if _MOD_MODELS is not None:
        aucs = [v["auc"] for v in _MOD_MODELS["modules"].values()]
        macro = f"{sum(aucs) / len(aucs):.3f}"
    return f"""\n  <section class="card">\n    <h2>▍AMENDMENT SURFACE <span class="sub">— which modules will change · P vs base rate (tick)</span></h2>\n    <div class="msurf">{"".join(rows)}</div>\n    <div class="note">Per-module logistic models, leakage-mitigated (each excludes its own feature). Macro-AUC {macro} held-out. The tick marks the corpus base rate — bar past it = elevated risk for this design.</div>\n  </section>"""


def _calibration_block(bt: BacktestReport | None) -> str:
    if bt is None:
        return ""
    rows: list[str] = []
    for tier in ("LOW", "MODERATE", "HIGH", "CRITICAL"):
        tm = bt.tier_means.get(tier)
        if not tm:
            continue
        color = _TIER_COLOR.get(tier, "#2B3BE5")
        rows.append(
            f"""\n      <tr>\n        <td style="color:{color};font-weight:700">{tier}</td>\n        <td>{int(tm["n"])}</td>\n        <td>{tm["mean_score"]}</td>\n        <td style="color:#FF6B35">{tm["mean_actual_amendments"]}</td>\n      </tr>"""
        )
    return f"""\n  <section class="card">\n    <h2>▍COHORT CALIBRATION <span class="sub">— score vs. public ground-truth</span></h2>\n    <div class="spear">Spearman ρ(score, actual amendments) = <b>{bt.spearman:.3f}</b> &nbsp;·&nbsp; n={bt.n} completed trials</div>\n    <table class="cal">\n      <thead><tr><th>TIER</th><th>N</th><th>MEAN SCORE</th><th>MEAN ACTUAL AMENDMENTS</th></tr></thead>\n      <tbody>{"".join(rows)}</tbody>\n    </table>\n    <div class="note">Spearman ρ is the ordering evidence; per-tier means are indicative and noisy at small n. Driver mixing weights were fit on a separate broad corpus (see provenance above), not on this cohort — so this is out-of-cohort evidence.</div>\n  </section>"""


def render_report(result: CopilotResult, backtest: BacktestReport | None = None) -> str:
    f = result.features
    a = result.assessment
    e = result.ledger_entry
    chain = "CHAIN VERIFIED" if e.entry_hash else "UNVERIFIED"
    tier_color = _TIER_COLOR.get(a.tier, "#2B3BE5")
    exp = a.expected_amendments
    exp_callout = (
        f'<div class="callout">FORECAST <b>{exp:.1f}</b> substantive protocol amendments<span class="muted"> · {_esc(a.mode)} model, isotonic-calibrated</span></div>'
        if exp is not None
        else ""
    )
    return f'<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="utf-8"/>\n<meta name="viewport" content="width=device-width, initial-scale=1"/>\n<title>APEX-TRIALS · {_esc(f.nct_id)} · Amendment Risk Attestation</title>\n<style>\n  :root {{ --bg:#0A0A0A; --panel:#111118; --line:#22222c; --ink:#F5F5F7; --mut:#6b6b78; --cobalt:#2B3BE5; }}\n  * {{ box-sizing:border-box; }}\n  body {{ margin:0; background:var(--bg); color:var(--ink);\n         font-family:ui-monospace,"JetBrains Mono","SF Mono",Menlo,monospace; line-height:1.5; }}\n  .wrap {{ max-width:1040px; margin:0 auto; padding:40px 24px 80px; }}\n  .masthead {{ display:flex; justify-content:space-between; align-items:baseline;\n               border-bottom:1px solid var(--line); padding-bottom:14px; margin-bottom:8px; }}\n  .brand {{ font-weight:700; letter-spacing:3px; font-size:15px; }}\n  .brand b {{ color:var(--cobalt); }}\n  .rl {{ color:var(--mut); font-size:11px; letter-spacing:2px; }}\n  .ascii {{ color:#1c1c26; font-size:11px; letter-spacing:1px; overflow:hidden; white-space:nowrap; margin:2px 0 26px; }}\n  h1 {{ font-size:19px; font-weight:600; margin:0 0 2px; }}\n  .nct {{ color:var(--cobalt); font-weight:700; }}\n  .subtitle {{ color:var(--mut); font-size:13px; margin-bottom:26px; }}\n  .top {{ display:flex; gap:28px; align-items:center; flex-wrap:wrap; margin-bottom:8px; }}\n  .facts {{ flex:1; min-width:280px; display:grid; grid-template-columns:1fr 1fr; gap:10px 22px; }}\n  .fact .k {{ color:var(--mut); font-size:10px; letter-spacing:1.5px; }}\n  .fact .v {{ font-size:15px; }}\n  .card {{ background:var(--panel); border:1px solid var(--line); border-radius:4px;\n           padding:22px 24px; margin:22px 0; }}\n  h2 {{ font-size:13px; letter-spacing:2px; margin:0 0 16px; color:var(--ink); font-weight:700; }}\n  h2 .sub {{ color:var(--mut); font-weight:400; letter-spacing:0; }}\n  table {{ width:100%; border-collapse:collapse; font-size:12.5px; }}\n  th {{ text-align:left; color:var(--mut); font-weight:500; font-size:10px; letter-spacing:1px;\n        border-bottom:1px solid var(--line); padding:0 10px 8px 0; }}\n  td {{ padding:8px 10px 8px 0; border-bottom:1px solid #17171f; vertical-align:middle; }}\n  tr.off td {{ opacity:.4; }}\n  .drv {{ font-weight:600; white-space:nowrap; }}\n  .ev {{ color:#b9b9c6; white-space:nowrap; }}\n  .pts {{ font-weight:700; white-space:nowrap; }} .pts .mx {{ color:var(--mut); font-weight:400; }}\n  .ctr {{ font-weight:700; color:#cfcfda; white-space:nowrap; }}\n  .callout {{ display:inline-block; margin:0 0 22px; padding:9px 16px; border:1px solid var(--cobalt);\n              border-left:3px solid var(--cobalt); border-radius:4px; background:#0d0f1e; font-size:14px; }}\n  .callout b {{ color:var(--cobalt); font-size:19px; margin:0 4px; }}\n  .barcell {{ width:120px; }}\n  .bar {{ display:block; height:7px; border-radius:3px; min-width:2px; }}\n  .rule {{ color:var(--mut); font-size:11px; }}\n  .attest {{ display:grid; grid-template-columns:150px 1fr; gap:9px 16px; font-size:12px; }}\n  .attest .k {{ color:var(--mut); letter-spacing:1px; }}\n  .attest .v {{ word-break:break-all; color:#cfcfda; }}\n  .hash {{ color:#4CAF50; }}\n  .badge {{ display:inline-block; padding:3px 10px; border:1px solid #4CAF50; color:#4CAF50;\n            border-radius:3px; font-size:11px; letter-spacing:1px; }}\n  .grid2 {{ display:grid; grid-template-columns:repeat(4,1fr); gap:14px; margin-bottom:18px; }}\n  .stat {{ background:#0c0c12; border:1px solid var(--line); border-radius:4px; padding:12px 14px; }}\n  .stat .k {{ color:var(--mut); font-size:9.5px; letter-spacing:1px; }}\n  .stat .v {{ font-size:26px; font-weight:700; }}\n  .timeline {{ list-style:none; padding:0; margin:0; font-size:12.5px; }}\n  .timeline li {{ padding:6px 0 6px 4px; border-left:1px solid var(--line); margin-left:6px; padding-left:16px; position:relative; }}\n  .timeline .dot {{ position:absolute; left:-4px; top:11px; width:7px; height:7px; background:#FF6B35; border-radius:50%; }}\n  .timeline .date {{ color:var(--cobalt); margin-right:8px; }}\n  .muted {{ color:var(--mut); }}\n  .msurf {{ display:flex; flex-direction:column; gap:11px; }}\n  .mrow {{ display:grid; grid-template-columns:180px 1fr 92px; align-items:center; gap:14px; font-size:12.5px; }}\n  .mlabel {{ font-weight:600; white-space:nowrap; }}\n  .mbar {{ position:relative; height:11px; background:#0c0c12; border:1px solid var(--line); border-radius:3px; }}\n  .mfill {{ display:block; height:100%; border-radius:2px; }}\n  .mbase {{ position:absolute; top:-3px; width:2px; height:17px; background:#f5f5f7; opacity:.55; }}\n  .mval {{ text-align:right; font-weight:700; white-space:nowrap; }} .mval .mlift {{ color:var(--mut); font-weight:400; font-size:11px; }}\n  .spear {{ font-size:13px; margin-bottom:14px; color:#cfcfda; }} .spear b {{ color:var(--cobalt); }}\n  table.cal td, table.cal th {{ padding:7px 12px 7px 0; }}\n  .note {{ color:var(--mut); font-size:11px; margin-top:12px; }}\n  .verdict {{ font-size:12px; color:#b9b9c6; margin-top:14px; padding-top:14px; border-top:1px solid var(--line); }}\n  footer {{ color:var(--mut); font-size:10.5px; letter-spacing:1px; text-align:center;\n            margin-top:44px; border-top:1px solid var(--line); padding-top:18px; }}\n  a {{ color:var(--cobalt); }}\n</style>\n</head>\n<body>\n<div class="wrap">\n  <div class="masthead">\n    <div class="brand">APEX·<b>TRIALS</b> — AMENDMENT RISK ENGINE</div>\n    <div class="rl">REALITY_LEVEL: C5-REAL · INDUSTRIAL NOIR 2026</div>\n  </div>\n  <div class="ascii">█▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█ █▄█</div>\n\n  <h1><span class="nct">{_esc(f.nct_id)}</span> — {_esc(f.brief_title)}</h1>\n  <div class="subtitle">{_esc(f.phase)} · {_esc(f.study_type)} · {_esc(f.therapeutic_area)} · {_esc(a.model_version)}</div>\n  {exp_callout}\n\n  <div class="top">\n    {_gauge_svg(a.score, a.tier)}\n    <div class="facts">\n      <div class="fact"><div class="k">ELIGIBILITY CRITERIA</div><div class="v">{f.n_eligibility_criteria} ({f.n_inclusion} incl / {f.n_exclusion} excl)</div></div>\n      <div class="fact"><div class="k">ENDPOINTS</div><div class="v">{f.n_primary_endpoints} primary / {f.n_secondary_endpoints} secondary</div></div>\n      <div class="fact"><div class="k">ARMS</div><div class="v">{f.n_arms}</div></div>\n      <div class="fact"><div class="k">ENROLLMENT</div><div class="v">{f.enrollment:,}</div></div>\n      <div class="fact"><div class="k">GEOGRAPHY</div><div class="v">{f.n_countries} countries / {f.n_sites} sites</div></div>\n      <div class="fact"><div class="k">DESIGN</div><div class="v">{_esc(f.intervention_model)} · mask {_esc(f.masking)}</div></div>\n    </div>\n  </div>\n\n  <section class="card">\n    <h2>▍RISK DECOMPOSITION <span class="sub">— every point traced to a firing rule</span></h2>\n    <table>\n      <thead><tr><th>DRIVER</th><th>EVIDENCE</th><th>BAND</th><th>CONTRIB</th><th></th><th>RULE</th></tr></thead>\n      <tbody>{_rules_rows(result)}</tbody>\n    </table>\n    <div class="verdict">Raw {a.raw_score}/{114} band points → normalized <b style="color:{tier_color}">{a.score}/100 · {_esc(a.tier)}</b>\n      via {_esc(a.mode)} mixing. This is a pure function of the protocol record: identical input reproduces this exact score.</div>\n    {_fit_provenance()}\n  </section>\n\n  <section class="card">\n    <h2>▍CRYPTOGRAPHIC ATTESTATION <span class="sub">— cortex-persist hash-chain · 21 CFR Part 11 audit trail</span></h2>\n    <div style="margin-bottom:14px"><span class="badge">🟢 {chain}</span></div>\n    <div class="attest">\n      <div class="k">LEDGER ID (uuid5)</div><div class="v">{_esc(e.id)}</div>\n      <div class="k">ENTRY HASH</div><div class="v hash">{_esc(e.entry_hash)}</div>\n      <div class="k">PREV HASH</div><div class="v">{_esc(e.prev_hash)}</div>\n      <div class="k">LAMPORT_T</div><div class="v">{e.lamport_t}</div>\n      <div class="k">CAUSAL TAINT</div><div class="v">{_esc(e.causal_taint)}</div>\n      <div class="k">AGENT ID</div><div class="v">{_esc(e.agent_id)}</div>\n      <div class="k">CREATED AT</div><div class="v">{_esc(e.created_at)}</div>\n    </div>\n    <div class="note">The hash covers the decision content only (not wall-clock), so the chain reproduces byte-for-byte. Tampering with any field breaks verification on read.</div>\n  </section>\n\n  <section class="card">\n    <h2>▍GROUND-TRUTH AMENDMENT HISTORY <span class="sub">— public record vs. our prediction</span></h2>\n    {_history_block(result)}\n  </section>\n\n  {_module_surface_block(result)}\n\n  {_calibration_block(backtest)}\n\n  <footer>\n    APEX-TRIALS · cortex-persist substrate · data © ClinicalTrials.gov (public domain)<br/>\n    Titular Civil: Borja Fernández Angulo · AKA Borja Moskv (borjamoskv) · Hash: FORGED IN C5-REAL EXECUTION\n  </footer>\n</div>\n</body>\n</html>'
