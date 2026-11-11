"""Local CI policy regressions; no downloads, installs, or publishing."""

import os
from pathlib import Path
import re
import subprocess
import tempfile
import unittest

import yaml

ROOT = Path(__file__).resolve().parents[1]


def workflow(name):
    return yaml.safe_load((ROOT / ".github/workflows" / name).read_text())


class SupplyChainTests(unittest.TestCase):
    def test_publish_credentials_are_separated_from_build(self):
        # INV_C5_LICENSE_PARITY_GATE: PyPI publishing is frozen. The workflow may
        # build and verify, but no job may hold OIDC publish credentials.
        data = workflow("pypi-publish.yml")
        self.assertEqual(data["permissions"], {"contents": "read"})
        jobs = data["jobs"]
        self.assertNotIn("pypi-publish", jobs)
        build, frozen = jobs["build"], jobs["verify-frozen-publish"]
        self.assertEqual(build["permissions"], {"contents": "read"})
        self.assertEqual(frozen["needs"], "build")
        self.assertEqual(frozen["permissions"], {"contents": "read"})
        for name, job in jobs.items():
            self.assertNotIn("id-token", job.get("permissions", {}) or {}, name)
            self.assertNotIn("environment", job, name)
            for step in job["steps"]:
                uses = step.get("uses", "")
                self.assertNotIn("pypi-publish", uses, name)
                self.assertNotIn("twine upload", step.get("run", ""), name)
                self.assertNotIn("uv publish", step.get("run", ""), name)
                if uses:
                    self.assertRegex(uses, r"@[0-9a-f]{40}$")
        self.assertFalse(any("checkout@" in step.get("uses", "") for step in frozen["steps"]))
        commands = "\n".join(step.get("run", "") for step in build["steps"])
        self.assertIn("uv lock --check", commands)
        self.assertNotIn("pip install", commands)
        self.assertNotIn("curl ", commands)

    def test_conformance_rejects_manifest_lock_drift(self):
        steps = workflow("conformance.yml")["jobs"]["conformance"]["steps"]
        commands = [s["run"] for s in steps if "run" in s]
        self.assertEqual(commands[0], "uv sync --locked --all-extras")
        # The only other command builds, from Cargo.lock, the Rust binary the suite
        # exercises offline (test_rust_babylon_skills_mcp_stdio_interop); the
        # conformance script itself runs last without re-resolving.
        self.assertEqual(commands[1:-1], ["cargo build --locked -p babylon-skills-mcp"])
        self.assertTrue(commands[-1].startswith("uv run --no-sync "))
        for step in steps:
            if "uses" in step:
                self.assertRegex(step["uses"], r"@[0-9a-f]{40}$")
        setup = next(s for s in steps if "setup-uv@" in s.get("uses", ""))
        self.assertRegex(setup["uses"], r"@[0-9a-f]{40}$")
        self.assertRegex(setup["with"]["version"], r"^\d+\.\d+\.\d+$")
        self.assertRegex(setup["with"]["checksum"], r"^[0-9a-f]{64}$")

    def test_tampered_elan_download_fails_before_extract_or_execute(self):
        for name, job in [("ci.yml", "claims"), ("verify_lean.yml", "verify-lean")]:
            with self.subTest(workflow=name), tempfile.TemporaryDirectory() as tmp:
                steps = workflow(name)["jobs"][job]["steps"]
                script = next(s["run"] for s in steps if "elan.tar.gz" in s.get("run", ""))
                self.assertNotIn("/master/", script)
                self.assertIn("/v4.2.4/", script)
                self.assertLess(script.index("shasum "), script.index("tar -xzf"))
                stub = Path(tmp) / "curl"
                stub.write_text('#!/bin/sh\nwhile [ "$1" != "-o" ]; do shift; done\nprintf tampered > "$2"\n')
                stub.chmod(0o755)
                marker = Path(tmp) / "extracted"
                tar = Path(tmp) / "tar"
                tar.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 0\n')
                tar.chmod(0o755)
                # This checksum fixture must reach a declared runner branch,
                # regardless of the actual host running the unit test.
                uname = Path(tmp) / "uname"
                uname.write_text('#!/bin/sh\ncase "$1" in -s) echo Linux;; -m) echo x86_64;; *) exit 1;; esac\n')
                uname.chmod(0o755)
                env = dict(os.environ, PATH=tmp + ":" + os.environ["PATH"], RUNNER_TEMP=tmp, HOME=tmp)
                result = subprocess.run(["bash", "-c", script], env=env, capture_output=True, text=True, timeout=10)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn("FAILED", result.stdout + result.stderr)
                self.assertFalse(marker.exists())

    def test_all_workflow_shell_blocks_parse(self):
        for name in ["pypi-publish.yml", "conformance.yml", "ci.yml", "verify_lean.yml"]:
            for job in workflow(name)["jobs"].values():
                for step in job["steps"]:
                    if "run" in step:
                        # GitHub expands expressions before passing the command to bash.
                        script = re.sub(r"\$\{\{.*?\}\}", "placeholder", step["run"])
                        result = subprocess.run(["bash", "-n"], input=script, capture_output=True, text=True)
                        self.assertEqual(result.returncode, 0, (name, result.stderr))


if __name__ == "__main__":
    unittest.main()
