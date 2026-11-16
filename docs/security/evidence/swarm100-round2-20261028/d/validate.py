#!/usr/bin/env python3
"""Disposable-fixture validation; no repository source writes or production state."""

import contextlib
import hashlib
import importlib.util
import io
import json
import pathlib
import platform
import shutil
import sqlite3
import tempfile
import traceback
from types import SimpleNamespace
from unittest.mock import patch

OUT = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path("/Users/borjafernandezangulo/10_PROJECTS/BABYLON-60")
SOURCES = {
    "consolidate": REPO / "scripts/c5_cortex/consolidate_dbs.py",
    "browser": REPO
    / "tools/skill_library/global/c5-browser-forensics-and-extension-triage/scripts/browser_forensics.py",
    "native": REPO / "01_KISH_ENGINE/babylon60/utils/void_accel.c",
    "wrapper": REPO / "01_KISH_ENGINE/babylon60/transducers/void_vec.py",
}


# Source top-level was inspected before import: stdlib imports, constants, definitions,
# and a main guard. Neither module invokes its main when imported under another name.
def load(name):
    spec = importlib.util.spec_from_file_location("fixture_audit_" + name, SOURCES[name])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


results = {
    "python": platform.python_version(),
    "sqlite": sqlite3.sqlite_version,
    "source_hashes_before": {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in SOURCES.items()},
    "cases": [],
    "limits": [
        "All mutations confined to new disposable fixture root.",
        "No actual browser profile, user database, network, credentials, hardware or native accelerator execution.",
        "Actual Python source functions imported after top-level inspection; production globals redirected before function calls.",
        "These fixtures validate stated failure triggers, not deployed reachability or production data loss.",
    ],
}
with tempfile.TemporaryDirectory(prefix="fixture-", dir=OUT) as td:
    fixture = pathlib.Path(td).resolve()
    results["fixture_root"] = str(fixture)
    consolidation = load("consolidate")
    browser = load("browser")
    original_unlink, original_rmtree, original_copy2 = pathlib.Path.unlink, shutil.rmtree, shutil.copy2

    def contained(path):
        resolved = pathlib.Path(path).resolve()
        if not resolved.is_relative_to(fixture):
            raise AssertionError("Fixture boundary violation: " + str(resolved))

    def safe_unlink(path, *args, **kwargs):
        contained(path)
        return original_unlink(path, *args, **kwargs)

    def safe_rmtree(path, *args, **kwargs):
        contained(path)
        return original_rmtree(path, *args, **kwargs)

    def safe_copy2(src, dst, *args, **kwargs):
        contained(src)
        contained(dst)
        return original_copy2(src, dst, *args, **kwargs)

    def run_case(name, fn):
        log = io.StringIO()
        try:
            with (
                contextlib.redirect_stdout(log),
                patch.object(pathlib.Path, "unlink", safe_unlink),
                patch.object(shutil, "rmtree", safe_rmtree),
                patch.object(shutil, "copy2", safe_copy2),
            ):
                case = fn()
            case.update(name=name, execution="completed", stdout=log.getvalue())
        except Exception as exc:
            case = dict(
                name=name, execution="failed", error=repr(exc), traceback=traceback.format_exc(), stdout=log.getvalue()
            )
        results["cases"].append(case)

    def rows(path):
        conn = sqlite3.connect(path)
        try:
            return conn.execute("SELECT item FROM witness ORDER BY item").fetchall()
        finally:
            conn.close()

    def make_db(path, item):
        path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(path)
        conn.execute("CREATE TABLE witness (item TEXT)")
        conn.execute("INSERT INTO witness VALUES (?)", (item,))
        conn.commit()
        conn.close()

    def divergent():
        root = fixture / "divergent" / "repo"
        central = fixture / "divergent" / "central"
        source = root / "cortex.db"
        dest = central / "cortex.db"
        make_db(source, "unique_source_record")
        make_db(dest, "unique_destination_record")
        before = dict(source=rows(source), destination=rows(dest))
        consolidation.REPO_ROOT = root
        consolidation.CENTRAL_DIR = central
        consolidation.consolidate_dbs()
        after = dict(source_exists=source.exists(), destination=rows(dest))
        return dict(
            verdict="corroborated"
            if not after["source_exists"] and after["destination"] == before["destination"]
            else "not_corroborated",
            input={"source_name": "cortex.db", "existing_destination_name": "cortex.db"},
            before=before,
            after=after,
            condition="Different source and existing destination with identical basename; function invoked explicitly.",
        )

    run_case("divergent_same_name_ledger_deletion", divergent)

    def wal():
        root = fixture / "wal" / "repo"
        central = fixture / "wal" / "central"
        root.mkdir(parents=True)
        source = root / "cortex.db"
        dest = central / "cortex.db"
        conn = sqlite3.connect(source)
        try:
            mode = conn.execute("PRAGMA journal_mode=WAL").fetchone()[0]
            conn.execute("PRAGMA wal_autocheckpoint=0")
            conn.execute("CREATE TABLE witness (item TEXT)")
            conn.commit()
            checkpoint = conn.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchall()
            conn.execute("INSERT INTO witness VALUES ('committed_only_in_wal')")
            conn.commit()
            walpath = pathlib.Path(str(source) + "-wal")
            before = dict(
                mode=mode,
                checkpoint=checkpoint,
                source_rows=conn.execute("SELECT item FROM witness").fetchall(),
                wal_exists=walpath.exists(),
                wal_bytes=walpath.stat().st_size,
            )
            consolidation.REPO_ROOT = root
            consolidation.CENTRAL_DIR = central
            consolidation.consolidate_dbs()
            after = dict(source_exists=source.exists(), source_wal_exists=walpath.exists(), destination_rows=rows(dest))
            return dict(
                verdict="corroborated"
                if before["source_rows"] and not after["destination_rows"] and not after["source_wal_exists"]
                else "not_corroborated",
                before=before,
                after=after,
                condition="WAL committed row not checkpointed; live connection kept open during consolidation; no destination exists.",
            )
        finally:
            conn.close()

    run_case("committed_wal_omitted_then_deleted", wal)

    def purge(absolute):
        root = fixture / ("browser_absolute" if absolute else "browser_relative")
        profile = root / "Chrome" / "Default"
        (profile / "Extensions").mkdir(parents=True)
        victim = root / "other_directory" if absolute else profile / "victim"
        victim.mkdir()
        sentinel = victim / "disposable-sentinel.txt"
        sentinel.write_text("fixture only")
        extid = str(victim) if absolute else "../victim"
        browser.CHROME_BASE = str(root / "Chrome")
        observed_profiles = browser.get_profile_paths()
        browser.cmd_purge(SimpleNamespace(id=extid))
        after = dict(victim_exists=victim.exists(), sentinel_exists=sentinel.exists(), profile_exists=profile.exists())
        return dict(
            verdict="corroborated" if not after["sentinel_exists"] and after["profile_exists"] else "not_corroborated",
            input={"id": extid, "profiles": observed_profiles},
            before={"sentinel_exists": True, "victim_inside_extensions": False},
            after=after,
            condition="CLI-equivalent purge callback; only fake Chrome base redirected; target is a new fixture directory outside Extensions.",
        )

    run_case("extension_purge_relative_traversal", lambda: purge(False))
    run_case("extension_purge_absolute_path", lambda: purge(True))

# Pure integer witness for the size_t subtraction, no C compilation or native call.
boundaries = []
for bits in (32, 64):
    mask = (1 << bits) - 1
    for width in (16, 64):
        for length in (0, 1, width - 1, width, width + 1):
            bound = (length - width) & mask
            boundaries.append(
                dict(
                    size_t_bits=bits,
                    vector_bytes=width,
                    len=length,
                    initial_j=0,
                    wrapped_bound=bound,
                    loop_enters=(0 <= bound),
                    first_load_in_bounds=(length >= width),
                )
            )
results["native_boundary_analysis"] = {
    "verdict": "corroborated_static_mathematical",
    "source_lines": [32, 63],
    "witnesses": boundaries,
    "condition": "C size_t subtraction is unsigned. For len<vector width, initial comparison admits a load wider than buffer. Applies only if matching native accelerator source is compiled/loaded; artifact provenance not established.",
}
results["source_hashes_after"] = {k: hashlib.sha256(v.read_bytes()).hexdigest() for k, v in SOURCES.items()}
results["source_unchanged"] = results["source_hashes_before"] == results["source_hashes_after"]
(OUT / "results.json").write_text(json.dumps(results, indent=2))
print(
    json.dumps(
        {
            "cases": [(x["name"], x.get("verdict", x["execution"])) for x in results["cases"]],
            "source_unchanged": results["source_unchanged"],
            "results": str(OUT / "results.json"),
        },
        indent=2,
    )
)
