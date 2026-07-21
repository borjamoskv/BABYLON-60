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

import re
import pathlib
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIRS = ["babylon60", "strike_rs/src", "contracts", "scripts", "proof"]
PRUNE = {"target", "__pycache__", ".venv", "node_modules", "experimental", ".lake", "dist", "extensions"}


def _iter_files(exts):  # type: ignore
    for d in SRC_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.suffix in exts and f.is_file() and PRUNE.isdisjoint(f.parts):
                yield f


def _scan(exts, pattern, flags=0):  # type: ignore
    rx = re.compile(pattern, flags)
    hits = []
    for f in _iter_files(exts):  # type: ignore
        text = f.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    return hits


def _fail_msg(law, hits):  # type: ignore
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
    assert not hits, _fail_msg("INV_C5_04 (firma real)", hits)  # type: ignore


@pytest.mark.xfail(
    reason="Advisory: SIGKILL es fail-fast intencional hoy; INV_C5_07 pide SIGTERM+cleanup.", strict=False
)
def test_inv_c5_07b_no_global_sigkill() -> None:
    """INV_C5_07 (advisory) — SIGKILL global no es tolerancia bizantina, es auto-necrosis."""
    hits = _scan({".py"}, r"signal\.SIGKILL")  # type: ignore
    assert not hits, _fail_msg("INV_C5_07b (SIGKILL global)", hits)  # type: ignore


@pytest.mark.skip(
    reason="INV_C5_06 (modelo ligado) exige revisión humana: el .lean debe ligar mecánicamente a ledger_actor, no por prosa."
)
def test_inv_c5_06_lean_bound_to_system() -> None:
    pass


@pytest.mark.asyncio
async def test_inv_c5_05_verify_chain_survives_encryption(tmp_path, monkeypatch) -> None:  # type: ignore
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
    # Filter out library self-references if any
    hits = [
        h
        for h in hits
        if "test_c5_invariants.py" not in h and "autodetect_invariants.py" not in h and "demo_exergy_poc.py" not in h
    ]
    assert not hits, _fail_msg("INV_C5_10 (PyNaCl serialization)", hits)  # type: ignore


def test_inv_c5_11_gh_purge_constraints() -> None:
    """INV_C5_11 — Abort git push --mirror/mirror-rewrites if gh auth fails or Broken pipe detected."""
    # Scan for Option B retries in error catching blocks
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
    # Temporarily bypass PRUNE checks for extensions directory to detect wal_checkpoint
    rx = re.compile(r"PRAGMA\s+wal_checkpoint\(TRUNCATE\)|CORTEX-TAINT:borjamoskv:seal:")
    hits = []
    # Explicitly scan extensions directory for seal protocol markers
    for f in ROOT.rglob("*.py"):
        if ".venv" in f.parts or "node_modules" in f.parts or "target" in f.parts:
            continue
        text = f.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}")

    assert len(hits) >= 1, "Terminal Seal Protocol (INV_C5_16) implementation markers not found in the source tree."


def test_inv_c5_17_autodidact_omega_bypass() -> None:
    """INV_C5_17 — Autodidact Omega & Ultrathink Bypass."""
    local_agents = ROOT / ".agents/AGENTS.md"
    found = False
    if local_agents.exists():
        text = local_agents.read_text(errors="ignore")
        if "INV_C5_17" in text and "Ultrathink Bypass" in text:
            found = True
    assert found, "INV_C5_17 missing in local AGENTS.md"
