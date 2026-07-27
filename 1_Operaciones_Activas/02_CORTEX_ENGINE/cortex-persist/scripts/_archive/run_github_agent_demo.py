from __future__ import annotations
#!/usr/bin/env python3
"""Run the BABYLON60 GitHubAgent end-to-end from the terminal."""

import logging

import argparse
import asyncio
import json

from babylon60.services.github_agent_demo import build_github_agent_payload, run_github_agent_demo


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the BABYLON60 GitHubAgent against the current repository."
    )
    parser.add_argument(
        "--op",
        default="status",
        help=(
            "GitHubAgent operation. Examples: status, dev, permalink, search, diff_url, "
            "review, blame, history, pr_checkout, pr_view, pr_create, repo_clone."
        ),
    )
    parser.add_argument("--remote", default="origin", help="Git remote to resolve.")
    parser.add_argument("--path", default=None, help="Repo-relative path for file-oriented ops.")
    parser.add_argument("--lines", default=None, help="Line selection, e.g. 10 or 10-25.")
    parser.add_argument("--query", default=None, help="Search query for the search op.")
    parser.add_argument("--language", default=None, help="Language qualifier for search.")
    parser.add_argument("--symbol", default=None, help="Symbol qualifier for search.")
    parser.add_argument("--all-repos", action="store_true", help="Disable repo: scoping in search.")
    parser.add_argument("--pr-number", type=int, default=None, help="Pull request number.")
    parser.add_argument("--commit-sha", default=None, help="Commit SHA for diff_url.")
    parser.add_argument(
        "--format-name",
        default=None,
        help="Format for diff_url, usually patch or diff.",
    )
    parser.add_argument("--ref", default=None, help="Git ref for blame/history.")
    parser.add_argument("--title", default=None, help="PR title for pr_create.")
    parser.add_argument("--body", default=None, help="PR body for pr_create.")
    parser.add_argument("--base", default=None, help="Base branch for pr_create.")
    parser.add_argument("--head", default=None, help="Head branch for pr_create.")
    parser.add_argument("--draft", action="store_true", help="Create a draft PR.")
    parser.add_argument(
        "--fill", action="store_true", help="Ask gh to fill title/body from commits."
    )
    parser.add_argument(
        "--web", action="store_true", help="Open browser flow for supported gh ops."
    )
    parser.add_argument(
        "--name-with-owner",
        default=None,
        help="owner/repo identifier for repo_clone.",
    )
    parser.add_argument(
        "--directory",
        default=None,
        help="Destination directory for repo_clone.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Seconds to wait for the agent reply.",
    )
    parser.add_argument(
        "--dump-payload",
        action="store_true",
        help="Print the outgoing TASK_REQUEST payload before sending it.",
    )
    return parser


def build_payload(args: argparse.Namespace) -> dict[str, object]:
    return build_github_agent_payload(
        op=args.op,
        remote=args.remote,
        path=args.path,
        lines=args.lines,
        query=args.query,
        language=args.language,
        symbol=args.symbol,
        all_repos=args.all_repos,
        pr_number=args.pr_number,
        commit_sha=args.commit_sha,
        format_name=args.format_name,
        ref=args.ref,
        title=args.title,
        body=args.body,
        base=args.base,
        head=args.head,
        draft=args.draft,
        fill=args.fill,
        web=args.web,
        name_with_owner=args.name_with_owner,
        directory=args.directory,
    )


async def run_demo(args: argparse.Namespace) -> int:
    payload = build_payload(args)
    if args.dump_payload:
        logging.getLogger(__name__).info(json.dumps(payload, indent=2, sort_keys=True))
    reply = await run_github_agent_demo(payload, timeout=args.timeout)
    ok = "error" not in reply
    output = {"ok": ok, **reply}
    logging.getLogger(__name__).info(json.dumps(output, indent=2, sort_keys=True, default=str))
    return 0 if ok else 1


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return asyncio.run(run_demo(args))


if __name__ == "__main__":
    raise SystemExit(main())
