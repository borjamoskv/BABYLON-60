"""Reject publication unless the latest CI result is successful for this SHA."""

import json
import os
import sys


def main() -> None:
    runs = json.load(sys.stdin)
    if not isinstance(runs, list) or len(runs) != 1:
        raise SystemExit("Publication requires exactly one latest CI result")
    run = runs[0]
    expected = os.environ["GITHUB_SHA"]
    if (
        run.get("headSha") != expected
        or run.get("status") != "completed"
        or run.get("conclusion") != "success"
        or run.get("event") != "push"
        or run.get("headBranch") != "main"
    ):
        raise SystemExit("Publication requires a successful completed main push run for the exact SHA")
    print(f"Verified CI success for {expected}")


if __name__ == "__main__":
    main()
