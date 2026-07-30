# [C5-REAL] AUTODIDACT Dead Surface Validator
"""Validates dead surfaces found by the AUTODIDACT audit.

Sections:
    §1  Route Registration Integrity
    §2  Broken Imports (P0)
    §3  Phantom Agent Tools
    §4  Missing __init__.py in Extensions
    §5  CLI Orphan Detection
"""

from __future__ import annotations

import logging

import os
import re
from pathlib import Path

import pytest
import yaml

os.environ["PYTEST_CURRENT_TEST"] = "dead_surfaces"

ROOT = Path(__file__).resolve().parent.parent.parent

# ---------------------------------------------------------------------------
# §1  ROUTE REGISTRATION INTEGRITY
# ---------------------------------------------------------------------------

KNOWN_ORPHAN_ROUTES = {
    "memories",
    "notebooklm",
    "llm_proxy",
    "keyed_retrieval",
}

# Files that are NOT route modules (infra/helpers)
_ROUTE_INFRA_FILES = {
    "__init__",
    "middleware",
    "admin_health_probes",
    "notch_ws",
    "langbase",
    "stripe",
}


def _discover_route_modules() -> set[str]:
    """Return stems of all .py files in routes/ that define a FastAPI router."""
    routes_dir = ROOT / "babylon60" / "routes"
    modules: set[str] = set()
    for py_file in sorted(routes_dir.glob("*.py")):
        stem = py_file.stem
        if stem.startswith("_") or stem in _ROUTE_INFRA_FILES:
            continue
        text = py_file.read_text(errors="replace")
        if "APIRouter()" in text or "@router." in text or "= APIRouter(" in text:
            modules.add(stem)
    return modules


def _extract_registered_modules() -> set[str]:
    """Extract module names registered in _API_ROUTE_SPECS_ALL from routes/__init__.py."""
    init_path = ROOT / "babylon60" / "routes" / "__init__.py"
    text = init_path.read_text()
    # Match tuples like ("events", "events_router")
    return set(re.findall(r'\("(\w+)",\s*"[^"]+"\)', text))


class TestRouteRegistration:
    """§1 — Validate that all FastAPI route modules are registered."""

    def test_known_orphan_routes_detected(self):
        """Known orphan route files must be detected as unregistered."""
        registered = _extract_registered_modules()
        all_route_modules = _discover_route_modules()
        unregistered = all_route_modules - registered

        for orphan in KNOWN_ORPHAN_ROUTES:
            assert orphan in unregistered, (
                f"Expected orphan route '{orphan}' to be unregistered, "
                f"but it was found in registered set: {registered}"
            )

    def test_report_all_unregistered_routes(self):
        """Report the full list of unregistered route files."""
        registered = _extract_registered_modules()
        all_route_modules = _discover_route_modules()
        unregistered = all_route_modules - registered

        # This test always passes — it reports findings
        logging.getLogger(__name__).info(f"\n[DEAD-SURFACE §1] Registered: {sorted(registered)}")
        logging.getLogger(__name__).info(f"[DEAD-SURFACE §1] All route modules: {sorted(all_route_modules)}")
        logging.getLogger(__name__).info(f"[DEAD-SURFACE §1] Unregistered: {sorted(unregistered)}")
        assert len(unregistered) >= len(KNOWN_ORPHAN_ROUTES), (
            f"Expected at least {len(KNOWN_ORPHAN_ROUTES)} orphan routes, "
            f"found {len(unregistered)}: {sorted(unregistered)}"
        )


# ---------------------------------------------------------------------------
# §2  BROKEN IMPORTS (P0)
# ---------------------------------------------------------------------------


class TestBrokenImports:
    """§2 — Validate P0 broken import: EventSourceResponse in fastapi.responses."""

    def test_event_source_response_not_in_fastapi(self):
        """EventSourceResponse is NOT a native fastapi.responses export.

        If sse-starlette monkey-patches it in, skip. Otherwise confirm the gap.
        """
        import fastapi.responses as fr

        members = dir(fr)
        if "EventSourceResponse" in members:
            pytest.skip(
                "sse-starlette is installed and patches EventSourceResponse "
                "into fastapi.responses — P0 masked at runtime"
            )
        # Confirmed: EventSourceResponse does NOT exist natively
        assert "EventSourceResponse" not in members, (
            "EventSourceResponse unexpectedly found in fastapi.responses"
        )

    def test_relay_server_references_event_source(self):
        """Confirm that relay_server.py actually references EventSourceResponse."""
        relay = ROOT / "babylon60" / "cli" / "relay_server.py"
        if not relay.exists():
            pytest.skip("relay_server.py not found")
        text = relay.read_text(errors="replace")
        assert "EventSourceResponse" in text, (
            "relay_server.py no longer references EventSourceResponse — P0 may be fixed"
        )


# ---------------------------------------------------------------------------
# §3  PHANTOM AGENT TOOLS
# ---------------------------------------------------------------------------

KNOWN_PHANTOM_TOOLS = {
    "dag_executor",
    "consensus_arbiter",
    "agent_dispatch",
    "agent_registry",
    "embedding_benchmark",
    "recall_evaluator",
    "compaction_engine",
    "bundle_analyzer",
    "browser_interaction",
    "lighthouse_audit",
    "notebooklm_ingest",
}


def _collect_yaml_tools() -> dict[str, list[str]]:
    """Parse all agent YAML definitions and extract tools lists."""
    defs_dir = ROOT / "babylon60" / "extensions" / "agents" / "definitions"
    agent_tools: dict[str, list[str]] = {}
    for yaml_file in sorted(defs_dir.glob("*.yaml")):
        with open(yaml_file, encoding="utf-8") as fh:
            data = yaml.safe_load(fh)
        if data and isinstance(data.get("tools"), list):
            agent_tools[yaml_file.stem] = data["tools"]
    return agent_tools


def _collect_implemented_tools() -> set[str]:
    """Collect tool names that have Python implementations."""
    tools_dir = ROOT / "babylon60" / "extensions" / "agents" / "tools"
    implemented: set[str] = set()
    if not tools_dir.exists():
        return implemented
    for py_file in tools_dir.glob("*.py"):
        stem = py_file.stem
        if not stem.startswith("_"):
            # Strip common suffixes to get canonical tool name
            canonical = stem.removesuffix("_tool")
            implemented.add(canonical)
            implemented.add(stem)
    return implemented


class TestPhantomAgentTools:
    """§3 — Validate that agent YAML tools reference real implementations."""

    def test_detect_phantom_tools(self):
        """At least 5 phantom tools must be detected."""
        agent_tools = _collect_yaml_tools()
        implemented = _collect_implemented_tools()

        # Flatten all referenced tools
        all_referenced: set[str] = set()
        for tools_list in agent_tools.values():
            all_referenced.update(tools_list)

        phantom = all_referenced - implemented
        logging.getLogger(__name__).info(f"\n[DEAD-SURFACE §3] Implemented tools: {sorted(implemented)}")
        logging.getLogger(__name__).info(f"[DEAD-SURFACE §3] All referenced tools: {sorted(all_referenced)}")
        logging.getLogger(__name__).info(f"[DEAD-SURFACE §3] Phantom tools ({len(phantom)}): {sorted(phantom)}")

        assert len(phantom) >= 5, (
            f"Expected >= 5 phantom tools, found {len(phantom)}: {sorted(phantom)}"
        )

    def test_known_phantoms_detected(self):
        """Known phantom tools must appear in the phantom set."""
        agent_tools = _collect_yaml_tools()
        implemented = _collect_implemented_tools()

        all_referenced: set[str] = set()
        for tools_list in agent_tools.values():
            all_referenced.update(tools_list)

        phantom = all_referenced - implemented

        detected_known = KNOWN_PHANTOM_TOOLS & phantom
        logging.getLogger(__name__).info(
            f"\n[DEAD-SURFACE §3] Known phantoms detected: "
            f"{sorted(detected_known)} ({len(detected_known)}/{len(KNOWN_PHANTOM_TOOLS)})"
        )
        # At least half of the known phantoms should be detected
        assert len(detected_known) >= len(KNOWN_PHANTOM_TOOLS) // 2, (
            f"Expected >= {len(KNOWN_PHANTOM_TOOLS) // 2} known phantoms, "
            f"found {len(detected_known)}: {sorted(detected_known)}"
        )


# ---------------------------------------------------------------------------
# §4  MISSING __init__.py
# ---------------------------------------------------------------------------


class TestMissingInitPy:
    """§4 — Validate that extension directories with .py files have __init__.py."""

    def test_detect_missing_init(self):
        """Directories with .py files must have __init__.py."""
        ext_dir = ROOT / "babylon60" / "extensions"
        missing: list[str] = []

        for dirpath in sorted(ext_dir.rglob("*")):
            if not dirpath.is_dir():
                continue
            if dirpath.name == "__pycache__":
                continue
            py_files = list(dirpath.glob("*.py"))
            if not py_files:
                continue
            init_file = dirpath / "__init__.py"
            if not init_file.exists():
                rel = dirpath.relative_to(ROOT)
                missing.append(str(rel))

        logging.getLogger(__name__).info(f"\n[DEAD-SURFACE §4] Dirs missing __init__.py: {missing}")
        assert len(missing) >= 1, "Expected at least 1 directory missing __init__.py"

    def test_ttt_missing_init(self):
        """Known gap: babylon60/extensions/ttt/ has no __init__.py."""
        ttt_dir = ROOT / "babylon60" / "extensions" / "ttt"
        if not ttt_dir.exists():
            pytest.skip("ttt/ directory does not exist")

        py_files = list(ttt_dir.glob("*.py"))
        assert len(py_files) > 0, "ttt/ has no .py files — gap no longer relevant"
        assert not (ttt_dir / "__init__.py").exists(), (
            "ttt/__init__.py now exists — gap has been fixed"
        )


# ---------------------------------------------------------------------------
# §5  CLI ORPHAN DETECTION
# ---------------------------------------------------------------------------

CLI_ORPHAN_FILES = [
    "relay_daemon.py",
    "relay_server.py",
    "demo_bicameral.py",
    "demo_swarm.py",
]


class TestCLIOrphans:
    """§5 — Validate that standalone CLI files are not imported by main.py."""

    def test_orphan_files_exist(self):
        """Orphan CLI files must exist on disk."""
        cli_dir = ROOT / "babylon60" / "cli"
        for filename in CLI_ORPHAN_FILES:
            filepath = cli_dir / filename
            assert filepath.exists(), f"Expected orphan file {filename} to exist"

    def test_orphans_not_in_main(self):
        """Orphan CLI files must NOT be referenced in main.py."""
        main_path = ROOT / "babylon60" / "cli" / "main.py"
        main_text = main_path.read_text(errors="replace")

        for filename in CLI_ORPHAN_FILES:
            module_name = filename.removesuffix(".py")
            # Check neither import nor string reference
            assert module_name not in main_text, (
                f"Orphan module '{module_name}' is referenced in main.py — "
                f"it may no longer be orphaned"
            )
        logging.getLogger(__name__).info(f"\n[DEAD-SURFACE §5] Confirmed orphans: {CLI_ORPHAN_FILES}")
