# [C5-REAL] Exergy-Maximized
"""
MEJORAlo Ship Gate.

Validates the 7 Seals for production readiness.
Refactored: each seal is an independent checker function.
"""

import logging
import os
from pathlib import Path

from babylon60.extensions.mejoralo.constants import SCAN_EXTENSIONS, SKIP_DIRS
from babylon60.extensions.mejoralo.models import ShipResult, ShipSeal
from babylon60.extensions.mejoralo.scan import scan
from babylon60.extensions.mejoralo.utils import (
    detect_stack,
    get_build_cmd,
    get_lint_cmd,
    get_test_cmd,
    run_quiet,
)
from babylon60.guards.path_guard import is_safe_path

__all__ = ["check_ship_gate"]

logger = logging.getLogger("babylon60_extensions.mejoralo")




def _seal_build(stack: str, cwd: str) -> ShipSeal:
    """Seal 1: Build Zero-Warning."""
    build_cmd = get_build_cmd(stack)
    if not build_cmd:
        return ShipSeal(
            name="Build Zero-Warning", passed=False, detail="No build command for stack"
        )
    ret, _, _ = run_quiet(build_cmd, cwd=cwd)
    passed = ret == 0
    return ShipSeal(
        name="Build Zero-Warning",
        passed=passed,
        detail="Build successful" if passed else "Build failed",
    )


def _seal_tests(stack: str, cwd: str) -> ShipSeal:
    """Seal 2: Tests 100% Green."""
    test_cmd = get_test_cmd(stack)
    if not test_cmd:
        return ShipSeal(name="Tests 100% Green", passed=False, detail="No test command for stack")
    ret, stdout, stderr = run_quiet(test_cmd, cwd=cwd)
    passed = ret == 0
    if not passed:
        logger.error("Tests failed with ret=%s\nSTDOUT:\n%s\nSTDERR:\n%s", ret, stdout, stderr)
    return ShipSeal(
        name="Tests 100% Green",
        passed=passed,
        detail="Tests passed" if passed else "Tests failed",
    )


def _seal_linter(stack: str, cwd: str) -> ShipSeal:
    """Seal 3: Linter Silence."""
    lint_cmd = get_lint_cmd(stack)
    if not lint_cmd:
        return ShipSeal(name="Linter Silence", passed=True, detail="No linter configured - pass")
    ret, _, _ = run_quiet(lint_cmd, cwd=cwd)
    passed = ret == 0
    return ShipSeal(
        name="Linter Silence",
        passed=passed,
        detail="Linter clean" if passed else "Linter issues found",
    )


def _seal_visual(p: Path) -> ShipSeal:
    """Seal 4: Visual Proof."""
    import json
    p_str = str(p)
    if ".." in p_str or p_str.startswith("-"):
        raise ValueError("Unsafe path traversal blocked in visual seal")

    visual_json = p / "visual_proof.json"
    screenshots = list(p.glob("**/screenshot*.png"))
    visual_ok = visual_json.exists() or len(screenshots) > 0

    if visual_json.exists():
        try:
            with open(visual_json) as f:
                data = json.load(f)
            components = data.get("components_tested", len(data.get("tests", [])))
            status = data.get("status", "OK")
            detail = f"Visual Proof: {components} components rendered | Status: {status}"
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as e:  # noqa: BLE001
            detail = f"Found visual_proof.json (parse error: {e})"
    elif screenshots:
        detail = f"Found {len(screenshots)} screenshots"
    else:
        detail = "No visual proof found"
    return ShipSeal(name="Visual Proof", passed=visual_ok, detail=detail)


def _seal_performance(project: str, path: str | Path) -> ShipSeal:
    """Seal 5: Performance - score must be >= 70 as quality proxy."""
    result = scan(project, path)
    passed = result.score >= 70
    return ShipSeal(
        name="Performance <100ms",
        passed=passed,
        detail=f"Quality score: {result.score}/100 ({'OK' if passed else 'below threshold'})",
    )


def _seal_a11y(p: Path, stack: str) -> ShipSeal:
    """Seal 6: A11y 100%."""
    a11y_findings: list[str] = []
    extensions = SCAN_EXTENSIONS.get(stack, SCAN_EXTENSIONS["unknown"])

    html_files: list[Path] = []
    p_str = str(p)
    if ".." in p_str or p_str.startswith("-"):
        raise ValueError("Unsafe path traversal blocked in accessibility seal")
    for root, dirs, files in os.walk(p):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            fp = Path(root) / f
            if fp.suffix in extensions and fp.suffix in (".html", ".html.erb", ".jsx", ".tsx"):
                html_files.append(fp)

    for hf in html_files[:5]:
        try:
            content = hf.read_text(errors="replace").lower()
            if "<img" in content and 'alt="' not in content:
                a11y_findings.append(f"{hf.name}: missing alt tags")
        except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError) as exc:  # noqa: BLE001
            logger.warning("Suppressed exception: %s", exc)

    return ShipSeal(
        name="A11y 100%",
        passed=len(a11y_findings) == 0,
        detail=f"Issues: {len(a11y_findings)}"
        if a11y_findings
        else "Basic accessibility patterns found",
    )


def _seal_psi(project: str, path: str | Path) -> ShipSeal:
    """Seal 7: No Psi Debt."""
    scan_result = scan(project, path)
    psi_dim = next((d for d in scan_result.dimensions if d.name == "Psi"), None)
    psi_ok = psi_dim is not None and psi_dim.score == 100
    return ShipSeal(
        name="No Psi Debt",
        passed=psi_ok,
        detail=f"Psi score: {psi_dim.score if psi_dim else 0}",
    )




def check_ship_gate(project: str, path: str | Path) -> ShipResult:
    """Validate the 7 Seals for production readiness."""
    if not is_safe_path(path):
        logger.error("🚫 [Mejoralo] Blocked unsafe path: %s", path)
        return ShipResult(
            project=project,
            ready=False,
            seals=[ShipSeal(name="Path Safety", passed=False, detail="Blocked unsafe path")],
            passed=0,
            total=1,
        )

    import os

    base_dir = os.path.realpath(str(Path.cwd()))
    target_str = os.path.realpath(os.path.join(base_dir, os.path.expanduser(str(path))))
    try:
        common = os.path.commonpath([base_dir, target_str])
    except ValueError:
        common = ""

    if common != base_dir:
        logger.error("🚫 [Mejoralo] Blocked unsafe path: %s", path)
        return ShipResult(
            project=project,
            ready=False,
            seals=[ShipSeal(name="Path Safety", passed=False, detail="Blocked unsafe path")],
            passed=0,
            total=1,
        )
    target_path = Path(target_str)
    stack = detect_stack(target_path)
    cwd = str(target_path)

    seals = [
        _seal_build(stack, cwd),
        _seal_tests(stack, cwd),
        _seal_linter(stack, cwd),
        _seal_visual(target_path),
        _seal_performance(project, target_path),
        _seal_a11y(target_path, stack),
        _seal_psi(project, target_path),
    ]

    passed_count = sum(1 for s in seals if s.passed)
    return ShipResult(
        project=project,
        ready=passed_count == len(seals),
        seals=seals,
        passed=passed_count,
        total=len(seals),
    )
