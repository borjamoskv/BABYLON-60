"""Check instruction files, direct symlinks and MCP registrations; optionally a response signature."""

import argparse
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import unicodedata

EXPECTED_LINE = "[ TOPOLOGÍA ACTIVA ]: MOSKV-1"
TOPOLOGY_LINE = re.compile(r"^[ \t]*\[ TOPOLOGÍA ACTIVA \]:[^\r\n]*", re.MULTILINE)
FOOTER_FIELDS = (
    "[ LLM ]: ",
    "[ MODO COGNITIVO ]: ",
    "[ TOPOLOGÍA ACTIVA ]: ",
    "[ RÉGIMEN TÉRMICO ]: ",
    "[ EXERGÍA INFORMATIVA ]: ",
    "[ MUTACIÓN CAUSAL ]: ",
)
FENCE = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})(.*)$")
FIELD_NAMES = tuple(field[2:-4] for field in FOOTER_FIELDS)
V2_FIELD_NAMES = FIELD_NAMES + ("VERIFICACIÓN", "CAMBIOS", "LÍMITES")
V2_REQUIRED_FIELDS = ("TOPOLOGÍA ACTIVA", "LLM")
V2_SOURCED_FIELDS = ("LLM", "MODO COGNITIVO", "VERIFICACIÓN", "RÉGIMEN TÉRMICO", "EXERGÍA INFORMATIVA")
V2_CONTEXT_FIELDS = ("VERIFICACIÓN", "CAMBIOS", "LÍMITES")
VISUAL_START = "visualize"
VISUAL_END = ""
MAX_VISUAL_BYTES = 1024 * 1024


def validate_values(field_values: dict[str, str], require_selector_verdict: bool) -> list[str]:
    errors = []
    for name, value in field_values.items():
        if not value:
            errors.append(f"Signature field must be nonempty: {name}")
        if re.search(r"<[^<>]*>|\{\{.*?\}\}", value) or value.casefold() in {
            "pendiente", "pending", "tbd", "todo", "por definir", "por completar", "...", "…",
        }:
            errors.append(f"Signature field contains an unresolved placeholder: {name}")
        if any(unicodedata.category(char) in {"Cc", "Cf"} for char in value):
            errors.append(f"Signature field contains invisible control characters: {name}")
    if require_selector_verdict:
        for name in ("LLM", "MODO COGNITIVO"):
            value = field_values.get(name, "")
            if value and value.casefold() != "no expuesto" and not re.search(
                r"\b(?:ÓPTIMO|DESAJUSTADO|No evaluable)\b", value, re.IGNORECASE
            ):
                errors.append(f"Signature field {name} must declare ÓPTIMO, DESAJUSTADO or No evaluable verdict")
    return errors


@dataclass
class SignatureElement:
    tag: str
    hidden: bool
    field: str | None
    source: str | None
    root: int | None
    is_root: bool

    @property
    def contains_signature(self) -> bool:
        return self.field is not None or self.source is not None or self.is_root


class VisualSignatureParser(HTMLParser):
    """Read declared signature data; reject obvious hiding without certifying CSS or evidence."""

    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}
    NONVISIBLE_TAGS = {"head", "script", "style", "template"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[SignatureElement] = []
        self.values: dict[str, list[str]] = {}
        self.sources: dict[str, list[str]] = {}
        self.value_roots: dict[str, int | None] = {}
        self.source_roots: dict[str, int | None] = {}
        self.roots: list[tuple[str | None, str | None]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        hidden = tag in self.NONVISIBLE_TAGS or any(frame.hidden for frame in self.stack)
        for key, value in attrs:
            if key == "hidden" or (key == "aria-hidden" and (value or "").strip().casefold() == "true"):
                hidden = True
            if key == "style" and re.search(
                r"(?:^|;)\s*(?:display\s*:\s*none|(?:content-)?visibility\s*:\s*hidden|opacity\s*:\s*0(?:\.0*)?)(?:\s*!important)?\s*(?:;|$)",
                value or "", re.IGNORECASE,
            ):
                hidden = True
        versions = [value for key, value in attrs if key == "data-signature-version"]
        root = self.stack[-1].root if self.stack else None
        if versions:
            dates = [value for key, value in attrs if key == "data-signature-observed-at"]
            if len(versions) != 1 or len(dates) > 1 or (versions[0] == "2" and len(dates) != 1):
                self.errors.append("Visual signature root requires a unique version and a v2 observation timestamp")
            root = len(self.roots)
            self.roots.append((versions[0], dates[0] if dates else None))
        fields = [value for key, value in attrs if key == "data-signature-field"]
        sources = [value for key, value in attrs if key == "data-signature-source"]
        name = fields[0] if fields else None
        source = sources[0] if sources else None
        if fields and sources:
            self.errors.append("Visual signature fields and sources must use separate elements")
        inside_value = any(frame.field is not None or frame.source is not None for frame in self.stack)
        for attributes, label, values, roots in (
            (fields, "field", self.values, self.value_roots),
            (sources, "source", self.sources, self.source_roots),
        ):
            if not attributes:
                continue
            field_key = attributes[0]
            if len(attributes) != 1 or field_key not in V2_FIELD_NAMES or field_key in values:
                self.errors.append(f"Expected one unique known visual signature {label}: {field_key}")
            elif field_key is not None:
                values[field_key] = []
                roots[field_key] = root
            if hidden:
                self.errors.append(f"Visual signature {label} must be visible: {field_key}")
            if inside_value:
                self.errors.append("Visual signature fields and sources must not be nested")
            if label == "field" and field_key in V2_CONTEXT_FIELDS and any(frame.tag == "details" for frame in self.stack):
                self.errors.append(f"Visual signature context must be outside disclosure details: {field_key}")
        if hidden and inside_value:
            self.errors.append("Visual signature value must not contain hidden content")
        if tag not in self.VOID_TAGS:
            self.stack.append(SignatureElement(tag, hidden, name, source, root, bool(versions)))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        for position in range(len(self.stack) - 1, -1, -1):
            if self.stack[position].tag == tag:
                if position != len(self.stack) - 1 and any(frame.contains_signature for frame in self.stack[position:]):
                    self.errors.append("Visual signature fields must have balanced HTML tags")
                del self.stack[position:]
                break

    def handle_data(self, data: str) -> None:
        if any(frame.hidden for frame in self.stack):
            return
        for frame in self.stack:
            if frame.field is not None and frame.field in self.values:
                self.values[frame.field].append(data)
            if frame.source is not None and frame.source in self.sources:
                self.sources[frame.source].append(data)


def validate_visual_schema(parser: VisualSignatureParser) -> list[str]:
    """Validate v2 declarations and scope, not their truth, freshness, or rendered CSS."""
    errors: list[str] = []
    if len(parser.roots) > 1:
        errors.append("Expected exactly one visual signature root")
    version, observed_at = parser.roots[0] if parser.roots else (None, None)
    if parser.roots and version not in {"1", "2"}:
        errors.append("Unsupported visual signature version; expected 1 or 2")
    if version != "2":
        for name in parser.values:
            if name not in FIELD_NAMES:
                errors.append(f"Legacy visual signature contains an unknown field: {name}")
        if parser.sources:
            errors.append("Visual signature sources require an explicit v2 root")
        return errors
    if not observed_at or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-](?:[01]\d|2[0-3]):[0-5]\d)", observed_at
    ):
        errors.append("Visual signature observation requires an ISO8601 timestamp with timezone")
    else:
        try:
            observed = datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
            if observed.utcoffset() is None:
                raise ValueError("missing timezone")
        except ValueError:
            errors.append("Visual signature observation timestamp is invalid")
    for label, roots in (("field", parser.value_roots), ("source", parser.source_roots)):
        for name, root in roots.items():
            if root != 0:
                errors.append(f"Visual signature {label} must be inside its v2 root: {name}")
    for name in V2_SOURCED_FIELDS:
        if name in parser.values and name not in parser.sources:
            errors.append(f"Visual signature field requires a declared source: {name}")
    for name in parser.sources:
        if name not in parser.values:
            errors.append(f"Visual signature source has no corresponding field: {name}")
    return errors


def validate_visual_response(text: str, require_selector_verdict: bool) -> list[str]:
    errors = []
    if unclosed_fence(text):
        errors.append("The response contains an unclosed Markdown code fence")
    for name in V2_FIELD_NAMES:
        if re.search(r"\[\s*" + re.escape(name) + r"\s*\]:", text):
            errors.append(f"A visual signature must not duplicate textual signature fields: {name}")
    line = text.rstrip().splitlines()[-1]
    if not line.startswith(VISUAL_START) or not line.endswith(VISUAL_END):
        return errors + ["The visual signature must be the final standalone response directive"]
    try:
        payload = json.loads(line[len(VISUAL_START):-len(VISUAL_END)])
        if not isinstance(payload, dict) or set(payload) != {"path"} or not isinstance(payload["path"], str):
            raise ValueError("expected a single path string")
        path = Path(payload["path"])
        if not path.is_absolute() or path.suffix.lower() != ".html":
            raise ValueError("visual signature path must be absolute and end in .html")
        with os.fdopen(os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK), "rb") as panel:
            if not stat.S_ISREG(os.fstat(panel.fileno()).st_mode):
                raise ValueError("visual signature must reference a regular file")
            data = panel.read(MAX_VISUAL_BYTES + 1)
        if len(data) > MAX_VISUAL_BYTES:
            raise ValueError("visual signature exceeds the 1 MiB size limit")
        html = data.decode("utf-8")
    except (OSError, ValueError, UnicodeError) as error:
        return errors + [f"Unreadable visual signature: {error}"]
    parser = VisualSignatureParser()
    parser.feed(html)
    parser.close()
    errors.extend(parser.errors)
    if any(frame.contains_signature for frame in parser.stack):
        errors.append("Visual signature fields must have balanced HTML tags")
    errors.extend(validate_visual_schema(parser))
    values = {name: "".join(parts).strip() for name, parts in parser.values.items()}
    is_v2 = bool(parser.roots) and parser.roots[0][0] == "2"
    required = V2_REQUIRED_FIELDS if is_v2 else FIELD_NAMES
    for name in required:
        if name not in values:
            errors.append(f"Expected exactly one signature field: {name}")
    for name, value in values.items():
        if re.match(r"(?:\[\s*)?" + re.escape(name) + r"(?:\s*\])?\s*:", value):
            errors.append(f"Visual signature field must contain its value without a duplicated label: {name}")
    errors.extend(validate_values(values, require_selector_verdict))
    sources = {name: "".join(parts).strip() for name, parts in parser.sources.items()}
    errors.extend(validate_values(sources, False))
    if values.get("TOPOLOGÍA ACTIVA") != "MOSKV-1":
        errors.append("The visual footer must identify literal MOSKV-1")
    return errors


def unclosed_fence(text: str) -> bool:
    opened: tuple[str, int] | None = None
    for line in text.splitlines():
        match = FENCE.match(line)
        if match is None:
            continue
        marker, suffix = match.groups()
        if opened is None:
            opened = (marker[0], len(marker))
        elif marker[0] == opened[0] and len(marker) >= opened[1] and not suffix.strip():
            opened = None
    return opened is not None


def validate_text(
    text: str,
    *,
    response: bool = False,
    require_selector_verdict: bool = False,
) -> list[str]:
    if response and text.rstrip().splitlines() and text.rstrip().splitlines()[-1].startswith(VISUAL_START):
        return validate_visual_response(text, require_selector_verdict)
    errors = []
    field_values: dict[str, str] = {}
    for field in FOOTER_FIELDS:
        name = field.split("[ ", 1)[1].split(" ]", 1)[0]
        pattern = re.compile(r"^[ \t]*\[[ \t]*" + re.escape(name) + r"[ \t]*\]:([^\r\n]*)", re.MULTILINE)
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            errors.append(f"Expected exactly one signature field: {name}")
            continue
        value = matches[0].group(1).strip()
        field_values[name] = value
    errors.extend(validate_values(field_values, require_selector_verdict))
    labels = [match.group().strip() for match in TOPOLOGY_LINE.finditer(text)]
    if labels != [EXPECTED_LINE]:
        errors.append(f"Expected exactly one literal topology line: {EXPECTED_LINE}")
    if response:
        if unclosed_fence(text):
            errors.append("The response contains an unclosed Markdown code fence")
        lines = [line.strip() for line in text.strip().splitlines()]
        size = len(FOOTER_FIELDS)
        if lines and lines[-1] == "```":
            if len(lines) < size + 2 or lines[-size - 2] != "```text":
                errors.append("The signature code block must contain only six fields and use ```text")
            lines.pop()
        footer = lines[-size:]
        if len(footer) != size or any(
            not line.startswith(field) or not line[len(field):].strip()
            for line, field in zip(footer, FOOTER_FIELDS)
        ):
            errors.append("The response must end with the six ordered nonempty signature fields")
        elif footer[2] != EXPECTED_LINE:
            errors.append("The final footer must identify MOSKV-1")
    return errors


def validate_file(
    path: Path,
    *,
    response: bool = False,
    require_selector_verdict: bool = False,
) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        return [f"{path}: {error}"]
    return [
        f"{path}: {error}"
        for error in validate_text(
            text,
            response=response,
            require_selector_verdict=require_selector_verdict,
        )
    ]


def index_file(root: Path, name: str) -> str:
    result = subprocess.run(
        ["git", "show", f":{name}"],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if result.returncode:
        raise ValueError(f"{name}: missing or unreadable in the Git index")
    return result.stdout


def validate_instruction_text(text: str) -> list[str]:
    """Documents are not signatures; detailed semantics/links have a separate gate."""
    errors = []
    if not text.strip():
        errors.append("Instruction document is empty")
    if unclosed_fence(text):
        errors.append("Instruction document contains an unclosed Markdown code fence")
    return errors


def validate_instruction_file(path: Path) -> list[str]:
    try:
        if path.is_symlink() or not path.is_file():
            return [f"{path}: expected a regular instruction file"]
        return [f"{path}: {error}" for error in validate_instruction_text(path.read_text(encoding="utf-8"))]
    except (OSError, UnicodeError) as error:
        return [f"{path}: unreadable ({error})"]


ROOT_SYMLINKS = (
    ".codexrules",
    ".cursorrules",
    ".windsurfrules",
    "CLAUDE.md",
    ".clinerules",
    ".roorules",
)
NESTED_SYMLINKS = {
    ".github/copilot-instructions.md": "../.babylon60rules",
    ".cursor/mcp.json": "../.mcp.json",
}
MCP_MANIFESTS = (
    ".mcp.json",
    ".gemini/settings.json",
    ".claude/settings.json",
    ".codex/config.toml",
)
# VS Code configuration is host-local and may be excluded by global Git ignores.
OPTIONAL_MCP_MANIFESTS = (".vscode/mcp.json",)
DEPENDENCY_LOCK_FILES = frozenset(
    {"uv.lock", "Cargo.lock", "pyproject.toml", "Cargo.toml", "package.json", "package-lock.json"}
)


def validate_lockfile_isolation(root: Path, *, staged: bool = False) -> list[str]:
    """Enforce INV_C5_CLEAN_WORKTREE_LOCK_GATE in O(1) via porcelain status."""
    if not (root / ".git").exists():
        return []
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--untracked-files=normal"],
        cwd=root,
        capture_output=True,
        text=False,
        check=True,
    )
    records = result.stdout.split(b"\0")
    mutated_locks: list[str] = []
    staged_locks: list[str] = []
    unrelated_dirty: list[str] = []
    unstaged_drift: list[str] = []
    idx = 0
    while idx < len(records):
        entry = records[idx]
        idx += 1
        if len(entry) < 4:
            continue
        xy = entry[:2].decode("ascii", errors="replace")
        path = entry[3:].decode("utf-8", errors="surrogateescape")
        if "R" in xy or "C" in xy:
            idx += 1
        x_status, y_status = xy[0], xy[1]
        if Path(path).name in DEPENDENCY_LOCK_FILES:
            mutated_locks.append(path)
            if x_status not in {" ", "?"}:
                staged_locks.append(path)
            if y_status != " ":
                unstaged_drift.append(path)
        else:
            unrelated_dirty.append(path)
            if y_status != " " or xy == "??":
                unstaged_drift.append(path)
    if not mutated_locks:
        return []
    prefix = "index:" if staged else ""
    if unrelated_dirty:
        locks = ", ".join(mutated_locks)
        dirty = ", ".join(unrelated_dirty[:5])
        return [
            f"{prefix}INV_C5_CLEAN_WORKTREE_LOCK_GATE: dependency/lockfile mutation ({locks}) "
            f"forbidden on a dirty worktree ({dirty})"
        ]
    if staged and staged_locks and unstaged_drift:
        locks = ", ".join(staged_locks)
        drift = ", ".join(unstaged_drift[:5])
        return [
            f"{prefix}INV_C5_CLEAN_WORKTREE_LOCK_GATE: staged dependency/lockfile mutation ({locks}) "
            f"requires a clean unstaged worktree ({drift})"
        ]
    return []


def validate_mcp_manifests(root: Path, *, staged: bool = False) -> list[str]:
    errors: list[str] = []
    launch_script = "scripts/c5_cli/launch_kernel_mcp.py"
    for rel_path in MCP_MANIFESTS + OPTIONAL_MCP_MANIFESTS:
        path = root / rel_path
        if not staged and not path.is_file():
            if rel_path in OPTIONAL_MCP_MANIFESTS and not path.exists() and not path.is_symlink():
                continue
            errors.append(f"{rel_path}: missing MCP manifest file")
            continue
        try:
            content = index_file(root, rel_path) if staged else path.read_text(encoding="utf-8")
        except (OSError, UnicodeError, ValueError) as error:
            if (
                staged and rel_path in OPTIONAL_MCP_MANIFESTS
                and isinstance(error, ValueError) and not isinstance(error, UnicodeError)
            ):
                continue
            errors.append(f"{rel_path}: unreadable ({error})")
            continue
        if "/Users/" in content:
            errors.append(f"{rel_path}: contains forbidden absolute user path '/Users/'")
        if rel_path == ".claude/settings.json":
            if "babylon60-kernel" not in content:
                errors.append(f"{rel_path}: missing 'babylon60-kernel' registration")
        else:
            if launch_script not in content:
                errors.append(f"{rel_path}: does not reference '{launch_script}'")
    return errors


def index_modes(root: Path) -> dict[str, str]:
    result = subprocess.run(
        [
            "git",
            "ls-files",
            "--stage",
            "-z",
            "--",
            ".babylon60rules",
            "AGENTS.md",
            *ROOT_SYMLINKS,
            *NESTED_SYMLINKS.keys(),
        ],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    )
    modes = {}
    for record in result.stdout.split("\0"):
        if not record:
            continue
        metadata, name = record.split("\t", 1)
        mode, _object_id, stage = metadata.split()
        if stage != "0":
            raise ValueError(f"index:{name}: unresolved merge conflict")
        modes[name] = mode
    return modes


def validate_index(root: Path) -> list[str]:
    errors: list[str] = []
    try:
        modes = index_modes(root)
        for name in (".babylon60rules", "AGENTS.md"):
            if modes.get(name) not in {"100644", "100755"}:
                errors.append(f"index:{name}: expected a regular instruction file")
                continue
            errors.extend(f"index:{name}: {error}" for error in validate_instruction_text(index_file(root, name)))
        for name in ROOT_SYMLINKS:
            if modes.get(name) != "120000" or index_file(root, name) != ".babylon60rules":
                errors.append(f"index:{name}: expected a direct symlink to .babylon60rules")
        for name, target in NESTED_SYMLINKS.items():
            if modes.get(name) != "120000" or index_file(root, name) != target:
                errors.append(f"index:{name}: expected a direct symlink to {target}")
        errors.extend(f"index:{error}" for error in validate_mcp_manifests(root, staged=True))
        errors.extend(validate_lockfile_isolation(root, staged=True))
    except (OSError, ValueError, UnicodeError, subprocess.CalledProcessError) as error:
        errors.append(str(error))
    return errors


def validate_worktree(root: Path) -> list[str]:
    errors = []
    for name in (".babylon60rules", "AGENTS.md"):
        errors.extend(validate_instruction_file(root / name))
    targets = {name: ".babylon60rules" for name in ROOT_SYMLINKS} | NESTED_SYMLINKS
    for name, target in targets.items():
        link = root / name
        try:
            if not link.is_symlink() or link.readlink() != Path(target):
                errors.append(f"{link}: expected a direct symlink to {target}")
        except OSError as error:
            errors.append(f"{link}: unreadable symlink ({error})")
    errors.extend(validate_mcp_manifests(root))
    try:
        errors.extend(validate_lockfile_isolation(root, staged=False))
    except (OSError, subprocess.CalledProcessError) as error:
        errors.append(str(error))
    return errors


def self_test() -> int:
    values = ("GPT-6.1 Sol", "Alto", "MOSKV-1", "No medido", "No medida", "Ninguna")
    footer = "\n".join(field + value for field, value in zip(FOOTER_FIELDS, values))
    valid = "Respuesta.\n\n```text\n" + footer + "\n```\n"
    cases = [(valid, True), ("Respuesta.\n" + footer, True)]
    for model, mode in (("Claude Sonnet", "Extended thinking"), ("Gemini", "Thinking"), ("No expuesto", "No expuesto")):
        cases.append((valid.replace("GPT-6.1 Sol", model).replace("Alto", mode), True))
    for topology in ("Codex", "GPT-6", "<Modelo>", "MOSKV-1 (Codex)", "moskv-1", ""):
        cases.append((valid.replace("MOSKV-1", topology), False))
    for field, value in zip(FOOTER_FIELDS, values):
        line = field + value
        cases.extend([
            (valid.replace(line + "\n", ""), False),
            (valid.replace(line, field), False),
            (valid.replace(line, line + "\n" + line), False),
        ])
        for placeholder in ("<valor>", "Pendiente", "TBD", "{{value}}", "…"):
            cases.append((valid.replace(line, field + placeholder), False))
    cases.extend([
        (valid + "Texto después de la firma\n", False),
        (valid.replace("[ LLM ]: GPT-6.1 Sol\n[ MODO COGNITIVO ]: Alto", "[ MODO COGNITIVO ]: Alto\n[ LLM ]: GPT-6.1 Sol"), False),
        (valid.replace("```text", "```"), False),
        (valid.removesuffix("```\n"), False),
        (valid.replace("Alto", "Alto\u200b"), False),
    ])
    for _ in range(100):
        for draft, accepted in cases:
            if (not validate_text(draft, response=True)) != accepted:
                raise AssertionError(f"Unexpected signature validation result: {draft!r}")
    return len(cases) * 100


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument("--workspace-instructions", type=Path)
    parser.add_argument(
        "--response",
        type=Path,
        help="Validate a final response draft before sending it",
    )
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument(
        "--staged",
        action="store_true",
        help="Check instruction files, required symlinks and MCP registrations in the Git index",
    )
    parser.add_argument(
        "--require-selector-verdict",
        action="store_true",
        help="Require ÓPTIMO, DESAJUSTADO or No evaluable independently for each exposed selector field",
    )
    args = parser.parse_args()
    if args.self_test:
        if args.response or args.staged or args.workspace_instructions:
            parser.error("--self-test cannot be combined with a validation request")
        print(f"PASS: {self_test()} signature acceptance/rejection checks")
        return 0
    errors = validate_index(args.repo_root) if args.staged else validate_worktree(args.repo_root)
    if args.workspace_instructions:
        errors.extend(validate_instruction_file(args.workspace_instructions))
    if args.response:
        errors.extend(
            validate_file(
                args.response,
                response=True,
                require_selector_verdict=args.require_selector_verdict,
            )
        )
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1
    scope = "Git index" if args.staged else "worktree"
    print(f"PASS: instruction files, required direct symlinks and MCP registration references ({scope}; VS Code if present)")
    if args.response:
        print("PASS: declared response signature structure (legacy/v2); evidence and freshness not certified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
