#!/usr/bin/env python3
# C5-REAL EXERGY CERTIFIED
"""
verify_attestation.py (C5-REAL Certified)
-----------------------------------------
Falsifier for the L5 DevSecOps attestation.

The stamp alone prevents nothing. This transducer is where the anchoring pays:
it re-derives the source digest from the current checkout and confronts it with
the digest that Bitcoin witnessed. Any backdoor injected after the stamp, any
force-pushed rewrite of history, any silently swapped artifact, produces a
divergence that no repository authority can retro-sign away.

Four independent invariants, each falsifiable in isolation:
  I1 SELF      -- the attestation digest matches its own `core` block (no tampered JSON).
  I2 SOURCE    -- the checkout re-derives the same source digest (no code drift).
  I3 LEDGER    -- the attestation is present in the append-only L1 ledger.
  I4 ANCHOR    -- the .ots proof validates against the Bitcoin chain (L5).

Exit code 0 only if every REQUESTED invariant resists.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPTS_DIR))

import bft_sqlite  # noqa: E402  (Omega_23 dynamic module resolution)
from devsecops_attest import (  # noqa: E402
    DEFAULT_ANCHOR_DIR,
    DEFAULT_DB_PATH,
    AttestationError,
    compute_source_digest,
    recompute_digest,
)

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

OTS_TIMEOUT_SECONDS = 120.0


def _report(invariant: str, resisted: bool, detail: str) -> bool:
    status = f"{GREEN}[RESISTED]{RESET}" if resisted else f"{RED}[FALSIFIED]{RESET}"
    print(f"{status} {invariant}: {detail}")
    return resisted


def _skip(invariant: str, detail: str) -> None:
    print(f"{YELLOW}[SKIPPED]{RESET}  {invariant}: {detail}")


def verify_self(attestation: dict[str, Any]) -> bool:
    """I1: the JSON has not been edited after stamping."""
    claimed = attestation.get("attestation_digest_sha3_256", "")
    core = attestation.get("core")
    if not isinstance(core, dict) or not claimed:
        return _report("I1 SELF", False, "atestación malformada (falta `core` o el digest)")
    derived = recompute_digest(core)
    if derived != claimed:
        return _report("I1 SELF", False, f"digest declarado {claimed[:16]}... != recalculado {derived[:16]}...")
    return _report("I1 SELF", True, f"el bloque `core` produce {derived[:16]}...")


def verify_source(attestation: dict[str, Any], commit: str | None = None) -> bool:
    """I2: the working checkout still contains exactly the attested source."""
    core = attestation["core"]
    target = commit or core["commit"]
    try:
        derived = compute_source_digest(target)
    except AttestationError as exc:
        return _report("I2 SOURCE", False, f"no se pudo derivar el árbol de {target[:12]}: {exc}")

    expected = core["source_digest_sha3_256"]
    if derived != expected:
        return _report(
            "I2 SOURCE",
            False,
            f"el árbol de {target[:12]} produce {derived[:16]}... pero se atestó {expected[:16]}... "
            "-- el código difiere del que fue aprobado y escaneado",
        )
    if not core.get("worktree_clean", False):
        print(f"{YELLOW}[AVISO]{RESET}   I2 SOURCE: la atestación se emitió sobre un worktree sucio (prueba degradada)")
    return _report("I2 SOURCE", True, f"el árbol de {target[:12]} reproduce {derived[:16]}...")


def verify_ledger(attestation: dict[str, Any], db_path: Path) -> bool:
    """I3: the digest is present in the append-only L1 ledger."""
    if not db_path.exists():
        return _report("I3 LEDGER", False, f"el ledger L1 no existe en {db_path}")

    digest = attestation["attestation_digest_sha3_256"]
    conn = bft_sqlite.connect(str(db_path))
    try:
        cursor = conn.conn.execute(
            "SELECT uuid, timestamp FROM bft_taint_log WHERE payload LIKE ?",
            (f"%{digest}%",),
        )
        rows = cursor.fetchall()
    finally:
        conn.close()

    if not rows:
        return _report("I3 LEDGER", False, f"ningún registro L1 contiene {digest[:16]}...")
    return _report("I3 LEDGER", True, f"fijado en L1 como {rows[0][0]} ({rows[0][1]})")


def verify_anchor(attestation: dict[str, Any], anchor_dir: Path, upgrade: bool = True) -> bool:
    """I4: the OpenTimestamps proof validates against the Bitcoin chain."""
    digest = attestation["attestation_digest_sha3_256"]
    ots_file = anchor_dir / f"{digest}.digest.ots"
    data_file = anchor_dir / f"{digest}.digest"

    if not ots_file.exists():
        return _report("I4 ANCHOR", False, f"no existe el sello {ots_file.name}")
    if not data_file.exists():
        # Reconstructible: the stamped payload is the digest string itself.
        data_file.write_text(digest, encoding="utf-8")
    if shutil.which("ots") is None:
        return _report("I4 ANCHOR", False, "`ots` no está en PATH; el sello no puede validarse")

    if upgrade:
        subprocess.run(
            ["ots", "upgrade", str(ots_file)],
            check=False,
            capture_output=True,
            text=True,
            timeout=OTS_TIMEOUT_SECONDS,
        )

    proc = subprocess.run(
        ["ots", "verify", str(ots_file)],
        check=False,
        capture_output=True,
        text=True,
        timeout=OTS_TIMEOUT_SECONDS,
    )
    output = f"{proc.stdout}\n{proc.stderr}".strip()

    if "Success!" in output or "Bitcoin block" in output:
        line = next((ln.strip() for ln in output.splitlines() if "Bitcoin block" in ln), output.splitlines()[-1])
        return _report("I4 ANCHOR", True, line)
    if "Pending" in output or "pending" in output:
        # Not a falsification: the calendar has not folded the digest into a block yet.
        _skip("I4 ANCHOR", "sello aún pendiente de confirmación en un bloque de Bitcoin (reintenta en ~1-24h)")
        return True
    return _report("I4 ANCHOR", False, output.splitlines()[-1] if output else "ots verify no produjo salida")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Falsifies a DevSecOps attestation against source, ledger and Bitcoin.")
    parser.add_argument("attestation", type=Path, help="Path to the .attestation.json produced by devsecops_attest.py")
    parser.add_argument("--commit", default=None, help="Re-derive the source digest from this commit instead of the attested one.")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the L1 BFT ledger.")
    parser.add_argument("--anchor-dir", type=Path, default=DEFAULT_ANCHOR_DIR, help="Directory holding the .ots proofs.")
    parser.add_argument("--skip-ledger", action="store_true", help="Do not check invariant I3 (useful on a fresh CI runner).")
    parser.add_argument("--skip-anchor", action="store_true", help="Do not check invariant I4 (offline audit).")
    parser.add_argument("--no-upgrade", action="store_true", help="Do not contact calendars to upgrade the stamp.")
    args = parser.parse_args(argv)

    if not args.attestation.is_file():
        print(f"[ERR] No existe la atestación {args.attestation}", file=sys.stderr)
        return 2
    try:
        attestation = json.loads(args.attestation.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[ERR] Atestación ilegible: {exc}", file=sys.stderr)
        return 2

    print(">>> PROTOCOLO DE FALSIFICACIÓN L5 (DEVSECOPS TRUST ANCHOR) <<<\n")

    verdicts = [verify_self(attestation)]
    if verdicts[0]:
        verdicts.append(verify_source(attestation, args.commit))
        if args.skip_ledger:
            _skip("I3 LEDGER", "desactivado por --skip-ledger")
        else:
            verdicts.append(verify_ledger(attestation, args.db))
        if args.skip_anchor:
            _skip("I4 ANCHOR", "desactivado por --skip-anchor")
        else:
            verdicts.append(verify_anchor(attestation, args.anchor_dir, upgrade=not args.no_upgrade))

    if all(verdicts):
        print(f"\n{GREEN}[C5-REAL] CADENA DE CONFIANZA INTACTA.{RESET} El código auditado es el código atestado.")
        return 0
    print(f"\n{RED}[FATAL] CADENA DE CONFIANZA ROTA.{RESET} El estado actual diverge de lo que Bitcoin atestiguó.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
