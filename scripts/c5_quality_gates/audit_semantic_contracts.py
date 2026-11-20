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


_SUCCESS_DICT_KEYS = frozenset({"ok", "admitted", "passed", "valid", "verified"})


def _success_literal(node: ast.expr | None) -> bool:
    if isinstance(node, ast.Constant):
        return node.value is True or (type(node.value) is int and node.value == 0)
    if isinstance(node, (ast.Tuple, ast.List)):
        return bool(node.elts) and all(_success_literal(item) for item in node.elts)
    if isinstance(node, ast.Dict):
        return any(
            isinstance(k, ast.Constant)
            and k.value in _SUCCESS_DICT_KEYS
            and isinstance(v, ast.Constant)
            and v.value is True
            for k, v in zip(node.keys, node.values)
        )
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


def _is_io_or_sqlite_handler(
    handler: ast.ExceptHandler,
    error_names: set[str],
    sqlite_names: set[str],
    has_sqlite: bool,
) -> bool:
    if handler.type is None:
        return True
    types = list(ast.walk(handler.type))
    return any(
        (isinstance(t, ast.Name) and (t.id in error_names or (has_sqlite and t.id in {"Exception", "BaseException"})))
        or (
            isinstance(t, ast.Attribute)
            and isinstance(t.value, ast.Name)
            and t.value.id in sqlite_names
            and t.attr.endswith("Error")
        )
        for t in types
    )


def _is_text_git_diff(node: ast.Call) -> bool:
    if not node.args or not isinstance(node.args[0], (ast.List, ast.Tuple)):
        return False
    elts = node.args[0].elts
    if len(elts) < 2:
        return False
    if not (
        isinstance(elts[0], ast.Constant)
        and elts[0].value == "git"
        and isinstance(elts[1], ast.Constant)
        and elts[1].value == "diff"
    ):
        return False
    return any(
        (kw.arg in {"text", "universal_newlines"} and isinstance(kw.value, ast.Constant) and kw.value.value is True)
        or (kw.arg == "encoding" and isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str))
        for kw in node.keywords
    )


_STRUCT_METHODS = frozenset({"pack", "unpack", "pack_into", "unpack_from", "iter_unpack", "Struct"})


def _is_biometric_gate_with_legacy_message(node: ast.Call) -> bool:
    has_gate = False
    has_message = False
    for child in ast.walk(node):
        if isinstance(child, ast.Constant):
            val = str(child.value)
            if "c5_biometric_gate" in val:
                has_gate = True
            if val == "--message" or val.startswith("--message=") or "--message" in val:
                has_message = True
    return has_gate and has_message


def _is_struct_with_d_specifier(node: ast.Call) -> bool:
    is_struct_call = False
    if isinstance(node.func, ast.Attribute) and node.func.attr in _STRUCT_METHODS:
        is_struct_call = True
    elif isinstance(node.func, ast.Name) and node.func.id in _STRUCT_METHODS:
        is_struct_call = True

    if not is_struct_call or not node.args:
        return False

    fmt_arg = node.args[0]
    fmt_str: str | None = None
    if isinstance(fmt_arg, ast.Constant):
        if isinstance(fmt_arg.value, str):
            fmt_str = fmt_arg.value
        elif isinstance(fmt_arg.value, bytes):
            fmt_str = fmt_arg.value.decode("ascii", errors="ignore")
    elif isinstance(fmt_arg, ast.JoinedStr):
        for val in fmt_arg.values:
            if isinstance(val, ast.Constant) and isinstance(val.value, str) and "D" in val.value:
                return True

    return fmt_str is not None and "D" in fmt_str


PRAGMA_SYNCHRONOUS_FORBIDDEN_RE = re.compile(
    r"\bPRAGMA\s+synchronous\s*=\s*(?:NORMAL|OFF|0|1)\b",
    re.IGNORECASE,
)
CANONICAL_HASH_FN_RE = re.compile(
    r"(?:canonical_.*hash|bft_.*hash|merkle_.*leaf|canonical_digest|event_identity|compute_canonical|canonical_event_id)",
    re.I,
)
_HASH_METHODS = frozenset({"sha256", "sha3_256", "blake2b", "blake2s", "md5", "sha1", "digest", "hexdigest", "update"})


def _is_physical_clock_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    if isinstance(node.func, ast.Attribute):
        if (
            node.func.attr in {"time", "time_ns"}
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "time"
        ):
            return True
        if node.func.attr in {"now", "utcnow"}:
            return True
    return False


def _is_docstring(node: ast.Constant, tree: ast.AST) -> bool:
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            if parent.body and isinstance(parent.body[0], ast.Expr) and parent.body[0].value is node:
                return True
    return False


_SEC1_TERMS = frozenset({"sec1", "x962", "raw_point", "p256_point", "uncompressed_point", "uncompressedpoint"})
_COMPRESSED_TERMS = frozenset({"compressed_point", "compressedpoint", "sec1_compressed"})
_SPKI_DER_TERMS = frozenset({"spki", "der", "x509", "asn1", "subjectpublickeyinfo", "subject_public_key_info"})
_NORMALIZE_TERMS = frozenset(
    {
        "normalize",
        "to_sec1",
        "from_encoded_point",
        "same_public_key",
        "extract_sec1",
        "der_to_sec1",
        "spki_to_sec1",
    }
)


def _ast_tokens_lower(node: ast.AST) -> set[str]:
    tokens: set[str] = set()
    for child in ast.walk(node):
        if isinstance(child, ast.Name):
            tokens.add(child.id.lower())
        elif isinstance(child, ast.Attribute):
            tokens.add(child.attr.lower())
        elif isinstance(child, ast.Constant) and isinstance(child.value, str):
            tokens.add(child.value.lower())
    return tokens


def _has_compressed_term(text: str) -> bool:
    cleaned = text.replace("uncompressed_point", "").replace("uncompressedpoint", "").replace("uncompressed", "")
    return any(c in cleaned for c in _COMPRESSED_TERMS)


def _classify_key_expr(expr: ast.AST, env: dict[str, set[str]] | None = None) -> set[str]:
    if isinstance(expr, ast.Call):
        func_name = ""
        if isinstance(expr.func, ast.Name):
            func_name = expr.func.id
        elif isinstance(expr.func, ast.Attribute):
            func_name = expr.func.attr
        func_lower = func_name.lower()

        if func_name == "public_bytes":
            arg_nodes: list[ast.AST] = [*expr.args, *(kw.value for kw in expr.keywords)]
            tokens = {tok for arg in arg_nodes for tok in _ast_tokens_lower(arg)}
            if any(_has_compressed_term(tok) for tok in tokens):
                return {"sec1_compressed"}
            if any(any(s in tok for s in _SEC1_TERMS) for tok in tokens):
                return {"sec1"}
            if any(any(d in tok for d in _SPKI_DER_TERMS) for tok in tokens):
                return {"spki_der"}

        if any(n in func_lower for n in _NORMALIZE_TERMS):
            return {"sec1_normalized"}

        if func_lower in {"importkey", "import_key"} and expr.args:
            first_tokens = _ast_tokens_lower(expr.args[0])
            if any(t in {"raw", *_SEC1_TERMS} for t in first_tokens):
                return {"sec1"}
            if any(t in _SPKI_DER_TERMS for t in first_tokens):
                return {"spki_der"}

        if "load_der_public_key" in func_lower or "to_der" in func_lower or "to_spki" in func_lower:
            return {"spki_der"}

        formats: set[str] = set()
        if isinstance(expr.func, ast.Attribute):
            formats.update(_classify_key_expr(expr.func.value, env))
        for arg in expr.args:
            formats.update(_classify_key_expr(arg, env))
        for kw in expr.keywords:
            formats.update(_classify_key_expr(kw.value, env))
        return formats

    if isinstance(expr, ast.Name):
        formats = set(env.get(expr.id, ())) if env else set()
        name_lower = expr.id.lower()
        if _has_compressed_term(name_lower):
            formats.add("sec1_compressed")
        elif any(t in name_lower for t in _SEC1_TERMS):
            formats.add("sec1")
        if any(t in name_lower for t in _SPKI_DER_TERMS):
            formats.add("spki_der")
        return formats

    if isinstance(expr, ast.Attribute):
        attr_lower = expr.attr.lower()
        formats = set()
        if _has_compressed_term(attr_lower):
            formats.add("sec1_compressed")
        elif any(t in attr_lower for t in _SEC1_TERMS):
            formats.add("sec1")
        if any(t in attr_lower for t in _SPKI_DER_TERMS):
            formats.add("spki_der")
        if formats:
            return formats
        return _classify_key_expr(expr.value, env)

    if isinstance(expr, ast.Constant) and isinstance(expr.value, str):
        val_lower = expr.value.lower()
        formats = set()
        if _has_compressed_term(val_lower):
            formats.add("sec1_compressed")
        elif any(t in val_lower for t in _SEC1_TERMS):
            formats.add("sec1")
        if any(t in val_lower for t in _SPKI_DER_TERMS):
            formats.add("spki_der")
        return formats

    formats = set()
    for child in ast.iter_child_nodes(expr):
        formats.update(_classify_key_expr(child, env))
    return formats


def _collect_key_format_env(tree: ast.AST) -> dict[str, set[str]]:
    env: dict[str, set[str]] = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            inferred = _classify_key_expr(node.value, env)
            if inferred:
                env[var_name] = inferred
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.value is not None:
            var_name = node.target.id
            inferred = _classify_key_expr(node.value, env)
            if inferred:
                env[var_name] = inferred
    return env


def _has_incompatible_key_formats(left_formats: set[str], right_formats: set[str]) -> bool:
    if "sec1_normalized" in left_formats or "sec1_normalized" in right_formats:
        return False
    left_sec1 = "sec1" in left_formats
    right_sec1 = "sec1" in right_formats
    left_comp = "sec1_compressed" in left_formats
    right_comp = "sec1_compressed" in right_formats
    left_spki = "spki_der" in left_formats
    right_spki = "spki_der" in right_formats

    if (left_sec1 or left_comp) and right_spki:
        return True
    if left_spki and (right_sec1 or right_comp):
        return True
    if (left_sec1 and right_comp) or (left_comp and right_sec1):
        return True
    return False


def _is_unnormalized_sec1_der_compare(node: ast.Compare, env: dict[str, set[str]] | None = None) -> bool:
    left_formats = _classify_key_expr(node.left, env)
    for comp in node.comparators:
        right_formats = _classify_key_expr(comp, env)
        if _has_incompatible_key_formats(left_formats, right_formats):
            return True
    return False


def _extract_symlink_check_target(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Attribute) and node.func.attr == "is_symlink":
        if isinstance(node.func.value, ast.Name):
            return node.func.value.id
    elif isinstance(node.func, ast.Attribute) and node.func.attr == "islink":
        if node.args and isinstance(node.args[0], ast.Name):
            return node.args[0].id
    return None


def _extract_unsafe_open_target(node: ast.AST) -> str | None:
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name) and node.func.id == "open":
        if node.args and isinstance(node.args[0], ast.Name):
            return node.args[0].id
    elif isinstance(node.func, ast.Attribute) and node.func.attr in {"open", "read_text", "read_bytes"}:
        if isinstance(node.func.value, ast.Name):
            return node.func.value.id
    return None


def _iter_scope_nodes(scope_root: ast.AST) -> list[ast.AST]:
    result: list[ast.AST] = []
    stack = [scope_root]
    while stack:
        curr = stack.pop()
        result.append(curr)
        for child in reversed(list(ast.iter_child_nodes(curr))):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            stack.append(child)
    return result


def _find_toctou_symlink_open(tree: ast.AST) -> list[tuple[int, str]]:
    """Detect TOCTOU: checking is_symlink/islink before open/read on the same target."""
    violations: list[tuple[int, str]] = []
    scopes: list[ast.AST] = [tree]
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            scopes.append(node)

    for scope in scopes:
        nodes = _iter_scope_nodes(scope)
        checks: dict[str, list[int]] = {}
        for n in nodes:
            target = _extract_symlink_check_target(n)
            n_lineno = getattr(n, "lineno", 0)
            if target and isinstance(n_lineno, int) and n_lineno > 0:
                checks.setdefault(target, []).append(n_lineno)

        if not checks:
            continue

        for n in nodes:
            target = _extract_unsafe_open_target(n)
            n_lineno = getattr(n, "lineno", 0)
            if target and target in checks and isinstance(n_lineno, int) and n_lineno > 0:
                check_lines = checks[target]
                if any(c_line <= n_lineno for c_line in check_lines):
                    violations.append(
                        (
                            n_lineno,
                            f"INV_C5_FS_DESCRIPTOR_NOFOLLOW: checking is_symlink/islink before open/read on '{target}' introduces a TOCTOU race; open descriptor directly with O_NOFOLLOW.",
                        )
                    )
    return violations


def _is_float_expr(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant) and type(node.value) is float:
        return True
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "float":
        return True
    if isinstance(node, ast.AnnAssign) and isinstance(node.annotation, ast.Name) and node.annotation.id == "float":
        return True
    if isinstance(node, ast.arg) and isinstance(node.annotation, ast.Name) and node.annotation.id == "float":
        return True
    return False


def _is_broad_or_bare_except_pass(handler: ast.ExceptHandler) -> bool:
    if len(handler.body) != 1 or not isinstance(handler.body[0], ast.Pass):
        return False
    if handler.type is None:
        return True
    return any(isinstance(t, ast.Name) and t.id in {"Exception", "BaseException"} for t in ast.walk(handler.type))


def scan_python_fail_open(paths: Iterable[Path], *, check_symlink_resolve: bool = True) -> list[SemanticViolation]:
    violations = []
    for path in paths:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as exc:
            violations.append(SemanticViolation(path, 0, "AST-PARSE-ERROR", str(exc)))
            continue
        sqlite_names = {"sqlite3"}
        has_sqlite = False
        error_names = {"OSError", "IOError"}
        ast12_lines: set[int] = set()
        ast13_lines: set[int] = set()
        ast14_lines: set[int] = set()
        ast15_lines: set[int] = set()
        ast16_lines: set[int] = set()
        for toctou_line, toctou_msg in _find_toctou_symlink_open(tree):
            if toctou_line not in ast14_lines:
                ast14_lines.add(toctou_line)
                violations.append(
                    SemanticViolation(
                        path,
                        toctou_line,
                        "AST-014",
                        toctou_msg,
                    )
                )
        key_env = _collect_key_format_env(tree)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if CANONICAL_HASH_FN_RE.search(node.name):
                    for child in ast.walk(node):
                        child_lineno = getattr(child, "lineno", node.lineno)
                        if _is_physical_clock_call(child) and child_lineno not in ast12_lines:
                            ast12_lines.add(child_lineno)
                            violations.append(
                                SemanticViolation(
                                    path,
                                    child_lineno,
                                    "AST-012",
                                    "INV_C5_CANONICAL_LOGICAL_TICK: physical clock forbidden in canonical/BFT hash generation; use logical_tick.",
                                )
                            )
                        if _is_float_expr(child) and getattr(child, "lineno", 0) not in ast15_lines:
                            line_no = getattr(child, "lineno", node.lineno)
                            ast15_lines.add(line_no)
                            violations.append(
                                SemanticViolation(
                                    path,
                                    line_no,
                                    "AST-015",
                                    "INV_C5_CANONICAL_HASH_FLOAT_FORBIDDEN: IEEE 754 float forbidden in canonical/BFT hash generation; use fixed-point int or sexagesimal rational.",
                                )
                            )
                if node.name.startswith(("audit_", "verify_")):
                    for child in ast.walk(node):
                        if isinstance(child, ast.ExceptHandler) and _is_broad_or_bare_except_pass(child):
                            if child.lineno not in ast16_lines:
                                ast16_lines.add(child.lineno)
                                violations.append(
                                    SemanticViolation(
                                        path,
                                        child.lineno,
                                        "AST-016",
                                        "INV_C5_FAIL_CLOSED_AUDIT_EXCEPT: silent except-pass forbidden in audit/verify functions; fail closed or record violation.",
                                    )
                                )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sqlite3":
                        has_sqlite = True
                        sqlite_names.add(alias.asname or alias.name)
            if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
                has_sqlite = True
                error_names.update(a.asname or a.name for a in node.names if a.name.endswith("Error"))
            if (
                check_symlink_resolve
                and isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "resolve"
                and isinstance(node.func.value, ast.Call)
                and (
                    (isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "Path")
                    or (isinstance(node.func.value.func, ast.Attribute) and node.func.value.func.attr == "Path")
                )
                and len(node.func.value.args) == 1
                and isinstance(node.func.value.args[0], ast.Name)
                and node.func.value.args[0].id == "__file__"
            ):
                violations.append(
                    SemanticViolation(
                        path,
                        node.lineno,
                        "AST-007",
                        "INV_C5_PATH_SYMLINK_CONFINEMENT: Path(__file__).resolve() forbidden for logical worktree root normalization; use Path(__file__).absolute() for REPO_ROOT and resolve().is_relative_to(REPO_ROOT) for path confinement.",
                    )
                )
            if isinstance(node, ast.Call):
                if _is_text_git_diff(node):
                    violations.append(
                        SemanticViolation(
                            path,
                            node.lineno,
                            "AST-008",
                            "INV_C5_GIT_DIFF_BINARY_SAFE: git diff must operate on bytes (text=False).",
                        )
                    )
                if _is_biometric_gate_with_legacy_message(node):
                    violations.append(
                        SemanticViolation(
                            path,
                            node.lineno,
                            "AST-009",
                            "INV_C5_BIOMETRIC_CLI_ALIGNMENT: c5_biometric_gate legacy --message flag forbidden; use structured parameters (--action, --agent, --scope, --causal-hash).",
                        )
                    )
                if _is_struct_with_d_specifier(node):
                    violations.append(
                        SemanticViolation(
                            path,
                            node.lineno,
                            "AST-010",
                            "INV_C5_CBOR_STRUCT: struct format with 'D' forbidden; use canonical '>Bd' for f64.",
                        )
                    )
                is_hash = False
                if isinstance(node.func, ast.Attribute) and node.func.attr in _HASH_METHODS:
                    is_hash = True
                elif isinstance(node.func, ast.Name) and node.func.id in {"blake3", "sha256"}:
                    is_hash = True
                if is_hash:
                    hash_key_formats = {fmt for arg in node.args for fmt in _classify_key_expr(arg, key_env)}
                    if (
                        _has_incompatible_key_formats(hash_key_formats, hash_key_formats)
                        and node.lineno not in ast13_lines
                    ):
                        ast13_lines.add(node.lineno)
                        violations.append(
                            SemanticViolation(
                                path,
                                node.lineno,
                                "AST-013",
                                "INV_C5_SECURE_ENCLAVE_POINT_NORMALIZATION: raw SEC1 vs SPKI/DER comparison forbidden; normalize to SEC1 point before comparing.",
                            )
                        )
                    for child in ast.walk(node):
                        child_lineno = getattr(child, "lineno", node.lineno)
                        if _is_physical_clock_call(child) and child_lineno not in ast12_lines:
                            ast12_lines.add(child_lineno)
                            violations.append(
                                SemanticViolation(
                                    path,
                                    child_lineno,
                                    "AST-012",
                                    "INV_C5_CANONICAL_LOGICAL_TICK: physical clock forbidden in canonical/BFT hash generation; use logical_tick.",
                                )
                            )
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and PRAGMA_SYNCHRONOUS_FORBIDDEN_RE.search(node.value)
                and not _is_docstring(node, tree)
            ):
                violations.append(
                    SemanticViolation(
                        path,
                        node.lineno,
                        "AST-011",
                        "INV_C5_WAL_SYNCHRONOUS_FULL: PRAGMA synchronous must be FULL (NORMAL/OFF/0/1 forbidden).",
                    )
                )
            if (
                isinstance(node, ast.Compare)
                and node.lineno not in ast13_lines
                and _is_unnormalized_sec1_der_compare(node, key_env)
            ):
                ast13_lines.add(node.lineno)
                violations.append(
                    SemanticViolation(
                        path,
                        node.lineno,
                        "AST-013",
                        "INV_C5_SECURE_ENCLAVE_POINT_NORMALIZATION: raw SEC1 vs SPKI/DER comparison forbidden; normalize to SEC1 point before comparing.",
                    )
                )
        for handler in ast.walk(tree):
            if not isinstance(handler, ast.ExceptHandler):
                continue
            if not _is_io_or_sqlite_handler(handler, error_names, sqlite_names, has_sqlite):
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
    args = parser.parse_args()
    root = args.repo_root
    rules, skills = root / ".agents/rules", root / ".agents/skills"
    gates = root / "scripts/c5_quality_gates"
    for directory in (rules, skills, gates):
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
    guards = root / "scripts/guards"
    kish_engine = root / "01_KISH_ENGINE/babylon60"
    python_roots = [gates, *([guards] if guards.is_dir() else [])]
    gate_python = [
        p
        for d in python_roots
        for p in d.rglob("*.py")
        if "__pycache__" not in p.parts and p.name != Path(__file__).name
    ]
    kish_python = (
        sorted(p for p in kish_engine.rglob("*.py") if "__pycache__" not in p.parts) if kish_engine.is_dir() else []
    )
    python = gate_python + kish_python
    violations = (
        scan_markdown_files(markdown)
        + scan_python_fail_open(gate_python, check_symlink_resolve=True)
        + scan_python_fail_open(kish_python, check_symlink_resolve=False)
    )
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
