#!/usr/bin/env python3
"""Check Markdown destinations and anchors; inaccessible remotes remain unverified."""

from pathlib import Path
import argparse
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import json
import re
from typing import TypedDict
from urllib.error import HTTPError
from urllib.parse import unquote, urldefrag, urlparse
from urllib.request import Request, urlopen


class FetchResult(TypedDict, total=False):
    status: str
    http: int
    final_url: str
    ids: list[str]
    error: str


class Finding(TypedDict):
    file: str
    line: int
    target: str
    status: str
    reason: str


class AuditReport(TypedDict):
    links: int
    unique_remote_urls: int
    findings: list[Finding]
    responses: dict[str, FetchResult]


def anchors(text: str) -> set[str]:
    result = set(re.findall(r'(?:id|name)=["\']([^"\']+)', text))
    seen: dict[str, int] = {}
    fence = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fence = not fence
            continue
        if fence:
            continue
        if re.match(r"^#{1,6}\s", line):
            title = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", re.sub(r"^#+\s*", "", line).strip().rstrip("#").strip())
            slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
            count = seen.get(slug, 0)
            seen[slug] = count + 1
            result.add(slug + ("-" + str(count) if count else ""))
    return result


class IDs(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.ids.update(v for k, v in attrs if k in {"id", "name"} and v)


def fetch(url: str) -> FetchResult:
    try:
        with urlopen(Request(url, headers={"User-Agent": "BABYLON-60-LinkAudit/1.0"}), timeout=18) as response:
            body = response.read(8 * 1024 * 1024).decode("utf-8", errors="replace")
            parser = IDs()
            parser.feed(body)
            return {"status": "ok", "http": response.status, "final_url": response.url, "ids": sorted(parser.ids)}
    except HTTPError as exc:
        return {"status": "broken" if exc.code in {404, 410} else "unverified", "http": exc.code}
    except Exception as exc:
        return {"status": "unverified", "error": type(exc).__name__ + ": " + str(exc)}


def inspect(roots: list[Path], remote: bool = True) -> AuditReport:
    links: list[tuple[Path, int, str]] = []
    for root in roots:
        if not root.is_dir():
            raise OSError(f"Missing Markdown root: {root}")
        for p in root.rglob("*.md"):
            if any(x in {"_archive", "archive", ".system", "__pycache__"} for x in p.relative_to(root).parts):
                continue
            fence = False
            for n, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
                if line.lstrip().startswith(("```", "~~~")):
                    fence = not fence
                    continue
                if fence:
                    continue
                for target in re.findall(r"\]\(([^)]+)\)", line):
                    links.append((p, n, target.strip("<>")))
    urls = sorted({urldefrag(t)[0] for _, _, t in links if urlparse(t).scheme in {"https", "http"}})
    responses = dict(zip(urls, ThreadPoolExecutor(max_workers=20).map(fetch, urls))) if remote else {}
    findings: list[Finding] = []
    for p, n, target in links:
        url, fragment = urldefrag(target)
        scheme = urlparse(url).scheme
        status = "ok"
        reason = ""
        if scheme in {"http", "https"}:
            data = responses.get(url, {"status": "unverified"})
            status = data["status"]
            reason = str(data.get("http", "not checked"))
            if (
                status == "ok"
                and fragment
                and unquote(fragment) not in data.get("ids", [])
                and "user-content-" + unquote(fragment) not in data.get("ids", [])
            ):
                status = "unverified"
                reason = "remote anchor absent in retrieved HTML"
        elif not scheme or scheme == "file":
            parsed = urlparse(url)
            if scheme == "file" and parsed.netloc not in {"", "localhost"}:
                findings.append(
                    {"file": str(p), "line": n, "target": target, "status": "unverified", "reason": "remote file host"}
                )
                continue
            local = unquote(parsed.path if scheme == "file" else url)
            dest = p.parent / local if local else p
            if not dest.exists():
                status = "broken"
                reason = "missing file"
            elif (
                fragment
                and dest.is_file()
                and dest.suffix == ".md"
                and unquote(fragment) not in anchors(dest.read_text(errors="replace"))
            ):
                status = "broken"
                reason = "missing local anchor"
        else:
            continue
        if status != "ok":
            findings.append({"file": str(p), "line": n, "target": target, "status": status, "reason": reason})
    return {"links": len(links), "unique_remote_urls": len(urls), "findings": findings, "responses": responses}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, action="append", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--local-only", action="store_true")
    args = parser.parse_args()
    result = inspect(args.root, not args.local_only)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k not in {"findings", "responses"}}))
    print(
        "broken",
        sum(v["status"] == "broken" for v in result["findings"]),
        "unverified",
        sum(v["status"] == "unverified" for v in result["findings"]),
    )
    raise SystemExit(1 if any(f["status"] == "broken" or not args.local_only for f in result["findings"]) else 0)
