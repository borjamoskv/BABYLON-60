#!/usr/bin/env python3
"""Inventory selected files and report unimplemented audit controls explicitly.

These concurrent reporters do not execute hardware, formal, network or physical
checks. PASS applies only to the narrow file/content predicate stated in details.
"""

from __future__ import annotations

import asyncio
import json
import math
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR_BABYLON = REPO_ROOT / ".agents" / "skills"
SKILLS_DIR_GLOBAL = Path.home() / ".gemini" / "config" / "skills"
SKILLS_JSON_REPO = REPO_ROOT / "docs" / "skills.json"
SKILLS_JSON_GLOBAL = SKILLS_DIR_GLOBAL / "skills.json"


@dataclass
class AgentAuditResult:
    agent_id: int
    cohort: str
    target: str
    verdict: str
    exergy_ms: float  # Historical field: measured reporter wall-clock milliseconds only.
    details: str
    entropy_bits: float | None = None


@dataclass
class SwarmSitrep:
    timestamp: str
    total_agents: int = 100
    cohorts_executed: int = 5
    passed_agents: int = 0
    warned_agents: int = 0
    failed_agents: int = 0
    not_executed_agents: int = 0
    observed_agents: int = 0
    certification: str = "NOT_ATTESTED"
    evidence_scope: str = "STATED_FILE_AND_CONTENT_PREDICATES_ONLY"
    wall_clock_seconds: float = 0.0
    results: list[AgentAuditResult] = field(default_factory=list)


def calc_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    counts: dict[str, int] = {}
    for char in text:
        counts[char] = counts.get(char, 0) + 1
    total = len(text)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def _result(
    agent_id: int,
    cohort: str,
    target: str,
    start: float,
    verdict: str = "NOT_EXECUTED",
    details: str = "Control no ejecutado; sin comprobador implementado.",
    entropy: float | None = None,
) -> AgentAuditResult:
    return AgentAuditResult(
        agent_id, cohort, target, verdict, round((time.perf_counter() - start) * 1000, 3), details, entropy
    )


async def audit_cohort_ring0(agent_id: int, sem: asyncio.Semaphore) -> AgentAuditResult:
    async with sem:
        start = time.perf_counter()
        target = f"Ring-0 / hardware control {agent_id:03d}"
        if agent_id == 1:
            files = list(REPO_ROOT.glob("**/shared_manifest*.rs")) + list(REPO_ROOT.glob("**/c5_shared_manifest*.py"))
            return _result(
                agent_id,
                "COHORT-1-RING0",
                "Shared manifest file census",
                start,
                "OBSERVED",
                f"Localizados {len(files)} nombres de archivo; layout y hardware NO_VERIFICADO.",
            )
        if agent_id == 10:
            present = (REPO_ROOT / "Cargo.toml").is_file()
            return _result(
                agent_id,
                "COHORT-1-RING0",
                "Cargo.toml file presence",
                start,
                "PASS" if present else "WARN",
                f"Cargo.toml is_file={present}; no valida workspace ni compilación.",
            )
        return _result(agent_id, "COHORT-1-RING0", target, start)


async def audit_cohort_formal(agent_id: int, sem: asyncio.Semaphore) -> AgentAuditResult:
    async with sem:
        start = time.perf_counter()
        if agent_id == 21:
            files = list((REPO_ROOT / "proof" / "lean").glob("*.lean"))
            return _result(
                agent_id,
                "COHORT-2-FORMAL",
                "Lean source file census",
                start,
                "OBSERVED",
                f"Localizados {len(files)} archivos .lean; no se compiló ni validó ninguna prueba.",
            )
        return _result(agent_id, "COHORT-2-FORMAL", f"Formal control {agent_id:03d}", start)


async def audit_cohort_linguistics(agent_id: int, sem: asyncio.Semaphore, text: str | None = None) -> AgentAuditResult:
    async with sem:
        start = time.perf_counter()
        cohort = "COHORT-3-LINGUISTICS"
        target = f"Linguistic control {agent_id:03d}"
        try:
            if agent_id == 41 and text is not None:
                entropy = calc_shannon_entropy(text)
                return _result(
                    agent_id,
                    cohort,
                    "Supplied text character Shannon entropy",
                    start,
                    "OBSERVED",
                    f"Entropía de {len(text)} caracteres suministrados: {entropy:.6f} bits/caracter; sin inferencia física.",
                    entropy,
                )
            if agent_id == 44:
                path = SKILLS_DIR_GLOBAL / "github-architect" / "SKILL.md"
                found = path.is_file() and "Strict English Invariant" in path.read_text(encoding="utf-8")
                return _result(
                    agent_id,
                    cohort,
                    "Literal Strict English Invariant presence",
                    start,
                    "PASS" if found else "WARN",
                    f"Literal encontrado={found}; no comprueba el idioma del documento.",
                )
            if agent_id == 45:
                present = (SKILLS_DIR_GLOBAL / "github-architect" / "references" / "rubric.md").is_file()
                return _result(
                    agent_id,
                    cohort,
                    "Rubric file presence",
                    start,
                    "OBSERVED",
                    f"rubric.md is_file={present}; idioma NO_VERIFICADO.",
                )
            if agent_id == 47:
                path = REPO_ROOT / "docs" / "03_guides" / "guide_skill_arsenal_taxonomy.md"
                found = path.is_file() and "NIVEL S — KERNEL SOBERANO" in path.read_text(encoding="utf-8")
                return _result(
                    agent_id,
                    cohort,
                    "Literal taxonomy header presence",
                    start,
                    "PASS" if found else "WARN",
                    f"Encabezado literal encontrado={found}; no valida taxonomía completa.",
                )
        except (OSError, UnicodeError):
            return _result(agent_id, cohort, target, start, "FAIL", "No se pudo leer el archivo seleccionado.")
        return _result(agent_id, cohort, target, start)


def _catalog_entries(path: Path) -> list[object]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("entries"), list):
        raise ValueError("Catalog must contain an entries list")
    return data["entries"]


def _strict_json_equal(left: object, right: object) -> bool:
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        assert isinstance(right, dict)
        return set(left.keys()) == set(right.keys()) and all(
            _strict_json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        assert isinstance(right, list)
        return len(left) == len(right) and all(
            _strict_json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


async def audit_cohort_topology(agent_id: int, sem: asyncio.Semaphore) -> AgentAuditResult:
    async with sem:
        start = time.perf_counter()
        cohort = "COHORT-4-TOPOLOGY"
        target = f"Topology control {agent_id:03d}"
        if agent_id == 66:
            present = (REPO_ROOT / "scripts" / "c5_skills_ontology" / "c5_skill_router.py").is_file()
            return _result(
                agent_id,
                cohort,
                "Router source file presence",
                start,
                "OBSERVED",
                f"Router is_file={present}; no se ejecutó ni validó integración CLI.",
            )
        if agent_id == 67:
            if not SKILLS_JSON_REPO.is_file() or not SKILLS_JSON_GLOBAL.is_file():
                return _result(
                    agent_id,
                    cohort,
                    "Catalog entries equality",
                    start,
                    "NOT_EXECUTED",
                    "Falta uno de los dos catálogos.",
                )
            try:
                repo = _catalog_entries(SKILLS_JSON_REPO)
                global_ = _catalog_entries(SKILLS_JSON_GLOBAL)
            except (OSError, UnicodeError, ValueError):
                return _result(
                    agent_id, cohort, "Catalog entries equality", start, "FAIL", "Catálogo ilegible o esquema inválido."
                )
            equal = _strict_json_equal(repo, global_)
            return _result(
                agent_id,
                cohort,
                "Catalog entries equality",
                start,
                "PASS" if equal else "WARN",
                f"Igualdad JSON de entries={equal}; tamaños {len(repo)}/{len(global_)}; no valida ejecución de skills.",
            )
        return _result(agent_id, cohort, target, start)


async def audit_cohort_devsecops(agent_id: int, sem: asyncio.Semaphore) -> AgentAuditResult:
    async with sem:
        start = time.perf_counter()
        cohort = "COHORT-5-DEVSECOPS"
        target = f"DevSecOps control {agent_id:03d}"
        if agent_id == 81:
            git_dir = REPO_ROOT / ".git"
            if not git_dir.is_dir():
                return _result(
                    agent_id,
                    cohort,
                    "Git lock file census",
                    start,
                    details="No hay directorio .git en esta raíz; locks NO_VERIFICADO.",
                )
            locks = list(git_dir.glob("*.lock"))
            return _result(
                agent_id,
                cohort,
                "Git lock file census",
                start,
                "WARN" if locks else "PASS",
                f"Encontrados {len(locks)} archivos .lock; no determina antigüedad ni dueño.",
            )
        if agent_id == 84:
            present = (Path.home() / "Music").is_dir()
            return _result(
                agent_id,
                cohort,
                "Home Music directory presence",
                start,
                "OBSERVED",
                f"Music is_dir={present}; no comprueba ubicación de activos.",
            )
        if agent_id == 85:
            dumps = list(REPO_ROOT.glob("**/*.vtt")) + list(REPO_ROOT.glob("**/*.srt"))
            return _result(
                agent_id,
                cohort,
                "VTT/SRT file census",
                start,
                "WARN" if dumps else "PASS",
                f"Encontrados {len(dumps)} archivos .vtt/.srt; no comprueba Git ni bases de datos.",
            )
        if agent_id == 89:
            present = (REPO_ROOT / "docs" / "00_index.md").is_file()
            return _result(
                agent_id,
                cohort,
                "Documentation index file presence",
                start,
                "OBSERVED",
                f"Índice is_file={present}; enlaces y contenido NO_VERIFICADO.",
            )
        return _result(agent_id, cohort, target, start)


async def run_100_agents_audit(output_json: Path | None = None) -> SwarmSitrep:
    sem = asyncio.Semaphore(25)
    start = time.perf_counter()
    functions = [
        audit_cohort_ring0,
        audit_cohort_formal,
        audit_cohort_linguistics,
        audit_cohort_topology,
        audit_cohort_devsecops,
    ]
    tasks = [asyncio.create_task(functions[(agent_id - 1) // 20](agent_id, sem)) for agent_id in range(1, 101)]
    results = await asyncio.gather(*tasks)
    sitrep = SwarmSitrep(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        total_agents=len(results),
        cohorts_executed=len({r.cohort for r in results}),
        passed_agents=sum(r.verdict == "PASS" for r in results),
        warned_agents=sum(r.verdict == "WARN" for r in results),
        failed_agents=sum(r.verdict == "FAIL" for r in results),
        observed_agents=sum(r.verdict == "OBSERVED" for r in results),
        not_executed_agents=sum(r.verdict == "NOT_EXECUTED" for r in results),
        wall_clock_seconds=round(time.perf_counter() - start, 4),
        results=results,
    )
    if output_json is not None:
        output_json.parent.mkdir(parents=True, exist_ok=True)
        output_json.write_text(json.dumps(asdict(sitrep), indent=2, ensure_ascii=False), encoding="utf-8")
    return sitrep


def main() -> None:
    out = REPO_ROOT / "scripts" / "c5_legion" / "legion_100_audit_sitrep.json"
    sitrep = asyncio.run(run_100_agents_audit(output_json=out))
    print(
        f"Reporters: {sitrep.total_agents}; PASS={sitrep.passed_agents}; WARN={sitrep.warned_agents}; FAIL={sitrep.failed_agents}"
    )
    print(f"OBSERVED={sitrep.observed_agents}; NOT_EXECUTED={sitrep.not_executed_agents}; {sitrep.certification}")
    print(f"Reporter wall-clock: {sitrep.wall_clock_seconds:.4f}s; output: {out}")


if __name__ == "__main__":
    main()
