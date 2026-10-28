"""Security regressions for the Babylon IDE terminal."""

from pathlib import Path
import shutil
import subprocess
import unittest


class TerminalLogTests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("node"), "Node is required for browser logic regression")
    def test_untrusted_log_text_is_not_interpreted_as_html(self) -> None:
        html = (Path(__file__).resolve().parents[1] / "tools" / "ui_babylon_ide" / "index.html").read_text()
        function = (
            "function appendLog(tag, msg) {"
            + html.split("    function appendLog(tag, msg) {", 1)[1].split("    function clearLogs", 1)[0]
        )
        harness = r"""
const assert = require('node:assert/strict');
const logs = {children: [], scrollHeight: 42, appendChild(node) { this.children.push(node); }};
global.document = {
  getElementById: () => logs,
  createElement: name => ({
    name, children: [],
    appendChild(node) { this.children.push(node); },
    set innerHTML(value) { throw new Error('Log text was interpreted as HTML'); }
  })
};
const tag = '<img src=x onerror=alert(1)>';
const message = '<script>alert(2)</script> & text';
appendLog(tag, message);
const row = logs.children[0];
assert.equal(row.className, 'log-line');
assert.equal(row.children[0].className, 'log-tag');
assert.equal(row.children[0].textContent, `[${tag}]`);
assert.equal(row.children[1].textContent, message);
assert.equal(logs.scrollTop, 42);
"""
        node = shutil.which("node")
        assert node is not None
        result = subprocess.run([node, "-"], input=function + harness, text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
