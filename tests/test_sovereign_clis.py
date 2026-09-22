#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ SOVEREIGN CLIS TEST SUITE | TESTS | STATE: C5-REAL
# ============================================================================
"""
Unit tests for BABYLON-60 sovereign CLI entrypoints:
  - babylon60-swarm / edin-swarm
  - babylon60-acoustics / balag60
  - babylon60-transduce
"""

from pathlib import Path
from edin.cli.swarm_cli import main as swarm_cli_main
from agents_archi.cli.swarm_cli import main as agents_archi_cli_main
from babylon60.cli.acoustics_cli import main as acoustics_cli_main
from babylon60.cli.transduction_cli import find_canonical_balag_stem


def test_swarm_cli_profile() -> None:
    """Validates that swarm profile executes cleanly with code 0."""
    code = swarm_cli_main(["profile"])
    assert code == 0


def test_swarm_cli_route() -> None:
    """Validates typo-tolerant routing via swarm CLI."""
    code = swarm_cli_main(["route", "enjmabres"])
    assert code == 0


def test_swarm_cli_kudurru_accepted() -> None:
    """Validates acceptance of high-exergy candidate through CLI."""
    code = swarm_cli_main(
        [
            "kudurru",
            "--payload",
            "Axiomatic proof of Chentsov uniqueness over manifold",
            "--exergy",
            "0.95",
        ]
    )
    assert code == 0


def test_swarm_cli_kudurru_rejected() -> None:
    """Validates silent drop / rejection of uniform low-entropy slop."""
    code = swarm_cli_main(
        [
            "kudurru",
            "--payload",
            "00000000",
            "--exergy",
            "0.10",
        ]
    )
    assert code == 1


def test_acoustics_cli_euclidean() -> None:
    """Validates Euclidean rhythm calculation via acoustics CLI."""
    code = acoustics_cli_main(["euclidean", "5", "8"])
    assert code == 0


def test_acoustics_cli_scala(tmp_path: Path) -> None:
    """Validates export of Scala .scl tuning files via acoustics CLI."""
    dest = tmp_path / "tunings"
    code = acoustics_cli_main(["scala", "--destination", str(dest)])
    assert code == 0
    assert (dest / "babylon60_just_intonation_12.scl").exists()
    assert (dest / "pythagorean_12.scl").exists()
    assert (dest / "babylon60_sexagesimal_harmonics.scl").exists()


def test_agents_archi_facade_cli() -> None:
    """Validates backward-compatible agents_archi CLI facade."""
    code = agents_archi_cli_main(["profile"])
    assert code == 0


def test_find_canonical_balag_stem() -> None:
    """Verifies lookup logic for BALAG-60 canonical acoustic stems."""
    stem = find_canonical_balag_stem()
    # If the file exists in ~/Music or data/c5_acoustics, it returns a valid string path
    if stem is not None:
        assert Path(stem).exists()
        assert stem.endswith(".wav")
