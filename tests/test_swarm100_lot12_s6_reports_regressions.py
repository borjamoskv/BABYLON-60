"""S6: distinguish observed data, unexecuted controls and simulation."""

from __future__ import annotations

import asyncio
import importlib.util
import json
import shutil
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> Any:
    """Load scripts whose differing runtime APIs are the subject of these fixtures."""
    qualified = f"lot12_{name}"
    spec = importlib.util.spec_from_file_location(qualified, ROOT / "scripts/c5_sharur" / f"{name}.py")
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[qualified] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))


def corpus():
    return SimpleNamespace(
        artifacts=[],
        artifacts_by_ext={},
        scripts_in_brain=[],
        target_files_mutated={},
        large_files=[],
        conv_dirs=[],
        secret_matches={},
        touch_id_invocations=0,
        learned_preferences=[],
        learned_workspace_facts=[],
        transcripts=[],
        total_lines=0,
        user_messages=[],
        planner_messages=[],
        tool_calls_counter={},
        total_brain_bytes=0,
        entropy_samples=[],
    )


def test_c0328_reproduction():
    m = load("sharur_100_conversation_reporters")
    r = asyncio.run(m.run_cohort_5(99, corpus(), asyncio.Semaphore(1)))
    assert r.verdict == "NOT_EXECUTED"
    assert r.metrics.get("certification") != "ATTESTED_C5_REAL"
    assert r.metrics.get("health_index") is None


def test_c0343_reproduction(tmp_path):
    m = load("sharur_100_full_spectrum_auditor")
    m.REPO_ROOT = tmp_path
    r = asyncio.run(m.audit_cohort_ring0(2, asyncio.Semaphore(1)))
    assert r.verdict == "NOT_EXECUTED"
    assert "certificadas" not in r.details


def test_c0354_reproduction(tmp_path):
    m = load("sharur_100_swarm_execution")
    m.REPO_ROOT = tmp_path
    sitrep, _ = asyncio.run(m.execute_sharur_100())
    assert sitrep.get("simulation") is True
    assert sitrep["passed_agents"] == 0
    assert sitrep["critical_fixes_attested"] == []
    assert all(r["status"] == "NOT_EXECUTED" for r in sitrep["results"])


@pytest.mark.parametrize("agent_id", [64, 65, 67, 68, 69, 70, 72, 73, 74, 76, 77, 78, 79, 999])
def test_reporter_topology_unperformed_controls(agent_id):
    m = load("sharur_100_conversation_reporters")
    r = asyncio.run(m.run_cohort_4(agent_id, corpus(), asyncio.Semaphore(1)))
    assert r.verdict == "NOT_EXECUTED"
    assert r.metrics["check_status"] == "NOT_EXECUTED"


@pytest.mark.parametrize("agent_id", [83, 84, 85, 86, 88, 89, 90, 91, 94, 95, 96, 97, 98, 99, 999])
def test_reporter_security_unperformed_controls(agent_id):
    m = load("sharur_100_conversation_reporters")
    r = asyncio.run(m.run_cohort_5(agent_id, corpus(), asyncio.Semaphore(1)))
    assert r.verdict == "NOT_EXECUTED"
    assert r.metrics["check_status"] == "NOT_EXECUTED"


def test_reporter_observations_and_actual_thresholds():
    m = load("sharur_100_conversation_reporters")
    c = corpus()
    c.artifacts = ["a", "b"]
    c.secret_matches = {"ssh": 1, "github": 2}
    c.touch_id_invocations = 7
    r = asyncio.run(m.run_cohort_4(60, c, asyncio.Semaphore(1)))
    assert r.verdict == "OBSERVED" and r.metrics["total_artifacts"] == 2
    security = asyncio.run(m.run_cohort_5(82, c, asyncio.Semaphore(1)))
    assert security.verdict == "FAIL"
    hardware = asyncio.run(m.run_cohort_5(87, c, asyncio.Semaphore(1)))
    assert hardware.verdict == "OBSERVED"
    assert hardware.metrics["hardware_verified"] is False


def test_reporter_aggregate_no_fabricated_score(tmp_path):
    m = load("sharur_100_conversation_reporters")
    c = corpus()
    results = [
        asyncio.run(m.run_cohort_4(60, c, asyncio.Semaphore(1))),
        asyncio.run(m.run_cohort_5(99, c, asyncio.Semaphore(1))),
    ]
    s = m.compile_swarm_sitrep(c, results, 0.1)
    assert s.total_agents == 2 and s.cohorts_executed == 2
    assert s.passed_agents == 0 and s.not_executed_agents == 1 and s.observed_agents == 1
    assert s.exergy_score is None
    assert s.certification == "NOT_ATTESTED"
    scripts, audit = tmp_path / "scripts", tmp_path / "audit"
    scripts.mkdir()
    audit.mkdir()
    m.emit_sitrep_reports(s, scripts, audit)
    a = json.loads((scripts / "sharur_100_conversations_sitrep.json").read_text())
    b = json.loads((audit / "sharur_100_conversations_sitrep.json").read_text())
    assert a == b == asdict(s)
    assert "NOT_EXECUTED=1" in m.render_markdown_report(s)
    assert "NOT_ATTESTED" in m.render_html_report(s)


def test_reporter_html_escapes_untrusted_fields():
    m = load("sharur_100_conversation_reporters")
    c = corpus()
    malicious = m.AgentResult(
        agent_id=1,
        cohort_id=1,
        cohort_name='<img src=x onerror="alert(1)">',
        target="<script>alert('target')</script>",
        verdict="WARN<script>",
        exergy_ms=1.0,
        entropy_bits=None,
        details='"><svg onload=alert(2)>',
    )
    s = m.compile_swarm_sitrep(c, [malicious], 0.1)
    s.timestamp = "2026-11-06<script>"
    s.certification = "NOT_ATTESTED<b>"
    rendered = m.render_html_report(s)
    assert "<script>" not in rendered
    assert "<svg" not in rendered
    assert '<img src=x' not in rendered
    assert "&lt;script&gt;alert(&#x27;target&#x27;)&lt;/script&gt;" in rendered
    assert "&quot;&gt;&lt;svg onload=alert(2)&gt;" in rendered


@pytest.mark.parametrize(
    "function,agent_id",
    [
        ("audit_cohort_ring0", 7),
        ("audit_cohort_formal", 23),
        ("audit_cohort_linguistics", 42),
        ("audit_cohort_topology", 64),
        ("audit_cohort_devsecops", 86),
    ],
)
def test_full_spectrum_unknown_in_every_cohort(tmp_path, function, agent_id):
    m = load("sharur_100_full_spectrum_auditor")
    m.REPO_ROOT = tmp_path
    r = asyncio.run(getattr(m, function)(agent_id, asyncio.Semaphore(1)))
    assert r.verdict == "NOT_EXECUTED"
    assert r.entropy_bits is None


def test_full_spectrum_entropy_requires_measured_input(tmp_path):
    m = load("sharur_100_full_spectrum_auditor")
    m.REPO_ROOT = tmp_path
    absent = asyncio.run(m.audit_cohort_linguistics(41, asyncio.Semaphore(1)))
    assert absent.verdict == "NOT_EXECUTED" and absent.entropy_bits is None
    for text, expected in [("", 0.0), ("aaaa", 0.0), ("abab", 1.0), ("abcd", 2.0)]:
        r = asyncio.run(m.audit_cohort_linguistics(41, asyncio.Semaphore(1), text=text))
        assert r.verdict == "OBSERVED"
        assert r.entropy_bits == expected == m.calc_shannon_entropy(text)


def test_full_spectrum_catalog_difference_not_pass(tmp_path):
    m = load("sharur_100_full_spectrum_auditor")
    m.REPO_ROOT = tmp_path
    m.SKILLS_JSON_REPO, m.SKILLS_JSON_GLOBAL = tmp_path / "repo.json", tmp_path / "global.json"
    m.SKILLS_JSON_REPO.write_text('{"entries":["one"]}')
    m.SKILLS_JSON_GLOBAL.write_text('{"entries":["two"]}')
    r = asyncio.run(m.audit_cohort_topology(67, asyncio.Semaphore(1)))
    assert r.verdict == "WARN"
    m.SKILLS_JSON_REPO.write_text('{"entries":[{"flag":true,"zero":false}]}')
    m.SKILLS_JSON_GLOBAL.write_text('{"entries":[{"flag":1,"zero":0}]}')
    assert asyncio.run(m.audit_cohort_topology(67, asyncio.Semaphore(1))).verdict == "WARN"
    m.SKILLS_JSON_GLOBAL.write_text(m.SKILLS_JSON_REPO.read_text())
    assert asyncio.run(m.audit_cohort_topology(67, asyncio.Semaphore(1))).verdict == "PASS"
    m.SKILLS_JSON_GLOBAL.write_text("not JSON")
    assert asyncio.run(m.audit_cohort_topology(67, asyncio.Semaphore(1))).verdict == "FAIL"


def test_full_spectrum_runtime_checks_and_serialization(tmp_path):
    m = load("sharur_100_full_spectrum_auditor")
    m.REPO_ROOT = tmp_path
    m.SKILLS_DIR_GLOBAL = tmp_path / "skills"
    m.SKILLS_JSON_REPO = tmp_path / "repo.json"
    m.SKILLS_JSON_GLOBAL = tmp_path / "global.json"
    (tmp_path / "Cargo.toml").write_text("[workspace]\n")
    (tmp_path / ".git").mkdir()
    (tmp_path / "bad.vtt").write_text("fixture")
    out = tmp_path / "out.json"
    s = asyncio.run(m.run_100_agents_audit(output_json=out))
    assert s.total_agents == len(s.results) == 100
    assert s.not_executed_agents > 80
    assert s.passed_agents + s.warned_agents + s.failed_agents + s.observed_agents + s.not_executed_agents == 100
    assert s.certification == "NOT_ATTESTED"
    assert next(r for r in s.results if r.agent_id == 85).verdict == "WARN"
    assert json.loads(out.read_text()) == asdict(s)


def test_swarm_simulation_has_honest_counts_and_no_measurements(tmp_path):
    m = load("sharur_100_swarm_execution")
    m.REPO_ROOT = tmp_path
    s, duration = asyncio.run(m.execute_sharur_100())
    assert duration >= 0
    assert s["total_agents"] == len(s["results"]) == 100
    assert s["not_executed_agents"] == 100
    assert s["passed_agents"] == s["warned_agents"] == s["failed_agents"] == 0
    assert s["certification"] == "NOT_ATTESTED"
    assert s["claims_manifest"] is None
    assert all(r["simulation"] is True and r["exergy_score"] is None for r in s["results"])
    out = tmp_path / "scripts/c5_legion/legion_100_audit_sitrep.json"
    assert json.loads(out.read_text()) == s


@pytest.mark.parametrize("name", ["sharur_100_full_spectrum_auditor", "sharur_100_swarm_execution"])
def test_cli_copied_tree_stays_uncertified(tmp_path, name):
    script = tmp_path / "scripts/c5_sharur" / f"{name}.py"
    script.parent.mkdir(parents=True)
    shutil.copyfile(ROOT / "scripts/c5_sharur" / f"{name}.py", script)
    result = subprocess.run([sys.executable, str(script)], cwd=tmp_path, capture_output=True, text=True, timeout=20)
    assert result.returncode == 0, result.stderr
    assert "NOT_ATTESTED" in result.stdout
    assert "Silicio verificado" not in result.stdout
    report = json.loads((tmp_path / "scripts/c5_legion/legion_100_audit_sitrep.json").read_text())
    assert report["certification"] == "NOT_ATTESTED"
    if name.endswith("swarm_execution"):
        assert report["simulation"] is True and report["passed_agents"] == 0
    else:
        assert report["not_executed_agents"] > 80
