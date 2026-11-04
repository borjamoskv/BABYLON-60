"""Retrieve a signed authorization after Production approval, without registry credentials.

An operator-controlled HTTPS endpoint serves <run_id>/<run_attempt>.json. The
transport is not a trust root: the independent verifier checks signatures and
all bindings. Unknown profiles and unavailable receipts fail closed.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import urllib.request
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).absolute().parents[2] / "01_KISH_ENGINE"))
from babylon60.compliance_exporter.regulatory import MAX_BYTES, load_json  # noqa: E402


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("Authorization endpoint redirects are not allowed")


def prepare(output: Path, environment: dict) -> None:
    raw = environment.get("POLICY_JSON", "").strip()
    output.mkdir(parents=True, exist_ok=True)
    if not raw:
        raw = Path(".github/regulatory-policy.json").read_text(encoding="utf-8")
    policy_path = output / "policy.json"
    policy_path.write_text(raw, encoding="utf-8")
    policy = load_json(policy_path)
    profile = policy.get("release_profile")
    if profile == "infrastructure":
        (output / "receipt.json").unlink(missing_ok=True)
        return
    if profile != "eu_ai_act_high_risk":
        raise ValueError("Release profile unknown")
    base = environment.get("AUTHORIZATION_BASE_URL", "")
    parts = urlsplit(base)
    if (
        parts.scheme != "https"
        or not parts.hostname
        or parts.username
        or parts.password
        or parts.query
        or parts.fragment
    ):
        raise ValueError("A protected HTTPS authorization endpoint is required")
    run, attempt = environment["GITHUB_RUN_ID"], environment["GITHUB_RUN_ATTEMPT"]
    if not re.fullmatch(r"[0-9]+", run) or not re.fullmatch(r"[0-9]+", attempt):
        raise ValueError("Invalid Actions execution")
    url = f"{base.rstrip('/')}/{run}/{attempt}.json"
    opener = urllib.request.build_opener(NoRedirect)
    with opener.open(url, timeout=20) as response:
        data = response.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("Receipt too large")
    # The consumer rejects malformed/duplicate keys and checks trust independently.
    json.loads(data)
    (output / "receipt.json").write_bytes(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        prepare(Path(args.output), dict(os.environ))
        return 0
    except Exception as exc:
        print(f"REGULATED_PREPARATION_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
