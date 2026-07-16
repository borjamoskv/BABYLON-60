// lib.rs — Cortex Consensus crate root

pub mod hotstuff;

#[cfg(not(feature = "use_hotstuff"))]
pub mod pbft {
    use super::ConsensusEngine;

    pub struct Pbft;

    impl Pbft {
        pub fn new() -> Self {
            Pbft
        }
    }

    impl ConsensusEngine for Pbft {
        fn propose(&self, _payload: Vec<u8>) -> Result<(), String> {
            // PBFT propose logic (stub — legacy path)
            Ok(())
        }
    }
}

/// Trait definition for consensus engines.
/// All consensus implementations (PBFT, HotStuff) must satisfy this interface.
pub trait ConsensusEngine: Send + Sync {
    fn propose(&self, payload: Vec<u8>) -> Result<(), String>;
}

/// Factory function: returns the active consensus engine based on compile-time feature flags.
pub fn get_consensus_engine() -> Box<dyn ConsensusEngine> {
    #[cfg(feature = "use_hotstuff")]
    {
        use std::sync::Arc;
        Box::new(hotstuff::HotStuffSync::new(Arc::new(hotstuff::MockTransport)))
    }
    #[cfg(not(feature = "use_hotstuff"))]
    {
        Box::new(pbft::Pbft::new())
    }
}
