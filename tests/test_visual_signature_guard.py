"""Acceptance and rejection cases for visual response signatures."""

from html import escape
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.guards.verify_active_topology import FOOTER_FIELDS, validate_text


class VisualSignatureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "signature.html"
        self.values = {
            "LLM": "GPT-6 (entorno; No evaluable)",
            "MODO COGNITIVO": "No expuesto",
            "TOPOLOGÍA ACTIVA": "MOSKV-1",
            "RÉGIMEN TÉRMICO": "No medido",
            "EXERGÍA INFORMATIVA": "No medida",
            "MUTACIÓN CAUSAL": "Ninguna (presentación)",
        }

    def write_panel(self, *, outer: str = "main", attributes: str = "") -> str:
        fields = "".join(
            f'<div data-signature-field="{name}"><span>{escape(value)}</span></div>'
            for name, value in self.values.items()
        )
        panel = f"<!doctype html><html><body><{outer} {attributes}>{fields}</{outer}></body></html>"
        self.path.write_text(panel, encoding="utf-8")
        return panel

    def response(self, path: Path | None = None) -> str:
        payload = json.dumps({"path": str(path or self.path)}, ensure_ascii=False)
        return f"Resultado revisado.\n\nvisualize{payload}\n"

    def write_v2_panel(
        self,
        *,
        values: dict[str, str] | None = None,
        sources: dict[str, str] | None = None,
        observed_at: str = "2026-10-18T00:45:00+02:00",
        version: str = "2",
    ) -> str:
        if values is None:
            values = {"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"]}
        if sources is None:
            sources = {"LLM": "Cabecera de la sesión"}
        fields = "".join(f'<div data-signature-field="{name}">{escape(value)}</div>' for name, value in values.items())
        provenance = "".join(
            f'<small data-signature-source="{name}">{escape(value)}</small>' for name, value in sources.items()
        )
        panel = (
            "<!doctype html><html><body>"
            f'<main data-signature-version="{escape(version)}" '
            f'data-signature-observed-at="{escape(observed_at)}">'
            f"{fields}{provenance}</main></body></html>"
        )
        self.path.write_text(panel, encoding="utf-8")
        return panel

    def test_v2_requires_only_identity_and_model(self) -> None:
        self.write_v2_panel()
        self.assertEqual(validate_text(self.response(), response=True, require_selector_verdict=True), [])
        self.write_v2_panel(values={"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": "No expuesto"})
        self.assertEqual(validate_text(self.response(), response=True, require_selector_verdict=True), [])

    def test_explicit_legacy_v1_without_timestamp_preserves_six_fields(self) -> None:
        panel = self.write_panel(attributes='data-signature-version="1"')
        self.assertEqual(validate_text(self.response(), response=True, require_selector_verdict=True), [])
        for invalid in (
            panel.replace('data-signature-field="MODO COGNITIVO"', ""),
            panel.replace("</main>", '<small data-signature-source="LLM">Fuente</small></main>'),
        ):
            self.path.write_text(invalid, encoding="utf-8")
            self.assertTrue(validate_text(self.response(), response=True))

    def test_v2_optional_fields_and_declared_sources(self) -> None:
        for name in (
            "MODO COGNITIVO",
            "VERIFICACIÓN",
            "CAMBIOS",
            "LÍMITES",
            "RÉGIMEN TÉRMICO",
            "EXERGÍA INFORMATIVA",
            "MUTACIÓN CAUSAL",
        ):
            with self.subTest(name=name):
                self.write_v2_panel(
                    values={"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"], name: "Dato declarado"},
                    sources={"LLM": "Cabecera de sesión", name: "Referencia declarada"},
                )
                self.assertEqual(validate_text(self.response(), response=True), [])

    def test_v2_missing_identity_model_or_required_sources_rejected(self) -> None:
        for missing in ("TOPOLOGÍA ACTIVA", "LLM"):
            with self.subTest(missing=missing):
                values = {"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"]}
                del values[missing]
                self.write_v2_panel(values=values)
                self.assertTrue(validate_text(self.response(), response=True))
        for name in ("LLM", "MODO COGNITIVO", "VERIFICACIÓN", "RÉGIMEN TÉRMICO", "EXERGÍA INFORMATIVA"):
            for source in (None, "", "TBD"):
                with self.subTest(name=name, source=source):
                    values = {"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"]}
                    sources = {"LLM": "Cabecera de sesión"}
                    if name != "LLM":
                        values[name] = "Dato declarado"
                    if source is None:
                        sources.pop(name, None)
                    else:
                        sources[name] = source
                    self.write_v2_panel(values=values, sources=sources)
                    self.assertTrue(validate_text(self.response(), response=True))

    def test_v2_requires_explicit_supported_version_and_zoned_iso_timestamp(self) -> None:
        for version in ("", "3", "2 2"):
            with self.subTest(version=version):
                self.write_v2_panel(version=version)
                self.assertTrue(validate_text(self.response(), response=True))
        for observed_at in (
            "",
            "2026-10-18",
            "2026-10-18T00:45:00",
            "2026-99-18T00:45:00Z",
            "hoy",
            "2026-10-18T00:45:00+24:00",
            "2026-10-18T00:45:00+00:99",
        ):
            with self.subTest(observed_at=observed_at):
                self.write_v2_panel(observed_at=observed_at)
                self.assertTrue(validate_text(self.response(), response=True))
        for observed_at in ("2026-10-18T00:45:00Z", "2026-10-18T00:45:00+02:00"):
            with self.subTest(observed_at=observed_at):
                self.write_v2_panel(observed_at=observed_at)
                self.assertEqual(validate_text(self.response(), response=True), [])

    def test_v2_rejects_duplicate_roots_fields_sources_and_outside_content(self) -> None:
        for operation in ("root", "version", "timestamp", "field", "source", "outside_field", "outside_source"):
            with self.subTest(operation=operation):
                panel = self.write_v2_panel()
                if operation == "root":
                    panel = panel.replace("</main>", '</main><aside data-signature-version="2"></aside>')
                elif operation == "version":
                    panel = panel.replace(
                        'data-signature-version="2"', 'data-signature-version="2" data-signature-version="2"'
                    )
                elif operation == "timestamp":
                    panel = panel.replace("<main ", '<main data-signature-observed-at="2026-10-18T00:45:00Z" ')
                elif operation == "field":
                    panel = panel.replace("</main>", '<div data-signature-field="LLM">Duplicado</div></main>')
                elif operation == "source":
                    panel = panel.replace("</main>", '<small data-signature-source="LLM">Duplicado</small></main>')
                elif operation == "outside_field":
                    panel = panel.replace("</main>", '</main><div data-signature-field="CAMBIOS">Cambio</div>')
                else:
                    panel = panel.replace("</main>", '</main><small data-signature-source="CAMBIOS">Referencia</small>')
                self.path.write_text(panel, encoding="utf-8")
                self.assertTrue(validate_text(self.response(), response=True))

    def test_v2_provenance_must_be_visible_and_values_remain_validated(self) -> None:
        for operation in (
            "hidden_source",
            "hidden_root",
            "blank_field",
            "unknown_field",
            "nested_source",
            "wrong_identity",
        ):
            with self.subTest(operation=operation):
                panel = self.write_v2_panel()
                if operation == "hidden_source":
                    panel = panel.replace("<small ", "<small hidden ")
                elif operation == "hidden_root":
                    panel = panel.replace("<main ", "<main hidden ")
                elif operation == "blank_field":
                    panel = panel.replace("</main>", '<div data-signature-field="CAMBIOS"> </div></main>')
                elif operation == "unknown_field":
                    panel = panel.replace('data-signature-field="LLM"', 'data-signature-field="EXTRA"')
                elif operation == "nested_source":
                    panel = panel.replace(
                        "MOSKV-1</div>", 'MOSKV-1<small data-signature-source="LLM">Fuente</small></div>'
                    )
                else:
                    panel = panel.replace("MOSKV-1", "moskv-1")
                self.path.write_text(panel, encoding="utf-8")
                self.assertTrue(validate_text(self.response(), response=True))

    def test_v2_does_not_certify_evidence_or_freshness(self) -> None:
        self.write_v2_panel(
            values={"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"], "VERIFICACIÓN": "Declaración del autor"},
            sources={"LLM": "Fuente declarada", "VERIFICACIÓN": "/ruta/no-comprobada.txt"},
            observed_at="2001-01-01T00:00:00Z",
        )
        self.assertEqual(validate_text(self.response(), response=True), [])

    def test_v2_context_must_not_be_disclosed_only_inside_details(self) -> None:
        for name in ("VERIFICACIÓN", "CAMBIOS", "LÍMITES"):
            for attributes in ("", "open"):
                with self.subTest(name=name, attributes=attributes):
                    panel = self.write_v2_panel(
                        values={"TOPOLOGÍA ACTIVA": "MOSKV-1", "LLM": self.values["LLM"], name: "Dato declarado"},
                        sources={"LLM": "Fuente", name: "Referencia"},
                    )
                    panel = panel.replace(
                        f'<div data-signature-field="{name}">Dato declarado</div>',
                        f"<details {attributes}><summary>Contexto</summary>"
                        f'<div data-signature-field="{name}">Dato declarado</div></details>',
                    )
                    self.path.write_text(panel, encoding="utf-8")
                    self.assertTrue(validate_text(self.response(), response=True))

    def test_v2_sources_may_be_inside_details(self) -> None:
        panel = self.write_v2_panel()
        panel = panel.replace("<small ", "<details><summary>Fuentes</summary><small ")
        panel = panel.replace("</small>", "</small></details>")
        self.path.write_text(panel, encoding="utf-8")
        self.assertEqual(validate_text(self.response(), response=True), [])

    def test_v2_repeated_validation_after_warmup(self) -> None:
        self.write_v2_panel()
        response = self.response()
        self.assertEqual(validate_text(response, response=True), [])
        for _ in range(100):
            self.assertEqual(validate_text(response, response=True), [])

    def test_visual_footer_replaces_text_footer(self) -> None:
        self.write_panel()
        self.assertEqual(validate_text(self.response(), response=True, require_selector_verdict=True), [])

    def test_legacy_footer_and_independent_verdicts(self) -> None:
        pairs = (
            ("GPT-6 (entorno; No evaluable)", "No expuesto", True),
            ("No expuesto", "Alto (selector; ÓPTIMO)", True),
            ("No expuesto", "Alto", False),
            ("GPT-6", "No expuesto", False),
            ("No expuesto", "No expuesto", True),
        )
        for llm, mode, accepted in pairs:
            with self.subTest(llm=llm, mode=mode):
                self.values.update({"LLM": llm, "MODO COGNITIVO": mode})
                self.write_panel()
                footer = "\n".join(field + value for field, value in zip(FOOTER_FIELDS, self.values.values()))
                for response in (self.response(), "Resultado.\n" + footer, "```text\n" + footer + "\n```"):
                    self.assertEqual(
                        not validate_text(response, response=True, require_selector_verdict=True), accepted
                    )

    def test_textual_signature_cannot_be_duplicated_after_panel(self) -> None:
        self.write_panel()
        response = "[ LLM ]: GPT-6\n" + self.response()
        self.assertTrue(any("duplicate textual" in error for error in validate_text(response, response=True)))

    def test_directive_must_be_final_standalone_and_outside_fences(self) -> None:
        self.write_panel()
        for response in (
            self.response() + "Después.",
            self.response().replace("\n\n", " "),
            "```html\n" + self.response(),
            self.response().replace("", ""),
        ):
            with self.subTest(response=response):
                self.assertTrue(validate_text(response, response=True))

    def test_six_unique_known_fields_required(self) -> None:
        for operation in ("missing", "duplicate", "unknown", "nested", "unclosed"):
            with self.subTest(operation=operation):
                panel = self.write_panel()
                if operation == "missing":
                    panel = panel.replace('data-signature-field="LLM"', "")
                elif operation == "duplicate":
                    panel = panel.replace("</main>", '<p data-signature-field="LLM">Otro</p></main>')
                elif operation == "unknown":
                    panel = panel.replace("</main>", '<p data-signature-field="EXTRA">Otro</p></main>')
                elif operation == "nested":
                    panel = panel.replace("<span>", '<span data-signature-field="LLM">', 1)
                else:
                    panel = panel.replace("</div>", "", 1)
                self.path.write_text(panel, encoding="utf-8")
                self.assertTrue(validate_text(self.response(), response=True))

    def test_obviously_hidden_fields_and_content_rejected(self) -> None:
        for attributes in (
            "hidden",
            'aria-hidden="true"',
            'style="display: none !important"',
            'style="visibility: hidden"',
            'style="opacity: 0"',
        ):
            with self.subTest(attributes=attributes):
                self.write_panel(attributes=attributes)
                self.assertTrue(validate_text(self.response(), response=True))
        for outer in ("script", "style", "template", "head"):
            with self.subTest(outer=outer):
                self.write_panel(outer=outer)
                self.assertTrue(validate_text(self.response(), response=True))
        panel = self.write_panel().replace("<span>", "<span hidden>", 1)
        self.path.write_text(panel, encoding="utf-8")
        self.assertTrue(validate_text(self.response(), response=True))

    def test_value_invariants_survive_html_entity_decoding(self) -> None:
        for name, value in (
            ("LLM", ""),
            ("LLM", "TBD"),
            ("LLM", "<Modelo>"),
            ("LLM", "{{model}}"),
            ("LLM", "GPT-6\u200b"),
            ("LLM", "GPT-6\x01"),
            ("LLM", "GPT\t6"),
            ("LLM", "GPT\n6"),
            ("LLM", "[ LLM ]: GPT-6"),
            ("TOPOLOGÍA ACTIVA", "moskv-1"),
            ("TOPOLOGÍA ACTIVA", "MOSKV-1 (Codex)"),
        ):
            with self.subTest(name=name, value=value):
                previous = self.values[name]
                self.values[name] = value
                self.write_panel()
                self.assertTrue(validate_text(self.response(), response=True))
                self.values[name] = previous

    def test_paths_reject_missing_relative_wrong_extension_and_symlink(self) -> None:
        self.write_panel()
        symlink = self.path.with_name("link.html")
        symlink.symlink_to(self.path)
        wrong_extension = self.path.with_suffix(".txt")
        wrong_extension.write_text(self.path.read_text(encoding="utf-8"), encoding="utf-8")
        for path in (Path("signature.html"), self.path.with_name("missing.html"), wrong_extension, symlink):
            with self.subTest(path=path):
                self.assertTrue(validate_text(self.response(path), response=True))

    def test_invalid_json_payloads_rejected(self) -> None:
        for payload in ("{}", "null", "[]", '{"path": 1}', '{"path": "x.html", "extra": 1}', "{invalid}"):
            with self.subTest(payload=payload):
                self.assertTrue(validate_text(f"visualize{payload}", response=True))

    def test_nonregular_files_rejected_without_blocking(self) -> None:
        directory = self.path.with_name("directory.html")
        directory.mkdir()
        fifo = self.path.with_name("fifo.html")
        os.mkfifo(fifo)
        for path in (directory, fifo):
            with self.subTest(path=path):
                self.assertTrue(validate_text(self.response(path), response=True))

    def test_non_utf8_and_oversized_files_rejected(self) -> None:
        for data in (b"\xff", b" " * (1024 * 1024 + 1)):
            with self.subTest(size=len(data)):
                self.path.write_bytes(data)
                self.assertTrue(validate_text(self.response(), response=True))

    def test_repeated_validation_after_warmup(self) -> None:
        self.write_panel()
        response = self.response()
        validate_text(response, response=True)
        for _ in range(100):
            self.assertEqual(validate_text(response, response=True), [])


if __name__ == "__main__":
    unittest.main()
