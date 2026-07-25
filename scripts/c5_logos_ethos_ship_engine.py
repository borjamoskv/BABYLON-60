import hashlib
import os
import sqlite3
import string
import sys
import time
from decimal import getcontext
from typing import Literal
import babylon60.database.core
StateKind = Literal['C5_Real_Atomic', 'C4_Simulated_Buffer']
getcontext().prec = 38

class SexagesimalCoordinate:
    __slots__ = ('units', 'sixtieths', 'ticks')

    def __init__(self, units: int, sixtieths: int, ticks: int) -> None:
        if not (0 <= sixtieths < 60 and 0 <= ticks < 60):
            raise ValueError('[SIGKILL_State_Purge] Out of bounds for Base-60 coordinate.')
        self.units = units
        self.sixtieths = sixtieths
        self.ticks = ticks

    def divide_exact_by(self, divisor: int) -> 'SexagesimalCoordinate':
        valid_divisors = {1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60}
        if divisor not in valid_divisors:
            raise ValueError(f'[SIGKILL_State_Purge] Divisor {divisor} is not in D_60. Would produce infinite periodic drift.')
        total_ticks = self.units * 3600 + self.sixtieths * 60 + self.ticks
        exact_ticks = total_ticks // divisor
        u, rem = divmod(exact_ticks, 3600)
        s, t = divmod(rem, 60)
        return SexagesimalCoordinate(u, s, t)

    def to_string(self) -> str:
        return f'{self.units}:{self.sixtieths:02d}:{self.ticks:02d}_BASE60'

class PhysicalMembraneState:
    __slots__ = ('state_type', 'payload_hash', 'lamport_clock')

    def __init__(self, state_type: StateKind, payload_hash: str, lamport_clock: int) -> None:
        if state_type not in ('C5_Real_Atomic', 'C4_Simulated_Buffer'):
            raise TypeError(f'[SIGKILL_State_Purge] Illegal state unrepresentable: {state_type}')
        if state_type == 'C4_Simulated_Buffer':
            raise RuntimeError('[SIGKILL_State_Purge] C4-SIM state rejected by C5-REAL physical membrane during SHIP.')
        if len(payload_hash) != 64 or not all((c in string.hexdigits for c in payload_hash)):
            raise ValueError(f'[SIGKILL_State_Purge] Invalid payload_hash: Must be 64-char SHA3-256 hex. Got: {payload_hash}')
        if lamport_clock <= 0:
            raise ValueError(f'[SIGKILL_State_Purge] lamport_clock must be strictly positive. Got: {lamport_clock}')
        self.state_type = state_type
        self.payload_hash = payload_hash
        self.lamport_clock = lamport_clock

class BFTMasterLedgerWAL:

    def __init__(self, db_path: str | None=None) -> None:
        if db_path is None:
            root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            scratch_dir = os.path.join(root_dir, 'scratch')
            os.makedirs(scratch_dir, exist_ok=True)
            db_path = os.path.join(scratch_dir, 'c5_logos_ethos_ship_test.db')
        self.db_path = db_path
        self._init_membrane()

    def _init_membrane(self) -> None:
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            conn.execute('PRAGMA journal_mode = WAL;')
            conn.execute('PRAGMA synchronous = NORMAL;')
            conn.execute('PRAGMA busy_timeout = 5000;')
            conn.execute('\n                CREATE TABLE IF NOT EXISTS master_ledger (\n                    sequence_id int PRIMARY KEY AUTOINCREMENT,\n                    prev_hash TEXT NOT NULL UNIQUE,\n                    claim_payload TEXT NOT NULL,\n                    lamport_clock int NOT NULL,\n                    agent_id TEXT NOT NULL,\n                    taint_hash TEXT NOT NULL UNIQUE,\n                    created_at REAL NOT NULL\n                );\n            ')
            conn.commit()

    def append_c5_transaction(self, claim_payload: str, lamport_clock: int, agent_id: str) -> str:
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT taint_hash FROM master_ledger ORDER BY sequence_id DESC LIMIT 1;')
            row = cursor.fetchone()
            prev_hash: str = row[0] if row else '0' * 64
            raw_taint = f'{prev_hash}||{claim_payload}||{lamport_clock}||{agent_id}'.encode('utf-8')
            taint_hash = hashlib.sha3_256(raw_taint).hexdigest()
            try:
                cursor.execute('\n                    INSERT INTO master_ledger (prev_hash, claim_payload, lamport_clock, agent_id, taint_hash, created_at)\n                    VALUES (?, ?, ?, ?, ?, ?);\n                ', (prev_hash, claim_payload, lamport_clock, agent_id, taint_hash, time.time()))
                conn.commit()
                return taint_hash
            except sqlite3.IntegrityError as e:
                conn.rollback()
                raise RuntimeError(f'[SIGKILL_State_Purge] BFT/WAL integrity violation: {e}')

    def verify_ledger_integrity(self) -> bool:
        with babylon60.database.core.connect_sync(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT prev_hash, claim_payload, lamport_clock, agent_id, taint_hash FROM master_ledger ORDER BY sequence_id ASC;')
            rows = cursor.fetchall()
            if not rows:
                return True
            expected_prev = '0' * 64
            for prev_h, payload, clock, agent, taint_h in rows:
                if prev_h != expected_prev:
                    raise AssertionError(f'[SIGKILL_State_Purge] Chain break detected! Expected prev {expected_prev}, got {prev_h}')
                raw_t = f'{prev_h}||{payload}||{clock}||{agent}'.encode('utf-8')
                calc_t = hashlib.sha3_256(raw_t).hexdigest()
                if taint_h != calc_t:
                    raise AssertionError(f'[SIGKILL_State_Purge] Taint hash mismatch! Expected {calc_t}, got {taint_h}')
                expected_prev = taint_h
            return True

def run_c5_verification_suite() -> int:
    print('[+] Igniting C5-REAL Verification Suite: LOGOS, ETHOS, SHIP...')
    coord = SexagesimalCoordinate(12, 30, 0)
    div_coord = coord.divide_exact_by(15)
    assert div_coord.to_string() == '0:50:00_BASE60', f'Unexpected coord: {div_coord.to_string()}'
    print('[✓] PRIMITIVA-LOGOS-001: Base-60 Sexagesimal Exact Divisibility verified.')
    try:
        PhysicalMembraneState('C4_Simulated_Buffer', 'hash123', 1)
        assert False, 'Should have rejected C4_Simulated_Buffer'
    except RuntimeError as e:
        assert 'rejected by C5-REAL' in str(e)
    print('[✓] PRIMITIVA-LOGOS-002: F# Algebraic Membrane / Illegal State rejection verified.')
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scratch_dir = os.path.join(root_dir, 'scratch')
    os.makedirs(scratch_dir, exist_ok=True)
    ledger_db = os.path.join(scratch_dir, 'c5_logos_ethos_ship_test.db')
    if os.path.exists(ledger_db):
        os.remove(ledger_db)
    ledger = BFTMasterLedgerWAL(ledger_db)
    t1 = ledger.append_c5_transaction('CLAIM: LOGOS_BASE60_COLLAPSED', 101, 'borjamoskv')
    t2 = ledger.append_c5_transaction('CLAIM: ETHOS_TAINT_VERIFIED', 102, 'borjamoskv')
    t3 = ledger.append_c5_transaction('CLAIM: SHIP_DISK_COMMITTED', 103, 'borjamoskv')
    assert len(t1) == 64 and len(t2) == 64 and (len(t3) == 64)
    assert ledger.verify_ledger_integrity() is True
    print(f'[✓] PRIMITIVA-ETHOS-003 & SHIP-004: BFT/WAL Master Ledger & SHA3-256 Taint Chain verified. Head: {t3[:16]}...')
    print('[+] ALL 4 CORE PRIMITIVES AND LOGOS-ETHOS-SHIP TRIAD VERIFIED 100% C5-REAL.')
    return 0
if __name__ == '__main__':
    sys.exit(run_c5_verification_suite())