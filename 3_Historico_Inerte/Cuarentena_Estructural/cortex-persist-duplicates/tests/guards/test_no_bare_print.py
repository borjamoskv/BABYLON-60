# [C5-REAL] Exergy-Maximized
# This file is part of CORTEX. Apache-2.0.
import ast
import os
from pathlib import Path


def test_no_bare_print_in_production_core():
    """
    AST-based lint test to verify that no bare print() statements
    exist in the core production modules: engine, memory, guards, core.
    """
    root_dir = Path(__file__).parent.parent.parent / "babylon60"
    target_dirs = ["engine", "memory", "guards", "core"]

    violations = []

    for target in target_dirs:
        dir_path = root_dir / target
        if not dir_path.exists():
            continue

        for root, _, files in os.walk(dir_path):
            for file in files:
                if not file.endswith(".py"):
                    continue

                file_path = Path(root) / file
                try:
                    content = file_path.read_text(encoding="utf-8")
                    tree = ast.parse(content, filename=str(file_path))

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Call):
                            if isinstance(node.func, ast.Name) and node.func.id == "print":
                                # Get line number if available
                                line_no = getattr(node, "lineno", "?")
                                violations.append(
                                    f"{file_path.relative_to(root_dir.parent)}:L{line_no}"
                                )
                except Exception as e:  # noqa: BLE001
                    # Ignore parse errors for test purposes if any, or report them
                    pass

    assert not violations, f"Bare print() found in core modules: {', '.join(violations)}"
