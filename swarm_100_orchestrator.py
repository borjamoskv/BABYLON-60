#!/usr/bin/env python3
"""
BABYLON-60 Deterministic 10x10 MMR Specification Harness + L0 SQLite WORM + Lean 4 BitVec Proof.

Scope (SHARUR-3600 / .babylon60rules):
  Compiles the declarative 10x10 cohort manifest (`babylon_swarm_100.toml`) into a
  deterministic Merkle Mountain Range (MMR) chain over SQLite WAL (`synchronous = FULL`)
  and emits a zero-GMP fixed-width (`BitVec 64` / `BitVec 32`) Lean 4 proof artifact
  with constructive non-vacuity witness (`inv_inhabited`).
  Does NOT claim or simulate live LLM execution (`MODEL_SPEC_SEALED`).
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import sqlite3
import tempfile
import tomllib
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).absolute().parent
DEFAULT_MANIFEST = Path(__file__).absolute().parent / "babylon_swarm_100.toml"
DEFAULT_LEAN_OUT = ROOT / "proof" / "lean" / "SwarmMmrTrace.lean"


def digest32(data: bytes) -> bytes:
    """Deterministic SHA-256 digest so emitted Lean traces are invariant across Python envs."""
    return hashlib.sha256(data).digest()


@dataclasses.dataclass(frozen=True)
class WaveMmrSeal:
    wave: int
    logical_tick: int
    start_seq: int
    end_seq: int
    leaf_count: int
    peaks_hex: tuple[str, ...]
    prev_mmr_root: str
    mmr_root: str
    cose_sig: str


class MmrAccumulator:
    def __init__(self) -> None:
        self.leaf_count = 0
        self.peaks: list[tuple[int, bytes]] = []

    def append_leaf(self, seq_id: int, receipt_hex: str) -> None:
        cur = digest32(b"\x00" + seq_id.to_bytes(8, "big") + bytes.fromhex(receipt_hex))
        h = 0
        while self.peaks and self.peaks[-1][0] == h:
            _, left = self.peaks.pop()
            cur = digest32(b"\x01" + left + cur)
            h += 1
        self.peaks.append((h, cur))
        self.leaf_count += 1
        if len(self.peaks) != self.leaf_count.bit_count():
            raise RuntimeError("MMR peak count diverged from binary popcount")

    def root(self) -> bytes:
        acc = self.peaks[-1][1]
        n_be = self.leaf_count.to_bytes(8, "big")
        for _, left in reversed(self.peaks[:-1]):
            acc = digest32(b"\x02" + n_be + left + acc)
        return acc


class ImmutableL0SwarmLedger:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS swarm_l0_receipts (
                    seq_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    logical_tick INTEGER NOT NULL UNIQUE,
                    wave INTEGER NOT NULL CHECK (wave BETWEEN 1 AND 10),
                    agent_id TEXT NOT NULL UNIQUE,
                    model_id TEXT NOT NULL,
                    target TEXT NOT NULL,
                    status TEXT NOT NULL,
                    prev_receipt_hash TEXT NOT NULL CHECK (length(prev_receipt_hash) = 64),
                    receipt_hash TEXT NOT NULL UNIQUE CHECK (length(receipt_hash) = 64)
                );
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_receipts_no_update
                BEFORE UPDATE ON swarm_l0_receipts
                BEGIN SELECT RAISE(ABORT, 'L0_LEDGER_IMMUTABLE_VIOLATION'); END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_receipts_no_delete
                BEFORE DELETE ON swarm_l0_receipts
                BEGIN SELECT RAISE(ABORT, 'L0_LEDGER_IMMUTABLE_VIOLATION'); END;
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS swarm_wave_mmr_seals (
                    wave INTEGER PRIMARY KEY CHECK (wave BETWEEN 1 AND 10),
                    logical_tick INTEGER NOT NULL UNIQUE,
                    start_seq INTEGER NOT NULL,
                    end_seq INTEGER NOT NULL,
                    leaf_count INTEGER NOT NULL,
                    peaks_json TEXT NOT NULL,
                    prev_mmr_root TEXT NOT NULL CHECK (length(prev_mmr_root) = 64),
                    mmr_root TEXT NOT NULL UNIQUE CHECK (length(mmr_root) = 64),
                    cose_sig TEXT NOT NULL CHECK (length(cose_sig) = 128)
                );
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_seals_no_update
                BEFORE UPDATE ON swarm_wave_mmr_seals
                BEGIN SELECT RAISE(ABORT, 'L0_LEDGER_IMMUTABLE_VIOLATION'); END;
                """
            )
            conn.execute(
                """
                CREATE TRIGGER IF NOT EXISTS trg_seals_no_delete
                BEFORE DELETE ON swarm_wave_mmr_seals
                BEGIN SELECT RAISE(ABORT, 'L0_LEDGER_IMMUTABLE_VIOLATION'); END;
                """
            )
            conn.execute("COMMIT;")
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

    def _conn(self) -> sqlite3.Connection:
        c = sqlite3.connect(self.db_path, isolation_level=None, timeout=30.0)
        c.execute("PRAGMA journal_mode = WAL;")
        c.execute("PRAGMA synchronous = FULL;")
        return c

    def record_spec_entry(self, tick: int, wave: int, agent: dict[str, str], status: str) -> str:
        model_id = agent.get("model", "gemini-4-hydrogen")
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            row = conn.execute(
                "SELECT seq_id, receipt_hash FROM swarm_l0_receipts ORDER BY seq_id DESC LIMIT 1;"
            ).fetchone()
            seq = 1 if row is None else int(row[0]) + 1
            prev_h = "0" * 64 if row is None else str(row[1])
            raw = f"{seq}|{tick}|{wave}|{agent['id']}|{model_id}|{agent['target']}|{status}|{prev_h}"
            r_hash = digest32(raw.encode("utf-8")).hex()
            conn.execute(
                "INSERT INTO swarm_l0_receipts (logical_tick, wave, agent_id, model_id, target, status, prev_receipt_hash, receipt_hash) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                (tick, wave, agent["id"], model_id, agent["target"], status, prev_h, r_hash),
            )
            conn.execute("COMMIT;")
            return r_hash
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()

    def seal_wave(self, wave: int, tick: int, key32: bytes) -> WaveMmrSeal:
        conn = self._conn()
        try:
            conn.execute("BEGIN IMMEDIATE;")
            if wave == 1:
                prev_root = "0" * 64
            else:
                prev_row = conn.execute(
                    "SELECT mmr_root FROM swarm_wave_mmr_seals WHERE wave = ?;", (wave - 1,)
                ).fetchone()
                if prev_row is None:
                    raise RuntimeError(f"Missing previous MMR seal for wave {wave - 1}")
                prev_root = str(prev_row[0])

            bounds = conn.execute(
                "SELECT MIN(seq_id), MAX(seq_id), COUNT(*) FROM swarm_l0_receipts WHERE wave = ?;",
                (wave,),
            ).fetchone()
            if bounds is None:
                raise RuntimeError(f"Empty wave {wave}")
            s_seq, e_seq, cnt = int(bounds[0]), int(bounds[1]), int(bounds[2])
            if cnt != 10 or e_seq != wave * 10 or s_seq + 9 != e_seq:
                raise RuntimeError(f"Wave {wave} contiguous boundary violation: {bounds}")

            mmr = MmrAccumulator()
            for seq_id, r_hash in conn.execute(
                "SELECT seq_id, receipt_hash FROM swarm_l0_receipts WHERE seq_id <= ? ORDER BY seq_id ASC;",
                (e_seq,),
            ).fetchall():
                mmr.append_leaf(int(seq_id), str(r_hash))

            peaks_hex = tuple(h.hex() for _, h in mmr.peaks)
            root_hex = mmr.root().hex()
            tbs = f"COSE_B60_MMR_V1|{wave}|{tick}|{s_seq}|{e_seq}|{mmr.leaf_count}|{prev_root}|{root_hex}".encode()
            sig_hex = hashlib.blake2b(tbs, key=key32, digest_size=64).hexdigest()

            seal = WaveMmrSeal(
                wave=wave,
                logical_tick=tick,
                start_seq=s_seq,
                end_seq=e_seq,
                leaf_count=mmr.leaf_count,
                peaks_hex=peaks_hex,
                prev_mmr_root=prev_root,
                mmr_root=root_hex,
                cose_sig=sig_hex,
            )
            conn.execute(
                "INSERT INTO swarm_wave_mmr_seals VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (
                    seal.wave,
                    seal.logical_tick,
                    seal.start_seq,
                    seal.end_seq,
                    seal.leaf_count,
                    json.dumps(seal.peaks_hex, separators=(",", ":")),
                    seal.prev_mmr_root,
                    seal.mmr_root,
                    seal.cose_sig,
                ),
            )
            conn.execute("COMMIT;")
            return seal
        except Exception:
            conn.execute("ROLLBACK;")
            raise
        finally:
            conn.close()


def _fmt_digest256(hex64: str) -> str:
    if len(hex64) != 64:
        raise ValueError(f"Expected 64 hex chars, got {len(hex64)}")
    limbs = [f"0x{hex64[i:i + 16]}#64" for i in range(0, 64, 16)]
    return f"⟨{', '.join(limbs)}⟩"


def _fmt_sig512(hex128: str) -> str:
    if len(hex128) != 128:
        raise ValueError(f"Expected 128 hex chars, got {len(hex128)}")
    return f"⟨{_fmt_digest256(hex128[:64])}, {_fmt_digest256(hex128[64:])}⟩"


def emit_lean4_bitvec(seals: Sequence[WaveMmrSeal], out_file: Path) -> None:
    """Emit zero-GMP fixed-width BitVec 64/32 Lean 4 proof with inv_inhabited witness."""
    lines = [
        "/-! Auto-generated by BABYLON-60 MMR Specification Harness.",
        "    Zero-GMP fixed-width BitVec 64/32 proof (INV_C5_BITVEC_SOUNDNESS & INV_C5_NON_VACUITY_WITNESS). -/",
        "set_option warningAsError true",
        "",
        "namespace Babylon.L0.SwarmMmrTrace",
        "",
        "structure Digest256 where",
        "  w0 : BitVec 64",
        "  w1 : BitVec 64",
        "  w2 : BitVec 64",
        "  w3 : BitVec 64",
        "  deriving Repr, DecidableEq",
        "",
        "def Digest256.zero : Digest256 := ⟨0#64, 0#64, 0#64, 0#64⟩",
        "",
        "structure Sig512 where",
        "  lo : Digest256",
        "  hi : Digest256",
        "  deriving Repr, DecidableEq",
        "",
        "structure WaveMmrSeal where",
        "  wave        : BitVec 32",
        "  logicalTick : BitVec 64",
        "  startSeq    : BitVec 32",
        "  endSeq      : BitVec 32",
        "  leafCount   : BitVec 32",
        "  peaks       : List Digest256",
        "  prevMmrRoot : Digest256",
        "  mmrRoot     : Digest256",
        "  coseSig     : Sig512",
        "  deriving Repr, DecidableEq",
        "",
        "def popcount8 (n : BitVec 32) : BitVec 32 :=",
        "  (n &&& 1#32) +",
        "  ((n >>> 1) &&& 1#32) +",
        "  ((n >>> 2) &&& 1#32) +",
        "  ((n >>> 3) &&& 1#32) +",
        "  ((n >>> 4) &&& 1#32) +",
        "  ((n >>> 5) &&& 1#32) +",
        "  ((n >>> 6) &&& 1#32) +",
        "  ((n >>> 7) &&& 1#32)",
        "",
        "abbrev ValidWaveSeal (s : WaveMmrSeal) : Prop :=",
        "  1#32 <= s.wave /\\ s.wave <= 10#32 /\\",
        "  s.endSeq = s.wave * 10#32 /\\",
        "  s.startSeq + 9#32 = s.endSeq /\\",
        "  s.leafCount = s.endSeq /\\",
        "  BitVec.ofNat 32 s.peaks.length = popcount8 s.leafCount /\\",
        "  s.mmrRoot ≠ Digest256.zero",
        "",
        "abbrev ValidSealStep (s : WaveMmrSeal) (expectedPrev : Digest256) (prevTick : BitVec 64) : Prop :=",
        "  ValidWaveSeal s /\\",
        "  s.prevMmrRoot = expectedPrev /\\",
        "  prevTick < s.logicalTick",
        "",
        "def ValidSealChain : List WaveMmrSeal -> Digest256 -> BitVec 64 -> Prop",
        "  | [], _, _ => True",
        "  | s :: rest, expectedPrev, prevTick =>",
        "      ValidSealStep s expectedPrev prevTick /\\",
        "      ValidSealChain rest s.mmrRoot s.logicalTick",
        "",
        "def decValidSealChain :",
        "    (tr : List WaveMmrSeal) -> (prev : Digest256) -> (tick : BitVec 64) ->",
        "    Decidable (ValidSealChain tr prev tick)",
        "  | [], _, _ => isTrue trivial",
        "  | s :: rest, expectedPrev, prevTick =>",
        "      match (inferInstance : Decidable (ValidSealStep s expectedPrev prevTick)),",
        "            decValidSealChain rest s.mmrRoot s.logicalTick with",
        "      | isTrue hStep, isTrue hRest => isTrue (And.intro hStep hRest)",
        "      | isFalse hStep, _ => isFalse (fun h => hStep h.left)",
        "      | _, isFalse hRest => isFalse (fun h => hRest h.right)",
        "",
        "instance (tr : List WaveMmrSeal) (prev : Digest256) (tick : BitVec 64) :",
        "    Decidable (ValidSealChain tr prev tick) :=",
        "  decValidSealChain tr prev tick",
        "",
    ]
    for s in seals:
        p_str = ", ".join(_fmt_digest256(p) for p in s.peaks_hex)
        lines.extend(
            [
                f"def seal_w{s.wave:02d} : WaveMmrSeal := {{",
                f"  wave        := {s.wave}#32,",
                f"  logicalTick := {s.logical_tick}#64,",
                f"  startSeq    := {s.start_seq}#32,",
                f"  endSeq      := {s.end_seq}#32,",
                f"  leafCount   := {s.leaf_count}#32,",
                f"  peaks       := [{p_str}],",
                f"  prevMmrRoot := {_fmt_digest256(s.prev_mmr_root)},",
                f"  mmrRoot     := {_fmt_digest256(s.mmr_root)},",
                f"  coseSig     := {_fmt_sig512(s.cose_sig)}",
                "}",
                "",
            ]
        )
    trace_list = ", ".join(f"seal_w{s.wave:02d}" for s in seals)
    lines.extend(
        [
            f"def swarmTrace : List WaveMmrSeal := [{trace_list}]",
            "",
            "theorem swarmTrace_valid : ValidSealChain swarmTrace Digest256.zero 0#64 := by",
            "  decide",
            "",
            "theorem swarmTrace_complete_100_specs :",
            "    swarmTrace.length = 10 /\\ seal_w10.leafCount = 100#32 /\\ seal_w10.peaks.length = 3 := by",
            "  decide",
            "",
            "theorem inv_inhabited :",
            "    ∃ tr : List WaveMmrSeal, tr ≠ [] /\\ ValidSealChain tr Digest256.zero 0#64 :=",
            "  ⟨swarmTrace, by decide, swarmTrace_valid⟩",
            "",
            "/-- info: 'Babylon.L0.SwarmMmrTrace.swarmTrace_valid' depends on axioms: [propext, Quot.sound] -/",
            "#guard_msgs in",
            "#print axioms swarmTrace_valid",
            "",
            "/-- info: 'Babylon.L0.SwarmMmrTrace.inv_inhabited' depends on axioms: [propext, Quot.sound] -/",
            "#guard_msgs in",
            "#print axioms inv_inhabited",
            "",
            "end Babylon.L0.SwarmMmrTrace",
            "",
        ]
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")


def inspect_manifest(manifest: dict[str, object], agent_filter: str | None = None) -> None:
    tandas = manifest["tanda"]
    assert isinstance(tandas, dict)
    for idx, t_key in enumerate(sorted(tandas.keys()), start=1):
        t = tandas[t_key]
        print(f"TANDA {idx:02d}: {t['name']} — {t['goal']}")
        for ag in t["agents"]:
            if agent_filter and ag["id"] != agent_filter:
                continue
            print(f"  [{ag['id']}] ({ag['model']}) {ag['name']} -> {ag['target']}")


def compile_spec_trace(manifest_path: Path, lean_out: Path) -> list[WaveMmrSeal]:
    manifest = tomllib.loads(manifest_path.read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory(prefix="b60-mmr-spec-") as tmp_dir:
        db_path = Path(tmp_dir) / "swarm_100_spec.db"
        ledger = ImmutableL0SwarmLedger(db_path)
        tick = 0
        seals: list[WaveMmrSeal] = []
        key32 = hashlib.sha256(b"B60_SWARM_100_L0_DETERMINISTIC_SEED").digest()

        tandas = manifest["tanda"]
        for idx, t_key in enumerate(sorted(tandas.keys()), start=1):
            t = tandas[t_key]
            for ag in sorted(t["agents"], key=lambda x: x["id"]):
                tick += 1
                ledger.record_spec_entry(tick, idx, ag, "MODEL_SPEC_SEALED")
            tick += 1
            seal = ledger.seal_wave(idx, tick, key32)
            seals.append(seal)
        for ext in ("", "-wal", "-shm"):
            Path(f"{db_path}{ext}").unlink(missing_ok=True)

    emit_lean4_bitvec(seals, lean_out)
    return seals


def main() -> None:
    parser = argparse.ArgumentParser(description="Compile deterministic 10x10 MMR specification trace.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--lean-out", type=Path, default=DEFAULT_LEAN_OUT)
    parser.add_argument("--plan", action="store_true", help="Inspect cohort manifest without writing Lean trace")
    parser.add_argument("--agent", type=str, default=None, help="Inspect a single agent specification by ID")
    args = parser.parse_args()

    if args.plan or args.agent:
        manifest = tomllib.loads(args.manifest.read_text(encoding="utf-8"))
        inspect_manifest(manifest, args.agent)
        return

    seals = compile_spec_trace(args.manifest, args.lean_out)
    print(
        f"[MODEL_SPEC_SEALED] 100 cohort entries sealed across {len(seals)} waves "
        f"(no live agent execution) | Final MMR Root={seals[-1].mmr_root}"
    )


if __name__ == "__main__":
    main()
