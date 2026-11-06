"""Document contracts, checked without launching hardware benchmarks."""

from pathlib import Path
import re
import subprocess
import sys
import tomllib
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def test_energy_claim_is_scoped_and_compatible_with_listing():
    claim = tomllib.loads((ROOT / "CLAIMS.toml").read_text())["claim"]["zero_anergy"]
    assert claim["status"] == "partial_trace"
    assert claim["evidence_level"] == "L2_IMPLEMENTATION"
    assert "does not measure RFO" in claim["statement"]
    assert "NO_VERIFICADO" in claim["notes"]
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts/c5_quality_gates/verify_claims.py"), "--list"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "[DECLARED] zero_anergy" in result.stdout
    assert "No outcome asserted" in result.stdout


def test_faq_does_not_promise_authentication_fallback_or_zero_energy():
    faq = (ROOT / "README.md").read_text().split("Preguntas Frecuentes para Humanos", 1)[1]
    assert "sin reintentos ni autenticación alternativa" in faq
    assert "NO_VERIFICADO" in faq
    assert "conmuta automáticamente" not in faq
    assert "0.00%" not in faq
    assert "($RFO=0$)" not in faq


def test_normative_hash_matrix_and_incident_bounds_declared():
    manifest = tomllib.loads((ROOT / "CLAIMS.toml").read_text())
    metadata = manifest["metadata"]
    assert "BLAKE3_CANONICAL" in metadata["hash_matrix_normative"]
    assert "SHA256_HARDWARE_AND_WITNESS" in metadata["hash_matrix_normative"]
    assert "SHA3_256_LEGACY_L0" in metadata["hash_matrix_normative"]
    assert "SIGKILL_VERIFIED" in metadata["incident_bounds_normative"]
    assert "POWER_LOSS_UNVERIFIED" in metadata["incident_bounds_normative"]

    sqlite_claim = manifest["claim"]["cortex_persist_sqlite"]
    assert "BLAKE3 Canonical" in sqlite_claim["notes"]
    assert "SHA-256 Hardware/Witness" in sqlite_claim["notes"]
    assert "SHA3-256 Legacy L0" in sqlite_claim["notes"]
    assert "SIGKILL" in sqlite_claim["scope"]
    assert "corte eléctrico" in sqlite_claim["scope"]

    readme_text = (ROOT / "README.md").read_text()
    assert "Matriz Normativa de Hashes (`BLAKE3` · `SHA-256` · `SHA3-256`)" in readme_text
    assert "Cotas de Incidentes (`SIGKILL` de Proceso vs. Corte Eléctrico Físico)" in readme_text


def test_monorepo_readmes_have_valid_local_links_and_no_legacy_packages_paths():
    readmes = [
        "README.md",
        "docs/README.md",
        "src/README.md",
        "00_ABZU_KERNEL/README.md",
        "00_ABZU_KERNEL/crates/babylon60-kernel/README.md",
        "00_ABZU_KERNEL/crates/babylon60-compiler/README.md",
        "00_ABZU_KERNEL/crates/strike-rs/README.md",
        "crates/eridu-infer/README.md",
        "01_KISH_ENGINE/README.md",
        "01_KISH_ENGINE/babylon60/kernel/README.md",
        "01_KISH_ENGINE/babylon60/agents/sovereign_mcp/README.md",
        "02_EDIN_SWARMS/README.md",
        "proof/README.md",
        "tests/README.md",
        "tools/README.md",
    ]
    for rel in readmes:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        assert "PYTHONPATH=packages:." not in text, f"Obsolete PYTHONPATH=packages:. in {rel}"
        assert "packages/babylon60/" not in text, f"Obsolete packages/babylon60/ path in {rel}"
        for target in re.findall(r"\]\(([^)]+)\)", text):
            parsed = urlsplit(target)
            if parsed.scheme or parsed.netloc or not parsed.path:
                continue
            dest = (path.parent / unquote(parsed.path)).resolve()
            assert dest.exists(), f"Broken local link in {rel}: {target} -> {dest}"
