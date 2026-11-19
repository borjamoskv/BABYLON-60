"""Run three bounded, real OpenAI -> typed projection -> MCP stdio experiments.

Only the synthetic note tool and public interface are sent to OpenAI. API keys
and model reasoning are not recorded. No retries; every vector has fresh state.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from importlib.metadata import version
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from typing import Any

import httpx

from babylon60.mcp.cortex_openai_adapter import CortexOpenAIAdapter, cortex_stdio_session


ROOT = Path(__file__).absolute().parents[2]
FIXTURE = ROOT / "tests/fixtures/cortex_openai_note_server.py"
VECTORS = json.loads((ROOT / "tests/fixtures/cortex_ptc_presence.json").read_text(encoding="utf-8"))
INTENTIONS = {
    "preserve": "Conserva la nota original sin modificarla. Llama a update_note una sola vez.",
    "clear": "Borra la nota: debe quedar null. Llama a update_note una sola vez.",
    "empty": 'Deja la nota como una cadena vacía, "". Llama a update_note una sola vez.',
}


def observation(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def error_evidence(error: BaseException) -> list[dict[str, Any]]:
    """Unwrap SDK task groups without logging messages, headers or credentials."""
    if isinstance(error, BaseExceptionGroup):
        return [item for child in error.exceptions for item in error_evidence(child)]
    item: dict[str, Any] = {"type": type(error).__name__}
    if isinstance(error, httpx.HTTPStatusError):
        item["status_code"] = error.response.status_code
        try:
            body = error.response.json().get("error", {})
            for field in ("type", "code"):
                value = body.get(field)
                if isinstance(value, str) and re.fullmatch(r"[a-z_]{1,80}", value):
                    item[f"api_error_{field}"] = value
        except (ValueError, AttributeError):
            pass
    return [item]


async def run_probe(model: str, output: Path) -> bool:
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    report: dict[str, Any] = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Real OpenAI Responses, production adapter, official MCP client, CORTEX stdio, synthetic note tool",
        "requested_model": model,
        "mcp_version": version("mcp"),
        "httpx_version": version("httpx"),
        "max_openai_requests": 3,
        "automatic_retries": 0,
        "store": False,
        "cases": [],
        "passed": False,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with tempfile.TemporaryDirectory(prefix="cortex-openai-presence-") as directory:
            for vector in VECTORS["tests"]:
                name = vector["description"]
                row: dict[str, Any] = {
                    "intent": name,
                    "expected_arguments": vector["expected_arguments"],
                    "expected_state": vector["expected_state"],
                    "passed": False,
                }
                report["cases"].append(row)
                for route in ("direct", "openai"):
                    path = Path(directory) / f"{name}-{route}.json"
                    async with cortex_stdio_session(
                        sys.executable,
                        [str(FIXTURE), "--observation", str(path)],
                        cwd=str(ROOT),
                        env={"PYTHONPATH": str(ROOT / "01_KISH_ENGINE")},
                    ) as session:
                        initial = observation(path)
                        assert initial["state"] == vector["initial_state"]
                        assert initial["received"] == []
                        success = False
                        try:
                            if route == "direct":
                                result = await session.call_tool("update_note", vector["data"])
                                success = not result.model_dump(by_alias=True)["isError"]
                            else:
                                adapter = await CortexOpenAIAdapter.discover(session, allowed_tools=["update_note"])
                                evidence = await adapter.request_function_call(
                                    api_key=api_key, model=model, prompt=INTENTIONS[name], tool_name="update_note"
                                )
                                row["openai_response"] = evidence
                                result_output = await adapter.execute_function_call(evidence["function_call"])
                                success = not json.loads(result_output["output"])["isError"]
                        finally:
                            row[route] = {
                                "initial_state": initial["state"],
                                **observation(path),
                                "response_ok": success,
                            }
                row["passed"] = (
                    all(
                        row[route]["response_ok"]
                        and row[route]["received"] == [vector["expected_arguments"]]
                        and row[route]["state"] == vector["expected_state"]
                        and not row[route]["has_openai_key"]
                        for route in ("direct", "openai")
                    )
                    and row["direct"]["pid"] != row["openai"]["pid"]
                )
                print(f"{name}: {'PASS' if row['passed'] else 'FAIL'}", flush=True)
                if not row["passed"]:
                    break
        report["passed"] = len(report["cases"]) == 3 and all(row["passed"] for row in report["cases"])
    except Exception as exc:
        # No exception repr/body: an HTTP or process exception may contain secrets.
        report["error_type"] = type(exc).__name__
        report["errors"] = error_evidence(exc)
        print(f"Probe stopped: {json.dumps(report['errors'])}", file=sys.stderr)
    finally:
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    return bool(report["passed"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", required=True, help="Authorize up to three billed API calls")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", "gpt-4.1-mini"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    return 0 if asyncio.run(run_probe(args.model, args.output)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
