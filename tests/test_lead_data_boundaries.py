"""Regressions for scenario inputs, UI failures and concurrent provenance changes.

SQLite fixtures and browser responses below are test data; no biometric process
or commercial communication is invoked.
"""

import json
from pathlib import Path
import shutil
import subprocess
import threading
import unittest
import urllib.error
import urllib.request
from http.server import HTTPServer
from typing import ClassVar, cast

from scripts import babylon_launcher


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


if __name__ == "__main__":
    unittest.main()
