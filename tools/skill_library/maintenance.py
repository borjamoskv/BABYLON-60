"""Generate, audit and distribute owned entries; never execute skill procedures."""

from dataclasses import asdict
import json
import os
from pathlib import Path
import shutil
import tempfile
from collections.abc import Iterable
from typing import TypedDict
from scripts.c5_skills_ontology.build_skill_library import SOURCE, build
from scripts.c5_quality_gates.freeze_skills_manifest import InventoryEntry, inventory
from scripts.c5_quality_gates.audit_skill_links import inspect as inspect_links
from scripts.c5_quality_gates.audit_semantic_contracts import scan_markdown_files
from tools.skill_library.checks.declarative import inspect as inspect_declarative


class _ReceiptTarget(TypedDict):
    environment: str
    destination: str
    stage: str
    backup: str
    names: list[str]
    before: dict[str, InventoryEntry]
    expected: dict[str, InventoryEntry]


class ReceiptTarget(_ReceiptTarget, total=False):
    prepared: str


class _Receipt(TypedDict):
    schema_version: int
    phase: str
    source: str
    targets: list[ReceiptTarget]


class Receipt(_Receipt, total=False):
    error: str


class _EnvironmentReport(TypedDict):
    skills: int
    checks: list[dict[str, object]]
    blocking_passed: bool
    status: str


class EnvironmentReport(_EnvironmentReport, total=False):
    distribution: dict[str, str | int]


class MaintenanceReport(TypedDict):
    schema_version: int
    operation: str
    environments: dict[str, EnvironmentReport]
    status: str


def write_json(path: Path, data: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".writing")
    with temporary.open("w") as stream:
        json.dump(data, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def signature(root: Path, names: Iterable[str]) -> dict[str, InventoryEntry]:
    present = {name for name in names if os.path.lexists(root / name)}
    if not present:
        return {}
    result = inventory(root, top_levels=present)["entries"]
    result.pop(".", None)
    return result


def audit_distribution(root: Path) -> EnvironmentReport:
    declarative = inspect_declarative(root)
    paths = sorted(root.rglob("SKILL.md")) + sorted(root.rglob("MODULE.md"))
    links = inspect_links([root], remote=False)
    broken = [f for f in links["findings"] if f["status"] == "broken"]
    semantic = [dict(asdict(v), file_path=str(v.file_path.relative_to(root))) for v in scan_markdown_files(paths)]
    catalog = json.loads((root / "skill_catalog.generated.json").read_text())
    route_errors: list[dict[str, str]] = []
    for table in root.glob("*/references/aliases.json"):
        for record in json.loads(table.read_text())["modules"]:
            relative = Path(record["module"])
            if relative.is_absolute() or ".." in relative.parts or not (table.parent.parent / relative).is_file():
                route_errors.append(
                    {"file": str(table.relative_to(root)), "module": str(relative), "rule": "unconfined-or-missing"}
                )
            if not record.get("intent", {}).get("topics") or not record.get("intent", {}).get("actions"):
                route_errors.append({"name": record["name"], "rule": "missing-contextual-intent"})
    legacy = [str(path.relative_to(root)) for path in paths if "/.gemini/config/skills/" in path.read_text()]
    checks: list[dict[str, object]] = [
        dict(declarative, blocking=True),
        {"check": "routes", "status": "fail" if route_errors else "pass", "blocking": True, "findings": route_errors},
        {
            "check": "legacy-resource-paths",
            "status": "fail" if legacy else "pass",
            "blocking": True,
            "findings": legacy,
        },
        {
            "check": "local-links",
            "status": "fail" if broken else "pass",
            "blocking": True,
            "links": links["links"],
            "findings": broken,
            "remote": {
                "status": "unverified",
                "unique_urls": links["unique_remote_urls"],
                "reason": "Not requested; no network access used",
            },
        },
        {
            "check": "semantic-contracts",
            "status": "fail" if semantic else "pass",
            "blocking": False,
            "findings": semantic,
            "method": "Independent lexical checker; findings require contextual review",
        },
    ]
    return {
        "skills": len(catalog["skills"]),
        "checks": checks,
        "blocking_passed": not any(c["blocking"] and c["status"] == "fail" for c in checks),
        "status": "fail" if any(c["status"] == "fail" for c in checks) else "pass",
    }


def restore(receipt: Receipt, receipt_path: Path) -> None:
    """Preserve later user changes and unrelated entries. Keep displaced release files."""
    if receipt["phase"] not in {"applying", "applied", "rolled-back"}:
        raise OSError("Rollback refused: receipt has no applied installation")
    # Validate all destinations before restoring any entry, including later deletions.
    for target in receipt["targets"]:
        destination, backup = Path(target["destination"]), Path(target["backup"])
        if any(name in {".", "..", ".system"} or "/" in name or "\\" in name for name in target["names"]):
            raise OSError("Rollback refused: invalid owned entry")
        if not destination.is_dir() or destination.is_symlink() or not backup.is_dir() or backup.is_symlink():
            raise OSError("Rollback refused: destination or backup is missing or linked")
        if receipt["phase"] == "applied" and signature(destination, target["names"]) != target["expected"]:
            raise OSError("Rollback refused: entry changed: " + str(destination))
        if receipt["phase"] == "applied" and signature(backup, target["names"]) != target["before"]:
            raise OSError("Rollback refused: backup changed: " + str(backup))
        if receipt["phase"] == "rolled-back":
            if signature(destination, target["names"]) != target["before"]:
                raise OSError("Rollback refused: entry changed: " + str(destination))
            continue
        for name in target["names"]:
            prior = any(path == name or path.startswith(name + "/") for path in target["before"])
            if os.path.lexists(backup / name) or (not prior and os.path.lexists(destination / name)):
                expected = {p: v for p, v in target["expected"].items() if p == name or p.startswith(name + "/")}
                if os.path.lexists(destination / name) and signature(destination, {name}) != expected:
                    raise OSError("Rollback refused: entry changed: " + str(destination / name))
    if receipt["phase"] == "rolled-back":
        return
    for target in reversed(receipt["targets"]):
        destination, backup = Path(target["destination"]), Path(target["backup"])
        displaced = backup / "_replaced-release"
        displaced.mkdir(exist_ok=True)
        for name in reversed(target["names"]):
            old = backup / name
            exists = os.path.lexists(destination / name)
            prior = any(path == name or path.startswith(name + "/") for path in target["before"])
            if os.path.lexists(old) or (not prior and exists):
                if exists:
                    current = signature(destination, {name})
                    expected = {p: v for p, v in target["expected"].items() if p == name or p.startswith(name + "/")}
                    if current != expected:
                        raise OSError("Rollback refused: entry changed: " + str(destination / name))
                    os.replace(destination / name, displaced / name)
                if os.path.lexists(old):
                    os.replace(old, destination / name)
        if signature(destination, target["names"]) != target["before"]:
            raise OSError("Rollback verification failed: " + target["environment"])
    receipt["phase"] = "rolled-back"
    write_json(receipt_path, receipt)


def maintain(targets: dict[str, Path], output: Path, apply: bool = False) -> MaintenanceReport:
    if not targets:
        raise ValueError("At least one target is required")
    output = output.absolute()
    physical_output = Path(os.path.realpath(output))
    physical_source = Path(os.path.realpath(SOURCE))
    if physical_output.is_relative_to(physical_source) or physical_source.is_relative_to(physical_output):
        raise ValueError("Source and output overlap")
    checked: list[Path] = []
    for environment, destination in targets.items():
        if environment not in {"codex", "antigravity", "workspace"}:
            raise ValueError("Unknown environment: " + environment)
        physical = Path(os.path.realpath(destination))
        if not destination.is_dir() or destination.is_symlink() or physical in {Path(physical.anchor), Path.home()}:
            raise ValueError("Destination must be an existing, non-linked skill directory")
        if physical.is_relative_to(physical_source) or physical_source.is_relative_to(physical):
            raise ValueError("Source and installation overlap")
        if physical.is_relative_to(physical_output) or physical_output.is_relative_to(physical):
            raise ValueError("Output and installation overlap")
        if any(physical.is_relative_to(other) or other.is_relative_to(physical) for other in checked):
            raise ValueError("Destinations overlap")
        checked.append(physical)
    output.mkdir(parents=True, exist_ok=False)
    source_before = inventory(SOURCE)
    receipt: Receipt = {"schema_version": 1, "phase": "staged", "source": str(SOURCE), "targets": []}
    report: MaintenanceReport = {
        "schema_version": 1,
        "operation": "apply" if apply else "check",
        "environments": {},
        "status": "staged",
    }
    for environment, destination in targets.items():
        if environment not in {"codex", "antigravity", "workspace"}:
            raise ValueError("Unknown environment: " + environment)
        destination = destination.absolute()
        if (
            not destination.is_dir()
            or destination.is_symlink()
            or destination == Path(destination.anchor)
            or destination == Path.home()
        ):
            raise ValueError("Destination must be an existing, non-linked skill directory")
        if destination.is_relative_to(SOURCE) or SOURCE.is_relative_to(destination):
            raise ValueError("Source and installation overlap")
        for previous in receipt["targets"]:
            other = Path(previous["destination"])
            if destination.is_relative_to(other) or other.is_relative_to(destination):
                raise ValueError("Destinations overlap")
        stage = output / environment
        build(stage, environment)
        names = sorted(p.name for p in stage.iterdir() if p.name != "__pycache__")
        if ".system" in names or any("/" in name or name in {".", ".."} for name in names):
            raise ValueError("Invalid owned entry")
        audit = audit_distribution(stage)
        report["environments"][environment] = audit
        backup = output / ("backup-" + environment)
        backup.mkdir()
        receipt["targets"].append(
            {
                "environment": environment,
                "destination": str(destination),
                "stage": str(stage),
                "backup": str(backup),
                "names": names,
                "before": signature(destination, names),
                "expected": signature(stage, names),
            }
        )
        write_json(output / ("manifest-" + environment + ".json"), inventory(stage))
    if inventory(SOURCE) != source_before:
        raise OSError("Canonical source changed while staging; regenerate before installing")
    report["status"] = "fail" if any(v["status"] == "fail" for v in report["environments"].values()) else "pass"
    write_json(output / "report.json", report)
    write_json(output / "receipt.json", receipt)
    if not all(v["blocking_passed"] for v in report["environments"].values()):
        raise ValueError("Blocking checks failed; no installation changed. See report.json")
    if not apply:
        return report
    for target in receipt["targets"]:
        if signature(Path(target["destination"]), target["names"]) != target["before"]:
            raise OSError("Installation changed after review; regenerate before installing")
        # Copies finish before any installed entry changes. Renames stay on the same filesystem.
        parent = Path(target["destination"]).parent
        prepared = Path(tempfile.mkdtemp(prefix=".skills-release-", dir=parent))
        backup = Path(tempfile.mkdtemp(prefix=".skills-backup-", dir=parent))
        target.update({"prepared": str(prepared), "backup": str(backup)})
        for name in target["names"]:
            source = Path(target["stage"]) / name
            if source.is_dir():
                shutil.copytree(source, prepared / name, symlinks=True)
            else:
                shutil.copy2(source, prepared / name, follow_symlinks=False)
        if signature(prepared, target["names"]) != target["expected"]:
            raise OSError("Prepared copy differs from reviewed release")
    receipt["phase"] = "applying"
    write_json(output / "receipt.json", receipt)
    try:
        for target in receipt["targets"]:
            destination, prepared, backup = map(Path, [target["destination"], target["prepared"], target["backup"]])
            for name in target["names"]:
                before = {p: v for p, v in target["before"].items() if p == name or p.startswith(name + "/")}
                if signature(destination, {name}) != before:
                    raise OSError("Entry changed while applying: " + str(destination / name))
                if os.path.lexists(destination / name):
                    os.replace(destination / name, backup / name)
                os.replace(prepared / name, destination / name)
            actual = signature(destination, target["names"])
            if actual != target["expected"]:
                raise OSError("Post-install hash verification failed: " + target["environment"])
            report["environments"][target["environment"]]["distribution"] = {
                "status": "pass",
                "entries": len(actual),
                "unmanaged_siblings": "preserved",
            }
    except (OSError, ValueError) as exc:
        receipt["error"] = str(exc)
        write_json(output / "receipt.json", receipt)
        restore(receipt, output / "receipt.json")
        raise
    receipt["phase"] = "applied"
    write_json(output / "receipt.json", receipt)
    write_json(output / "report.json", report)
    return report
