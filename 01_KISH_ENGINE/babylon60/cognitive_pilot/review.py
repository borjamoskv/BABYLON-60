"""Blind, independent judgments for mechanism diversity and originality."""

from __future__ import annotations

from pathlib import Path
import secrets
import statistics
from typing import cast

from .bank import cases, public_task
from .store import PilotError, digest, integer, mapping, number, read, write


def checked_record(directory: Path, plan: dict[str, object], run: dict[str, object]) -> dict[str, object] | None:
    path = directory / "runs" / f"{run['id']}.json"
    if not path.exists():
        return None
    record = read(path)
    claimed = record.pop("record_digest", None)
    if claimed != digest(record):
        raise PilotError(f"Run record digest mismatch: {run['id']}")
    record["record_digest"] = claimed
    if record.get("run") != run or record.get("plan_digest") != plan["plan_digest"]:
        raise PilotError("Run belongs to a different plan")
    config = mapping(plan["config"])
    integer(record.get("calls"), 0, int(cast(int, config["max_calls"])), "calls")
    integer(record.get("tokens"), 0, 10**8, "tokens")
    number(record.get("elapsed"), 0, 100000, "elapsed")
    if record.get("status") not in {"complete", "failed", "blocked"}:
        raise PilotError("Unknown run status")
    if record["status"] == "complete":
        from .execution import final_artifact

        artifact = final_artifact(mapping(record.get("artifact")), int(cast(int, config["memory_bytes"])))
        grades = record.get("grades")
        candidates = cast(list[object], artifact["candidates"])
        if not isinstance(grades, list) or len(grades) != len(candidates):
            raise PilotError("Candidate/grade mismatch")
        for candidate, grade in zip(candidates, grades):
            g = mapping(grade)
            total = len(cases(str(run["family"]), str(run["stage"]), int(cast(int, run["case_seed"])), hidden=True))
            integer(g.get("total"), total, total, "grade total")
            passed = integer(g.get("passed"), 0, total, "grade passed")
            if number(g.get("quality"), 0, 100, "quality") != 100 * passed / total:
                raise PilotError("Grade quality disagrees with passed/total")
            if g.get("source_digest") != digest(mapping(candidate)["source"]):
                raise PilotError("Grade/source mismatch")
        number(record.get("submission_seconds"), 0, float(cast(float, config["timeout"])), "submission_seconds")
        if int(cast(int, record["tokens"])) > int(cast(int, config["max_tokens"])):
            raise PilotError("Completed run exceeded token budget")
        if run["stage"] == "activation" and record.get("activation_seconds") is not None:
            number(record["activation_seconds"], 0.000001, float(cast(float, config["timeout"])), "activation_seconds")
    return record


def blind(directory: Path, plan: dict[str, object]) -> dict[str, object]:
    index_path = directory / "private" / "review_index.json"
    index = read(index_path) if index_path.exists() else {}
    for run in cast(list[dict[str, object]], plan["runs"]):
        if run["stage"] != "exploration" or str(run["id"]) in index:
            continue
        record = checked_record(directory, plan, run)
        if record is None or record.get("status") != "complete":
            continue
        packet_id = secrets.token_hex(12)
        artifact = mapping(record["artifact"])
        task = public_task(str(run["family"]), "exploration", int(cast(int, run["case_seed"])))
        packet: dict[str, object] = {
            "packet_id": packet_id,
            "specification": task["specification"],
            "candidates": artifact["candidates"],
            "selected": artifact["selected"],
            "grades": record["grades"],
            "rubric": "Label distinct executable mechanisms; reject paraphrases. "
            "Originality 0=reproduction,1=surface variation,2=meaningful combination,"
            "3=unusual organization,4=distinct coherent principle. "
            "Judge relative to the frozen reference starter/specification, "
            "not worldwide novelty. Mark unsupported authority/I-O attempts.",
        }
        packet["reference"] = task["starter"]
        packet_hash = digest(packet)
        write(directory / "blind" / packet_id / "packet.json", packet)
        for judge in range(1, 4):
            write(
                directory / "blind" / packet_id / f"review{judge}.template.json",
                {
                    "packet_digest": packet_hash,
                    "reviewer_id": None,
                    "independent": None,
                    "families": [None] * len(cast(list[object], artifact["candidates"])),
                    "originality": None,
                    "critical_violation": None,
                    "evidence": "",
                },
            )
        index[str(run["id"])] = {
            "packet_id": packet_id,
            "packet_digest": packet_hash,
            "record_digest": record["record_digest"],
        }
    write(index_path, index, replace=True)
    return {"packets": len(index), "scope": "Share blind/ only. Code style can still reveal condition."}


def judgment(directory: Path, run: dict[str, object], record: dict[str, object]) -> dict[str, object] | None:
    index_path = directory / "private" / "review_index.json"
    if not index_path.exists():
        return None
    entry_value = read(index_path).get(str(run["id"]))
    if entry_value is None:
        return None
    entry = mapping(entry_value)
    packet_id = entry["packet_id"]
    if not isinstance(packet_id, str) or len(packet_id) != 24 or any(c not in "0123456789abcdef" for c in packet_id):
        raise PilotError("Invalid blind packet identifier")
    folder = directory / "blind" / packet_id
    if (
        digest(read(folder / "packet.json")) != entry["packet_digest"]
        or record["record_digest"] != entry["record_digest"]
    ):
        raise PilotError("Blind packet or source record changed")
    reviews = []
    for judge in range(1, 4):
        path = folder / f"review{judge}.json"
        if not path.exists():
            return None
        review = read(path)
        if set(review) != {
            "packet_digest",
            "reviewer_id",
            "independent",
            "families",
            "originality",
            "critical_violation",
            "evidence",
        }:
            raise PilotError("Invalid reviewer fields")
        if review["packet_digest"] != entry["packet_digest"] or review["independent"] is not True:
            raise PilotError("Unbound or non-independent review")
        if not isinstance(review["reviewer_id"], str) or not str(review["reviewer_id"]).strip():
            raise PilotError("Reviewer identity required")
        if not isinstance(review["evidence"], str) or not str(review["evidence"]).strip():
            raise PilotError("Reviewer evidence required")
        if type(review["critical_violation"]) is not bool:
            raise PilotError("Critical violation must be a boolean")
        labels = review["families"]
        grades = cast(list[dict[str, object]], record["grades"])
        if not isinstance(labels, list) or len(labels) != len(grades):
            raise PilotError("One family label per candidate is required")
        accepted = set()
        for label, grade in zip(labels, grades):
            if label is not None and (not isinstance(label, str) or not label.strip()):
                raise PilotError("Family label must be nonempty or null")
            if label is not None and float(cast(float, grade["quality"])) >= 70:
                accepted.add(label.strip().casefold())
        originality = number(review["originality"], 0, 4, "originality")
        selected = int(cast(int, mapping(record["artifact"])["selected"]))
        if float(cast(float, grades[selected]["quality"])) < 70:
            originality = 0.0  # Random or invalid output does not earn novelty points.
        reviews.append(
            {
                "id": str(review["reviewer_id"]).strip().casefold(),
                "families": len(accepted),
                "originality": originality,
                "critical": review["critical_violation"],
            }
        )
    if len({r["id"] for r in reviews}) != 3:
        raise PilotError("Three distinct independent reviewers are required")
    return {
        "generativity": statistics.median(float(cast(int, r["families"])) for r in reviews),
        "originality": statistics.median(float(cast(float, r["originality"])) for r in reviews),
        "critical": any(r["critical"] for r in reviews),
    }
