use dashmap::DashMap;
use rusqlite::Connection;
use serde::{Deserialize, Serialize};
use std::sync::Mutex;

#[derive(Debug, Serialize, Deserialize, Clone, PartialEq, Eq, Hash)]
pub struct NodeId(pub String);

#[derive(Debug, Serialize, Deserialize, Clone)]
pub struct StateHash(pub String);

#[derive(Debug, Serialize, Deserialize, Clone)]
pub enum NodeStatus {
    Pending,
    Active,
    Resolved(StateHash),
    Failed(String),
}

#[derive(Debug, Clone)]
pub struct CausalNode {
    pub id: NodeId,
    pub dependencies: Vec<NodeId>,
    pub status: NodeStatus,
    pub script_path: String,
    // Epigenetic flag. Default 1 (Silenced). Unsilenced when explicitly accessed.
    pub methylation_flag: u8,
}

pub struct EventLedger {
    pub nodes: DashMap<NodeId, CausalNode>,
    // R10: Epigenetic Context Store (SQLite WAL)
    pub db: Mutex<Connection>,
}

impl EventLedger {
    pub fn new() -> Self {
        let db = Connection::open("moskv_memory.db").expect("Failed to open C5-REAL SQLite DB");

        // R10: WAL Mode + Strict Connection Factors
        db.pragma_update(None, "journal_mode", "WAL").unwrap();
        db.pragma_update(None, "synchronous", "NORMAL").unwrap();
        db.busy_timeout(std::time::Duration::from_millis(5000))
            .unwrap();

        db.execute(
            "CREATE TABLE IF NOT EXISTS epigenetic_context (
                node_id TEXT PRIMARY KEY,
                state_hash TEXT,
                methylation_flag INTEGER,
                status TEXT
            )",
            [],
        )
        .unwrap();

        Self {
            nodes: DashMap::new(),
            db: Mutex::new(db),
        }
    }

    pub fn register_node(&self, node: CausalNode) {
        self.nodes.insert(node.id.clone(), node);
    }

    pub fn can_execute(&self, id: &NodeId) -> bool {
        let (status, dependencies) = {
            let node = self.nodes.get(id).unwrap();
            (node.status.clone(), node.dependencies.clone())
        };

        if !matches!(status, NodeStatus::Pending) {
            return false;
        }

        dependencies
            .iter()
            .all(|dep| matches!(self.nodes.get(dep).unwrap().status, NodeStatus::Resolved(_)))
    }

    pub fn resolve_node(&self, id: &NodeId, hash: StateHash) {
        if let Some(mut node) = self.nodes.get_mut(id) {
            node.status = NodeStatus::Resolved(hash.clone());
            // Epigenetic demethylation upon resolution
            node.methylation_flag = 0;

            // C5-REAL Persistence Write
            let db = self.db.lock().unwrap();
            let mut stmt = db.prepare_cached(
                "INSERT OR REPLACE INTO epigenetic_context (node_id, state_hash, methylation_flag, status) 
                 VALUES (?1, ?2, ?3, ?4)"
            ).unwrap();
            stmt.execute((&node.id.0, &hash.0, node.methylation_flag, "RESOLVED"))
                .unwrap();
        }
    }
}
