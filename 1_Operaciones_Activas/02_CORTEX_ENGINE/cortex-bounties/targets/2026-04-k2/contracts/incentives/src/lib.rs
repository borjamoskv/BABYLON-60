#![no_std]

mod calculation;
mod constants;
mod contract;
mod error;
mod events;
mod storage;

pub use contract::IncentivesContract;
pub use contract::IncentivesContractClient;
pub use error::IncentivesError;

