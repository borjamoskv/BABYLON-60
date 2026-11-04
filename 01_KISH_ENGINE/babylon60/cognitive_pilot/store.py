"""Frozen plans and bounded, descriptor-read experiment artifacts."""

from __future__ import annotations

from contextlib import contextmanager
import json
import math
import os
from pathlib import Path
import random
import stat
import secrets
from typing import Iterator, cast

from blake3 import blake3

from .bank import FAMILIES, STAGES, cases, public_task


MAX_BYTES = 2 * 1024 * 1024
WEIGHTS = {"knowledge": (0.30, 0.25, 0.15, 0.05, 0.15, 0.10), "creativity": (0.20, 0.15, 0.25, 0.20, 0.10, 0.10)}
METRICS = ("quality", "transfer", "generativity", "originality", "activation", "retention")
TARGETS = (20.0, 20.0, 2.0, 1.0, 0.25, 20.0)
COMMON = "Apply Babylon authorization and isolation rules. Verify outcomes; do not fabricate evidence."
CONDITIONS = {
    "A": "Plan, implement, test and revise. Summarize relevant facts, consult examples, compare quality, utility "
    "and originality of alternatives, and retain a concise implementation summary for later reuse.",
    "B": "Use cognitive-exergy protocol: identify enabled capabilities; activation requirements; limits and "
    "counterexamples; variations and connections; select and develop alternatives; retain a reusable "
    "capability/requirements/limits/checks note for a fresh context.",
}
GEMINI_COMPAT_POLICY = {
    "protocol": "gemini-openai-compat-v1",
    "auth_environment": "GEMINI_API_KEY",
    "response_format": "json_object",
    "response_retention": "Parsed final artifact and provider-reported usage only; no reasoning trace.",
}
OLLAMA_NATIVE_POLICY = {
    "protocol": "ollama-native-v2",
    "stream": False,
    "think": False,
    "format": "json",
    "num_ctx": 8192,
    "max_num_predict": 2048,
    "keep_alive": "5m",
    "model_binding": "Match configured alias and manifest digest against GET /api/tags before every inference.",
    "credentials": "No credentials; exact IPv4 loopback endpoint only.",
    "response_retention": "Parsed final artifact, model metadata and numeric usage only; no thinking or raw body.",
}


def response_schema(contract: str) -> dict[str, object]:
    """Inline, disjoint transport shapes; semantic and byte checks stay in Python."""
    if contract == "judge":
        return {
            "type": "object",
            "properties": {
                "families": {"type": "array", "items": {"type": ["string", "null"]}, "minItems": 1, "maxItems": 5},
                "originality": {"type": "number"},
                "critical_violation": {"type": "boolean"},
                "evidence": {"type": "string", "minLength": 1, "maxLength": 800},
            },
            "required": ["families", "originality", "critical_violation", "evidence"],
            "additionalProperties": False,
        }
    if contract != "agent":
        raise PilotError("Unknown structured-response contract")
    test: dict[str, object] = {
        "type": "object",
        "properties": {"action": {"type": "string", "enum": ["test"]}, "source": {"type": "string"}},
        "required": ["action", "source"],
        "additionalProperties": False,
    }
    final: dict[str, object] = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["final"]},
            "source": {"type": "string"},
            "candidates": {
                "type": "array",
                "minItems": 1,
                "maxItems": 5,
                "items": {
                    "type": "object",
                    "properties": {
                        "source": {"type": "string"},
                        "mechanism": {"type": "string", "minLength": 1, "maxLength": 160},
                    },
                    "required": ["source", "mechanism"],
                    "additionalProperties": False,
                },
            },
            "selected": {"type": "integer", "minimum": 0, "maximum": 4},
            "memory": {"type": "string"},
        },
        "required": ["action", "source", "candidates", "selected", "memory"],
        "additionalProperties": False,
    }
    return {"oneOf": [test, final]}


def provider_policy(config: dict[str, object]) -> dict[str, object]:
    if config["backend"] == "ollama_structured_v3":
        return {
            **OLLAMA_NATIVE_POLICY,
            "protocol": "ollama-structured-v3",
            "format": response_schema(str(config["response_contract"])),
            "response_contract": config["response_contract"],
            "model_digest": config["model_digest"],
            "parallelism": config["parallelism"],
        }
    if config["backend"] == "ollama_native":
        return {**OLLAMA_NATIVE_POLICY, "model_digest": config["model_digest"], "parallelism": config["parallelism"]}
    return {**GEMINI_COMPAT_POLICY, "reasoning_effort": config["reasoning_effort"]}


class PilotError(ValueError):
    """Invalid, altered or incomplete experiment inputs."""


def canonical(value: object) -> bytes:
    try:
        _validate_json(value)
        return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    except (ValueError, TypeError, RecursionError, OverflowError, UnicodeError) as exc:
        raise PilotError("Artifact must contain bounded, finite JSON values") from exc


def digest(value: object) -> str:
    return blake3(canonical(value)).hexdigest()


def number(value: object, low: float, high: float, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise PilotError(f"{label}: expected finite number")
    if not low <= value <= high:
        raise PilotError(f"{label}: outside [{low},{high}]")
    if not math.isfinite(value):
        raise PilotError(f"{label}: expected finite number")
    return float(value)


def integer(value: object, low: int, high: int, label: str) -> int:
    if type(value) is not int:
        raise PilotError(f"{label}: expected integer")
    number(value, low, high, label)
    return value


def mapping(value: object) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(k, str) for k in value):
        raise PilotError("Expected JSON object")
    return cast(dict[str, object], value)


def _validate_json(value: object) -> None:
    pending = [(value, 0)]
    while pending:
        item, depth = pending.pop()
        if depth > 64:
            raise PilotError("JSON nesting exceeds 64 levels")
        if isinstance(item, dict):
            pending.extend((child, depth + 1) for child in mapping(item).values())
        elif isinstance(item, (list, tuple)):
            pending.extend((child, depth + 1) for child in item)
        elif isinstance(item, float) and not math.isfinite(item):
            raise PilotError("JSON numbers must be finite")


def _unique_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise PilotError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


@contextmanager
def _directory_fd(path: Path, *, create: bool = False) -> Iterator[int]:
    """Walk from the filesystem root using descriptors; never follow a symlink."""
    absolute = path.absolute()
    if ".." in absolute.parts:
        raise PilotError("Artifact paths must not contain parent traversal")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    fd = os.open(absolute.anchor, flags)
    try:
        for component in absolute.parts[1:]:
            if create:
                try:
                    os.mkdir(component, mode=0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            child = os.open(component, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd
    finally:
        os.close(fd)


def read(path: Path) -> dict[str, object]:
    with _directory_fd(path.parent) as parent:
        fd = os.open(path.name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW, dir_fd=parent)
    with os.fdopen(fd, "rb") as stream:
        if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
            raise PilotError("Artifact must be a regular file")
        raw = stream.read(MAX_BYTES + 1)
    return decode(raw)


def decode(raw: bytes | str) -> dict[str, object]:
    if len(raw) > MAX_BYTES:
        raise PilotError("Artifact exceeds 2 MiB")
    try:
        value = json.loads(
            raw,
            object_pairs_hook=_unique_pairs,
            parse_constant=lambda token: (_ for _ in ()).throw(PilotError(f"Nonfinite {token}")),
        )
    except (UnicodeError, ValueError, RecursionError) as exc:
        raise PilotError("Invalid JSON artifact") from exc
    _validate_json(value)
    return mapping(value)


def write(path: Path, value: object, *, replace: bool = False) -> None:
    data = canonical(value) + b"\n"
    if len(data) > MAX_BYTES:
        raise PilotError("Artifact exceeds 2 MiB")
    with _directory_fd(path.parent, create=True) as parent:
        temporary = ".receipt-" + secrets.token_hex(16)
        fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            if replace:
                os.replace(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent)
            else:
                # Publish complete, synced bytes without ever replacing an existing receipt.
                os.link(temporary, path.name, src_dir_fd=parent, dst_dir_fd=parent, follow_symlinks=False)
            os.fsync(parent)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent)
                os.fsync(parent)
            except FileNotFoundError:
                pass


def schedule(seed: int, repetitions: int) -> list[dict[str, object]]:
    rng = random.Random(seed)
    runs: list[dict[str, object]] = []
    blocks = [(f.name, repetition) for f in FAMILIES for repetition in range(repetitions)]
    rng.shuffle(blocks)
    for name, repetition in blocks:
        stages = list(STAGES[1:])
        rng.shuffle(stages)
        for stage in ["quality", *stages]:
            arms = ["A", "B"]
            rng.shuffle(arms)
            for arm in arms:
                runs.append(
                    {
                        "id": f"{name}.{repetition}.{stage}.{arm}",
                        "family": name,
                        "stage": stage,
                        "arm": arm,
                        "repetition": repetition,
                        "case_seed": seed + repetition,
                    }
                )
    return runs


def bank_digest(seed: int, repetitions: int) -> str:
    return digest(
        [
            {"public": public_task(f.name, s, seed + rep), "hidden": cases(f.name, s, seed + rep, hidden=True)}
            for f in FAMILIES
            for s in STAGES
            for rep in range(repetitions)
        ]
    )


def prepare(directory: Path, config: dict[str, object], seed: int = 42, repetitions: int = 3) -> dict[str, object]:
    integer(seed, 0, 2**31 - 1, "seed")
    integer(repetitions, 1, 10, "repetitions")
    validate_config(config)
    if config["backend"] == "ollama_structured_v3" and config["response_contract"] != "agent":
        raise PilotError("Experiment plans require the agent structured-response contract")
    directory = directory.absolute()
    if directory.exists():
        raise PilotError("Destination must not exist; refuse overwrite")
    # Runtime evidence does not belong inside the installed Python package.
    if Path(__file__).resolve().parents[1] in directory.resolve().parents:
        raise PilotError("Runtime output must be outside package sources")
    frozen: dict[str, object] = {
        "schema": {"ollama_native": "cognitive-pilot-v2", "ollama_structured_v3": "cognitive-pilot-v3"}.get(
            str(config["backend"]), "cognitive-pilot-v1"
        ),
        "seed": seed,
        "repetitions": repetitions,
        "config": config,
        "conditions": CONDITIONS,
        "common": COMMON,
        "weights": WEIGHTS,
        "targets": TARGETS,
        "bank_digest": bank_digest(seed, repetitions),
        "runs": schedule(seed, repetitions),
        "scope": "experimental software-agent benchmark; not physical exergy",
    }
    if config["backend"] in {"gemini_compat", "ollama_native", "ollama_structured_v3"}:
        frozen["provider_policy"] = provider_policy(config)
    frozen["plan_digest"] = digest(frozen)
    write(directory / "plan.json", frozen)
    return frozen


def load(directory: Path) -> dict[str, object]:
    plan = read(directory / "plan.json")
    claimed = plan.pop("plan_digest", None)
    if claimed != digest(plan):
        raise PilotError("Frozen plan digest mismatch")
    plan["plan_digest"] = claimed
    seed = integer(plan.get("seed"), 0, 2**31 - 1, "seed")
    repetitions = integer(plan.get("repetitions"), 1, 10, "repetitions")
    if plan.get("runs") != schedule(seed, repetitions):
        raise PilotError("Execution schedule mismatch")
    if plan.get("conditions") != CONDITIONS or plan.get("common") != COMMON:
        raise PilotError("Condition instructions changed")
    if plan.get("weights") != {k: list(v) for k, v in WEIGHTS.items()} or plan.get("targets") != list(TARGETS):
        raise PilotError("Scoring contract changed")
    current = bank_digest(seed, repetitions)
    if plan.get("bank_digest") != current:
        raise PilotError("Task bank changed since registration")
    validate_config(mapping(plan.get("config")))
    if mapping(plan["config"])["backend"] == "gemini_compat" and plan.get("provider_policy") != provider_policy(
        mapping(plan["config"])
    ):
        raise PilotError("Gemini provider policy changed since registration")
    if mapping(plan["config"])["backend"] == "ollama_native":
        if plan.get("schema") != "cognitive-pilot-v2" or plan.get("provider_policy") != provider_policy(
            mapping(plan["config"])
        ):
            raise PilotError("Ollama v2 provider policy changed since registration")
    if mapping(plan["config"])["backend"] == "ollama_structured_v3":
        if mapping(plan["config"])["response_contract"] != "agent":
            raise PilotError("Experiment plan has the wrong structured-response role")
        if plan.get("schema") != "cognitive-pilot-v3" or plan.get("provider_policy") != provider_policy(
            mapping(plan["config"])
        ):
            raise PilotError("Ollama v3 provider policy changed since registration")
    return plan


def validate_config(config: dict[str, object]) -> None:
    from urllib.parse import urlparse

    if not isinstance(config.get("backend"), str):
        raise PilotError("Backend must be an explicit name")
    expected = {
        "backend",
        "model",
        "endpoint",
        "max_tokens",
        "max_calls",
        "timeout",
        "temperature",
        "memory_bytes",
    }
    if config.get("backend") == "gemini_compat":
        expected.add("reasoning_effort")
    if config.get("backend") in {"ollama_native", "ollama_structured_v3"}:
        expected.update({"model_digest", "parallelism"})
    if config.get("backend") == "ollama_structured_v3":
        expected.add("response_contract")
    if set(config) != expected:
        raise PilotError("Config fields differ from the v1 contract")
    hosts = {
        "local_mlx": {"localhost", "127.0.0.1"},
        "local_vllm": {"localhost", "127.0.0.1"},
        "moonshot": {"api.moonshot.cn"},
        "openrouter": {"openrouter.ai"},
        "gemini_compat": {"generativelanguage.googleapis.com"},
        "ollama_native": {"127.0.0.1"},
        "ollama_structured_v3": {"127.0.0.1"},
    }
    backend = str(config["backend"])
    endpoint = urlparse(str(config["endpoint"]))
    if backend not in hosts or endpoint.hostname not in hosts[backend] or endpoint.username or endpoint.password:
        raise PilotError("Backend/endpoint host mismatch or embedded credentials")
    if endpoint.query or endpoint.fragment or endpoint.scheme not in {"http", "https"}:
        raise PilotError("Invalid endpoint")
    if (
        not backend.startswith("local_")
        and backend not in {"ollama_native", "ollama_structured_v3"}
        and endpoint.scheme != "https"
    ):
        raise PilotError("Remote backends require HTTPS")
    if backend == "gemini_compat" and str(config["endpoint"]) != (
        "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions"
    ):
        raise PilotError("Gemini compatibility requires the exact HTTPS chat-completions endpoint")
    if backend == "gemini_compat":
        effort = config["reasoning_effort"]
        if not isinstance(effort, str) or effort not in {"none", "minimal", "low", "medium", "high"}:
            raise PilotError("Choose an explicit Gemini reasoning effort")
        if effort == "none" and str(config["model"]) not in {"gemini-2.5-flash", "gemini-2.5-flash-lite"}:
            raise PilotError("Thinking cannot be disabled for this Gemini model")
    if backend in {"ollama_native", "ollama_structured_v3"}:
        if str(config["endpoint"]) != "http://127.0.0.1:11434/api/chat":
            raise PilotError("Ollama requires the exact IPv4 loopback native-chat endpoint")
        value = config["model_digest"]
        if (
            not isinstance(value, str)
            or len(value) != 64
            or any(character not in "0123456789abcdef" for character in value)
        ):
            raise PilotError("Ollama requires the exact lowercase SHA-256 manifest digest from /api/tags")
        integer(config["parallelism"], 1, 2, "parallelism")
    if backend == "ollama_structured_v3" and config["response_contract"] not in ("agent", "judge"):
        raise PilotError("Choose the agent or judge structured-response contract")
    if not isinstance(config["model"], str) or not str(config["model"]).strip():
        raise PilotError("Choose an explicit model; no automatic model selection")
    integer(config["max_tokens"], 256, 12000, "max_tokens")
    integer(config["max_calls"], 1, 40, "max_calls")
    number(config["timeout"], 1, 480, "timeout")
    number(config["temperature"], 0, 2, "temperature")
    integer(config["memory_bytes"], 0, 8192, "memory_bytes")
