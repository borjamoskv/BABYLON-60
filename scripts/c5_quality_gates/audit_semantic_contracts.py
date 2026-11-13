#!/usr/bin/env python3
"""Detect known contract regressions; lexical checks do not prove semantic consistency.

Scope: central governance documents/links, workspace rules, available global
skills and SQLite/IO quality gates. --workspace-only excludes default host skills.
Archives are excluded. No dependencies or external effects.
"""

from __future__ import annotations

import argparse
import ast
from dataclasses import dataclass
from pathlib import Path
import re
import sys
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from scripts.c5_quality_gates.governance_documents import GOVERNANCE_DOCUMENTS, validate_local_links
elif __package__:
    from .governance_documents import GOVERNANCE_DOCUMENTS, validate_local_links
else:
    from governance_documents import GOVERNANCE_DOCUMENTS, validate_local_links


@dataclass(frozen=True)
class SemanticViolation:
    file_path: Path
    line: int
    rule_id: str
    message: str


PATTERNS = (
    (
        "SEM-001",
        r"(?:cualquier modificaci[oó]n de c[oó]digo|toda mutaci[oó]n causal exige|modificaci[oó]n de c[oó]digo, despliegues)",
        "Biometric scope must exclude ordinary authorized workspace edits.",
    ),
    (
        "SEM-002",
        r"(?:emitir[aá]? un diagn[oó]stico|emite un diagn[oó]stico|inferir estados? (?:biol[oó]gicos?|fisiol[oó]gicos?)|corta(?:r[aá]?)? (?:inmediatamente )?la conversaci[oó]n|peligro inminente de .?burnout)",
        "Unmeasured operator diagnosis or unilateral session termination.",
    ),
    (
        "SEM-004",
        r"(?:hipervisor f[ií]sico|hypervisor de silicio|cada respuesta final termina con|firma[^.\n]*en cada respuesta sin excepci[oó]n)",
        "Physical identity or unconditional signature claim.",
    ),
    (
        "SEM-005",
        r"(?:(?:coste|costo) de landauer cero|zero landauer cost|evasi[oó]n total de jetsam|disipaci[oó]n de anerg[ií]a colapsada a cero)",
        "Unsupported absolute physical guarantee.",
    ),
    (
        "SEM-007",
        r"(?:OBLIGADO[^\n]*copiar[^\n]*\.git/hooks/pre-commit)",
        "Automatic replacement of an existing Git hook.",
    ),
    (
        "SEM-008",
        r"(?:force remove[^\n]*without prompting|SHALL NEVER pause execution to request Operator permission)",
        "Destructive workflow removes the operator authorization boundary.",
    ),
    (
        "SEM-009",
        r"(?:escaneo de transcripciones pasadas[^\n]*claves|gluc[oó]geno se agot[oó]|coste de CPU cero)",
        "Transcript secret harvesting or an unsupported physiological/resource claim.",
    ),
    (
        "SEM-010",
        r"(?:ejecutar inmediatamente la fase de migraci[oó]n|ejecuta este script bash para consolidar|cuota garantizada)",
        "Automatic migration or guaranteed quota claim needs an explicit, verifiable scope.",
    ),
)
NEGATION = re.compile(r"\b(?:no|nunca|jam[aá]s|prohibid[oa])\b", re.I)
DEPLOY = re.compile(r"(?:wrangler\s+(?:deploy|secret\s+put)|ejecuta directamente el despliegue)", re.I)
GUARD = re.compile(r"(?:contrato de (?:despliegue|autorizaci[oó]n)|PRIVILEGED_MUTATION|atestaci[oó]n)", re.I)
ACOUSTIC_CONTEXT = re.compile(r"\b(?:ac[uú]stic[oa]|audio|DSP|mezcla|masterizaci[oó]n|LUFS|dBFS)\b", re.I)
BIOLOGICAL_CONTEXT = re.compile(
    r"\b(?:operador|usuario|biol[oó]gic[oa]|fisiol[oó]gic[oa]|cl[ií]nic[oa]|gluc[oó]geno|cortisol|dopamina|burnout)\b",
    re.I,
)
CLAUSE_BOUNDARY = re.compile(r"[.!?;\n]|\b(?:pero|sino|excepto|salvo|sin embargo|but|except|unless)\b", re.I)


def scan_markdown_files(paths: Iterable[Path]) -> list[SemanticViolation]:
    violations = []
    for path in paths:
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            violations.append(SemanticViolation(path, 0, "IO-READ-ERROR", str(exc)))
            continue
        # Join wrapped prose within a paragraph; guards belong to the same sentence.
        for paragraph in re.finditer(r"\S[^\n]*(?:\n(?!\s*\n)[^\n]+)*", content):
            for rule_id, pattern, message in PATTERNS:
                for match in re.finditer(pattern, paragraph.group(), re.I):
                    prefix = paragraph.group()[: match.start()]
                    sentence = CLAUSE_BOUNDARY.split(prefix)[-1]
                    if NEGATION.search(sentence):
                        continue
                    suffix = CLAUSE_BOUNDARY.split(paragraph.group()[match.end() :])[0]
                    clause = sentence + match.group() + suffix
                    # A signal diagnosis is allowed; audio words must not hide an operator diagnosis.
                    if (
                        rule_id == "SEM-002"
                        and ACOUSTIC_CONTEXT.search(clause)
                        and not BIOLOGICAL_CONTEXT.search(clause)
                    ):
                        continue
                    offset = paragraph.start() + match.start()
                    violations.append(SemanticViolation(path, content.count("\n", 0, offset) + 1, rule_id, message))
        section = ""
        syntax_examples = "syntax examples, not execution orders" in content.lower()
        in_fence = False
        ordered = False
        for number, line in enumerate(content.splitlines(), 1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if not in_fence and line.startswith("#"):
                section = ""
                if not in_fence:
                    ordered = False
            section += line + "\n"
            imperative = bool(
                re.search(
                    r"\b(?:execute|run|ejecuta|ejecutar|ejecute|must|shall|automatically|inmediatamente|obligatorio|debe ejecutar)\b",
                    line,
                    re.I,
                )
            )
            if not in_fence and line.strip() and not line.lstrip().startswith("|"):
                ordered = imperative if re.match(r"^\s*\d+[.)]\s", line) else ordered or imperative
            commands = list(DEPLOY.finditer(line))
            hazardous = any(
                not (
                    "deploy" in m.group().lower()
                    and re.search(r"--dry-run\b", re.split(r";|&&|\|\|", line[m.end() :])[0])
                )
                for m in commands
            )
            reference = syntax_examples or bool(
                re.search(r"^#+\s+(?:examples?|ejemplos?|quick reference)\b", section, re.I)
            )
            descriptive = reference and not (imperative or ordered)
            if hazardous and not descriptive and not GUARD.search(section):
                violations.append(
                    SemanticViolation(
                        path, number, "SEM-003", "Deployment recipe lacks a preceding authorization contract."
                    )
                )
    return violations


def _success_literal(node: ast.expr | None) -> bool:
    if isinstance(node, ast.Constant):
        return node.value is True or (type(node.value) is int and node.value == 0)
    if isinstance(node, (ast.Tuple, ast.List)):
        return bool(node.elts) and all(_success_literal(item) for item in node.elts)
    return False


def _handler_returns(nodes: list[ast.stmt]) -> Iterable[ast.Return]:
    for node in nodes:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        if isinstance(node, ast.Return):
            yield node
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.stmt):
                yield from _handler_returns([child])
            elif isinstance(child, ast.ExceptHandler):
                yield from _handler_returns(child.body)


def scan_python_fail_open(paths: Iterable[Path]) -> list[SemanticViolation]:
    violations = []
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(SemanticViolation(path, 0, "AST-PARSE-ERROR", str(exc)))
            continue
        sqlite_names = {"sqlite3"}
        error_names = {"OSError", "IOError"}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                sqlite_names.update(a.asname or a.name for a in node.names if a.name == "sqlite3")
            if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
                error_names.update(a.asname or a.name for a in node.names if a.name.endswith("Error"))
        for handler in ast.walk(tree):
            if not isinstance(handler, ast.ExceptHandler):
                continue
            types = list(ast.walk(handler.type)) if handler.type else []
            io_handler = any(
                (isinstance(t, ast.Name) and t.id in error_names)
                or (
                    isinstance(t, ast.Attribute)
                    and isinstance(t.value, ast.Name)
                    and t.value.id in sqlite_names
                    and t.attr.endswith("Error")
                )
                for t in types
            )
            if not io_handler:
                continue
            for returned in _handler_returns(handler.body):
                if _success_literal(returned.value):
                    violations.append(
                        SemanticViolation(
                            path, returned.lineno, "AST-006", "SQLite/IO error converted into a success literal."
                        )
                    )
    return violations


def iter_skill_markdown_files(roots: Iterable[Path]) -> Iterable[Path]:
    """Follow linked skill folders once; fail on unreadable or broken scope."""
    excluded = {"_archive", "archive", "node_modules", ".git"}
    visited: set[tuple[int, int]] = set()

    def visit(directory: Path) -> Iterable[Path]:
        info = directory.stat()
        identity = (info.st_dev, info.st_ino)
        if identity in visited:
            return
        visited.add(identity)
        for child in sorted(directory.iterdir()):
            if child.name in excluded:
                continue
            if child.is_symlink() and not child.exists():
                raise OSError(f"Broken skill reference: {child}")
            if child.is_dir():
                yield from visit(child)
            elif child.name in {"SKILL.md", "MODULE.md"}:
                yield child

    for root in roots:
        yield from visit(root)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path(__file__).absolute().parents[2])
    parser.add_argument(
        "--skills-root",
        type=Path,
        action="append",
        help="Additional skills roots; repeat to scan multiple libraries (must exist)",
    )
    parser.add_argument("--workspace-only", action="store_true", help="Explicitly omit the default Antigravity library")
    parser.add_argument(
        "--public-projection",
        action="store_true",
        help="Public tree: .agents/rules is vault-only (scripts/verify_release.sh); report it NOT_CHECKED if absent",
    )
    args = parser.parse_args()
    root = args.repo_root
    rules, skills = root / ".agents/rules", root / ".agents/skills"
    gates = root / "scripts/c5_quality_gates"
    required = (skills, gates) if args.public_projection and not rules.is_dir() else (rules, skills, gates)
    if rules not in required:
        print(f"NOT_CHECKED: vault-only workspace rules absent from public projection: {rules}")
    for directory in required:
        if not directory.is_dir():
            print(f"NO_VERIFICADO: missing scope: {directory}", file=sys.stderr)
            return 2
    try:
        governance = [root / name for name in GOVERNANCE_DOCUMENTS] + sorted(rules.glob("*.md"))
        markdown = governance + list(iter_skill_markdown_files([skills]))
    except OSError as exc:
        print(f"NO_VERIFICADO: {exc}", file=sys.stderr)
        return 2
    extra_roots = list(args.skills_root or [])
    if not args.workspace_only:
        default_global = Path.home() / ".gemini/config/skills"
        if default_global.is_dir():
            extra_roots.append(default_global)
        else:
            print(f"NOT_CHECKED: optional global library unavailable: {default_global}")
    for directory in extra_roots:
        if not directory.is_dir():
            print(f"NO_VERIFICADO: missing requested skills root: {directory}", file=sys.stderr)
            return 2
        try:
            discovered = list(iter_skill_markdown_files([directory]))
        except OSError as exc:
            print(f"NO_VERIFICADO: {exc}", file=sys.stderr)
            return 2
        if not discovered:
            print(f"NO_VERIFICADO: no skill documents in requested root: {directory}", file=sys.stderr)
            return 2
        print(f"Scope: {directory} ({len(discovered)} skill documents)")
        markdown.extend(discovered)
    markdown = sorted(set(markdown))
    python = [p for p in gates.rglob("*.py") if p.name != Path(__file__).name]
    violations = scan_markdown_files(markdown) + scan_python_fail_open(python)
    link_errors = validate_local_links(governance)
    for v in violations:
        print(f"{v.file_path}:{v.line}: {v.rule_id}: {v.message}", file=sys.stderr)
    for error in link_errors:
        print(error, file=sys.stderr)
    if violations or link_errors:
        return 1
    print(
        f"PASS: known semantic patterns ({len(markdown)} documents, {len(python)} Python files), "
        f"local links/anchors in {len(governance)} governance documents; "
        "not a proof of semantic consistency or runtime."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
