"""Explicit experiment CLI; never contact a provider during prepare, blind or report."""

from __future__ import annotations

import argparse
import asyncio
from pathlib import Path
from typing import cast

from . import execution, judging, review, scoring, store


def register(
    directory: Path, config: dict[str, object], seed: int, repetitions: int, token_cap: int
) -> dict[str, object]:
    """Freeze the total provider-reported token cap before any run claim exists."""
    store.integer(token_cap, 256, 100_000_000, "total_token_cap")
    plan = store.prepare(directory, config, seed, repetitions)
    registration: dict[str, object] = {
        "schema": {
            "ollama_native": "cognitive-pilot-execution-v2",
            "ollama_structured_v3": "cognitive-pilot-execution-v3",
        }.get(str(config["backend"]), "cognitive-pilot-execution-v1"),
        "plan_digest": plan["plan_digest"],
        "total_token_cap": token_cap,
        "parallelism": config.get("parallelism", 2),
        "scope": "Provider-reported usage, including prompts; not an independent tokenizer or monetary cap.",
    }
    registration["registration_digest"] = store.digest(registration)
    store.write(directory / "execution.json", registration)
    return plan


def registration(directory: Path, plan: dict[str, object]) -> dict[str, object]:
    value = store.read(directory / "execution.json")
    claimed = value.pop("registration_digest", None)
    if claimed != store.digest(value) or value.get("plan_digest") != plan["plan_digest"]:
        raise store.PilotError("Execution registration digest or plan mismatch")
    store.integer(value.get("total_token_cap"), 256, 100_000_000, "total_token_cap")
    parallelism = store.integer(value.get("parallelism"), 1, 2, "parallelism")
    if parallelism != store.mapping(plan["config"]).get("parallelism", 2):
        raise store.PilotError("Frozen execution parallelism differs from the plan")
    return value


async def run_batch(directory: Path, limit: int | None = None) -> dict[str, object]:
    """Resume only untouched scheduled runs, reserving full per-run budgets in pairs.

    An orphan claim has unknown provider usage and prevents automatic continuation.
    A blocked provider/executor stops new work after the current pair finishes.
    Failed model artifacts stay in the denominator. Retention waits for valid memory.
    """
    if limit is not None:
        store.integer(limit, 1, 12000, "limit")
    plan = store.load(directory)
    contract = registration(directory, plan)
    runs = cast(list[dict[str, object]], plan["runs"])
    records = {str(run["id"]): review.checked_record(directory, plan, run) for run in runs}
    for run in runs:
        if records[str(run["id"])] is None and (directory / "claims" / f"{run['id']}.json").exists():
            raise store.PilotError("Orphan claim has unknown usage; automatic retry or continuation refused")
    spent = sum(int(cast(int, record["tokens"])) for record in records.values() if record is not None)
    maximum = int(cast(int, store.mapping(plan["config"])["max_tokens"]))
    cap = int(cast(int, contract["total_token_cap"]))
    parallelism = int(cast(int, contract["parallelism"]))
    attempted = 0
    previously_blocked = any(record is not None and record["status"] == "blocked" for record in records.values())
    stop = "previously blocked run requires investigation" if previously_blocked else "no eligible runs"
    while not previously_blocked and (limit is None or attempted < limit):
        batch: list[dict[str, object]] = []
        for run in runs:
            if records[str(run["id"])] is not None:
                continue
            if run["stage"] == "retention":
                parent = records[f"{run['family']}.{run['repetition']}.quality.{run['arm']}"]
                if parent is None or parent["status"] != "complete":
                    continue
            if spent + maximum * (len(batch) + 1) > cap:
                stop = "total token reservation cap reached"
                break
            batch.append(run)
            if len(batch) == parallelism or (limit is not None and attempted + len(batch) == limit):
                break
        if not batch:
            break
        # return_exceptions ensures a sibling completes its durable receipt before propagating.
        results = await asyncio.gather(
            *(execution.run_one(directory, plan, run) for run in batch), return_exceptions=True
        )
        for result in results:
            if isinstance(result, BaseException):
                raise result
            records[str(store.mapping(result["run"])["id"])] = result
            spent += int(cast(int, result["tokens"]))
            attempted += 1
        if any(not isinstance(result, BaseException) and result["status"] == "blocked" for result in results):
            stop = "provider or executor blocked; no further work dispatched"
            break
        if spent > cap:
            stop = "provider-reported usage exceeded cap; no further work dispatched"
            break
    if limit is not None and attempted == limit and stop == "no eligible runs":
        stop = "requested run limit reached"
    return {
        "plan_digest": plan["plan_digest"],
        "attempted_now": attempted,
        "recorded_runs": sum(record is not None for record in records.values()),
        "provider_reported_tokens": spent,
        "total_token_cap": cap,
        "stop": stop,
        "scope": "No silent reruns; unknown orphan-claim usage blocks continuation.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare = commands.add_parser("prepare", help="Freeze a plan without provider calls")
    prepare.add_argument("directory", type=Path)
    prepare.add_argument("--config", type=Path, required=True)
    prepare.add_argument("--seed", type=int, default=42)
    prepare.add_argument("--repetitions", type=int, default=1)
    prepare.add_argument("--total-token-cap", type=int, required=True)
    run = commands.add_parser("run", help="Execute untouched scheduled runs, at most two concurrently")
    run.add_argument("directory", type=Path)
    run.add_argument("--limit", type=int)
    for name in ("blind", "report"):
        command = commands.add_parser(name)
        command.add_argument("directory", type=Path)
    judge_prepare = commands.add_parser("judge-prepare", help="Freeze AI judgment protocol before experiment attempts")
    judge_prepare.add_argument("directory", type=Path)
    judge_prepare.add_argument("--config", type=Path, required=True)
    judge_prepare.add_argument("--reviewer", action="append", required=True)
    judge_prepare.add_argument("--total-token-cap", type=int, required=True)
    judge_run = commands.add_parser("judge-run", help="Judge anonymous packets using fresh AI calls, two at a time")
    judge_run.add_argument("directory", type=Path)
    judge_run.add_argument("--limit", type=int)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            plan = register(args.directory, store.read(args.config), args.seed, args.repetitions, args.total_token_cap)
            result = {"plan_digest": plan["plan_digest"], "planned_runs": len(cast(list[object], plan["runs"]))}
        elif args.command == "run":
            result = asyncio.run(run_batch(args.directory, args.limit))
        elif args.command == "judge-prepare":
            frozen = judging.prepare_judging(
                args.directory, store.read(args.config), args.reviewer, args.total_token_cap
            )
            result = {"judging_digest": frozen["judging_digest"], "scope": frozen["scope"]}
        elif args.command == "judge-run":
            result = asyncio.run(judging.run_judging(args.directory, args.limit))
        else:
            plan = store.load(args.directory)
            result = (
                review.blind(args.directory, plan) if args.command == "blind" else scoring.report(args.directory, plan)
            )
        print(store.canonical(result).decode())
    except (store.PilotError, OSError) as exc:
        parser.exit(2, f"cognitive-pilot: {type(exc).__name__}: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
