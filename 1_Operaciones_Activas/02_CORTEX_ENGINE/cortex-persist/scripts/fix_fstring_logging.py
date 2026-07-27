# [C5-REAL] Exergy-Maximized
"""
cat_id: fix-fstring-logging
cat_type: script
version: 1.0.0
reality_level: C5-REAL
owner: borjamoskv
exergy_tier: P2
"""


import logging


from __future__ import annotations

import ast
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

LOGGING_METHODS = {"debug", "info", "warning", "error", "critical", "exception", "log"}

# Format spec → printf mapping
FORMAT_SPEC_MAP = {
    "d": "%d",
    "f": "%f",
    "s": "%s",
    "r": "%r",
    "x": "%x",
    "X": "%X",
    "o": "%o",
    "e": "%e",
    "E": "%E",
    "g": "%g",
    "G": "%G",
}


@dataclass
class FixResult:
    file: str
    line: int
    original: str
    replacement: str
    status: str  # "fixed" | "skipped"
    reason: str = ""


@dataclass
class Stats:
    fixed: int = 0
    skipped: int = 0
    files_modified: int = 0
    results: list[FixResult] = field(default_factory=list)


def is_logging_call(node: ast.Call) -> bool:
    """Check if a Call node is a logging method call."""
    if not isinstance(node.func, ast.Attribute):
        return False
    if node.func.attr not in LOGGING_METHODS:
        return False
    # logger.info(...) or logging.info(...) or self.logger.info(...)
    # We accept any attribute access ending in a logging method name
    return True


def format_spec_to_printf(spec: str) -> str | None:
    """Convert Python format spec to printf-style format string.

    Examples:
        ""      → "%s"
        ".2f"   → "%.2f"
        ".4f"   → "%.4f"
        "d"     → "%d"
        ">10s"  → None (alignment — too complex)
        "08x"   → "%08x"
    """
    if not spec:
        return "%s"

    # Simple type-only specs: "d", "f", "s", "r", "x", etc.
    if spec in FORMAT_SPEC_MAP:
        return FORMAT_SPEC_MAP[spec]

    # Precision + type: ".2f", ".4f", ".2e", etc.
    m = re.match(r"^(\.\d+)([fFeEgG])$", spec)
    if m:
        return f"%{m.group(1)}{m.group(2)}"

    # Width + type: "08x", "10d", etc.
    m = re.match(r"^(\d+)([dxXosfFeEgG])$", spec)
    if m:
        return f"%{m.group(1)}{m.group(2)}"

    # Zero-padded width + type: "08x"
    m = re.match(r"^(0\d+)([dxXo])$", spec)
    if m:
        return f"%{m.group(1)}{m.group(2)}"

    # Width.precision + type: "10.2f"
    m = re.match(r"^(\d+\.\d+)([fFeEgG])$", spec)
    if m:
        return f"%{m.group(1)}{m.group(2)}"

    return None


def is_simple_expr(node: ast.expr) -> bool:
    """Check if an expression is simple enough to extract as a logging argument."""
    if isinstance(node, ast.Name):
        return True
    if isinstance(node, ast.Attribute):
        return is_simple_expr(node.value)
    if isinstance(node, ast.Subscript):
        # Allow simple subscripts: var[0], var[:16], var["key"]
        if not is_simple_expr(node.value):
            return False
        sl = node.slice
        if isinstance(sl, ast.Constant):
            return True
        if isinstance(sl, ast.Slice):
            return all(
                s is None or isinstance(s, (ast.Constant, ast.Name, ast.UnaryOp))
                for s in (sl.lower, sl.upper, sl.step)
            )
        if isinstance(sl, ast.Name):
            return True
        return False
    if isinstance(node, ast.Call):
        # Allow simple function calls like len(x), str(x), type(x).__name__
        # But mark as "semi-complex" — we still allow them
        if isinstance(node.func, ast.Name) and node.func.id in (
            "len",
            "str",
            "repr",
            "type",
            "int",
            "float",
            "hex",
            "id",
            "bool",
        ):
            return all(is_simple_expr(a) for a in node.args) and not node.keywords
        # method calls like x.method() — allow if receiver is simple and no complex args
        if isinstance(node.func, ast.Attribute) and is_simple_expr(node.func.value):
            return all(is_simple_expr(a) for a in node.args) and not node.keywords
        return False
    if isinstance(node, ast.UnaryOp):
        return is_simple_expr(node.operand)
    if isinstance(node, ast.BinOp):
        return is_simple_expr(node.left) and is_simple_expr(node.right)
    if isinstance(node, ast.Constant):
        return True
    if isinstance(node, ast.Starred):
        return False
    return False


def unparse_expr(node: ast.expr) -> str:
    """Unparse an AST expression node back to source code."""
    return ast.unparse(node)


def convert_fstring(node: ast.JoinedStr) -> tuple[str, list[str]] | None:
    """Convert an f-string AST node to (format_string, [args]).

    Returns None if conversion is not possible (too complex).
    """
    format_parts: list[str] = []
    args: list[str] = []

    for value in node.values:
        if isinstance(value, ast.Constant) and isinstance(value.value, str):
            # Literal string part — escape any existing %
            format_parts.append(value.value.replace("%", "%%"))
        elif isinstance(value, ast.FormattedValue):
            expr = value.value
            conversion = value.conversion  # -1=none, 115=!s, 114=!r, 97=!a
            fmt_spec = value.format_spec

            # Check expression complexity
            if not is_simple_expr(expr):
                return None

            # Handle format spec
            if fmt_spec is not None:
                # format_spec is itself a JoinedStr in the AST
                if isinstance(fmt_spec, ast.JoinedStr):
                    # Dynamic format specs like {x:{width}f} — skip
                    if any(isinstance(v, ast.FormattedValue) for v in fmt_spec.values):
                        return None
                    # Static format spec embedded in JoinedStr
                    spec_str = ""
                    for v in fmt_spec.values:
                        if isinstance(v, ast.Constant):
                            spec_str += str(v.value)
                        else:
                            return None
                elif isinstance(fmt_spec, ast.Constant):
                    spec_str = str(fmt_spec.value)
                else:
                    return None

                printf_fmt = format_spec_to_printf(spec_str)
                if printf_fmt is None:
                    return None
                format_parts.append(printf_fmt)
            elif conversion == 114:  # !r
                format_parts.append("%r")
            elif conversion == 115:  # !s
                format_parts.append("%s")
            elif conversion == 97:  # !a
                # ascii() — no direct printf equivalent, wrap
                format_parts.append("%s")
                args.append(f"ascii({unparse_expr(expr)})")
                continue
            else:
                format_parts.append("%s")

            args.append(unparse_expr(expr))
        else:
            return None

    return "".join(format_parts), args


def find_fstring_logging_calls(tree: ast.Module) -> list[ast.Call]:
    """Find all logging calls with f-string first arguments."""
    results = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not is_logging_call(node):
            continue
        if not node.args:
            continue

        first_arg = node.args[0]
        # For logger.log(level, f"..."), the f-string is the second arg
        if (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "log"
            and len(node.args) >= 2
            and isinstance(node.args[1], ast.JoinedStr)
        ):
            results.append(node)
        elif isinstance(first_arg, ast.JoinedStr):
            results.append(node)
    return results


def _byte_col_to_str_col(line: str, byte_col: int) -> int:
    """Convert a UTF-8 byte offset to a string (code point) offset.

    Python 3.12+ AST col_offset/end_col_offset are UTF-8 byte offsets.
    We need string indices for slicing.
    """
    encoded = line.encode("utf-8")
    # Clamp to valid range
    byte_col = min(byte_col, len(encoded))
    prefix = encoded[:byte_col]
    return len(prefix.decode("utf-8", errors="replace"))


def fix_file(filepath: str, stats: Stats, dry_run: bool = False) -> bool:
    """Fix f-string logging calls in a single file. Returns True if modified."""
    try:
        source = Path(filepath).read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError):
        return False

    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return False

    calls = find_fstring_logging_calls(tree)
    if not calls:
        return False

    # Sort by line number descending so we can replace from bottom to top
    # without invalidating line numbers
    lines = source.splitlines(keepends=True)
    # (start_line, end_line, start_str_col, end_str_col, orig, new_source)
    replacements: list[tuple[int, int, int, int, str, str]] = []

    for call in calls:
        # Determine which arg is the f-string
        if (
            isinstance(call.func, ast.Attribute)
            and call.func.attr == "log"
            and len(call.args) >= 2
            and isinstance(call.args[1], ast.JoinedStr)
        ):
            fstring_idx = 1
            fstring_node = call.args[1]
        else:
            fstring_idx = 0
            fstring_node = call.args[0]

        line_no = fstring_node.lineno
        result_conversion = convert_fstring(fstring_node)

        if result_conversion is None:
            # Get the source line for reporting
            src_line = lines[line_no - 1].strip() if line_no <= len(lines) else "<unknown>"
            stats.skipped += 1
            stats.results.append(
                FixResult(
                    file=filepath,
                    line=line_no,
                    original=src_line,
                    replacement="",
                    status="skipped",
                    reason="Complex f-string expression",
                )
            )
            continue

        fmt_str, fmt_args = result_conversion

        # Check if there are already extra args beyond the f-string
        # (some logging calls have extra args already — don't break them)
        existing_extra_args = call.args[fstring_idx + 1 :]
        existing_kwargs = call.keywords

        # Build the replacement for the entire call
        # Strategy: use ast.unparse on a modified AST node
        new_args: list[ast.expr] = list(call.args[:fstring_idx])

        # The format string
        new_args.append(ast.Constant(value=fmt_str))

        # The extracted arguments
        for arg_str in fmt_args:
            try:
                arg_node = ast.parse(arg_str, mode="eval").body
            except SyntaxError:
                stats.skipped += 1
                src_line = lines[line_no - 1].strip() if line_no <= len(lines) else "<unknown>"
                stats.results.append(
                    FixResult(
                        file=filepath,
                        line=line_no,
                        original=src_line,
                        replacement="",
                        status="skipped",
                        reason=f"Cannot parse extracted arg: {arg_str}",
                    )
                )
                break
            new_args.append(arg_node)
        else:
            # Add back any existing extra args
            new_args.extend(existing_extra_args)

            # Create modified call node
            new_call = ast.Call(
                func=call.func,
                args=new_args,
                keywords=existing_kwargs,
            )
            new_source = ast.unparse(new_call)

            # Get original source span — convert byte offsets to string offsets
            start_line = call.lineno
            end_line = call.end_lineno or call.lineno
            byte_start_col = call.col_offset
            byte_end_col = call.end_col_offset or len(lines[end_line - 1].encode("utf-8"))

            start_str_col = _byte_col_to_str_col(lines[start_line - 1], byte_start_col)
            end_str_col = _byte_col_to_str_col(lines[end_line - 1], byte_end_col)

            # Extract original source
            if start_line == end_line:
                orig = lines[start_line - 1][start_str_col:end_str_col]
            else:
                orig_parts = [lines[start_line - 1][start_str_col:]]
                for i in range(start_line, end_line - 1):
                    orig_parts.append(lines[i])
                orig_parts.append(lines[end_line - 1][:end_str_col])
                orig = "".join(orig_parts)

            replacements.append(
                (start_line, end_line, start_str_col, end_str_col, orig.strip(), new_source)
            )
            stats.fixed += 1
            stats.results.append(
                FixResult(
                    file=filepath,
                    line=line_no,
                    original=orig.strip(),
                    replacement=new_source,
                    status="fixed",
                )
            )

    if not replacements or dry_run:
        return False

    # Apply replacements from bottom to top
    replacements.sort(key=lambda r: (r[0], r[2]), reverse=True)
    for start_line, end_line, start_col, end_col, _orig, new_source in replacements:
        if start_line == end_line:
            line = lines[start_line - 1]
            lines[start_line - 1] = line[:start_col] + new_source + line[end_col:]
        else:
            # Multi-line: replace first line from col_offset, delete middle, truncate last
            first_line = lines[start_line - 1]
            last_line = lines[end_line - 1]
            lines[start_line - 1] = first_line[:start_col] + new_source + last_line[end_col:]
            # Remove the intermediate and last lines
            del lines[start_line:end_line]

    new_source_text = "".join(lines)
    # Verify the result parses
    try:
        ast.parse(new_source_text, filename=filepath)
    except SyntaxError as e:
        logging.getLogger(__name__).info(
            f"  ⚠ ABORT {filepath}: result would not parse (line {e.lineno}). No changes written."
        )
        return False

    Path(filepath).write_text(new_source_text, encoding="utf-8")
    stats.files_modified += 1
    return True


def scan_directory(directory: str, stats: Stats, dry_run: bool = False) -> None:
    """Recursively scan a directory for Python files and fix them."""
    for root, _dirs, files in os.walk(directory):
        # Skip __pycache__, .git, node_modules, etc.
        if any(skip in root for skip in ("__pycache__", ".git", "node_modules", ".venv", "venv")):
            continue
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            filepath = os.path.join(root, fname)
            fix_file(filepath, stats, dry_run=dry_run)


def main() -> None:
    if len(sys.argv) < 2:
        logging.getLogger(__name__).info("Usage: python fix_fstring_logging.py <directory_or_file> [--dry-run]")
        sys.exit(1)

    target = sys.argv[1]
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        logging.getLogger(__name__).info("=== DRY RUN MODE (no files will be modified) ===\n")

    stats = Stats()

    if os.path.isfile(target):
        fix_file(target, stats, dry_run=dry_run)
    elif os.path.isdir(target):
        scan_directory(target, stats, dry_run=dry_run)
    else:
        logging.getLogger(__name__).info(f"Error: {target} is not a valid file or directory")
        sys.exit(1)

    # Report
    logging.getLogger(__name__).info("=" * 72)
    logging.getLogger(__name__).info(f"  F-STRING LOGGING CODEMOD — {'DRY RUN' if dry_run else 'EXECUTED'}")
    logging.getLogger(__name__).info("=" * 72)
    logging.getLogger(__name__).info(f"  Fixed:          {stats.fixed}")
    logging.getLogger(__name__).info(f"  Skipped:        {stats.skipped}")
    logging.getLogger(__name__).info(f"  Files modified: {stats.files_modified}")
    logging.getLogger(__name__).info("=" * 72)

    if stats.results:
        logging.getLogger(__name__).info("\n--- FIXED ---")
        for r in stats.results:
            if r.status == "fixed":
                logging.getLogger(__name__).info(f"  {r.file}:{r.line}")
                logging.getLogger(__name__).info(f"    - {r.original[:120]}")
                logging.getLogger(__name__).info(f"    + {r.replacement[:120]}")

        skipped = [r for r in stats.results if r.status == "skipped"]
        if skipped:
            logging.getLogger(__name__).info("\n--- SKIPPED (manual review needed) ---")
            for r in skipped:
                logging.getLogger(__name__).info(f"  {r.file}:{r.line} — {r.reason}")
                logging.getLogger(__name__).info(f"    {r.original[:120]}")

    logging.getLogger(__name__).info()


if __name__ == "__main__":
    main()
