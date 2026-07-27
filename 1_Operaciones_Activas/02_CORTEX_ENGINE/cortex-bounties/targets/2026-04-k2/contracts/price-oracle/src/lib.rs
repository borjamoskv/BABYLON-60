#![no_std]

pub mod contract;
mod error;
mod events;
mod oracle;
mod storage;
mod upgrade;

pub use contract::PriceOracleContract;
pub use contract::PriceOracleContractClient;
pub use error::OracleError;


#[cfg(test)]
mod test_poc_staleness;
