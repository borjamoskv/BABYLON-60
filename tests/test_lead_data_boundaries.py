"""Regressions for scenario inputs, UI failures and concurrent provenance changes.

SQLite fixtures and browser responses below are test data; no biometric process
or commercial communication is invoked.
"""

import contextlib
import io
import json
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
import threading
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
from http.server import HTTPServer
from collections.abc import Mapping
from typing import ClassVar, cast

from scripts import babylon_launcher, outreach_cockpit, partition_campaigns


class QuietHandler(babylon_launcher.BabylonHTTPHandler):
    def log_message(self, format: str, *args: object) -> None:
        pass


class ScenarioInputTests(unittest.TestCase):
    server: ClassVar[HTTPServer]
    worker: ClassVar[threading.Thread]

    @classmethod
    def setUpClass(cls) -> None:
        cls.server = HTTPServer(("127.0.0.1", 0), QuietHandler)
        cls.worker = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.worker.start()

    @classmethod
    def tearDownClass(cls) -> None:
        cls.server.shutdown()
        cls.server.server_close()
        cls.worker.join(5)

    def scenario(self, query: str) -> tuple[int, dict[str, object]]:
        url = f"http://127.0.0.1:{self.server.server_port}/api/guardrails/simulate?{query}"
        try:
            response = urllib.request.urlopen(url, timeout=5)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, cast(dict[str, object], json.load(response))

    def test_empty_and_ambiguous_parameters_are_rejected(self) -> None:
        for query in ("n=", "eps=", "delta=", "n=0&n=100", "eps=0&eps=1", "delta=0&delta=1"):
            with self.subTest(query=query):
                status, data = self.scenario(query)
                self.assertEqual(status, 400)
                self.assertIn("error", data)

    def test_omitted_defaults_and_explicit_zero_remain_valid(self) -> None:
        for query, expected in (("", 100), ("n=0", 0), ("n=100&eps=0.1&delta=0.2", 2)):
            with self.subTest(query=query):
                status, data = self.scenario(query)
                self.assertEqual(status, 200)
                actual = data["expected_joint_failures_annual"]
                assert isinstance(actual, (int, float))
                self.assertAlmostEqual(actual, expected)


class BrowserFailureTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for browser logic regression")
    def test_http_error_cannot_report_biometric_success(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "tools" / "ui_babylon_ide" / "index.html").read_text()
        function = (
            "function authenticateBiometrics() {"
            + html.split("    function authenticateBiometrics() {", 1)[1].split("    function handleProvider", 1)[0]
        )
        harness = r"""
const assert = require('node:assert/strict');
let logs = [], steps = [];
global.playHapticPulse = () => {};
global.appendLog = (tag, message) => logs.push([tag, message]);
global.setStep = step => steps.push(step);
global.setTimeout = callback => callback();
const body = {status: 'AUTHORIZATION_REPORTED', authorization_scope: 'DEMONSTRATION_ONLY'};
// A misleading body must not override the failed HTTP status.
const cases = [
  [async () => ({ok: false, status: 500, json: async () => body}), false],
  [async () => {throw new Error('offline');}, false],
  [async () => ({ok: true, status: 200, json: async () => {throw new Error('invalid JSON');}}), false],
  [async () => ({ok: true, status: 200, json: async () => body}), true]
];
(async () => {
  for (const [fetchResponse, accepted] of cases) {
    logs = []; steps = []; global.fetch = fetchResponse;
    authenticateBiometrics();
    await new Promise(resolve => setImmediate(resolve));
    assert.deepEqual(steps, accepted ? [2] : []);
    assert.equal(logs.some(([tag]) => tag === 'AUTH_DEMO'), accepted);
    assert.equal(logs.some(([tag]) => tag === 'SEC_ERROR'), !accepted);
  }
})().catch(error => {console.error(error); process.exitCode = 1;});
"""
        node = shutil.which("node")
        assert node is not None
        result = subprocess.run([node, "-"], input=function + harness, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


class ProvenanceSnapshotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="lead-boundaries-")
        self.addCleanup(self.temporary.cleanup)
        self.folder = Path(self.temporary.name)
        self.db = self.folder / "contacts.db"
        self.writer = sqlite3.connect(self.db)
        self.addCleanup(self.writer.close)
        self.writer.execute("PRAGMA journal_mode=WAL")
        self.writer.execute("""CREATE TABLE leads (
            lead_id TEXT, company_name TEXT, sector TEXT, country TEXT,
            target_role TEXT, record_classification TEXT,
            source_reference TEXT, verified_at TEXT
        )""")
        self.writer.executemany(
            "INSERT INTO leads VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (
                    "TEST-1",
                    "Offline fixture one",
                    "TEST_ONLY",
                    "España",
                    "CISO",
                    "REAL_CONTACT",
                    "fixture://offline-regression",
                    "2026-10-12",
                ),
                (
                    "TEST-2",
                    "Offline fixture two",
                    "TEST_ONLY",
                    "España",
                    "DPO",
                    "REAL_CONTACT",
                    "fixture://offline-regression",
                    "2026-10-12",
                ),
            ],
        )
        self.writer.commit()

    def test_partition_exports_the_same_snapshot_it_validated(self) -> None:
        original_validator = partition_campaigns.require_commercial_record

        def validate_then_change(record: Mapping[str, object]) -> None:
            original_validator(record)
            if record["lead_id"] == "TEST-2":
                self.writer.execute("""UPDATE leads SET record_classification = 'SYNTHETIC_ONLY',
                    company_name = 'MODIFIED' WHERE lead_id = 'TEST-2'""")
                self.writer.commit()

        output = self.folder / "campaigns"
        with (
            patch.object(partition_campaigns, "DB_PATH", self.db),
            patch.object(partition_campaigns, "CAMPAIGNS_DIR", output),
            patch.object(partition_campaigns, "require_commercial_record", validate_then_change),
            contextlib.redirect_stdout(io.StringIO()),
        ):
            partition_campaigns.partition_campaigns()
        rows = [
            json.loads(line) for line in (output / "campaign_tier1_spain_top_priority.jsonl").read_text().splitlines()
        ]
        self.assertEqual(len(rows), 2)
        self.assertTrue(all(row["record_classification"] == "REAL_CONTACT" for row in rows))
        self.assertEqual(rows[1]["company_name"], "Offline fixture two")
        self.assertEqual(
            self.writer.execute("SELECT company_name FROM leads WHERE lead_id = 'TEST-2'").fetchone()[0], "MODIFIED"
        )

    def test_cockpit_counts_the_snapshot_it_validated(self) -> None:
        original_validator = outreach_cockpit.require_commercial_record

        def validate_then_delete(record: Mapping[str, object]) -> None:
            original_validator(record)
            if record["lead_id"] == "TEST-2":
                self.writer.execute("DELETE FROM leads WHERE lead_id = 'TEST-2'")
                self.writer.commit()

        captured = io.StringIO()
        with (
            patch.object(outreach_cockpit, "DB_PATH", self.db),
            patch.object(outreach_cockpit, "QUEUE_PATH", self.folder / "missing.jsonl"),
            patch.object(outreach_cockpit, "require_commercial_record", validate_then_delete),
            contextlib.redirect_stdout(captured),
        ):
            outreach_cockpit.render_cockpit()
        self.assertIn("Contactos en base privada:      2 registros", captured.getvalue())
        self.assertEqual(self.writer.execute("SELECT COUNT(*) FROM leads").fetchone()[0], 1)


if __name__ == "__main__":
    unittest.main()
