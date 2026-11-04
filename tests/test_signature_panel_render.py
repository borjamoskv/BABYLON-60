"""A response signature contains only sourced fields from its own payload."""

from __future__ import annotations

from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from scripts.guards.render_signature_panel import render_panel
from scripts.guards.verify_active_topology import validate_text


SCRIPT = Path(__file__).absolute().parents[1] / "scripts/guards/render_signature_panel.py"
TEMPLATE = """<article data-signature-version="2">
<span data-signature-field="TOPOLOGÍA ACTIVA">MOSKV-1</span>
<span data-signature-field="LLM">{{MODEL}}</span>
<span>{{MODEL_CONTEXT}}</span>{{EFFORT_BLOCK}}
{{CONTEXT_ROWS}}
<details><summary>Fuentes</summary>
<span data-signature-source="LLM">{{MODEL_SOURCE}}</span>{{SOURCE_ROWS}}</details>
<time datetime="{{OBSERVED_AT}}">{{OBSERVED_LABEL}}</time></article>"""


def _payload() -> dict[str, object]:
    return {
        "model": "GPT-6",
        "model_source": "Cabecera vigente del entorno",
        "observed_at": "2026-10-18T00:32:51+02:00",
    }


class PanelParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.tags: list[str] = []
        self.fields: list[str] = []
        self.sources: list[str] = []
        self.hidden_fields: list[str] = []
        self.details_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        if tag == "details":
            self.details_depth += 1
        for key, value in attrs:
            if key == "data-signature-field" and value is not None:
                self.fields.append(value)
                if self.details_depth:
                    self.hidden_fields.append(value)
            if key == "data-signature-source" and value is not None:
                self.sources.append(value)

    def handle_endtag(self, tag: str) -> None:
        if tag == "details":
            self.details_depth -= 1


def test_minimal_signature_omits_unknown_effort_and_unmeasured_metrics() -> None:
    rendered = render_panel(_payload(), TEMPLATE)
    parsed = PanelParser()
    parsed.feed(rendered)
    assert parsed.fields == ["TOPOLOGÍA ACTIVA", "LLM"]
    assert parsed.sources == ["LLM"]
    assert 'class="s-context"' not in rendered
    assert "No evaluable" in rendered
    assert "18/10/2026 · 00:32 UTC+02:00" in rendered
    assert "No medido" not in rendered
    assert "No medida" not in rendered
    assert "No expuesto" not in rendered


def test_real_context_is_visible_once_and_its_sources_stay_separate() -> None:
    payload = _payload()
    payload.update(
        {
            "effort": {"value": "Medium", "source": "Metadatos vigentes"},
            "verification": {"value": "12 pruebas aprobadas", "source": "pytest.log"},
            "changes": {"value": "2 archivos modificados", "source": "git-status.txt"},
            "limits": {"value": "Sin comprobación visual", "source": "Informe de ejecución"},
            "thermal": {"value": "Estado nominal", "source": "NSProcessInfo observado en este turno"},
            "lexical": {"value": "7500", "source": "c5-lexical-v2, cuerpo actual"},
            "mutation": {"value": "Ninguna (cambios locales)", "source": "HEAD observado en el turno"},
        }
    )
    rendered = render_panel(payload, TEMPLATE)
    parsed = PanelParser()
    parsed.feed(rendered)
    fields = [
        "LLM",
        "MODO COGNITIVO",
        "VERIFICACIÓN",
        "CAMBIOS",
        "LÍMITES",
        "RÉGIMEN TÉRMICO",
        "EXERGÍA INFORMATIVA",
        "MUTACIÓN CAUSAL",
    ]
    assert parsed.fields == ["TOPOLOGÍA ACTIVA", *fields]
    assert parsed.sources == fields
    assert parsed.hidden_fields == []
    assert rendered.count("12 pruebas aprobadas") == 1
    assert rendered.count("Sin comprobación visual") == 1
    assert "pytest.log" in rendered.split("<details>", 1)[1]


def test_html_in_all_untrusted_values_is_text_and_never_a_template() -> None:
    payload = _payload()
    malicious = '<script>alert("x")</script>&\' {{MODEL}}'
    for field in ("model", "model_source", "model_context"):
        payload[field] = malicious
    for field in ("effort", "verification", "changes", "limits", "thermal", "lexical", "mutation"):
        payload[field] = {"value": malicious, "source": malicious}
    rendered = render_panel(payload, TEMPLATE)
    parsed = PanelParser()
    parsed.feed(rendered)
    assert "script" not in parsed.tags
    assert "<script>" not in rendered
    assert rendered.count("{{MODEL}}") == 17
    assert rendered.count("&lt;script&gt;") == 17
    assert "&amp;&#x27;" in rendered


@pytest.mark.parametrize("field", ["model", "model_source", "observed_at"])
def test_required_fields_cannot_be_missing(field: str) -> None:
    payload = _payload()
    del payload[field]
    with pytest.raises(ValueError, match=field):
        render_panel(payload, TEMPLATE)


@pytest.mark.parametrize("value", [None, 4, False, [], {}, "", "  \n"])
@pytest.mark.parametrize("field", ["model", "model_source", "model_context", "observed_at"])
def test_required_text_and_optional_context_reject_invalid_values(field: str, value: object) -> None:
    payload = _payload()
    payload[field] = value
    with pytest.raises(ValueError, match=field):
        render_panel(payload, TEMPLATE)


@pytest.mark.parametrize(
    "value",
    [
        None,
        1,
        True,
        "Medium",
        [],
        {},
        {"value": "Medium"},
        {"source": "Current turn"},
        {"value": "", "source": "Turn"},
        {"value": "Medium", "source": []},
        {"value": "Medium", "source": "Turn", "extra": "unknown"},
    ],
)
def test_optional_objects_reject_wrong_types_empty_or_unsourced_values(value: object) -> None:
    payload = _payload()
    payload["effort"] = value
    with pytest.raises(ValueError, match="effort"):
        render_panel(payload, TEMPLATE)


@pytest.mark.parametrize(
    "field,value",
    [
        ("effort", "No expuesto"),
        ("effort", " No expuesto (metadatos ausentes) "),
        ("thermal", "No medido"),
        ("thermal", "NO MEDIDA"),
        ("lexical", "No medida"),
        ("lexical", "No medido · sin cálculo"),
    ],
)
def test_absent_effort_and_unmeasured_metrics_must_be_omitted(field: str, value: str) -> None:
    payload = _payload()
    payload[field] = {"value": value, "source": "Turno actual"}
    with pytest.raises(ValueError, match=field):
        render_panel(payload, TEMPLATE)


@pytest.mark.parametrize(
    "stamp",
    [
        "2026-10-18",
        "2026-10-18T00:32:51",
        "yesterday",
        "2026-02-30T00:32:51+02:00",
        "2026-10-18T00:32:51+99:00",
        "2026-10-18 00:32:00+02:00",
        "2026-10-18T00:32:00+00:99",
    ],
)
def test_observation_requires_valid_date_and_explicit_timezone(stamp: str) -> None:
    payload = _payload()
    payload["observed_at"] = stamp
    with pytest.raises(ValueError, match="observed_at"):
        render_panel(payload, TEMPLATE)


def test_utc_timestamp_retains_its_own_timezone() -> None:
    payload = _payload()
    payload["observed_at"] = "2026-10-17T22:32:51Z"
    rendered = render_panel(payload, TEMPLATE)
    assert 'datetime="2026-10-17T22:32:51Z"' in rendered
    assert "17/10/2026 · 22:32 UTC" in rendered


def test_unknown_payload_keys_are_rejected() -> None:
    payload = _payload()
    payload["temperature_guess"] = "Warm"
    with pytest.raises(ValueError, match="temperature_guess"):
        render_panel(payload, TEMPLATE)


@pytest.mark.parametrize("with_context", [False, True])
def test_real_template_output_passes_response_guard(tmp_path: Path, with_context: bool) -> None:
    payload = _payload()
    if with_context:
        payload["changes"] = {"value": "2 archivos modificados", "source": "Estado de Git del turno"}
        payload["limits"] = {"value": "Sin publicación", "source": "Alcance solicitado"}
    rendered = render_panel(payload, SCRIPT.with_name("signature_panel.html").read_text(encoding="utf-8"))
    output = tmp_path / "real-signature.html"
    output.write_text(rendered, encoding="utf-8")
    response = "Respuesta.\n\nvisualize" + json.dumps({"path": str(output)}, ensure_ascii=False) + ""
    assert validate_text(response, response=True) == []


def _cli_files(tmp_path: Path) -> tuple[Path, Path, Path]:
    cli = tmp_path / "render_signature_panel.py"
    shutil.copyfile(SCRIPT, cli)
    cli.with_name("signature_panel.html").write_text(TEMPLATE, encoding="utf-8")
    payload = tmp_path / "turn.json"
    payload.write_text(json.dumps(_payload()), encoding="utf-8")
    return cli, payload, tmp_path / "signature.html"


def _run_cli(cli: Path, payload: Path, output: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(cli), str(payload), str(output)],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )


def test_cli_creates_a_new_signature_and_refuses_to_replace_it(tmp_path: Path) -> None:
    cli, payload, output = _cli_files(tmp_path)
    first = _run_cli(cli, payload, output)
    assert first.returncode == 0, first.stderr
    original = output.read_bytes()
    second_payload = _payload()
    second_payload["model"] = "Another model"
    payload.write_text(json.dumps(second_payload), encoding="utf-8")
    second = _run_cli(cli, payload, output)
    assert second.returncode != 0
    assert output.read_bytes() == original


def test_cli_rejects_symlink_input_without_creating_output(tmp_path: Path) -> None:
    cli, payload, output = _cli_files(tmp_path)
    link = tmp_path / "symlink.json"
    link.symlink_to(payload)
    result = _run_cli(cli, link, output)
    assert result.returncode != 0
    assert not output.exists()


def test_cli_rejects_symlink_output_without_modifying_target(tmp_path: Path) -> None:
    cli, payload, output = _cli_files(tmp_path)
    target = tmp_path / "existing.txt"
    target.write_text("preserved", encoding="utf-8")
    output.symlink_to(target)
    result = _run_cli(cli, payload, output)
    assert result.returncode != 0
    assert target.read_text(encoding="utf-8") == "preserved"


@pytest.mark.parametrize("document", ["[]", "null", "4", '{"model":"GPT-6",', '{"model":"GPT-6","model":"another"}'])
def test_cli_rejects_invalid_or_ambiguous_json(tmp_path: Path, document: str) -> None:
    cli, payload, output = _cli_files(tmp_path)
    payload.write_text(document, encoding="utf-8")
    result = _run_cli(cli, payload, output)
    assert result.returncode != 0
    assert not output.exists()
