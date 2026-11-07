"""Validate ledger trailers on every commit introduced by an event."""

import argparse
import re
import subprocess


def git(*args: str, input_text: str | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        input=input_text,
        text=True,
        capture_output=True,
        check=True,
    ).stdout.strip()


def verify(base: str, head: str) -> None:
    for revision in (base, head):
        if not re.fullmatch(r"[0-9a-f]{40,64}", revision) or set(revision) == {"0"}:
            raise ValueError("An explicit nonzero base and head commit SHA are required")
        git("cat-file", "-e", f"{revision}^{{commit}}")
    commits = git("rev-list", f"{base}..{head}").splitlines()
    if not commits:
        raise ValueError("No introduced commits to verify")
    for commit in commits:
        trailers = git("interpret-trailers", "--parse", input_text=git("show", "-s", "--format=%B", commit))
        for name, pattern in (("Ledger-Head", r"[0-9a-f]{64}"), ("Ledger-Seq", r"0|[1-9][0-9]*")):
            values = [
                line.split(":", 1)[1].strip()
                for line in trailers.splitlines()
                if line.partition(":")[0].lower() == name.lower()
            ]
            if len(values) != 1 or re.fullmatch(pattern, values[0]) is None:
                raise ValueError(f"{commit}: requires exactly one valid {name} trailer")
    print(f"Verified ledger trailer syntax on {len(commits)} introduced commits")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    try:
        verify(args.base, args.head)
    except (ValueError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"Ledger trailer verification failed: {error}\n")


if __name__ == "__main__":
    main()
