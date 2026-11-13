"""Select native checks without leaving required workflow contexts pending.

Unknown events, missing history and malformed metadata require native execution.
Only a successfully inspected diff containing no native inputs can skip it.
"""

from fnmatch import fnmatchcase
import json
import os
from pathlib import Path
import re
import subprocess
import sys


NATIVE_INPUTS = (
    "src/**", "crates/**", "00_ABZU_KERNEL/**", "01_KISH_ENGINE/cortex/**",
    "Cargo.toml", "Cargo.lock", "build.rs", "rust-toolchain*", ".cargo/**",
    "tests/omega_mediation_campaign.rs", ".github/workflows/macos-native.yml",
    "scripts/guards/native_ci_scope.py", "tests/test_ci_runner_policy.py",
    "tests/test_native_ci_scope.py",
)
SHA = re.compile(r"[0-9a-f]{40}\Z")


def native_path(path: str) -> bool:
    return any(fnmatchcase(path, pattern) for pattern in NATIVE_INPUTS)


def requires_native(event_name: str, event: dict, head: str, root: Path) -> bool:
    if event_name == "pull_request":
        base = event.get("pull_request", {}).get("base", {}).get("sha", "")
    elif event_name == "push":
        base = event.get("before", "")
    else:
        return True
    if not all(isinstance(sha, str) and SHA.fullmatch(sha) and sha != "0" * 40 for sha in (base, head)):
        return True
    try:
        result = subprocess.run(
            ["git", "diff", "--no-ext-diff", "--no-renames", "--name-only", "-z", base, head, "--"],
            cwd=root, capture_output=True, timeout=30, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return True
    return any(native_path(os.fsdecode(path)) for path in result.stdout.split(b"\0") if path)


def main() -> None:
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_bytes())
        required = requires_native(os.environ.get("GITHUB_EVENT_NAME", ""), event,
                                   os.environ.get("GITHUB_SHA", ""), Path.cwd())
    except (KeyError, OSError, ValueError, TypeError, AttributeError):
        print("Native scope unavailable; requiring native execution", file=sys.stderr)
        required = True
    print(f"required={str(required).lower()}")


if __name__ == "__main__":
    main()
