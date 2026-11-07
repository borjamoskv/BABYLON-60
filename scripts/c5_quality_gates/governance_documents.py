"""Bounded local governance inventory and Markdown link checks; never fetch URLs."""

from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

ROOT_INSTRUCTIONS = (".babylon60rules", "AGENTS.md")
MAX_ROOT_INSTRUCTION_BYTES = 10_183
GOVERNANCE_DOCUMENTS = ROOT_INSTRUCTIONS + (
    "docs/03_guides/agent_contracts.md",
    "docs/03_guides/guide_agent_workflow.md",
    "docs/03_guides/guide_portable_signature.md",
    "01_KISH_ENGINE/babylon60/presentation.md",
    "01_KISH_ENGINE/babylon60/session_profile.md",
    "01_KISH_ENGINE/babylon60/mcp_instructions.md",
)
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})")
INLINE_LINK = re.compile(r"!?\[[^\]\n]*\]\(\s*(<[^>\n]+>|[^\s)]+)(?:\s+['\"][^\n]*?['\"])?\s*\)")
REFERENCE = re.compile(r"^\s{0,3}\[([^\]]+)\]:\s*(<[^>\n]+>|\S+)", re.M)
REFERENCE_USE = re.compile(r"!?\[([^\]\n]+)\](?:\[([^\]\n]*)\])?(?!\s*\()")


def prose_lines(text: str) -> list[tuple[int, str]]:
    """Retain line numbers, excluding fenced examples and inline code."""
    lines = []
    fence = ""
    for number, line in enumerate(text.splitlines(), 1):
        match = FENCE.match(line)
        if match:
            marker = match.group(1)
            if not fence:
                fence = marker
            elif marker[0] == fence[0] and len(marker) >= len(fence) and not line[match.end():].strip():
                fence = ""
            continue
        if not fence:
            lines.append((number, re.sub(r"(`+).*?\1", "", line)))
    return lines


def markdown_anchors(text: str) -> set[str]:
    """GitHub-style heading slugs, duplicate suffixes and explicit HTML anchors."""
    anchors: set[str] = set()
    # Keep the text of code spans in headings (unlike prose link extraction).
    text = re.sub(r"`([^`\n]+)`", r"\1", text)
    previous = ""
    for _, line in prose_lines(text):
        for match in re.finditer(r"\b(?:id|name)=[\"']([^\"']+)[\"']", line):
            anchors.add(match.group(1))
        heading = re.match(r"^ {0,3}#{1,6}\s+(.+?)(?:\s+#+)?\s*$", line)
        title = heading.group(1) if heading else previous if re.fullmatch(r" {0,3}(?:=+|-+)\s*", line) else None
        if title:
            title = re.sub(r"<[^>]+>", "", title)
            title = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", title)
            slug = re.sub(r"[^\w\- ]", "", title.lower()).replace(" ", "-")
            candidate, suffix = slug, 0
            while candidate in anchors:
                suffix += 1
                candidate = f"{slug}-{suffix}"
            anchors.add(candidate)
        previous = line.strip()
    return anchors


def validate_local_links(paths: list[Path]) -> list[str]:
    """Check only explicit local links in these documents, not a recursive crawl."""
    errors = []
    anchor_cache: dict[Path, set[str]] = {}
    for path in paths:
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            errors.append(f"{path}: unreadable document: {exc}")
            continue
        lines = prose_lines(text)
        definitions = {
            match.group(1).casefold(): match.group(2).strip("<>")
            for _, line in lines for match in REFERENCE.finditer(line)
        }
        for number, line in lines:
            links = [match.group(1).strip("<>") for match in INLINE_LINK.finditer(line)]
            definition = REFERENCE.match(line)
            if definition:
                links.append(definition.group(2).strip("<>"))
            else:
                for match in REFERENCE_USE.finditer(line):
                    label = (match.group(2) or match.group(1)).casefold()
                    if label in definitions:
                        links.append(definitions[label])
                    elif match.group(2) is not None:
                        errors.append(f"{path}:{number}: undefined link reference: {label}")
            for target in links:
                try:
                    url = urlsplit(target)
                    if url.scheme or url.netloc:
                        continue
                    destination = path.parent / unquote(url.path) if url.path else path
                    if not destination.exists():
                        errors.append(f"{path}:{number}: missing local target: {target}")
                        continue
                    if url.fragment:
                        if destination not in anchor_cache:
                            anchor_cache[destination] = markdown_anchors(destination.read_text(encoding="utf-8"))
                        if unquote(url.fragment) not in anchor_cache[destination]:
                            errors.append(f"{path}:{number}: missing local anchor: {target}")
                except (OSError, UnicodeError, ValueError) as exc:
                    errors.append(f"{path}:{number}: unreadable local target {target}: {exc}")
    return errors
