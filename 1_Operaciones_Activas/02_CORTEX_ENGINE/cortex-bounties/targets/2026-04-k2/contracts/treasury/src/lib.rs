#![no_std]

pub mod contract;
pub mod error;
mod events;
pub mod storage;

pub use contract::TreasuryContract;
pub use contract::TreasuryContractClient;
pub use error::TreasuryError;

