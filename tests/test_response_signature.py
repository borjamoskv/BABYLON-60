"""Consumer-facing guarantees for portable signatures; no kernel fixtures."""

import copy
from html import unescape
from html.parser import HTMLParser
import json
import re
import unittest

from babylon60.response_signature import (
    FIELD_NAMES,
    OPTIONAL_FIELD_NAMES,
    SIGNATURE_SCHEMA,
    normalize_signature,
    render_signature,
)


class SignatureDocument(HTMLParser):
    def __init__(self, document: str):
        super().__init__(convert_charrefs=True)
        self.fields: dict[str, str] = {}
        self.sources: dict[str, str] = {}
        self.tags: list[str] = []
        self.attributes: list[tuple[str, str | None]] = []
        self.active: tuple[dict[str, str], str] | None = None
        self.timestamp = ""
        self.feed(document)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        self.attributes.extend(attrs)
        attributes = dict(attrs)
        for attribute, destination in (("data-signature-field", self.fields), ("data-signature-source", self.sources)):
            field = attributes.get(attribute)
            if field:
                if field in destination:
                    raise AssertionError(f"Duplicate signature value: {field}")
                destination[field] = ""
                self.active = destination, field
        if tag == "time":
            self.timestamp = attributes.get("datetime") or ""

    def handle_data(self, data: str) -> None:
        if self.active:
            destination, field = self.active
            destination[field] += data

    def handle_endtag(self, tag: str) -> None:
        self.active = None


def observation() -> dict[str, object]:
    return {
        "schema_version": 1,
        "observed_at": "2026-10-18T09:30:00+02:00",
        "fields": {
            "LLM": "Modelo de prueba",
            "MODO COGNITIVO": "Esfuerzo de prueba",
            "TOPOLOGÍA ACTIVA": "MOSKV-1",
            "RÉGIMEN TÉRMICO": "Estado nominal; temperatura no medida",
            "EXERGÍA INFORMATIVA": "0.42; índice léxico de prueba",
            "MUTACIÓN CAUSAL": "Ninguna (artefacto de prueba)",
        },
        "sources": {field: f"Fuente de prueba: {field}" for field in FIELD_NAMES},
    }


class ResponseSignatureTests(unittest.TestCase):
    def test_unknown_observations_remain_unknown_and_are_not_shown_as_metrics(self) -> None:
        payload: dict[str, object] = {"observed_at": "2026-10-18T07:30:00Z"}
        normalized = normalize_signature(payload)
        self.assertEqual(
            normalized["fields"],
            dict(
                zip(
                    FIELD_NAMES,
                    (
                        "No expuesto",
                        "No expuesto",
                        "MOSKV-1",
                        "No medido",
                        "No medida",
                        "Ninguna",
                    ),
                )
            ),
        )
        self.assertEqual(normalized["sources"], dict.fromkeys(FIELD_NAMES, "No expuesta"))
        document = SignatureDocument(render_signature(payload, "html"))
        self.assertEqual(document.fields, {"LLM": "No expuesto", "TOPOLOGÍA ACTIVA": "MOSKV-1"})
        self.assertEqual(set(document.sources), set(document.fields))
        self.assertNotIn("s-metric", [value for name, value in document.attributes if name == "class"])
        self.assertEqual(document.timestamp, payload["observed_at"])

    def test_same_observations_and_sources_survive_all_formats(self) -> None:
        payload = observation()
        before = copy.deepcopy(payload)
        json_result = json.loads(render_signature(payload, "json"))
        html_result = SignatureDocument(render_signature(payload, "html"))
        self.assertEqual(html_result.fields, json_result["fields"])
        self.assertEqual(html_result.sources, json_result["sources"])
        self.assertEqual(html_result.timestamp, json_result["observed_at"])
        text_result = render_signature(payload, "text")
        markdown_result = render_signature(payload, "markdown")
        markdown_rows = markdown_result.splitlines()[2:8]
        for row, field in zip(markdown_rows, FIELD_NAMES):
            cells = [
                unescape(re.sub(r"\\([\\`*_{}\[\]()#+.!|~-])", r"\1", cell.strip()))
                for cell in re.split(r"(?<!\\)\|", row)[1:-1]
            ]
            self.assertEqual(cells, [field, json_result["fields"][field], json_result["sources"][field]])
            self.assertIn(f"[ {field} ]: {json_result['fields'][field]}", text_result)
            self.assertIn(f"  {field}: {json_result['sources'][field]}", text_result)
        self.assertEqual(payload, before)

    def test_html_treats_values_and_sources_as_text(self) -> None:
        attack = '<img src="https://invalid.test/a" onerror="alert(1)"> & </div><script>alert(2)</script>'
        payload: dict[str, object] = {
            "observed_at": "2026-10-18T07:30:00Z",
            "fields": {"LLM": attack},
            "sources": {"LLM": attack},
        }
        rendered = render_signature(payload, "html")
        document = SignatureDocument(rendered)
        self.assertEqual(document.fields["LLM"], attack)
        self.assertEqual(document.sources["LLM"], attack)
        self.assertNotIn("script", document.tags)
        self.assertNotIn("img", document.tags)
        self.assertFalse(any(name in {"src", "href", "onerror"} for name, _ in document.attributes))
        self.assertNotIn("$MODEL", rendered)

    def test_markdown_escapes_table_and_link_injection(self) -> None:
        attack = "[label](https://invalid.test) | `code` <img src=x> & *style*"
        payload: dict[str, object] = {
            "observed_at": "2026-10-18T07:30:00Z",
            "fields": {"LLM": attack},
            "sources": {"LLM": "test"},
        }
        result = render_signature(payload, "markdown")
        self.assertIn(r"\|", result)
        self.assertIn(r"\[label\]\(", result)
        self.assertNotIn("<img", result)
        self.assertEqual(len(re.split(r"(?<!\\)\|", result.splitlines()[2])), 5)

    def test_no_timestamp_is_fabricated_and_timezone_is_mandatory(self) -> None:
        for stamp in (None, "2026-10-18", "2026-10-18T09:30:00", "2026-02-30T09:30:00Z", "2026-10-18T09:30:00+00:60"):
            with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                render_signature({"observed_at": stamp}, "html")

    def test_claims_require_non_placeholder_sources(self) -> None:
        for field in FIELD_NAMES:
            if field == "TOPOLOGÍA ACTIVA":
                continue
            value = "abcdef0" if field == "MUTACIÓN CAUSAL" else "Observed value"
            for sources in ({}, {field: "No expuesta"}, {field: " no disponible "}):
                with self.subTest(field=field, sources=sources), self.assertRaises(ValueError):
                    normalize_signature(
                        {"observed_at": "2026-10-18T07:30:00Z", "fields": {field: value}, "sources": sources}
                    )

    def test_malformed_data_cannot_be_hidden_by_choosing_another_format(self) -> None:
        invalid: list[dict[str, object]] = [
            {"schema_version": True},
            {"schema_version": 2},
            {"extra": "ignored?"},
            {"fields": {"UNKNOWN": "value"}},
            {"sources": {"UNKNOWN": "value"}},
            {"fields": {"TOPOLOGÍA ACTIVA": "OTHER"}},
            {"fields": {"LLM": 0}},
            {"fields": {"LLM": ""}},
            {"fields": []},
            {"sources": []},
            {"fields": {"MUTACIÓN CAUSAL": "some work was done"}, "sources": {"MUTACIÓN CAUSAL": "test"}},
            {"fields": {"MUTACIÓN CAUSAL": "Ninguna (  )"}, "sources": {"MUTACIÓN CAUSAL": "test"}},
        ]
        for item in invalid:
            for format in ("html", "markdown", "text", "json"):
                with self.subTest(item=item, format=format), self.assertRaises(ValueError):
                    render_signature({"observed_at": "2026-10-18T07:30:00Z", **item}, format)

    def test_control_characters_and_unresolved_placeholders_are_rejected(self) -> None:
        for value in ("a\nb", "a\x1bb", "a\u202eb", "a\u2028b", "{{MODEL}}", "${VALUE}", "TODO", "..."):
            for component in ("fields", "sources"):
                with self.subTest(value=value, component=component), self.assertRaises(ValueError):
                    normalize_signature({"observed_at": "2026-10-18T07:30:00Z", component: {"LLM": value}})

    def test_each_render_is_independent(self) -> None:
        first = observation()
        result = render_signature(first, "html")
        empty = render_signature({"observed_at": "2026-10-18T08:00:00Z"}, "html")
        self.assertIn("Modelo de prueba", result)
        self.assertNotIn("Modelo de prueba", empty)
        self.assertNotIn("0.42", empty)
        self.assertEqual(render_signature(first, "html"), result)

    def test_optional_context_has_no_defaults_and_requires_its_own_source(self) -> None:
        minimal: dict[str, object] = {"observed_at": "2026-10-18T07:30:00Z"}
        fields_dict = normalize_signature(minimal).get("fields")
        self.assertTrue(
            isinstance(fields_dict, dict) and all(field not in fields_dict for field in OPTIONAL_FIELD_NAMES)
        )
        for field in OPTIONAL_FIELD_NAMES:
            with self.subTest(field=field), self.assertRaises(ValueError):
                normalize_signature({**minimal, "fields": {field: "Contexto observado"}})
        fields = dict.fromkeys(OPTIONAL_FIELD_NAMES, "Contexto observado")
        sources = dict.fromkeys(OPTIONAL_FIELD_NAMES, "Comprobación del turno")
        payload = {**minimal, "fields": fields, "sources": sources}
        rendered = render_signature(payload, "html")
        document = SignatureDocument(rendered)
        for field in OPTIONAL_FIELD_NAMES:
            self.assertEqual(document.fields[field], fields[field])
            self.assertEqual(document.sources[field], sources[field])
            self.assertIn(field, render_signature(payload, "text").split("[ LLM ]:")[0])
            self.assertIn(field, render_signature(payload, "markdown"))
        self.assertEqual(len(render_signature(payload, "text").splitlines()[-6:]), 6)
        self.assertNotIn("data-signature-field", rendered.split("<details>")[1])

    def test_transport_schema_is_json_and_unsupported_renderers_fail(self) -> None:
        schema = json.loads(json.dumps(SIGNATURE_SCHEMA))
        self.assertEqual(schema["properties"]["observed_at"]["format"], "date-time")
        self.assertFalse(schema["properties"]["fields"]["additionalProperties"])
        with self.assertRaises(ValueError):
            render_signature(observation(), "ansi")


if __name__ == "__main__":
    unittest.main()
