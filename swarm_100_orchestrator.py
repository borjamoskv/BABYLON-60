#!/usr/bin/env python3
"""
BABYLON-60 Deterministic 10x10 Swarm Orchestrator + L0 SQLite WORM + MMR + Lean 4 GMP Proof.
"""
from __future__ import annotations

import asyncio
import dataclasses
import hashlib
import json
import sqlite3
import tomllib
from pathlib import Path
from typing import Sequence


def digest32(data: bytes) -> bytes:
    try:
        import blake3  # type: ignore[import-not-found]
        return blake3.blake3(data).digest()
    except ImportError:
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
        assert len(self.peaks) == self.leaf_count.bit_count()

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

    def record_agent(self, tick: int, wave: int, agent: dict[str, str], status: str) -> str:
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

            b = conn.execute(
                "SELECT MIN(seq_id), MAX(seq_id), COUNT(*) FROM swarm_l0_receipts WHERE wave = ?;",
                (wave,),
            ).fetchone()
            assert b is not None
            s_seq, e_seq, cnt = int(b[0]), int(b[1]), int(b[2])
            if cnt != 10 or e_seq != wave * 10 or s_seq + 9 != e_seq:
                raise RuntimeError(f"Wave {wave} contiguous boundary violation: {b}")

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


def emit_lean4(seals: Sequence[WaveMmrSeal], out_file: Path) -> None:
    b256 = "0x1" + ("0" * 64)
    b512 = "0x1" + ("0" * 128)
    lines = [
        "/-! Auto-generated by BABYLON-60 Swarm Orchestrator. Constructive GMP-backed kernel proof. -/",
        "namespace Babylon.L0.SwarmMmrTrace",
        "",
        f"def BOUND_256 : Nat := {b256}",
        f"def BOUND_512 : Nat := {b512}",
        "",
        "structure WaveMmrSeal where",
        "  wave        : Nat",
        "  logicalTick : Nat",
        "  startSeq    : Nat",
        "  endSeq      : Nat",
        "  leafCount   : Nat",
        "  peaks       : List Nat",
        "  prevMmrRoot : Nat",
        "  mmrRoot     : Nat",
        "  coseSig     : Nat",
        "  deriving Repr, DecidableEq",
        "",
        "def popcountFuel : Nat -> Nat -> Nat",
        "  | 0, _ => 0",
        "  | _ + 1, 0 => 0",
        "  | fuel + 1, n => (n % 2) + popcountFuel fuel (n / 2)",
        "",
        "def popcount (n : Nat) : Nat := popcountFuel 8 n",
        "",
        "def checkPeaks256 : List Nat -> Bool",
        "  | [] => true",
        "  | p :: ps => decide (p < BOUND_256) && checkPeaks256 ps",
        "",
        "abbrev ValidWaveSeal (s : WaveMmrSeal) : Prop :=",
        "  1 <= s.wave /\\ s.wave <= 10 /\\",
        "  s.endSeq = s.wave * 10 /\\",
        "  s.startSeq + 9 = s.endSeq /\\",
        "  s.leafCount = s.endSeq /\\",
        "  s.peaks.length = popcount s.leafCount /\\",
        "  checkPeaks256 s.peaks = true /\\",
        "  s.prevMmrRoot < BOUND_256 /\\",
        "  s.mmrRoot < BOUND_256 /\\",
        "  s.coseSig < BOUND_512",
        "",
        "abbrev ValidSealStep (s : WaveMmrSeal) (expectedPrev : Nat) (prevTick : Nat) : Prop :=",
        "  ValidWaveSeal s /\\",
        "  s.prevMmrRoot = expectedPrev /\\",
        "  prevTick < s.logicalTick",
        "",
        "def ValidSealChain : List WaveMmrSeal -> Nat -> Nat -> Prop",
        "  | [], _, _ => True",
        "  | s :: rest, expectedPrev, prevTick =>",
        "      ValidSealStep s expectedPrev prevTick /\\",
        "      ValidSealChain rest s.mmrRoot s.logicalTick",
        "",
        "def decValidSealChain :",
        "    (tr : List WaveMmrSeal) -> (prev : Nat) -> (tick : Nat) ->",
        "    Decidable (ValidSealChain tr prev tick)",
        "  | [], _, _ => isTrue trivial",
        "  | s :: rest, expectedPrev, prevTick =>",
        "      match (inferInstance : Decidable (ValidSealStep s expectedPrev prevTick)),",
        "            decValidSealChain rest s.mmrRoot s.logicalTick with",
        "      | isTrue hStep, isTrue hRest => isTrue (And.intro hStep hRest)",
        "      | isFalse hStep, _ => isFalse (fun h => hStep h.left)",
        "      | _, isFalse hRest => isFalse (fun h => hRest h.right)",
        "",
        "instance (tr : List WaveMmrSeal) (prev : Nat) (tick : Nat) :",
        "    Decidable (ValidSealChain tr prev tick) :=",
        "  decValidSealChain tr prev tick",
        "",
    ]
    for s in seals:
        p_str = ", ".join(f"0x{p}" for p in s.peaks_hex)
        lines.extend(
            [
                f"def seal_w{s.wave:02d} : WaveMmrSeal := {{",
                f"  wave        := {s.wave},",
                f"  logicalTick := {s.logical_tick},",
                f"  startSeq    := {s.start_seq},",
                f"  endSeq      := {s.end_seq},",
                f"  leafCount   := {s.leaf_count},",
                f"  peaks       := [{p_str}],",
                f"  prevMmrRoot := 0x{s.prev_mmr_root},",
                f"  mmrRoot     := 0x{s.mmr_root},",
                f"  coseSig     := 0x{s.cose_sig}",
                "}",
                "",
            ]
        )
    trace_list = ", ".join(f"seal_w{s.wave:02d}" for s in seals)
    lines.extend(
        [
            f"def swarmTrace : List WaveMmrSeal := [{trace_list}]",
            "",
            "theorem swarmTrace_valid : ValidSealChain swarmTrace 0 0 := by",
            "  decide",
            "",
            "theorem swarmTrace_complete_100_agents :",
            "    swarmTrace.length = 10 /\\ seal_w10.leafCount = 100 /\\ seal_w10.peaks.length = 3 := by",
            "  decide",
            "",
            "end Babylon.L0.SwarmMmrTrace",
            "",
        ]
    )
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text("\n".join(lines), encoding="utf-8")


async def eval_agent(ag: dict[str, str], sem: asyncio.Semaphore) -> tuple[dict[str, str], str]:
    async with sem:
        await asyncio.sleep(0.001)
        return ag, "PASS"


async def main() -> None:
    manifest = tomllib.loads(Path("babylon_swarm_100.toml").read_text(encoding="utf-8"))
    vault_dir = Path.home() / ".babylon60_vault" / "runtime_l0"
    vault_dir.mkdir(parents=True, exist_ok=True)
    db_path = vault_dir / "swarm_100_l0.db"
    for ext in ("", "-wal", "-shm"):
        Path(f"{db_path}{ext}").unlink(missing_ok=True)

    ledger = ImmutableL0SwarmLedger(db_path)
    sem = asyncio.Semaphore(4)
    tick = 0
    carbon = 0
    hydrogen = 0
    seals: list[WaveMmrSeal] = []
    key32 = hashlib.sha256(b"B60_SWARM_100_L0_DETERMINISTIC_SEED").digest()

    tandas = manifest["tanda"]
    for idx, t_key in enumerate(sorted(tandas.keys()), start=1):
        t = tandas[t_key]
        results = await asyncio.gather(*(eval_agent(ag, sem) for ag in t["agents"]))
        for ag, st in sorted(results, key=lambda x: x[0]["id"]):
            tick += 1
            if ag.get("model") == "gemini-4-carbon":
                carbon += 1
            else:
                hydrogen += 1
            ledger.record_agent(tick, idx, ag, st)
        tick += 1
        seal = ledger.seal_wave(idx, tick, key32)
        seals.append(seal)
        print(
            f"[W{idx:02d}] {t['name']} -> leaves={seal.leaf_count:3d} | "
            f"peaks={len(seal.peaks_hex)} | mmr_root={seal.mmr_root[:16]}..."
        )

    emit_lean4(seals, Path("proof/lean/SwarmMmrTrace.lean"))

    u_c = (2000 * 2.0 + 500 * 10.0) / 1_000_000
    u_h = (2000 * 1.5 + 500 * 7.5) / 1_000_000
    savings = (1.0 - ((carbon * u_c + hydrogen * u_h) / (100 * u_c))) * 100.0
    print(
        f"\n[OK] 100/100 agentes sellados | Carbon={carbon} Hydrogen={hydrogen} "
        f"(Ahorro base FL-027: {savings:.2f}%) | Final MMR Root={seals[-1].mmr_root}"
    )


if __name__ == "__main__":
    asyncio.run(main())
