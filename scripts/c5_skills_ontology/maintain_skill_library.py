#!/usr/bin/env python3
"""One maintenance source, independent checks, verified distribution and rollback."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).absolute().parents[2]))
from tools.skill_library.maintenance import maintain, restore


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target", action="append", default=[], help="environment=/absolute/skills/root; repeat per environment"
    )
    parser.add_argument("--output", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", type=Path, help="Saved receipt.json; refuses to replace later user changes")
    args = parser.parse_args()
    if args.rollback:
        if args.apply or args.target or args.output:
            parser.error("--rollback cannot be combined with other operations")
        restore(json.loads(args.rollback.read_text()), args.rollback)
        print("Rollback verified from saved receipt")
        return 0
    if not args.target or not args.output:
        parser.error("--target and --output are required")
    targets = {}
    for value in args.target:
        environment, separator, path = value.partition("=")
        if not separator or environment in targets:
            parser.error("Each target requires a distinct environment=/absolute/path")
        targets[environment] = Path(path)
    try:
        report = maintain(targets, args.output.absolute(), args.apply)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(
        json.dumps(
            {
                "status": report["status"],
                "applied": args.apply,
                "report": str(args.output / "report.json"),
                "skills": {k: v["skills"] for k, v in report["environments"].items()},
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "pass" else 2


if __name__ == "__main__":
    raise SystemExit(main())
