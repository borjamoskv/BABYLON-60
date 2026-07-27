// C5-REAL EXERGY CERTIFIED
//! Block type for Base chains.

use crate::BaseTxEnvelope;

/// A block type for Base chains.
pub type BaseBlock = alloy_consensus::Block<BaseTxEnvelope>;
