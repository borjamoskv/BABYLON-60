"""
bft_orchestrator — Byzantine Fault-Tolerant Consensus Orchestrator (C5-REAL / Ω17 / Ω26).

This module implements a 3-node virtual BFT consensus layer that:
  - Routes action tuples (domain, primitive, modifier) through an asyncio Queue.
  - Executes each tuple in parallel across N BFT replica nodes backed by the
    Rust `strike_rs` extension (StateVector, CognitiveChainVector, TTSHarnessState).
  - Reaches simple-majority consensus on the resulting SHA3-256 state hash.
  - Commits accepted transitions to an immutable SQLite WAL ledger with
    append-only triggers (Ω11 / R10).
  - Detects and heals Byzantine outlier nodes by syncing state from a majority leader.

Rule references: R10 (persistence), Ω11 (immutability), Ω17 (type annotations),
                 Ω24 (SHA3-256 integrity), Ω26 (typed exceptions).
"""

import asyncio
import sqlite3
import hashlib
import time
try:
    import strike_rs  # type: ignore[import-untyped]
except ImportError:
    strike_rs = None

__all__ = [
    "BFTNode",
    "BFTOrchestrator",
    "init_bft_database",
    "DB_PATH",
    "strike_rs",
]

# DB Concurrency & Persist Configurations (R10)
DB_PATH = "cortex_bft_ledger.db"

def init_bft_database() -> None:
    """Initializes SQLite Master Ledger with WAL, busy_timeout, and write protection triggers (R10, Ω11)."""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    # Enable WAL mode and set busy_timeout
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    
    # Create ledger table enforcing UNIQUE(prev_hash)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS bft_ledger (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        step_index INTEGER NOT NULL,
        domain INTEGER NOT NULL,
        primitive INTEGER NOT NULL,
        modifier INTEGER NOT NULL,
        prev_hash TEXT NOT NULL UNIQUE,
        current_hash TEXT NOT NULL,
        cortex_taint TEXT NOT NULL
    );
    """)
    
    # Create triggers to block UPDATE and DELETE operations via RAISE(ABORT) (Ω11)
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_ledger_update
    BEFORE UPDATE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'Ledger updates are forbidden. Immutability violation.');
    END;
    """)
    
    conn.execute("""
    CREATE TRIGGER IF NOT EXISTS prevent_ledger_delete
    BEFORE DELETE ON bft_ledger
    BEGIN
        SELECT RAISE(ABORT, 'Ledger deletions are forbidden. Immutability violation.');
    END;
    """)
    
    conn.commit()
    conn.close()

class BFTNode:
    """Represents a virtual Byzantine replica node holding its own Rust-backed states."""
    def __init__(self, node_id: int) -> None:
        self.node_id = node_id
        self.state_vector = strike_rs.StateVector()
        self.cognitive_chain_vector = strike_rs.CognitiveChainVector()
        self.tts_harness_state = strike_rs.TTSHarnessState()
        self.arm64_re_matrix = strike_rs.Arm64ReMatrix()
        self.is_healthy = True

    def compute_state_hash(self) -> str:
        """Computes the state hash of the node using SHA3-256 for cryptographic integrity (Ω24)."""
        # Read attributes from the Rust PyO3 classes
        state_data = (
            f"states:{self.state_vector.states},"
            f"covariance:{self.state_vector.covariance},"
            f"innovation:{self.state_vector.innovation},"
            f"homeostasis_energy:{self.cognitive_chain_vector.homeostasis_energy},"
            f"prediction_error:{self.cognitive_chain_vector.prediction_error},"
            f"attention_weight:{self.cognitive_chain_vector.attention_weight},"
            f"action_torque:{self.cognitive_chain_vector.action_torque},"
            f"language_entropy:{self.cognitive_chain_vector.language_entropy},"
            f"mcts_budget:{self.tts_harness_state.mcts_budget_tokens},"
            f"latent_value:{self.tts_harness_state.latent_value},"
            f"kv_eff:{self.tts_harness_state.kv_cache_efficiency},"
            f"arm64_pac:{self.arm64_re_matrix.pac_bypass_entropy},"
            f"arm64_dyld:{self.arm64_re_matrix.dyld_cache_hit_rate}"
        )
        return hashlib.sha3_256(state_data.encode("utf-8")).hexdigest()

    def sync_from(self, source_node: 'BFTNode') -> None:
        """Synchronizes the state from a healthy node to resolve a Byzantine fault."""
        # Synchronize StateVector
        self.state_vector.states = list(source_node.state_vector.states)
        self.state_vector.covariance = [list(row) for row in source_node.state_vector.covariance]
        self.state_vector.innovation = list(source_node.state_vector.innovation)
        self.state_vector.norm_error = source_node.state_vector.norm_error
        self.state_vector.execution_count = source_node.state_vector.execution_count
        
        # Synchronize CognitiveChainVector
        self.cognitive_chain_vector.homeostasis_energy = source_node.cognitive_chain_vector.homeostasis_energy
        self.cognitive_chain_vector.prediction_error = source_node.cognitive_chain_vector.prediction_error
        self.cognitive_chain_vector.attention_weight = source_node.cognitive_chain_vector.attention_weight
        self.cognitive_chain_vector.action_torque = source_node.cognitive_chain_vector.action_torque
        self.cognitive_chain_vector.language_entropy = source_node.cognitive_chain_vector.language_entropy
        self.cognitive_chain_vector.execution_count = source_node.cognitive_chain_vector.execution_count
        
        # Synchronize TTSHarnessState
        self.tts_harness_state.mcts_budget_tokens = source_node.tts_harness_state.mcts_budget_tokens
        self.tts_harness_state.latent_value = source_node.tts_harness_state.latent_value
        self.tts_harness_state.harness_score = source_node.tts_harness_state.harness_score
        self.tts_harness_state.kv_cache_efficiency = source_node.tts_harness_state.kv_cache_efficiency
        self.tts_harness_state.pruning_rate = source_node.tts_harness_state.pruning_rate
        self.tts_harness_state.execution_count = source_node.tts_harness_state.execution_count
        
        # Synchronize Arm64ReMatrix
        self.arm64_re_matrix.execution_count = source_node.arm64_re_matrix.execution_count
        self.arm64_re_matrix.pac_bypass_entropy = source_node.arm64_re_matrix.pac_bypass_entropy
        self.arm64_re_matrix.dyld_cache_hit_rate = source_node.arm64_re_matrix.dyld_cache_hit_rate
        self.arm64_re_matrix.amfi_enforcement_level = source_node.arm64_re_matrix.amfi_enforcement_level
        
        self.is_healthy = True


class BFTOrchestrator:
    """Asynchronous Orchestrator confined to queue routing and BFT Consensus Verification (R10, Ω11)."""
    def __init__(self, num_nodes: int = 3) -> None:
        if not isinstance(num_nodes, int) or num_nodes < 1:
            raise ValueError("num_nodes must be a positive integer")
        init_bft_database()
        self.queue: asyncio.Queue[tuple[int, int, int]] = asyncio.Queue()
        self.nodes = [BFTNode(i) for i in range(num_nodes)]
        self.step_index = 0
        self.last_committed_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        self.is_running = False
        self._conn: sqlite3.Connection | None = None

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            self._conn = sqlite3.connect(DB_PATH, timeout=5.0)
        return self._conn

    async def enqueue_task(self, d: int, p: int, m: int) -> None:
        """Enqueues an action tuple (domain, primitive, modifier) for asynchronous BFT processing.

        Args:
            d: Domain index. Must be a non-negative integer.
            p: Primitive index. Must be a non-negative integer.
            m: Modifier index. Must be a non-negative integer.

        Raises:
            ValueError: If any argument is not a non-negative integer.
        """
        if not isinstance(d, int) or d < 0:
            raise ValueError(f"enqueue_task: 'd' must be a non-negative integer, got {d!r}")
        if not isinstance(p, int) or p < 0:
            raise ValueError(f"enqueue_task: 'p' must be a non-negative integer, got {p!r}")
        if not isinstance(m, int) or m < 0:
            raise ValueError(f"enqueue_task: 'm' must be a non-negative integer, got {m!r}")
        await self.queue.put((d, p, m))

    async def start_loop(self, max_steps: int = -1) -> None:
        """Runs the main BFT State Loop, consuming tasks from the asyncio.Queue."""
        if not isinstance(max_steps, int) or (max_steps != -1 and max_steps < 1):
            raise ValueError(f"start_loop: 'max_steps' must be -1 or a positive integer, got {max_steps!r}")
        self.is_running = True
        steps_executed = 0
        
        while self.is_running:
            if max_steps > 0 and steps_executed >= max_steps:
                break
                
            try:
                task = await asyncio.wait_for(self.queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            d, p, m = task
            self.step_index += 1
            
            hashes = self._process_task_parallel(d, p, m)
            self._evaluate_consensus(d, p, m, hashes)

            self.queue.task_done()
            steps_executed += 1

        if self._conn:
            self._conn.close()
            self._conn = None

    def _process_task_parallel(self, d: int, p: int, m: int) -> dict[int, str]:
        """Executes the task across all active nodes and returns their hashes."""
        hashes: dict[int, str] = {}
        for node in self.nodes:
            if not node.is_healthy:
                continue
            try:
                strike_rs.dispatch_state_observer(d, p, m, node.state_vector)
                strike_rs.dispatch_neuro_chain(d, p, m, node.cognitive_chain_vector)
                strike_rs.dispatch_tts_harness(d, p, m, node.tts_harness_state)
                strike_rs.dispatch_arm64_re(d, p, m, node.arm64_re_matrix)
                hashes[node.node_id] = node.compute_state_hash()
            except (OSError, RuntimeError, ValueError) as e:
                node.is_healthy = False
                print(f"⚠️ Node {node.node_id} encountered fault during mutation: {e}")
        return hashes

    def _evaluate_consensus(self, d: int, p: int, m: int, hashes: dict[int, str]) -> None:
        """Evaluates consensus among nodes and commits to ledger if majority is reached."""
        hash_votes: dict[str, int] = {}
        for h in hashes.values():
            hash_votes[h] = hash_votes.get(h, 0) + 1

        if not hash_votes:
            print("❌ Fatal: All nodes failed execution. Apoptosis triggered.")
            self.is_running = False
            return

        majority_hash = max(hash_votes, key=lambda k: hash_votes[k])
        vote_count = hash_votes[majority_hash]
        
        active_count = len(hashes)
        if vote_count >= (active_count // 2 + 1):
            prev_hash_to_write = self.last_committed_hash
            self.last_committed_hash = majority_hash
            self._write_to_ledger(d, p, m, prev_hash_to_write, majority_hash)
            
            for node in self.nodes:
                if node.node_id in hashes and hashes[node.node_id] != majority_hash:
                    print(f"🔧 Byzantine fault detected in Node {node.node_id}. Syncing state to majority.")
                    leader_node = next(n for n in self.nodes if hashes.get(n.node_id) == majority_hash)
                    node.sync_from(leader_node)
        else:
            print("❌ BFT consensus could not be reached! Splitting or fault limit exceeded.")

    def _write_to_ledger(self, d: int, p: int, m: int, prev_hash: str, current_hash: str) -> None:
        """Writes BFT transaction to SQLite with CORTEX-TAINT signature (R10, Ω11)."""
        taint = f"[CORTEX-TAINT:borjamoskv:bft_orchestrator:{self.step_index}:{int(time.time())}]"
        conn = self._get_connection()
        try:
            conn.execute(
                "INSERT INTO bft_ledger (step_index, domain, primitive, modifier, prev_hash, current_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (self.step_index, d, p, m, prev_hash, current_hash, taint)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Double write or uniqueness constraint violation on prev_hash: {e}")
            conn.rollback()

    def get_ledger_count(self) -> int:
        """Returns the current number of rows in the Master Ledger."""
        with sqlite3.connect(DB_PATH, timeout=5.0) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM bft_ledger;")
            count = cursor.fetchone()[0]
            return int(count)

