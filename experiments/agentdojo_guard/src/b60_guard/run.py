"""Campaign runner with strict budget gate, JSONL trace logging, and baseline support."""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SRC_DIR = Path(__file__).absolute().parents[1]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

import anthropic  # noqa: E402
import openai  # noqa: E402
from agentdojo.agent_pipeline.base_pipeline_element import BasePipelineElement  # noqa: E402
from agentdojo.attacks.attack_registry import load_attack  # noqa: E402
from agentdojo.task_suite.load_suites import get_suites  # noqa: E402
from google.genai import errors as genai_errors  # noqa: E402

from b60_guard.approver import OracleGroundTruthApprover  # noqa: E402
from b60_guard.contracts import GuardArm, GuardSession  # noqa: E402
from b60_guard.effects import extract_tool_specs, load_tool_effect_policy  # noqa: E402
from b60_guard.manifest import build_run_manifest, write_run_manifest  # noqa: E402
from b60_guard.openai_responses import (  # noqa: E402
    DEFAULT_REASONING_EFFORT,
    VALID_REASONING_EFFORTS,
    TokenUsageTracker,
    validate_reasoning_effort,
)
from b60_guard.pipeline import (  # noqa: E402
    build_baseline_pipeline,
    build_guarded_pipeline,
    register_attack_model_name,
    resolve_llm_element,
)
from b60_guard.planner import QuarantinedPlanner  # noqa: E402

BASELINE_DEFENSE_MAP: dict[str, str | None] = {
    "B1-tool_filter": "tool_filter",
    "B2-spotlighting": "spotlighting_with_delimiting",
    "B3-repeat_user_prompt": "repeat_user_prompt",
    "B4-transformers_pi_detector": "transformers_pi_detector",
}

GUARDED_ARMS = frozenset({"A0", "A1", "A2-strict", "A2c", "A2-noBroker", "A2-HITL", "C+", "C-"})
ALL_ARMS = tuple(sorted(GUARDED_ARMS | set(BASELINE_DEFENSE_MAP.keys())))
ARMS_WITH_PLANNER = frozenset({"A1", "A2-strict", "A2c", "A2-noBroker", "A2-HITL", "C-"})
ARMS_WITH_EXTRA_PRECALL = ARMS_WITH_PLANNER | frozenset({"B1-tool_filter"})

# Heuristic upper-band per-LLM-call USD cost solely for pre-flight budget gating (not billing).
# GPT-6.2 entries are calibrated for reasoning.effort="low" with prompt caching across multi-turn runs.
_HEURISTIC_COST_PER_CALL_USD: dict[str, float] = {
    "gpt-6.2-sol": 0.008,
    "gpt-6.2-astra": 0.032,
    "gpt-6-luna": 0.0005,
    "gpt-6.1-terra": 0.004,
    "gpt-6.1-sol": 0.008,
    "gpt-6-sol": 0.008,
    "gpt-6-astra": 0.040,
    "mini": 0.002,
    "flash": 0.002,
    "haiku": 0.004,
    "sonnet": 0.020,
    "gpt-4o-2024": 0.020,
    "opus": 0.080,
    "pro": 0.025,
    "local": 0.0,
    "vllm_parsed": 0.0,
}

_REASONING_EFFORT_COST_MULTIPLIER: dict[str, float] = {
    "low": 1.0,
    "medium": 1.75,
    "high": 2.5,
    "xhigh": 3.5,
    "max": 4.5,
}


@dataclass(frozen=True)
class PlannedCase:
    suite_name: str
    user_task_id: str
    injection_task_id: str | None


class FatalProviderAuthError(RuntimeError):
    """Raised on 401/403 or missing provider credentials to abort fail-closed."""


_SECRET_FRAGMENT_RE = re.compile(r"(sk-[A-Za-z0-9_\-\*]{4,}|AIza[A-Za-z0-9_\-]{4,})")


def _iter_exception_chain(exc: BaseException) -> list[BaseException]:
    seen: set[int] = set()
    chain: list[BaseException] = []
    cur: BaseException | None = exc
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        chain.append(cur)
        cur = cur.__cause__ or cur.__context__
    return chain


def _is_fatal_auth_error(exc: BaseException) -> bool:
    for cur in _iter_exception_chain(exc):
        if isinstance(
            cur,
            (
                openai.AuthenticationError,
                openai.PermissionDeniedError,
                anthropic.AuthenticationError,
                anthropic.PermissionDeniedError,
            ),
        ):
            return True
        if isinstance(cur, genai_errors.ClientError) and getattr(cur, "code", None) in (401, 403):
            return True
        if getattr(cur, "status_code", None) in (401, 403):
            return True
        if isinstance(cur, (openai.OpenAIError, anthropic.AnthropicError)) and "api_key" in str(cur).lower():
            return True
    return False


def _sanitize_auth_error(exc: BaseException) -> str:
    msg = _SECRET_FRAGMENT_RE.sub("<REDACTED>", str(exc))
    return f"{type(exc).__name__}: {msg}"


def select_cases(
    *,
    suites: dict[str, Any],
    suite_names: Sequence[str],
    attack_name: str,
    user_tasks: Sequence[str] | None = None,
    injection_tasks: Sequence[str] | None = None,
    max_cases: int | None = None,
) -> list[PlannedCase]:
    """Select deterministic ordered evaluation cases across suites."""
    cases: list[PlannedCase] = []
    for sname in suite_names:
        suite = suites[sname]
        u_ids = list(user_tasks) if user_tasks else sorted(suite.user_tasks.keys())
        if attack_name == "none":
            for uid in u_ids:
                if uid in suite.user_tasks:
                    cases.append(PlannedCase(sname, uid, None))
        else:
            i_ids = list(injection_tasks) if injection_tasks else sorted(suite.injection_tasks.keys())
            for uid in u_ids:
                if uid not in suite.user_tasks:
                    continue
                for iid in i_ids:
                    if iid in suite.injection_tasks:
                        cases.append(PlannedCase(sname, uid, iid))
    if max_cases is not None:
        return cases[: max(0, max_cases)]
    return cases


def estimate_run_budget(
    *,
    arm: str,
    model: str,
    provider: str | None,
    n_cases: int,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
) -> dict[str, Any]:
    """Produce a pre-flight call-count and cost band estimate (heuristic, never billing)."""
    validate_reasoning_effort(reasoning_effort)
    if provider in ("local", "vllm_parsed") or model in ("local", "vllm_parsed", "dry-run"):
        per_call_usd = 0.0
    else:
        lower = model.lower()
        per_call_usd = 0.025
        for hint, rate in _HEURISTIC_COST_PER_CALL_USD.items():
            if hint in lower:
                per_call_usd = rate
                break
        if provider == "openai-responses" or lower.startswith("gpt-6"):
            per_call_usd = round(per_call_usd * _REASONING_EFFORT_COST_MULTIPLIER[reasoning_effort], 6)

    pre_calls = 1 if arm in ARMS_WITH_EXTRA_PRECALL else 0
    avg_executor_turns = 4
    est_calls = n_cases * (avg_executor_turns + pre_calls)
    return {
        "estimate_heuristic_only": True,
        "cases": n_cases,
        "estimated_llm_calls": est_calls,
        "estimated_cost_usd": round(est_calls * per_call_usd, 4),
        "heuristic_usd_per_call": per_call_usd,
        "reasoning_effort": reasoning_effort,
    }


def _collect_usage_tracker(elem: Any, sink: list[TokenUsageTracker]) -> None:
    tracker = getattr(elem, "usage_tracker", None)
    if isinstance(tracker, TokenUsageTracker) and not any(t is tracker for t in sink):
        sink.append(tracker)


def _build_case_pipeline(
    *,
    arm: str,
    suite_name: str,
    model: str,
    provider: str | None,
    model_id: str | None,
    executor_llm_factory: Callable[[], BasePipelineElement] | None,
    planner_llm_factory: Callable[[], BasePipelineElement] | None,
    policy: Any,
    session_sink: list[GuardSession],
    approver_factory: Any = None,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    usage_tracker: TokenUsageTracker | None = None,
    trackers_sink: list[TokenUsageTracker] | None = None,
) -> Any:
    if arm in BASELINE_DEFENSE_MAP:
        defense = BASELINE_DEFENSE_MAP[arm]
        if executor_llm_factory is not None:
            llm_elem = executor_llm_factory()
            if trackers_sink is not None:
                _collect_usage_tracker(llm_elem, trackers_sink)
            return build_baseline_pipeline(llm=llm_elem, defense=defense, model_name=model)
        llm_elem, canonical_model = resolve_llm_element(
            model=model,
            provider=provider,
            model_id=model_id,
            reasoning_effort=reasoning_effort,
            usage_tracker=usage_tracker,
        )
        if trackers_sink is not None:
            _collect_usage_tracker(llm_elem, trackers_sink)
        return build_baseline_pipeline(llm=llm_elem, defense=defense, model_name=canonical_model)

    if executor_llm_factory is not None:
        exec_llm = executor_llm_factory()
        plan_llm = planner_llm_factory() if planner_llm_factory is not None else executor_llm_factory()
        canonical_model = model
    else:
        exec_llm, canonical_model = resolve_llm_element(
            model=model,
            provider=provider,
            model_id=model_id,
            reasoning_effort=reasoning_effort,
            usage_tracker=usage_tracker,
        )
        plan_llm, _ = resolve_llm_element(
            model=model,
            provider=provider,
            model_id=model_id,
            reasoning_effort=reasoning_effort,
            usage_tracker=usage_tracker,
        )

    if trackers_sink is not None:
        _collect_usage_tracker(exec_llm, trackers_sink)
        _collect_usage_tracker(plan_llm, trackers_sink)

    planner = QuarantinedPlanner(plan_llm) if arm in ARMS_WITH_PLANNER else None
    guard_arm: GuardArm = arm  # type: ignore[assignment]
    return build_guarded_pipeline(
        arm=guard_arm,
        suite_name=suite_name,
        executor_llm=exec_llm,
        planner=planner,
        policy=policy,
        model_name=canonical_model,
        approver_factory=approver_factory,
        session_sink=session_sink,
    )


def run_campaign(
    *,
    arm: str,
    suite_names: Sequence[str],
    model: str,
    attack_name: str,
    output_dir: Path,
    run_id: str,
    provider: str | None = None,
    model_id: str | None = None,
    reasoning_effort: str = DEFAULT_REASONING_EFFORT,
    user_tasks: Sequence[str] | None = None,
    injection_tasks: Sequence[str] | None = None,
    max_cases: int | None = None,
    allow_dirty: bool = False,
    confirm_budget_usd: float | None = None,
    executor_llm_factory: Callable[[], BasePipelineElement] | None = None,
    planner_llm_factory: Callable[[], BasePipelineElement] | None = None,
    benchmark_version: str = "v1.2.2",
) -> tuple[Path, Path]:
    """Execute selected cases and emit ``<run_id>.manifest.json`` + ``<run_id>.jsonl``."""
    if arm not in ALL_ARMS:
        raise ValueError(f"Unsupported arm {arm!r}; valid={ALL_ARMS}")
    validate_reasoning_effort(reasoning_effort)

    policy = load_tool_effect_policy()
    suites = get_suites(benchmark_version)
    cases = select_cases(
        suites=suites,
        suite_names=suite_names,
        attack_name=attack_name,
        user_tasks=user_tasks,
        injection_tasks=injection_tasks,
        max_cases=max_cases,
    )
    budget = estimate_run_budget(
        arm=arm,
        model=model,
        provider=provider,
        n_cases=len(cases),
        reasoning_effort=reasoning_effort,
    )

    if executor_llm_factory is None:
        if confirm_budget_usd is None:
            raise SystemExit(
                f"Refusing live API execution without --confirm-budget-usd (estimated=${budget['estimated_cost_usd']})."
            )
        if budget["estimated_cost_usd"] > confirm_budget_usd:
            raise SystemExit(
                f"Estimated cost ${budget['estimated_cost_usd']} exceeds --confirm-budget-usd ${confirm_budget_usd}."
            )

    suite_label = ",".join(suite_names)
    manifest = build_run_manifest(
        arm=arm,
        suite=suite_label,
        model=model,
        attack=attack_name,
        allow_dirty=allow_dirty,
    )
    manifest["run_id"] = run_id
    manifest["provider"] = provider
    if provider == "openai-responses":
        manifest["reasoning_effort"] = reasoning_effort
    manifest["planned_cases"] = len(cases)
    manifest["budget_estimate"] = budget

    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / f"{run_id}.manifest.json"
    jsonl_path = output_dir / f"{run_id}.jsonl"
    write_run_manifest(manifest_path, manifest)

    attack_cache: dict[str, Any] = {}
    rows_written = 0
    try:
        with jsonl_path.open("w", encoding="utf-8") as fh:
            for case in cases:
                suite = suites[case.suite_name]
                user_task = suite.get_user_task_by_id(case.user_task_id)
                inj_task = suite.get_injection_task_by_id(case.injection_task_id) if case.injection_task_id else None
                sessions: list[GuardSession] = []

                approver_factory = None
                injections: dict[str, str] = {}

                if arm == "A2-HITL":
                    specs = extract_tool_specs(case.suite_name, {t.name: t for t in suite.tools}, policy)
                    pre_base = suite.load_and_inject_default_environment({})
                    pre_task_env = user_task.init_environment(pre_base)

                    def _make_hitl(
                        mint_cb: Any,
                        _ut: Any = user_task,
                        _pe: Any = pre_task_env,
                        _sp: Any = specs,
                    ) -> OracleGroundTruthApprover:
                        return OracleGroundTruthApprover(_ut, _pe, _sp, mint_cb)

                    approver_factory = _make_hitl

                case_tracker = TokenUsageTracker()
                trackers_sink: list[TokenUsageTracker] = []
                try:
                    pipeline = _build_case_pipeline(
                        arm=arm,
                        suite_name=case.suite_name,
                        model=model,
                        provider=provider,
                        model_id=model_id,
                        executor_llm_factory=executor_llm_factory,
                        planner_llm_factory=planner_llm_factory,
                        policy=policy,
                        session_sink=sessions,
                        approver_factory=approver_factory,
                        reasoning_effort=reasoning_effort,
                        usage_tracker=case_tracker,
                        trackers_sink=trackers_sink,
                    )
                except Exception as exc:
                    if _is_fatal_auth_error(exc):
                        raise FatalProviderAuthError(_sanitize_auth_error(exc)) from exc
                    raise

                if inj_task is not None:
                    if case.suite_name not in attack_cache:
                        register_attack_model_name(model)
                        attack_cache[case.suite_name] = load_attack(attack_name, suite, pipeline)
                    injections = attack_cache[case.suite_name].attack(user_task, inj_task)

                t0 = time.perf_counter()
                err_msg: str | None = None
                try:
                    utility, security = suite.run_task_with_pipeline(pipeline, user_task, inj_task, injections)
                except Exception as exc:
                    if _is_fatal_auth_error(exc):
                        raise FatalProviderAuthError(_sanitize_auth_error(exc)) from exc
                    utility = False
                    security = inj_task is not None
                    err_msg = f"{type(exc).__name__}: {exc}"
                wall_ms = round((time.perf_counter() - t0) * 1000.0, 2)

                case_usage = TokenUsageTracker()
                if trackers_sink:
                    for tracker in trackers_sink:
                        case_usage.merge(tracker)
                else:
                    case_usage.merge(case_tracker)

                sess = sessions[-1] if sessions else None
                exec_writes = [r for r in sess.records if r.kind == "write" and r.allowed] if sess else []
                with_receipt = [r for r in exec_writes if isinstance(r.evidence_id, bytes) and len(r.evidence_id) == 32]
                blocked = [r for r in sess.records if not r.allowed] if sess else []
                nested_denied = [r for r in sess.records if r.nested_call_denied] if sess else []
                hitl_reqs = [r for r in sess.records if r.hitl_requested] if sess else []
                hitl_grants = [r for r in sess.records if r.hitl_granted] if sess else []
                latencies_ns = [r.latency_ns for r in sess.records if r.kind == "write" and r.broker_used] if sess else []

                row = {
                    "run_id": run_id,
                    "arm": arm,
                    "model": model,
                    "suite": case.suite_name,
                    "attack": attack_name,
                    "user_task_id": case.user_task_id,
                    "injection_task_id": case.injection_task_id,
                    "utility": bool(utility),
                    "targeted_asr": bool(security) if inj_task is not None else False,
                    "executed_writes": len(exec_writes),
                    "writes_with_receipt": len(with_receipt),
                    "blocked_calls": len(blocked),
                    "nested_calls_denied": len(nested_denied),
                    "hitl_requests": len(hitl_reqs),
                    "hitl_grants": len(hitl_grants),
                    "broker_latencies_ns": latencies_ns,
                    "receipts_hex": [r.evidence_id.hex() for r in with_receipt if r.evidence_id],
                    "plan_stats": sess.plan_stats if sess else {},
                    "token_usage": case_usage.to_dict(),
                    "wall_time_ms": wall_ms,
                    "error": err_msg,
                }
                fh.write(json.dumps(row, sort_keys=True) + "\n")
                fh.flush()
                rows_written += 1
    except FatalProviderAuthError:
        if rows_written == 0:
            jsonl_path.unlink(missing_ok=True)
            manifest_path.unlink(missing_ok=True)
        raise

    return manifest_path, jsonl_path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="BABYLON GUARD P0 campaign runner")
    parser.add_argument("--arm", required=True, choices=ALL_ARMS)
    parser.add_argument("--suite", required=True, choices=("workspace", "travel", "banking", "slack", "all"))
    parser.add_argument("--model", required=True)
    parser.add_argument("--provider", default=None)
    parser.add_argument("--model-id", default=None)
    parser.add_argument(
        "--reasoning-effort",
        default=DEFAULT_REASONING_EFFORT,
        choices=VALID_REASONING_EFFORTS,
        help="Reasoning effort for OpenAI Responses API models (default: low)",
    )
    parser.add_argument("--attack", default="important_instructions")
    parser.add_argument("--user-tasks", default=None, help="Comma-separated user task IDs")
    parser.add_argument("--injection-tasks", default=None, help="Comma-separated injection task IDs")
    parser.add_argument("--max-cases", type=int, default=None)
    parser.add_argument("--output-dir", type=Path, default=Path("results"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Emit manifest and budget estimate without calling any LLM API",
    )
    parser.add_argument(
        "--confirm-budget-usd",
        type=float,
        default=None,
        help="Explicit API spend ceiling for live runs",
    )
    parser.add_argument("--allow-dirty", action="store_true")
    args = parser.parse_args(argv)

    suite_names = ["workspace", "travel", "banking", "slack"] if args.suite == "all" else [args.suite]
    u_tasks = [x.strip() for x in args.user_tasks.split(",") if x.strip()] if args.user_tasks else None
    i_tasks = [x.strip() for x in args.injection_tasks.split(",") if x.strip()] if args.injection_tasks else None

    if args.dry_run:
        suites = get_suites("v1.2.2")
        cases = select_cases(
            suites=suites,
            suite_names=suite_names,
            attack_name=args.attack,
            user_tasks=u_tasks,
            injection_tasks=i_tasks,
            max_cases=args.max_cases,
        )
        manifest = build_run_manifest(
            arm=args.arm,
            suite=",".join(suite_names),
            model=args.model,
            attack=args.attack,
            allow_dirty=args.allow_dirty,
        )
        manifest["provider"] = args.provider
        if args.provider == "openai-responses":
            manifest["reasoning_effort"] = args.reasoning_effort
        budget = estimate_run_budget(
            arm=args.arm,
            model=args.model,
            provider=args.provider,
            n_cases=len(cases),
            reasoning_effort=args.reasoning_effort,
        )
        payload = {
            **manifest,
            "budget_estimate": budget,
            "preview_cases": [f"{c.suite_name}:{c.user_task_id}:{c.injection_task_id}" for c in cases[:10]],
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
        return 0

    run_id = args.run_id or f"{args.arm}_{args.suite}_{args.attack}_{int(time.time())}"
    try:
        manifest_path, jsonl_path = run_campaign(
            arm=args.arm,
            suite_names=suite_names,
            model=args.model,
            provider=args.provider,
            model_id=args.model_id,
            reasoning_effort=args.reasoning_effort,
            attack_name=args.attack,
            output_dir=args.output_dir,
            run_id=run_id,
            user_tasks=u_tasks,
            injection_tasks=i_tasks,
            max_cases=args.max_cases,
            allow_dirty=args.allow_dirty,
            confirm_budget_usd=args.confirm_budget_usd,
        )
    except FatalProviderAuthError as exc:
        print(f"FATAL_AUTH_ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"manifest": str(manifest_path), "results": str(jsonl_path)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
