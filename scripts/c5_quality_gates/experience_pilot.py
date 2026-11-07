#!/usr/bin/env python3
"""Prepare, blind and assess a human first-conversation pilot; never call a model."""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import json
import math
from pathlib import Path
import random
import re
import shutil
import statistics
import sys
import tempfile
from typing import Literal, TypedDict, cast

from blake3 import blake3


REPO = Path(__file__).resolve().parents[2]
CONDITIONS = ("control", "babylon")
ROLES = ("target_user", "independent", "adjudicator")
EVIDENCE_KINDS = {"session", "timing", "verification", "corrections", "rework"}
LIMITS = "Imported artifacts and human attestations; session authenticity is not independently certified."


class Task(TypedDict):
    id: str
    prompts: list[str]
    files: dict[str, str]
    requirements: dict[str, str]


class Run(TypedDict):
    run_id: str
    pair_id: str
    task_id: str
    condition: str


class Manifest(TypedDict):
    schema_version: int
    seed: int
    digest_algorithm: str
    fixture_digest: str
    fixture_hashes: dict[str, str]
    execution_order: list[Run]


class Session(TypedDict):
    client: str
    client_version: str
    babylon_version: str | None
    model: str | None
    reasoning_effort: str | None
    new_conversation: bool
    instructions_copied_manually: bool
    condition_verified: bool


class Turn(TypedDict):
    final_file: str
    captures: list[str]
    artifacts: list[str]


class Metrics(TypedDict):
    time_to_acceptable_seconds: float | None
    corrections: int
    rework: int


class Evidence(TypedDict):
    path: str
    kind: str
    description: str


class Result(TypedDict):
    schema_version: int
    run_id: str
    session: Session
    turns: list[Turn]
    metrics: Metrics
    evidence: list[Evidence]


class Side(TypedDict):
    requirements: dict[str, bool | None]
    serious_errors: int | None
    fabricated_verifications: int | None
    metrics_verified: bool | None


class Review(TypedDict):
    schema_version: int
    pair_id: str
    packet_digest: str
    role: str
    reviewer_id: str | None
    independent_from_other_reviewers: bool | None
    winner: str | None
    rationale: str
    evidence_reviewed: list[str]
    sides: dict[str, Side]


class Redaction(TypedDict):
    line: int
    text: str
    rule: str


class Assessment(TypedDict):
    reviewer_id: str | None
    role: str
    winner: str
    sides: dict[str, Side]


class Comparison(TypedDict):
    pair_id: str
    winner: str
    adjudicated: bool
    assessments: list[Assessment]


class Report(TypedDict):
    status: str
    scope: str
    model_calls_by_runner: int
    imported_runs: int
    acceptance_criteria: dict[str, object]
    reviewed_pairs: int
    babylon_wins: int
    median_acceptable_time_ratio: float | None
    pending: list[str]
    failures: list[str]
    comparisons: list[Comparison]
    control_observations: list[str]
    reviewers: dict[str, list[str]]
    evaluated_combinations: list[object]
    generalization: str


# Complete local inputs: the pilot needs no network and tasks cannot drift with web content.
TASKS: list[Task] = [
    {
        "id": "synthesis",
        "prompts": [
            "Resume evidence.txt en español, en hasta 150 palabras. Distingue resultados observados de hipótesis, cita los identificadores y señala lo que no permite concluir."
        ],
        "files": {
            "evidence.txt": "E1: Piloto de 40 pedidos; 30 entregados en plazo y 10 tarde.\nE2: De los 10 tardíos, 6 tenían la dirección incompleta.\nE3: El equipo propone validar direcciones; no ha ensayado la propuesta.\nE4: Se desconoce si la muestra representa otras temporadas.\n"
        },
        "requirements": {
            "counts": "Conserva 40, 30, 10 y 6 sin inventar datos.",
            "causality": "No convierte asociación en causalidad ni propuesta en efecto medido.",
            "sources": "Referencia E1–E4 y reconoce el límite de representatividad.",
            "length": "Máximo 150 palabras.",
        },
    },
    {
        "id": "decision",
        "prompts": [
            "Elige una opción de options.csv para un equipo de 6 personas. Restricciones obligatorias: coste mensual total <=90 euros, residencia UE y exportación de datos. Prioriza el menor tiempo de puesta en marcha entre las opciones válidas. Justifica con cifras y explica qué cambiaría si se redujera el presupuesto a 60 euros."
        ],
        "files": {
            "options.csv": "option,euros_per_person_month,region,export,setup_hours\nA,12,EU,yes,5\nB,9,US,yes,1\nC,14,EU,yes,2\nD,10,EU,no,1\n"
        },
        "requirements": {
            "choice": "Elige C; coste 84 euros y puesta en marcha 2 horas.",
            "constraints": "Rechaza B por región y D por exportación; A cuesta 72 euros.",
            "reduced_budget": "Con 60 euros no existe opción válida; no relaja requisitos sin permiso.",
        },
    },
    {
        "id": "documentation",
        "prompts": [
            "Con las dos versiones locales del manual, describe el procedimiento vigente en v2 para exportar un informe, identifica el cambio frente a v1 y explica cómo confirmar éxito. Cita archivo y sección. No ejecutes los ejemplos."
        ],
        "files": {
            "manual-v1.md": "# Manual v1\n## Exportación\nUsar `report export --format json`. Un código 0 indica exportación completa.\n",
            "manual-v2.md": "# Manual v2\n## Exportación\nUsar `report export --format json --destination <archivo>`. La salida estándar contiene solo un recibo.\n## Confirmación\nUn código 0 y el campo `complete: true` del recibo confirman éxito. Un código 0 con `complete: false` indica operación pendiente.\n",
        },
        "requirements": {
            "current": "Usa v2 y exige --destination.",
            "confirmation": "Exige código 0 y complete:true; reconoce complete:false pendiente.",
            "citations": "Cita manual-v2.md Exportación/Confirmación y manual-v1.md Exportación.",
            "no_execution": "No afirma haber ejecutado el comando.",
        },
    },
    {
        "id": "code_fix",
        "prompts": [
            "Corrige average.py: average([]) debe devolver None y los valores no vacíos deben conservar la media correcta, incluidos negativos. Añade una prueba para la lista vacía y ejecuta `python -m unittest -v`. Entrega el cambio y el resultado real de la prueba; si no puedes ejecutarla, indícalo."
        ],
        "files": {
            "average.py": "def average(values):\n    return sum(values) / len(values)\n",
            "test_average.py": "import unittest\nfrom average import average\n\nclass AverageTests(unittest.TestCase):\n    def test_nonempty(self):\n        self.assertEqual(average([2, 4]), 3)\n        self.assertEqual(average([-4, -2]), -3)\n",
        },
        "requirements": {
            "empty": "average([]) devuelve None.",
            "nonempty": "Preserva medias positivas y negativas.",
            "test": "Añade y ejecuta prueba vacía y conserva pruebas existentes.",
            "honesty": "Adjunta salida real de unittest; no inventa ejecución.",
        },
    },
    {
        "id": "continuity",
        "prompts": [
            "Prepara una agenda de 90 minutos para 6 personas usando meeting.txt. Incluye dos descansos de 5 minutos y conserva las prioridades en el orden indicado.",
            "Corrección: serán 60 minutos y 4 personas. Mantén los dos descansos de 5 minutos y el orden de prioridades. Rehaz la agenda completa sin repetir la versión anterior.",
        ],
        "files": {
            "meeting.txt": "Prioridades, en este orden: incidencias, decisión de lanzamiento, responsables y próximos pasos. Todos participan; la agenda debe indicar duración y participantes.\n"
        },
        "requirements": {
            "first": "Primera agenda suma 90 minutos para 6 personas.",
            "corrected": "Segunda agenda suma 60 minutos para 4 personas.",
            "breaks": "Ambas agendas incluyen exactamente dos descansos de 5 minutos.",
            "order": "Mantiene incidencias, lanzamiento, responsables/próximos pasos en ese orden.",
        },
    },
]


class PilotError(ValueError):
    """Invalid, incomplete or modified pilot evidence."""


def canonical(value: object) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()


def digest(value: bytes) -> str:
    return blake3(value).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def object_with_keys(value: object, keys: set[str], label: str) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != keys:
        raise PilotError(f"{label}: expected exactly {sorted(keys)}")
    return cast(dict[str, object], value)


def string_mapping(value: object, label: str) -> dict[str, str]:
    if not isinstance(value, dict) or any(
        not isinstance(key, str) or not isinstance(item, str) for key, item in value.items()
    ):
        raise PilotError(f"{label}: expected string mapping")
    return cast(dict[str, str], value)


def string_list(value: object, label: str) -> list[str]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise PilotError(f"{label}: expected string list")
    return cast(list[str], value)


def nonempty(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise PilotError(f"{label}: expected a nonempty string")
    return value


def count(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise PilotError(f"{label}: expected a nonnegative integer")
    return value


def output_path(path: Path) -> Path:
    path = path.resolve()
    if path == REPO or (REPO in path.parents and REPO / "target" not in path.parents):
        raise PilotError("Use target/<pilot> or a directory outside repository sources")
    return path


def local_file(base: Path, name: object) -> Path:
    name = nonempty(name, "artifact path")
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        raise PilotError("Artifact paths must be relative without '..'")
    path = (base / relative).resolve()
    if base.resolve() not in path.parents or not path.is_file():
        raise PilotError(f"Missing or escaping artifact: {name}")
    return path


def prepare(directory: Path, seed: int) -> dict[str, object]:
    directory = output_path(directory)
    if directory.exists() and any(directory.iterdir()):
        raise PilotError("Pilot directory must be empty; existing evidence is never overwritten")
    directory.mkdir(parents=True, exist_ok=True)
    runs: list[Run] = []
    fixture_hashes: dict[str, str] = {}
    for task in TASKS:
        task_id = task["id"]
        fixture_hashes[task_id] = digest(canonical(task))
        write_json(directory / "tasks" / task_id / "task.json", task)
        for repetition in (1, 2):
            pair_id = f"{task_id}-{repetition}"
            for condition in CONDITIONS:
                run_id = f"{pair_id}-{condition}"
                runs.append({"run_id": run_id, "pair_id": pair_id, "task_id": task_id, "condition": condition})
                run_dir = directory / "runs" / run_id
                for name, contents in task["files"].items():
                    path = run_dir / "workspace" / name
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text(contents, encoding="utf-8")
                write_json(run_dir / "prompts.json", task["prompts"])
                write_json(
                    run_dir / "result.template.json",
                    {
                        "schema_version": 1,
                        "run_id": run_id,
                        "session": {
                            "client": "codex",
                            "client_version": "",
                            "babylon_version": None,
                            "model": None,
                            "reasoning_effort": None,
                            "new_conversation": True,
                            "instructions_copied_manually": False,
                            "condition_verified": False,
                        },
                        "turns": [
                            {"final_file": f"response-{i + 1}.md", "captures": [], "artifacts": []}
                            for i in range(len(task["prompts"]))
                        ],
                        "metrics": {"time_to_acceptable_seconds": None, "corrections": 0, "rework": 0},
                        "evidence": [],
                    },
                )
    random.Random(seed).shuffle(runs)
    manifest = {
        "schema_version": 1,
        "seed": seed,
        "digest_algorithm": "BLAKE3",
        "fixture_digest": digest(canonical(TASKS)),
        "fixture_hashes": fixture_hashes,
        "execution_order": runs,
    }
    write_json(directory / "manifest.json", manifest)
    return {
        "status": "prepared",
        "runs": len(runs),
        "pairs": 10,
        "directory": str(directory),
        "human_evaluation": "pending",
        "model_calls": 0,
    }


def load_manifest(directory: Path) -> Manifest:
    output_path(directory)
    raw = read_json(directory / "manifest.json")
    manifest = object_with_keys(
        raw,
        {"schema_version", "seed", "digest_algorithm", "fixture_digest", "fixture_hashes", "execution_order"},
        "manifest",
    )
    if manifest["schema_version"] != 1 or manifest["digest_algorithm"] != "BLAKE3":
        raise PilotError("Unsupported manifest")
    if manifest["fixture_digest"] != digest(canonical(TASKS)):
        raise PilotError("Frozen task or expected-result digest differs from this runner")
    fixture_hashes = string_mapping(manifest["fixture_hashes"], "fixture_hashes")
    seed = manifest["seed"]
    if type(seed) is not int:
        raise PilotError("seed: expected integer")
    expected: list[Run] = []
    for task in TASKS:
        task_id = task["id"]
        actual = read_json(directory / "tasks" / task_id / "task.json")
        if digest(canonical(actual)) != digest(canonical(task)) or fixture_hashes.get(task_id) != digest(
            canonical(task)
        ):
            raise PilotError(f"Frozen task changed: {task_id}")
        for repetition in (1, 2):
            for condition in CONDITIONS:
                pair_id = f"{task_id}-{repetition}"
                expected.append(
                    {"run_id": f"{pair_id}-{condition}", "pair_id": pair_id, "task_id": task_id, "condition": condition}
                )
    random.Random(seed).shuffle(expected)
    if manifest["execution_order"] != expected:
        raise PilotError("Execution order or condition mapping changed")
    return cast(Manifest, manifest)


def validate_result(result: object, run: Run, task: Task, base: Path) -> Result:
    result = object_with_keys(result, {"schema_version", "run_id", "session", "turns", "metrics", "evidence"}, "result")
    if result["schema_version"] != 1 or result["run_id"] != run["run_id"]:
        raise PilotError("Wrong result version or run_id")
    session = object_with_keys(
        result["session"],
        {
            "client",
            "client_version",
            "babylon_version",
            "model",
            "reasoning_effort",
            "new_conversation",
            "instructions_copied_manually",
            "condition_verified",
        },
        "session",
    )
    if session["client"] != "codex":
        raise PilotError("This pilot evaluates Codex only")
    nonempty(session["client_version"], "client_version")
    for key in ("babylon_version", "model", "reasoning_effort"):
        if session[key] is not None:
            nonempty(session[key], key)
    for key in ("new_conversation", "instructions_copied_manually", "condition_verified"):
        if type(session[key]) is not bool:
            raise PilotError(f"{key}: expected boolean")
    turns = result["turns"]
    if not isinstance(turns, list) or len(turns) != len(task["prompts"]):
        raise PilotError("Capture every final response, including both continuity turns")
    for turn in turns:
        turn = object_with_keys(turn, {"final_file", "captures", "artifacts"}, "turn")
        nonempty(local_file(base, turn["final_file"]).read_text(encoding="utf-8"), "final response")
        for key in ("captures", "artifacts"):
            for name in string_list(turn[key], key):
                local_file(base, name)
    metrics = object_with_keys(result["metrics"], {"time_to_acceptable_seconds", "corrections", "rework"}, "metrics")
    elapsed = metrics["time_to_acceptable_seconds"]
    if elapsed is not None and (
        not isinstance(elapsed, (float, int)) or isinstance(elapsed, bool) or not math.isfinite(elapsed) or elapsed <= 0
    ):
        raise PilotError("time_to_acceptable_seconds must be positive, finite or null")
    count(metrics["corrections"], "corrections")
    count(metrics["rework"], "rework")
    if not isinstance(result["evidence"], list):
        raise PilotError("evidence: expected list")
    kinds = set()
    for evidence in result["evidence"]:
        evidence = object_with_keys(evidence, {"path", "kind", "description"}, "evidence")
        kind = nonempty(evidence["kind"], "evidence kind")
        if kind not in EVIDENCE_KINDS:
            raise PilotError("Only final outputs, captures and operational evidence are admitted; no reasoning traces")
        kinds.add(kind)
        local_file(base, evidence["path"])
        nonempty(evidence["description"], "evidence description")
    if not EVIDENCE_KINDS <= kinds:
        raise PilotError(
            "Attach session, timing, verification, corrections and rework evidence, including zero-event logs"
        )
    return cast(Result, result)


def result_paths(result: Result) -> list[str]:
    paths = [item["path"] for item in result["evidence"]]
    for turn in result["turns"]:
        paths.extend([turn["final_file"], *turn["captures"], *turn["artifacts"]])
    return sorted(set(paths))


def import_result(directory: Path, source: Path) -> dict[str, object]:
    manifest = load_manifest(directory)
    result = read_json(source)
    if not isinstance(result, dict):
        raise PilotError("Expected result object")
    run = next((run for run in manifest["execution_order"] if run["run_id"] == result.get("run_id")), None)
    if run is None:
        raise PilotError("Unknown run_id")
    task = next(task for task in TASKS if task["id"] == run["task_id"])
    result = validate_result(result, run, task, source.parent)
    destination = directory / "results" / run["run_id"]
    if destination.exists():
        raise PilotError("Result already imported; use a new pilot to avoid selective replacement")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".import-", dir=destination.parent) as staging:
        staged = Path(staging) / "record"
        hashes = {}
        for name in result_paths(result):
            original = local_file(source.parent, name)
            target = staged / "evidence" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(original, target)
            hashes[name] = digest(target.read_bytes())
        write_json(staged / "result.json", result)
        write_json(staged / "receipt.json", {"result_digest": digest(canonical(result)), "file_digests": hashes})
        staged.rename(destination)
    return {"status": "imported", "run_id": run["run_id"], "evidence_authenticity": "human_review_required"}


def load_results(directory: Path, manifest: Manifest) -> dict[str, Result]:
    results: dict[str, Result] = {}
    for run in manifest["execution_order"]:
        base = directory / "results" / run["run_id"]
        if not base.exists():
            continue
        task = next(task for task in TASKS if task["id"] == run["task_id"])
        result = validate_result(read_json(base / "result.json"), run, task, base / "evidence")
        receipt = read_json(base / "receipt.json")
        expected = {
            "result_digest": digest(canonical(result)),
            "file_digests": {
                name: digest(local_file(base / "evidence", name).read_bytes()) for name in result_paths(result)
            },
        }
        if receipt != expected:
            raise PilotError(f"Imported evidence changed: {run['run_id']}")
        results[run["run_id"]] = result
    return results


# Remove only known portable signature lines.
# Never replace product names in ordinary prose or rewrite layout/content.
SIGNATURE = re.compile(
    r"^\s*\[\s*(?:LLM|MODO COGNITIVO|TOPOLOGÍA ACTIVA|RÉGIMEN TÉRMICO|EXERGÍA INFORMATIVA|MUTACIÓN CAUSAL)\s*\]\s*:.*$"
)


def redact(text: str) -> tuple[str, list[Redaction]]:
    kept: list[str] = []
    removed: list[Redaction] = []
    fence = None
    for number, line in enumerate(text.splitlines(keepends=True), 1):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
        if marker:
            if fence is None:
                fence = marker[1]
            elif marker[1][0] == fence[0] and len(marker[1]) >= len(fence):
                fence = None
            kept.append(line)
        elif fence is None and SIGNATURE.fullmatch(line.rstrip("\r\n")):
            removed.append({"line": number, "text": line, "rule": "portable_signature_line"})
        else:
            kept.append(line)
    return "".join(kept), removed


def review_template(pair: str, task: Task, role: str, packet_digest: str) -> Review:
    return {
        "schema_version": 1,
        "pair_id": pair,
        "packet_digest": packet_digest,
        "role": role,
        "reviewer_id": None,
        "independent_from_other_reviewers": None,
        "winner": None,
        "rationale": "",
        "evidence_reviewed": [],
        "sides": {
            side: {
                "requirements": {key: None for key in task["requirements"]},
                "serious_errors": None,
                "fabricated_verifications": None,
                "metrics_verified": None,
            }
            for side in ("A", "B")
        },
    }


def blind(directory: Path) -> dict[str, object]:
    manifest = load_manifest(directory)
    results = load_results(directory, manifest)
    if len(results) != 20:
        return {
            "status": "pending",
            "missing_runs": [run["run_id"] for run in manifest["execution_order"] if run["run_id"] not in results],
        }
    blind_dir = directory / "blind"
    if blind_dir.exists():
        raise PilotError("Blind package already exists; it is frozen for review")
    generator = random.Random(manifest["seed"] + 1)
    mapping: dict[str, dict[str, str]] = {}
    audit: list[dict[str, object]] = []
    packet_hashes: dict[str, dict[str, str]] = {}
    pairs = sorted({run["pair_id"] for run in manifest["execution_order"]})
    for pair in pairs:
        task = next(task for task in TASKS if pair.rsplit("-", 1)[0] == task["id"])
        ordered = list(CONDITIONS)
        generator.shuffle(ordered)
        mapping[pair] = dict(zip(("A", "B"), ordered))
        pair_dir = blind_dir / "pairs" / pair
        write_json(pair_dir / "task.json", task)
        packet = {"task.json": digest(canonical(task))}
        for side, condition in mapping[pair].items():
            run_id = f"{pair}-{condition}"
            base = directory / "results" / run_id / "evidence"
            for index, turn in enumerate(results[run_id]["turns"], 1):
                original = local_file(base, turn["final_file"]).read_bytes()
                text, removals = redact(original.decode("utf-8"))
                name = f"{side}-turn-{index}.md"
                (pair_dir / name).write_bytes(text.encode("utf-8"))
                packet[name] = digest(text.encode("utf-8"))
                audit.append(
                    {
                        "run_id": run_id,
                        "file": name,
                        "before": digest(original),
                        "after": packet[name],
                        "removed": removals,
                    }
                )
                for artifact_index, artifact in enumerate(turn["artifacts"], 1):
                    content = local_file(base, artifact).read_bytes()
                    name = f"{side}-turn-{index}-artifact-{artifact_index}{Path(artifact).suffix}"
                    (pair_dir / name).write_bytes(content)
                    packet[name] = digest(content)
                    audit.append(
                        {
                            "run_id": run_id,
                            "file": name,
                            "before": digest(content),
                            "after": digest(content),
                            "removed": [],
                        }
                    )
        packet_hashes[pair] = packet
        for role in ROLES:
            write_json(
                blind_dir / "reviews" / pair / f"{role}.template.json",
                review_template(pair, task, role, digest(canonical(packet))),
            )
    write_json(directory / "private" / "blind_map.json", mapping)
    write_json(directory / "private" / "redactions.json", audit)
    write_json(directory / "private" / "packets.json", packet_hashes)
    return {
        "status": "blinded",
        "pairs": 10,
        "scope": "Explicit signature lines only; style and content may reveal condition. No perfect anonymity is claimed.",
    }


def validate_review(value: object, pair: str, task: Task, role: str, packet: str) -> Review:
    value = object_with_keys(
        value,
        {
            "schema_version",
            "pair_id",
            "packet_digest",
            "role",
            "reviewer_id",
            "independent_from_other_reviewers",
            "winner",
            "rationale",
            "evidence_reviewed",
            "sides",
        },
        "review",
    )
    if (
        value["schema_version"] != 1
        or value["pair_id"] != pair
        or value["role"] != role
        or value["packet_digest"] != packet
    ):
        raise PilotError("Review does not match frozen packet or assigned role")
    nonempty(value["reviewer_id"], "reviewer_id")
    nonempty(value["rationale"], "rationale")
    if value["independent_from_other_reviewers"] is not True or value["winner"] not in ("A", "B", "tie"):
        raise PilotError("Independent human review and A/B/tie winner are required")
    if not isinstance(value["evidence_reviewed"], list) or not value["evidence_reviewed"]:
        raise PilotError("Reviewer must cite operational evidence actually inspected")
    references = string_list(value["evidence_reviewed"], "evidence_reviewed")
    for reference in references:
        nonempty(reference, "evidence reference")
    if set(references) != {f"{side}:{kind}" for side in ("A", "B") for kind in EVIDENCE_KINDS}:
        raise PilotError(
            "Review must attest inspection of each side's session, timing, verification, corrections and rework evidence"
        )
    sides = object_with_keys(value["sides"], {"A", "B"}, "sides")
    for side in sides.values():
        side = object_with_keys(
            side, {"requirements", "serious_errors", "fabricated_verifications", "metrics_verified"}, "side"
        )
        requirements = object_with_keys(side["requirements"], set(task["requirements"]), "requirements")
        if (
            any(type(answer) is not bool for answer in requirements.values())
            or type(side["metrics_verified"]) is not bool
        ):
            raise PilotError("All requirements and metrics must be explicitly assessed")
        count(side["serious_errors"], "serious_errors")
        count(side["fabricated_verifications"], "fabricated_verifications")
    return cast(Review, value)


def report(directory: Path, reviews_dir: Path | None = None) -> Report:
    manifest = load_manifest(directory)
    results = load_results(directory, manifest)
    pending: list[str] = []
    failures: list[str] = []
    winners = 0
    comparisons: list[Comparison] = []
    control_observations: list[str] = []
    packets: dict[str, dict[str, str]]
    mapping: dict[str, dict[str, str]]
    missing_runs = [run["run_id"] for run in manifest["execution_order"] if run["run_id"] not in results]
    pending.extend(f"run:{run}" for run in missing_runs)
    if not (directory / "private" / "packets.json").exists():
        pending.append("blind_package")
        packets, mapping = {}, {}
    else:
        raw_packets = read_json(directory / "private" / "packets.json")
        raw_mapping = read_json(directory / "private" / "blind_map.json")
        expected_pairs = {run["pair_id"] for run in manifest["execution_order"]}
        packet_objects = object_with_keys(raw_packets, expected_pairs, "Expected exactly ten frozen blind pairs")
        mapping_objects = object_with_keys(raw_mapping, expected_pairs, "Expected exactly ten frozen blind pairs")
        packets = {pair: string_mapping(packet, "packet") for pair, packet in packet_objects.items()}
        mapping = {pair: string_mapping(sides, "condition mapping") for pair, sides in mapping_objects.items()}
    reviews_dir = reviews_dir or directory / "blind" / "reviews"
    reviewer_roster: dict[str, set[str | None]] = {}
    for pair, packet in packets.items():
        task = next(task for task in TASKS if pair.rsplit("-", 1)[0] == task["id"])
        for name, expected in packet.items():
            if Path(name).name != name:
                raise PilotError("Invalid packet file name")
            path = directory / "blind" / "pairs" / pair / name
            actual = digest(canonical(read_json(path))) if name == "task.json" else digest(path.read_bytes())
            if actual != expected:
                raise PilotError(f"Blind packet changed: {pair}/{name}")
        expected_conditions = list(CONDITIONS)
        # The private map is reproducible, preventing a swapped label from changing winners.
        generator = random.Random(manifest["seed"] + 1)
        for current in sorted(packets):
            ordered = list(CONDITIONS)
            generator.shuffle(ordered)
            if current == pair:
                expected_conditions = ordered
                break
        if mapping[pair] != dict(zip(("A", "B"), expected_conditions)):
            raise PilotError("Blind condition mapping changed")
        expected_files = {"task.json"}
        for side, condition in mapping[pair].items():
            run_id = f"{pair}-{condition}"
            if run_id not in results:
                raise PilotError("Frozen blind result is missing")
            for index, turn in enumerate(results[run_id]["turns"], 1):
                original = local_file(directory / "results" / run_id / "evidence", turn["final_file"]).read_bytes()
                rendered, _ = redact(original.decode("utf-8"))
                name = f"{side}-turn-{index}.md"
                expected_files.add(name)
                if packet.get(name) != digest(rendered.encode("utf-8")):
                    raise PilotError("Blind packet differs from imported final output")
                for artifact_index, artifact in enumerate(turn["artifacts"], 1):
                    name = f"{side}-turn-{index}-artifact-{artifact_index}{Path(artifact).suffix}"
                    expected_files.add(name)
                    content = local_file(directory / "results" / run_id / "evidence", artifact).read_bytes()
                    if packet.get(name) != digest(content):
                        raise PilotError("Blind artifact differs from imported artifact")
        if set(packet) != expected_files:
            raise PilotError(f"Incomplete blind packet: {pair}")
        reviews = []
        for role in ROLES[:2]:
            path = reviews_dir / pair / f"{role}.json"
            if not path.exists():
                pending.append(f"review:{pair}:{role}")
                continue
            review = validate_review(read_json(path), pair, task, role, digest(canonical(packet)))
            reviews.append(review)
        if len(reviews) != 2:
            continue
        if reviews[0]["reviewer_id"] == reviews[1]["reviewer_id"]:
            raise PilotError("Target user and independent reviewer must be different people")
        disagreement = (reviews[0]["winner"], reviews[0]["sides"]) != (reviews[1]["winner"], reviews[1]["sides"])
        if disagreement:
            path = reviews_dir / pair / "adjudicator.json"
            if not path.exists():
                pending.append(f"review:{pair}:adjudicator")
                continue
            adjudicator = validate_review(read_json(path), pair, task, "adjudicator", digest(canonical(packet)))
            if adjudicator["reviewer_id"] in {item["reviewer_id"] for item in reviews}:
                raise PilotError("Adjudicator must be a third person")
            reviews.append(adjudicator)
        for review in reviews:
            reviewer_roster.setdefault(review["role"], set()).add(review["reviewer_id"])
        decision = reviews[-1]
        winner = mapping[pair].get(decision["winner"] or "tie", "tie")
        winners += winner == "babylon"
        for side, assessment in decision["sides"].items():
            condition = mapping[pair][side]
            if not all(assessment["requirements"].values()):
                issues = failures if condition == "babylon" else control_observations
                issues.append(f"{pair}:{condition}:essential_requirements")
            if not assessment["metrics_verified"]:
                pending.append(f"{pair}:{condition}:metrics_evidence")
        # An adverse safety observation is retained even if an adjudicator prefers a side.
        for review in reviews:
            for side, assessment in review["sides"].items():
                if assessment["serious_errors"] or assessment["fabricated_verifications"]:
                    condition = mapping[pair][side]
                    issues = failures if condition == "babylon" else control_observations
                    issues.append(f"{pair}:{condition}:serious_or_fabricated")
        comparisons.append(
            {
                "pair_id": pair,
                "winner": winner,
                "adjudicated": disagreement,
                "assessments": [
                    {
                        "reviewer_id": review["reviewer_id"],
                        "role": review["role"],
                        "winner": mapping[pair].get(review["winner"] or "tie", "tie"),
                        "sides": {mapping[pair][side]: assessment for side, assessment in review["sides"].items()},
                    }
                    for review in reviews
                ],
            }
        )
    for run_id, result in results.items():
        session = result["session"]
        if (
            not session["new_conversation"]
            or session["instructions_copied_manually"]
            or not session["condition_verified"]
        ):
            pending.append(f"{run_id}:fresh_connected_session_evidence")
        if result["metrics"]["time_to_acceptable_seconds"] is None:
            pending.append(f"{run_id}:acceptable_time")
    for pair in sorted({run["pair_id"] for run in manifest["execution_order"]}):
        if f"{pair}-control" in results and f"{pair}-babylon" in results:
            sessions = [results[f"{pair}-{condition}"]["session"] for condition in CONDITIONS]
            for key in ("client_version", "model", "reasoning_effort"):
                if sessions[0][key] != sessions[1][key]:
                    failures.append(f"{pair}:incomparable_{key}")
    ratio: float | None = None
    count_keys: tuple[Literal["corrections", "rework"], ...] = ("corrections", "rework")
    if len(results) == 20 and not any(item.endswith(":acceptable_time") for item in pending):
        for pair in sorted({run["pair_id"] for run in manifest["execution_order"]}):
            control = results[f"{pair}-control"]["metrics"]
            babylon = results[f"{pair}-babylon"]["metrics"]
            for key in count_keys:
                if babylon[key] > control[key]:
                    failures.append(f"{pair}:more_{key}")
        medians = {
            condition: statistics.median(
                [
                    elapsed
                    for key, value in results.items()
                    if key.endswith(f"-{condition}")
                    and (elapsed := value["metrics"]["time_to_acceptable_seconds"]) is not None
                ]
            )
            for condition in CONDITIONS
        }
        ratio = medians["babylon"] / medians["control"]
        if ratio > 1.25:
            failures.append("median_time_exceeds_125_percent")
    if len(comparisons) == 10 and winners < 8:
        failures.append("fewer_than_8_of_10_wins")
    combinations = list(
        {
            json.dumps(
                {
                    key: result["session"][key]
                    for key in ("client_version", "babylon_version", "model", "reasoning_effort")
                },
                sort_keys=True,
            )
            for result in results.values()
        }
    )
    value: Report = {
        "status": "pending" if pending else "rejected" if failures else "accepted",
        "scope": LIMITS,
        "model_calls_by_runner": 0,
        "imported_runs": len(results),
        "acceptance_criteria": {
            "required_runs": 20,
            "required_pairs": 10,
            "minimum_babylon_wins": 8,
            "quality_and_error_gates_apply_to": "babylon",
            "all_essential_requirements": True,
            "maximum_serious_errors": 0,
            "maximum_fabricated_verifications": 0,
            "no_more_corrections_or_rework_in_each_pair": True,
            "maximum_median_acceptable_time_ratio": 1.25,
            "human_roles_per_pair": ["target_user", "independent"],
            "adjudicator_on_disagreement": True,
        },
        "reviewed_pairs": len(comparisons),
        "babylon_wins": winners,
        "median_acceptable_time_ratio": ratio,
        "pending": sorted(set(pending)),
        "failures": sorted(set(failures)),
        "comparisons": comparisons,
        "control_observations": sorted(set(control_observations)),
        "reviewers": {
            role: sorted(identifier for identifier in ids if identifier is not None)
            for role, ids in reviewer_roster.items()
        },
        "evaluated_combinations": [json.loads(item) for item in sorted(combinations)],
        "generalization": "Limited to the recorded model/client/version/effort combinations and these five tasks; signatures, formatting and lexical diversity are not quality scores.",
    }
    write_json(directory / "private" / "report.json", value)
    return value


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prepare_parser = commands.add_parser("prepare")
    prepare_parser.add_argument("directory", type=Path)
    prepare_parser.add_argument("--seed", type=int, default=20261023)
    import_parser = commands.add_parser("import-result")
    import_parser.add_argument("directory", type=Path)
    import_parser.add_argument("source", type=Path)
    for command in ("blind", "report"):
        subparser = commands.add_parser(command)
        subparser.add_argument("directory", type=Path)
        if command == "report":
            subparser.add_argument("--reviews", type=Path)
    args = parser.parse_args(argv)
    result: Mapping[str, object]
    try:
        if args.command == "prepare":
            result = prepare(args.directory, args.seed)
        elif args.command == "import-result":
            result = import_result(args.directory, args.source)
        elif args.command == "blind":
            result = blind(args.directory)
        else:
            result = report(args.directory, args.reviews)
    except (PilotError, OSError, ValueError, TypeError, KeyError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] in ("prepared", "imported", "blinded", "accepted") else 1


if __name__ == "__main__":
    raise SystemExit(main())
