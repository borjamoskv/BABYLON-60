// C5-REAL EXERGY CERTIFIED
// SCITT Atestation & Merkle Tree SHA3-256
use sha3::{Digest, Sha3_256};
use serde::{Deserialize, Serialize};
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ScittReceipt {
    pub version: u32,
    pub timestamp_ns: u64,
    pub action: String,
    pub target_path: String,
    pub bytes_reclaimed: u64,
    pub exergy_score: f64,
    pub leaf_hash: String,
    pub merkle_root: String,
}

pub struct MerkleTree {
    leaves: Vec<[u8; 32]>,
}

impl MerkleTree {
    pub fn new() -> Self {
        Self { leaves: Vec::new() }
    }

    pub fn add_leaf(&mut self, data: &[u8]) -> [u8; 32] {
        let mut hasher = Sha3_256::new();
        hasher.update(data);
        let digest: [u8; 32] = hasher.finalize().into();
        self.leaves.push(digest);
        digest
    }

    pub fn compute_root(&self) -> [u8; 32] {
        if self.leaves.is_empty() {
            return [0u8; 32];
        }
        let mut current_level = self.leaves.clone();
        while current_level.len() > 1 {
            let mut next_level = Vec::new();
            for chunk in current_level.chunks(2) {
                let mut hasher = Sha3_256::new();
                hasher.update(&chunk[0]);
                if chunk.len() > 1 {
                    hasher.update(&chunk[1]);
                } else {
                    hasher.update(&chunk[0]); // Duplicate odd leaf
                }
                next_level.push(hasher.finalize().into());
            }
            current_level = next_level;
        }
        current_level[0]
    }

    pub fn create_receipt(
        &mut self,
        action: &str,
        path: &str,
        bytes: u64,
        exergy_score: f64,
    ) -> ScittReceipt {
        let payload = format!("{}:{}:{}:{}", action, path, bytes, exergy_score);
        let leaf_digest = self.add_leaf(payload.as_bytes());
        let root_digest = self.compute_root();

        let now = SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos() as u64;

        ScittReceipt {
            version: 1,
            timestamp_ns: now,
            action: action.to_string(),
            target_path: path.to_string(),
            bytes_reclaimed: bytes,
            exergy_score,
            leaf_hash: hex::encode(leaf_digest),
            merkle_root: hex::encode(root_digest),
        }
    }
}

pub mod hex {
    pub fn encode(bytes: [u8; 32]) -> String {
        bytes.iter().map(|b| format!("{:02x}", b)).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_merkle_tree_determinism() {
        let mut tree1 = MerkleTree::new();
        let receipt1 = tree1.create_receipt("PURGE", "/tmp/cache", 1024, 0.05);

        let mut tree2 = MerkleTree::new();
        let leaf2 = tree2.add_leaf(b"PURGE:/tmp/cache:1024:0.05");

        assert_eq!(receipt1.leaf_hash, hex::encode(leaf2));
        assert_eq!(receipt1.merkle_root, hex::encode(tree2.compute_root()));
    }
}
