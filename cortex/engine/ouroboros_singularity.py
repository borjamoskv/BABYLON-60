import time
import hashlib
import sqlite3
import dataclasses
from typing import Final, Callable, TypeVar
from decimal import Decimal

DB_PATH: Final[str] = "nexus_anchors.db"
T = TypeVar("T")


@dataclasses.dataclass(frozen=True)
class OuroborosState:
    cycle_id: int
    exergy_net: Decimal
    falsified: bool
    causal_hash: str


def init_ouroboros_ledger() -> None:
    with sqlite3.connect(DB_PATH, timeout=5.0) as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute(
            "\n            CREATE TABLE IF NOT EXISTS ouroboros_100 (\n                causal_hash TEXT PRIMARY KEY,\n                cycle_id INTEGER,\n                exergy_net REAL,\n                falsified BOOLEAN\n            )\n        "
        )


def execute_apex_100(
    optimization_fn: Callable[[], Decimal], falsification_fn: Callable[[Decimal], bool]
) -> OuroborosState:
    init_ouroboros_ledger()
    exergy = optimization_fn()
    is_falsified = falsification_fn(exergy)
    if is_falsified:
        exergy_net = Decimal("0.0")
    else:
        exergy_net = exergy
    cycle_id = int(time.time() * 1000)
    raw_causal = f"{cycle_id}|{exergy_net}|{is_falsified}".encode("utf-8")
    causal_hash = hashlib.blake2b(raw_causal, digest_size=16).hexdigest()
    state = OuroborosState(
        cycle_id=cycle_id,
        exergy_net=exergy_net,
        falsified=is_falsified,
        causal_hash=causal_hash,
    )
    with sqlite3.connect(DB_PATH, timeout=5.0) as conn:
        conn.execute(
            "\n            INSERT INTO ouroboros_100 (causal_hash, cycle_id, exergy_net, falsified)\n            VALUES (?, ?, ?, ?)\n        ",
            (
                state.causal_hash,
                state.cycle_id,
                float(state.exergy_net),
                state.falsified,
            ),
        )
    return state


if __name__ == "__main__":

    def mock_optimize() -> Decimal:
        return Decimal("10000.0")

    def mock_falsify(val: Decimal) -> bool:
        return val < Decimal("0.0")

    final_state = execute_apex_100(mock_optimize, mock_falsify)
    print(
        f"APEX-100 COLAPSO: Exergía Neta={final_state.exergy_net}, Falsificado={final_state.falsified}, Hash={final_state.causal_hash}"
    )
