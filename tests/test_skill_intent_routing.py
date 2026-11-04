"""Behavioral routing checks use requests, not generated descriptions as an oracle."""

import json
from pathlib import Path
import pytest
from tools.skill_library.router import select

CATALOG = Path(__file__).absolute().parents[1] / "tools/skill_library/catalog.json"


def records():
    data = json.loads(CATALOG.read_text())
    result = []
    for name, capability in data["capabilities"]["global"].items():
        intent = dict(capability["intent"])
        intent.setdefault("actions", data["policy"]["default_actions"])
        result.append(dict(name=name, aliases=capability["aliases"], intent=intent))
    return result


@pytest.mark.parametrize(
    "query,expected",
    [
        ("Audita si tengo skills con activaciones que se pisan", "cortex-skill-auditor"),
        ("Revisa mis imports rotos sin ejecutar el proyecto", "existence-gap-audit"),
        ("Comprueba los paquetes inexistentes en este proyecto", "existence-gap-audit"),
        ("Combina estas skills en un pipeline", "cortex-skill-composer"),
        ("Arregla las cuotas Gemini API", "c5-gemini-api-2026-standards"),
        ("Diagnostica las redirecciones de Yahoo en Chrome", "c5-browser-forensics-and-extension-triage"),
        ("Formaliza este teorema en Lean 4", "c5-lean4-axiomatic-orchestrator"),
        ("Revisa este manuscrito científico", "c5-academic-peer-reviewer"),
        ("Corrige el autoescape del exportador HTML", "c5-html-report-injection-audit"),
        ("Abre Safari y busca el informe", "safari-browser-agent"),
        ("Renderiza el vídeo con Remotion", "youtube-remotion-sota"),
    ],
)
def test_requested_action_and_domain_select_capability(query, expected):
    assert expected in {r["name"] for r in select(query, records())}


@pytest.mark.parametrize(
    "query",
    [
        "sigue",
        "itera",
        "auditoría",
        "No uses /cortex-skill-auditor",
        "No audites las skills",
        "El documento dice «auditar skills». Solo corrige la ortografía.",
        "Chrome es mi navegador favorito",
        "Las skills están en esa carpeta",
        "Genera una página HTML bonita",
        "El artículo menciona Lean 4",
    ],
)
def test_mentions_and_negated_actions_do_not_activate(query):
    assert select(query, records()) == []


def test_continuation_requires_explicit_previous_objective():
    assert select("sigue", records()) == []
    assert "cortex-skill-auditor" in {
        r["name"] for r in select("sigue", records(), context="Audita mis skills por solapamiento")
    }


def test_new_request_does_not_inherit_unrelated_prior_context():
    assert select("Escribe una invitación de cumpleaños", records(), context="Audita mis skills") == []


def test_negation_in_one_clause_does_not_cancel_another_request():
    names = {r["name"] for r in select("No audites las skills; corrige los imports rotos", records())}
    assert "cortex-skill-auditor" not in names
    assert "existence-gap-audit" in names
