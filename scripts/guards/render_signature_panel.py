#!/usr/bin/env python3
"""Render one immutable MOSKV-1 signature from explicit, sourced turn data."""

from __future__ import annotations

import argparse
from collections.abc import Mapping, Sequence
from datetime import datetime
from html import escape
import json
import os
from pathlib import Path
import re
from typing import cast


CONTEXT_FIELDS: tuple[tuple[str, str, str], ...] = (
    ("verification", "Verificación", "VERIFICACIÓN"),
    ("changes", "Cambios", "CAMBIOS"),
    ("limits", "Límites", "LÍMITES"),
    ("thermal", "Régimen térmico", "RÉGIMEN TÉRMICO"),
    ("lexical", "Índice léxico", "EXERGÍA INFORMATIVA"),
    ("mutation", "Mutación causal", "MUTACIÓN CAUSAL"),
)
REQUIRED = frozenset({"model", "model_source", "observed_at"})
ALLOWED = REQUIRED | {"model_context", "effort"} | {key for key, _, _ in CONTEXT_FIELDS}
MARKER = re.compile(r"\{\{([A-Z_]+)\}\}")
OBSERVATION = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)"
)
UNMEASURED = re.compile(r"^no medid[oa]\b", re.IGNORECASE)
UNEXPOSED = re.compile(r"^no expuesto\b", re.IGNORECASE)


def _object(value: object, name: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{name}: expected an object")
    mapping = cast(Mapping[object, object], value)
    result: dict[str, object] = {}
    for key, item in mapping.items():
        if not isinstance(key, str):
            raise ValueError(f"{name}: keys must be strings")
        result[key] = item
    return result


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name}: expected a non-empty string")
    return value.strip()


def _observation(value: object) -> tuple[str, str]:
    stamp = _text(value, "observed_at")
    if not OBSERVATION.fullmatch(stamp):
        raise ValueError("observed_at: expected an ISO 8601 timestamp with T separator and valid timezone")
    try:
        observed = datetime.fromisoformat(stamp.removesuffix("Z") + "+00:00" if stamp.endswith("Z") else stamp)
    except ValueError as exc:
        raise ValueError("observed_at: expected an ISO 8601 timestamp with timezone") from exc
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ValueError("observed_at: timezone is required")
    return stamp, f"{observed:%d/%m/%Y · %H:%M} {observed.tzname()}"


def _sourced(value: object, key: str) -> tuple[str, str]:
    item = _object(value, key)
    if set(item) != {"value", "source"}:
        raise ValueError(f"{key}: exactly value and source are required")
    text = _text(item["value"], f"{key}.value")
    source = _text(item["source"], f"{key}.source")
    if key == "effort" and UNEXPOSED.match(text):
        raise ValueError("effort: omit the field when effort is not exposed")
    if key in {"thermal", "lexical"} and UNMEASURED.match(text):
        raise ValueError(f"{key}: omit the field when it has not been measured")
    return escape(text, quote=True), escape(source, quote=True)


def _source_row(label: str, field: str, source: str) -> str:
    return (
        f'<div class="s-source"><dt>{label}</dt>'
        f'<dd data-signature-source="{field}">{source}</dd></div>'
    )


def render_panel(payload: Mapping[str, object], template: str) -> str:
    """Escape data and render only optional fields with an explicit source.

    Source descriptions are observations supplied by the caller. Rendering them
    does not certify the model, the measurements, or the described verification.
    """
    data = _object(payload, "payload")
    unknown = set(data) - ALLOWED
    if unknown:
        raise ValueError(f"payload: unknown keys: {', '.join(sorted(unknown))}")
    missing = REQUIRED - set(data)
    if missing:
        raise ValueError(f"payload: missing keys: {', '.join(sorted(missing))}")
    model = _text(data["model"], "model")
    model_source = _text(data["model_source"], "model_source")
    model_context = _text(data.get("model_context", "No evaluable"), "model_context")
    stamp, observed_label = _observation(data["observed_at"])
    effort_block = ""
    sources: list[str] = []
    if "effort" in data:
        effort, source = _sourced(data["effort"], "effort")
        effort_block = f'<span class="s-effort" data-signature-field="MODO COGNITIVO">{effort}</span>'
        sources.append(_source_row("Esfuerzo", "MODO COGNITIVO", source))
    rows: list[str] = []
    for key, label, field in CONTEXT_FIELDS:
        if key not in data:
            continue
        value, source = _sourced(data[key], key)
        rows.append(
            f'<div class="s-row"><dt>{label}</dt>'
            f'<dd data-signature-field="{field}">{value}</dd></div>'
        )
        sources.append(_source_row(label, field, source))
    context = '<dl class="s-context">' + "".join(rows) + "</dl>" if rows else ""
    replacements = {
        "MODEL": escape(model, quote=True),
        "MODEL_CONTEXT": escape(model_context, quote=True),
        "MODEL_SOURCE": escape(model_source, quote=True),
        "OBSERVED_AT": escape(stamp, quote=True),
        "OBSERVED_LABEL": escape(observed_label, quote=True),
        "EFFORT_BLOCK": effort_block,
        "CONTEXT_ROWS": context,
        "SOURCE_ROWS": "".join(sources),
    }
    markers = set(MARKER.findall(template))
    if markers != set(replacements):
        raise ValueError("template: expected all eight supported signature markers and no unknown markers")
    # A single pass ensures user text containing {{MODEL}} stays literal text.
    return MARKER.sub(lambda match: replacements[match.group(1)], template)


def _unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"payload: duplicate key: {key}")
        result[key] = value
    return result


def _read_text(path: Path) -> str:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(descriptor, "r", encoding="utf-8") as stream:
        return stream.read()


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", type=Path, help="JSON containing sourced observations for this response")
    parser.add_argument("output", type=Path, help="A new HTML file; existing files are never replaced")
    args = parser.parse_args(argv)
    try:
        decoded: object = json.loads(_read_text(args.payload), object_pairs_hook=_unique_object)
        payload = _object(decoded, "payload")
        template = _read_text(Path(__file__).absolute().with_name("signature_panel.html"))
        rendered = render_panel(payload, template)
        with args.output.open("x", encoding="utf-8") as output:
            output.write(rendered)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(args.output.absolute())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
