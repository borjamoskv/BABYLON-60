# [C5-REAL] Exergy-Maximized
import asyncio
import json
import logging
import uuid
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from pathlib import Path

from babylon60.observability.prometheus_exporter import CortexPrometheusExporter

logger = logging.getLogger(__name__)

SNAPSHOT_DIR = Path("cortex_data/snapshots")
WAL_DIR = Path("cortex_data/wal")


@dataclass
class CortexState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    exergy: Decimal = field(default_factory=lambda: Decimal("1.0"))
    entropy: Decimal = field(default_factory=lambda: Decimal("0.0"))
    drift: Decimal = field(default_factory=lambda: Decimal("0.0"))
    cost: Decimal = field(default_factory=lambda: Decimal("0.0"))
    tick_count: int = 0

    def __post_init__(self):
        self.exergy = Decimal(str(self.exergy))
        self.entropy = Decimal(str(self.entropy))
        self.drift = Decimal(str(self.drift))
        self.cost = Decimal(str(self.cost))


class SnapshotManager:
    def __init__(self):
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)

    def create(self, state: CortexState) -> str:
        snapshot_id = f"snapshot_{state.tick_count:08d}"
        path = SNAPSHOT_DIR / f"{snapshot_id}.json"
        with path.open("w") as f:
            json.dump(asdict(state), f, default=str)
        return str(path)

    def get_latest(self) -> CortexState | None:
        files = sorted(SNAPSHOT_DIR.glob("snapshot_*.json"))
        if not files:
            return None
        with files[-1].open() as f:
            data = json.load(f)
        return CortexState(**data)


class WALManager:
    def __init__(self):
        WAL_DIR.mkdir(parents=True, exist_ok=True)

    def write_event(self, state: CortexState):
        path = WAL_DIR / f"{state.tick_count:08d}.log"
        with path.open("w") as f:
            json.dump(asdict(state), f, default=str)

    def truncate_before(self, tick_count: int):
        files = list(WAL_DIR.glob("*.log"))
        for fpath in files:
            basename = fpath.name
            tick = int(basename.split(".")[0])
            if tick <= tick_count:
                fpath.unlink()

    def replay_from(self, snapshot: CortexState | None) -> CortexState:
        start_tick = snapshot.tick_count if snapshot else -1
        files = sorted(WAL_DIR.glob("*.log"))

        current_state = snapshot or CortexState()
        replay_count = 0

        for fpath in files:
            basename = fpath.name
            tick = int(basename.split(".")[0])
            if tick > start_tick:
                with fpath.open() as f:
                    data = json.load(f)
                current_state = CortexState(**data)
                replay_count += 1

        if replay_count > 0:
            logger.info(
                "[WAL] Replayed %s frames from WAL. Recovered to tick %s.",
                replay_count,
                current_state.tick_count,
            )
        return current_state


class RecoveryManager:
    def __init__(self, snapshot_mgr: SnapshotManager, wal_mgr: WALManager):
        self.snapshot_mgr = snapshot_mgr
        self.wal_mgr = wal_mgr

    def recover(self, error: Exception) -> CortexState:
        logger.error("[RECOVERY] Initiating crash-consistent recovery due to: %s", error)

        latest_snap = self.snapshot_mgr.get_latest()
        if latest_snap:
            logger.info("[RECOVERY] Loaded base snapshot at tick %s.", latest_snap.tick_count)
        else:
            logger.critical("[RECOVERY] No snapshots available! Generating baseline state.")
            latest_snap = CortexState()

        # Replay WAL on top of snapshot
        recovered_state = self.wal_mgr.replay_from(latest_snap)
        return recovered_state


class CortexRuntime:
    def __init__(self):
        self.snapshot_mgr = SnapshotManager()
        self.wal_mgr = WALManager()
        self.recovery_mgr = RecoveryManager(self.snapshot_mgr, self.wal_mgr)
        self.exporter = CortexPrometheusExporter()
        self.running = False

    def load_state(self):
        logger.info("[RUNTIME] Checking disk for existing state...")
        # To simulate a cold start that picks up from crash automatically:
        try:
            self.state = self.recovery_mgr.recover(RuntimeError("Cold Boot / Crash Recovery"))
        except (ValueError, TypeError, KeyError, OSError, RuntimeError) as e:
            logger.warning("Failed to recover state: %s. Starting fresh.", e)
            self.state = CortexState()

    def execute_cycle(self, state: CortexState) -> CortexState:
        start_time = asyncio.get_event_loop().time()

        # Simulate execution physics
        state.tick_count += 1
        state.entropy += Decimal("0.05")
        state.exergy -= Decimal("0.005")
        state.cost += Decimal("0.02")

        # Simulate a random failure for testing auto-recovery if entropy gets too high
        if state.entropy > Decimal("1.0"):
            raise RuntimeError("Entropy Runaway Detected")

        self.exporter.track_latency(start_time)
        return state

    def persist(self, state: CortexState):
        # 1. Always append to WAL (Write-Ahead Log)
        self.wal_mgr.write_event(state)

        # 2. Snapshot every 10 ticks
        if state.tick_count % 10 == 0:
            snap_path = self.snapshot_mgr.create(state)
            logger.debug("[RUNTIME] Persisted snapshot: %s", snap_path)
            # Truncate WAL to avoid unbounded growth
            self.wal_mgr.truncate_before(state.tick_count)

    def emit_metrics(self):
        self.exporter.update_metrics(
            {
                "exergy": self.state.exergy,
                "entropy": self.state.entropy,
                "cost": self.state.cost,
                "drift": self.state.drift,
            }
        )

    async def run_forever(self, tick_delay: float = 1.0):
        self.load_state()
        self.running = True
        logger.info(
            "[RUNTIME] Cortex Kernel Started at Tick %s. Awaiting physical workload.",
            self.state.tick_count,
        )

        while self.running:
            try:
                self.state = self.execute_cycle(self.state)
                self.persist(self.state)
                self.emit_metrics()
                logger.info(
                    "[TICK %s] Exergy: %.3f | Entropy: %.3f",
                    self.state.tick_count,
                    self.state.exergy,
                    self.state.entropy,
                )
                await asyncio.sleep(tick_delay)

            except (ValueError, TypeError, KeyError, OSError, RuntimeError) as e:
                # In a normal crash, process dies. Here we catch internally to simulate rapid self-healing supervisor.
                self.state = self.recovery_mgr.recover(e)
                # Dampen entropy to break crash loop
                self.state.entropy *= Decimal("0.5")
                self.persist(self.state)  # Force WAL entry of the dampened state
                await asyncio.sleep(tick_delay)
