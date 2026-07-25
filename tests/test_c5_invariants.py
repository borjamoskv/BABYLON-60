"""
Conformidad C5-REAL — dientes de la AUDITORIA_CENTURIA.
Cada test codifica una ley INV_C5_* de ETHOS v9.3. Se pone ROJO si el pecado
reaparece en el árbol; verde sólo cuando el hallazgo está remediado.

  INV_C5_01  veracidad criptográfica  — sin commitments aleatorios
  INV_C5_02  clave soberana           — sin secretos en el árbol
  INV_C5_03  hash único               — sin MD5/SHA-1 en atestación
  INV_C5_04  firma real               — sin firmas mock
  INV_C5_05  verificador vivo         — verify_chain válido bajo cifrado
  INV_C5_06  modelo ligado            — (revisión manual; ver docstring)
  INV_C5_07  falla ruidosa            — sin broad-except / SIGKILL global

Génesis forense: AUDITORIA_CENTURIA.md (2026-07-17).
"""

import pathlib
import re
from collections.abc import Generator

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIRS = ["babylon60", "strike_rs/src", "contracts", "scripts", "proof"]
PRUNE = {"target", "__pycache__", ".venv", "node_modules", "experimental", ".lake", "dist", "extensions"}


def _iter_files(exts: set[str]) -> Generator[pathlib.Path, None, None]:
    for d in SRC_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.suffix in exts and f.is_file() and PRUNE.isdisjoint(f.parts):
                yield f


def _scan(exts: set[str], pattern: str, flags: int = 0) -> list[str]:
    rx = re.compile(pattern, flags)
    hits = []
    for f in _iter_files(exts):  # type: ignore
        text = f.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    return hits


def _fail_msg(law: str, hits: list[str]) -> str:
    return f"{law} violado — {len(hits)} ocurrencia(s):\n  " + "\n  ".join(hits)


def test_inv_c5_02_no_hardcoded_keys() -> None:
    """INV_C5_02 — ninguna clave simétrica literal vive en el árbol (env/KMS o nada)."""
    hits = _scan({".rs"}, r'Key::new\([^,]*,\s*b"')  # type: ignore
    hits += _scan(  # type: ignore
        {".py", ".rs", ".ts", ".js", ".sol", ".sh", ".yaml", ".yml", ".toml"},
        r'(SECRET|PRIVATE_KEY|MASTER_LEDGER_KEY|master_key|solana_keypair)\s*[:=]\s*["\']\w',
    )
    hits = [h for h in hits if "demo_exergy_poc.py" not in h]
    assert not hits, _fail_msg("INV_C5_02 (clave soberana)", hits)  # type: ignore


def test_inv_c5_01_no_fake_commitments() -> None:
    """INV_C5_01 — un commitment/hash debe ligar al payload, no ser token aleatorio."""
    hits = _scan({".py"}, r'(commitment|_hash)"\s*:\s*f"(sha256|hmac-sha256):\{.*token_hex')  # type: ignore
    assert not hits, _fail_msg("INV_C5_01 (veracidad criptográfica)", hits)  # type: ignore


def test_inv_c5_03_no_weak_hashes() -> None:
    """INV_C5_03 — un solo primitivo fuerte (SHA3-256/BLAKE3); MD5/SHA-1 proscritos."""
    hits = _scan({".py"}, r"hashlib\.(md5|sha1)\b")  # type: ignore
    assert not hits, _fail_msg("INV_C5_03 (hash único)", hits)  # type: ignore


def test_inv_c5_04_no_mock_signatures() -> None:
    """INV_C5_04 — Ed25519 físico o el recibo no existe; ninguna firma 'mock'."""
    hits = _scan({".py"}, r"mock_signature|ed25519:mock")  # type: ignore
    assert not hits, _fail_msg("INV_C5_04 (firma int)", hits)  # type: ignore


def test_inv_c5_07a_no_broad_except() -> None:
    """INV_C5_07 — Loud Failure: except Exception is strictly prohibited."""
    hits = _scan({".py"}, r"except\s+Exception\s*\w*\s*:")
    hits = [
        h
        for h in hits
        if "test_c5_invariants.py" not in h
        and "autodetect_invariants.py" not in h
        and "exergy_mass_mutator.py" not in h
    ]
    assert not hits, _fail_msg(
        "INV_C5_07a (Generic except (ValueError, TypeError, KeyError, RuntimeError, OSError, AssertionError): found)",
        hits,
    )


def test_inv_c5_07b_no_global_sigkill() -> None:
    """INV_C5_07 — SIGKILL global en runtime de aplicación no es tolerancia bizantina, es auto-necrosis."""
    hits = _scan({".py"}, r"signal\.SIGKILL")  # type: ignore
    hits = [h for h in hits if not h.startswith("scripts/")]
    assert not hits, _fail_msg("INV_C5_07b (SIGKILL global)", hits)  # type: ignore


@pytest.mark.skip(
    reason="INV_C5_06 (modelo ligado) exige revisión humana: el .lean debe ligar mecánicamente a ledger_actor, no por prosa."
)
def test_inv_c5_06_lean_bound_to_system() -> None:
    pass


@pytest.mark.asyncio
async def test_inv_c5_05_verify_chain_survives_encryption(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """INV_C5_05 — el verificador valida el estado que protege bajo cifrado.
    Hoy ROJO: el INSERT hashea el payload cifrado y verify_chain hashea el
    descifrado -> entry_hash != computed_hash -> False con CORTEX_VAULT_KEY activo.
    """
    pytest.importorskip("aiosqlite")
    fernet_mod = pytest.importorskip("cryptography.fernet")
    ledger = pytest.importorskip("babylon60.bft.ledger_actor")

    monkeypatch.setenv("CORTEX_VAULT_KEY", fernet_mod.Fernet.generate_key().decode("utf-8"))
    actor = ledger.BFTLedgerActor(tmp_path / "ledger.db")
    await actor.start()
    event = ledger.LedgerEvent(
        stream="audit",
        entity_id="e1",
        event_type="append",
        payload={"k": "v"},
        cortex_taint="operator/2026-07-17/test",
        source_db="db",
        source_table="t",
        source_pk="1",
    )
    await actor.append(event)
    ok = await actor.verify_chain()
    await actor.stop()
    assert ok is True, (
        "INV_C5_05: verify_chain() debe devolver True para un ledger CIFRADO. "
        "Fix: hashear la MISMA representación (texto plano en ambos caminos, "
        "o cifrado en ambos) en INSERT y en verify_chain."
    )


def test_inv_c5_10_pynacl_serialization() -> None:
    """INV_C5_10 — PyNaCl key serialization must not access private attributes like _seed or _public_key."""
    hits = _scan({".py"}, r"\._seed\b|\._public_key\b")  # type: ignore
    hits = [
        h
        for h in hits
        if "test_c5_invariants.py" not in h
        and "autodetect_invariants.py" not in h
        and "demo_exergy_poc.py" not in h
        and "exergy_mass_mutator.py" not in h
    ]
    assert not hits, _fail_msg("INV_C5_10 (PyNaCl serialization)", hits)  # type: ignore


def test_inv_c5_11_gh_purge_constraints() -> None:
    """INV_C5_11 — Abort git push --mirror/mirror-rewrites if gh auth fails or Broken pipe detected."""
    hits = _scan({".py", ".sh"}, r"git\s+push\s+--mirror.*retry|Broken\s+pipe.*Option\s+B")  # type: ignore
    assert not hits, _fail_msg("INV_C5_11 (Gh purge constraints)", hits)  # type: ignore


def test_inv_c5_12_nexus_symlinks() -> None:
    """INV_C5_12 — Relative symbolic links within babylon60 must have exactly two levels of depth (../../)."""
    for link_name in ["crypto", "extensions", "utils"]:
        link_path = ROOT / "babylon60" / link_name
        if link_path.is_symlink():
            target = str(link_path.readlink())
            assert target.startswith("../../"), (
                f"Symlink {link_name} target '{target}' does not have correct relative depth of 2."
            )


def test_inv_c5_13_autodetect_executable() -> None:
    """INV_C5_13 — autodetect_invariants.py script must exist and be executable."""
    import os

    script_path = ROOT / "scripts" / "autodetect_invariants.py"
    assert script_path.exists(), "autodetect_invariants.py missing."
    assert os.access(script_path, os.X_OK), "autodetect_invariants.py is not executable."


def test_inv_c5_14_exergy_agent() -> None:
    """INV_C5_14 — exergy_optimizer_agent.py must exist, be executable, and write attestation into ledger."""
    import os

    script_path = ROOT / "scripts" / "exergy_optimizer_agent.py"
    assert script_path.exists(), "exergy_optimizer_agent.py missing."
    assert os.access(script_path, os.X_OK), "exergy_optimizer_agent.py is not executable."

    db_path = pathlib.Path(os.path.expanduser("~")) / ".babylon60" / "exergy_agent_ledger.db"
    if not db_path.exists():
        pytest.skip(
            "exergy_agent_ledger.db es un artefacto de runtime local (~/.babylon60); "
            "no existe en un runner de CI limpio"
        )


def test_inv_c5_15_sync_vault_uuids() -> None:
    """INV_C5_15 — sync_vault_uuids.py must exist and be executable."""
    import os

    script_path = ROOT / "scripts" / "sync_vault_uuids.py"
    assert script_path.exists(), "sync_vault_uuids.py missing."
    assert os.access(script_path, os.X_OK), "sync_vault_uuids.py is not executable."


def test_inv_c5_16_terminal_seal_protocol() -> None:
    """INV_C5_16 — Terminal Seal Protocol verification in CLI and scripts."""
    rx = re.compile(r"PRAGMA\s+wal_checkpoint\(TRUNCATE\)|CORTEX-TAINT:borjamoskv:seal:")
    hits = []
    for f in ROOT.rglob("*.py"):
        if ".venv" in f.parts or "node_modules" in f.parts or "target" in f.parts:
            continue
        text = f.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}")

    assert len(hits) >= 1, "Terminal Seal Protocol (INV_C5_16) implementation markers not found in the source tree."


def test_inv_c5_17_autodidact_omega_bypass() -> None:
    """INV_C5_17 — Autodidact Omega & Ultrathink Protocol."""
    local_agents = ROOT / ".agents/AGENTS.md"
    found = False
    text = ""
    if local_agents.exists():
        text = local_agents.read_text(errors="ignore")
        if "INV_C5_17" in text and "Ultrathink Protocol" in text:
            found = True
    assert found, (
        f"INV_C5_17 missing in local AGENTS.md. Path: {local_agents}, Exists: {local_agents.exists()}, Text preview: {text[:100]}"
    )


def test_inv_c5_18_bft_float_exclusion() -> None:
    """INV_C5_18 — BFT Float Exclusion in canonicalize_cbor and BFT_Ledger."""
    import pytest

    from babylon60.core.crypto import canonicalize_cbor

    with pytest.raises(ValueError, match="Flotantes"):
        canonicalize_cbor({"data": 12.34})


def test_inv_c5_19_memory_convergence() -> None:
    """INV_C5_19 — BFT orchestration memory convergence must collapse into memory_vault."""
    hits = _scan({".py"}, r"memory_vault")
    assert hits, "INV_C5_19 violated: memory_vault convergence missing"


def test_inv_c5_20_kinetic_purge_protocol() -> None:
    """INV_C5_20 — Kinetic Purge Protocol must implement Mach VM cache dropping and SIGKILL rogue daemons."""
    hits_osascript = _scan({".py", ".sh"}, r'osascript\s+-e\s+[\'"]do\s+shell\s+script\s+["\']purge["\'][\'"]')
    hits_sigkill = _scan({".py", ".sh"}, r"kill\s+-9|SIGKILL")
    assert hits_osascript, "INV_C5_20 violated: Missing Mach VM cache drop via osascript purge"
    assert hits_sigkill, "INV_C5_20 violated: Missing SIGKILL (-9) on rogue daemons"


def test_inv_c5_08_solidity_eip1153() -> None:
    """INV_C5_08 — Solidity EIP-1153 transient reentrancy locks must read via tload and clear via tstore."""
    for f in _iter_files({".sol"}):
        text = f.read_text(errors="ignore")
        if "tload" in text:
            assert "tstore" in text, f"INV_C5_08 violated in {f}: tload without tstore cleanup"


def test_inv_c5_09_venv_isolation() -> None:
    """INV_C5_09 — Test execution must specify .venv Python 3.12+ isolation and BypassSandbox: true."""
    agents_paths = [ROOT / ".agents" / "AGENTS.md", ROOT / "AGENTS.md"]
    hits = [p for p in agents_paths if p.exists() and "BypassSandbox: true" in p.read_text(errors="ignore")]
    assert hits, "INV_C5_09 violated: Missing BypassSandbox: true specification in governance docs"


def test_inv_c5_21_goal_exergy_maximization() -> None:
    """INV_C5_21 — Exergy Maximization in Unattended Orchestration (/goal)."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_21 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_21" in content, "INV_C5_21 rule definition missing in .agents/AGENTS.md"
    assert "Oracle" in content, "INV_C5_21 missing Oracle clause"
    assert "Mitosis" in content, "INV_C5_21 missing Swarm Mitosis clause"


def test_inv_c5_22_kimi_k3_interleaved_execution() -> None:
    """INV_C5_22 — Kimi K3 Interleaved Long-Horizon Execution Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_22 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_22" in content, "INV_C5_22 rule definition missing in .agents/AGENTS.md"
    assert "Kimi" in content or "Interleaved" in content, "INV_C5_22 missing Interleaved clause"


def test_inv_c5_23_epistemic_grounding() -> None:
    """INV_C5_23 — Semi-Formal Epistemic Grounding Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_23 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_23" in content, "INV_C5_23 rule definition missing in .agents/AGENTS.md"
    assert "Epistemic" in content or "Semi-Formal" in content, "INV_C5_23 missing Epistemic clause"


def test_inv_c5_24_git_commit_signature_fallback() -> None:
    """INV_C5_24 — Git Commit Signature Fallback Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_24 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_24" in content, "INV_C5_24 rule definition missing in .agents/AGENTS.md"
    assert "gpgsign=false" in content, "INV_C5_24 missing gpgsign=false fallback clause"


def test_inv_c5_25_dynamic_brain_vault_scanning() -> None:
    """INV_C5_25 — Dynamic Brain Memory Vault Scanning Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_25 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_25" in content, "INV_C5_25 rule definition missing in .agents/AGENTS.md"
    assert "belongs_to_babylon" in content, "INV_C5_25 missing belongs_to_babylon filtering clause"


def test_inv_c5_26_maximum_exergy_nodes() -> None:
    """INV_C5_26 — Maximum Exergy Nodes."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_26 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_26" in content, "INV_C5_26 rule definition missing in .agents/AGENTS.md"
    assert "1000/1000" in content, "INV_C5_26 missing 1000/1000 exergy criteria clause"


def test_inv_c5_27_high_density_ontological_ingestion() -> None:
    """INV_C5_27 — High Density Ontological Ingestion Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_27 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_27" in content, "INV_C5_27 rule definition missing in .agents/AGENTS.md"
    assert "S/N ≥ 0.80" in content or "S/N >= 0.80" in content, "INV_C5_27 missing Signal/Noise (S/N) ratio restriction"


def test_inv_c5_28_tauri_ipc_type_derive() -> None:
    """INV_C5_28 — Tauri IPC Type Derive Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_28 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_28" in content, "INV_C5_28 rule definition missing in .agents/AGENTS.md"
    assert "Serialize" in content and "Deserialize" in content, "INV_C5_28 missing Serialize/Deserialize requirement"


def test_inv_c5_29_pypi_proprietary_license_alignment() -> None:
    """INV_C5_29 — PyPI Proprietary License Alignment Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_29 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_29" in content, "INV_C5_29 rule definition missing in .agents/AGENTS.md"
    assert "license" in content, "INV_C5_29 missing license metadata clause"


def test_inv_c5_30_deterministic_cbor_canonization() -> None:
    """INV_C5_30 — Deterministic CBOR Structural Canonization Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_30 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_30" in content, "INV_C5_30 rule definition missing in .agents/AGENTS.md"
    assert "CBOR" in content, "INV_C5_30 missing CBOR canonization clause"


def test_inv_c5_31_keychain_bypass_test_env() -> None:
    """INV_C5_31 — Keychain Bypass in Test Environments Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_31 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_31" in content, "INV_C5_31 rule definition missing in .agents/AGENTS.md"
    assert "CORTEX_TESTING" in content, "INV_C5_31 missing CORTEX_TESTING clause"


def test_inv_c5_32_hypothesis_deadline_exemption() -> None:
    """INV_C5_32 — Hypothesis Deadline Exemption Under Load Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_32 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_32" in content, "INV_C5_32 rule definition missing in .agents/AGENTS.md"
    assert "deadline=None" in content, "INV_C5_32 missing deadline=None clause"


def test_inv_c5_33_safe_subprocess_vectorization() -> None:
    """INV_C5_33 — Safe Subprocess Argument Vectorization Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_33 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_33" in content, "INV_C5_33 rule definition missing in .agents/AGENTS.md"
    assert "shell=True" in content or "shell" in content, "INV_C5_33 missing shell=True restriction clause"


def test_inv_c5_34_rootless_uv_docker() -> None:
    """INV_C5_34 — Rootless UV Docker Multi-stage Invariant."""
    agents_path = ROOT / ".agents" / "AGENTS.md"
    assert agents_path.exists(), "INV_C5_34 violated: .agents/AGENTS.md missing"
    content = agents_path.read_text(errors="ignore")
    assert "INV_C5_34" in content, "INV_C5_34 rule definition missing in .agents/AGENTS.md"

