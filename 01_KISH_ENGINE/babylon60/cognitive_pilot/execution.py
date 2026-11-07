"""Bounded agent loop using Babylon provider configuration and its OS validator.

The agent has only a public-test tool. Hidden tests run after final submission.
No agent-supplied source runs in the evaluator's Python process.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
import tempfile
import time
from typing import cast

import httpx

from .bank import cases, public_task
from .store import (
    COMMON,
    CONDITIONS,
    PilotError,
    canonical,
    decode,
    digest,
    integer,
    load,
    mapping,
    validate_config,
    write,
)


class IsolationUnavailable(PilotError):
    """No performance conclusion is possible without the OS boundary."""


def provider_error(exc: httpx.HTTPError) -> dict[str, object]:
    """Safe diagnostic fields: never retain exception text, request headers or body."""
    fields: dict[str, object] = {"provider_error_type": type(exc).__name__}
    if isinstance(exc, httpx.HTTPStatusError):
        fields["provider_http_status"] = exc.response.status_code
    return fields


def _observation(data: dict[str, object], usage: dict[str, object], call: int) -> dict[str, object]:
    result: dict[str, object] = {"call": call}
    for field in ("id", "model", "model_digest"):
        value = data.get(field)
        if (
            isinstance(value, str)
            and 1 <= len(value) <= 160
            and all(character.isascii() and (character.isalnum() or character in "._:/-") for character in value)
        ):
            result[field] = value
    result["usage"] = {
        key: usage[key]
        for key in ("prompt_tokens", "completion_tokens", "total_tokens")
        if type(usage.get(key)) is int and 0 <= cast(int, usage[key]) <= 10**8
    }
    return result


async def evaluate(source: str, tests: list[dict[str, object]], timeout: float = 10) -> dict[str, object]:
    from babylon60.kernel.mcp_deductive_engine import McpCandidateContract, McpToolParameter
    from babylon60.kernel.mcp_sandbox_validator import McpSandboxValidator
    from babylon60.kernel.mcp_scaffolder import McpCodeScaffolder

    if not isinstance(source, str) or len(source.encode()) > 24000:
        raise PilotError("Source must be a string of at most 24000 bytes")
    if not tests:
        raise PilotError("At least one test case is required")
    body = source + "\nreturn [solve(p) for p in batch['items']]"
    contract = McpCandidateContract(
        "cognitive_pilot",
        "solve_batch",
        "Isolated benchmark candidate",
        parameters=[McpToolParameter("batch", "object", "Input cases")],
        implementation_body=body,
    )
    with tempfile.TemporaryDirectory(prefix="cognitive_candidate_") as temporary:
        try:
            script = McpCodeScaffolder(temporary).scaffold_fastmcp_python(contract)
        except (ValueError, SyntaxError) as exc:
            return {
                "quality": 0.0,
                "passed": 0,
                "total": len(tests),
                "source_digest": digest(source),
                "error": f"Invalid candidate: {str(exc)[:180]}",
            }
        result = await asyncio.wait_for(
            McpSandboxValidator().execute_and_detonate_mcp(
                script,
                contract,
                {"batch": {"items": [t["input"] for t in tests]}},
                timeout_seconds=min(30.0, max(0.1, timeout)),
            ),
            timeout=min(30.0, max(0.1, timeout)) + 2,
        )
    if not result.get("is_valid"):
        code = result.get("error_code")
        if code == "OS_ISOLATION_UNAVAILABLE":
            raise IsolationUnavailable("Babylon OS-confinement probe failed; candidate was not admitted")
        return {"quality": 0.0, "passed": 0, "total": len(tests), "source_digest": digest(source), "error": str(code)}
    output = mapping(result.get("tool_output")).get("result")
    if not isinstance(output, list) or len(output) != len(tests):
        passed = 0
    else:
        try:
            passed = sum(canonical(actual) == canonical(test["expected"]) for actual, test in zip(output, tests))
        except PilotError:
            passed = 0
    return {
        "quality": 100 * passed / len(tests),
        "passed": passed,
        "total": len(tests),
        "source_digest": digest(source),
        "isolation_backend": result.get("isolation_backend"),
        "isolation_evidence": result.get("isolation_evidence"),
    }


def protocol() -> str:
    return (
        "You are a Babylon software agent in a fresh session. Output one JSON object per turn, no markdown. "
        "Tools: {action:'test',source:'def solve(p): ...'} tests public cases only. "
        "Final: {action:'final',source:'...',candidates:[{source:'...',mechanism:'short factual label'}],"
        "selected:0,memory:'concise reusable facts'}. Use at most 5 candidates; selected identifies the final "
        "candidate and its source must equal source. Outside exploration one candidate is sufficient. "
        "Never request file, network, shell or authority access. Do not output internal deliberations. "
        "Calls, tokens and wall time are bounded. A test call counts against the tool budget."
    )


class Provider:
    """Same explicit model/backend for both arms; no automatic retries or fallback."""

    def __init__(self, config: dict[str, object]) -> None:
        validate_config(config)
        self.config = config
        self.tokens = 0
        self.calls = 0
        self.observations: list[dict[str, object]] = []

    async def call(self, messages: list[dict[str, str]], timeout: float) -> dict[str, object]:
        remaining = int(cast(int, self.config["max_tokens"])) - self.tokens
        if remaining < 64:
            raise PilotError("Token budget exhausted")
        if self.config["backend"] in {"ollama_native", "ollama_structured_v3"}:
            from .ollama import native_completion

            return self._consume(await native_completion(self.config, messages, timeout, remaining))
        headers = {"Content-Type": "application/json"}
        if self.config["backend"] == "gemini_compat":
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                raise PilotError("GEMINI_API_KEY is required for the Gemini compatibility backend")
        else:
            from babylon60.kernel.swarm_orchestrator import InferenceBackend, SwarmConfig

            backend = InferenceBackend(str(self.config["backend"]))
            api_key = SwarmConfig(backend=backend).api_key
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        payload = {
            "model": self.config["model"],
            "temperature": self.config["temperature"],
            "messages": messages,
            "max_tokens": min(2048, remaining),
        }
        if self.config["backend"] == "gemini_compat":
            payload["reasoning_effort"] = self.config["reasoning_effort"]
            payload["response_format"] = {"type": "json_object"}
        # Usage is provider-reported. Missing usage makes the run unscorable;
        # the completion bound cannot independently bound prompt token usage.
        request_timeout = httpx.Timeout(
            timeout, connect=min(10.0, timeout), pool=min(10.0, timeout), write=min(10.0, timeout)
        )
        async with httpx.AsyncClient(timeout=request_timeout, follow_redirects=False, trust_env=False) as client:
            async with client.stream("POST", str(self.config["endpoint"]), headers=headers, json=payload) as response:
                response.raise_for_status()
                raw = bytearray()
                async for chunk in response.aiter_bytes():
                    raw.extend(chunk)
                    if len(raw) > 1024 * 1024:
                        raise PilotError("Provider output exceeds 1 MiB")
        return self._consume(decode(bytes(raw)))

    def _consume(self, data: dict[str, object]) -> dict[str, object]:
        self.calls += 1
        usage = mapping(data.get("usage"))
        self.tokens += integer(usage.get("total_tokens"), 1, 10**8, "provider total_tokens")
        self.observations.append(_observation(data, usage, self.calls))
        if self.tokens > int(cast(int, self.config["max_tokens"])):
            raise PilotError("Provider-reported token budget exceeded")
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise PilotError("Provider returned no choices")
        content = mapping(mapping(choices[0]).get("message")).get("content")
        if not isinstance(content, str):
            raise PilotError("Provider returned no content")
        return decode(content)


def final_artifact(action: dict[str, object], memory_bytes: int) -> dict[str, object]:
    if set(action) != {"action", "source", "candidates", "selected", "memory"} or action["action"] != "final":
        raise PilotError("Invalid final artifact fields")
    candidates = action["candidates"]
    if not isinstance(candidates, list) or not 1 <= len(candidates) <= 5:
        raise PilotError("Expected 1–5 executable candidates")
    for candidate in candidates:
        item = mapping(candidate)
        if set(item) != {"source", "mechanism"}:
            raise PilotError("Candidate fields must be source and mechanism")
        if not isinstance(item["source"], str) or len(str(item["source"]).encode()) > 24000:
            raise PilotError("Invalid source")
        if not isinstance(item["mechanism"], str) or not 1 <= len(str(item["mechanism"])) <= 160:
            raise PilotError("Expected short factual mechanism label")
    selected = integer(action["selected"], 0, len(candidates) - 1, "selected")
    if action["source"] != mapping(candidates[selected])["source"]:
        raise PilotError("Selected candidate/source mismatch")
    if not isinstance(action["memory"], str) or len(str(action["memory"]).encode()) > memory_bytes:
        raise PilotError("Persistent note exceeds frozen byte budget")
    return action


async def _activation_seconds(
    events: list[dict[str, object]],
    hidden: list[dict[str, object]],
    chosen: dict[str, object],
    submission_seconds: float,
) -> float | None:
    acceptable = []
    for event in events:
        checked = await evaluate(str(event["source"]), hidden)
        if float(cast(float, checked["quality"])) >= 70:
            acceptable.append(float(cast(float, event["submitted_at"])))
    if float(cast(float, chosen["quality"])) >= 70:
        acceptable.append(submission_seconds)
    return min(acceptable) if acceptable else None


async def run_one(directory: Path, plan: dict[str, object], run: dict[str, object]) -> dict[str, object]:
    frozen = load(directory)
    if canonical(plan) != canonical(frozen) or run not in cast(list[dict[str, object]], frozen["runs"]):
        raise PilotError("Run and plan must match the frozen scheduled experiment")
    config = mapping(plan["config"])
    run_id = str(run["id"])
    path = directory / "runs" / f"{run_id}.json"
    if path.exists():
        raise PilotError("Run already recorded; no silent reruns")
    name, stage, arm = str(run["family"]), str(run["stage"]), str(run["arm"])
    task = public_task(name, stage, int(cast(int, run["case_seed"])))
    note = ""
    parent_digest: str | None = None
    if stage == "retention":
        from .review import checked_record

        parent_run = next(
            item
            for item in cast(list[dict[str, object]], plan["runs"])
            if item["id"] == f"{name}.{run['repetition']}.quality.{arm}"
        )
        parent = checked_record(directory, plan, parent_run)
        if parent is None or parent.get("status") != "complete":
            raise PilotError("Retention requires a completed, same-arm quality run")
        parent_digest = digest(parent)
        note = str(mapping(parent["artifact"])["memory"])
    try:
        write(directory / "claims" / f"{run_id}.json", {"plan_digest": plan["plan_digest"], "run": run})
    except FileExistsError as exc:
        raise PilotError("Run attempt already recorded; no concurrent or silent reruns") from exc
    messages = [
        {"role": "system", "content": COMMON + "\n" + CONDITIONS[arm] + "\n" + protocol()},
        {"role": "user", "content": canonical(task).decode() + "\nPersistent note:\n" + note},
    ]
    started = time.monotonic()
    provider = Provider(config)
    events: list[dict[str, object]] = []
    record: dict[str, object] = {
        "run": run,
        "plan_digest": plan["plan_digest"],
        "status": "failed",
        "parent_digest": parent_digest,
        "events": events,
        "scope": "provider-reported usage; OS-confined candidates; no hardware attestation claim",
    }
    deadline = started + float(cast(float, config["timeout"]))
    cancellation: asyncio.CancelledError | None = None
    try:
        for _ in range(int(cast(int, config["max_calls"]))):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PilotError("Wall-time budget exhausted")
            action = await asyncio.wait_for(provider.call(messages, remaining), timeout=remaining)
            if action.get("action") == "final":
                record["artifact"] = final_artifact(action, int(cast(int, config["memory_bytes"])))
                record["submission_seconds"] = time.monotonic() - started
                # Hidden evaluation latency is not charged to agent activation.
                hidden = cases(name, stage, int(cast(int, run["case_seed"])), hidden=True)
                grades = [
                    await evaluate(str(mapping(c)["source"]), hidden) for c in cast(list[object], action["candidates"])
                ]
                record["grades"] = grades
                if stage == "activation":
                    chosen = grades[int(cast(int, action["selected"]))]
                    record["activation_seconds"] = await _activation_seconds(
                        events, hidden, chosen, float(cast(float, record["submission_seconds"]))
                    )
                record["status"] = "complete"
                break
            if set(action) != {"action", "source"} or action.get("action") != "test":
                raise PilotError("Invalid tool action")
            if not isinstance(action["source"], str):
                raise PilotError("Tool source must be a string")
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise PilotError("Wall-time budget exhausted")
            submitted_at = time.monotonic() - started
            grade = await asyncio.wait_for(
                evaluate(
                    str(action["source"]),
                    cast(list[dict[str, object]], task["public_cases"]),
                    timeout=min(10.0, remaining),
                ),
                timeout=remaining,
            )
            # Factual artifacts only: no raw response/reasoning trace is persisted.
            events.append(
                {
                    "elapsed": time.monotonic() - started,
                    "submitted_at": submitted_at,
                    "source": action["source"],
                    "kind": "public_test",
                    "grade": grade,
                }
            )
            messages.extend(
                [
                    {"role": "assistant", "content": canonical(action).decode()},
                    {"role": "user", "content": "Public test result: " + canonical(grade).decode()},
                ]
            )
        else:
            raise PilotError("Call budget exhausted before final submission")
    except IsolationUnavailable as exc:
        record.update({"status": "blocked", "error": str(exc)})
    except httpx.HTTPError as exc:
        record.update(
            {"status": "blocked", "error": "Provider request failed; no efficacy conclusion", **provider_error(exc)}
        )
    except (OSError, RuntimeError):
        record.update({"status": "blocked", "error": "Execution infrastructure failed; no efficacy conclusion"})
    except asyncio.CancelledError as exc:
        cancellation = exc
        record.update({"status": "blocked", "error": "Run cancelled; no efficacy conclusion"})
    except (ValueError, TypeError, RecursionError, OverflowError, asyncio.TimeoutError) as exc:
        record.update({"status": "failed", "error": type(exc).__name__ + ": " + str(exc)[:160]})
    record.update(
        {
            "tokens": provider.tokens,
            "calls": provider.calls,
            "elapsed": time.monotonic() - started,
            "provider_observations": provider.observations,
        }
    )
    # Save even failures. Replacing or discarding them would bias the comparison.
    record["record_digest"] = digest(record)
    write(path, record)
    if cancellation is not None:
        raise cancellation
    return record
