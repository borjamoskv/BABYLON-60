#!/usr/bin/env python3
import sqlite3
import time

DB_PATH = "swarm_os.sqlite"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS quorum_pheromones (
            agent_id TEXT,
            intent_hash TEXT,
            timestamp REAL,
            PRIMARY KEY (agent_id, intent_hash)
        )
    ''')
    conn.commit()
    conn.close()

def emit_pheromone(agent_id: str, intent_hash: str):
    """
    Emits a lightweight state token to the decentralized bus.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO quorum_pheromones (agent_id, intent_hash, timestamp) VALUES (?, ?, ?)', (agent_id, intent_hash, time.time()))
    conn.commit()
    conn.close()
    print(f"[QuorumBus] Pheromone emitted by {agent_id} for intent {intent_hash[:8]}...")

def check_quorum(intent_hash: str, required_nodes: int, threshold: float = 0.51):
    """
    Evaluates if the swarm has reached the critical mass to execute the next DAG phase.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Pheromones expire after 60 seconds (volatile memory)
    cutoff_time = time.time() - 60 
    c.execute('SELECT COUNT(*) FROM quorum_pheromones WHERE intent_hash = ? AND timestamp > ?', (intent_hash, cutoff_time))
    active_votes = c.fetchone()[0]
    conn.close()
    
    current_ratio = active_votes / required_nodes
    if current_ratio >= threshold:
        print(f"[QuorumBus] QUORUM REACHED ({current_ratio*100:.1f}%). Triggering phase shift.")
        return True
    
    print(f"[QuorumBus] Waiting for Quorum... ({current_ratio*100:.1f}%)")
    return False

if __name__ == "__main__":
    print("=== C5-REAL QUORUM SENSING BUS ===")
    init_db()
    intent = "a1b2c3d4"
    emit_pheromone("worker-1", intent)
    emit_pheromone("worker-2", intent)
    # Assume a swarm of 3 nodes, 2 votes = 66% (Quorum reached)
    reached = check_quorum(intent, required_nodes=3)
    assert reached == True
    print("Self-Test: PASSED")
