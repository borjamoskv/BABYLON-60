#!/usr/bin/env python3
"""
auto_heal_hardcoded_paths.py - Sovereign AST-based Auto-Remediation Engine for hardcoded paths.
Uses Python AST NodeTransformer to safely transform hardcoded absolute user home paths
into dynamic Path.home() expressions without syntax corruption or regex side-effects.
"""

import ast
import os
import re
from pathlib import Path

WORKSPACE_DIR = Path(__file__).resolve().parent.parent.parent


class HardcodedPathRemediator(ast.NodeTransformer):
    """AST Transformer that converts string literals containing user home paths to Path.home() calls."""

    def __init__(self) -> None:
        self.modified = False
        self.needs_pathlib = False

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        # Preserve docstrings in functions
        self.generic_visit(node)
        return node

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.AST:
        # Preserve docstrings in classes
        self.generic_visit(node)
        return node

    def visit_Module(self, node: ast.Module) -> ast.AST:
        # Preserve module-level docstring if present
        if (node.body and isinstance(node.body[0], ast.Expr) and 
                isinstance(node.body[0].value, ast.Constant) and 
                isinstance(node.body[0].value.value, str)):
            for child in node.body[1:]:
                self.visit(child)
            return node
        self.generic_visit(node)
        return node

    def visit_Constant(self, node: ast.Constant) -> ast.AST:
        if isinstance(node.value, str):
            val = node.value
            # Match absolute user home path: <home_prefix>/<user>/...
            match = re.match(r"^/(" + "Users|home" + r")/[^/]+(?:/(.*))?$", val)
            if match:
                rel_path = match.group(2) or ""
                self.modified = True
                self.needs_pathlib = True
                
                # Build AST: str(Path.home() / "rel_path") or str(Path.home())
                if rel_path:
                    new_node = ast.Call(
                        func=ast.Name(id="str", ctx=ast.Load()),
                        args=[
                            ast.BinOp(
                                left=ast.Call(
                                    func=ast.Attribute(
                                        value=ast.Name(id="Path", ctx=ast.Load()),
                                        attr="home",
                                        ctx=ast.Load()
                                    ),
                                    args=[],
                                    keywords=[]
                                ),
                                op=ast.Div(),
                                right=ast.Constant(value=rel_path)
                            )
                        ],
                        keywords=[]
                    )
                else:
                    new_node = ast.Call(
                        func=ast.Name(id="str", ctx=ast.Load()),
                        args=[
                            ast.Call(
                                func=ast.Attribute(
                                    value=ast.Name(id="Path", ctx=ast.Load()),
                                    attr="home",
                                    ctx=ast.Load()
                                ),
                                args=[],
                                keywords=[]
                            )
                        ],
                        keywords=[]
                    )
                return ast.copy_location(new_node, node)
        return node


def ensure_pathlib_import(tree: ast.Module) -> None:
    """Inserts 'from pathlib import Path' if not present in module body."""
    has_pathlib = False
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == "pathlib":
            if any(alias.name == "Path" for alias in node.names):
                has_pathlib = True
                break
        elif isinstance(node, ast.Import):
            if any(alias.name == "pathlib" for alias in node.names):
                has_pathlib = True
                break

    if not has_pathlib:
        import_node = ast.ImportFrom(
            module="pathlib",
            names=[ast.alias(name="Path", asname=None)],
            level=0
        )
        idx = 0
        # Insert after shebang/module docstring if present
        if (tree.body and isinstance(tree.body[0], ast.Expr) and 
                isinstance(tree.body[0].value, ast.Constant)):
            idx = 1
        tree.body.insert(idx, import_node)
        ast.fix_missing_locations(tree)


def heal_file(filepath: Path) -> bool:
    try:
        content = filepath.read_text(encoding="utf-8")
        tree = ast.parse(content, filename=str(filepath))
    except Exception:
        return False

    transformer = HardcodedPathRemediator()
    new_tree = transformer.visit(tree)

    if transformer.modified:
        ast.fix_missing_locations(new_tree)
        if transformer.needs_pathlib:
            ensure_pathlib_import(new_tree)
        
        remediated_code = ast.unparse(new_tree)
        # Preserve shebang if original had one
        lines = content.splitlines()
        if lines and lines[0].startswith("#!"):
            remediated_code = f"{lines[0]}\n" + remediated_code

        filepath.write_text(remediated_code + "\n", encoding="utf-8")
        return True
    return False


def main() -> None:
    print("[*] Initiating AST Sovereign Auto-Heal Engine for Hardcoded Paths...")
    target_dir = WORKSPACE_DIR / "scripts"
    if not target_dir.exists():
        target_dir = WORKSPACE_DIR

    healed_count = 0
    for root, _, files in os.walk(target_dir):
        if ".git" in root or "__pycache__" in root or "node_modules" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                filepath = Path(root) / f
                if heal_file(filepath):
                    rel = filepath.relative_to(WORKSPACE_DIR)
                    print(f"  [⚡ AST HEALED] Remediated: {rel}")
                    healed_count += 1

    print(f"[*] AST Auto-Heal Complete. {healed_count} files remediated.")


if __name__ == "__main__":
    main()
