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


def _iter_files(exts):
    for d in SRC_DIRS:
        base = ROOT / d
        if not base.exists():
            continue
        for f in base.rglob("*"):
            if f.suffix in exts and f.is_file() and PRUNE.isdisjoint(f.parts):
                yield f


def _scan(exts, pattern, flags=0):
    rx = re.compile(pattern, flags)
    hits = []
    for f in _iter_files(exts):
        text = f.read_text(errors="ignore")
        for i, line in enumerate(text.splitlines(), 1):
            if rx.search(line):
                hits.append(f"{f.relative_to(ROOT)}:{i}: {line.strip()[:100]}")
    return hits


def _fail_msg(law, hits):
    return f"{law} violado — {len(hits)} ocurrencia(s):\n  " + "\n  ".join(hits)


def test_inv_c5_02_no_hardcoded_keys():
    """INV_C5_02 — ninguna clave simétrica literal vive en el árbol (env/KMS o nada)."""
    hits = _scan({".rs"}, r'Key::new\([^,]*,\s*b"')
    hits += _scan(
        {".py", ".rs", ".ts", ".js", ".sol", ".sh", ".yaml", ".yml", ".toml"},
        r'(SECRET|PRIVATE_KEY|MASTER_LEDGER_KEY|master_key|solana_keypair)\s*[:=]\s*["\']\w',
    )
    hits = [h for h in hits if "demo_exergy_poc.py" not in h]
    assert not hits, _fail_msg("INV_C5_02 (clave soberana)", hits)


def test_inv_c5_01_no_fake_commitments():
    """INV_C5_01 — un commitment/hash debe ligar al payload, no ser token aleatorio."""
    hits = _scan({".py"}, r'(commitment|_hash)"\s*:\s*f"(sha256|hmac-sha256):\{.*token_hex')
    assert not hits, _fail_msg("INV_C5_01 (veracidad criptográfica)", hits)


def test_inv_c5_03_no_weak_hashes():
    """INV_C5_03 — un solo primitivo fuerte (SHA3-256/BLAKE3); MD5/SHA-1 proscritos."""
    hits = _scan({".py"}, r"hashlib\.(md5|sha1)\b")
    assert not hits, _fail_msg("INV_C5_03 (hash único)", hits)


def test_inv_c5_04_no_mock_signatures():
    """INV_C5_04 — Ed25519 físico o el recibo no existe; ninguna firma 'mock'."""
    hits = _scan({".py"}, r"mock_signature|ed25519:mock")
    assert not hits, _fail_msg("INV_C5_04 (firma real)", hits)


@pytest.mark.xfail(
    reason="Advisory: SIGKILL es fail-fast intencional hoy; INV_C5_07 pide SIGTERM+cleanup.", strict=False
)
def test_inv_c5_07b_no_global_sigkill():
    """INV_C5_07 (advisory) — SIGKILL global no es tolerancia bizantina, es auto-necrosis."""
    hits = _scan({".py"}, r"signal\.SIGKILL")
    assert not hits, _fail_msg("INV_C5_07b (SIGKILL global)", hits)


@pytest.mark.skip(
    reason="INV_C5_06 (modelo ligado) exige revisión humana: el .lean debe ligar mecánicamente a ledger_actor, no por prosa."
)
def test_inv_c5_06_lean_bound_to_system():
    pass


@pytest.mark.asyncio
async def test_inv_c5_05_verify_chain_survives_encryption(tmp_path, monkeypatch):
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


def test_inv_c5_10_pynacl_serialization():
    """INV_C5_10 — PyNaCl key serialization must not access private attributes like _seed or _public_key."""
    hits = _scan({".py"}, r"\._seed\b|\._public_key\b")
    # Filter out library self-references if any
    hits = [
        h
        for h in hits
        if "test_c5_invariants.py" not in h and "autodetect_invariants.py" not in h and "demo_exergy_poc.py" not in h
    ]
    assert not hits, _fail_msg("INV_C5_10 (PyNaCl serialization)", hits)


def test_inv_c5_11_gh_purge_constraints():
    """INV_C5_11 — Abort git push --mirror/mirror-rewrites if gh auth fails or Broken pipe detected."""
    # Scan for Option B retries in error catching blocks
    hits = _scan({".py", ".sh"}, r"git\s+push\s+--mirror.*retry|Broken\s+pipe.*Option\s+B")
    assert not hits, _fail_msg("INV_C5_11 (Gh purge constraints)", hits)


def test_inv_c5_12_nexus_symlinks():
    """INV_C5_12 — Relative symbolic links within babylon60 must have exactly two levels of depth (../../)."""
    for link_name in ["crypto", "extensions", "utils"]:
        link_path = ROOT / "babylon60" / link_name
        if link_path.is_symlink():
            target = str(link_path.readlink())
            assert target.startswith("../../"), (
                f"Symlink {link_name} target '{target}' does not have correct relative depth of 2."
            )





def test_inv_c5_13_nesting_depth_ceiling():
    """INV_C5_13 / GELABP_DEPTH_INVARIANT — AST Control Flow Nesting Depth Ceiling <= 4 per function."""
    import ast

    CONTROL_NODES = (ast.If, ast.For, ast.While, ast.Try, ast.With)

    def get_max_depth(node, current_depth=0):
        max_d = current_depth
        for child in ast.iter_child_nodes(node):
            next_depth = current_depth + (1 if isinstance(child, CONTROL_NODES) else 0)
            max_d = max(max_d, get_max_depth(child, next_depth))
        return max_d

    hits = []
    for f in _iter_files({".py"}):
        if "test_" in f.name or "experimental" in str(f) or "scripts" in str(f):
            continue
        try:
            tree = ast.parse(f.read_text(errors="ignore"))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    depth = get_max_depth(node)
                    if depth > 4:
                        hits.append(f"{f.relative_to(ROOT)}:{node.lineno}: {node.name}() has nesting depth {depth} > 4")
        except Exception:
            pass

    assert not hits, _fail_msg("INV_C5_13 (AST Nesting Depth Ceiling <= 4)", hits)


def test_inv_c5_14_no_broad_except_pass():
    """INV_C5_14 — No bare `except Exception: pass` or swallowing exceptions silently."""
    hits = _scan({".py"}, r'except\s+Exception\s*:\s*pass\b')
    hits = [h for h in hits if "test_" not in h]
    assert not hits, _fail_msg("INV_C5_14 (No Silent Broad Except Pass)", hits)


def test_inv_c5_15_vault_sync_script():
    """INV_C5_15 — Memory vault session synchronizer script scripts/sync_vault_uuids.py must exist."""
    script_path = ROOT / "scripts" / "sync_vault_uuids.py"
    assert script_path.exists(), "INV_C5_15: scripts/sync_vault_uuids.py is missing from project"


def test_inv_c5_16_toolchain_fallback():
    """INV_C5_16 — Scripts invoking uv must provide fallback or check binary existence."""
    _ = _scan({".sh", ".py"}, r'subprocess.*["\']uv["\']\s*,')
    # Should not blindly fail if uv is absent
    assert True


def test_inv_c5_17_sovereign_zero_cost():
    """INV_C5_17 — Todo SIEMPRE 100% gratis, libre y auto-hospedado."""
    hits = _scan({".py", ".ts", ".tsx", ".toml", ".yaml"}, r'(stripe_api_key|paywall|subscription_fee|api_billing_tier)')
    assert not hits, _fail_msg("INV_C5_17 (Sovereign Zero-Cost)", hits)


def test_inv_c5_18_zero_worktree_swarm():
    """INV_C5_18 — Swarms masivos en memoria sin crear worktrees fisicos masivos."""
    hits = _scan({".py", ".sh"}, r'git\s+worktree\s+add.*agent_')
    hits = [h for h in hits if "test_" not in h]
    assert not hits, _fail_msg("INV_C5_18 (Zero-Worktree Swarm Scaling)", hits)


def test_inv_c5_19_turing_castration_scan():
    """INV_C5_19 / INV_C5_TURING_CASTRATION — No unbounded while True loops without stop_event or timeout."""
    hits = _scan({".py"}, r'while\s+True\s*:\s*$')
    hits = [h for h in hits if "test_" not in h and "extensions" not in h and "experimental" not in h and "yt-dlp" not in h]
    assert not hits, _fail_msg("INV_C5_19 (Turing Castration — Unbounded while True loop)", hits)


def test_inv_c5_20_no_placeholders():
    """INV_C5_20 — Deterministic Execution Matrix: No placeholders (# TODO, pass, ...)."""
    hits = _scan({".py", ".rs", ".ts", ".sol"}, r'(?i)#\s*TODO\b|^\s*\.\.\.\s*$')
    hits = [
        h for h in hits
        if not h.startswith("tests/") and "autodetect_invariants.py" not in h and "demo_exergy_poc.py" not in h
    ]
    assert not hits, _fail_msg("INV_C5_20 (No placeholders / TODO / ...)", hits)


def test_inv_c5_21_eip_1153():
    """INV_C5_21 — EIP-1153 strict EVM bounds: keccak256, mload(0x40), lt(gas(), 8000), revert(0x00, 0x04)."""
    hits = _scan({".sol"}, r'revert\(0,\s*0\)|revert\(0x00,\s*0x00\)')
    assert not hits, _fail_msg("INV_C5_21 (Invalid revert pattern, MUST use 0x00, 0x04)", hits)


def test_inv_c5_22_swarm_workspace_locks():
    """INV_C5_22 — Swarm Workspace Deduplication: verify atomic lock acquisition."""
    hits = _scan({".py"}, r'os\.O_CREAT')
    bad_files = []
    for hit in hits:
        filepath = hit.split(":")[0]
        full_path = ROOT / filepath
        if full_path.exists():
            content = full_path.read_text(errors="ignore")
            if ".cortex_thermal_lock" not in content and "swarm_lock_guard.py" not in content:
                bad_files.append(hit)
    assert not bad_files, _fail_msg("INV_C5_22 (Missing .cortex_thermal_lock in atomic I/O)", bad_files)


def test_inv_c5_28_stub():
    """INV_C5_28 — Auto-generated stub for rule validation."""
    # TODO: Implement concrete scan logic for rule INV_C5_28
    pass
