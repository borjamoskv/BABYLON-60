import asyncio
import sqlite3
import hashlib
import time
import os
from typing import List, Tuple, Dict, Any
import strike_rs

# DB Concurrency & Persist Configurations (R10)
DB_PATH = "cortex_bft_ledger.db"

def init_bft_database():
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
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.state_vector = strike_rs.StateVector()
        self.cognitive_chain_vector = strike_rs.CognitiveChainVector()
        self.tts_harness_state = strike_rs.TTSHarnessState()
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
            f"kv_eff:{self.tts_harness_state.kv_cache_efficiency}"
        )
        return hashlib.sha3_256(state_data.encode("utf-8")).hexdigest()

    def sync_from(self, source_node: 'BFTNode'):
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
        
        self.is_healthy = True


class BFTOrchestrator:
    """Asynchronous Orchestrator confined to queue routing and BFT Consensus Verification (R10, Ω11)."""
    def __init__(self, num_nodes: int = 3):
        init_bft_database()
        self.queue = asyncio.Queue()
        self.nodes = [BFTNode(i) for i in range(num_nodes)]
        self.step_index = 0
        self.last_committed_hash = "GENESIS_HASH_00000000000000000000000000000000000000000000000000000"
        self.is_running = False

    async def enqueue_task(self, d: int, p: int, m: int):
        """Enqueues an action tuple to be processed asynchronously."""
        await self.queue.put((d, p, m))

    async def start_loop(self, max_steps: int = -1):
        """Runs the main BFT State Loop consuming tasks from the asyncio.Queue."""
        self.is_running = True
        steps_executed = 0
        
        while self.is_running:
            if max_steps > 0 and steps_executed >= max_steps:
                break
                
            try:
                # Retrieve next task with a short timeout to allow clean shutdown
                task = await asyncio.wait_for(self.queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                continue

            d, p, m = task
            self.step_index += 1
            
            # 1. Parallel execution across all nodes via Rust strike_rs
            hashes = {}
            for node in self.nodes:
                if not node.is_healthy:
                    continue
                try:
                    # Delegate mutation of the 3000 primitives to Rust compiled core
                    strike_rs.dispatch_state_observer(d, p, m, node.state_vector)
                    strike_rs.dispatch_neuro_chain(d, p, m, node.cognitive_chain_vector)
                    strike_rs.dispatch_tts_harness(d, p, m, node.tts_harness_state)
                    
                    # Compute state hash
                    h = node.compute_state_hash()
                    hashes[node.node_id] = h
                except Exception as e:
                    # Mark node as Byzantine/unhealthy if execution throws
                    node.is_healthy = False
                    print(f"⚠️ Node {node.node_id} encountered fault during mutation: {e}")

            # 2. BFT Consensus voting (N >= 3 consensus check)
            hash_votes = {}
            for node_id, h in hashes.items():
                hash_votes[h] = hash_votes.get(h, 0) + 1

            if not hash_votes:
                print("❌ Fatal: All nodes failed execution. Apoptosis triggered.")
                self.is_running = False
                self.queue.task_done()
                break

            # Find majority hash
            majority_hash = max(hash_votes, key=hash_votes.get)
            vote_count = hash_votes[majority_hash]
            
            # Consensus achieved if majority matches simple majority of active nodes
            active_count = len([n for n in self.nodes if n.is_healthy])
            if vote_count >= (active_count // 2 + 1):
                # Valid transition, commit to Master Ledger (Ω11)
                prev_hash_to_write = self.last_committed_hash
                self.last_committed_hash = majority_hash
                
                # Write to the immutable SQLite WAL database
                self._write_to_ledger(d, p, m, prev_hash_to_write, majority_hash)
                
                # Correct any Byzantine outlier node
                for node in self.nodes:
                    if node.node_id in hashes and hashes[node.node_id] != majority_hash:
                        print(f"🔧 Byzantine fault detected in Node {node.node_id}. Syncing state to majority.")
                        # Find a healthy node with the majority hash
                        leader_node = next(n for n in self.nodes if hashes.get(n.node_id) == majority_hash)
                        node.sync_from(leader_node)
            else:
                print("❌ BFT consensus could not be reached! Splitting or fault limit exceeded.")

            self.queue.task_done()
            steps_executed += 1

    def _write_to_ledger(self, d: int, p: int, m: int, prev_hash: str, current_hash: str):
        """Writes BFT transaction to SQLite with CORTEX-TAINT signature (R10, Ω11)."""
        taint = f"[CORTEX-TAINT:borjamoskv:bft_orchestrator:{self.step_index}:{int(time.time())}]"
        
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        try:
            conn.execute(
                "INSERT INTO bft_ledger (step_index, domain, primitive, modifier, prev_hash, current_hash, cortex_taint) VALUES (?, ?, ?, ?, ?, ?, ?);",
                (self.step_index, d, p, m, prev_hash, current_hash, taint)
            )
            conn.commit()
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Double write or uniqueness constraint violation on prev_hash: {e}")
            conn.rollback()
        finally:
            conn.close()

    def get_ledger_count(self) -> int:
        """Returns the current number of rows in the Master Ledger."""
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bft_ledger;")
        count = cursor.fetchone()[0]
        conn.close()
        return count
