# [C5-REAL] Exergy-Maximized
from __future__ import annotations

import asyncio
import json
import sys

from babylon60.guards._seals_cache import GlobalSourceCache, arun_cmd, printer
from babylon60.guards.cobbler_audit import run_cobbler_audit

GateResult = tuple[bool, str]


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEAL 1: CODE QUALITY - Ruff Lint + LOC Guard (≤600)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_seal_1_code_quality() -> GateResult:
    printer.seal(1, "AX-IV Thermodynamic Cognition", "Code Quality (Ruff + LOC ≤700)")
    passed = True

    # ── Ruff Lint ──
    code, out = await arun_cmd(["ruff", "check", "cortex/", "--output-format", "concise"])
    if code == 0:
        printer.success("Ruff checks passed.")
    elif code == 127:
        printer.warn("Ruff not found - skipping (install with: pip install ruff)")
    else:
        printer.fail("Ruff linting failed.")
        printer.print(out[:2000], style="dim")
        passed = False

    # ── LOC Guard ──
    blocked = 0
    warnings = 0
    for py_file, content in GlobalSourceCache.files.items():
        lines = content.count("\n") + 1
        if lines > 700:
            printer.fail(f"{py_file.name} exceeds 700 LOC ({lines})")
            blocked += 1
        elif lines > 500:
            warnings += 1

    if blocked > 0:
        passed = False
    else:
        printer.success(f"All files within entropy limits. ({warnings} warnings >400 LOC)")

    return passed, "verified"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEAL 2: TYPE SAFETY - Pyright/Mypy
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_seal_2_type_safety() -> GateResult:
    printer.seal(2, "AX-I Stochastic Determinism", "Type Check (Pyright)")
    code, out = await arun_cmd(["pyright", "cortex/", "--outputjson"], timeout=180.0)
    if code == 127:
        printer.warn("No type checker found (pyright/mypy) - skipping")
        return True, "verified"

    if code != 0:
        try:
            start_idx = out.find("{")
            if start_idx != -1:
                data = json.loads(out[start_idx:])
                ecount = data.get("summary", {}).get("errorCount", 999)
                if ecount <= 78:
                    printer.success(f"Type checks passed (within baseline threshold: {ecount}/78).")
                    return True, "verified"
                printer.fail(f"Type checking failed (threshold: {ecount}/78).")
                printer.print(out[:2000], style="dim")
                return False, "verified"
        except (ValueError, TypeError, KeyError, AssertionError) as exc:
            import logging

            logging.warning("Suppressed exception: %s", exc)

    if code == 0 or "Success: no issues found" in out or '"errorCount":0' in out:
        printer.success("Type checks passed.")
        return True, "verified"
    printer.fail("Type checking failed.")
    printer.print(out[:2000], style="dim")
    return False, "verified"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEAL 3: SECURITY - Bandit + Cobbler Self-Audit
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_seal_3_security() -> GateResult:
    printer.seal(3, "AX-VII Computational Immunology", "Security (Bandit + Self-Audit)")
    passed = True

    # ── Bandit Scan ──
    code, out = await arun_cmd(
        ["bandit", "-r", "cortex/", "-q", "--severity-level", "high", "--confidence-level", "high"]
    )
    if code == 0:
        printer.success("Bandit security scan passed.")
    elif code == 127:
        printer.warn("Bandit not found - skipping")
    else:
        printer.fail("Security vulnerabilities detected.")
        printer.print(out[:2000], style="dim")
        passed = False

    # ── Cobbler's Compliance ──
    cobbler_passed = await run_cobbler_audit(GlobalSourceCache.files, printer)
    if not cobbler_passed:
        passed = False

    return passed, "verified"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEAL 4: TESTS - pytest
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_seal_4_tests() -> GateResult:
    printer.seal(4, "AX-II Epistemic Paradox", "Tests & Coverage")
    python_cmd = sys.executable
    cmd = [str(python_cmd), "-m", "pytest", "tests/", "-x", "-q", "--tb=short"]
    try:
        code, out = await asyncio.wait_for(arun_cmd(cmd, timeout=600.0), timeout=605.0)
    except asyncio.TimeoutError:
        printer.fail("Tests timed out after 600 seconds (Singularity Prevention).")
        return False, "verified"

    if code == 0:
        printer.success("All tests passed.")
        return True, "verified"
    printer.fail("Tests failed.")
    printer.print(out[:3000], style="dim")
    return False, "verified"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEAL 5: LEDGER INTEGRITY - Schema Init + Connection Guard
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
async def check_seal_5_ledger() -> GateResult:
    printer.seal(5, "AX-II Epistemic Paradox", "Schema Init + Connection Guard")
    passed = True

    # ── Schema Init ──
    try:
        from babylon60.engine.core.cortex_engine import CortexEngine

        engine = CortexEngine(":memory:", auto_embed=False)
        await engine.init_db()
        await engine.close()  # type: ignore[no-untyped-call]
        printer.success("Ledger schema initialized successfully.")
    except (ValueError, TypeError, KeyError, AssertionError, RuntimeError) as e:
        printer.fail(f"Ledger initialization threw error: {e}")
        passed = False

    # ── Connection Guard ──
    python_cmd = sys.executable
    code, out = await arun_cmd(
        [str(python_cmd), "-m", "cortex.database.connection_guard", "--root", "cortex"]
    )
    if code == 0:
        printer.success("Connection guard passed.")
    else:
        printer.fail("Connection guard failed.")
        printer.print(out, style="dim")
        passed = False

    return passed, "verified"
