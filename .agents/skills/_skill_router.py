#!/usr/bin/env python3
"""Resolve a requested capability; routing never executes its procedure."""

import argparse
import json
from pathlib import Path
import re
import unicodedata
from collections.abc import Sequence
from typing import TypedDict

NEGATED = re.compile(
    r"\b(?:no|nunca|jamas)\s+(?:uses|usar|utilices|actives|ejecutes|ejecutar|cargues|apliques|audita|audites|auditar|revisa|revises|revisar|quiero)\b|^no\s+[$/]|^(?:sin|evita|evitar|excepto|omite|omitir|ignora|ignorar)\b"
)


class RouteIntent(TypedDict):
    actions: list[str]
    topics: list[str]
    exclude: list[str]


class _RouteBase(TypedDict):
    name: str
    aliases: list[str]
    module: str


class RouteRecord(_RouteBase, total=False):
    intent: RouteIntent


class SelectionPolicy(TypedDict):
    generic: list[str]
    continuations: list[str]
    default_actions: list[str]


def normalize(value: str) -> str:
    text = unicodedata.normalize("NFKD", value.casefold())
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def contains(text: str, phrase: str) -> bool:
    return bool(phrase and re.search(r"(?<!\w)" + re.escape(normalize(phrase)) + r"(?!\w)", text))


def clauses(query: str) -> list[str]:
    # Negations apply to their clause, not to a different requested action.
    return [normalize(part) for part in re.split(r"[.;!?\n]+|\bpero\b|\bbut\b", query, flags=re.I) if part.strip()]


def selection_policy() -> SelectionPolicy:
    source = Path(__file__).absolute().parent
    for filename in ["catalog.json", "skill_catalog.generated.json"]:
        candidate = source / filename
        if candidate.is_file():
            policy: SelectionPolicy = json.loads(candidate.read_text())["policy"]
            return policy
    raise ValueError("Canonical routing policy is missing; regenerate this distribution")


def select(query: str, records: Sequence[RouteRecord], context: str = "") -> list[RouteRecord]:
    policy = selection_policy()
    generic = {normalize(value) for value in policy["generic"]}
    continuations = {normalize(value) for value in policy["continuations"]}
    query = normalize(query)
    if query in continuations and context:
        query = normalize(context)
    elif query in generic or query in continuations:
        return []
    positive = [part for part in clauses(query) if not NEGATED.search(part)]
    explicit = [
        record
        for record in records
        if any(
            part in {normalize(record["name"]), normalize("/" + record["name"]), normalize("$" + record["name"])}
            or contains(part, "$" + record["name"])
            or contains(part, "/" + record["name"])
            for part in positive
        )
    ]
    if explicit:
        return explicit
    exact = [
        record
        for record in records
        if query in {normalize(alias) for alias in record["aliases"] if normalize(alias) not in generic} and positive
    ]
    if exact:
        return exact
    contexts: list[str] = []
    for part in positive:
        if re.search(r"\b(?:dice|menciona|cita|ejemplo|describe)\b", part):
            part = re.sub(r'«[^»]*»|"[^"]*"|`[^`]*`', " ", part)
        contexts.append(part)
    hits: list[tuple[RouteRecord, str, str]] = []
    for record in records:
        intent = record.get("intent")
        for part in contexts:
            if intent is not None:
                if any(contains(part, phrase) for phrase in intent.get("exclude", [])):
                    continue
                if not any(contains(part, action) for action in intent["actions"]):
                    continue
                topics = [phrase for phrase in intent["topics"] if contains(part, phrase)]
            else:
                # Read compatibility only: generated production records always carry intent.
                topics = [
                    alias for alias in record["aliases"] if normalize(alias) not in generic and contains(part, alias)
                ]
            hits.extend((record, normalize(topic), part) for topic in topics)
    selected = []
    for record in records:
        if any(
            not any(
                other_topic != topic and other_part == part and contains(other_topic, topic)
                for _, other_topic, other_part in hits
            )
            for match, topic, part in hits
            if match is record
        ):
            selected.append(record)
    return selected


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True)
    parser.add_argument("--context", default="", help="Previous user objective, used only for an explicit continuation")
    roots = parser.add_mutually_exclusive_group(required=True)
    roots.add_argument("--hub-root", type=Path)
    roots.add_argument("--library-root", type=Path)
    args = parser.parse_args()
    root = (args.hub_root or args.library_root).absolute()
    if args.hub_root:
        records: list[RouteRecord] = json.loads((root / "references/aliases.json").read_text())["modules"]
    else:
        catalog = json.loads((root / "skill_catalog.generated.json").read_text())
        records = []
        for name, capability in catalog["capabilities"].items():
            module = capability.get("module")
            intent: RouteIntent = capability["intent"].copy()
            intent.setdefault("actions", catalog["policy"]["default_actions"])
            records.append(
                {
                    "name": name,
                    "aliases": capability["aliases"],
                    "intent": intent,
                    "module": str(Path(module["hub"]) / module["path"]) if module else name + "/SKILL.md",
                }
            )
    matches = select(args.query, records, args.context)
    result = []
    for record in matches:
        relative = Path(record["module"])
        if relative.is_absolute() or ".." in relative.parts or not (root / relative).is_file():
            parser.error("Selected procedure is missing or outside its hub")
        result.append({"name": record["name"], "module": str(root / relative)})
    print(json.dumps(result, ensure_ascii=False))
    return 3 if len(matches) > 1 else 0 if matches else 2


if __name__ == "__main__":
    raise SystemExit(main())
