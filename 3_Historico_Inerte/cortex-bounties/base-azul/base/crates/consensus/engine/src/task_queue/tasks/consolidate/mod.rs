// C5-REAL EXERGY CERTIFIED
//! Consolidation Task

mod error;
pub use error::ConsolidateTaskError;

mod task;
pub use task::{ConsolidateInput, ConsolidateTask};

#[cfg(test)]
mod task_test;
