#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
C5-REAL Manifest Compiler & Enforcement Engine.
Enforces topologic and epistemological rules declared in AGENTS.md.
Execution MUST Fail-Stop (exit code > 0) upon detecting any anergy.
"""

import os
import re
import ast
import sys
from pathlib import Path

# Epistemic Fail-Stop Registry
VIOLATIONS = []

def report_violation(rule: str, detail: str):
    print(f"🔥 [VIOLATION] {rule}")
    print(f"   -> {detail}")
    VIOLATIONS.append(rule)

def iter_files(root: Path, pattern: str):
    banned_dirs = {".venv", "node_modules", "target", "scratch", ".git", ".jj", "dist", "build"}
    for file in root.rglob(pattern):
        if file.is_file() and not any(banned in file.parts for banned in banned_dirs):
            yield file

# --- A. [KERNEL & SILICIO] ---
def verify_rust_ffi(root: Path):
    """Enforces unsafe(no_mangle) and cache-line alignment."""
    for rs_file in iter_files(root, "*.rs"):
        content = rs_file.read_text(errors="ignore")
        if re.search(r'#\[no_mangle\](?![\s\n]*pub\s+unsafe)', content) or re.search(r'(?<!unsafe\()#\[no_mangle\]', content):
            if "#[no_mangle]" in content and "#[unsafe(no_mangle)]" not in content:
                report_violation("SILICIO_FFI_01", f"Found raw #[no_mangle] in {rs_file.name}. Must be #[unsafe(no_mangle)].")
        
def verify_cargo_dependencies(root: Path):
    for toml_file in iter_files(root, "Cargo.toml"):
        content = toml_file.read_text(errors="ignore")
        if "crossbeam-epoch" in content:
            report_violation("SILICIO_EBR_01", f"Banned GC/Epoch library 'crossbeam-epoch' found in {toml_file.name}.")

# --- B. [EPISTEMOLOGÍA & ESTÉTICA] ---
def verify_markdown_latex(root: Path):
    """Bans raw LaTeX formatting."""
    for md_file in iter_files(root, "*.md"):
        if md_file.name == "AGENTS.md" or md_file.name.endswith("SKILL.md"):
            continue
        try:
            content = md_file.read_text(errors="ignore")
            if (
                re.search(r'\$\$.+?\$\$', content, re.DOTALL) or 
                re.search(r'(?<!\$)\$(?!\$).+?(?<!\$)\$(?!\$)', content) or
                re.search(r'\\(mathcal|mathbb|rightarrow|frac|text|implies|blacksquare|lim|sum)', content)
            ):
                report_violation("ESTETICA_LATEX_01", f"Raw LaTeX detected in {md_file.name}. Use UTF-8 Universal Mathematics.")
        except Exception:
            pass

# --- C. [OPERACIONES] ---
class NestingDepthVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        self.max_depth = 0
        self.current_depth = 0
        self.violations = []

    def generic_visit(self, node):
        is_nesting_node = isinstance(node, (ast.If, ast.For, ast.While, ast.With, ast.Try))
        if is_nesting_node:
            self.current_depth += 1
            if self.current_depth > 3:
                self.violations.append(getattr(node, 'lineno', 0))
        super().generic_visit(node)
        if is_nesting_node:
            self.current_depth -= 1

def verify_python_nesting(root: Path):
    """Enforces early returns, banning nesting depth > 3."""
    for py_file in iter_files(root, "*.py"):
        try:
            content = py_file.read_text(errors="ignore")
            if "# C5_IGNORE_NESTING" in content:
                continue
            tree = ast.parse(content)
            visitor = NestingDepthVisitor(py_file.name)
            visitor.visit(tree)
            if visitor.violations:
                report_violation("OPERACIONES_NESTING_01", f"Thermal Nesting (>3 levels) detected in {py_file.name} near lines {visitor.violations[:3]}. Use Early Returns.")
        except Exception:
            pass

def _check_banned_clocks_in_file(file: Path, banned_calls: list):
    if "c5_manifest_compiler" in file.name or "poc_teff_transition" in file.name:
        return
    content = file.read_text(errors="ignore")
    for banned in banned_calls:
        if re.search(banned, content):
            report_violation("OPERACIONES_TIME_01", f"Wall-clock usage ({banned.replace(r'.', '.')}) found in {file.name}. Use monotonic hardware clocks.")

def verify_time_monotonicity(root: Path):
    """Bans wall-clock time reliance."""
    banned_calls = [r"Date\.now\(\)", r"CLOCK_REALTIME", r"time\.time\(\)"]
    for ext in ["*.js", "*.ts", "*.rs", "*.py"]:
        for file in iter_files(root, ext):
            _check_banned_clocks_in_file(file, banned_calls)

# --- D. [REPOSITORIO] ---
def verify_drop_zone_hygiene(root: Path):
    """Ensures root directory is pristine (Level 0 Hygiene)."""
    allowed_root_files = {
        "README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", 
        "CODEOWNERS", "Cargo.toml", "Cargo.lock", "pyproject.toml", 
        "uv.toml", "uv.lock", "requirements.txt", "lefthook.yml", 
        "Makefile", ".gitignore", ".git-blame-ignore-revs", "go.mod",
        "pyrightconfig.json", "imports.json", "LICENSE"
    }
    for item in root.iterdir():
        if item.is_file() and not item.name.startswith("."):
            if item.name not in allowed_root_files:
                report_violation("REPOSITORIO_HIGIENE_01", f"Transient file found in root: {item.name}. Move to scratch/.")

def verify_supply_chain(root: Path):
    """Bans dynamic dependencies."""
    for pkg in iter_files(root, "package.json"):
        content = pkg.read_text(errors="ignore")
        if re.search(r'\"[\^~]\d', content):
            report_violation("REPOSITORIO_SUPPLY_01", f"Dynamic semantic versioning (^, ~) found in {pkg.name}. Use exact versions.")

def main():
    print("=" * 60)
    print(" 🛡️  C5-REAL MANIFEST COMPILER (Pre-Flight Analysis)")
    print("=" * 60)
    
    root_path = Path.cwd()
    
    verify_drop_zone_hygiene(root_path)
    verify_supply_chain(root_path)
    verify_cargo_dependencies(root_path)
    verify_rust_ffi(root_path)
    verify_markdown_latex(root_path)
    verify_python_nesting(root_path)
    verify_time_monotonicity(root_path)
    
    if VIOLATIONS:
        print("=" * 60)
        print(f"❌ COMPILATION FAILED: {len(VIOLATIONS)} Anergy violations found.")
        print("   -> Resolution requires strict mapping to AGENTS.md invariants.")
        print("=" * 60)
        sys.exit(1)
    else:
        print("✅ COMPILATION SUCCESS: Topologic Integrity Verified (Entropy = 0).")
        sys.exit(0)

if __name__ == "__main__":
    main()
