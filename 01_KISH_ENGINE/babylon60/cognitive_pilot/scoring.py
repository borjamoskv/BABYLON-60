"""Fixed 1–1000 index, paired effects, missingness bounds and family bootstrap."""

from __future__ import annotations

import math
from pathlib import Path
import random
import statistics
from typing import cast

from .bank import FAMILIES
from .review import checked_record, judgment
from .store import METRICS, TARGETS, WEIGHTS, PilotError, digest, mapping


Pair = tuple[float, float]
Blocks = dict[str, dict[str, list[Pair]]]


def index(fractions: list[float | None], domain: str) -> dict[str, object]:
    if len(fractions) != 6 or domain not in WEIGHTS:
        raise PilotError("Six fractions and a known domain are required")
    for value in fractions:
        if value is not None and (not math.isfinite(value) or not 0 <= value <= 1):
            raise PilotError("Fractions must be finite in [0,1] or missing")
    lower = sum(w * (p if p is not None else 0.0) for w, p in zip(WEIGHTS[domain], fractions))
    upper = sum(w * (p if p is not None else 1.0) for w, p in zip(WEIGHTS[domain], fractions))

    def convert(value: float) -> int:
        return math.floor(1 + 999 * value + 0.5)

    return {
        "score": convert(lower) if None not in fractions else None,
        "bounds": [convert(lower), convert(upper)],
        "coverage_weight": sum(w for w, p in zip(WEIGHTS[domain], fractions) if p is not None),
    }


def survival_median(observations: list[Pair]) -> float | None:
    """Kaplan–Meier median: pair=(observed time, event 0/1), ties before censoring."""
    at_risk = len(observations)
    survival = 1.0
    for elapsed in sorted({t for t, _ in observations}):
        events = sum(hit for t, hit in observations if t == elapsed)
        removed = sum(t == elapsed for t, _ in observations)
        survival *= 1 - events / at_risk
        if survival <= 0.5:
            return elapsed
        at_risk -= removed
    return None


def effects(blocks: Blocks, names: list[str]) -> list[float | None]:
    values: list[float | None] = []
    for metric in METRICS:
        pairs = [pair for name in names for pair in blocks[name][metric]]
        if not pairs or any(not blocks[name][metric] for name in names):
            values.append(None)
            continue
        if metric == "activation":
            # Each family stores [A event/censor, B event/censor] per repetition.
            a, b = survival_median(pairs[::2]), survival_median(pairs[1::2])
            values.append(None if a is None or b is None or a <= 0 else (a - b) / a)
        else:
            values.append(statistics.mean(b - a for a, b in pairs))
    return values


def fractions(raw: list[float | None]) -> list[float | None]:
    return [None if value is None else max(0.0, min(1.0, value / goal)) for value, goal in zip(raw, TARGETS)]


def quality(record: dict[str, object]) -> float:
    if record["status"] == "failed":
        return 0.0
    artifact = mapping(record["artifact"])
    grade = cast(list[dict[str, object]], record["grades"])[int(cast(int, artifact["selected"]))]
    return float(cast(float, grade["quality"]))


def report(directory: Path, plan: dict[str, object], bootstrap: int = 2000) -> dict[str, object]:
    if type(bootstrap) is not int or not 100 <= bootstrap <= 10000:
        raise PilotError("bootstrap must be an integer in [100,10000]")
    runs = cast(list[dict[str, object]], plan["runs"])
    records = {str(run["id"]): checked_record(directory, plan, run) for run in runs}
    pending: list[str] = []
    critical: list[str] = []
    blocks: Blocks = {f.name: {metric: [] for metric in METRICS} for f in FAMILIES}
    incomplete: set[tuple[str, str]] = set()
    config = mapping(plan["config"])
    for run in runs:
        if run["arm"] != "A":
            continue
        prefix = str(run["id"])[:-1]
        a, b = records[prefix + "A"], records[prefix + "B"]
        name, stage = str(run["family"]), str(run["stage"])
        metrics = ("generativity", "originality") if stage == "exploration" else (stage,)
        if a is None or b is None or a["status"] == "blocked" or b["status"] == "blocked":
            pending.append(prefix + "paired execution")
            incomplete.update((name, m) for m in metrics)
            continue
        if stage == "retention":
            for arm, record in (("A", a), ("B", b)):
                parent = records[f"{name}.{run['repetition']}.quality.{arm}"]
                if parent is None or record.get("parent_digest") != digest(parent):
                    raise PilotError("Retention memory lineage mismatch")
        if stage == "exploration":
            ratings = [
                judgment(directory, {**run, "id": prefix + arm, "arm": arm}, record)
                if record["status"] == "complete"
                else {"generativity": 0.0, "originality": 0.0, "critical": False}
                for arm, record in (("A", a), ("B", b))
            ]
            if None in ratings:
                pending.append(prefix + "three independent blind reviews per arm")
                incomplete.update((name, m) for m in metrics)
                continue
            first, second = cast(list[dict[str, object]], ratings)
            for metric in metrics:
                blocks[name][metric].append((float(cast(float, first[metric])), float(cast(float, second[metric]))))
            if first["critical"] or second["critical"]:
                critical.append(prefix + "reviewed critical violation")
        elif stage == "activation":
            for record in (a, b):
                elapsed = record.get("activation_seconds") if record["status"] == "complete" else None
                limit = float(cast(float, config["timeout"]))
                blocks[name][stage].append(
                    (limit if elapsed is None else float(cast(float, elapsed)), 0.0 if elapsed is None else 1.0)
                )
        else:
            blocks[name][stage].append((quality(a), quality(b)))
    # A partially observed metric is not silently averaged over successful pairs.
    for name, metric in incomplete:
        blocks[name][metric] = []
    domains: dict[str, object] = {}
    rng = random.Random(int(cast(int, plan["seed"])) + 1847)
    for domain in WEIGHTS:
        names = [f.name for f in FAMILIES if f.domain == domain]
        raw = effects(blocks, names)
        result = index(fractions(raw), domain)
        harms = [metric for metric, value in zip(METRICS[:2], raw[:2]) if value is not None and value <= -5]
        interval: list[int] | None = None
        samples: list[int] = []
        if result["score"] is not None:
            for _ in range(bootstrap):
                sample = [rng.choice(names) for _ in names]
                score = index(fractions(effects(blocks, sample)), domain)["score"]
                if score is not None:
                    samples.append(int(cast(int, score)))
            if len(samples) == bootstrap:
                samples.sort()
                interval = [samples[int(0.025 * (bootstrap - 1))], samples[int(0.975 * (bootstrap - 1))]]
        score = result["score"]
        if critical or harms:
            status = "critical_or_harmful"
        elif score is None or interval is None:
            status = "pending"
        elif interval[0] >= 900:
            status = "preliminary_support_900"
        elif interval[1] < 900:
            status = "does_not_support_900"
        elif int(cast(int, score)) >= 900:
            status = "promising_uncertain"
        else:
            status = "inconclusive"
        domains[domain] = {
            **result,
            "status": status,
            "effects": dict(zip(METRICS, raw)),
            "fractions": dict(zip(METRICS, fractions(raw))),
            "bootstrap_interval_95": interval,
            "bootstrap_complete_samples": len(samples),
            "harmful_metrics": harms,
            "independent_families": len(names),
        }
    return {
        "schema": "cognitive-pilot-report-v1",
        "plan_digest": plan["plan_digest"],
        "planned_runs": len(runs),
        "recorded_runs": sum(r is not None for r in records.values()),
        "completed_runs": sum(r is not None and r["status"] == "complete" for r in records.values()),
        "failed_runs": sum(r is not None and r["status"] == "failed" for r in records.values()),
        "blocked_runs": sum(r is not None and r["status"] == "blocked" for r in records.values()),
        "pending": pending,
        "critical": critical,
        "domains": domains,
        "limitations": [
            "Experimental software benchmark, not physical energy or general intelligence.",
            "Six independent families per domain; repeats are not independent tasks.",
            "Bootstrap is exploratory, conditional on this bank and the three reviewers.",
            "Usage and reviewer identities are declarations, not hardware attestations.",
            "Positive-gain index clips losses; inspect signed effects and harm flags.",
            "Hidden inputs are distinct from public inputs within a stage; stages may overlap.",
            "Transfer measures new draws from the same task family, not independent problem domains.",
            "Persistence is fresh-context reuse with a byte-bounded note, not a 30-day study.",
        ],
    }
