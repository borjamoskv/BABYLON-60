// C5-REAL EXERGY CERTIFIED
//! Configuration types for load tests and workloads.

mod workload;
pub use workload::WorkloadConfig;

mod test_config;
pub use test_config::{OsakaTarget, PrecompileTarget, TestConfig, TxTypeConfig, WeightedTxType};
