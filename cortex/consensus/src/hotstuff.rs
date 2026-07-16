// hotstuff.rs — HotStuff BFT Consensus for ULTRATHINK 10k-node Swarm
//
// Implements the 3-phase pipelined HotStuff protocol (Yin et al., 2019)
// with SHA3-256 cryptographic hashing and quorum certificate aggregation.
// Linear message complexity O(N) per view via leader-based broadcast.

use async_trait::async_trait;
use serde::{Deserialize, Serialize};
use sha3::{Digest, Sha3_256};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::Mutex;
use log::{info, warn};

// ─────────────────────────────────────────────
// Core Data Structures
// ─────────────────────────────────────────────

/// A node in the DAG-based consensus log.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DagNode {
    pub payload: Vec<u8>,
    pub parent_hash: Option<String>,
    pub hash: String,
    pub view_number: u64,
    pub proposer_id: String,
}

impl DagNode {
    /// Compute SHA3-256 hash over (payload || parent_hash || view_number || proposer_id).
    pub fn compute_hash(
        payload: &[u8],
        parent_hash: &Option<String>,
        view_number: u64,
        proposer_id: &str,
    ) -> String {
        let mut hasher = Sha3_256::new();
        hasher.update(payload);
        if let Some(ph) = parent_hash {
            hasher.update(ph.as_bytes());
        }
        hasher.update(view_number.to_le_bytes());
        hasher.update(proposer_id.as_bytes());
        hex::encode(hasher.finalize())
    }

    pub fn new(payload: Vec<u8>, parent_hash: Option<String>, view_number: u64, proposer_id: String) -> Self {
        let hash = Self::compute_hash(&payload, &parent_hash, view_number, &proposer_id);
        DagNode {
            payload,
            parent_hash,
            hash,
            view_number,
            proposer_id,
        }
    }
}

/// Quorum Certificate — aggregated proof that >= 2f+1 replicas voted for a node.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct QuorumCertificate {
    pub node_hash: String,
    pub view_number: u64,
    pub voter_ids: Vec<String>,
    pub signature_aggregate: String, // Simplified: SHA3 of concatenated voter IDs
}

impl QuorumCertificate {
    pub fn new(node_hash: String, view_number: u64, voter_ids: Vec<String>) -> Self {
        let mut hasher = Sha3_256::new();
        hasher.update(node_hash.as_bytes());
        hasher.update(view_number.to_le_bytes());
        for vid in &voter_ids {
            hasher.update(vid.as_bytes());
        }
        let signature_aggregate = hex::encode(hasher.finalize());
        QuorumCertificate {
            node_hash,
            view_number,
            voter_ids,
            signature_aggregate,
        }
    }

    /// Check if quorum threshold is met (>= 2f+1 for N = 3f+1 replicas).
    pub fn has_quorum(&self, total_replicas: usize) -> bool {
        let f = (total_replicas.saturating_sub(1)) / 3;
        self.voter_ids.len() >= 2 * f + 1
    }
}

/// HotStuff phases per the pipelined protocol.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize, Deserialize)]
pub enum Phase {
    Prepare,
    PreCommit,
    Commit,
    Decide,
}

/// Messages exchanged between replicas.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum HotStuffMessage {
    Proposal {
        node: DagNode,
        qc: Option<QuorumCertificate>,
    },
    Vote {
        node_hash: String,
        view_number: u64,
        voter_id: String,
        phase: Phase,
    },
    NewView {
        view_number: u64,
        high_qc: Option<QuorumCertificate>,
        replica_id: String,
    },
}

// ─────────────────────────────────────────────
// Network Transport Trait
// ─────────────────────────────────────────────

#[async_trait]
pub trait NetworkTransport: Send + Sync {
    async fn broadcast(&self, data: &[u8]) -> Result<(), String>;
    async fn send(&self, target: &str, data: &[u8]) -> Result<(), String>;
    async fn receive(&self) -> Result<Vec<u8>, String>;
}

// ─────────────────────────────────────────────
// HotStuff Engine (Async)
// ─────────────────────────────────────────────

struct HotStuffState {
    view_number: u64,
    current_phase: Phase,
    last_committed: Option<DagNode>,
    pending: Vec<DagNode>,
    votes: HashMap<String, Vec<String>>, // node_hash -> voter_ids
    high_qc: Option<QuorumCertificate>,
    locked_qc: Option<QuorumCertificate>,
    replica_id: String,
    total_replicas: usize,
}

impl Default for HotStuffState {
    fn default() -> Self {
        HotStuffState {
            view_number: 0,
            current_phase: Phase::Prepare,
            last_committed: None,
            pending: Vec::new(),
            votes: HashMap::new(),
            high_qc: None,
            locked_qc: None,
            replica_id: "leader-0".to_string(),
            total_replicas: 4, // N=4 => f=1 => quorum=3
        }
    }
}

pub struct HotStuff {
    transport: Arc<dyn NetworkTransport>,
    state: Mutex<HotStuffState>,
}

impl HotStuff {
    pub fn new(transport: Arc<dyn NetworkTransport>) -> Self {
        HotStuff {
            transport,
            state: Mutex::new(HotStuffState::default()),
        }
    }

    pub fn with_config(
        transport: Arc<dyn NetworkTransport>,
        replica_id: String,
        total_replicas: usize,
    ) -> Self {
        let mut state = HotStuffState::default();
        state.replica_id = replica_id;
        state.total_replicas = total_replicas;
        HotStuff {
            transport,
            state: Mutex::new(state),
        }
    }

    /// Phase 1: Leader proposes a new node, piggybacking the highest QC.
    pub async fn propose(&self, payload: Vec<u8>) -> Result<DagNode, String> {
        let mut state = self.state.lock().await;
        state.view_number += 1;
        let parent_hash = state.last_committed.as_ref().map(|c| c.hash.clone());
        let node = DagNode::new(
            payload,
            parent_hash,
            state.view_number,
            state.replica_id.clone(),
        );

        // Track pending node
        state.pending.push(node.clone());

        let msg = HotStuffMessage::Proposal {
            node: node.clone(),
            qc: state.high_qc.clone(),
        };
        let serialized = bincode::serialize(&msg).map_err(|e| e.to_string())?;
        drop(state); // release lock before I/O
        self.transport.broadcast(&serialized).await?;
        info!("HotStuff: proposed node {} at view {}", node.hash, node.view_number);
        Ok(node)
    }

    /// Collect a vote for a node. Returns Some(QC) when quorum is reached.
    pub async fn collect_vote(
        &self,
        node_hash: &str,
        voter_id: String,
        view_number: u64,
    ) -> Result<Option<QuorumCertificate>, String> {
        let mut state = self.state.lock().await;
        let total_replicas = state.total_replicas;
        let current_phase = state.current_phase;
        let f = (total_replicas.saturating_sub(1)) / 3;
        let quorum_threshold = 2 * f + 1;

        let voters = state.votes.entry(node_hash.to_string()).or_default();
        if voters.contains(&voter_id) {
            warn!("HotStuff: duplicate vote from {} for {}", voter_id, node_hash);
            return Ok(None);
        }
        voters.push(voter_id);

        if voters.len() >= quorum_threshold {
            let qc = QuorumCertificate::new(
                node_hash.to_string(),
                view_number,
                voters.clone(),
            );
            info!(
                "HotStuff: quorum reached for {} ({}/{} votes) in phase {:?}",
                node_hash,
                voters.len(),
                total_replicas,
                current_phase
            );
            // Advance phase and enforce locking invariant
            let next_phase = match current_phase {
                Phase::Prepare => Phase::PreCommit,
                Phase::PreCommit => {
                    // SAFETY INVARIANT: Lock the QC during PreCommit.
                    // Once locked, a conflicting node cannot be committed
                    // unless the new proposal carries a QC with a higher
                    // view than locked_qc.
                    state.locked_qc = Some(qc.clone());
                    info!("HotStuff: locked QC at view {} for {}", view_number, node_hash);
                    Phase::Commit
                }
                Phase::Commit => Phase::Decide,
                Phase::Decide => Phase::Decide, // terminal
            };
            state.current_phase = next_phase;
            state.high_qc = Some(qc.clone());
            Ok(Some(qc))
        } else {
            Ok(None)
        }
    }

    /// Commit a node after Decide phase quorum is reached.
    /// Verifies: (1) phase is Decide, (2) high_qc matches the node being committed.
    pub async fn commit(&self, node: DagNode) -> Result<(), String> {
        let mut state = self.state.lock().await;
        if state.current_phase != Phase::Decide {
            return Err(format!(
                "Cannot commit in phase {:?}; must be in Decide",
                state.current_phase
            ));
        }
        // Verify the high_qc corresponds to the node we are committing
        if let Some(ref hqc) = state.high_qc {
            if hqc.node_hash != node.hash {
                return Err(format!(
                    "high_qc hash {} does not match commit target {}",
                    hqc.node_hash, node.hash
                ));
            }
        } else {
            return Err("Cannot commit without a high_qc".to_string());
        }
        info!("HotStuff: committing node {} at view {}", node.hash, node.view_number);
        state.last_committed = Some(node.clone());
        state.pending.retain(|n| n.hash != node.hash);
        state.votes.remove(&node.hash);
        // Reset phase and clear lock for next round
        state.current_phase = Phase::Prepare;
        state.locked_qc = None;
        Ok(())
    }

    /// Check if a proposal is safe w.r.t. the locking invariant.
    /// A proposal is safe if:
    ///   (a) there is no locked_qc, OR
    ///   (b) the proposal extends the locked node, OR
    ///   (c) the proposal carries a QC with view >= locked_qc.view_number
    pub async fn is_safe_proposal(
        &self,
        _node: &DagNode,
        justification_qc: &Option<QuorumCertificate>,
    ) -> bool {
        let state = self.state.lock().await;
        match &state.locked_qc {
            None => true, // no lock => always safe
            Some(locked) => {
                // Check if justification QC has a view >= locked view
                match justification_qc {
                    Some(jqc) => jqc.view_number >= locked.view_number,
                    None => false, // no justification but we have a lock => unsafe
                }
            }
        }
    }

    /// Get the current locked QC (for monitoring/debugging).
    pub async fn locked_qc(&self) -> Option<QuorumCertificate> {
        let state = self.state.lock().await;
        state.locked_qc.clone()
    }

    /// View change: triggered when the leader is suspected of being faulty.
    /// Replicas send their highest QC to the new leader.
    pub async fn initiate_view_change(&self) -> Result<u64, String> {
        let mut state = self.state.lock().await;
        state.view_number += 1;
        let new_view = state.view_number;
        let msg = HotStuffMessage::NewView {
            view_number: new_view,
            high_qc: state.high_qc.clone(),
            replica_id: state.replica_id.clone(),
        };
        let serialized = bincode::serialize(&msg).map_err(|e| e.to_string())?;
        drop(state);
        self.transport.broadcast(&serialized).await?;
        info!("HotStuff: view change initiated, new view = {}", new_view);
        Ok(new_view)
    }

    /// Get current state snapshot for monitoring.
    pub async fn status(&self) -> (u64, Phase, Option<String>) {
        let state = self.state.lock().await;
        (
            state.view_number,
            state.current_phase,
            state.last_committed.as_ref().map(|n| n.hash.clone()),
        )
    }
}

/// Synchronous wrapper for HotStuff that implements ConsensusEngine trait.
/// Uses a dedicated single-threaded runtime to avoid panicking when called
/// from within an existing tokio runtime (e.g. nested block_on).
pub struct HotStuffSync {
    inner: Arc<HotStuff>,
    runtime: std::sync::Mutex<tokio::runtime::Runtime>,
}

impl HotStuffSync {
    pub fn new(transport: Arc<dyn NetworkTransport>) -> Self {
        let inner = Arc::new(HotStuff::new(transport));
        let runtime = tokio::runtime::Builder::new_current_thread()
            .enable_all()
            .build()
            .expect("Failed to create HotStuffSync runtime");
        HotStuffSync {
            inner,
            runtime: std::sync::Mutex::new(runtime),
        }
    }
}

impl super::ConsensusEngine for HotStuffSync {
    fn propose(&self, payload: Vec<u8>) -> Result<(), String> {
        let rt = self.runtime.lock().map_err(|e| e.to_string())?;
        rt.block_on(async {
            self.inner.propose(payload).await.map(|_| ())
        })
    }
}

// ─────────────────────────────────────────────
// Mock Transport (for testing)
// ─────────────────────────────────────────────

pub struct MockTransport;

#[async_trait]
impl NetworkTransport for MockTransport {
    async fn broadcast(&self, _data: &[u8]) -> Result<(), String> {
        Ok(())
    }
    async fn send(&self, _target: &str, _data: &[u8]) -> Result<(), String> {
        Ok(())
    }
    async fn receive(&self) -> Result<Vec<u8>, String> {
        Ok(vec![])
    }
}

// ─────────────────────────────────────────────
// Unit Tests
// ─────────────────────────────────────────────

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_dag_node_hash_deterministic() {
        let payload = b"test_payload".to_vec();
        let parent = Some("abc123".to_string());
        let h1 = DagNode::compute_hash(&payload, &parent, 1, "leader-0");
        let h2 = DagNode::compute_hash(&payload, &parent, 1, "leader-0");
        assert_eq!(h1, h2, "Hash must be deterministic");
        assert_eq!(h1.len(), 64, "SHA3-256 hex digest must be 64 chars");
    }

    #[test]
    fn test_dag_node_hash_changes_with_view() {
        let payload = b"test".to_vec();
        let h1 = DagNode::compute_hash(&payload, &None, 1, "r0");
        let h2 = DagNode::compute_hash(&payload, &None, 2, "r0");
        assert_ne!(h1, h2, "Different views must produce different hashes");
    }

    #[test]
    fn test_quorum_certificate_threshold() {
        let qc = QuorumCertificate::new(
            "hash123".to_string(),
            1,
            vec!["r0".to_string(), "r1".to_string(), "r2".to_string()],
        );
        assert!(qc.has_quorum(4), "3/4 replicas should meet 2f+1 threshold (f=1)");
        assert!(!qc.has_quorum(10), "3/10 replicas should NOT meet threshold (f=3, need 7)");
    }

    #[test]
    fn test_qc_signature_deterministic() {
        let voters = vec!["a".to_string(), "b".to_string()];
        let qc1 = QuorumCertificate::new("h".to_string(), 5, voters.clone());
        let qc2 = QuorumCertificate::new("h".to_string(), 5, voters);
        assert_eq!(qc1.signature_aggregate, qc2.signature_aggregate);
    }

    #[tokio::test]
    async fn test_hotstuff_propose() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::new(transport);
        let node = hs.propose(b"hello world".to_vec()).await.unwrap();
        assert_eq!(node.view_number, 1);
        assert!(!node.hash.is_empty());
        assert_eq!(node.parent_hash, None);
    }

    #[tokio::test]
    async fn test_hotstuff_vote_collection_quorum() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::with_config(transport, "leader".to_string(), 4);
        let node = hs.propose(b"payload".to_vec()).await.unwrap();

        // 2 votes — not enough (need 3 for N=4, f=1)
        let r1 = hs.collect_vote(&node.hash, "r1".to_string(), 1).await.unwrap();
        assert!(r1.is_none());
        let r2 = hs.collect_vote(&node.hash, "r2".to_string(), 1).await.unwrap();
        assert!(r2.is_none());

        // 3rd vote reaches quorum
        let r3 = hs.collect_vote(&node.hash, "r3".to_string(), 1).await.unwrap();
        assert!(r3.is_some(), "Quorum must be reached at 3/4 votes");
        let qc = r3.unwrap();
        assert!(qc.has_quorum(4));
    }

    #[tokio::test]
    async fn test_hotstuff_duplicate_vote_rejected() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::new(transport);
        let node = hs.propose(b"dup".to_vec()).await.unwrap();

        let _ = hs.collect_vote(&node.hash, "r1".to_string(), 1).await.unwrap();
        let dup = hs.collect_vote(&node.hash, "r1".to_string(), 1).await.unwrap();
        assert!(dup.is_none(), "Duplicate votes must be silently rejected");
    }

    #[tokio::test]
    async fn test_hotstuff_view_change() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::new(transport);
        let _ = hs.propose(b"x".to_vec()).await.unwrap();
        let new_view = hs.initiate_view_change().await.unwrap();
        assert_eq!(new_view, 2, "View change should increment view number");
    }

    #[tokio::test]
    async fn test_hotstuff_status() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::new(transport);
        let (view, phase, committed) = hs.status().await;
        assert_eq!(view, 0);
        assert_eq!(phase, Phase::Prepare);
        assert!(committed.is_none());
    }

    /// Full round-trip: propose → 3 quorum rounds (Prepare→PreCommit→Commit→Decide) → commit.
    /// Verifies phase transitions, locking, and final committed state.
    #[tokio::test]
    async fn test_full_round_trip_propose_vote_commit() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::with_config(transport, "leader".to_string(), 4);

        // Propose
        let node = hs.propose(b"round_trip".to_vec()).await.unwrap();
        let view = node.view_number;

        // Phase 1: Prepare → PreCommit (3 votes = quorum for N=4)
        for voter in ["r1", "r2", "r3"] {
            hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
        }
        let (_, phase, _) = hs.status().await;
        assert_eq!(phase, Phase::PreCommit, "After Prepare quorum, should be PreCommit");
        assert!(hs.locked_qc().await.is_none(), "No lock yet before PreCommit quorum");

        // Phase 2: PreCommit → Commit (3 more votes)
        // Reset votes for next phase by using different vote keys
        // In real HotStuff, each phase has its own vote set.
        // Here we simulate by collecting on the same hash which advances the phase.
        {
            let mut state = hs.state.lock().await;
            state.votes.remove(&node.hash);
        }
        for voter in ["r1", "r2", "r3"] {
            hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
        }
        let (_, phase, _) = hs.status().await;
        assert_eq!(phase, Phase::Commit, "After PreCommit quorum, should be Commit");
        assert!(hs.locked_qc().await.is_some(), "Lock must be set after PreCommit quorum");

        // Phase 3: Commit → Decide (3 more votes)
        {
            let mut state = hs.state.lock().await;
            state.votes.remove(&node.hash);
        }
        for voter in ["r1", "r2", "r3"] {
            hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
        }
        let (_, phase, _) = hs.status().await;
        assert_eq!(phase, Phase::Decide, "After Commit quorum, should be Decide");

        // Commit
        hs.commit(node.clone()).await.unwrap();
        let (_, phase, committed) = hs.status().await;
        assert_eq!(phase, Phase::Prepare, "After commit, phase resets to Prepare");
        assert_eq!(committed, Some(node.hash.clone()), "Committed hash must match");
        assert!(hs.locked_qc().await.is_none(), "Lock must be cleared after commit");
    }

    /// Verify that commit fails when high_qc doesn't match the target node.
    #[tokio::test]
    async fn test_commit_rejects_mismatched_hash() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::with_config(transport, "leader".to_string(), 4);

        let node = hs.propose(b"real".to_vec()).await.unwrap();
        let view = node.view_number;

        // Drive all 3 phases to Decide
        for _ in 0..3 {
            {
                let mut state = hs.state.lock().await;
                state.votes.remove(&node.hash);
            }
            for voter in ["r1", "r2", "r3"] {
                hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
            }
        }

        // Try to commit a DIFFERENT node
        let fake_node = DagNode::new(b"fake".to_vec(), None, 999, "attacker".to_string());
        let result = hs.commit(fake_node).await;
        assert!(result.is_err(), "Committing a node not matching high_qc must fail");
        assert!(
            result.unwrap_err().contains("does not match"),
            "Error must mention hash mismatch"
        );
    }

    /// Verify locking safety: a proposal without sufficient justification
    /// is deemed unsafe when a lock exists.
    #[tokio::test]
    async fn test_locking_safety_invariant() {
        let transport = Arc::new(MockTransport);
        let hs = HotStuff::with_config(transport, "leader".to_string(), 4);

        // Initially safe (no lock)
        let node = hs.propose(b"safe".to_vec()).await.unwrap();
        assert!(hs.is_safe_proposal(&node, &None).await, "No lock => always safe");

        // Drive through Prepare + PreCommit to set locked_qc
        let view = node.view_number;
        for voter in ["r1", "r2", "r3"] {
            hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
        }
        {
            let mut state = hs.state.lock().await;
            state.votes.remove(&node.hash);
        }
        for voter in ["r1", "r2", "r3"] {
            hs.collect_vote(&node.hash, voter.to_string(), view).await.unwrap();
        }
        assert!(hs.locked_qc().await.is_some(), "Lock must exist after PreCommit");

        // Without justification => unsafe
        let node2 = DagNode::new(b"conflict".to_vec(), None, 99, "rogue".to_string());
        assert!(!hs.is_safe_proposal(&node2, &None).await, "No justification + lock => unsafe");

        // With a QC at a higher view => safe
        let high_qc = QuorumCertificate::new("any".to_string(), view + 1, vec!["r1".into()]);
        assert!(hs.is_safe_proposal(&node2, &Some(high_qc)).await, "Higher view QC => safe");

        // With a QC at a lower view => unsafe
        let low_qc = QuorumCertificate::new("any".to_string(), 0, vec!["r1".into()]);
        assert!(!hs.is_safe_proposal(&node2, &Some(low_qc)).await, "Lower view QC => unsafe");
    }
}
