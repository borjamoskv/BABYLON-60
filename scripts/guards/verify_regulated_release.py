"""Check the exact prebuilt archive before login and again before publication.

Policy is supplied by the protected environment / reviewed repository, never by
the archive. This checker is read-only and does not consume a receipt; Actions
run id AND attempt bind it to one execution, including retries.
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
import hashlib
import os
from pathlib import Path
import sys
from typing import Any

sys.path.insert(0, str(Path(__file__).absolute().parents[2] / "01_KISH_ENGINE"))
from babylon60.compliance_exporter.regulatory import load_json  # noqa: E402
from babylon60.compliance_exporter.regulatory_gate import verify_receipt  # noqa: E402


def verify(
    artifact: Path, policy: dict[str, Any], receipt: dict[str, Any] | None, environment: Mapping[str, str]
) -> str:
    hasher = hashlib.sha256()
    with artifact.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(block)
    profile = policy.get("release_profile")
    if profile == "infrastructure":
        return "INFRASTRUCTURE_ONLY: no regulated approval or legal conformity asserted"
    if profile != "eu_ai_act_high_risk" or receipt is None:
        raise ValueError("Unknown release profile or missing regulated authorization")
    expected = {
        "action": "authorize-release",
        "profile_digest": policy["release_profile_digest"],
        "commit": environment["GITHUB_SHA"],
        "artifact_sha256": hasher.hexdigest(),
        "destination": "ghcr.io/" + environment["GITHUB_REPOSITORY"].lower(),
        "run_id": environment["GITHUB_RUN_ID"],
        "run_attempt": environment["GITHUB_RUN_ATTEMPT"],
    }
    verify_receipt(receipt, policy, expected)
    return "REGULATED_PUBLICATION_AUTHORIZED_WITHIN_ARTICLES_9_14_GATE"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact", required=True)
    parser.add_argument("--policy", required=True)
    parser.add_argument("--receipt")
    args = parser.parse_args()
    try:
        receipt = load_json(args.receipt) if args.receipt and Path(args.receipt).exists() else None
        print(verify(Path(args.artifact), load_json(args.policy), receipt, dict(os.environ)))
        return 0
    except Exception as exc:
        print(f"REGULATED_PUBLICATION_REJECTED: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
