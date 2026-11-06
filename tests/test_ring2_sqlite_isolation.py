# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import tempfile
from pathlib import Path
from scripts.c5_quality_gates.audit_ring2_sqlite_isolation import (
    check_file_for_sqlite_imports,
    audit_ring2_isolation,
)


def test_clean_file_passes() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("import math\nfrom os import path\nx = 42\n")
        f_path = Path(f.name)
    try:
        violations = check_file_for_sqlite_imports(f_path)
        assert len(violations) == 0
    finally:
        f_path.unlink()


def test_import_sqlite3_fails() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("import sqlite3\nconn = sqlite3.connect(':memory:')\n")
        f_path = Path(f.name)
    try:
        violations = check_file_for_sqlite_imports(f_path)
        assert len(violations) == 1
        assert "import directo de 'sqlite3'" in violations[0][1]
    finally:
        f_path.unlink()


def test_from_aiosqlite_fails() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("from aiosqlite import connect\n")
        f_path = Path(f.name)
    try:
        violations = check_file_for_sqlite_imports(f_path)
        assert len(violations) == 1
        assert "from 'aiosqlite'" in violations[0][1]
    finally:
        f_path.unlink()


def test_dynamic_import_fails() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("mod = __import__('sqlite3')\n")
        f_path = Path(f.name)
    try:
        violations = check_file_for_sqlite_imports(f_path)
        assert len(violations) == 1
        assert "__import__('sqlite3') dinámico detectado" in violations[0][1]
    finally:
        f_path.unlink()


def test_dynamic_import_alias_fails() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False) as f:
        f.write("from importlib import import_module as load\nmod = load('sqlite3')\n")
        f_path = Path(f.name)
    try:
        violations = check_file_for_sqlite_imports(f_path)
        assert len(violations) == 1
        assert "load('sqlite3') dinámico detectado" in violations[0][1]
    finally:
        f_path.unlink()


def test_audit_live_repo_clean() -> None:
    assert audit_ring2_isolation() is True
